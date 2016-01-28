import os

from django.utils.translation import ugettext_lazy as _

from settings_common import *

# file is not in the repository
from settings_prod_private import *

DEBUG = False
TEMPLATE_DEBUG = False

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

EXTERNAL_LINKS = [
    (_('Wiki'), u'/wiki/')
]
