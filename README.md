# Сайт Управління соціальної та ветеранської політики Лубенської міської ради

Django 5.2 LTS · Wagtail 7.4 LTS · PostgreSQL · Python 3.12

## Швидкий старт
```bash
cp .env.example .env              # і змініть DJANGO_SECRET_KEY
uv sync
docker compose up -d db           # або закоментуйте DATABASE_URL у .env — буде SQLite
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py setup_roles        # групи «Адміністратори» й «Контент-менеджери»
uv run python manage.py tailwind build     # зібрати CSS (під час розробки: tailwind watch)
uv run python manage.py runserver
```
- Сайт: http://localhost:8000/ (англійська версія — `/en/`)
- Адмінка для контенту: http://localhost:8000/cms-admin/
- UI-кіт і wireframes: http://localhost:8000/styleguide/ (опис — [DESIGN.md](docs/DESIGN.md))

## Збірка для продакшну
`static/css/tailwind.css` не зберігається в git. Перед `collectstatic` обов'язково виконайте
`manage.py tailwind build`, інакше manifest-сховище статики дасть помилку 500 на всіх сторінках.
- Після кожного деплою: `manage.py migrate` і `manage.py setup_roles` (оновлює права груп).
- **django-axes за Nginx.** `AXES_PROXY_COUNT=1` безпечний, лише якщо Nginx додає адресу клієнта
  (`proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`), а Gunicorn недоступний напряму
  (слухає лише localhost або внутрішню мережу Docker). Інакше заголовок можна підробити.
- **2FA** у prod обов'язкова для всіх, хто входить в адмінку. Під час першого входу Wagtail попросить
  налаштувати застосунок-автентифікатор. Публічні сторінки сайту доступні й без 2FA.
- **Кеш.** Меню кешується на 5 хвилин і скидається під час публікації. З кількома процесами Gunicorn
  задайте спільний кеш `CACHE_URL` (див. `.env.example`), інакше зміни меню в інших процесах
  з'являться із затримкою до 5 хвилин.

## Розробка
```bash
uv run pre-commit install
uv run pytest
uv run ruff check . && uv run djlint templates --lint
```

Документація: [план реалізації](docs/IMPLEMENTATION_PLAN.md), [стек](docs/STACK.md).
