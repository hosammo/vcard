from .settings import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ['devvcard.hosammo.com', 'localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_dev.sqlite3',
    }
}

STATIC_ROOT = BASE_DIR / 'static_collected'
MEDIA_ROOT = BASE_DIR / 'media'
WAGTAILADMIN_BASE_URL = 'https://devvcard.hosammo.com'
