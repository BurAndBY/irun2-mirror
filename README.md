# Insight Runner 2 #

## Разработка ##

### Настройка окружения ###

Вам понадобится Python 2.7.

Для установки библиотеки MySQL-python может понадобиться предварительно установить заголовочные файлы Python и клиентскую библиотеку MySQL. Для Debian/Ubuntu это можно сделать так:

    sobols@magellan:~$ sudo apt-get install python-dev libmysqlclient-dev

Для Windows можно найти уже собранный wheel с MySQL-python.

Далее, клонируем репозиторий и ставим все зависимости в virtualenv.

    sobols@magellan:~$ git clone git@bitbucket.org:sobols/irunner2.git
    sobols@magellan:~$ cd irunner2
    sobols@magellan:~/irunner2$ virtualenv venv --no-site-packages
    sobols@magellan:~/irunner2$ source venv/bin/activate
    (venv)sobols@magellan:~/irunner2$ pip install -r requirements.txt
    (venv)sobols@magellan:~/irunner2$ cd project
    (venv)sobols@magellan:~/irunner2$ export DJANGO_SETTINGS_MODULE="irunner2.settings_dev"
    (venv)sobols@magellan:~/irunner2/project$ python manage.py migrate
    (venv)sobols@magellan:~/irunner2/project$ python manage.py runserver

Готово.