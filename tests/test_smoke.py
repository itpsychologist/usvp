from django.conf import settings
from wagtail.models import Site

from apps.home.models import HomePage


def test_default_site_points_to_homepage():
    site = Site.objects.get(is_default_site=True)
    assert isinstance(site.root_page.specific, HomePage)
    assert site.root_page.locale.language_code == "uk"


def test_homepage_is_ukrainian_by_default(client):
    response = client.get("/")
    assert response.status_code == 200
    assert '<html lang="uk">' in response.content.decode()


def test_english_prefix_switches_language(client):
    response = client.get("/en/")
    assert response.status_code == 200
    assert '<html lang="en">' in response.content.decode()


def test_ukrainian_has_no_language_prefix(client):
    assert client.get("/uk/").status_code == 404


def test_unknown_page_returns_404(client):
    assert client.get("/neisnuiucha-storinka/").status_code == 404


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200


def test_wagtail_admin_requires_login(client):
    response = client.get(f"/{settings.WAGTAIL_ADMIN_PATH}")
    assert response.status_code == 302
    assert "login" in response["Location"]
