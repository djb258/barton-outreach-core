@echo off
REM N8N Audit Script - Run this on Windows
REM This will SSH into the Hostinger VPS and audit the n8n installation

echo ===================================================
echo N8N HOSTINGER AUDIT
echo ===================================================
echo.
echo This will SSH into 72.61.65.44 and check n8n status
echo Password: Hammerhostinger15522?
echo.
echo Press any key to continue...
pause >nul

ssh root@72.61.65.44 "bash -s" << 'AUDIT_SCRIPT'
#!/bin/bash
echo "========================================"
echo "N8N INSTALLATION AUDIT"
echo "VPS: srv1153077.hstgr.cloud"
echo "Date: $(date)"
echo "========================================"
echo ""

echo "--- SYSTEM INFO ---"
hostname
cat /etc/os-release | grep PRETTY_NAME
uptime -p
echo "CPU: $(nproc) cores"
free -h | grep Mem
echo ""

echo "--- DOCKER CHECK ---"
which docker && docker --version || echo "Docker NOT installed"
if command -v docker &> /dev/null; then
    echo "Docker containers:"
    docker ps -a | grep n8n || echo "No n8n containers found"
fi
echo ""

echo "--- N8N PROCESSES ---"
ps aux | grep '[n]8n' || echo "No n8n processes running"
echo ""

echo "--- LISTENING PORTS ---"
ss -tlnp | grep -E ':(5678|80|443)' || echo "Ports 5678/80/443 not listening"
echo ""

echo "--- NGINX ---"
which nginx && nginx -v 2>&1 || echo "nginx NOT installed"
if command -v nginx &> /dev/null; then
    echo "Sites enabled:"
    ls /etc/nginx/sites-enabled/ 2>/dev/null
    echo ""
    echo "N8N configs:"
    grep -r 'n8n\|5678' /etc/nginx/sites-enabled/ 2>/dev/null | head -3
fi
echo ""

echo "--- N8N DIRECTORIES ---"
ls -la /opt/n8n 2>/dev/null || echo "/opt/n8n NOT found"
ls -la /root/.n8n 2>/dev/null || echo "/root/.n8n NOT found"
echo ""

echo "--- TEST LOCALHOST:5678 ---"
curl -I http://localhost:5678 2>&1 | head -5 || echo "No response on localhost:5678"
echo ""

echo "========================================"
echo "AUDIT COMPLETE"
echo "========================================"
AUDIT_SCRIPT

echo.
echo ===================================================
echo Audit complete! Review output above.
echo ===================================================
pause
