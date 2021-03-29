#!/bin/bash

postfix start

if [ ! -f .initialized ]; then
	set -e
	echo "Migrating database..."
	python manage.py makemigrations quicksell_app
	python manage.py migrate quicksell_app
	echo "Collecting static files..."
	python manage.py collectstatic --no-input
	echo "Performing tests..."
	python manage.py test --no-input
    touch .initialized
fi

exec "$@"
