#!/bin/sh
set -e

# This script is run as root.

# Fix ownership of mounted volumes
# The user 'ordnungshub' has UID/GID 1000 by default in the Dockerfile
echo "Fixing ownership of app directories..."
chown -R ordnungshub:ordnungshub /app/data /app/uploads /app/logs /app/backups /app/models

# Drop privileges and execute the main command (CMD)
echo "Switching to user 'ordnungshub' and executing command..."
exec gosu ordnungshub "$@"
