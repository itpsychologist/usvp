import json
import re

import pytest
from wagtail.documents import get_document_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTestCase

from apps.contacts.models import ContactPage
from apps.home.models import HomePage
from apps.news.models import AnnouncementIndexPage, AnnouncementPage, NewsIndexPage, NewsPage
from apps.organization.models import DirectoryPage
from apps.pages.models import ProgramPage, SectionIndexPage, ServicePage, StandardPage
from tests.factories import (
    SectionIndexPageFactory,
    StandardPageFactory,
    home_page,
    publish,
)


class TestPageHierarchy(WagtailPageTestCase):
    def test_home_children(self):
        self.assertAllowedSubpageTypes(
            HomePage,
            {SectionIndexPage, StandardPage, NewsIndexPage, AnnouncementIndexPage, ContactPage},
        )

    def test_section_children(self):
        self.assertAllowedSubpageTypes(
            SectionIndexPage,
            {SectionIndexPage, StandardPage, ServicePage, ProgramPage, DirectoryPage},
        )

    def test_leaf_pages(self):
        for model in (ServicePage, ProgramPage, DirectoryPage, ContactPage):
            self.assertAllowedSubpageTypes(model, set())
        self.assertAllowedSubpageTypes(NewsIndexPage, {NewsPage})
        self.assertAllowedSubpageTypes(AnnouncementIndexPage, {AnnouncementPage})
        self.assertCanNotCreateAt(HomePage, ServicePage)
        self.assertCanNotCreateAt(SectionIndexPage, NewsPage)

    def test_standard_page_children(self):
        self.assertAllowedSubpageTypes(StandardPage, {StandardPage})

    def test_section_cannot_be_created_at_root(self):
        self.assertCanNotCreateAt(Page, SectionIndexPage)
        self.assertCanNotCreateAt(StandardPage, SectionIndexPage)


def raw_stream(blocks):
    """StreamField у форматі БД (JSON з ID), щоб не створювати об'єкти для кожного блоку."""
    return json.dumps([{"type": block_type, "value": value} for block_type, value in blocks])


def h1_count(html):
    return len(re.findall(r"<h1[\s>]", html))


@pytest.fixture
def section():
    return publish(
        SectionIndexPageFactory(
            parent=home_page(), intro="Вступ до розділу", accent=SectionIndexPage.ACCENT_VETERAN
        )
    )


def test_section_page_lists_children(client, section):
    StandardPageFactory(parent=section, title="Питання статусу", intro="Опис для картки")
    StandardPageFactory(parent=section, title="Чернетка", live=False)

    html = client.get(section.url).content.decode()

    assert h1_count(html) == 1
    assert "Питання статусу" in html
    assert "Опис для картки" in html
    assert "Чернетка" not in html
    assert "bg-veteran-100" in html
    assert 'aria-label="Хлібні крихти"' in html


def test_standard_page_renders_all_blocks(client, section):
    image = get_image_model_instance()
    document = get_document_model().objects.create(
        title="Зразок заяви", file=get_test_image_file(filename="zrazok.png")
    )
    body = [
        ("heading", {"text": "Хто має право", "level": "h2"}),
        ("paragraph", "<p>Звичайний текст</p>"),
        ("heading", {"text": "Які документи", "level": "h2"}),
        ("image", {"image": {"image": image.pk, "alt_text": "Опис фото", "decorative": False}}),
        ("documents", {"title": "Бланки", "documents": [document.pk]}),
        ("heading", {"text": "Куди звертатися", "level": "h2"}),
        (
            "accordion",
            {"title": "Часті питання", "items": [{"question": "Питання?", "answer": "<p>Так</p>"}]},
        ),
        (
            "table",
            {
                "caption": "Графік",
                "table": {
                    "columns": [{"type": "text", "heading": "День"}],
                    "rows": [{"values": ["Понеділок"]}],
                },
            },
        ),
        ("callout", {"variant": "warning", "title": "Увага", "text": "Візьміть паспорт"}),
        ("contact_card", {"title": "Відділ", "phone": "(05361) 7-00-00", "email": "a@b.ua"}),
        ("button", {"text": "Детальніше", "page": section.pk, "url": "", "style": "primary"}),
    ]
    page = publish(StandardPageFactory(parent=section, body=raw_stream(body)))

    response = client.get(page.url)
    html = response.content.decode()

    assert response.status_code == 200
    assert h1_count(html) == 1
    assert 'id="хто-має-право"' in html
    assert "На цій сторінці" in html  # три заголовки H2 → є зміст
    assert 'alt="Опис фото"' in html
    assert "Зразок заяви" in html
    assert '<caption id="tablytsia-графік">Графік</caption>' in html
    assert 'aria-labelledby="tablytsia-графік"' in html
    assert 'href="tel:+380536170000"' in html
    assert f'href="{section.url}"' in html
    assert 'aria-current="page"' in html  # бокова навігація розділу
    assert "Сторінку оновлено" in html
    assert 'class="block-' not in html  # блоки без обгорток, щоб діяли стилі .prose-site


def test_toc_hidden_with_few_headings(client, section):
    page = publish(
        StandardPageFactory(parent=section, body=[("heading", {"text": "Один", "level": "h2"})])
    )
    assert "На цій сторінці" not in client.get(page.url).content.decode()


def test_standard_page_is_searchable(section):
    StandardPageFactory(parent=section, title="Реабілітація ветеранів", intro="Унікальнийвступ")
    results = StandardPage.objects.live().search("Унікальнийвступ")
    assert [p.title for p in results] == ["Реабілітація ветеранів"]


def test_homepage_renders_tiles_and_featured(client, section):
    home = home_page()
    home.hero_text = "Допомагаємо мешканцям громади"
    home.tiles = raw_stream(
        [("tile", {"title": "Ветеранам", "icon": "shield", "page": section.pk, "veteran": True})]
    )
    home.featured_pages = raw_stream([("page", section.pk)])
    publish(home)

    html = client.get("/").content.decode()

    assert h1_count(html) == 1
    assert "Допомагаємо мешканцям громади" in html
    assert "Що вам потрібно?" in html
    assert "Ключові послуги та програми" in html
    assert html.count(section.url) >= 2


def get_image_model_instance():
    from wagtail.images import get_image_model

    return get_image_model().objects.create(title="Фото", file=get_test_image_file())


def test_duplicate_headings_get_unique_anchors(client, section):
    body = [("heading", {"text": "Документи", "level": "h2"})] * 3
    page = publish(StandardPageFactory(parent=section, body=raw_stream(body)))
    html = client.get(page.url).content.decode()

    for anchor in ("документи", "документи-2", "документи-3"):
        assert f'id="{anchor}"' in html
        assert f'href="#{anchor}"' in html


def test_nested_headings_follow_page_structure(client, section):
    card = {"title": "Відділ", "phone": "", "email": ""}
    body = [
        ("contact_card", card),  # до першого H2 — заголовок картки H2
        ("heading", {"text": "Розділ", "level": "h2"}),
        ("contact_card", card),  # після H2 — H3
        (
            "accordion",
            {"title": "Часті питання", "items": [{"question": "?", "answer": "<p>!</p>"}]},
        ),
    ]
    page = publish(StandardPageFactory(parent=section, body=raw_stream(body)))
    html = client.get(page.url).content.decode()

    assert re.search(r"<h2[^>]*>\s*Відділ", html)
    assert re.search(r"<h3[^>]*>\s*Відділ", html)
    assert re.search(r"<h3[^>]*>\s*Часті питання", html)


def test_body_cannot_start_with_h3():
    from django.core.exceptions import ValidationError

    from apps.core.blocks import BodyStreamBlock

    block = BodyStreamBlock()
    value = block.to_python([{"type": "heading", "value": {"text": "Підрозділ", "level": "h3"}}])
    with pytest.raises(ValidationError):
        block.clean(value)
    ok = block.to_python(
        [
            {"type": "heading", "value": {"text": "Розділ", "level": "h2"}},
            {"type": "heading", "value": {"text": "Підрозділ", "level": "h3"}},
        ]
    )
    block.clean(ok)


def test_section_nav_follows_article_in_dom(client, section):
    page = publish(StandardPageFactory(parent=section))
    StandardPageFactory(parent=section, title="Сусідня")
    html = client.get(page.url).content.decode()
    assert html.index("<article") < html.index("<aside")


def test_summary_prefers_search_description(section):
    page = StandardPageFactory(parent=section, intro="Вступ", search_description="Опис для пошуку")
    assert page.summary == "Опис для пошуку"
    page.search_description = ""
    assert page.summary == "Вступ"
