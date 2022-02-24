from django.utils.translation import ugettext_lazy as _

LOCATION = 'APROMIS'

LANGUAGE_CODE = 'lt'

TIME_ZONE = 'Europe/Vilnius'

STATIC_ROOT = 'C:\\inetpub\\wwwroot\\static'

MYSQL_CONFIG = 'myvm.cnf'

STORAGE_DIR = 'D:\\FileStorage'

EXTERNAL_LINKS = [
]

LANGUAGES = (
    ('en', 'English'),
    ('lt', 'Lithuanian'),
    ('ru', 'Russian'),
)

MODEL_LANGUAGES = ['lt', 'en', 'ru']

MAIN_LOGO = {
    'en': {
        'path': 'vgtu/logo_vgtu.png',
    }
}

ADMINS = [('Arturas Mackunas', '12arturas@gmail.com'), ('Sergei Sobol', 'sergei_sobol@tut.by')]

LAST_NAME_FIRST_IN_COURSES = False

SYSTEM_FULL_NAME = 'Skaitmeninė mokymo priemonė APROMIS'
SYSTEM_SHORT_NAME = 'APROMIS'
META_DESCRIPTION = 'Programavimo mokymo informacinė sistema.'
SHOW_ABOUT_PAGE = False
