#!/bin/bash

echo "--- Starting application using start.sh ---"

# Set the current working directory to where your app code is copied
cd /opt/app
export PYTHONPATH=$PWD

echo "Current PATH: $PATH"
echo "--- Contents of /usr/local/bin/ ---"
ls -la /usr/local/bin/
echo "------------------------------------"

# --- Run database migrations ---
echo "Running database migrations..."
python -m flask db upgrade
echo "Migrations complete."
# --- End of database migration section ---

which gunicorn

gunicorn --bind 0.0.0.0:10000 src.wsgi:application