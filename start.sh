#!/bin/bash
echo "--- Starting application using start.sh ---"

# Explicitly set the PATH to ensure gunicorn is found
export PATH="/usr/local/bin:$PATH"

echo "Current PATH: $PATH"

echo "--- Contents of /usr/local/bin/ ---"
ls -la /usr/local/bin/
echo "------------------------------------"

echo "Attempting to find gunicorn with 'which': $(which gunicorn)"

exec gunicorn wsgi --chdir ./src/