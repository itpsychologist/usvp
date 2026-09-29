"""Фаза 3: послуги, програми, довідники, новини, оголошення, контакти."""

import datetime
import json
import re

import pytest
import wagtail_factories
from django.core.exceptions import ValidationError
from django.utils import timezone
from wagtail.documents import get_document_model
from wagtail.images.tests.utils import get_test_image_file

from apps.contacts.models import ContactPage
from apps.news.models import (
    AnnouncementIndexPage,
    AnnouncementPage,
    NewsIndexPage,
    NewsPage,
    NewsTopic,
)
from apps.organization.models import (
    Department,
    DirectoryPage,
    Person,
    VeteranSpace,
    VeteranSpecialist,
)
from apps.pages.models import ProgramPage, ServicePage
from tests.factories import SectionIndexPageFactory, home_page, publish


def raw_stream(blocks):
    return json.dumps([{"type": block_type, "value": value} for block_type, value in blocks])


def h1_count(html):
    return len(re.findall(r"<h1[\s>]", html))


def factory(model):
    return type(
        f"{model.__name__}Factory",
        (wagtail_factories.PageFactory,),
        {"Meta": type("Meta", (), {"model": model})},
    )


@pytest.fixture
def section():
    return publish(SectionIndexPageFactory(parent=home_page(), title="Соціальний напрямок"))


@pytest.fixture
def department():
    return Department.objects.create(
        name="Відділ соціальних виплат", phone="(05361) 7-11-11", email="vyplaty@example.gov.ua"
    )


# --- Послуги -----------------------------------------------------------------------------


def test_service_page_renders_structured_sections(client, section, department):
    document = get_document_model().objects.create(
        title="Заява на допомогу", file=get_test_image_file(filename="zayava.png")
    )
    page = publish(
        factory(ServicePage)(
            parent=section,
            title="Допомога на поховання",
            intro="Для родин загиблих",
            eligibility="<p>Члени родини</p>",
            required_documents="<ol><li>Паспорт</li></ol>",
            how_to_apply="<p>Особисто у відділі</p>",
            department=department,
            term="10 робочих днів",
            forms=raw_stream([("document", document.pk)]),
            legal_basis=raw_stream(
                [("link", {"title": "Закон про соцзахист", "url": "https://zakon.rada.gov.ua/"})]
            ),
            faq=raw_stream([("item", {"question": "Скільки чекати?", "answer": "<p>10 днів</p>"})]),
        )
    )

    html = client.get(page.url).content.decode()

    assert h1_count(html) == 1
    for text in (
        "10 робочих днів",
        "Безоплатно",
        'id="who"',
        'id="documents"',
        'id="how"',
        'id="legal"',
        'id="faq"',
        "Заява на допомогу",
        "Відділ соціальних виплат",
        'href="tel:+380536171111"',
        "https://zakon.rada.gov.ua/",
        "Скільки чекати?",
        "На цій сторінці",
    ):
        assert text in html, text
    # schema.org GovernmentService
    data = json.loads(
        re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1]
    )
    assert data["@type"] == "GovernmentService"
    assert data["name"] == "Допомога на поховання"


def test_service_json_ld_is_escaped(section):
    page = factory(ServicePage)(parent=section, title="</script><script>alert(1)</script>")
    assert "</script>" not in page.schema_org()


def test_empty_service_sections_are_hidden(client, section):
    page = publish(factory(ServicePage)(parent=section, title="Порожня послуга", cost=""))
    html = client.get(page.url).content.decode()
    assert 'id="who"' not in html
    assert "На цій сторінці" not in html


# --- Програми ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "status"),
    [(-1, 1, "active"), (1, 2, "planned"), (-3, -1, "completed")],
)
def test_program_status_follows_years(section, start, end, status):
    year = timezone.localdate().year
    page = ProgramPage(title="Програма", start_year=year + start, end_year=year + end)
    assert page.status == status


def test_program_page_renders(client, section, department):
    year = timezone.localdate().year
    page = publish(
        factory(ProgramPage)(
            parent=section,
            title="Програма підтримки ветеранів",
            start_year=year,
            end_year=year + 2,
            funding="1 000,0 тис. грн",
            responsible=department,
            goal="<p>Мета програми</p>",
        )
    )
    html = client.get(page.url).content.decode()
    assert f"{year}–{year + 2}" in html
    assert "Діє" in html
    assert "1 000,0 тис. грн" in html
    assert "Відділ соціальних виплат" in html


def test_program_end_year_validation():
    with pytest.raises(ValidationError):
        ProgramPage(title="Програма", slug="p", start_year=2026, end_year=2025).clean()


# --- Довідники ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", [k for k, _ in DirectoryPage.KINDS])
def test_directory_pages_render(client, section, department, kind):
    Person.objects.create(name="Іваненко Іван", position="Начальник", is_leadership=True)
    Person.objects.create(name="Петренко Петро", position="Спеціаліст", department=department)
    VeteranSpecialist.objects.create(name="Коваленко Олена", territory="Лубни", phone="0501234567")
    VeteranSpace.objects.create(name="Простір «Ветеран»", address="вул. Тестова, 2")
    page = publish(factory(DirectoryPage)(parent=section, title="Довідник", kind=kind))

    html = client.get(page.url).content.decode()

    assert h1_count(html) == 1
    expected = {
        DirectoryPage.LEADERSHIP: "Іваненко Іван",
        DirectoryPage.DEPARTMENTS: "Петренко Петро",
        DirectoryPage.SPECIALISTS: "Коваленко Олена",
        DirectoryPage.SPACES: "Простір «Ветеран»",
    }[kind]
    assert expected in html
    if kind == DirectoryPage.LEADERSHIP:
        assert "Петренко Петро" not in html  # не керівництво


def test_empty_directory_shows_placeholder(client, section):
    page = publish(factory(DirectoryPage)(parent=section, kind=DirectoryPage.SPACES))
    assert "Інформація готується до оприлюднення" in client.get(page.url).content.decode()


def test_snippets_default_to_default_locale():
    department = Department.objects.create(name="Відділ")
    assert department.locale.language_code == "uk"


# --- Новини ------------------------------------------------------------------------------


@pytest.fixture
def news_index():
    return publish(factory(NewsIndexPage)(parent=home_page(), title="Новини", slug="novyny"))


def make_news(index, title, date, topics=()):
    page = factory(NewsPage)(
        parent=index,
        title=title,
        date=date,
        intro=f"Лід: {title}",
        body=raw_stream([("paragraph", "<p>Текст</p>")]),
    )
    page.topics.set(topics)
    return publish(page)


def test_news_index_filters_by_year_and_topic(client, news_index):
    veterans = NewsTopic.objects.create(name="Ветеранам", slug="veteranam")
    make_news(news_index, "Новина 2025", datetime.date(2025, 5, 1))
    make_news(news_index, "Новина для ветеранів", datetime.date(2026, 5, 1), [veterans])
    make_news(news_index, "Інша новина 2026", datetime.date(2026, 6, 1))

    html = client.get(news_index.url).content.decode()
    assert all(t in html for t in ("Новина 2025", "Новина для ветеранів", "Інша новина 2026"))
    assert "Знайдено новин: 3" in html

    html = client.get(news_index.url, {"year": "2025"}).content.decode()
    assert "Новина 2025" in html and "Інша новина 2026" not in html

    html = client.get(news_index.url, {"topic": "veteranam"}).content.decode()
    assert "Новина для ветеранів" in html and "Інша новина 2026" not in html
    assert "Скинути фільтри" in html


def test_news_pagination(client, news_index):
    for i in range(14):
        make_news(news_index, f"Новина {i:02}", datetime.date(2026, 1, 1) + datetime.timedelta(i))

    first = client.get(news_index.url).content.decode()
    second = client.get(news_index.url, {"page": 2}).content.decode()

    assert 'aria-current="page"' in first
    assert "Новина 13" in first and "Новина 00" not in first
    assert "Новина 00" in second
    assert client.get(news_index.url, {"page": "999"}).status_code == 200


def test_news_rss(client, news_index):
    make_news(news_index, "Новина в RSS", datetime.date(2026, 9, 1))
    response = client.get(f"{news_index.url}rss/")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/rss+xml")
    assert "Новина в RSS" in response.content.decode()


def test_news_page_shows_cover_and_related(client, news_index):
    image = wagtail_factories.ImageFactory(file__from_path=None, description="Учасники зустрічі")
    news = make_news(news_index, "Головна новина", datetime.date(2026, 9, 2))
    news.cover = image
    publish(news)
    make_news(news_index, "Сусідня новина", datetime.date(2026, 9, 1))

    html = client.get(news.url).content.decode()

    assert 'alt="Учасники зустрічі"' in html
    assert "Інші новини" in html and "Сусідня новина" in html


# --- Оголошення --------------------------------------------------------------------------


@pytest.fixture
def announcements_index():
    return publish(
        factory(AnnouncementIndexPage)(parent=home_page(), title="Оголошення", slug="oholoshennia")
    )


def make_announcement(index, title, valid_until=None):
    return publish(
        factory(AnnouncementPage)(
            parent=index,
            title=title,
            valid_until=valid_until,
            date=timezone.localdate() - datetime.timedelta(days=30),
            body=raw_stream([("paragraph", "<p>Текст</p>")]),
        )
    )


def test_announcements_are_archived_after_valid_until(client, announcements_index):
    today = timezone.localdate()
    make_announcement(announcements_index, "Безстрокове")
    make_announcement(announcements_index, "Діє сьогодні", today)
    old = make_announcement(announcements_index, "Застаріле", today - datetime.timedelta(days=1))

    actual = client.get(announcements_index.url).content.decode()
    archive = client.get(announcements_index.url, {"archive": "1"}).content.decode()

    assert "Безстрокове" in actual and "Діє сьогодні" in actual
    assert "Застаріле" not in actual
    assert "Застаріле" in archive and "Безстрокове" not in archive
    assert "Оголошення втратило актуальність" in client.get(old.url).content.decode()


def test_announcement_valid_until_validation():
    page = AnnouncementPage(
        title="О", slug="o", date=datetime.date(2026, 9, 10), valid_until=datetime.date(2026, 9, 1)
    )
    with pytest.raises(ValidationError):
        page.clean()


def test_homepage_shows_latest_news_and_actual_announcements(
    client, news_index, announcements_index
):
    make_news(news_index, "Свіжа новина", timezone.localdate())
    make_announcement(announcements_index, "Актуальне оголошення")
    make_announcement(
        announcements_index, "Архівне оголошення", timezone.localdate() - datetime.timedelta(1)
    )

    html = client.get("/").content.decode()

    assert "Свіжа новина" in html
    assert "Актуальне оголошення" in html
    assert "Архівне оголошення" not in html
    assert "Усі новини" in html and "Усі оголошення" in html


# --- Контакти ----------------------------------------------------------------------------


def test_contact_page_lists_leadership_and_departments(client, department):
    Person.objects.create(
        name="Іваненко Іван", position="Начальник", is_leadership=True, reception="Вівторок 9–12"
    )
    page = publish(
        factory(ContactPage)(
            parent=home_page(),
            title="Контакти",
            slug="kontakty",
            how_to_apply=raw_stream([("paragraph", "<p>Письмово або особисто</p>")]),
        )
    )

    html = client.get(page.url).content.decode()

    assert h1_count(html) == 1
    assert "Як звернутися" in html and "Письмово або особисто" in html
    assert "Іваненко Іван" in html and "Вівторок 9–12" in html
    assert "Відділ соціальних виплат" in html


def test_new_pages_are_searchable(section, department):
    factory(ServicePage)(parent=section, title="Послуга", eligibility="<p>Унікальнеслово</p>")
    assert ServicePage.objects.live().search("Унікальнеслово").count() == 1


@pytest.mark.parametrize(
    "params", [{"year": "99999"}, {"year": "²"}, {"topic": "nema"}, {"page": "abc"}]
)
def test_news_index_ignores_invalid_filters(client, news_index, params):
    make_news(news_index, "Звичайна новина", datetime.date(2026, 5, 1))
    response = client.get(news_index.url, params)
    assert response.status_code == 200
    assert "Звичайна новина" in response.content.decode()


def test_news_topics_come_only_from_published_news(client, news_index):
    public = NewsTopic.objects.create(name="Публічна тема", slug="publichna")
    hidden = NewsTopic.objects.create(name="Тема чернетки", slug="chernetka")
    make_news(news_index, "Опублікована", datetime.date(2026, 5, 1), [public])
    draft = factory(NewsPage)(
        parent=news_index,
        title="Чернетка",
        live=False,
        body=raw_stream([("paragraph", "<p>т</p>")]),
    )
    draft.topics.set([hidden])
    draft.save()

    html = client.get(news_index.url).content.decode()
    assert "Публічна тема" in html
    assert "Тема чернетки" not in html


def test_news_cover_requires_image_description(news_index):
    image = wagtail_factories.ImageFactory(description="")
    page = NewsPage(title="Новина", slug="n", cover=image)
    with pytest.raises(ValidationError):
        page.clean()
    image.description = "Учасники зустрічі"
    page.clean()


def test_departments_show_only_people_of_same_locale(client, section, department):
    from wagtail.models import Locale

    english = Locale.objects.create(language_code="en")
    Person.objects.create(name="Петренко Петро", position="Спеціаліст", department=department)
    Person.objects.create(
        name="Petro Petrenko", position="Specialist", department=department, locale=english
    )
    page = publish(factory(DirectoryPage)(parent=section, kind=DirectoryPage.DEPARTMENTS))

    html = client.get(page.url).content.decode()
    assert "Петренко Петро" in html
    assert "Petro Petrenko" not in html


def test_news_page_related_queries_do_not_grow(client, news_index, django_assert_max_num_queries):
    topic = NewsTopic.objects.create(name="Тема", slug="tema")
    for i in range(4):
        make_news(news_index, f"Новина {i}", datetime.date(2026, 5, i + 1), [topic])
    page = NewsPage.objects.get(title="Новина 3")
    client.get(page.url)  # прогріває кеш меню
    with django_assert_max_num_queries(25):
        client.get(page.url)
