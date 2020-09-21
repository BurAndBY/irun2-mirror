"""
Django settings for irunner2 project.

Generated by 'django-admin startproject' using Django 1.8.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

APPEND_SLASH = True

# Application definition

INSTALLED_APPS = (
    #'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # external apps
    'bootstrap3',
    'django_js_reverse',
    'mptt',
    'rest_framework',
    'widget_tweaks',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',

    # irunner2 apps
    'api',
    'cauth',
    'common',
    'contests',
    'courses',
    'events',
    'feedback',
    'home',
    'news',
    'plagiarism',
    'problems',
    'proglangs',
    'registration',
    'solutions',
    'storage',
    'tex',
    'users',
    'quizzes',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'common.middleware.LogRemoteUserMiddleware',
    'cauth.middleware.AdminMiddleware',
]

ROOT_URLCONF = 'irunner2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'common.context_processors.system_name',
                'dealer.contrib.django.context_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'irunner2.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Minsk'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = (
    ('ru', 'Russian'),
    ('en', 'English'),
    # ('lt', 'Lithuanian'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# Authentication

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'

TWO_FACTOR_PATCH_ADMIN = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 182 * 24 * 60 * 60  # half year

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',  # for bulk update (contests, etc.)
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',  # for compatibility with old iRunner
]

# External applications configuration

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',  # Any other renders
    ),

    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',  # Any other parsers
    )
}

BOOTSTRAP3 = {
    'set_placeholder': False
}

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'irunner_import': {
            'handlers': ['console'],
            'level': 'INFO'
        },
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    }
}

# External links in the navbar

EXTERNAL_LINKS = []

SEMAPHORE = 'http://127.0.0.1:17083/'

DEALER_TYPE = 'git'
DEALER_PATH = BASE_DIR
APRIL_FOOLS_DAY_MODE = False

MAIN_LOGO = {
    'ru': {
        'path': 'bsu/logo_ru.svg',
        'fallback': 'bsu/logo_ru.png',
        'width': 376,
        'height': 96,
    },
    'en': {
        'path': 'bsu/logo_en.svg',
        'fallback': 'bsu/logo_en.png',
        'width': 232,
        'height': 97,
    }
}
