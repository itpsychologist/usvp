---
name: wagtail-page-type
description: Чек-лист додавання нового типу сторінки або snippet у Wagtail для сайту УСВП — модель, панелі адмінки, шаблон, доступність, переклад, міграції й тести. Використовувати щоразу, коли створюється або суттєво змінюється модель Page чи snippet.
---

# Новий тип сторінки Wagtail

Виконуй кроки по черзі й не пропускай перевірки наприкінці.

## 1. Модель
- Розмісти модель у відповідному застосунку `apps/<app>/models.py` (див. структуру в `docs/STACK.md`).
- Успадковуй `wagtail.models.Page` (або спільний базовий клас з `apps/core`, коли він з'явиться).
- Обов'язково вкажи `parent_page_types` і `subpage_types`, щоб редактор не міг створити сторінку в неправильному місці.
- `verbose_name` / `verbose_name_plural` та `help_text` полів — українською: їх бачить контент-менеджер.
- Для тексту використовуй StreamField-блоки з `apps/core/blocks.py`, а не нові одноразові блоки.
- Поля, які треба перекладати, — звичайні текстові поля. Службові дані, що однакові для всіх мов (дати, телефони), познач як `SynchronizedField` у `override_translatable_fields`, коли підключено wagtail-localize.
- Додай поля до `search_fields` (`index.SearchField` для тексту, `index.FilterField` для фільтрів).

## 2. Адмінка
- `content_panels` згрупуй через `MultiFieldPanel` з логічними заголовками.
- Для зображень пиши `help_text` з нагадуванням про alt-текст.

## 3. Шаблон
- `templates/<app>/<model_snake_case>.html`, `{% extends "base.html" %}`.
- Семантичні теги (`article`, `nav`, `section` із заголовком), один `h1` на сторінку, без пропусків рівнів заголовків.
- Усі інтерфейсні рядки — через `{% translate %}` / `{% blocktranslate %}`.
- Зображення — через `{% image %}` з `srcset`/WebP і змістовним `alt`.
- Посилання, що відкриваються в новій вкладці, мають це позначати для скрінрідера.

## 4. Міграції
```
uv run python manage.py makemigrations <app>
uv run python manage.py migrate
```
Перевір, що міграція не містить випадкових змін інших моделей.

## 5. Тести (`tests/` або `apps/<app>/tests/`)
- Фабрика через `wagtail_factories.PageFactory`.
- Сторінка рендериться з кодом 200 і правильним `<html lang>`.
- `assertCanCreateAt` / `assertCanNotCreateAt` для ієрархії (через `WagtailPageTestCase`).
- Сторінка знаходиться пошуком, якщо має `search_fields`.

## 6. Перевірка
```
uv run ruff check . && uv run djlint templates --check --lint
uv run python manage.py makemigrations --check --dry-run
uv run pytest
```
Після цього запусти skill `a11y-check` для нового шаблону.
