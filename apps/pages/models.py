from django.db import models
from django.utils.functional import cached_property
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.core.blocks import BodyStreamBlock, prepare_body

# Скільки заголовків H2 потрібно, щоб показати блок «На цій сторінці»
TOC_MIN_HEADINGS = 3


class BasePage(Page):
    """Спільні поля внутрішніх сторінок: вступ і короткий опис для карток."""

    intro = models.TextField(
        "Вступ",
        blank=True,
        max_length=400,
        help_text="1–2 речення під заголовком: для кого сторінка і що тут можна дізнатися.",
    )

    content_panels = [*Page.content_panels, FieldPanel("intro")]
    search_fields = [*Page.search_fields, index.SearchField("intro")]

    class Meta:
        abstract = True

    @cached_property
    def body_items(self):
        """Блоки вмісту з унікальними якорями й рівнями заголовків (див. prepare_body)."""
        return prepare_body(getattr(self, "body", []))

    @property
    def summary(self):
        """Текст для карток у списках: опис для пошукових систем або вступ."""
        return self.search_description or self.intro

    def get_section(self):
        """Розділ верхнього рівня (дочірня сторінка головної), до якого належить сторінка."""
        if self.depth <= 3:
            return self if isinstance(self, SectionIndexPage) else None
        section = self.get_ancestors().filter(depth=3).specific().first()
        return section if isinstance(section, SectionIndexPage) else None


class SectionIndexPage(BasePage):
    """Лендинг розділу: вступ і картки дочірніх сторінок."""

    ACCENT_DEFAULT = "default"
    ACCENT_VETERAN = "veteran"

    accent = models.CharField(
        "Колірний акцент",
        max_length=20,
        choices=[
            (ACCENT_DEFAULT, "Основний (синій)"),
            (ACCENT_VETERAN, "Ветеранський (оливковий)"),
        ],
        default=ACCENT_DEFAULT,
    )
    body = StreamField(
        BodyStreamBlock(),
        verbose_name="Додатковий вміст",
        blank=True,
        use_json_field=True,
        help_text="Необов'язково: показується під картками підрозділів (наприклад, часті питання).",
    )

    content_panels = [
        *BasePage.content_panels,
        FieldPanel("accent"),
        FieldPanel("body"),
    ]
    search_fields = [*BasePage.search_fields, index.SearchField("body")]

    parent_page_types = ["home.HomePage", "pages.SectionIndexPage"]
    subpage_types = ["pages.SectionIndexPage", "pages.StandardPage"]

    class Meta:
        verbose_name = "Розділ (лендинг)"
        verbose_name_plural = "Розділи (лендинги)"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = self.get_children().live().public().specific()
        return context


class StandardPage(BasePage):
    """Звичайна текстова сторінка з конструктором вмісту."""

    body = StreamField(BodyStreamBlock(), verbose_name="Вміст", blank=True, use_json_field=True)
    show_toc = models.BooleanField(
        "Показувати «На цій сторінці»",
        default=True,
        help_text=f"Зміст зі посиланнями на заголовки H2; з'являється, якщо їх щонайменше "
        f"{TOC_MIN_HEADINGS}.",
    )

    content_panels = [*BasePage.content_panels, FieldPanel("body"), FieldPanel("show_toc")]
    search_fields = [*BasePage.search_fields, index.SearchField("body")]

    parent_page_types = ["home.HomePage", "pages.SectionIndexPage", "pages.StandardPage"]
    subpage_types = ["pages.StandardPage"]

    class Meta:
        verbose_name = "Текстова сторінка"
        verbose_name_plural = "Текстові сторінки"

    @property
    def toc(self):
        if not self.show_toc:
            return []
        entries = [
            {"id": extra["anchor"], "title": block.value["text"]}
            for block, extra in self.body_items
            if block.block_type == "heading" and block.value["level"] == "h2"
        ]
        return entries if len(entries) >= TOC_MIN_HEADINGS else []
