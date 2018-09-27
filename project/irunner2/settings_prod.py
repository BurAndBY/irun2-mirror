import os

from django.utils.translation import ugettext_lazy as _

from irunner2.settings_common import *

# file is not in the repository
from irunner2.settings_prod_private import *

DEBUG = False
TEMPLATE_DEBUG = False

STATIC_ROOT = 'C:\\inetpub\\wwwroot-acm\\static'

STATIC_URL = '/static/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

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

STORAGE_DIR = 'E:\\irunner2\\filestorage'

EXTERNAL_LINKS = [
    (_('Wiki'), u'/wiki/')
]

ADMINS = [('Sergei Sobol', 'sergei_sobol@tut.by')]

SERVER_EMAIL = 'irunner.2@ya.ru'
EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'irunner-2'
