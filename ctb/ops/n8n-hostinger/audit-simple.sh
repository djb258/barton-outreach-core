#!/bin/bash
echo "========================================"
echo "N8N INSTALLATION AUDIT"
echo "VPS: srv1153077.hstgr.cloud (72.61.65.44)"
echo "Date: $(date)"
echo "========================================"
echo ""

echo "--- SYSTEM INFO ---"
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Uptime: $(uptime -p)"
echo "CPU: $(nproc) cores"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo ""

echo "--- N8N BINARY ---"
which n8n && n8n --version || echo "n8n binary not in PATH"
echo ""

echo "--- DOCKER ---"
which docker && docker --version || echo "Docker not installed"
if command -v docker &> /dev/null; then
    echo "Docker containers:"
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -i n8n || echo "No n8n containers"
fi
echo ""

echo "--- DOCKER COMPOSE ---"
which docker-compose && docker-compose --version || echo "Docker Compose not installed"
echo "Looking for docker-compose.yml files:"
find /opt /root -name "docker-compose.yml" 2>/dev/null | head -5
echo ""

echo "--- PM2 ---"
which pm2 && pm2 list | grep -i n8n || echo "PM2 not installed or no n8n processes"
echo ""

echo "--- SYSTEMD SERVICE ---"
systemctl list-units --type=service | grep n8n || echo "No n8n systemd service"
echo ""

echo "--- RUNNING PROCESSES ---"
ps aux | grep n8n | grep -v grep || echo "No n8n processes running"
echo ""

echo "--- LISTENING PORTS ---"
ss -tlnp | grep -E ":(5678|3000|8080|80|443)" || echo "No relevant ports"
echo ""

echo "--- NGINX ---"
which nginx && nginx -v 2>&1 || echo "nginx not installed"
if command -v nginx &> /dev/null; then
    echo "nginx status:"
    systemctl status nginx --no-pager 2>&1 | head -5
    echo ""
    echo "nginx sites-enabled:"
    ls /etc/nginx/sites-enabled/ 2>/dev/null
    echo ""
    echo "nginx configs with n8n:"
    grep -r "n8n\|5678" /etc/nginx/sites-enabled/ 2>/dev/null | head -5
fi
echo ""

echo "--- N8N DATA DIRECTORIES ---"
ls -la /opt/n8n 2>/dev/null || echo "/opt/n8n not found"
echo ""
ls -la /root/.n8n 2>/dev/null || echo "/root/.n8n not found"
echo ""

echo "--- ENVIRONMENT FILES ---"
find /opt /root -name ".env" 2>/dev/null | while read f; do
    if grep -q "n8n\|N8N" "$f" 2>/dev/null; then
        echo "Found n8n .env: $f"
        echo "Config preview (non-sensitive):"
        grep -E "^N8N_|^DB_|^WEBHOOK" "$f" | grep -v "PASSWORD\|SECRET\|KEY" | head -5
        echo ""
    fi
done
echo ""

echo "--- DATABASE CONFIG ---"
echo "SQLite databases:"
find /opt /root -name "*.db" -o -name "*.sqlite" 2>/dev/null | grep -i n8n || echo "None found"
echo ""
echo "PostgreSQL client:"
which psql && psql --version || echo "psql not installed"
echo ""

echo "--- SSL CERTIFICATES ---"
which certbot && certbot certificates 2>/dev/null || echo "certbot not installed"
ls /etc/letsencrypt/live/ 2>/dev/null || echo "No Let's Encrypt certs"
echo ""

echo "--- FIREWALL ---"
which ufw && ufw status || echo "ufw not installed"
echo ""

echo "--- NETWORK TEST ---"
echo "Testing localhost:5678..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678 2>/dev/null)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "✓ n8n responding on localhost:5678 (HTTP $HTTP_CODE)"
    curl -s -I http://localhost:5678 2>/dev/null | head -3
else
    echo "✗ n8n not responding on localhost:5678 (HTTP $HTTP_CODE)"
fi
echo ""

echo "Public IP:"
curl -s ifconfig.me 2>/dev/null
echo ""

echo "========================================"
echo "AUDIT COMPLETE"
echo "========================================"
