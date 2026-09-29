import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from apps.core.blocks import BodyStreamBlock, FaqItemBlock, LinkBlock, prepare_body

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
    subpage_types = [
        "pages.SectionIndexPage",
        "pages.StandardPage",
        "pages.ServicePage",
        "pages.ProgramPage",
        "organization.DirectoryPage",
    ]

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


RICH_FEATURES = ["bold", "italic", "ol", "ul", "link", "document-link"]
JSON_LD_ESCAPES = {ord("<"): "\\u003c", ord(">"): "\\u003e", ord("&"): "\\u0026"}


def json_ld(data):
    """JSON-LD для <script type="application/ld+json">: екрануємо <, > і &, як json_script."""
    return mark_safe(json.dumps(data, ensure_ascii=False).translate(JSON_LD_ESCAPES))  # noqa: S308


class ServicePage(BasePage):
    """Послуга: однакова структура для всіх послуг (хто має право, документи, куди звертатися…)."""

    eligibility = RichTextField(
        "Хто має право", blank=True, features=RICH_FEATURES, help_text="Категорії отримувачів."
    )
    required_documents = RichTextField(
        "Які документи потрібні",
        blank=True,
        features=RICH_FEATURES,
        help_text="Нумерований список документів.",
    )
    how_to_apply = RichTextField(
        "Як отримати",
        blank=True,
        features=RICH_FEATURES,
        help_text="Куди й як звернутися: особисто, поштою, через ЦНАП чи онлайн-сервіс.",
    )
    department = models.ForeignKey(
        "organization.Department",
        verbose_name="Відповідальний відділ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Контакти відділу показуються в картці «Куди звертатися».",
    )
    term = models.CharField(
        "Строк надання", max_length=150, blank=True, help_text="Напр. «10 робочих днів»."
    )
    cost = models.CharField("Вартість", max_length=150, blank=True, default="Безоплатно")
    legal_basis = StreamField(
        [("link", LinkBlock())],
        verbose_name="Підстави (нормативні акти)",
        blank=True,
        use_json_field=True,
    )
    forms = StreamField(
        [("document", DocumentChooserBlock(label="Документ"))],
        verbose_name="Бланки та зразки",
        blank=True,
        use_json_field=True,
        help_text="Бланки заяв і зразки. Назва документа в бібліотеці видна відвідувачам.",
    )
    faq = StreamField(
        [("item", FaqItemBlock())], verbose_name="Часті питання", blank=True, use_json_field=True
    )
    body = StreamField(
        BodyStreamBlock(),
        verbose_name="Додаткова інформація",
        blank=True,
        use_json_field=True,
        help_text="Необов'язково: показується перед підставами.",
    )

    content_panels = [
        *BasePage.content_panels,
        MultiFieldPanel(
            [FieldPanel("term"), FieldPanel("cost"), FieldPanel("department")],
            heading="Коротко про послугу",
        ),
        FieldPanel("eligibility"),
        FieldPanel("required_documents"),
        FieldPanel("forms"),
        FieldPanel("how_to_apply"),
        FieldPanel("body"),
        FieldPanel("legal_basis"),
        FieldPanel("faq"),
    ]
    search_fields = [
        *BasePage.search_fields,
        index.SearchField("eligibility"),
        index.SearchField("required_documents"),
        index.SearchField("how_to_apply"),
        index.SearchField("body"),
    ]

    parent_page_types = ["pages.SectionIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Послуга"
        verbose_name_plural = "Послуги"

    @property
    def toc(self):
        """Зміст за заповненими розділами (у тому ж порядку, що й на сторінці)."""
        sections = [
            ("who", _("Хто має право"), self.eligibility),
            ("documents", _("Які документи потрібні"), self.required_documents or self.forms),
            ("how", _("Як отримати"), self.how_to_apply or self.department_id),
            ("more", _("Додаткова інформація"), self.body),
            ("legal", _("Підстави"), self.legal_basis),
            ("faq", _("Часті питання"), self.faq),
        ]
        return [{"id": key, "title": title} for key, title, value in sections if value]

    @cached_property
    def body_items(self):
        # «Додаткова інформація» йде після розділів із H2, тож вкладені заголовки блоків — H3
        return [(block, {**extra, "heading_level": 3}) for block, extra in prepare_body(self.body)]

    def schema_org(self):
        data = {
            "@context": "https://schema.org",
            "@type": "GovernmentService",
            "name": self.title,
            "url": self.full_url,
            "provider": {
                "@type": "GovernmentOrganization",
                "name": "Управління соціальної та ветеранської політики Лубенської міської ради",
            },
        }
        if self.summary:
            data["description"] = self.summary
        return json_ld(data)


class ProgramPage(BasePage):
    """Місцева програма: період дії, мета, фінансування, документи й звіти про виконання."""

    STATUS_PLANNED = "planned"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_LABELS = {
        STATUS_PLANNED: "Запланована",
        STATUS_ACTIVE: "Діє",
        STATUS_COMPLETED: "Завершена",
    }

    start_year = models.PositiveSmallIntegerField("Рік початку")
    end_year = models.PositiveSmallIntegerField("Рік завершення")
    goal = RichTextField("Мета програми", blank=True, features=RICH_FEATURES)
    funding = models.CharField(
        "Обсяг фінансування",
        max_length=250,
        blank=True,
        help_text="Як у рішенні, напр. «1 250,0 тис. грн (бюджет громади)».",
    )
    responsible = models.ForeignKey(
        "organization.Department",
        verbose_name="Відповідальний виконавець",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    documents = StreamField(
        [("document", DocumentChooserBlock(label="Документ"))],
        verbose_name="Документи програми",
        blank=True,
        use_json_field=True,
        help_text="Рішення про затвердження, зміни, паспорт програми.",
    )
    reports = StreamField(
        [("document", DocumentChooserBlock(label="Звіт"))],
        verbose_name="Звіти про виконання",
        blank=True,
        use_json_field=True,
    )
    body = StreamField(BodyStreamBlock(), verbose_name="Опис", blank=True, use_json_field=True)

    content_panels = [
        *BasePage.content_panels,
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("start_year"), FieldPanel("end_year")]),
                FieldPanel("funding"),
                FieldPanel("responsible"),
            ],
            heading="Основні відомості",
        ),
        FieldPanel("goal"),
        FieldPanel("body"),
        FieldPanel("documents"),
        FieldPanel("reports"),
    ]
    search_fields = [
        *BasePage.search_fields,
        index.SearchField("goal"),
        index.SearchField("body"),
        index.FilterField("start_year"),
        index.FilterField("end_year"),
    ]

    parent_page_types = ["pages.SectionIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Програма"
        verbose_name_plural = "Програми"

    def clean(self):
        super().clean()
        if self.start_year and self.end_year and self.end_year < self.start_year:
            raise ValidationError(
                {"end_year": "Рік завершення не може бути раніше за рік початку."}
            )

    @property
    def status(self):
        """Статус за роками дії відносно поточного року — не потребує ручного оновлення."""
        year = timezone.localdate().year
        if year < self.start_year:
            return self.STATUS_PLANNED
        if year > self.end_year:
            return self.STATUS_COMPLETED
        return self.STATUS_ACTIVE

    @property
    def status_label(self):
        return self.STATUS_LABELS[self.status]

    @property
    def period(self):
        if self.start_year == self.end_year:
            return str(self.start_year)
        return f"{self.start_year}–{self.end_year}"
