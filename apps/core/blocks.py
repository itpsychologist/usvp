"""Спільні StreamField-блоки. Нові типи сторінок беруть BodyStreamBlock, а не одноразові блоки.

Шаблони блоків — у templates/blocks/ і спираються на компоненти UI-кіту з templates/components/.
"""

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from wagtail import blocks
from wagtail.blocks.stream_block import StreamBlockValidationError
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageBlock

ICON_CHOICES = [
    ("shield", "Щит (ветерани)"),
    ("home", "Дім (житло, ВПО)"),
    ("heart", "Серце (соціальні послуги)"),
    ("percent", "Відсоток (пільги)"),
    ("activity", "Пульс (реабілітація)"),
    ("clock", "Годинник (графік)"),
    ("phone", "Телефон (контакти)"),
    ("landmark", "Будівля (публічна інформація)"),
    ("users", "Люди"),
    ("file-text", "Документ"),
    ("calendar", "Календар"),
    ("megaphone", "Гучномовець (оголошення)"),
    ("newspaper", "Газета (новини)"),
    ("info", "Інформація"),
]


class LinkStructValue(blocks.StructValue):
    """Посилання блоку. Метод зветься href, бо ключ url у StructValue (словнику) шаблон
    знайде раніше за метод і поверне порожнє поле."""

    def href(self):
        page = self.get("page")
        if page:
            return page.localized.url
        return self.get("url") or ""


def validate_page_or_url(value):
    """Рівно одне з двох: внутрішня сторінка або зовнішнє посилання."""
    if bool(value.get("page")) == bool(value.get("url")):
        message = "Оберіть сторінку сайту або вкажіть зовнішнє посилання (одне з двох)."
        raise StructBlockValidationError(
            block_errors={"page": ValidationError(message), "url": ValidationError(message)}
        )


class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(label="Текст заголовка", max_length=120)
    level = blocks.ChoiceBlock(
        label="Рівень",
        choices=[("h2", "Заголовок розділу (H2)"), ("h3", "Підзаголовок (H3)")],
        default="h2",
        help_text="H3 використовуйте лише всередині розділу з H2, щоб не порушувати структуру.",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        # Унікальний якір передає prepare_body(); без нього — якір із тексту
        if not context.get("anchor"):
            context["anchor"] = heading_anchor(value["text"])
        return context

    class Meta:
        icon = "title"
        label = "Заголовок"
        template = "blocks/heading.html"


def heading_anchor(text):
    """Якір для «На цій сторінці»: кирилиця допустима в id та в адресі (#…)."""
    return slugify(text, allow_unicode=True) or "rozdil"


class ParagraphBlock(blocks.RichTextBlock):
    class Meta:
        icon = "pilcrow"
        label = "Текст"
        template = "blocks/paragraph.html"


class ImageWithCaptionBlock(blocks.StructBlock):
    image = ImageBlock(
        label="Зображення",
        help_text="Альтернативний текст обов'язковий: опишіть, що зображено і навіщо це "
        "на сторінці. Позначте як декоративне, лише якщо зображення не несе змісту.",
    )
    caption = blocks.CharBlock(label="Підпис", required=False, max_length=250)

    class Meta:
        icon = "image"
        label = "Зображення"
        template = "blocks/image.html"


class DocumentsBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        label="Заголовок списку",
        required=False,
        max_length=120,
        help_text="Показується як заголовок (H2 або H3 залежно від місця на сторінці).",
    )
    documents = blocks.ListBlock(
        DocumentChooserBlock(label="Документ"), label="Документи", min_num=1
    )

    class Meta:
        icon = "doc-full"
        label = "Документи"
        template = "blocks/documents.html"
        help_text = "Назва документа в бібліотеці показується відвідувачам — пишіть її зрозуміло."


class FaqItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(label="Питання", max_length=250)
    answer = blocks.RichTextBlock(
        label="Відповідь", features=["bold", "italic", "ol", "ul", "link", "document-link"]
    )


class AccordionBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        label="Заголовок блоку",
        required=False,
        max_length=120,
        help_text="Наприклад, «Часті питання».",
    )
    items = blocks.ListBlock(FaqItemBlock(label="Питання"), label="Питання й відповіді", min_num=1)

    class Meta:
        icon = "list-ul"
        label = "Акордеон / FAQ"
        template = "blocks/accordion.html"


class TableBlock(blocks.StructBlock):
    caption = blocks.CharBlock(
        label="Назва таблиці",
        max_length=200,
        help_text="Обов'язково: назва допомагає користувачам скрінрідерів зрозуміти таблицю.",
    )
    table = TypedTableBlock(
        [
            ("text", blocks.CharBlock(label="Текст")),
            ("number", blocks.DecimalBlock(label="Число")),
            (
                "rich_text",
                blocks.RichTextBlock(label="Текст із посиланнями", features=["bold", "link"]),
            ),
        ],
        label="Таблиця",
    )

    class Meta:
        icon = "table"
        label = "Таблиця"
        template = "blocks/table.html"


class CalloutBlock(blocks.StructBlock):
    variant = blocks.ChoiceBlock(
        label="Тип",
        choices=[
            ("info", "Інформація"),
            ("success", "Успіх / підтвердження"),
            ("warning", "Увага"),
            ("danger", "Важливе попередження"),
        ],
        default="info",
    )
    title = blocks.CharBlock(label="Заголовок", required=False, max_length=120)
    text = blocks.TextBlock(label="Текст")

    class Meta:
        icon = "warning"
        label = "Виділений блок"
        template = "blocks/callout.html"


class ContactCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Назва (відділ, посада)", max_length=150)
    address = blocks.CharBlock(label="Адреса", required=False, max_length=250)
    room = blocks.CharBlock(label="Кабінет", required=False, max_length=50)
    phone = blocks.CharBlock(
        label="Телефон",
        required=False,
        max_length=30,
        help_text="Як показувати, напр. (05361) 7-00-00",
    )
    email = blocks.EmailBlock(label="Електронна пошта", required=False)
    hours = blocks.CharBlock(label="Години прийому", required=False, max_length=200)

    class Meta:
        icon = "user"
        label = "Контактна картка"
        template = "blocks/contact_card.html"


class ButtonLinkBlock(blocks.StructBlock):
    text = blocks.CharBlock(
        label="Текст кнопки",
        max_length=60,
        help_text="Має бути зрозумілим без контексту: «Завантажити бланк заяви», а не «Тут».",
    )
    page = blocks.PageChooserBlock(label="Сторінка сайту", required=False)
    url = blocks.URLBlock(label="Або зовнішнє посилання", required=False)
    style = blocks.ChoiceBlock(
        label="Вигляд",
        choices=[("primary", "Основна кнопка"), ("secondary", "Другорядна кнопка")],
        default="primary",
    )

    def clean(self, value):
        value = super().clean(value)
        validate_page_or_url(value)
        return value

    class Meta:
        icon = "link"
        label = "Кнопка-посилання"
        template = "blocks/button_link.html"
        value_class = LinkStructValue


class BodyStreamBlock(blocks.StreamBlock):
    """Конструктор вмісту сторінки. Для рендеру використовуйте prepare_body(): унікальні якорі
    заголовків і правильний рівень заголовків у картках, акордеонах і списках документів."""

    heading = HeadingBlock()
    paragraph = ParagraphBlock()
    image = ImageWithCaptionBlock()
    documents = DocumentsBlock()
    accordion = AccordionBlock()
    table = TableBlock()
    callout = CalloutBlock()
    contact_card = ContactCardBlock()
    button = ButtonLinkBlock()

    def clean(self, value):
        value = super().clean(value)
        # Структура заголовків (WCAG 1.3.1): перший заголовок сторінки після H1 — лише H2
        for child in value:
            if child.block_type == "heading":
                if child.value["level"] == "h3":
                    raise StreamBlockValidationError(
                        non_block_errors=ValidationError(
                            "Перший заголовок у вмісті має бути «Заголовок розділу (H2)»: "
                            "підзаголовок H3 можна ставити лише після H2."
                        )
                    )
                break
        return value


# Id, які вже використовує шаблон сторінки: якорі заголовків не повинні з ними збігатися
RESERVED_IDS = {"top", "main", "page-toc-title", "section-nav-title", "a11y-panel", "mobile-menu"}


def prepare_body(stream):
    """Готує StreamField до рендеру: [(блок, додатковий контекст)].

    - anchor — унікальний якір заголовка (однакові заголовки отримують суфікс -2, -3…);
    - heading_level — рівень заголовка для вкладених блоків (контактна картка, акордеон,
      документи): 2, поки на сторінці не було H2, далі 3.
    """
    seen = set(RESERVED_IDS)
    has_h2 = False
    items = []
    for block in stream:
        extra = {"anchor": None, "heading_level": 3 if has_h2 else 2}
        if block.block_type == "heading":
            base = heading_anchor(block.value["text"])
            anchor, suffix = base, 2
            while anchor in seen:
                anchor, suffix = f"{base}-{suffix}", suffix + 1
            seen.add(anchor)
            extra["anchor"] = anchor
            has_h2 = has_h2 or block.value["level"] == "h2"
        items.append((block, extra))
    return items


class TaskTileBlock(blocks.StructBlock):
    """Плитка «Що вам потрібно?» на головній."""

    title = blocks.CharBlock(label="Назва", max_length=60)
    text = blocks.CharBlock(label="Короткий опис", required=False, max_length=80)
    icon = blocks.ChoiceBlock(label="Іконка", choices=ICON_CHOICES, default="info")
    page = blocks.PageChooserBlock(label="Сторінка сайту", required=False)
    url = blocks.URLBlock(label="Або зовнішнє посилання", required=False)
    veteran = blocks.BooleanBlock(
        label="Ветеранський акцент", required=False, help_text="Оливковий колір іконки."
    )

    def clean(self, value):
        value = super().clean(value)
        validate_page_or_url(value)
        return value

    class Meta:
        icon = "grip"
        label = "Плитка"
        value_class = LinkStructValue


class PhoneBlock(blocks.StructBlock):
    label = blocks.CharBlock(
        label="Підпис", required=False, max_length=80, help_text="Напр. «Приймальня»"
    )
    number = blocks.CharBlock(
        label="Номер", max_length=30, help_text="Як показувати: (05361) 7-00-00"
    )

    class Meta:
        icon = "mobile-alt"
        label = "Телефон"


class ScheduleRowBlock(blocks.StructBlock):
    days = blocks.CharBlock(label="Дні", max_length=60, help_text="Напр. «Понеділок – четвер»")
    hours = blocks.CharBlock(label="Години", max_length=60, help_text="Напр. «08:00 – 17:15»")

    class Meta:
        icon = "time"
        label = "Рядок графіка"
