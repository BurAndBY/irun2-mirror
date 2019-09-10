from irunner2.settings_common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1@4i==7-0$*jmu_5-8o1x+i82vera$25&-x!qu7&g!u89z0a(l'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS += (
    'debug_toolbar',
    # and other apps for local development
)
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ('127.0.0.1',)

TEMPLATES[0]['APP_DIRS'] = True
STATIC_ROOT = '/opt/irunner2/static'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# File storage

STORAGE_DIR = os.path.join(BASE_DIR, os.pardir, 'filestorage')

# Worker

WORKER_TOKEN = 'abacaba'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
