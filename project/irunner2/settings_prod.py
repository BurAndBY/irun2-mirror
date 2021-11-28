import os

from irunner2.settings_common import *

# file is not in the repository
from irunner2.settings_prod_private import *

DEBUG = False
TEMPLATE_DEBUG = False

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
            'read_default_file': os.path.join(BASE_DIR, 'irunner2', MYSQL_CONFIG),
        },
        'CONN_MAX_AGE': 10 * 60,
    }
}

SERVER_EMAIL = 'irunner.2@ya.ru'
DEFAULT_FROM_EMAIL = 'iRunner 2 <{}>'.format(SERVER_EMAIL)
EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'irunner-2'
