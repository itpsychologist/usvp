"""Довідники управління (snippets): відділи, працівники, фахівці із супроводу, ветеранські простори.

Їх показує сторінка DirectoryPage (керівництво, структура, фахівці, простори) і ContactPage.
Фото працівників публікуються лише за письмовою згодою (ЗУ «Про захист персональних даних»).
"""

from django.db import models
from django.db.models import Prefetch
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index

from apps.core.models import TranslatableSnippet, validate_image_description
from apps.pages.models import BasePage

PHOTO_HELP = (
    "Лише за письмовою згодою працівника на оприлюднення фото. "
    "Альтернативний текст підставляється автоматично: ім'я працівника."
)
PHONE_HELP = "Як показувати відвідувачам: (05361) 7-00-00"


class OrderedSnippet(TranslatableSnippet):
    sort_order = models.PositiveIntegerField(
        "Порядок у списку", default=0, help_text="Менше число — вище у списку."
    )

    class Meta(TranslatableSnippet.Meta):
        abstract = True
        ordering = ["sort_order", "pk"]


class Department(index.Indexed, OrderedSnippet):
    name = models.CharField("Назва відділу", max_length=200)
    functions = RichTextField(
        "Основні функції",
        blank=True,
        features=["bold", "ol", "ul", "link"],
        help_text="Коротко: чим займається відділ і з якими питаннями до нього звертатися.",
    )
    address = models.CharField(
        "Адреса",
        max_length=250,
        blank=True,
        help_text="Заповнюйте, лише якщо відділ працює не за адресою управління.",
    )
    room = models.CharField("Кабінет", max_length=50, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True, help_text=PHONE_HELP)
    email = models.EmailField("Електронна пошта", blank=True)
    hours = models.CharField(
        "Години прийому", max_length=200, blank=True, help_text="Напр. «Пн–Чт 08:00–17:15»"
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("functions"),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("address"), FieldPanel("room")]),
                FieldRowPanel([FieldPanel("phone"), FieldPanel("email")]),
                FieldPanel("hours"),
            ],
            heading="Контакти",
        ),
        FieldPanel("sort_order"),
    ]
    search_fields = [index.SearchField("name"), index.SearchField("functions")]

    class Meta(OrderedSnippet.Meta):
        verbose_name = "Відділ"
        verbose_name_plural = "Відділи"

    def __str__(self):
        return self.name

    @property
    def title(self):
        """Для контактної картки UI-кіту."""
        return self.name


class Person(index.Indexed, OrderedSnippet):
    name = models.CharField("Прізвище, ім'я, по батькові", max_length=200)
    position = models.CharField("Посада", max_length=200)
    department = models.ForeignKey(
        Department,
        verbose_name="Відділ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="people",
    )
    is_leadership = models.BooleanField(
        "Керівництво",
        default=False,
        help_text="Показувати на сторінці «Керівництво» і в контактах.",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=PHOTO_HELP,
    )
    phone = models.CharField("Телефон", max_length=30, blank=True, help_text=PHONE_HELP)
    email = models.EmailField("Електронна пошта", blank=True)
    reception = models.CharField(
        "Особистий прийом",
        max_length=200,
        blank=True,
        help_text="Дні й години особистого прийому громадян, напр. «Вівторок, 09:00–12:00».",
    )

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("position")]),
        FieldRowPanel([FieldPanel("department"), FieldPanel("is_leadership")]),
        FieldPanel("photo"),
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("phone"), FieldPanel("email")]), FieldPanel("reception")],
            heading="Контакти й прийом",
        ),
        FieldPanel("sort_order"),
    ]
    search_fields = [index.SearchField("name"), index.SearchField("position")]

    class Meta(OrderedSnippet.Meta):
        verbose_name = "Працівник"
        verbose_name_plural = "Працівники"

    def __str__(self):
        return f"{self.name} — {self.position}"


class VeteranSpecialist(index.Indexed, OrderedSnippet):
    name = models.CharField("Прізвище, ім'я, по батькові", max_length=200)
    territory = models.CharField(
        "Територія обслуговування",
        max_length=200,
        help_text="Старостинський округ, мікрорайон або «усі громади».",
    )
    phone = models.CharField("Телефон", max_length=30, blank=True, help_text=PHONE_HELP)
    email = models.EmailField("Електронна пошта", blank=True)
    schedule = models.CharField("Графік прийому", max_length=200, blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("territory"),
        FieldRowPanel([FieldPanel("phone"), FieldPanel("email")]),
        FieldPanel("schedule"),
        FieldPanel("sort_order"),
    ]
    search_fields = [index.SearchField("name"), index.SearchField("territory")]

    class Meta(OrderedSnippet.Meta):
        verbose_name = "Фахівець із супроводу ветеранів"
        verbose_name_plural = "Фахівці із супроводу ветеранів"

    def __str__(self):
        return f"{self.name} ({self.territory})"


class VeteranSpace(index.Indexed, OrderedSnippet):
    name = models.CharField("Назва", max_length=200)
    address = models.CharField("Адреса", max_length=250)
    hours = models.CharField("Години роботи", max_length=200, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True, help_text=PHONE_HELP)
    services = RichTextField(
        "Послуги",
        blank=True,
        features=["bold", "ul", "ol", "link"],
        help_text="Що тут можна отримати.",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Фото",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Фото простору. Альтернативний текст — «Опис» зображення в бібліотеці "
        "(обов'язковий).",
    )
    map_url = models.URLField("Посилання на Google Maps", blank=True)

    panels = [
        FieldPanel("name"),
        FieldRowPanel([FieldPanel("address"), FieldPanel("map_url")]),
        FieldRowPanel([FieldPanel("hours"), FieldPanel("phone")]),
        FieldPanel("services"),
        FieldPanel("photo"),
        FieldPanel("sort_order"),
    ]
    search_fields = [index.SearchField("name"), index.SearchField("services")]

    class Meta(OrderedSnippet.Meta):
        verbose_name = "Ветеранський простір"
        verbose_name_plural = "Ветеранські простори"

    def clean(self):
        super().clean()
        validate_image_description(self.photo, "photo")

    def __str__(self):
        return self.name


class DirectoryPage(BasePage):
    """Сторінка-довідник: показує всі записи одного з довідників у заданому порядку."""

    LEADERSHIP = "leadership"
    DEPARTMENTS = "departments"
    SPECIALISTS = "specialists"
    SPACES = "spaces"
    KINDS = [
        (LEADERSHIP, "Керівництво"),
        (DEPARTMENTS, "Структура (відділи)"),
        (SPECIALISTS, "Фахівці із супроводу ветеранів"),
        (SPACES, "Ветеранські простори"),
    ]

    kind = models.CharField(
        "Що показувати",
        max_length=20,
        choices=KINDS,
        help_text="Записи редагуються в розділі «Фрагменти» адмінки; сторінка оновлюється сама.",
    )

    content_panels = [*BasePage.content_panels, FieldPanel("kind")]

    parent_page_types = ["pages.SectionIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Довідник (керівництво, відділи, фахівці, простори)"
        verbose_name_plural = "Довідники"

    def get_entries(self):
        locale = self.locale
        if self.kind == self.LEADERSHIP:
            return Person.objects.filter(locale=locale, is_leadership=True).select_related("photo")
        if self.kind == self.DEPARTMENTS:
            people = Person.objects.filter(locale=locale)
            return Department.objects.filter(locale=locale).prefetch_related(
                Prefetch("people", queryset=people)
            )
        if self.kind == self.SPECIALISTS:
            return VeteranSpecialist.objects.filter(locale=locale)
        return VeteranSpace.objects.filter(locale=locale).select_related("photo")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["entries"] = self.get_entries()
        return context
