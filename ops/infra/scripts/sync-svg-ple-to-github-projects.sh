#!/usr/bin/env bash
# =============================================================================
# SVG-PLE TO-DO TRACKER → GITHUB PROJECTS SYNC SCRIPT
# =============================================================================
# Purpose: Sync SVG-PLE implementation tracker to GitHub Projects board
# Usage: ./sync-svg-ple-to-github-projects.sh
# Requirements: gh CLI (GitHub CLI) installed and authenticated
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_NAME="SVG-PLE Doctrine Alignment"
TODO_FILE="infra/docs/svg-ple-todo.md"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  SVG-PLE TO-DO TRACKER → GITHUB PROJECTS SYNC${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

echo -e "${YELLOW}🔍 Running pre-flight checks...${NC}"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ ERROR: GitHub CLI (gh) is not installed.${NC}"
    echo ""
    echo "Install with:"
    echo "  macOS:   brew install gh"
    echo "  Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "  Windows: winget install --id GitHub.cli"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ GitHub CLI installed${NC}"

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ ERROR: jq is not installed (required for JSON parsing).${NC}"
    echo ""
    echo "Install with:"
    echo "  macOS:   brew install jq"
    echo "  Linux:   sudo apt-get install jq  (or yum install jq)"
    echo "  Windows: winget install jqlang.jq"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ jq installed${NC}"

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ ERROR: Not authenticated with GitHub CLI.${NC}"
    echo ""
    echo "Run: gh auth login"
    echo ""
    exit 1
fi
echo -e "${GREEN}✅ Authenticated with GitHub${NC}"

# Check if todo file exists
if [ ! -f "$REPO_ROOT/$TODO_FILE" ]; then
    echo -e "${RED}❌ ERROR: To-do file not found at $TODO_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ To-do file found${NC}"

# Get repo owner and name
REPO_OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
echo -e "${GREEN}✅ Repository: $REPO_OWNER/$REPO_NAME${NC}"

echo ""

# =============================================================================
# FIND OR CREATE PROJECT
# =============================================================================

echo -e "${YELLOW}📋 Checking for existing project...${NC}"

# Search for existing project
PROJECT_NUMBER=$(gh project list --owner "$REPO_OWNER" --limit 100 --format json | \
    jq -r ".projects[] | select(.title==\"$PROJECT_NAME\") | .number" | head -1)

if [ -z "$PROJECT_NUMBER" ]; then
    echo -e "${YELLOW}🆕 Project '$PROJECT_NAME' not found. Creating...${NC}"

    # Create new project
    CREATE_OUTPUT=$(gh project create --owner "$REPO_OWNER" --title "$PROJECT_NAME" --format json)
    PROJECT_NUMBER=$(echo "$CREATE_OUTPUT" | jq -r '.number')

    if [ -z "$PROJECT_NUMBER" ]; then
        echo -e "${RED}❌ ERROR: Failed to create project${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Created project #$PROJECT_NUMBER${NC}"
else
    echo -e "${GREEN}✅ Found existing project #$PROJECT_NUMBER${NC}"
fi

PROJECT_ID=$(gh project list --owner "$REPO_OWNER" --limit 100 --format json | \
    jq -r ".projects[] | select(.number==$PROJECT_NUMBER) | .id")

echo -e "${BLUE}Project ID: $PROJECT_ID${NC}"
echo ""

# =============================================================================
# PARSE TODO FILE AND EXTRACT TASKS
# =============================================================================

echo -e "${YELLOW}📝 Parsing to-do file...${NC}"

TASK_COUNT=0
COMPLETED_COUNT=0
PENDING_COUNT=0

# Read file and process tasks
while IFS= read -r line; do
    # Check if line is a task (starts with "- [ ]" or "- [x]")
    if [[ $line =~ ^-\ \[([ x])\]\ (.+)$ ]]; then
        STATUS="${BASH_REMATCH[1]}"
        TASK_TITLE="${BASH_REMATCH[2]}"

        ((TASK_COUNT++))

        if [ "$STATUS" = "x" ]; then
            TASK_STATUS="Done"
            ((COMPLETED_COUNT++))
        else
            TASK_STATUS="Todo"
            ((PENDING_COUNT++))
        fi

        # Create issue for this task
        echo -e "${BLUE}  [$TASK_STATUS] $TASK_TITLE${NC}"

        # Check if issue already exists with this title
        EXISTING_ISSUE=$(gh issue list --search "in:title \"$TASK_TITLE\"" --json number,title --jq '.[0].number' 2>/dev/null || echo "")

        if [ -z "$EXISTING_ISSUE" ]; then
            # Create new issue
            ISSUE_NUMBER=$(gh issue create \
                --title "$TASK_TITLE" \
                --body "SVG-PLE Doctrine Alignment Task - Status: $TASK_STATUS" \
                --label "svg-ple,automation" \
                --json number -q .number)

            # Add issue to project
            gh project item-add "$PROJECT_NUMBER" --owner "$REPO_OWNER" --url "https://github.com/$REPO_OWNER/$REPO_NAME/issues/$ISSUE_NUMBER" > /dev/null

            echo -e "${GREEN}    ✅ Created issue #$ISSUE_NUMBER and added to project${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Issue already exists: #$EXISTING_ISSUE (skipping)${NC}"
        fi
    fi
done < "$REPO_ROOT/$TODO_FILE"

echo ""
echo -e "${GREEN}✅ Processed $TASK_COUNT tasks${NC}"
echo -e "${GREEN}   • Completed: $COMPLETED_COUNT${NC}"
echo -e "${GREEN}   • Pending: $PENDING_COUNT${NC}"
echo ""

# =============================================================================
# ADD PHASE LABELS
# =============================================================================

echo -e "${YELLOW}🏷️  Creating phase labels...${NC}"

PHASES=(
    "phase-1:Environment & Baseline:0052CC"
    "phase-2:BIT Infrastructure:5319E7"
    "phase-3:Enrichment Spoke:1D76DB"
    "phase-4:Renewal & PLE:0E8A16"
    "phase-5:Grafana Dashboard:D93F0B"
    "phase-6:Verification & QA:E99695"
)

for phase_info in "${PHASES[@]}"; do
    IFS=':' read -r label_name label_desc label_color <<< "$phase_info"

    # Check if label exists
    if ! gh label list | grep -q "^$label_name"; then
        gh label create "$label_name" --description "$label_desc" --color "$label_color" 2>/dev/null || true
        echo -e "${GREEN}  ✅ Created label: $label_name${NC}"
    else
        echo -e "${BLUE}  ℹ️  Label already exists: $label_name${NC}"
    fi
done

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ✅ SYNC COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Project: $PROJECT_NAME${NC}"
echo -e "${GREEN}Project Number: #$PROJECT_NUMBER${NC}"
echo -e "${GREEN}Repository: $REPO_OWNER/$REPO_NAME${NC}"
echo -e "${GREEN}Tasks Processed: $TASK_COUNT${NC}"
echo -e "${GREEN}  • Completed: $COMPLETED_COUNT${NC}"
echo -e "${GREEN}  • Pending: $PENDING_COUNT${NC}"
echo ""
echo -e "${BLUE}View project:${NC}"
echo -e "https://github.com/users/$REPO_OWNER/projects/$PROJECT_NUMBER"
echo ""
echo -e "${BLUE}View issues:${NC}"
echo -e "https://github.com/$REPO_OWNER/$REPO_NAME/issues?q=label%3Asvg-ple"
echo ""
echo -e "${YELLOW}💡 TIP: You can manually update issue status in GitHub Projects UI${NC}"
echo -e "${YELLOW}   and it will be reflected across all views.${NC}"
echo ""
