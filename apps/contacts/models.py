from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.search import index

from apps.core.blocks import BodyStreamBlock, prepare_body
from apps.organization.models import Department, Person
from apps.pages.models import BasePage


class ContactPage(BasePage):
    """Контакти: основні дані з «Налаштувань сайту», особистий прийом керівництва, відділи."""

    how_to_apply = StreamField(
        BodyStreamBlock(),
        verbose_name="Як звернутися",
        blank=True,
        use_json_field=True,
        help_text="Способи звернення (особисто, письмово, електронною поштою) і вимоги до звернень "
        "згідно із ЗУ «Про звернення громадян». Онлайн-форм на сайті немає.",
    )
    show_leadership = models.BooleanField("Показувати особистий прийом керівництва", default=True)
    show_departments = models.BooleanField("Показувати контакти відділів", default=True)

    content_panels = [
        *BasePage.content_panels,
        FieldPanel("how_to_apply"),
        MultiFieldPanel(
            [FieldPanel("show_leadership"), FieldPanel("show_departments")],
            heading="Довідники на сторінці",
            help_text="Адреса, телефони й графік беруться з «Налаштувань сайту», керівництво й "
            "відділи — з розділу «Структура».",
        ),
    ]
    search_fields = [*BasePage.search_fields, index.SearchField("how_to_apply")]

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count_per_parent = 1

    class Meta:
        verbose_name = "Контакти"
        verbose_name_plural = "Сторінки контактів"

    @property
    def body_items(self):
        # Розділ «Як звернутися» має власний H2, тож заголовки всередині — H3
        return [
            (block, {**extra, "heading_level": 3})
            for block, extra in prepare_body(self.how_to_apply)
        ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        if self.show_leadership:
            context["leaders"] = Person.objects.filter(
                locale=self.locale, is_leadership=True
            ).select_related("photo")
        if self.show_departments:
            context["departments"] = Department.objects.filter(locale=self.locale)
        return context
