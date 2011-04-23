import os

DEBUG = True

DATABASE_ENGINE = 'sqlite3'

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'oembed.tests',
    'oembed',
]

DEFAULT_FILE_STORAGE = 'oembed.tests.storage.DummyMemoryStorage'

TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.media",
    "django.core.context_processors.request"
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'oembed.tests.urls'
SITE_ID = 1

MEDIA_ROOT = '%s/media/' % (SITE_ROOT)
MEDIA_URL = '/media/'
