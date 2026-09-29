import importlib
import re

import pytest

from apps.core.styleguide import WIREFRAMES

URLS = ["/styleguide/"] + [f"/styleguide/wireframes/{name}/" for name in WIREFRAMES]


@pytest.fixture
def styleguide_on(settings):
    settings.STYLEGUIDE_ENABLED = True


@pytest.mark.parametrize("url", URLS)
def test_styleguide_hidden_when_disabled(client, settings, url):
    settings.STYLEGUIDE_ENABLED = False
    assert client.get(url).status_code == 404


@pytest.mark.usefixtures("styleguide_on")
@pytest.mark.parametrize("url", URLS)
def test_styleguide_pages_render(client, url):
    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert '<html lang="uk"' in html
    assert len(re.findall(r"<h1[\s>]", html)) == 1
    assert 'href="#main"' in html
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    # Багаторядкові {# #} Django не підтримує — такий коментар потрапив би в HTML як текст
    assert "{#" not in html
    assert "{%" not in html


@pytest.mark.usefixtures("styleguide_on")
def test_unknown_wireframe_is_404(client):
    assert client.get("/styleguide/wireframes/nema/").status_code == 404


@pytest.mark.usefixtures("styleguide_on")
@pytest.mark.parametrize("url", URLS)
def test_ids_are_unique(client, url):
    html = client.get(url).content.decode()
    ids = re.findall(r'\sid="([^"]+)"', html)
    duplicates = {i for i in ids if ids.count(i) > 1}
    assert not duplicates


@pytest.mark.usefixtures("styleguide_on")
@pytest.mark.parametrize("url", URLS)
def test_aria_controls_point_to_existing_ids(client, url):
    html = client.get(url).content.decode()
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    assert set(re.findall(r'aria-controls="([^"]+)"', html)) <= ids


def test_homepage_uses_design_system(client):
    html = client.get("/").content.decode()
    assert "css/tailwind.css" in html
    assert "js/site.js" in html
    assert "<footer" in html


def test_styleguide_is_always_off_in_prod(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 50)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.gov.ua")
    monkeypatch.setenv("STYLEGUIDE_ENABLED", "True")
    prod = importlib.reload(importlib.import_module("config.settings.prod"))

    assert prod.STYLEGUIDE_ENABLED is False


@pytest.mark.usefixtures("styleguide_on")
def test_panels_are_visible_without_js(client):
    """Панелі не мають атрибута hidden: їх ховає CSS лише коли працює JS (клас js на <html>)."""
    html = client.get("/styleguide/wireframes/home/").content.decode()
    assert "data-disclosure-panel" in html
    assert not re.search(r"<(div|ul)[^>]*\shidden[\s>]", html)
