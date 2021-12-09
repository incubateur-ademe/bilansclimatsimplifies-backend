#! /bin/bash -l

source ./venv/bin/activate
cd ${APP_HOME} # Which has been loaded by the env.
python manage.py publicexport
