from django.utils.translation import ugettext_lazy as _

LOCATION = 'VGTU'

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Europe/Vilnius'

STATIC_ROOT = 'C:\\inetpub\\wwwroot\\static'

MYSQL_CONFIG = 'myvm.cnf'

STORAGE_DIR = 'D:\\FileStorage'

EXTERNAL_LINKS = [
]

LANGUAGES = (
    ('en', 'English'),
    ('ru', 'Russian'),
    # ('lt', 'Lithuanian'),
)

MODEL_LANGUAGES = ['lt', 'en', 'ru']

MAIN_LOGO = {
    'en': {
        'path': 'vgtu/vgtuitk.png',
        'width': 132,
        'height': 96,
    }
}

ADMINS = [('Arturas Mackunas', '12arturas@gmail.com'), ('Sergei Sobol', 'sergei_sobol@tut.by')]
