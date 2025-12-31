release: python manage.py migrate --no-input
web: gunicorn Elmosliga.wsgi:application --bind 0.0.0.0:$PORT