# OrdnungsHub Production Dockerfile - FINAL ROBUST VERSION
FROM python:3.11-slim as backend

# Install system dependencies, including gosu for user switching
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nodejs \
    npm \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN useradd --create-home --shell /bin/bash ordnungshub

# Copy and set up the entrypoint script (as root)
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create app directory
WORKDIR /app

# Copy dependency files first to leverage cache
COPY requirements.txt package.json package-lock.json* ./

# Install dependencies GLOBALLY as root.
# This makes them available to all users, including the 'ordnungshub' user who will run the app.
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install

# Now copy the rest of the application code
COPY . .

# Build the frontend
RUN npm run build || true

# The entrypoint will handle permissions for mounted volumes at runtime.

# Expose ports
EXPOSE 8000 9090

# Health check will be run by the user specified in the entrypoint (ordnungshub)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Start application (this becomes the command passed to the entrypoint, which runs it as 'ordnungshub')
CMD ["python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]