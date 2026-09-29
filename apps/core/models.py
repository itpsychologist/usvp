from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Locale, Orderable, TranslatableMixin

from apps.core.blocks import PhoneBlock, ScheduleRowBlock


def validate_image_description(image, field_name):
    """Wagtail бере alt зображення з «Опису», а без нього — з назви файлу. Для змістовних фото
    (обкладинка новини, фото простору) опис обов'язковий (WCAG 1.1.1)."""
    if image is not None and not (image.description or "").strip():
        raise ValidationError(
            {
                field_name: "Заповніть «Опис» зображення в бібліотеці (Зображення → редагувати): "
                "він стане альтернативним текстом для людей, які не бачать фото."
            }
        )


class TranslatableSnippet(TranslatableMixin, models.Model):
    """База для перекладних snippets: без явно заданої мови запис створюється основною мовою."""

    class Meta(TranslatableMixin.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        if self.locale_id is None:
            self.locale = Locale.get_default()
        super().save(*args, **kwargs)


@register_setting(icon="site")
class SiteSettings(BaseSiteSetting):
    """Контакти, графік і службові налаштування, що показуються в шапці, футері та на головній."""

    address = models.CharField(
        "Адреса",
        max_length=250,
        blank=True,
        help_text="Повна адреса з індексом, напр. «вул. …, 1, м. Лубни, Полтавська обл., 37500».",
    )
    email = models.EmailField("Електронна пошта", blank=True)
    phones = StreamField(
        [("phone", PhoneBlock())], verbose_name="Телефони", blank=True, use_json_field=True
    )
    schedule = StreamField(
        [("row", ScheduleRowBlock())],
        verbose_name="Графік роботи",
        blank=True,
        use_json_field=True,
        help_text="Кожен рядок — дні та години, включно з обідньою перервою й вихідними.",
    )

    map_url = models.URLField(
        "Посилання на Google Maps", blank=True, help_text="Лише посилання, без вбудованої карти."
    )
    facebook_url = models.URLField("Сторінка у Facebook", blank=True)
    council_url = models.URLField("Сайт Лубенської міської ради", blank=True)

    emblem = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Герб",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="PNG або WebP із прозорим фоном, висотою від 96 px. Поки не задано, показується "
        "тимчасова заглушка.",
    )
    content_license = models.CharField(
        "Ліцензія на матеріали сайту",
        max_length=250,
        blank=True,
        help_text="Рядок у футері, напр. «Матеріали сайту доступні за ліцензією CC BY 4.0, "
        "якщо не зазначено інше». Порожньо — рядок не показується.",
    )

    alert_enabled = models.BooleanField("Показувати термінове оголошення", default=False)
    alert_text = models.CharField(
        "Текст оголошення",
        max_length=200,
        blank=True,
        help_text="Одне коротке речення. Показується жовтим банером над шапкою на всіх сторінках.",
    )
    alert_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Сторінка з деталями",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("address"),
                FieldPanel("email"),
                FieldPanel("phones"),
                FieldPanel("schedule"),
            ],
            heading="Контакти й графік",
        ),
        MultiFieldPanel(
            [FieldPanel("map_url"), FieldPanel("facebook_url"), FieldPanel("council_url")],
            heading="Зовнішні посилання",
        ),
        MultiFieldPanel(
            [FieldPanel("emblem"), FieldPanel("content_license")],
            heading="Айдентика й ліцензія",
        ),
        MultiFieldPanel(
            [FieldPanel("alert_enabled"), FieldPanel("alert_text"), FieldPanel("alert_page")],
            heading="Термінове оголошення",
        ),
    ]

    class Meta:
        verbose_name = "Налаштування сайту"

    def clean(self):
        super().clean()
        if self.alert_enabled and not self.alert_text:
            raise ValidationError({"alert_text": "Вкажіть текст, щоб увімкнути оголошення."})


class NavigationMenu(TranslatableMixin, ClusterableModel):
    """Головне меню й меню футера. Для кожної мови — окремий переклад меню."""

    MAIN = "main"
    FOOTER = "footer"
    LOCATIONS = [(MAIN, "Головне меню (шапка)"), (FOOTER, "Меню футера (службові сторінки)")]

    location = models.CharField("Розташування", max_length=20, choices=LOCATIONS)

    panels = [
        FieldPanel("location"),
        InlinePanel(
            "items",
            label="Пункт меню",
            heading="Пункти меню",
            help_text="Для головного меню підпункти беруться автоматично з дочірніх сторінок "
            "обраної сторінки, позначених «Показувати в меню».",
        ),
    ]

    class Meta(TranslatableMixin.Meta):
        verbose_name = "Меню"
        verbose_name_plural = "Меню"
        constraints = [
            models.UniqueConstraint(fields=["location", "locale"], name="unique_menu_per_locale")
        ]

    def __str__(self):
        return self.get_location_display()

    @classmethod
    def for_location(cls, location):
        """Меню активної мови; якщо його ще не перекладено — меню основної мови."""
        menus = cls.objects.filter(location=location).prefetch_related("items__page")
        menu = menus.filter(locale=Locale.get_active()).first()
        return menu or menus.filter(locale=Locale.get_default()).first()


class MenuItem(Orderable):
    menu = ParentalKey(NavigationMenu, related_name="items", on_delete=models.CASCADE)
    page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Сторінка",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="+",
    )
    url = models.URLField("Або зовнішнє посилання", blank=True)
    title = models.CharField(
        "Назва пункту",
        max_length=60,
        blank=True,
        help_text="Необов'язково для сторінки: типово береться назва сторінки.",
    )
    description = models.CharField(
        "Опис у мегаменю",
        max_length=150,
        blank=True,
        help_text="Одне речення про розділ, показується у спливному меню на комп'ютері.",
    )

    panels = [
        FieldRowPanel([FieldPanel("page"), FieldPanel("url")]),
        FieldPanel("title"),
        FieldPanel("description"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункти меню"

    def __str__(self):
        return self.display_title

    def clean(self):
        super().clean()
        if bool(self.page_id) == bool(self.url):
            raise ValidationError("Оберіть сторінку або вкажіть зовнішнє посилання (одне з двох).")
        if self.url and not self.title:
            raise ValidationError({"title": "Для зовнішнього посилання назва обов'язкова."})

    @property
    def display_title(self):
        if self.title:
            return self.title
        return self.page.title if self.page_id else self.url
