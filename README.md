# Insight Runner 2 #

## Overview ##

iRunner 2 is a course and contest management system that is used at Belarusian State University. It is designed to store an archive of algorithmic problems and perform automatic testing of solutions submitted by students.

## Development ##

### Cloning the repository ###

On UNIX-like systems, this is done with git:
    sobols@magellan:~$ git clone git@bitbucket.org:sobols/irunner2.git
    sobols@magellan:~$ cd irunner2

### Setting up the environment ###

Ensure that Python 2.7 is installed and available through your PATH environment variable. 64-bit version is recommended.

You will also need pip and virtualenv tools. Follow official guides to set them up. pip is shipped together with recent Python distributions downloaded from python.org. Then, virtualenv is installed with pip:
    $ [sudo] pip install virtualenv
Please update pip if it says it has newer version.

Now create and activate a new virtual environment.

On UNIX-like systems:
    sobols@magellan:~/irunner2$ virtualenv venv --no-site-packages
    sobols@magellan:~/irunner2$ source venv/bin/activate
    (venv)sobols@magellan:~/irunner2$

On Windows:
    C:\work\irunner2>virtualenv venv --no-site-packages
    C:\work\irunner2>venv\Scripts\activate.bat
    (venv) C:\work\irunner2>

### Installing dependencies ###

On UNIX-like systems, you will probably have to build MySQL library from source, so please install Python development headers and MySQL client headers. Also you may need JPEG library in order to build Pillow module. Actual command may depend on your repository.
    sobols@magellan:~$ sudo apt-get install python-dev libmysqlclient-dev libjpeg-dev

Then, ask pip to install dependencies:
    (venv)sobols@magellan:~/irunner2$ pip install -r requirements.txt

On Windows, use the same command. It is expected that binary dependencies will be downloaded as pre-built wheels, so local Microsoft Visual Studio compiler is not required.
    (venv) C:\work\irunner2>pip install -r requirements.txt

### Running the server ###

You need to set up DJANGO_SETTINGS_MODULE environment variable. It is used to switch between development and production config.

On UNIX-like systems:
    (venv)sobols@magellan:~/irunner2$ export DJANGO_SETTINGS_MODULE=irunner2.settings_dev

On Windows:
    (venv) C:\work\irunner2>set DJANGO_SETTINGS_MODULE=irunner2.settings_dev

Now create tables in the development database and start the development server.

On UNIX-like systems:
    (venv)sobols@magellan:~/irunner2$ cd project
    (venv)sobols@magellan:~/irunner2/project$ python manage.py migrate
    (venv)sobols@magellan:~/irunner2/project$ python manage.py runserver

On Windows:
    (venv) C:\work\irunner2>cd project
    (venv) C:\work\irunner2>python manage.py migrate
    (venv) C:\work\irunner2>python manage.py runserver

By default, the server starts on port 8000. Open your browser and check.
