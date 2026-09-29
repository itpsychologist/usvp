"""Базові налаштування проєкту. Спільні для dev, test і prod."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    # Проєктні застосунки
    "apps.core",
    "apps.home",
    "apps.pages",
    "apps.organization",
    "apps.news",
    "apps.contacts",
    # Wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.contrib.sitemaps",
    "wagtail.contrib.typed_table_block",
    "wagtail.contrib.routable_page",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_tailwind_cli",
    # Безпека входу в адмінку: 2FA (TOTP) і захист від перебору паролів
    "wagtail_2fa",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "axes",
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.VerifyUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    # Має бути останнім: блокує вхід після серії невдалих спроб
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База даних: PostgreSQL через DATABASE_URL.
# Без змінної — локальний SQLite (лише для швидкого старту).
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Мови. Українська — основна й відкривається без префікса (ст. 27 ЗУ про державну мову).
LANGUAGE_CODE = "uk"
LANGUAGES = [
    ("uk", "Українська"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Статика й медіа
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "media")

# Tailwind CSS 4 (standalone-бінарник, Node не потрібен): manage.py tailwind build / watch
TAILWIND_CLI_SRC_CSS = "assets/css/source.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"
TAILWIND_CLI_VERSION = env("TAILWIND_CLI_VERSION", default="4.3.3")

# UI-кіт і wireframes на /styleguide/ — лише для розробки й погодження дизайну
STYLEGUIDE_ENABLED = env.bool("STYLEGUIDE_ENABLED", default=False)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Кеш (меню, дата оновлення). Типово — у пам'яті процесу; у prod з кількома процесами Gunicorn
# краще спільний кеш, напр. CACHE_URL=filecache:///var/tmp/usvp-cache або redis://…
CACHES = {"default": env.cache("CACHE_URL", default="locmemcache://")}

# Wagtail
WAGTAIL_SITE_NAME = "Управління соціальної та ветеранської політики Лубенської міської ради"
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")
WAGTAIL_ADMIN_PATH = env("WAGTAIL_ADMIN_PATH", default="cms-admin/")
DJANGO_ADMIN_PATH = env("DJANGO_ADMIN_PATH", default="django-admin/")
WAGTAILADMIN_PERMITTED_LANGUAGES = [("uk", "Українська"), ("en", "English")]
WAGTAILDOCS_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "odt", "ods", "csv", "zip"]
# Без SVG: файл SVG може містити скрипт, що виконається при відкритті з /media/ на домені сайту
WAGTAILIMAGES_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif", "gif"]
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024
WAGTAILSEARCH_BACKENDS = {
    "default": {"BACKEND": "wagtail.search.backends.database"},
}
WAGTAILEMBEDS_RESPONSIVE_HTML = True
WAGTAILADMIN_RICH_TEXT_EDITORS = {
    "default": {
        "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
        "OPTIONS": {
            "features": ["h3", "bold", "italic", "ol", "ul", "link", "document-link", "hr"]
        },
    }
}

# 2FA (TOTP) для всіх, хто має доступ до адмінки. У dev можна вимкнути через .env.
WAGTAIL_2FA_REQUIRED = env.bool("WAGTAIL_2FA_REQUIRED", default=True)
WAGTAIL_2FA_OTP_TOTP_NAME = "УСВП Лубни"

# django-axes: блокування за парою «логін + IP» після 5 невдалих спроб на 1 годину
AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", default=5)
AXES_COOLOFF_TIME = env.int("AXES_COOLOFF_HOURS", default=1)
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
AXES_VERBOSE = False
AXES_LOCKOUT_TEMPLATE = "core/lockout.html"
# Без проксі довіряємо лише REMOTE_ADDR: X-Forwarded-For клієнт може підробити (див. prod.py)
AXES_IPWARE_META_PRECEDENCE_ORDER = ["REMOTE_ADDR"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
