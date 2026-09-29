import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _enable_db(db):
    """Усі тести мають доступ до БД (Wagtail створює сторінки в міграціях)."""


@pytest.fixture(autouse=True)
def _clear_cache():
    """Меню кешується: кожен тест починає з порожнього кешу."""
    cache.clear()
    yield
    cache.clear()
