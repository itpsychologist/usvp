# Сайт Управління соціальної та ветеранської політики Лубенської міської ради

Django 5.2 LTS · Wagtail 7.4 LTS · PostgreSQL · Python 3.12

## Швидкий старт
```bash
cp .env.example .env              # і змініть DJANGO_SECRET_KEY
uv sync
docker compose up -d db           # або закоментуйте DATABASE_URL у .env — буде SQLite
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py tailwind build     # зібрати CSS (під час розробки: tailwind watch)
uv run python manage.py runserver
```
- Сайт: http://localhost:8000/ (англійська версія — `/en/`)
- Адмінка для контенту: http://localhost:8000/cms-admin/
- UI-кіт і wireframes: http://localhost:8000/styleguide/ (опис — [DESIGN.md](docs/DESIGN.md))

## Збірка для продакшну
`static/css/tailwind.css` не зберігається в git. Перед `collectstatic` обов'язково виконайте
`manage.py tailwind build`, інакше manifest-сховище статики дасть помилку 500 на всіх сторінках.

## Розробка
```bash
uv run pre-commit install
uv run pytest
uv run ruff check . && uv run djlint templates --lint
```

Документація: [план реалізації](docs/IMPLEMENTATION_PLAN.md), [стек](docs/STACK.md).
