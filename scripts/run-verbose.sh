#!/bin/sh

echo "🔥 Running Django (verbose mode)..."
python3 manage.py makemigrations 
python3 manage.py migrate --verbosity 2

python3 manage.py runserver 0.0.0.0:${DJANGO_PORT} --verbosity 3