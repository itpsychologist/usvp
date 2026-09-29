import pytest


@pytest.fixture(autouse=True)
def _enable_db(db):
    """Усі тести мають доступ до БД (Wagtail створює сторінки в міграціях)."""
