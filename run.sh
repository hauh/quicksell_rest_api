#!/bin/bash

PYTHON="python3.9"
APP_NAME="quicksell_app"
PORT="7777"

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "Preparing environment..."
if [ ! -f venv ]; then
	$PYTHON -m venv venv
fi
source venv/bin/activate
$PYTHON -m pip install -r requirements.txt 1>/dev/null

echo "Making migrations..."
$PYTHON quicksell/manage.py makemigrations 1>/dev/null
$PYTHON quicksell/manage.py migrate 1>/dev/null
$PYTHON quicksell/manage.py makemigrations $APP_NAME 1>/dev/null
$PYTHON quicksell/manage.py migrate $APP_NAME 1>/dev/null

echo "Starting server..."
$PYTHON quicksell/manage.py runserver 0.0.0.0:$PORT 1>/dev/null & disown
PID=$(echo $!)

if [ ! -d /proc/$PID ]; then
	echo "Deploy failed :("
else
	echo $PID > app.pid
	echo "Server is up!"
fi
