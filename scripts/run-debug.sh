#!/bin/sh

echo "🐛 Running Django (debug mode)..."

python manage.py migrate

python -m debugpy \
    --listen 0.0.0.0:${DEBUG_PORT} \
    --wait-for-client \
    manage.py runserver 0.0.0.0:${DJANGO_PORT}