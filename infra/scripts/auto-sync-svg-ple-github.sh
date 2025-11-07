#!/usr/bin/env bash
# =============================================================================
# AUTO-SYNC SVG-PLE TO-DO → GITHUB PROJECTS
# =============================================================================
# Purpose: Monitor svg-ple-todo.md for changes and auto-update GitHub Projects
# Modes: --watch (continuous monitoring), --once (single sync), --help
# Dependencies: gh CLI, jq, inotifywait (optional for watch mode)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TODO_FILE="infra/docs/svg-ple-todo.md"
PROJECT_NAME="SVG-PLE Doctrine Alignment"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MODE="${1:---once}"

# =============================================================================
# FUNCTIONS
# =============================================================================

show_help() {
    cat <<HELP
╔═══════════════════════════════════════════════════════════╗
║  Auto-Sync SVG-PLE To-Do → GitHub Projects               ║
╚═══════════════════════════════════════════════════════════╝

USAGE:
  $0 [MODE]

MODES:
  --once      Single sync (default)
              Sync current state and exit

  --watch     Continuous monitoring
              Watch for file changes and auto-sync
              Requires: inotifywait (inotify-tools package)

  --help      Show this help message

EXAMPLES:
  # Single sync (good for pre-commit hooks)
  $0 --once

  # Continuous monitoring (good for dev workflow)
  $0 --watch

  # Use in pre-commit hook
  echo './infra/scripts/auto-sync-svg-ple-github.sh --once' >> .git/hooks/pre-commit

REQUIREMENTS:
  • GitHub CLI (gh) installed and authenticated
  • jq (JSON processor)
  • inotifywait (only for --watch mode)

DOCUMENTATION:
  See: infra/docs/AUTO_SYNC_GITHUB_PROJECTS.md

HELP
}

check_dependencies() {
    local missing=0

    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}❌ ERROR: GitHub CLI (gh) not installed${NC}"
        echo "Install: https://cli.github.com/manual/installation"
        ((missing++))
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ ERROR: jq not installed${NC}"
        echo "Install: https://stedolan.github.io/jq/download/"
        ((missing++))
    fi

    # Check inotifywait only for watch mode
    if [ "$MODE" = "--watch" ]; then
        if ! command -v inotifywait &> /dev/null; then
            echo -e "${RED}❌ ERROR: inotifywait not installed (required for --watch mode)${NC}"
            echo "Install: sudo apt-get install inotify-tools (Linux)"
            echo "macOS: brew install fswatch (alternative watcher)"
            ((missing++))
        fi
    fi

    # Check authentication
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}❌ ERROR: Not authenticated with GitHub CLI${NC}"
        echo "Run: gh auth login"
        ((missing++))
    fi

    # Check todo file exists
    if [ ! -f "$REPO_ROOT/$TODO_FILE" ]; then
        echo -e "${RED}❌ ERROR: To-do file not found: $TODO_FILE${NC}"
        ((missing++))
    fi

    if [ $missing -gt 0 ]; then
        exit 1
    fi
}

find_project() {
    local owner=$(gh repo view --json owner -q .owner.login 2>/dev/null)
    if [ -z "$owner" ]; then
        echo -e "${RED}❌ ERROR: Could not determine repository owner${NC}"
        exit 1
    fi

    local project_num=$(gh project list --owner "$owner" --limit 100 --format json 2>/dev/null | \
        jq -r ".projects[] | select(.title==\"$PROJECT_NAME\") | .number" | head -1)

    if [ -z "$project_num" ]; then
        echo -e "${RED}❌ ERROR: Project '$PROJECT_NAME' not found${NC}"
        echo "Create it first by running: ./infra/scripts/sync-svg-ple-to-github-projects.sh"
        exit 1
    fi

    echo "$project_num"
}

sync_tasks() {
    local project_num="$1"
    local changes=0

    echo -e "${BLUE}🔄 Syncing tasks from $TODO_FILE...${NC}"

    # Parse markdown file and sync each task
    while IFS= read -r line; do
        # Extract status and task name
        if [[ $line =~ ^-\ \[([x\ ])\]\ (.+)$ ]]; then
            local checkbox="${BASH_REMATCH[1]}"
            local task_title="${BASH_REMATCH[2]}"
            local status=""

            if [ "$checkbox" = "x" ]; then
                status="Done"
            else
                status="Todo"
            fi

            # Find matching issue by title
            local issue_num=$(gh issue list --search "in:title \"$task_title\"" \
                --label "svg-ple" --json number --jq '.[0].number' 2>/dev/null || echo "")

            if [ -n "$issue_num" ]; then
                # Check current status
                local current_status=$(gh issue view "$issue_num" --json state -q .state 2>/dev/null || echo "")

                # Map our status to GitHub issue state
                local target_state=""
                if [ "$status" = "Done" ]; then
                    target_state="closed"
                else
                    target_state="open"
                fi

                # Update if different
                if [ "$current_status" != "$target_state" ]; then
                    if [ "$target_state" = "closed" ]; then
                        gh issue close "$issue_num" --comment "✅ Task completed (auto-synced from svg-ple-todo.md)" >/dev/null 2>&1
                        echo -e "${GREEN}  ✅ Closed: #$issue_num - $task_title${NC}"
                    else
                        gh issue reopen "$issue_num" --comment "🔄 Task reopened (auto-synced from svg-ple-todo.md)" >/dev/null 2>&1
                        echo -e "${YELLOW}  🔄 Reopened: #$issue_num - $task_title${NC}"
                    fi
                    ((changes++))
                fi
            else
                echo -e "${YELLOW}  ⚠️  No matching issue for: $task_title${NC}"
            fi
        fi
    done < "$REPO_ROOT/$TODO_FILE"

    if [ $changes -eq 0 ]; then
        echo -e "${GREEN}✅ All tasks already in sync (no changes)${NC}"
    else
        echo -e "${GREEN}✅ Synced $changes task(s)${NC}"
    fi

    return $changes
}

run_once() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  SVG-PLE To-Do → GitHub Projects (Single Sync)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    check_dependencies
    local project_num=$(find_project)
    echo -e "${GREEN}✅ Found project #$project_num: $PROJECT_NAME${NC}"
    echo ""

    sync_tasks "$project_num"

    echo ""
    echo -e "${GREEN}✅ Sync complete!${NC}"
}

run_watch() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  SVG-PLE To-Do → GitHub Projects (Watch Mode)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    check_dependencies
    local project_num=$(find_project)
    echo -e "${GREEN}✅ Found project #$project_num: $PROJECT_NAME${NC}"
    echo ""

    # Initial sync
    echo -e "${YELLOW}🔄 Running initial sync...${NC}"
    sync_tasks "$project_num"
    echo ""

    # Store initial state
    local previous_state=$(grep "^- \[" "$REPO_ROOT/$TODO_FILE" 2>/dev/null || echo "")

    echo -e "${BLUE}👁️  Watching for changes to $TODO_FILE...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    # Watch for changes
    while true; do
        # Wait for file modification
        if command -v inotifywait &> /dev/null; then
            # Linux
            inotifywait -e modify "$REPO_ROOT/$TODO_FILE" >/dev/null 2>&1
        elif command -v fswatch &> /dev/null; then
            # macOS alternative
            fswatch -1 "$REPO_ROOT/$TODO_FILE" >/dev/null 2>&1
        else
            # Fallback: poll every 5 seconds
            sleep 5
        fi

        # Check if content actually changed
        local current_state=$(grep "^- \[" "$REPO_ROOT/$TODO_FILE" 2>/dev/null || echo "")

        if [ "$current_state" != "$previous_state" ]; then
            echo ""
            echo -e "${YELLOW}📝 Change detected at $(date '+%H:%M:%S')${NC}"
            sync_tasks "$project_num"
            previous_state="$current_state"
            echo ""
            echo -e "${BLUE}👁️  Watching for changes...${NC}"
        fi
    done
}

# =============================================================================
# MAIN
# =============================================================================

case "$MODE" in
    --help|-h|help)
        show_help
        exit 0
        ;;
    --once|once)
        run_once
        ;;
    --watch|watch)
        run_watch
        ;;
    *)
        echo -e "${RED}❌ ERROR: Unknown mode: $MODE${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
