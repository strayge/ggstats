#!/bin/sh

if [ ! -f ./.build ]; then
  echo "Collecting statics files..."
  python3 manage.py collectstatic --noinput
  date > ./.build
fi

# Start Gunicorn processes
echo Starting Gunicorn...
exec gunicorn project.wsgi:application --bind 0.0.0.0:8080 --workers 3 --timeout 120
