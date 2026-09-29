import wagtail_factories
from wagtail.models import Page

from apps.home.models import HomePage
from apps.pages.models import SectionIndexPage, StandardPage


class SectionIndexPageFactory(wagtail_factories.PageFactory):
    title = "Ветеранська політика"

    class Meta:
        model = SectionIndexPage


class StandardPageFactory(wagtail_factories.PageFactory):
    title = "Пільги та гарантії"

    class Meta:
        model = StandardPage


def home_page():
    return HomePage.objects.get(depth=2)


def publish(page: Page) -> Page:
    """Публікує ревізію, щоб у сторінки були last_published_at і актуальний live-стан."""
    page.save_revision().publish()
    page.refresh_from_db()
    return page
