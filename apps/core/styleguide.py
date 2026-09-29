"""UI-кіт і wireframes ключових сторінок для погодження дизайну (фаза 1).

Доступно на /styleguide/ лише коли STYLEGUIDE_ENABLED (типово — у dev). Дані тут — заглушки
для макетів: адреси, телефони й імена навмисно не справжні. У фазах 2–4 ті самі компоненти
отримуватимуть дані з моделей Wagtail.
"""

from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

BASE = "/styleguide/wireframes"
ICONS_DIR = Path(settings.BASE_DIR) / "templates" / "components" / "icons"

WIREFRAMES = {
    "home": "Головна",
    "section": "Лендинг розділу",
    "service": "Сторінка послуги",
    "news-index": "Новини: список",
    "news": "Новина",
    "register": "Реєстр публічної інформації",
    "contacts": "Контакти",
}

PHONE = {"number": "(0XXXX) X-XX-XX", "href": "+380000000000"}
CARD_PHONE = {"phone": PHONE["number"]}

SITE_INFO = {
    "address": "вул. [Назва], [№], м. Лубни, Полтавська обл., [індекс]",
    "phones": [
        {"label": "Приймальня", **PHONE},
        {"label": "Гаряча лінія для ветеранів", **PHONE},
    ],
    "email": "usvp@example.gov.ua",
    "schedule": [
        {"days": "Понеділок – четвер", "hours": "08:00 – 17:15"},
        {"days": "П'ятниця", "hours": "08:00 – 16:00"},
        {"days": "Обідня перерва", "hours": "12:00 – 13:00"},
        {"days": "Субота, неділя", "hours": "вихідні"},
    ],
    "map_url": "https://maps.google.com/",
    "facebook_url": "https://www.facebook.com/",
    "council_url": "https://example.gov.ua/",
}

FOOTER_LINKS = [
    {"title": "Публічна інформація", "url": "#"},
    {"title": "Заява про доступність", "url": "#"},
    {"title": "Політика конфіденційності", "url": "#"},
    {"title": "Мапа сайту", "url": "#"},
]


def _nav(active=""):
    """Головне меню за картою сайту з docs/IMPLEMENTATION_PLAN.md."""
    sections = [
        (
            "about",
            "Про управління",
            "Положення, керівництво, структура та графік прийому.",
            [
                "Положення про управління",
                "Керівництво",
                "Структура",
                "Графік роботи та прийому",
                "Програми",
            ],
        ),
        (
            "social",
            "Соціальний напрямок",
            "Соціальні послуги, допомоги та місцеві гарантії.",
            ["Соціальні послуги", "Місцеві соціальні гарантії та програми"],
        ),
        (
            "veterans",
            "Ветеранська політика",
            "Статус, пільги, реабілітація та супровід ветеранів і їхніх родин.",
            [
                "Питання статусу",
                "Пільги та гарантії",
                "Реабілітація та перекваліфікація",
                "Ветеранські простори",
                "Фахівці із супроводу ветеранів",
            ],
        ),
        (
            "idp",
            "ВПО",
            "Довідка ВПО, допомога, житло та гуманітарна підтримка.",
            ["Довідка ВПО", "Допомога", "Житло", "Гуманітарна підтримка", "Часті питання"],
        ),
        (
            "public",
            "Публічна інформація",
            "Реєстр документів, запити на інформацію, запобігання корупції.",
            [
                "Реєстр публічної інформації",
                "Запити на інформацію",
                "Запобігання корупції",
                "Вакансії та кадрові питання",
                "Відкриті дані",
            ],
        ),
        (
            "news",
            "Новини та оголошення",
            "Події, повідомлення та оголошення управління.",
            ["Новини", "Оголошення"],
        ),
    ]
    items = [
        {
            "title": title,
            "url": f"{BASE}/section/" if key == "veterans" else "#",
            "description": description,
            "active": key == active,
            "children": [{"title": child, "url": "#"} for child in children],
        }
        for key, title, description, children in sections
    ]
    items.append({"title": "Контакти", "url": f"{BASE}/contacts/", "active": active == "contacts"})
    return items


def _lang_links():
    return [
        {"code": "uk", "label": "UA", "name": "Українська", "url": "#", "current": True},
        {"code": "en", "label": "EN", "name": "English", "url": "#", "current": False},
    ]


def _documents():
    return [
        {"title": "Положення про управління", "url": "#", "ext": "pdf", "size": "412 КБ"},
        {"title": "Заява (зразок)", "url": "#", "ext": "docx", "size": "38 КБ"},
        {
            "title": "Перелік документів для оформлення",
            "url": "#",
            "ext": "pdf",
            "size": "96 КБ",
            "date": date(2026, 9, 1),
        },
    ]


def _news(count=3):
    items = [
        {
            "title": "Заголовок новини про роботу управління",
            "url": f"{BASE}/news/",
            "date": date(2026, 9, 25),
            "lead": "Короткий лід: одне-два речення про головне в новині.",
            "tag": "Ветеранам",
        },
        {
            "title": "Зміни в порядку прийому громадян",
            "url": f"{BASE}/news/",
            "date": date(2026, 9, 18),
            "lead": "Короткий лід: що змінюється і з якої дати.",
            "tag": "Прийом громадян",
        },
        {
            "title": "Підсумки засідання комісії",
            "url": f"{BASE}/news/",
            "date": date(2026, 9, 10),
            "lead": "Короткий лід: які рішення ухвалено.",
            "tag": "ВПО",
        },
    ]
    return (items * 4)[:count]


def _announcements():
    return [
        {
            "title": "Оголошення про особистий прийом керівника",
            "url": "#",
            "date": date(2026, 9, 26),
            "event_date": datetime(2026, 10, 6, 10, 0),
            "valid_until": date(2026, 10, 6),
        },
        {
            "title": "Оголошення про конкурс на заміщення вакантної посади",
            "url": "#",
            "date": date(2026, 9, 20),
            "valid_until": date(2026, 10, 20),
        },
        {
            "title": "Зміна графіка роботи у святкові дні",
            "url": "#",
            "date": date(2026, 8, 20),
            "valid_until": date(2026, 8, 25),
            "archived": True,
        },
    ]


def _faq():
    return [
        {
            "title": "Хто може звернутися?",
            "text": "Текст-заглушка: відповідь на часте питання, 2–4 речення простою мовою.",
        },
        {
            "title": "Чи можна подати документи онлайн?",
            "text": "Текст-заглушка: де й як подати документи, посилання на офіційний сервіс.",
        },
        {
            "title": "Скільки часу займає розгляд?",
            "text": "Текст-заглушка: строк розгляду та від чого він залежить.",
        },
    ]


def _pagination():
    return {
        "prev_url": "#",
        "next_url": "#",
        "pages": [
            {"number": 1, "url": "#"},
            {"number": 2, "url": "#", "current": True},
            {"number": 3, "url": "#"},
            {"gap": True},
            {"number": 12, "url": "#"},
        ],
    }


def _base_context(active=""):
    return {
        "nav_items": _nav(active),
        "lang_links": _lang_links(),
        "search_url": "#",
        "site_info": SITE_INFO,
        "footer_links": FOOTER_LINKS,
        "last_updated": date(2026, 9, 29),
        "wireframes": WIREFRAMES,
    }


def _page_context(name):
    home = {"title": "Головна", "url": f"{BASE}/home/"}
    if name == "home":
        return {
            "alert": {
                "text": "Термінове оголошення: зміна графіка прийому громадян.",
                "url": "#",
            },
            "tiles": [
                {
                    "title": "Ветеранам",
                    "text": "Статус, пільги, супровід",
                    "icon": "shield",
                    "url": f"{BASE}/section/",
                    "veteran": True,
                },
                {
                    "title": "Внутрішньо переміщеним особам",
                    "text": "Довідка, допомога, житло",
                    "icon": "home",
                    "url": "#",
                },
                {
                    "title": "Соціальні послуги",
                    "text": "Догляд, допомога, підтримка",
                    "icon": "heart",
                    "url": "#",
                },
                {
                    "title": "Пільги",
                    "text": "Хто має право і як оформити",
                    "icon": "percent",
                    "url": "#",
                },
                {
                    "title": "Реабілітація",
                    "text": "Фізична, психологічна, професійна",
                    "icon": "activity",
                    "url": "#",
                    "veteran": True,
                },
                {
                    "title": "Графік прийому",
                    "text": "Коли й куди прийти",
                    "icon": "clock",
                    "url": "#",
                },
                {
                    "title": "Контакти",
                    "text": "Телефони відділів і адреса",
                    "icon": "phone",
                    "url": f"{BASE}/contacts/",
                },
                {
                    "title": "Публічна інформація",
                    "text": "Документи, звіти, запити",
                    "icon": "landmark",
                    "url": f"{BASE}/register/",
                },
            ],
            "announcements": _announcements()[:2],
            "news": _news(3),
            "services": [
                {
                    "title": "Назва ключової послуги",
                    "url": f"{BASE}/service/",
                    "text": "Одне речення: кому й навіщо ця послуга.",
                },
                {
                    "title": "Назва місцевої програми",
                    "url": "#",
                    "text": "Одне речення: мета програми та період дії.",
                },
                {
                    "title": "Назва ключової послуги",
                    "url": f"{BASE}/service/",
                    "text": "Одне речення: кому й навіщо ця послуга.",
                },
            ],
        }
    if name == "section":
        children = [
            ("Питання статусу", "Як отримати статус і посвідчення, які документи потрібні."),
            ("Пільги та гарантії", "Перелік пільг і порядок їх оформлення."),
            ("Реабілітація та перекваліфікація", "Програми відновлення та навчання."),
            ("Ветеранські простори", "Адреси, години роботи й послуги просторів."),
            ("Фахівці із супроводу ветеранів", "Хто допоможе у вашій громаді та як зв'язатися."),
        ]
        return {
            "breadcrumbs": [home, {"title": "Ветеранська політика", "url": ""}],
            "children": [
                {"title": title, "text": text, "url": f"{BASE}/service/"}
                for title, text in children
            ],
            "announcements": _announcements()[:2],
            "faq": _faq(),
        }
    if name == "service":
        return {
            "breadcrumbs": [
                home,
                {"title": "Ветеранська політика", "url": f"{BASE}/section/"},
                {"title": "Пільги та гарантії", "url": ""},
            ],
            "section": {
                "title": "Ветеранська політика",
                "url": f"{BASE}/section/",
                "children": [
                    {"title": "Питання статусу", "url": "#"},
                    {"title": "Пільги та гарантії", "url": "#", "current": True},
                    {"title": "Реабілітація та перекваліфікація", "url": "#"},
                    {"title": "Ветеранські простори", "url": "#"},
                    {"title": "Фахівці із супроводу ветеранів", "url": "#"},
                ],
            },
            "toc": [
                {"id": "who", "title": "Хто має право"},
                {"id": "documents", "title": "Які документи потрібні"},
                {"id": "where", "title": "Куди звертатися"},
                {"id": "terms", "title": "Строки та вартість"},
                {"id": "legal", "title": "Підстави"},
                {"id": "faq", "title": "Часті питання"},
            ],
            "documents": _documents()[1:],
            "contact": {
                "title": "Відділ [назва відділу]",
                "address": SITE_INFO["address"],
                "room": "каб. [№]",
                "email": SITE_INFO["email"],
                "hours": "Пн–Чт 08:00–17:15, Пт 08:00–16:00",
                **CARD_PHONE,
            },
            "faq": _faq(),
            "updated": date(2026, 9, 15),
        }
    if name == "news-index":
        return {
            "breadcrumbs": [home, {"title": "Новини", "url": ""}],
            "news": _news(6),
            "years": [2026, 2025],
            "topics": ["Ветеранам", "ВПО", "Соціальні послуги", "Прийом громадян"],
            "pagination": _pagination(),
        }
    if name == "news":
        return {
            "breadcrumbs": [
                home,
                {"title": "Новини", "url": f"{BASE}/news-index/"},
                {"title": "Заголовок новини про роботу управління", "url": ""},
            ],
            "article": _news(1)[0],
            "documents": _documents()[2:],
            "related": _news(3),
        }
    if name == "register":
        return {
            "breadcrumbs": [
                home,
                {"title": "Публічна інформація", "url": "#"},
                {"title": "Реєстр публічної інформації", "url": ""},
            ],
            "doc_types": ["Наказ", "Рішення", "Звіт", "Лист", "Паспорт бюджетної програми"],
            "areas": ["Соціальний захист", "Ветеранська політика", "Бюджет і фінанси"],
            "entries": [
                {
                    "title": "Назва документа [1]",
                    "created": date(2026, 9, 22),
                    "received": None,
                    "type": "Наказ",
                    "area": "Соціальний захист",
                    "storage": "Електронна",
                    "url": "#",
                    "ext": "pdf",
                },
                {
                    "title": "Назва документа [2]",
                    "created": date(2026, 9, 15),
                    "received": date(2026, 9, 16),
                    "type": "Лист",
                    "area": "Ветеранська політика",
                    "storage": "Паперова",
                    "url": "",
                    "ext": "",
                },
                {
                    "title": "Назва документа [3]",
                    "created": date(2026, 9, 1),
                    "received": None,
                    "type": "Паспорт бюджетної програми",
                    "area": "Бюджет і фінанси",
                    "storage": "Електронна",
                    "url": "#",
                    "ext": "pdf",
                },
            ],
            "total": 3,
            "pagination": _pagination(),
        }
    if name == "contacts":
        dept = {
            "address": SITE_INFO["address"],
            "email": SITE_INFO["email"],
            "hours": "Пн–Чт 08:00–17:15, Пт 08:00–16:00",
            **CARD_PHONE,
        }
        return {
            "breadcrumbs": [home, {"title": "Контакти", "url": ""}],
            "departments": [
                {"title": "Відділ [назва 1]", "room": "каб. [№]", **dept},
                {"title": "Відділ [назва 2]", "room": "каб. [№]", **dept},
                {"title": "Відділ [назва 3]", "room": "каб. [№]", **dept},
            ],
            "leaders": [
                {
                    "name": "Прізвище Ім'я По батькові",
                    "position": "Начальник управління",
                    "reception": "Особистий прийом: [день], [години]",
                    "phone": PHONE["number"],
                },
                {
                    "name": "Прізвище Ім'я По батькові",
                    "position": "Заступник начальника",
                    "reception": "Особистий прийом: [день], [години]",
                },
            ],
        }
    return {}


def _check_enabled():
    if not settings.STYLEGUIDE_ENABLED:
        raise Http404


def _render(request, template, context):
    response = render(request, template, context)
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def index(request):
    """UI-кіт: токени, типографіка й усі компоненти на одній сторінці."""
    _check_enabled()
    context = _base_context()
    context.update(
        {
            "breadcrumbs": [
                {"title": "Головна", "url": "#"},
                {"title": "Розділ", "url": "#"},
                {"title": "Поточна сторінка", "url": ""},
            ],
            # Класи bg-* записані повністю, щоб Tailwind їх знайшов (@source у source.css)
            "colors": [
                ("primary-900", "#0a2350", "15.3:1", "bg-primary-900"),
                ("primary-800", "#0e3170", "12.4:1", "bg-primary-800"),
                ("primary-700", "#123f8c", "9.9:1", "bg-primary-700"),
                ("primary-600", "#1c55b5", "7.0:1", "bg-primary-600"),
                ("primary-500", "#3a73d1", "4.6:1", "bg-primary-500"),
                ("primary-100", "#e3ecfa", "фон", "bg-primary-100"),
                ("primary-50", "#f2f6fd", "фон", "bg-primary-50"),
                ("accent-400", "#ffd500", "фокус", "bg-accent-400"),
                ("veteran-700", "#4a5528", "8.0:1", "bg-veteran-700"),
                ("veteran-600", "#5c6a31", "5.9:1", "bg-veteran-600"),
                ("veteran-100", "#eef1e2", "фон", "bg-veteran-100"),
                ("ink", "#1a1d21", "16.9:1", "bg-ink"),
                ("gray-700", "#444b54", "8.8:1", "bg-gray-700"),
                ("gray-600", "#5a626c", "6.2:1", "bg-gray-600"),
                ("gray-500", "#757d87", "рамки", "bg-gray-500"),
                ("gray-300", "#c5cbd3", "лінії", "bg-gray-300"),
                ("gray-100", "#f1f3f5", "фон", "bg-gray-100"),
            ],
            "tile": _page_context("home")["tiles"][0],
            "tile2": _page_context("home")["tiles"][1],
            "card": {"title": "Назва дочірньої сторінки", "text": "Короткий опис.", "url": "#"},
            "news_item": _news(1)[0],
            "announcements": _announcements()[1:],
            "documents": _documents(),
            "person": _page_context("contacts")["leaders"][0],
            "contact": _page_context("service")["contact"],
            "faq": _faq(),
            "pagination": _pagination(),
            "section": _page_context("service")["section"],
            "toc": _page_context("service")["toc"][:3],
            "schedule": SITE_INFO["schedule"],
            "alert": _page_context("home")["alert"],
            "icons": sorted(p.stem for p in ICONS_DIR.glob("*.html")),
        }
    )
    return _render(request, "styleguide/index.html", context)


def wireframe(request, name):
    _check_enabled()
    if name not in WIREFRAMES:
        raise Http404
    active = {"section": "veterans", "service": "veterans", "register": "public"}.get(name, "")
    if name in ("news", "news-index"):
        active = "news"
    if name == "contacts":
        active = "contacts"
    context = _base_context(active)
    context.update(_page_context(name))
    context["wireframe_title"] = WIREFRAMES[name]
    context["wireframe_name"] = name
    template = f"styleguide/wireframes/{name.replace('-', '_')}.html"
    return _render(request, template, context)
