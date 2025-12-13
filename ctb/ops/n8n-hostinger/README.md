# N8N Self-Hosted Deployment on Hostinger VPS

Complete guide for deploying n8n on Hostinger VPS with Neon PostgreSQL backend

---

## 📋 Overview

**Current:** n8n cloud ($20/month, execution limits)
**Target:** Self-hosted on Hostinger VPS ($10-20/month, unlimited)
**Savings:** $120-240/year + no execution limits
**Database:** Neon PostgreSQL (shared with barton-outreach-core)
**Purpose:** PLE automation workflows (enrichment, movement detection, outreach)

---

## 🏗️ Architecture

```
Internet
   ↓
NGINX (Reverse Proxy + SSL)
   ↓
Docker Container (n8n)
   ↓
Neon PostgreSQL (Remote)
```

**Components:**
- **Hostinger VPS:** Ubuntu 22.04/24.04, 2GB RAM, 50GB disk
- **Docker + Docker Compose:** Container runtime
- **NGINX:** Reverse proxy with Let's Encrypt SSL
- **n8n:** Latest Docker image
- **Neon PostgreSQL:** Serverless database (external)

---

## 📁 Files in This Directory

```
ctb/ops/n8n-hostinger/
├── README.md                    # This file
├── docker-compose.yml           # n8n Docker configuration
├── .env.example                 # Environment variables template
├── nginx-n8n.conf               # NGINX reverse proxy config
├── setup.sh                     # Automated setup script
├── backup.sh                    # Backup script (add to cron)
└── migration-guide.md           # Cloud → Self-hosted migration
```

---

## 🚀 Quick Start (5 Steps)

### Prerequisites

From Dave:
1. ✅ Hostinger VPS IP address
2. ✅ SSH credentials (root or sudo user)
3. ✅ Desired subdomain (e.g., `n8n.svgagency.com`)
4. ✅ Neon PostgreSQL connection string
5. ✅ Export of current n8n cloud workflows

### Step 1: Prepare VPS

```bash
# SSH into VPS
ssh root@YOUR_VPS_IP

# Create deployment directory
mkdir -p /opt/n8n
cd /opt/n8n
```

### Step 2: Upload Files

From your local machine:

```bash
# Upload files to VPS
scp docker-compose.yml root@YOUR_VPS_IP:/opt/n8n/
scp .env.example root@YOUR_VPS_IP:/opt/n8n/.env
scp nginx-n8n.conf root@YOUR_VPS_IP:/etc/nginx/sites-available/n8n
scp setup.sh root@YOUR_VPS_IP:/opt/n8n/
scp backup.sh root@YOUR_VPS_IP:/opt/n8n/
```

### Step 3: Configure Environment

On VPS:

```bash
cd /opt/n8n

# Edit .env file
nano .env

# REQUIRED values to set:
# - N8N_DOMAIN (e.g., n8n.svgagency.com)
# - NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD
# - N8N_ENCRYPTION_KEY (generate with: openssl rand -base64 32)
# - N8N_BASIC_AUTH_USER, N8N_BASIC_AUTH_PASSWORD
```

### Step 4: Run Setup Script

```bash
chmod +x setup.sh
sudo bash setup.sh
```

**What it does:**
- Installs Docker + Docker Compose
- Installs NGINX
- Installs Certbot (Let's Encrypt)
- Configures firewall (UFW)
- Deploys n8n container
- Obtains SSL certificate
- Starts n8n

### Step 5: Access n8n

1. Open browser: `https://n8n.svgagency.com`
2. Login with Basic Auth credentials from `.env`
3. Import workflows (see migration-guide.md)

---

## 🔧 Manual Setup (If Automated Fails)

### Install Docker

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Install NGINX

```bash
sudo apt-get install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Configure Firewall

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### Deploy n8n

```bash
cd /opt/n8n
docker-compose up -d

# View logs
docker-compose logs -f
```

### Configure NGINX

```bash
# Copy nginx config
sudo cp nginx-n8n.conf /etc/nginx/sites-available/n8n

# Enable site
sudo ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/n8n

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### Obtain SSL Certificate

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate (replace with your domain)
sudo certbot --nginx -d n8n.svgagency.com

# Auto-renewal is set up automatically
```

---

## 🗄️ Database Configuration

### Neon PostgreSQL Connection

n8n uses the **same Neon database** as barton-outreach-core:

```bash
# In .env:
NEON_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE=Marketing DB
NEON_USER=Marketing DB_owner
NEON_PASSWORD=npg_OsE4Z2oPCpiT
```

### Database Tables Created

n8n automatically creates these tables:

- `execution_entity` - Workflow execution logs
- `workflow_entity` - Workflow definitions
- `credentials_entity` - Encrypted credentials
- `tag_entity` - Workflow tags
- `webhook_entity` - Webhook registrations
- `settings_entity` - n8n settings
- `installed_packages` - Custom nodes
- `installed_nodes` - Node definitions

### Verify Database Connection

```bash
# Check n8n logs
docker-compose logs n8n | grep -i database

# Should see:
# "Database type: postgresdb"
# "Database connected successfully"
```

---

## 🔒 Security

### Firewall (UFW)

```bash
# Check status
sudo ufw status

# Should allow:
# 22/tcp   - SSH
# 80/tcp   - HTTP (for Let's Encrypt)
# 443/tcp  - HTTPS (for n8n)
```

### Basic Authentication

n8n UI is protected by Basic Auth (configured in `.env`):

```bash
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<strong-password>
```

### IP Whitelisting (Optional)

Edit `nginx-n8n.conf` to restrict access by IP:

```nginx
location / {
    allow YOUR_OFFICE_IP;
    allow YOUR_HOME_IP;
    deny all;

    proxy_pass http://localhost:5678;
    ...
}
```

### SSH Hardening

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use SSH keys instead of passwords
ssh-copy-id user@YOUR_VPS_IP

# Restart SSH
sudo systemctl restart sshd
```

### SSL Certificate Auto-Renewal

Certbot auto-renews certificates:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl status certbot.timer
```

---

## 💾 Backups

### Automated Daily Backups

Set up cron job:

```bash
# Make backup script executable
chmod +x /opt/n8n/backup.sh

# Add to crontab
sudo crontab -e

# Add this line (daily at 2 AM):
0 2 * * * /opt/n8n/backup.sh
```

### Manual Backup

```bash
cd /opt/n8n
sudo bash backup.sh
```

**Backs up:**
- n8n data volume (workflows, executions, credentials)
- Configuration files (docker-compose.yml, .env)

**Backup location:** `/opt/n8n-backups/`

**Retention:** 30 days (configurable in backup.sh)

### Restore from Backup

```bash
# List backups
ls -lh /opt/n8n-backups/

# Restore data volume
docker run --rm \
  -v n8n_data:/target \
  -v /opt/n8n-backups:/backup \
  alpine \
  sh -c 'cd /target && tar xzf /backup/n8n_backup_YYYYMMDD_HHMMSS.tar.gz'

# Restart n8n
cd /opt/n8n
docker-compose restart
```

---

## 📊 Monitoring

### View Logs

```bash
cd /opt/n8n

# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Filter for errors
docker-compose logs | grep -i error
```

### Check Container Status

```bash
docker-compose ps

# Should show:
# n8n - Up - healthy
```

### Check Resource Usage

```bash
# Container stats
docker stats n8n

# Disk usage
docker system df

# n8n data volume size
docker volume inspect n8n_data
```

### Health Check

n8n container includes health check:

```bash
# Check health status
docker inspect n8n | grep -A 10 Health

# Manual health check
curl http://localhost:5678/healthz
```

### NGINX Access Logs

```bash
# View access logs
sudo tail -f /var/log/nginx/n8n-access.log

# View error logs
sudo tail -f /var/log/nginx/n8n-error.log
```

---

## 🔄 Maintenance

### Update n8n

```bash
cd /opt/n8n

# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# Verify version
docker-compose logs | grep "Version:"
```

### Restart n8n

```bash
cd /opt/n8n
docker-compose restart

# Or stop and start
docker-compose stop
docker-compose start
```

### Reset n8n (Nuclear Option)

⚠️ **WARNING:** This deletes all workflows and executions!

```bash
cd /opt/n8n
docker-compose down -v  # -v removes volumes
docker-compose up -d
```

### Clean Up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

---

## 🐛 Troubleshooting

### n8n won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Port 5678 already in use
# - Database connection failed
# - Invalid .env values

# Verify .env file
cat .env | grep -v "^#" | grep -v "^$"
```

### Can't access n8n UI

1. Check NGINX is running:
   ```bash
   sudo systemctl status nginx
   ```

2. Check SSL certificate:
   ```bash
   sudo certbot certificates
   ```

3. Check DNS:
   ```bash
   dig n8n.svgagency.com
   # Should show VPS IP
   ```

4. Check firewall:
   ```bash
   sudo ufw status
   # Should allow 80, 443
   ```

### Webhooks not firing

1. Check webhook URL in workflow
2. Verify NGINX is forwarding `/webhook` paths
3. Test with curl:
   ```bash
   curl -X POST https://n8n.svgagency.com/webhook/YOUR_ID \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

4. Check n8n logs:
   ```bash
   docker-compose logs | grep webhook
   ```

### Database connection error

1. Verify Neon credentials in `.env`
2. Test connection from VPS:
   ```bash
   psql "postgresql://USER:PASS@HOST:5432/DATABASE?sslmode=require"
   ```

3. Check Neon console for connection limits

### High memory usage

```bash
# Check Docker stats
docker stats n8n

# If high, restart:
docker-compose restart

# Or increase VPS RAM
```

---

## 📚 Resources

- **n8n Docs:** https://docs.n8n.io/
- **n8n Self-Hosting:** https://docs.n8n.io/hosting/
- **Docker Compose:** https://docs.docker.com/compose/
- **NGINX:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/
- **Neon Docs:** https://neon.tech/docs

---

## 💰 Cost Breakdown

**Cloud n8n:**
- Monthly: $20
- Annual: $240
- Execution limits apply

**Self-Hosted (Hostinger VPS):**
- VPS: $10-20/month
- Annual: $120-240
- **Unlimited executions!**

**Savings:** $120-240/year + no limits

---

## ✅ Success Checklist

After deployment:

- [ ] n8n accessible at `https://n8n.svgagency.com`
- [ ] Basic Auth login working
- [ ] SSL certificate valid (green padlock)
- [ ] Database connected to Neon
- [ ] Workflows imported from cloud
- [ ] Webhooks firing correctly
- [ ] Backups configured (cron job)
- [ ] Firewall enabled
- [ ] Logs rotating correctly
- [ ] Resource usage acceptable

---

## 🆘 Emergency Contacts

**Support:**
- n8n Community: https://community.n8n.io/
- Hostinger Support: https://www.hostinger.com/support
- Neon Support: https://neon.tech/docs/introduction/support

**Quick Commands:**

```bash
# Emergency restart
cd /opt/n8n && docker-compose restart

# View errors
docker-compose logs --tail=50 | grep -i error

# Restore from backup
bash /opt/n8n/backup.sh

# Check all services
systemctl status nginx docker
docker-compose ps
```

---

**Last Updated:** 2025-11-25
**Version:** 1.0
**Status:** Production Ready
**Deployment Time:** ~2 hours
**Maintenance:** Minimal (automated backups, auto-updates)
