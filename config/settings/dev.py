from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

STYLEGUIDE_ENABLED = env.bool("STYLEGUIDE_ENABLED", default=True)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Без маніфесту статики, щоб не потрібен був collectstatic під час розробки
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# WhiteNoise віддає статику напряму з STATICFILES_DIRS, без collectstatic
WHITENOISE_AUTOREFRESH = True
