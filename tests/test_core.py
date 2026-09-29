import pytest
from django.core.exceptions import ValidationError
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.models import Locale, Site

from apps.core.blocks import ButtonLinkBlock
from apps.core.models import MenuItem, NavigationMenu, SiteSettings
from apps.core.templatetags.site_tags import tel_href
from tests.factories import SectionIndexPageFactory, StandardPageFactory, home_page, publish


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        ("(05361) 7-00-00", "+380536170000"),
        ("+380 50 123 45 67", "+380501234567"),
        ("", ""),
    ],
)
def test_tel_href(number, expected):
    assert tel_href(number) == expected


@pytest.fixture
def section():
    section = publish(SectionIndexPageFactory(parent=home_page()))
    StandardPageFactory(parent=section, title="Пільги", show_in_menus=True)
    StandardPageFactory(parent=section, title="Прихована", show_in_menus=False)
    return section


@pytest.fixture
def main_menu(section):
    menu = NavigationMenu.objects.create(location=NavigationMenu.MAIN, locale=Locale.get_default())
    MenuItem.objects.create(menu=menu, page=section, description="Опис розділу", sort_order=0)
    MenuItem.objects.create(
        menu=menu, url="https://example.gov.ua/", title="Міськрада", sort_order=1
    )
    return menu


def test_main_menu_in_header(client, main_menu, section):
    html = client.get("/").content.decode()

    assert 'aria-label="Головне меню"' in html
    assert "Опис розділу" in html
    assert "Пільги" in html  # дочірня сторінка з «Показувати в меню»
    assert "Прихована" not in html
    assert "Міськрада" in html


def test_main_menu_marks_active_section(client, main_menu, section):
    html = client.get(section.url).content.decode()
    assert "поточний розділ" in html


def test_footer_menu_and_settings(client, section):
    menu = NavigationMenu.objects.create(
        location=NavigationMenu.FOOTER, locale=Locale.get_default()
    )
    MenuItem.objects.create(menu=menu, page=section, title="Заява про доступність")
    settings = SiteSettings.for_site(Site.objects.get(is_default_site=True))
    settings.address = "вул. Тестова, 1, м. Лубни"
    settings.phones = [("phone", {"label": "Приймальня", "number": "(05361) 7-00-00"})]
    settings.schedule = [("row", {"days": "Пн–Пт", "hours": "08:00–17:00"})]
    settings.content_license = "Матеріали доступні за ліцензією CC BY 4.0"
    settings.save()

    html = client.get("/").content.decode()

    assert "вул. Тестова, 1, м. Лубни" in html
    assert 'href="tel:+380536170000"' in html
    assert "08:00–17:00" in html
    assert "Заява про доступність" in html
    assert "CC BY 4.0" in html


def test_alert_banner(client, section):
    settings = SiteSettings.for_site(Site.objects.get(is_default_site=True))
    settings.alert_text = "Змінено графік прийому"
    settings.alert_page = section
    settings.save()
    assert "Змінено графік прийому" not in client.get("/").content.decode()

    settings.alert_enabled = True
    settings.save()
    html = client.get("/").content.decode()
    assert "Змінено графік прийому" in html
    assert 'aria-label="Термінове оголошення"' in html


def test_alert_requires_text():
    settings = SiteSettings(site=Site.objects.get(is_default_site=True), alert_enabled=True)
    with pytest.raises(ValidationError):
        settings.clean()


def test_menu_item_requires_exactly_one_target(section):
    with pytest.raises(ValidationError):
        MenuItem(title="Порожній").clean()
    with pytest.raises(ValidationError):
        MenuItem(page=section, url="https://example.gov.ua/").clean()
    with pytest.raises(ValidationError):
        MenuItem(url="https://example.gov.ua/").clean()  # без назви
    MenuItem(page=section).clean()


def test_button_block_requires_page_or_url(section):
    block = ButtonLinkBlock()
    with pytest.raises(StructBlockValidationError):
        block.clean(block.to_python({"text": "Кнопка", "style": "primary"}))
    value = block.clean(block.to_python({"text": "Кнопка", "url": "https://example.gov.ua/"}))
    assert value.href() == "https://example.gov.ua/"


def test_menu_is_unique_per_locale():
    from django.db import IntegrityError

    NavigationMenu.objects.create(location=NavigationMenu.MAIN, locale=Locale.get_default())
    with pytest.raises(IntegrityError):
        NavigationMenu.objects.create(location=NavigationMenu.MAIN, locale=Locale.get_default())


def test_menu_hides_unpublished_and_private_pages(client, section):
    from wagtail.models import PageViewRestriction

    draft = StandardPageFactory(parent=home_page(), title="Чернетка розділу", live=False)
    private = publish(StandardPageFactory(parent=home_page(), title="Закритий розділ"))
    PageViewRestriction.objects.create(page=private, restriction_type="password", password="x")
    menu = NavigationMenu.objects.create(location=NavigationMenu.MAIN, locale=Locale.get_default())
    for order, page in enumerate((section, draft, private)):
        MenuItem.objects.create(menu=menu, page=page, sort_order=order)

    html = client.get("/").content.decode()

    assert section.title in html
    assert "Чернетка розділу" not in html
    assert "Закритий розділ" not in html


def test_menu_is_cached_and_invalidated_on_publish(
    client, main_menu, section, django_assert_max_num_queries
):
    client.get("/")  # заповнює кеш
    with django_assert_max_num_queries(12):
        client.get("/")

    new_child = StandardPageFactory(parent=section, title="Нова послуга", show_in_menus=True)
    publish(new_child)
    assert "Нова послуга" in client.get("/").content.decode()
