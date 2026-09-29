from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key"  # noqa: S105
ALLOWED_HOSTS = ["*"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# WhiteNoise віддає статику напряму з STATICFILES_DIRS, без collectstatic
WHITENOISE_AUTOREFRESH = True
