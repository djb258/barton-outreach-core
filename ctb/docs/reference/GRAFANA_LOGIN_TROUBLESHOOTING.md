# 🔧 Grafana Login Troubleshooting Guide

**Issue:** Unable to login to Grafana at http://localhost:3000/login with admin/changeme

---

## 📋 Current Configuration

**From your files:**
- **.env file:** `GRAFANA_ADMIN_PASSWORD=changeme`
- **docker-compose.yml:** `GF_SECURITY_ADMIN_USER=admin`
- **Expected credentials:** admin / changeme

**The problem:** These credentials likely didn't take effect because the Grafana container was started before the .env file was created, or the Docker volume already has data with a different password.

---

## ✅ Solution 1: Reset Admin Password (Recommended)

### Step 1: Reset password using Grafana CLI

**Open your terminal/PowerShell and run:**

```bash
# Navigate to your repository
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"

# Reset the admin password to 'changeme'
docker exec -it barton-outreach-grafana grafana-cli admin reset-admin-password changeme
```

**Expected output:**
```
Admin password changed successfully ✔
```

### Step 2: Try logging in again

1. Go to http://localhost:3000/login
2. Username: `admin`
3. Password: `changeme`
4. Click "Log in"

**If this works, you're done!** Grafana will prompt you to change the password after first login.

---

## ✅ Solution 2: Restart Container with Correct Environment Variables

If the password reset didn't work, the container might need to be recreated:

### Step 1: Stop and remove the container (keeps data)

```bash
# Stop Grafana
docker compose down

# Or if using older Docker:
# docker-compose down
```

### Step 2: Remove the Grafana volume (⚠️ WARNING: This deletes all Grafana data!)

**Only do this if you haven't created any custom dashboards you want to keep:**

```bash
# Remove the volume
docker volume rm barton-outreach-core_grafana-storage

# Or list volumes first to confirm the name:
docker volume ls | grep grafana
```

### Step 3: Start Grafana again

```bash
# Start Grafana (will create fresh container with correct password)
docker compose up -d

# Wait 30 seconds for startup
timeout 30

# Check logs to verify it started
docker compose logs grafana | tail -20
```

### Step 4: Login with default credentials

1. Go to http://localhost:3000/login
2. Username: `admin`
3. Password: `changeme`
4. Grafana will prompt you to change the password

---

## ✅ Solution 3: Check What's Actually Running

### Step 1: Verify Grafana is running

```bash
# Check if container is running
docker ps | grep grafana

# Expected output:
# barton-outreach-grafana   grafana/grafana:latest   ...   Up 2 minutes   0.0.0.0:3000->3000/tcp
```

### Step 2: Check Grafana logs for auth errors

```bash
# View last 50 lines of logs
docker compose logs grafana --tail=50

# Or follow logs in real-time
docker compose logs -f grafana
```

**Look for:**
- `Invalid username or password` - Indicates wrong credentials
- `Database locked` - Indicates SQLite issue
- `Failed to initialize` - Indicates config problem

### Step 3: Check environment variables inside container

```bash
# Enter the container
docker exec -it barton-outreach-grafana bash

# Check environment variables
env | grep GF_

# Expected output should include:
# GF_SECURITY_ADMIN_USER=admin
# GF_SECURITY_ADMIN_PASSWORD=changeme

# Exit container
exit
```

---

## ✅ Solution 4: Manual Database Password Reset (Advanced)

If all else fails, you can directly edit the Grafana SQLite database:

### Step 1: Enter the Grafana container

```bash
docker exec -it barton-outreach-grafana bash
```

### Step 2: Install SQLite (if not present)

```bash
apk add sqlite
```

### Step 3: Reset the admin password in database

```bash
# Navigate to Grafana data directory
cd /var/lib/grafana

# Open the database
sqlite3 grafana.db

# Reset admin password (password: 'changeme' hashed with bcrypt)
UPDATE user SET password = '$2a$10$PprDZ0p.KkMJPkUY8N8WqOWdEMvDrKxHxbUJXO8hS5r3Y8h8qY9hK', salt = '' WHERE login = 'admin';

# Exit SQLite
.quit

# Exit container
exit
```

### Step 4: Restart Grafana

```bash
docker compose restart grafana
```

### Step 5: Login

- Username: `admin`
- Password: `changeme`

---

## 🔍 Diagnostic Commands

Run these to gather information:

### Check if Grafana is accessible

```bash
# Test if Grafana is responding
curl http://localhost:3000/api/health

# Expected output:
# {"commit":"...","database":"ok","version":"..."}
```

### Check Docker logs for startup errors

```bash
docker compose logs grafana | grep -i error
```

### Verify .env file is being read

```bash
# Check if .env file exists
cat .env | grep GRAFANA

# Expected output:
# GRAFANA_ADMIN_PASSWORD=changeme
```

### Check if port 3000 is actually open

```bash
# Windows PowerShell
netstat -ano | findstr :3000

# Expected output should show LISTENING on port 3000
```

---

## 🚨 Common Issues & Fixes

### Issue: "Connection refused" when accessing http://localhost:3000

**Cause:** Grafana container not running

**Fix:**
```bash
# Start Grafana
docker compose up -d

# Wait 30 seconds
timeout 30

# Check status
docker compose ps
```

### Issue: "Invalid username or password" with admin/changeme

**Cause:** Grafana volume has old data with different password

**Fix:** Use Solution 1 (reset password) or Solution 2 (recreate volume)

### Issue: Can't exec into container (Permission denied)

**Cause:** Windows Docker Desktop not running or permissions issue

**Fix:**
1. Open Docker Desktop
2. Ensure it's running
3. Try command again

### Issue: Password reset says "Error: user not found"

**Cause:** Admin user doesn't exist or database is corrupted

**Fix:**
```bash
# Create new admin user
docker exec -it barton-outreach-grafana grafana-cli admin create --name="Admin" --login=admin --password=changeme

# Or recreate volume (Solution 2)
```

---

## ✅ Final Verification

Once you successfully login, verify your dashboard:

### Step 1: Access the Overview Dashboard

Navigate to: http://localhost:3000/d/barton-outreach-overview

**Expected panels:**
- 🏢 Total Companies
- 👥 Total Contacts
- ✅ Filled Slots
- ⚠️ Unresolved Errors
- 📊 Filled Slots by Role (pie chart)
- 🏆 Top 20 Companies by Contact Count
- 🚨 Resolution Queue Breakdown
- 📈 Company Growth (Last 30 Days)
- 👤 Contact Growth (Last 30 Days)

### Step 2: Verify Neon Datasource

1. Click ☰ menu → Connections → Data sources
2. Click "Neon PostgreSQL"
3. Scroll down and click "Save & test"
4. Should see: ✅ "Database Connection OK"

### Step 3: Test a panel query

1. Open Overview Dashboard
2. Click on "Total Companies" panel
3. Click "Edit" (pencil icon)
4. Should see query: `SELECT COUNT(*) FROM marketing.company_master`
5. Click "Run query"
6. Should see a number (your company count)

---

## 🔐 Security: Change Password After Login

**Important:** Once you successfully login with `changeme`, Grafana will prompt you to set a new password.

**Recommended password requirements:**
- At least 8 characters
- Mix of letters, numbers, and symbols
- Not "changeme" or "admin"

**Update .env file after changing:**
```bash
# Edit .env file
# Change: GRAFANA_ADMIN_PASSWORD=changeme
# To: GRAFANA_ADMIN_PASSWORD=your_new_secure_password
```

---

## 📞 Quick Reference Commands

```bash
# Check if running
docker ps | grep grafana

# View logs
docker compose logs grafana --tail=50

# Reset password (easiest)
docker exec -it barton-outreach-grafana grafana-cli admin reset-admin-password changeme

# Restart container
docker compose restart grafana

# Stop container
docker compose down

# Start container
docker compose up -d

# Remove volume (nuclear option - deletes all data)
docker volume rm barton-outreach-core_grafana-storage
```

---

## 🎯 Recommended Solution Order

**Try solutions in this order:**

1. ✅ **Solution 1** (Reset password) - Takes 10 seconds, no data loss
2. ✅ **Solution 3** (Check logs) - Diagnose the actual issue
3. ✅ **Solution 2** (Restart container) - May lose custom changes
4. ✅ **Solution 4** (Manual database edit) - Advanced, last resort

---

## 📚 Additional Resources

- **Grafana Troubleshooting:** https://grafana.com/docs/grafana/latest/troubleshooting/
- **Grafana CLI Reference:** https://grafana.com/docs/grafana/latest/cli/
- **Grafana Configuration:** https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/

---

**Created:** 2025-11-06
**For:** Grafana login issues at localhost:3000
**Status:** Ready to use
