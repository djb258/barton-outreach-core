#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# N8N EXISTING INSTALLATION AUDIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VPS: srv1153077.hstgr.cloud (72.61.65.44)
# Purpose: Audit what's already installed before making changes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "N8N EXISTING INSTALLATION AUDIT"
echo "VPS: srv1153077.hstgr.cloud (72.61.65.44)"
echo "Date: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. SYSTEM INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SYSTEM INFO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo ""
echo "Resources:"
echo "  CPU: $(nproc) cores"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  Disk: $(df -h / | tail -1 | awk '{print $2}') total, $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. N8N INSTALLATION CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "N8N INSTALLATION DETECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for n8n binary
if command -v n8n &> /dev/null; then
    echo "✓ n8n binary found: $(which n8n)"
    echo "  Version: $(n8n --version 2>/dev/null || echo 'Could not determine')"
else
    echo "✗ n8n binary not found in PATH"
fi
echo ""

# Check for Docker
if command -v docker &> /dev/null; then
    echo "✓ Docker installed: $(docker --version)"
    echo ""
    echo "  Docker containers:"
    docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -i n8n || echo "  No n8n containers found"
else
    echo "✗ Docker not installed"
fi
echo ""

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose installed: $(docker-compose --version)"

    # Check for docker-compose.yml files
    echo ""
    echo "  Looking for docker-compose.yml files:"
    find /opt /root /home -name "docker-compose.yml" 2>/dev/null | while read file; do
        if grep -q "n8n" "$file" 2>/dev/null; then
            echo "  ✓ Found n8n config: $file"
        fi
    done
else
    echo "✗ Docker Compose not installed"
fi
echo ""

# Check for PM2
if command -v pm2 &> /dev/null; then
    echo "✓ PM2 installed: $(pm2 --version)"
    echo ""
    echo "  PM2 processes:"
    pm2 list | grep -i n8n || echo "  No n8n processes in PM2"
else
    echo "✗ PM2 not installed"
fi
echo ""

# Check for systemd service
if systemctl list-units --type=service | grep -q n8n; then
    echo "✓ n8n systemd service found"
    echo ""
    systemctl status n8n --no-pager || true
else
    echo "✗ No n8n systemd service found"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. N8N RUNNING PROCESSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RUNNING PROCESSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ps aux | grep -i n8n | grep -v grep || echo "No n8n processes found"
echo ""

# Check listening ports
echo "Ports listening:"
if command -v ss &> /dev/null; then
    ss -tlnp | grep -E ":(5678|3000|8080|80|443)" || echo "No relevant ports listening"
else
    netstat -tlnp | grep -E ":(5678|3000|8080|80|443)" || echo "No relevant ports listening"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. N8N CONFIGURATION FILES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "N8N CONFIGURATION FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Common n8n data locations
COMMON_LOCATIONS=(
    "/opt/n8n"
    "/root/.n8n"
    "/home/*/.n8n"
    "/var/lib/n8n"
)

for location in "${COMMON_LOCATIONS[@]}"; do
    if ls -d $location 2>/dev/null; then
        echo "✓ Found: $location"
        ls -lah $location 2>/dev/null | head -20
        echo ""
    fi
done

# Look for .env files
echo "Environment files:"
find /opt /root -name ".env" 2>/dev/null | while read file; do
    if grep -q "N8N\|n8n" "$file" 2>/dev/null; then
        echo "  ✓ Found n8n .env: $file"
        echo "    Preview (non-sensitive):"
        grep -E "^N8N_|^DB_|^WEBHOOK" "$file" 2>/dev/null | grep -v "PASSWORD\|SECRET\|KEY" | head -10
    fi
done
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. DATABASE CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DATABASE CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for SQLite databases (default n8n)
echo "SQLite databases:"
find /opt /root /var -name "*.db" -o -name "*.sqlite" 2>/dev/null | grep -i n8n || echo "None found"
echo ""

# Check for PostgreSQL connection
if command -v psql &> /dev/null; then
    echo "✓ psql (PostgreSQL client) installed"
else
    echo "✗ psql not installed"
fi
echo ""

# Look for database config in .env files
echo "Database config (from .env files):"
find /opt /root -name ".env" 2>/dev/null | while read file; do
    if grep -q "DB_TYPE\|DB_POSTGRESDB" "$file" 2>/dev/null; then
        echo "  File: $file"
        grep -E "^DB_TYPE|^DB_POSTGRESDB_HOST|^DB_POSTGRESDB_DATABASE" "$file" 2>/dev/null | sed 's/PASSWORD=.*/PASSWORD=***REDACTED***/'
    fi
done
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. WEB SERVER (NGINX/APACHE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WEB SERVER CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check NGINX
if command -v nginx &> /dev/null; then
    echo "✓ NGINX installed: $(nginx -v 2>&1)"
    echo ""
    echo "  NGINX status:"
    systemctl status nginx --no-pager || service nginx status
    echo ""
    echo "  NGINX sites enabled:"
    ls -l /etc/nginx/sites-enabled/ 2>/dev/null || echo "  Directory not found"
    echo ""
    echo "  N8N-related configs:"
    grep -r "n8n\|5678" /etc/nginx/sites-enabled/ /etc/nginx/sites-available/ 2>/dev/null || echo "  No n8n configs found"
else
    echo "✗ NGINX not installed"
fi
echo ""

# Check Apache
if command -v apache2 &> /dev/null; then
    echo "✓ Apache installed"
    systemctl status apache2 --no-pager || service apache2 status
else
    echo "✗ Apache not installed"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. SSL CERTIFICATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SSL CERTIFICATES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v certbot &> /dev/null; then
    echo "✓ Certbot installed: $(certbot --version)"
    echo ""
    echo "  Certificates:"
    certbot certificates 2>/dev/null || echo "  No certificates found or error accessing"
else
    echo "✗ Certbot not installed"
fi
echo ""

# Check for manual SSL certs
if [ -d "/etc/letsencrypt/live" ]; then
    echo "Let's Encrypt certificates found:"
    ls -l /etc/letsencrypt/live/ 2>/dev/null
else
    echo "No Let's Encrypt directory found"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. FIREWALL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FIREWALL STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v ufw &> /dev/null; then
    echo "✓ UFW installed"
    ufw status verbose || echo "UFW not active"
else
    echo "✗ UFW not installed"
fi
echo ""

# Check iptables
if command -v iptables &> /dev/null; then
    echo "Iptables rules (first 20):"
    iptables -L -n | head -20
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. NETWORK TEST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NETWORK ACCESSIBILITY TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test localhost access
echo "Testing localhost:5678..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5678 2>/dev/null | grep -q "200\|302\|401"; then
    echo "✓ n8n responding on localhost:5678"
    echo "  Response:"
    curl -s -I http://localhost:5678 2>/dev/null | head -5
else
    echo "✗ n8n not responding on localhost:5678"
fi
echo ""

# Test external access (if public IP)
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null)
if [ ! -z "$PUBLIC_IP" ]; then
    echo "Public IP: $PUBLIC_IP"
    echo "Testing external access..."
    curl -s -I http://$PUBLIC_IP 2>/dev/null | head -5 || echo "Not accessible externally on port 80"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. SUMMARY & RECOMMENDATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "AUDIT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Save this output and review with Dave to determine next steps:"
echo ""
echo "KEY QUESTIONS TO ANSWER:"
echo "1. Is n8n running? (Check processes and port 5678)"
echo "2. How is it installed? (Docker/npm/systemd/PM2?)"
echo "3. What database is it using? (SQLite or PostgreSQL?)"
echo "4. Is NGINX configured? (Reverse proxy + SSL?)"
echo "5. Is SSL configured? (Let's Encrypt certificates?)"
echo "6. What domain is it configured for?"
echo ""
echo "NEXT STEPS:"
echo "1. Review this output"
echo "2. Decide: Reconfigure existing OR start fresh"
echo "3. If reconfiguring: Migrate to Neon PostgreSQL"
echo "4. If starting fresh: Use deployment scripts from n8n-hostinger/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Audit complete: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
