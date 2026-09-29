# CLAUDE.md

Офіційний сайт **Управління соціальної та ветеранської політики Лубенської міської ради** (УСВП).
Django 5.2 LTS + Wagtail 7.4 LTS, PostgreSQL, Python 3.12, менеджер пакетів `uv`.

План і стек: `docs/IMPLEMENTATION_PLAN.md`, `docs/STACK.md`. Перед новою фазою звіряйся з планом.

## Команди
```
uv sync                                   # залежності
docker compose up -d db                   # PostgreSQL (без DATABASE_URL у .env буде SQLite)
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver         # сайт: /  EN: /en/  адмінка: /cms-admin/
uv run pytest                             # тести (settings: config.settings.test)
uv run ruff check . && uv run ruff format .
uv run djlint templates --reformat --lint
uv run python manage.py makemigrations --check --dry-run
```

## Структура
- `config/settings/{base,dev,test,prod}.py`: налаштування через `.env` (`django-environ`), зразок у `.env.example`.
- `apps/<app>/`: застосунки (`core`, `home`, далі `pages`, `organization`, `news`, `publicinfo`, `contacts`, `search`). Нові застосунки створюй саме тут, `name = "apps.<app>"`.
- `templates/`: усі шаблони (`base.html`, `<app>/<model>.html`, `components/`).
- `static/src/`: вихідні CSS/JS.

## Обов'язкові правила
- **Мова.** Українська — основна: відкривається на `/` без префікса, EN — на `/en/` (ст. 27 ЗУ «Про забезпечення функціонування української мови як державної»). EN не може містити більше інформації, ніж UA. Усі інтерфейсні рядки — через `{% translate %}` / `gettext`, вихідна мова рядків — українська. Назви полів і `help_text` в адмінці — українською.
- **Доступність WCAG 2.1 AA** (ДСТУ EN 301 549): семантичний HTML, видимий фокус, клавіатурна навігація, alt-тексти, контраст. Після змін у шаблонах — skill `a11y-check`.
- **Нові типи сторінок / snippets** — за skill `wagtail-page-type`.
- **Без реєстрації відвідувачів і зовнішніх інтеграцій.** Входять лише адміністратор і контент-менеджер. Facebook і Google — тільки посилання, без вбудованих віджетів і трекерів.
- **Безпека:** секрети лише в `.env`; шляхи адмінок задаються змінними `WAGTAIL_ADMIN_PATH`, `DJANGO_ADMIN_PATH`; `manage.py check --deploy --settings=config.settings.prod` без попереджень.
- Кожна зміна моделей — з міграцією; кожна нова сторінка чи фіча — з тестом у `tests/`.
- Код: ruff (line-length 100), djlint для шаблонів; хук у `.claude/settings.json` форматує файли автоматично.
