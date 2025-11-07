#!/usr/bin/env bash
# ====================================================================
# RESTART GRAFANA - APPLY NO-AUTH CHANGES
# ====================================================================
# Purpose: Restart Grafana to apply authentication disable
# Usage: ./restart-grafana.sh
# ====================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}  RESTARTING GRAFANA TO DISABLE AUTHENTICATION${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "This will restart Grafana so you can access it without login"
echo ""
read -p "Press Enter to continue..."

echo ""
echo -e "${YELLOW}[1/2] Stopping Grafana...${NC}"
docker compose down

echo ""
echo -e "${YELLOW}[2/2] Starting Grafana with no-auth configuration...${NC}"
docker compose up -d

echo ""
echo -e "${YELLOW}Waiting for Grafana to start (30 seconds)...${NC}"
sleep 30

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  SUCCESS! Grafana is now running without authentication${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo "You can now access Grafana without login:"
echo ""
echo -e "  URL: ${BLUE}http://localhost:3000${NC}"
echo ""
echo "Just open that URL in your browser - no credentials needed!"
echo ""
echo "Your dashboards:"
echo -e "  Overview: ${BLUE}http://localhost:3000/d/barton-outreach-overview${NC}"
echo -e "  All Dashboards: ${BLUE}http://localhost:3000/dashboards${NC}"
echo ""
echo -e "${GREEN}================================================================${NC}"
