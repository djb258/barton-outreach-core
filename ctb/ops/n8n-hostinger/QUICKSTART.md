# N8N Hostinger Setup - Quick Reference Card

**For:** Dave Barton (djb258)
**Time:** ~2 hours total
**Savings:** $120-240/year + unlimited executions

---

## Before You Start - Information Needed

1. **Hostinger VPS:**
   - [ ] IP address: `___.___.___.__`
   - [ ] SSH username: `root` or `_______`
   - [ ] SSH password/key: `_______`

2. **Domain/Subdomain:**
   - [ ] Choose: `n8n.svgagency.com` OR `automation.svgagency.com` OR `_______`

3. **Neon Database:**
   - [ ] Already have it! (same as barton-outreach-core)

4. **n8n Cloud:**
   - [ ] Export workflows: Settings → Workflows → Export All
   - [ ] Download JSON file
   - [ ] List credentials (can't export, must recreate)

---

## Step-by-Step (Copy-Paste Ready)

### 1. SSH into VPS (2 minutes)

```bash
ssh root@YOUR_VPS_IP
# Enter password when prompted
```

### 2. Create Directory & Upload Files (5 minutes)

```bash
# On VPS
mkdir -p /opt/n8n
cd /opt/n8n
```

**From your local machine** (new terminal):

```bash
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\ctb\ops\n8n-hostinger"

# Upload all files
scp docker-compose.yml root@YOUR_VPS_IP:/opt/n8n/
scp .env.example root@YOUR_VPS_IP:/opt/n8n/.env
scp nginx-n8n.conf root@YOUR_VPS_IP:/etc/nginx/sites-available/n8n
scp setup.sh root@YOUR_VPS_IP:/opt/n8n/
scp backup.sh root@YOUR_VPS_IP:/opt/n8n/
```

### 3. Configure Environment (5 minutes)

**Back on VPS:**

```bash
cd /opt/n8n
nano .env
```

**Edit these values:**

```bash
# Domain
N8N_DOMAIN=n8n.svgagency.com  # <-- CHANGE THIS

# Neon Database (copy from barton-outreach-core/.env)
NEON_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE=Marketing DB
NEON_USER=Marketing DB_owner
NEON_PASSWORD=npg_OsE4Z2oPCpiT

# Security (generate encryption key)
N8N_ENCRYPTION_KEY=PASTE_RESULT_OF_openssl_rand_base64_32

# Basic Auth
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=CHANGE_TO_STRONG_PASSWORD
```

**Generate encryption key:**

```bash
# Run this to generate key
openssl rand -base64 32

# Copy result and paste into .env
```

**Save file:** `Ctrl+X`, `Y`, `Enter`

### 4. Update DNS (5 minutes)

**Before running setup, configure DNS!**

1. Go to your DNS provider (Cloudflare, Namecheap, etc.)
2. Add A record:
   - **Name:** `n8n` (or `automation`)
   - **Type:** `A`
   - **Value:** `YOUR_VPS_IP`
   - **TTL:** `300` (5 minutes)

3. Wait for DNS propagation (test with):
   ```bash
   dig n8n.svgagency.com
   # Should show your VPS IP
   ```

### 5. Run Automated Setup (60-90 minutes)

```bash
cd /opt/n8n
chmod +x setup.sh
sudo bash setup.sh
```

**What it does:**
- ✅ Installs Docker + Docker Compose
- ✅ Installs NGINX
- ✅ Configures firewall
- ✅ Obtains SSL certificate (Let's Encrypt)
- ✅ Starts n8n

**You'll be prompted for:**
- Email for Let's Encrypt notifications
- Confirmation to obtain SSL cert

### 6. Access n8n (2 minutes)

```bash
# Open browser
https://n8n.svgagency.com

# Login with Basic Auth:
Username: admin (or what you set in .env)
Password: <your password from .env>
```

### 7. Import Workflows (30 minutes)

1. Click **Workflows** (left sidebar)
2. Click **Import from file**
3. Select `n8n-cloud-workflows-export.json`
4. Click **Import**

**For each workflow:**
- ✅ Open workflow
- ✅ Check for credential warnings (yellow)
- ✅ Recreate credentials (see migration-guide.md)
- ✅ Test execution
- ✅ Enable workflow

### 8. Update Webhook URLs (15 minutes)

If external services call your n8n webhooks:

**Old:** `https://dbarton.app.n8n.cloud/webhook/abc123`
**New:** `https://n8n.svgagency.com/webhook/abc123`

**Update in:**
- GitHub webhooks
- Stripe webhooks
- Any integrations calling n8n

### 9. Set Up Backups (5 minutes)

```bash
# Make backup script executable
chmod +x /opt/n8n/backup.sh

# Test backup
sudo bash /opt/n8n/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add this line:
0 2 * * * /opt/n8n/backup.sh
```

### 10. Cancel Cloud Subscription (After 1 week!)

⚠️ **Wait 1 week** to ensure self-hosted is stable!

1. Login to n8n cloud
2. Settings → Billing
3. Cancel subscription
4. Save **$240/year**!

---

## Useful Commands (Keep This Handy!)

```bash
# View logs
cd /opt/n8n && docker-compose logs -f

# Restart n8n
cd /opt/n8n && docker-compose restart

# Stop n8n
cd /opt/n8n && docker-compose stop

# Start n8n
cd /opt/n8n && docker-compose start

# Update n8n
cd /opt/n8n && docker-compose pull && docker-compose up -d

# Backup now
sudo bash /opt/n8n/backup.sh

# Check disk space
df -h

# Check memory
free -h

# View NGINX logs
sudo tail -f /var/log/nginx/n8n-error.log
```

---

## Troubleshooting (Common Issues)

### Can't access n8n UI

1. Check DNS: `dig n8n.svgagency.com`
2. Check NGINX: `sudo systemctl status nginx`
3. Check firewall: `sudo ufw status`
4. Check SSL: `sudo certbot certificates`

### Workflows failing

1. Check credentials recreated
2. Check webhook URLs updated
3. View logs: `docker-compose logs | grep error`

### Database connection error

1. Verify `.env` has correct Neon credentials
2. Test connection:
   ```bash
   psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require"
   ```

---

## Emergency Restart

```bash
cd /opt/n8n && docker-compose restart && docker-compose logs -f
```

---

## Success Checklist

- [ ] n8n accessible at `https://n8n.svgagency.com`
- [ ] Can login with Basic Auth
- [ ] SSL certificate valid (green padlock)
- [ ] Workflows imported
- [ ] Credentials recreated
- [ ] Test workflow executes successfully
- [ ] Webhooks firing (test with curl)
- [ ] Backups running daily
- [ ] Cloud subscription canceled (after 1 week)

---

## Cost Savings Summary

| Item | Cloud | Self-Hosted | Savings |
|------|-------|-------------|---------|
| Monthly | $20 | $10-20 | $0-10/mo |
| Annual | $240 | $120-240 | $0-120/yr |
| Executions | Limited | **Unlimited** | Priceless! |

**ROI:** Setup time (2 hours) pays for itself in 1-2 months!

---

## Support

**Issues?**
- Check `README.md` for detailed docs
- Check `migration-guide.md` for workflow migration help
- n8n Community: https://community.n8n.io/

**Files:**
- `/opt/n8n/` - All n8n files
- `/opt/n8n-backups/` - Daily backups
- `/var/log/nginx/` - NGINX logs

---

**Ready? Let's go! Start with Step 1 above.**

**Time Budget:**
- Setup: 90 minutes
- Migration: 60 minutes
- Testing: 30 minutes
- **Total: ~3 hours**

**Savings:** $120-240/year + unlimited automation!

---

**Last Updated:** 2025-11-25
**Author:** Claude Code
**Status:** Production Ready
