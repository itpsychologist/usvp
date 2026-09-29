"""Дані меню з кешем. Меню однакове для всіх відвідувачів, тому будуємо його раз на мову й
зберігаємо в кеші; позначки «поточний розділ / сторінка» додає шаблонний тег для кожного запиту.

Кеш скидається сигналами (публікація, зняття з публікації, переміщення, видалення сторінок,
зміна меню) і в будь-якому разі живе не довше за NAV_CACHE_TIMEOUT: у prod з кількома
процесами Gunicorn і локальним кешем кожен процес скидає лише свій кеш.
"""

from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from django.utils import translation
from wagtail.models import Page

from apps.core.models import NavigationMenu

NAV_CACHE_TIMEOUT = 300
CACHE_PREFIX = "usvp:nav"
LAST_UPDATED_KEY = f"{CACHE_PREFIX}:last-updated"


def _cache_key(location, language=None):
    return f"{CACHE_PREFIX}:{location}:{language or translation.get_language()}"


def _visible_pages(ids):
    """Опубліковані й загальнодоступні (без обмежень перегляду) сторінки з переданих id."""
    return {page.pk: page for page in Page.objects.live().public().filter(pk__in=ids).specific()}


def _build(location):
    menu = NavigationMenu.for_location(location)
    if menu is None:
        return []
    items = list(menu.items.all())
    localized = {item.pk: item.page.localized for item in items if item.page_id}
    visible = _visible_pages([page.pk for page in localized.values()])
    entries = []
    for item in items:
        entry = {"title": item.display_title, "description": item.description, "children": []}
        if item.page_id:
            page = visible.get(localized[item.pk].pk)
            if page is None or not page.url:
                continue
            entry.update(url=page.url, page_pk=page.pk, page_path=page.path, page_depth=page.depth)
            if location == NavigationMenu.MAIN:
                entry["children"] = [
                    {"title": child.title, "url": child.url, "page_pk": child.pk}
                    for child in page.get_children().live().public().in_menu()
                    if child.url
                ]
        else:
            entry["url"] = item.url
        entries.append(entry)
    return entries


def get_menu(location):
    key = _cache_key(location)
    entries = cache.get(key)
    if entries is None:
        entries = _build(location)
        cache.set(key, entries, NAV_CACHE_TIMEOUT)
    return entries


def get_last_updated():
    value = cache.get(LAST_UPDATED_KEY)
    if value is None:
        value = Page.objects.live().aggregate(latest=Max("last_published_at"))["latest"]
        cache.set(LAST_UPDATED_KEY, value, NAV_CACHE_TIMEOUT)
    return value


def clear_navigation_cache(**kwargs):
    """Обробник сигналів: скидає кеш меню всіх мов і дату останнього оновлення."""
    keys = [
        _cache_key(location, language)
        for location, _ in NavigationMenu.LOCATIONS
        for language, _ in settings.LANGUAGES
    ]
    cache.delete_many([*keys, LAST_UPDATED_KEY])
