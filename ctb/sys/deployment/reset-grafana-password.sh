#!/usr/bin/env bash
# ====================================================================
# GRAFANA PASSWORD RESET SCRIPT (Linux/macOS)
# ====================================================================
# Purpose: Reset Grafana admin password to 'changeme'
# Usage: ./reset-grafana-password.sh
# ====================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  GRAFANA PASSWORD RESET UTILITY${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "This script will reset your Grafana admin password to: changeme"
echo ""
echo "Container: barton-outreach-grafana"
echo "Username: admin"
echo "New Password: changeme"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo -e "${YELLOW}[1/3] Checking if Docker is running...${NC}"
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running or not installed${NC}"
    echo ""
    echo "Please start Docker and try again."
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

echo ""
echo -e "${YELLOW}[2/3] Checking if Grafana container exists...${NC}"
if ! docker ps -a --filter "name=barton-outreach-grafana" --format "{{.Names}}" | grep -q "barton-outreach-grafana"; then
    echo -e "${RED}ERROR: Grafana container 'barton-outreach-grafana' not found${NC}"
    echo ""
    echo "Please start Grafana first with: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Container found${NC}"

echo ""
echo -e "${YELLOW}[3/3] Resetting admin password...${NC}"
if docker exec -it barton-outreach-grafana grafana-cli admin reset-admin-password changeme; then
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}  SUCCESS! Password reset complete${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo "You can now login to Grafana with:"
    echo ""
    echo -e "  URL: ${BLUE}http://localhost:3000${NC}"
    echo -e "  Username: ${BLUE}admin${NC}"
    echo -e "  Password: ${BLUE}changeme${NC}"
    echo ""
    echo "Grafana will prompt you to change the password after login."
    echo ""
    echo -e "${GREEN}================================================================${NC}"
else
    echo ""
    echo -e "${RED}ERROR: Password reset failed${NC}"
    echo ""
    echo "Try these alternatives:"
    echo "1. Restart Grafana: docker compose restart grafana"
    echo "2. Recreate container: docker compose down && docker compose up -d"
    echo "3. See GRAFANA_LOGIN_TROUBLESHOOTING.md for more options"
    echo ""
    exit 1
fi
