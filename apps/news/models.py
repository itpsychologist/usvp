"""Новини та оголошення: списки з фільтрами й пагінацією, архів оголошень, RSS новин."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.fields import StreamField
from wagtail.search import index

from apps.core.blocks import BodyStreamBlock
from apps.core.models import TranslatableSnippet, validate_image_description
from apps.core.pagination import paginate
from apps.pages.models import BasePage

NEWS_PER_PAGE = 12
ANNOUNCEMENTS_PER_PAGE = 12


class NewsTopic(TranslatableSnippet):
    """Тема новин для фільтра: «Ветеранам», «ВПО», «Соціальні послуги»…"""

    name = models.CharField("Назва", max_length=80)
    slug = models.SlugField(
        "Ідентифікатор в адресі",
        max_length=80,
        allow_unicode=True,
        help_text="Латиницею або кирилицею без пробілів, напр. «veteranam».",
    )

    panels = [FieldPanel("name"), FieldPanel("slug")]

    class Meta(TranslatableSnippet.Meta):
        verbose_name = "Тема новин"
        verbose_name_plural = "Теми новин"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["slug", "locale"], name="unique_topic_slug_per_locale")
        ]

    def __str__(self):
        return self.name


class NewsIndexPage(RoutablePageMixin, BasePage):
    """Список новин: фільтр за роком і темою, пагінація, RSS за адресою rss/."""

    parent_page_types = ["home.HomePage"]
    subpage_types = ["news.NewsPage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Список новин"
        verbose_name_plural = "Списки новин"

    def get_news(self):
        return (
            NewsPage.objects.live()
            .public()
            .descendant_of(self)
            .order_by("-date", "-pk")
            .prefetch_related("topics")
            .select_related("cover")
        )

    def get_topics(self):
        """Лише теми опублікованих новин цього списку: назви тем із чернеток не показуємо."""
        return (
            NewsTopic.objects.filter(locale=self.locale, newspage__in=self.get_news())
            .distinct()
            .order_by("name")
        )

    def get_years(self):
        return [d.year for d in self.get_news().dates("date", "year", order="DESC")]

    @path("")
    def index(self, request):
        news = self.get_news()
        years = self.get_years()
        topics = self.get_topics()
        # Значення фільтрів приймаємо лише зі списків на сторінці: довільний ?year=99999
        # чи ?year=² інакше спричинив би помилку сервера
        year = request.GET.get("year", "")
        topic = request.GET.get("topic", "")
        if year not in {str(y) for y in years}:
            year = ""
        if topic not in {t.slug for t in topics}:
            topic = ""
        if year:
            news = news.filter(date__year=int(year))
        if topic:
            news = news.filter(topics__slug=topic)
        page_obj, pagination = paginate(request, news, NEWS_PER_PAGE)
        return self.render(
            request,
            context_overrides={
                "news": page_obj,
                "pagination": pagination,
                "years": years,
                "topics": topics,
                "selected_year": year,
                "selected_topic": topic,
                "is_filtered": bool(year or topic),
            },
        )

    @path("rss/", name="rss")
    def rss(self, request):
        from apps.news.feeds import NewsFeed

        return NewsFeed(self)(request)


class NewsPage(BasePage):
    date = models.DateField("Дата", default=timezone.localdate)
    cover = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Обкладинка",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Горизонтальне фото 16:9. Альтернативний текст — опис зображення в бібліотеці: "
        "що на фото, а не «фото».",
    )
    cover_caption = models.CharField("Підпис до фото", max_length=250, blank=True)
    topics = ParentalManyToManyField(NewsTopic, verbose_name="Теми", blank=True)
    body = StreamField(BodyStreamBlock(), verbose_name="Текст новини", use_json_field=True)

    content_panels = [
        *BasePage.content_panels,
        FieldRowPanel([FieldPanel("date"), FieldPanel("topics")]),
        MultiFieldPanel([FieldPanel("cover"), FieldPanel("cover_caption")], heading="Обкладинка"),
        FieldPanel("body"),
    ]
    search_fields = [
        *BasePage.search_fields,
        index.SearchField("body"),
        index.FilterField("date"),
    ]

    parent_page_types = ["news.NewsIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"

    def clean(self):
        super().clean()
        validate_image_description(self.cover, "cover")

    @property
    def lead(self):
        return self.intro

    @property
    def tag(self):
        """Перша тема — бейдж на картці новини (теми підвантажено через prefetch_related)."""
        topics = list(self.topics.all())
        return topics[0].name if topics else ""

    def get_related(self, count=3):
        return (
            NewsPage.objects.live()
            .public()
            .sibling_of(self, inclusive=False)
            .order_by("-date", "-pk")
            .select_related("cover")
            .prefetch_related("topics")[:count]
        )


class AnnouncementIndexPage(BasePage):
    """Оголошення: актуальні за замовчуванням, архів — ?archive=1."""

    parent_page_types = ["home.HomePage"]
    subpage_types = ["news.AnnouncementPage"]
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Список оголошень"
        verbose_name_plural = "Списки оголошень"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        show_archive = request.GET.get("archive") == "1"
        announcements = AnnouncementPage.objects.live().public().descendant_of(self)
        if show_archive:
            announcements = AnnouncementPage.archived_qs(announcements)
        else:
            announcements = AnnouncementPage.actual(announcements)
        page_obj, pagination = paginate(request, announcements, ANNOUNCEMENTS_PER_PAGE)
        context.update(announcements=page_obj, pagination=pagination, show_archive=show_archive)
        return context


class AnnouncementPage(BasePage):
    date = models.DateField("Дата публікації", default=timezone.localdate)
    event_date = models.DateTimeField(
        "Дата й час події",
        null=True,
        blank=True,
        help_text="Для оголошень про прийом, збори тощо. Порожньо, якщо події немає.",
    )
    valid_until = models.DateField(
        "Діє до",
        null=True,
        blank=True,
        help_text="Після цієї дати оголошення автоматично переходить в архів. "
        "Порожньо — оголошення актуальне без обмеження строку.",
    )
    body = StreamField(BodyStreamBlock(), verbose_name="Текст оголошення", use_json_field=True)

    content_panels = [
        *BasePage.content_panels,
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldRowPanel([FieldPanel("event_date"), FieldPanel("valid_until")]),
            ],
            heading="Дати",
        ),
        FieldPanel("body"),
    ]
    search_fields = [
        *BasePage.search_fields,
        index.SearchField("body"),
        index.FilterField("date"),
        index.FilterField("valid_until"),
    ]

    parent_page_types = ["news.AnnouncementIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Оголошення"
        verbose_name_plural = "Оголошення"

    def clean(self):
        super().clean()
        if self.valid_until and self.date and self.valid_until < self.date:
            raise ValidationError({"valid_until": "Дата «Діє до» раніша за дату публікації."})

    @property
    def archived(self):
        return bool(self.valid_until and self.valid_until < timezone.localdate())

    @staticmethod
    def actual(queryset):
        today = timezone.localdate()
        return queryset.filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=today)
        ).order_by("-date", "-pk")

    @staticmethod
    def archived_qs(queryset):
        return queryset.filter(valid_until__lt=timezone.localdate()).order_by("-valid_until", "-pk")
