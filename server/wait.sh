#!/bin/sh

echo Hello
while ! nc -z db 3306 ; do
    echo "Waiting for the MySQL Server"
    sleep 3
done
source prod_config.sh
python triplex_frontend/manage.py makemigrations
python triplex_frontend/manage.py migrate
cd triplex_frontend
gunicorn --bind 0.0.0.0:8001 triplex_frontend.wsgi --timeout 600 --workers 4 --capture-output --error-logfile - --access-logfile -