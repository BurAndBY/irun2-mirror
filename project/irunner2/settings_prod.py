import os

from settings_common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1@4i==7-0$*jmu_5-8o1x+i82vera$25&-x!qu7&g!u89z0a(l'

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['sobols.haze.yandex.net']

STATIC_ROOT = '/opt/irunner2/static'

STATIC_URL = '/beta/static/'
LOGIN_REDIRECT_URL = '/beta/'
LOGIN_URL = '/beta/login/'

TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, 'irunner2', 'my.cnf'),
        },
        'CONN_MAX_AGE': 10 * 60,
    }
}

# File storage

STORAGE_DIR = os.path.join('/opt/irunner2/filestorage')
