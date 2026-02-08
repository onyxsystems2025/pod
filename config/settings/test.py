"""Test settings."""
from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pod_test",
        "USER": config("DB_USER", default="pod"),  # noqa: F405
        "PASSWORD": config("DB_PASSWORD", default="pod"),  # noqa: F405
        "HOST": config("DB_HOST", default="localhost"),  # noqa: F405
        "PORT": config("DB_PORT", default="5432"),  # noqa: F405
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}
