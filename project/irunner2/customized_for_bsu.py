from django.utils.translation import ugettext_lazy as _

LOCATION = 'BSU'

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Minsk'

STATIC_ROOT = 'C:\\inetpub\\wwwroot-acm\\static'

MYSQL_CONFIG = 'my.cnf'

STORAGE_DIR = 'E:\\irunner2\\filestorage'

EXTERNAL_LINKS = [
    (_('Wiki'), u'/wiki/')
]

LANGUAGES = (
    ('ru', 'Russian'),
    ('en', 'English'),
)

MODEL_LANGUAGES = ['ru', 'en']

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

ADMINS = [('Sergei Sobol', 'sergei_sobol@tut.by')]

BSU_DC = 'inet.bsu.by'
BSU_USERNAME = 'fpm.student'
BSU_PASSWORD = 'fake'
