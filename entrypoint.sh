#!/bin/sh
flask db upgrade
exec gunicorn --bind 0.0.0.0:5001 --workers 1 --timeout 120 wsgi:app
