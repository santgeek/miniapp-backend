#!/bin/bash

echo "--- Starting application using start.sh ---"

# Set the current working directory to where your app code is copied
cd /opt/app/src 

echo "Current PATH: $PATH"
echo "--- Contents of /usr/local/bin/ ---"
ls -la /usr/local/bin/
echo "------------------------------------"

which gunicorn

gunicorn --bind 0.0.0.0:10000 wsgi:app