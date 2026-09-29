"""Дані для шапки, футера й навігації. Компоненти UI-кіту приймають прості словники,
тому ці теги перетворюють моделі (меню, SiteSettings, дерево сторінок) у формат компонентів."""

import re

from django import template
from django.template.defaultfilters import filesizeformat
from wagtail.models import Page

from apps.core.models import NavigationMenu, SiteSettings
from apps.core.navigation import get_last_updated, get_menu

register = template.Library()


@register.filter
def tel_href(number):
    """(05361) 7-00-00 → +380536170000 для посилання tel:."""
    digits = re.sub(r"\D", "", number or "")
    if digits.startswith("380"):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+38{digits}"
    return digits


@register.filter
def stream_values(stream):
    """Значення блоків StreamField — для компонентів, що приймають простий список."""
    return [block.value for block in stream or []]


@register.filter
def document_ext(doc):
    """Розширення файла: з документа Wagtail або зі словника демо-даних."""
    if isinstance(doc, dict):
        return doc.get("ext", "")
    return getattr(doc, "file_extension", "")


@register.filter
def document_size(doc):
    if isinstance(doc, dict):
        return doc.get("size", "")
    return filesizeformat(doc.file_size) if getattr(doc, "file_size", None) else ""


def _current_page(context):
    page = context.get("page") or context.get("self")
    return page if isinstance(page, Page) else None


def _site_settings(context):
    request = context.get("request")
    if request is None:
        return None
    # for_request кешує налаштування на об'єкті запиту: site_info і site_alert не дублюють запити
    return SiteSettings.for_request(request)


@register.simple_tag(takes_context=True)
def main_menu(context):
    """Пункти головного меню з підпунктами (дочірні сторінки з позначкою «Показувати в меню»).

    Структура береться з кешу (apps/core/navigation.py), тут лише позначаємо поточний розділ.
    """
    current = _current_page(context)
    items = []
    for cached in get_menu(NavigationMenu.MAIN):
        entry = {**cached, "active": False, "current": False}
        entry["children"] = [
            {**child, "current": bool(current and child["page_pk"] == current.pk)}
            for child in cached["children"]
        ]
        if current is not None and "page_pk" in cached:
            entry["current"] = current.pk == cached["page_pk"]
            entry["active"] = cached["page_depth"] > 2 and current.path.startswith(
                cached["page_path"]
            )
        items.append(entry)
    return items


@register.simple_tag
def footer_menu():
    items = get_menu(NavigationMenu.FOOTER)
    return [{"title": item["title"], "url": item["url"]} for item in items]


@register.simple_tag(takes_context=True)
def site_info(context):
    """Контакти з налаштувань сайту у форматі компонентів шапки й футера."""
    settings = _site_settings(context)
    if settings is None:
        return {}
    info = {
        "address": settings.address,
        "email": settings.email,
        "phones": [
            {
                "label": block.value["label"],
                "number": block.value["number"],
                "href": tel_href(block.value["number"]),
            }
            for block in settings.phones
        ],
        "schedule": [
            {"days": block.value["days"], "hours": block.value["hours"]}
            for block in settings.schedule
        ],
        "map_url": settings.map_url,
        "facebook_url": settings.facebook_url,
        "council_url": settings.council_url,
        "emblem": settings.emblem,
        "content_license": settings.content_license,
    }
    # Футер показує блок контактів лише коли є що показати
    has_content = any(info[key] for key in ("address", "email", "phones", "schedule"))
    return info if has_content or settings.emblem or settings.content_license else {}


@register.simple_tag(takes_context=True)
def site_alert(context):
    settings = _site_settings(context)
    if settings is None or not settings.alert_enabled or not settings.alert_text:
        return None
    page = settings.alert_page
    return {
        "text": settings.alert_text,
        "url": page.localized.url if page and page.live else "",
    }


@register.simple_tag
def site_last_updated():
    return get_last_updated()


@register.simple_tag
def breadcrumbs(page):
    """Від головної до поточної сторінки; на головній крихти не показуються."""
    if page is None or page.depth <= 2:
        return []
    ancestors = page.get_ancestors().filter(depth__gte=2)
    crumbs = [{"title": ancestor.title, "url": ancestor.url} for ancestor in ancestors]
    crumbs.append({"title": page.title, "url": ""})
    return crumbs


@register.simple_tag
def section_nav(page):
    """Бокова навігація: розділ верхнього рівня та його опубліковані підсторінки."""
    section = page.get_section() if hasattr(page, "get_section") else None
    if section is None:
        return None
    children = section.get_children().live().public()
    if not children.exists():
        return None
    return {
        "title": section.title,
        "url": section.url,
        "children": [
            {
                "title": child.title,
                "url": child.url,
                "current": child.pk == page.pk,
            }
            for child in children
        ],
    }
