#!/bin/bash

echo "--- Starting application using start.sh ---"

# Set the current working directory to where your app code is copied
cd /opt/app
export PYTHONPATH=$PWD

echo "Current PATH: $PATH"
echo "--- Contents of /usr/local/bin/ ---"
ls -la /usr/local/bin/
echo "------------------------------------"

echo "Attempting to diagnose database host resolution..."

# Extract the hostname from the DATABASE_URL environment variable
# This pattern extracts the part after '@' and before the next ':' or '/'
DB_HOST_EXTRACTED=$(echo "$DATABASE_URL" | sed -E 's/.*@([^:]+)(:.*)?(\/.*)?/\1/')

if [ -z "$DB_HOST_EXTRACTED" ]; then
    echo "Could not extract DB_HOST from DATABASE_URL. Skipping ping test."
else
    echo "Attempting to ping DB host: $DB_HOST_EXTRACTED (sending 1 packet)..."
    # Ping the database host once. The '||' will print a message if ping fails.
    ping -c 1 "$DB_HOST_EXTRACTED" || echo "PING FAILED: Host resolution issue detected during start.sh."
    echo "Ping test complete."
fi


# --- Run database migrations ---
echo "Running database migrations..."
python -m flask db upgrade
echo "Migrations complete."
# --- End of database migration section ---

which gunicorn

gunicorn --bind 0.0.0.0:10000 src.wsgi:application