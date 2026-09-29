from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.core.blocks import TaskTileBlock

HOME_NEWS_COUNT = 3
HOME_ANNOUNCEMENTS_COUNT = 3
DEFAULT_HERO_HEADING = "Управління соціальної та ветеранської політики Лубенської міської ради"


class HomePage(Page):
    """Головна: hero з пошуком, плитки «Що вам потрібно?», оголошення, новини, ключові послуги,
    контакти. Новини й оголошення беруться з дочірніх списків NewsIndexPage і
    AnnouncementIndexPage.
    """

    hero_heading = models.CharField(
        "Заголовок на головній", max_length=150, default=DEFAULT_HERO_HEADING
    )
    hero_text = models.TextField(
        "Текст під заголовком",
        blank=True,
        max_length=300,
        help_text="1–2 речення: чим управління допомагає мешканцям громади.",
    )
    tiles = StreamField(
        [("tile", TaskTileBlock())],
        verbose_name="Плитки «Що вам потрібно?»",
        blank=True,
        use_json_field=True,
        max_num=8,
        help_text="6–8 плиток за життєвими ситуаціями: «Ветеранам», «ВПО», «Пільги» тощо.",
    )
    featured_pages = StreamField(
        [("page", blocks.PageChooserBlock(label="Сторінка"))],
        verbose_name="Ключові послуги та програми",
        blank=True,
        use_json_field=True,
        max_num=6,
        help_text="До 6 сторінок. На картці показується назва й опис сторінки.",
    )

    content_panels = [
        *Page.content_panels,
        MultiFieldPanel([FieldPanel("hero_heading"), FieldPanel("hero_text")], heading="Hero"),
        FieldPanel("tiles"),
        FieldPanel("featured_pages"),
    ]
    search_fields = [*Page.search_fields, index.SearchField("hero_text")]

    max_count_per_parent = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "pages.SectionIndexPage",
        "pages.StandardPage",
        "news.NewsIndexPage",
        "news.AnnouncementIndexPage",
        "contacts.ContactPage",
    ]

    class Meta:
        verbose_name = "Головна сторінка"
        verbose_name_plural = "Головні сторінки"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        pages = [block.value for block in self.featured_pages if block.value]
        context["featured"] = [p.specific for p in pages if p.live]
        context.update(self.get_news_context())
        return context

    def get_news_context(self):
        """Останні новини й актуальні оголошення для головної (якщо списки створено)."""
        from apps.news.models import AnnouncementIndexPage, AnnouncementPage, NewsIndexPage

        context = {}
        news_index = NewsIndexPage.objects.live().public().child_of(self).first()
        if news_index:
            context["news_index"] = news_index
            context["latest_news"] = news_index.get_news()[:HOME_NEWS_COUNT]
        announcements_index = AnnouncementIndexPage.objects.live().public().child_of(self).first()
        if announcements_index:
            actual = AnnouncementPage.actual(
                AnnouncementPage.objects.live().public().descendant_of(announcements_index)
            )
            context["announcements_index"] = announcements_index
            context["announcements"] = actual[:HOME_ANNOUNCEMENTS_COUNT]
        return context
