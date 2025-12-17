#!/bin/bash
# Auto-Sync Script for Obsidian, GitKraken, and Git
# Automatically updates tools when repo changes are detected
# Usage: ./auto-sync.sh [--watch] [--force] [--interval=60]

set -e

# Parse arguments
WATCH_MODE=false
FORCE_MODE=false
INTERVAL=60

for arg in "$@"; do
    case $arg in
        --watch|-w)
            WATCH_MODE=true
            shift
            ;;
        --force|-f)
            FORCE_MODE=true
            shift
            ;;
        --interval=*)
            INTERVAL="${arg#*=}"
            shift
            ;;
        *)
            ;;
    esac
done

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Auto-Sync for Obsidian, GitKraken & Git${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

REPO_PATH=$(pwd)

# Function to check if Git repo has updates
check_git_updates() {
    echo -e "${GRAY}🔍 Checking for Git updates...${NC}"

    # Fetch from remote
    git fetch origin 2>/dev/null

    # Check if local is behind remote
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null)

    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        return 0  # Has updates
    fi

    return 1  # No updates
}

# Function to sync Obsidian vault
sync_obsidian_vault() {
    echo -e "${YELLOW}📚 Syncing Obsidian vault...${NC}"

    # Check if .obsidian folder exists
    if [ ! -d ".obsidian" ]; then
        echo -e "${YELLOW}⚠️  Obsidian vault not found, skipping...${NC}"
        return
    fi

    # Update workspace to reflect latest files
    WORKSPACE_FILE=".obsidian/workspace.json"
    if [ -f "$WORKSPACE_FILE" ]; then
        # Create updated workspace with recent files
        python3 -c "
import json
import sys

try:
    with open('$WORKSPACE_FILE', 'r') as f:
        workspace = json.load(f)

    workspace['lastOpenFiles'] = [
        'CTB_README.md',
        'README.md',
        'TOOLS_SETUP.md',
        'ENV_SETUP.md'
    ]

    with open('$WORKSPACE_FILE', 'w') as f:
        json.dump(workspace, f, indent=2)

    print('✅ Obsidian workspace updated')
except Exception as e:
    print(f'⚠️  Could not update workspace: {e}', file=sys.stderr)
" 2>/dev/null || echo -e "${YELLOW}⚠️  Python not available for workspace update${NC}"
    fi

    # Check if Obsidian is running
    if pgrep -x "obsidian" > /dev/null 2>&1 || pgrep -x "Obsidian" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Obsidian is running. Restart to apply changes.${NC}"
    else
        echo -e "${CYAN}💡 Obsidian is not running. Changes will apply on next launch.${NC}"
    fi

    echo -e "${GREEN}✅ Obsidian sync completed${NC}"
}

# Function to sync GitKraken configuration
sync_gitkraken_config() {
    echo -e "${YELLOW}🐙 Syncing GitKraken configuration...${NC}"

    if [ ! -d ".gitkraken" ]; then
        echo -e "${YELLOW}⚠️  GitKraken config not found, skipping...${NC}"
        return
    fi

    # Update GitKraken config with latest repo info
    CONFIG_FILE=".gitkraken/config.json"
    if [ -f "$CONFIG_FILE" ]; then
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

        python3 -c "
import json

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)

    config['project']['lastSync'] = '$CURRENT_TIME'
    config['project']['currentBranch'] = '$CURRENT_BRANCH'

    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2)

    print('✅ GitKraken config updated')
except Exception as e:
    print(f'⚠️  Could not update config: {e}', file=sys.stderr)
" 2>/dev/null || echo -e "${YELLOW}⚠️  Python not available for config update${NC}"
    fi

    # Check if GitKraken is running
    if pgrep -x "gitkraken" > /dev/null 2>&1 || pgrep -x "GitKraken" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  GitKraken is running. Refresh repository to see changes.${NC}"
    else
        echo -e "${CYAN}💡 GitKraken is not running. Changes will apply on next launch.${NC}"
    fi

    echo -e "${GREEN}✅ GitKraken sync completed${NC}"
}

# Function to update Git hooks
update_git_hooks() {
    echo -e "${YELLOW}🔧 Updating Git hooks...${NC}"

    if [ ! -d ".git/hooks" ]; then
        echo -e "${YELLOW}⚠️  Git hooks directory not found, skipping...${NC}"
        return
    fi

    # Make hooks executable
    HOOKS=("pre-commit" "commit-msg" "pre-push" "post-merge" "post-checkout")
    for hook in "${HOOKS[@]}"; do
        HOOK_PATH=".git/hooks/$hook"
        if [ -f "$HOOK_PATH" ]; then
            chmod +x "$HOOK_PATH"
        fi
    done

    echo -e "${GREEN}✅ Git hooks updated${NC}"
}

# Function to pull latest changes
pull_latest_changes() {
    echo -e "${YELLOW}⬇️  Pulling latest changes from remote...${NC}"

    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo -e "${GRAY}   Current branch: $CURRENT_BRANCH${NC}"

    # Check for local changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${GRAY}   Stashing local changes...${NC}"
        git stash push -m "Auto-stash before sync $(date '+%Y-%m-%d %H:%M:%S')"
        STASHED=true
    else
        STASHED=false
    fi

    # Pull changes
    if git pull origin "$CURRENT_BRANCH" 2>&1; then
        echo -e "${GREEN}✅ Successfully pulled latest changes${NC}"

        # Pop stash if we stashed
        if [ "$STASHED" = true ]; then
            echo -e "${GRAY}   Applying stashed changes...${NC}"
            git stash pop
        fi

        return 0
    else
        echo -e "${RED}❌ Failed to pull changes${NC}"
        return 1
    fi
}

# Function to sync CTB registry
sync_ctb_registry() {
    echo -e "${YELLOW}📋 Syncing CTB registry...${NC}"

    REGISTRY_FILE="ctb/meta/registry.json"
    if [ -f "$REGISTRY_FILE" ]; then
        # Count files in CTB directories
        TOTAL_FILES=0
        CTB_DIRS=("sys" "ai" "data" "docs" "ui" "meta")

        for dir in "${CTB_DIRS[@]}"; do
            DIR_PATH="ctb/$dir"
            if [ -d "$DIR_PATH" ]; then
                COUNT=$(find "$DIR_PATH" -type f | wc -l)
                TOTAL_FILES=$((TOTAL_FILES + COUNT))
            fi
        done

        CURRENT_DATE=$(date '+%Y-%m-%d')

        python3 -c "
import json

try:
    with open('$REGISTRY_FILE', 'r') as f:
        registry = json.load(f)

    registry['registry']['last_updated'] = '$CURRENT_DATE'
    registry['registry']['statistics']['total_files'] = $TOTAL_FILES

    with open('$REGISTRY_FILE', 'w') as f:
        json.dump(registry, f, indent=2)

    print('✅ CTB registry updated (Total files: $TOTAL_FILES)')
except Exception as e:
    print(f'⚠️  Could not update registry: {e}', file=sys.stderr)
" 2>/dev/null || echo -e "${YELLOW}⚠️  Python not available for registry update${NC}"
    fi

    echo -e "${GREEN}✅ CTB registry sync completed${NC}"
}

# Function to perform full sync
full_sync() {
    PULL_FIRST=$1

    echo ""
    echo -e "${CYAN}🔄 Starting full sync...${NC}"
    echo ""

    # Pull latest changes if requested
    if [ "$PULL_FIRST" = true ]; then
        if ! pull_latest_changes; then
            echo -e "${YELLOW}⚠️  Pull failed, but continuing with local sync...${NC}"
        fi
        echo ""
    fi

    # Sync all tools
    sync_obsidian_vault
    echo ""

    sync_gitkraken_config
    echo ""

    update_git_hooks
    echo ""

    sync_ctb_registry
    echo ""

    echo -e "${GREEN}✅ Full sync completed!${NC}"
    echo -e "${GRAY}   Timestamp: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
}

# Watch mode - continuous monitoring
watch_mode() {
    echo -e "${CYAN}👁️  Starting watch mode (checking every $INTERVAL seconds)...${NC}"
    echo -e "${GRAY}   Press Ctrl+C to stop${NC}"
    echo ""

    LAST_SYNC_TIME=$(date +%s)

    while true; do
        # Check for updates
        if check_git_updates; then
            echo ""
            echo -e "${GREEN}🆕 Updates detected!${NC}"
            full_sync true
            LAST_SYNC_TIME=$(date +%s)
        else
            CURRENT_TIME=$(date +%s)
            TIME_SINCE_SYNC=$(( (CURRENT_TIME - LAST_SYNC_TIME) / 60 ))
            echo -e "${GRAY}✓ No updates (Last sync: ${TIME_SINCE_SYNC} min ago) - $(date '+%H:%M:%S')${NC}"
        fi

        # Wait before next check
        sleep "$INTERVAL"
    done
}

# Main execution
if [ "$WATCH_MODE" = true ]; then
    # Watch mode - continuous monitoring
    watch_mode
else
    # One-time sync
    if [ "$FORCE_MODE" = true ]; then
        full_sync false
    else
        full_sync true
    fi

    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${YELLOW}💡 Tip: Run with --watch flag for continuous sync:${NC}"
    echo -e "${GRAY}   ./auto-sync.sh --watch${NC}"
    echo ""
fi
