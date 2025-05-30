#!/bin/bash

echo "--- Starting application using start.sh ---"

cd /opt/app
export PYTHONPATH=$PWD

echo "Current PATH: $PATH"
echo "--- Contents of /usr/local/bin/ ---"
ls -la /usr/local/bin/
echo "------------------------------------"

echo "Running database migrations..."
python -m flask db upgrade
echo "Migrations complete."

which gunicorn

gunicorn --bind 0.0.0.0:10000 src.wsgi:application