#!/bin/bash

# OrdnungsHub Backup Script
set -e

echo "🔄 Starting OrdnungsHub Backup..."
echo "=================================="

# Configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$BACKUP_DATE"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log_info "Backup directory: $BACKUP_DIR"

# Backup database
if docker ps | grep -q ordnungshub-postgres; then
    log_info "Backing up PostgreSQL database..."
    docker exec ordnungshub-postgres pg_dump -U ordnungshub ordnungshub_prod > "$BACKUP_DIR/database.sql"
    log_info "✅ Database backup completed"
elif [ -f "./ordnungshub.db" ]; then
    log_info "Backing up SQLite database..."
    cp "./ordnungshub.db" "$BACKUP_DIR/"
    log_info "✅ SQLite backup completed"
fi

# Backup uploaded files
if [ -d "./uploads" ]; then
    log_info "Backing up uploaded files..."
    cp -r "./uploads" "$BACKUP_DIR/"
    log_info "✅ Files backup completed"
fi

# Backup application data
if docker volume inspect ordnungshub_data &> /dev/null; then
    log_info "Backing up application data..."
    docker run --rm -v ordnungshub_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/app_data.tar.gz -C /data .
    log_info "✅ Application data backup completed"
fi

# Backup configuration
if [ -f ".env.production" ]; then
    log_info "Backing up configuration..."
    cp ".env.production" "$BACKUP_DIR/"
    # Don't backup secrets file for security
    log_info "✅ Configuration backup completed"
fi

# Create compressed archive
log_info "Creating compressed archive..."
tar czf "backups/${BACKUP_DATE}.tar.gz" -C "backups" "$BACKUP_DATE"
rm -rf "$BACKUP_DIR"
log_info "✅ Archive created: backups/${BACKUP_DATE}.tar.gz"

# Cleanup old backups
log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find ./backups -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
log_info "✅ Cleanup completed"

log_info "🎉 Backup completed successfully!"
echo "Backup file: backups/${BACKUP_DATE}.tar.gz"