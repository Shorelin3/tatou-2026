#!/usr/bin/env bash
set -e

if [[ -z "${FLAG_2:-}" ]]; then
    echo "WARNING: FLAG_2 is not set"
fi

# Replace placeholder in /app/flag while running as root
if [[ -f "/app/flag" ]]; then
    if grep -q "REPLACE_THIS_STRING_WITH_SERVER_FLAG" "/app/flag"; then
        echo "Replacing placeholder in flag"
        sed -i "s/REPLACE_THIS_STRING_WITH_SERVER_FLAG/${FLAG_2}/g" /app/flag
    fi
else
    echo "WARNING: /app/flag not found, skipping"
fi

# Make sure the flag remains readable only by root
chown root:root /app/flag
chmod 600 /app/flag

# Give the application user access to the storage volume
chown -R tatou:tatou /app/storage

echo "Starting server as non-root user..."

exec gosu tatou gunicorn -b 0.0.0.0:5000 server:app
