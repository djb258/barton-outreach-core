#!/bin/bash
# Stop Auto-Sync Background Service

PID_FILE="logs/sync-service.pid"

echo "Stopping Auto-Sync Background Service..."

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Found service PID: $PID"

    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        sleep 1

        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Forcing stop..."
            kill -9 "$PID"
        fi

        rm -f "$PID_FILE"
        echo "✅ Service stopped successfully!"
    else
        echo "⚠️  Process not found. Cleaning up PID file."
        rm -f "$PID_FILE"
    fi
else
    echo "❌ PID file not found. Service may not be running."
fi
