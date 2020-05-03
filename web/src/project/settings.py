import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY', 'FOR_TEST_ONLY')
DEBUG = os.path.isfile('.debug') or os.environ.get('DEBUG')

ALLOWED_HOSTS = ['strayge.com', '127.0.0.1', '*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'ggchat.apps.GgchatConfig',
]

MIDDLEWARE = []

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {},
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'database': os.environ['MYSQL_DATABASE'],
            'user': os.environ['MYSQL_USER'],
            'password': os.environ['MYSQL_PASSWORD'],
            'charset': 'utf8mb4',
            'host': 'ggstats_db',
            'port': 3306,
        },
        'CONN_MAX_AGE': 900,
    }
}

# LOCAL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'CONN_MAX_AGE': 60,
#         'timeout': 20,
#     }
# }

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = '../static/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
