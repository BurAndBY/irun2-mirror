from settings_common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1@4i==7-0$*jmu_5-8o1x+i82vera$25&-x!qu7&g!u89z0a(l'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

INSTALLED_APPS += (
    'debug_toolbar',
    # and other apps for local development
)

TEMPLATES[0]['APP_DIRS'] = True
