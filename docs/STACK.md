# Stack і інструменти розробки — сайт УСВП Лубенської міської ради

> Супровідний документ до [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

## 1. Архітектура та стек

### Ключове рішення: Django + Wagtail CMS
Wagtail — CMS, побудована на Django: це звичайний Django-проєкт з готовою адмінкою для контент-менеджера. З коробки є дерево сторінок, чернетки, ревізії, планування публікацій, workflow модерації, бібліотеки зображень і документів, пошук, ролі та права, багатомовність через `wagtail-localize`. Писати все це на чистому Django admin означало б місяці роботи й гірший UX для редактора.

### STACK
| Шар | Технологія |
|---|---|
| Мова / runtime | Python 3.12 |
| Фреймворк | **Django 5.2 LTS** (підтримка до 04.2028) |
| CMS | **Wagtail 7.4 LTS** (підтримка безпеки до 11.2027; 8.x — не LTS) |
| i18n | `wagtail-localize` (переклад UA→EN в адмінці), `django.middleware.locale`, `i18n_patterns(prefix_default_language=False)`: UA на `/`, EN на `/en/` |
| БД | **PostgreSQL 16+** |
| Пошук | Wagtail search, бекенд `database` на PostgreSQL FTS (конфіг `simple` + unaccent для UA; окремий індекс для EN) |
| Фронтенд | Django templates, **Tailwind CSS 4** через `django-tailwind-cli` (standalone-бінарник, Node не потрібен), невеликий vanilla JS без залежностей (`static/js/site.js`, сумісний із суворою CSP) для меню й панелі доступності, акордеони — нативні `<details>`. Без SPA. Дизайн-система — [DESIGN.md](DESIGN.md) |
| Шрифт | **e-Ukraine** / e-UkraineHead (безкоштовний шрифт Мінцифри, кирилиця), self-hosted |
| Медіа | Wagtail Images: рендишини WebP/AVIF, `srcset`, обов'язковий alt-текст. Документи: PDF/DOCX з обмеженням розміру й типу |
| Налаштування | `django-environ` (`.env`), розбиття `settings/base.py`, `dev.py`, `prod.py` |
| Безпека | `django-axes` (brute-force), 2FA для адмінки (`django-otp` або актуальний пакет 2FA для Wagtail), `django-csp`, HSTS, secure cookies, приховане адмін-URL |
| SEO | `wagtail.contrib.sitemaps`, `robots.txt`, hreflang uk/en, OpenGraph, schema.org `GovernmentOrganization` / `GovernmentService` |
| Статика | WhiteNoise (стиснення, хешування) |
| Сервер | Gunicorn за Nginx, Docker Compose (web, db, nginx), Let's Encrypt, коли з'явиться домен |
| Кеш | Кеш шаблонних фрагментів у Redis (опційно, для v1 достатньо локального) |
| Якість коду | `ruff` (lint + format), `djlint`, `pre-commit`, `mypy` (опційно) |
| Тести | `pytest-django`, `wagtail-factories`, `factory_boy`, Playwright + `axe-core`, Lighthouse CI |
| CI | GitHub Actions: lint → tests → a11y smoke → build image |
| Моніторинг | Логи у файл/journald, Sentry (self-hosted або вимкнений: погодити) , uptime-монітор |
| Бекапи | Щоденний `pg_dump` + rsync `media/`, зберігання 30 днів, окремий носій |

### Структура репозиторію
```
usvp/
├─ config/                 # settings/{base,dev,prod}.py, urls.py, wsgi.py
├─ apps/
│  ├─ core/                # SiteSettings, базові блоки StreamField, шаблонні теги, меню
│  ├─ home/                # HomePage
│  ├─ pages/               # StandardPage, SectionIndexPage, ServicePage, ProgramPage
│  ├─ organization/        # Керівництво, Структура, Фахівці із супроводу (snippets)
│  ├─ news/                # NewsIndex/NewsPage, AnnouncementIndex/AnnouncementPage
│  ├─ publicinfo/          # Реєстр публічної інформації, DocumentListPage
│  ├─ contacts/            # ContactPage
│  └─ search/              # SearchView
├─ templates/              # base.html, components/, pages/
├─ assets/css/             # source.css — вхід Tailwind (поза STATICFILES_DIRS)
├─ static/                 # js/, fonts/, css/tailwind.css (збирається, не в git)
├─ locale/                 # uk, en (.po) для інтерфейсних рядків
├─ docs/                   # IMPLEMENTATION_PLAN.md, STACK.md, CONTENT_GUIDE.md
├─ tests/  e2e/
├─ docker/  docker-compose.yml  Dockerfile  pyproject.toml  .env.example
└─ CLAUDE.md
```

### Ролі (Wagtail Groups)
- **Адміністратор**: усе, зокрема користувачі, налаштування сайту й меню.
- **Контент-менеджер**: створення, редагування й публікація сторінок, новин, оголошень, документів, переклад EN. Без доступу до користувачів і налаштувань безпеки.
- Опційно: workflow «Редактор → Погодження керівником» для розділу «Публічна інформація».

---

## 2. Що встановити для Claude Code

### Вбудовані skills (уже є, використовувати під час розробки)
| Skill / команда | Для чого |
|---|---|
| `/init` | Створити `CLAUDE.md` з правилами проєкту: стек, команди, коди стилю, правила мови та доступності |
| `/code-review`, `/security-review` | Перевірка кожної фічі та безпеки (адмінка, завантаження файлів, CSP) |
| `/simplify` | Прибирання коду після великих змін |
| `run` | Запуск dev-сервера та перевірка змін у браузері |
| `claude-in-chrome` / Playwright MCP | Візуальна перевірка сторінок, скриншоти, логи консолі |
| `fewer-permission-prompts` | Дозволити часті read-only команди (`manage.py check`, `pytest`, `ruff`) |

### Плагіни (офіційний marketplace, `/plugin`; перевірте, що вони там є)
- **frontend-design**: якісна верстка компонентів і шаблонів.
- **security-guidance**: хук, який попереджає про небезпечні патерни під час редагування.
- **commit-commands**, **pr-review-toolkit**: коміти, PR, рев'ю.
- **feature-dev**: покрокова розробка фіч (explore, plan, implement).

### MCP-сервери
| MCP | Навіщо |
|---|---|
| **Context7** | Актуальна документація Django 5.2 / Wagtail 7.4 / Tailwind 4 (менше застарілих API) |
| **Playwright MCP** | E2E-перевірка, скриншоти мобільної й десктопної версій, прогін axe-core |
| **PostgreSQL MCP** (read-only) | Перегляд схеми та даних під час налагодження |
| **GitHub MCP** або `gh` CLI | Issues, PR, CI |
| **Figma MCP** (опційно) | Якщо макети робитимуться у Figma |

### Локальні інструменти
`uv` (пакети Python), Docker Desktop (PostgreSQL + прод-подібне середовище), `gh`, Node LTS (лише для Playwright/axe/Lighthouse; сам сайт Node не потребує), `pre-commit`.

### Власні project-skills і хуки (створено у Фазі 0)
- `.claude/skills/wagtail-page-type/SKILL.md`: чек-лист, як додати новий тип сторінки (модель, панелі, шаблон, переклад, тест, міграція).
- `.claude/skills/a11y-check/SKILL.md`: прогін axe + Lighthouse і перевірка контрасту.
- Хук `PostToolUse` для `*.py` запускає `ruff format`, для `*.html` запускає `djlint --reformat`.

### Проєктні субагенти (`.claude/agents/`)
- Реалізатори: `wagtail-developer` (бекенд), `frontend-developer` (шаблони, Tailwind, JS), `content-editor` (тексти й переклад інтерфейсу).
- Рецензенти, лише читають і звітують: `django-reviewer` (коректність і безпека), `a11y-auditor` (WCAG 2.1 AA), `compliance-reviewer` (вимоги законодавства).
- Порядок використання описано в `CLAUDE.md`. Плагіни `feature-dev` і `pr-review-toolkit` поки не встановлені; їх можна додати через `/plugin` як загальні доповнення.
