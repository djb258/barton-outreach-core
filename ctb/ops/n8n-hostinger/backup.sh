#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# N8N BACKUP SCRIPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Backs up n8n data volume and config files
# Run: sudo bash backup.sh
# Add to crontab: 0 2 * * * /opt/n8n/backup.sh  # Daily at 2 AM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

# Configuration
BACKUP_DIR="/opt/n8n-backups"
N8N_DIR="/opt/n8n"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="n8n_backup_${DATE}.tar.gz"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "N8N BACKUP - $DATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop n8n (optional - safer but causes downtime)
# echo "Stopping n8n..."
# cd "$N8N_DIR"
# docker-compose stop

# Export n8n data volume
echo "Backing up n8n data volume..."
docker run --rm \
    -v n8n_data:/source:ro \
    -v "$BACKUP_DIR":/backup \
    alpine \
    tar czf "/backup/${BACKUP_FILE}" -C /source .

# Backup config files
echo "Backing up config files..."
cd "$N8N_DIR"
tar czf "$BACKUP_DIR/n8n_config_${DATE}.tar.gz" \
    docker-compose.yml \
    .env \
    nginx-n8n.conf

# Restart n8n (if stopped)
# echo "Restarting n8n..."
# docker-compose start

# Remove old backups
echo "Cleaning up old backups (>$RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "n8n_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "n8n_config_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ BACKUP COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo ""
echo "RESTORE COMMAND:"
echo "  docker run --rm -v n8n_data:/target -v $BACKUP_DIR:/backup alpine sh -c 'cd /target && tar xzf /backup/$BACKUP_FILE'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
