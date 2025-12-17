#!/bin/bash
# Background Sync Service for Linux/macOS
# Runs auto-sync continuously in the background
# Usage: ./start-sync-service.sh [interval]

INTERVAL=${1:-300}  # Default 5 minutes
LOG_FILE="logs/sync-service.log"
PID_FILE="logs/sync-service.pid"

# Ensure logs directory exists
mkdir -p logs

# Check if service is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "❌ Sync service is already running (PID: $OLD_PID)"
        echo "Run ./stop-sync-service.sh to stop it first"
        exit 1
    else
        echo "⚠️  Removing stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Function to write log
write_log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Cleanup on exit
cleanup() {
    write_log "Stopping sync service..."
    rm -f "$PID_FILE"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start background service
{
    write_log "========================================="
    write_log "Starting Auto-Sync Background Service"
    write_log "Interval: $INTERVAL seconds"
    write_log "========================================="

    # Save PID
    echo $$ > "$PID_FILE"
    write_log "Service PID: $$ (saved to $PID_FILE)"

    ITERATION=0
    while true; do
        ITERATION=$((ITERATION + 1))
        write_log "--- Iteration $ITERATION ---"

        # Run auto-sync
        ./auto-sync.sh --force 2>&1 | grep -E "^(✅|❌|⚠️|🆕)" | while read line; do
            write_log "$line"
        done

        write_log "Sync completed. Waiting $INTERVAL seconds..."
        sleep "$INTERVAL"
    done
} &

SERVICE_PID=$!
echo "✅ Sync service started (PID: $SERVICE_PID)"
echo "📋 Logs: $LOG_FILE"
echo "🛑 Stop with: ./stop-sync-service.sh"
