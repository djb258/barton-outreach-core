# 🚀 Start Grafana — Ready to Launch!

**Date:** 2025-11-06
**Status:** ✅ Configured and Ready

---

## ✅ Configuration Complete

All configuration files have been created with your Neon credentials:

- ✅ `.env` - Environment variables configured
- ✅ `grafana/provisioning/datasources/neon.yml` - Neon PostgreSQL datasource configured
- ✅ `docker-compose.yml` - Grafana service configured
- ✅ `grafana/provisioning/dashboards/dashboard.yml` - Dashboard auto-provisioning configured
- ✅ `grafana/provisioning/dashboards/barton-outreach-dashboard.json` - Overview dashboard ready

---

## 🚀 Starting Grafana (Choose Your Method)

### Method 1: Docker Compose (Recommended)

**Start Grafana in detached mode:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f grafana
```

**Stop Grafana:**
```bash
docker-compose down
```

**Restart Grafana:**
```bash
docker-compose restart grafana
```

### Method 2: Docker Compose with Logs (Debug Mode)

**Start Grafana with live logs:**
```bash
docker-compose up
```

Press `Ctrl+C` to stop.

---

## 🌐 Accessing Grafana

### Step 1: Start Grafana
```bash
docker-compose up -d
```

### Step 2: Wait for Startup (30-60 seconds)

Check if Grafana is ready:
```bash
docker-compose logs grafana | grep "HTTP Server Listen"
```

Expected output:
```
grafana  | logger=http.server t=... msg="HTTP Server Listen" address=[::]:3000 protocol=http
```

### Step 3: Access Grafana UI

Open your browser and navigate to:
```
http://localhost:3000
```

### Step 4: Login

**Credentials:**
- **Username:** `admin`
- **Password:** `changeme` (from your .env file)

**⚠️ IMPORTANT:** Change the default password after first login!

---

## 📊 Verifying Neon Connection

### Step 1: Check Datasources

1. Login to Grafana (http://localhost:3000)
2. Click the **☰** menu (top left)
3. Navigate to **Connections** → **Data sources**
4. You should see **Neon PostgreSQL** listed
5. Click **Neon PostgreSQL**
6. Scroll down and click **Save & test**

**Expected result:**
```
✅ Database Connection OK
```

### Step 2: Verify Dashboard Loaded

1. Click the **☰** menu
2. Navigate to **Dashboards**
3. You should see **Barton Outreach — Overview Dashboard**
4. Click to open it

**Expected panels:**
- 🏢 Total Companies
- 👥 Total Contacts
- ✅ Filled Slots
- ⚠️ Unresolved Errors
- 📊 Filled Slots by Role
- 🏆 Top 20 Companies by Contact Count
- 🚨 Resolution Queue Breakdown
- 📈 Company Growth (Last 30 Days)
- 👤 Contact Growth (Last 30 Days)

---

## 📥 Importing SVG-PLE Dashboard

### Step 1: Navigate to Import

1. Click the **☰** menu
2. Navigate to **Dashboards** → **Import**

### Step 2: Upload Dashboard JSON

1. Click **Upload JSON file**
2. Select: `infra/grafana/svg-ple-dashboard.json`
3. Or paste the file path in the import box

### Step 3: Configure Import

1. **Name:** SVG-PLE — BIT + Enrichment Dashboard
2. **Folder:** (leave blank or select folder)
3. **UID:** svg-ple-bit-enrichment
4. **Datasource:** Select **Neon PostgreSQL**

### Step 4: Click Import

The dashboard will be created with 6 panels:
- 🎯 BIT Heatmap — Company Intent Scores
- 💰 Enrichment ROI — Cost Per Success by Agent
- 📅 Renewal Pipeline — Next 120 Days
- 📊 Score Distribution
- 🔥 Hot Companies
- 📡 Signal Types

**⚠️ NOTE:** The SVG-PLE dashboard requires the BIT migration to be run first:
```bash
psql $DATABASE_URL -f infra/migrations/2025-11-06-bit-enrichment.sql
```

---

## 🔧 Configuration Details

### Neon Connection Settings

**From your .env file:**
- **Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
- **Database:** Marketing DB
- **User:** Marketing DB_owner
- **Port:** 5432
- **SSL Mode:** require (required for Neon)
- **PostgreSQL Version:** 15.0

**Connection String Format:**
```
postgresql://Marketing%20DB_owner:endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### Grafana Admin Settings

**From your .env file:**
- **Username:** admin
- **Password:** changeme

**⚠️ Security Reminder:**
1. Change the default admin password after first login
2. Create additional users with limited permissions for team members
3. Never commit `.env` or `neon.yml` to git (already in .gitignore)

---

## 🐛 Troubleshooting

### Issue: Port 3000 already in use

**Check what's using port 3000:**
```bash
# Windows
netstat -ano | findstr :3000

# macOS/Linux
lsof -i :3000
```

**Solution 1: Stop conflicting process**
```bash
# Find and stop the process using port 3000
```

**Solution 2: Change Grafana port**

Edit `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Changed from 3000:3000
```

Then access Grafana at: http://localhost:3001

### Issue: Docker not running

**Start Docker Desktop:**
- Windows: Open Docker Desktop from Start menu
- macOS: Open Docker Desktop from Applications
- Linux: `sudo systemctl start docker`

**Verify Docker is running:**
```bash
docker ps
```

### Issue: Grafana container fails to start

**View logs:**
```bash
docker-compose logs grafana
```

**Common issues:**
- Port conflict (see above)
- Invalid configuration file
- Permissions issue with volumes

**Reset Grafana (clean slate):**
```bash
docker-compose down -v
docker volume rm barton-outreach-core_grafana-storage
docker-compose up -d
```

⚠️ **WARNING:** This deletes all Grafana data!

### Issue: Database Connection Failed

**Check Neon credentials:**
```bash
cat .env | grep NEON
```

**Verify credentials match your Neon console:**
1. Login to [Neon Console](https://console.neon.tech)
2. Select your project: "Marketing DB"
3. Go to "Connection Details"
4. Verify host, database, user, and password match

**Test connection from command line:**
```bash
psql "postgresql://Marketing%20DB_owner:endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require"
```

**Check if Neon is accessible:**
```bash
curl -v https://ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432
```

### Issue: Dashboard shows "No Data"

**Verify database has data:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM marketing.company_master;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM marketing.people_master;"
```

**Check if tables exist:**
```bash
psql $DATABASE_URL -c "\dt marketing.*"
```

**If tables are empty, you need to populate data first.**

### Issue: Panels show query errors

**Check Grafana logs:**
```bash
docker-compose logs grafana | grep -i error
```

**Common causes:**
- Table doesn't exist (run migrations)
- Column name mismatch (check schema)
- Invalid SQL query (check panel query)

**Test query manually:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) as \"Companies\" FROM marketing.company_master"
```

---

## 📊 Next Steps After Grafana Starts

### Immediate (Required)

1. ✅ **Login to Grafana** (http://localhost:3000)
2. ✅ **Change admin password** (Settings → Profile → Change Password)
3. ✅ **Verify Neon datasource** (Connections → Data sources → Neon PostgreSQL → Save & test)
4. ✅ **Check Overview Dashboard** (Dashboards → Barton Outreach — Overview Dashboard)

### Optional (Recommended)

1. **Import SVG-PLE Dashboard**
   - Dashboards → Import
   - Upload `infra/grafana/svg-ple-dashboard.json`
   - Requires BIT migration first

2. **Run BIT Migration** (if not done)
   ```bash
   psql $DATABASE_URL -f infra/migrations/2025-11-06-bit-enrichment.sql
   ```

3. **Run Verification Queries**
   ```bash
   psql $DATABASE_URL -f infra/VERIFICATION_QUERIES.sql
   ```

4. **Customize Dashboards**
   - Edit panels to match your needs
   - Add custom queries
   - Create new dashboards

5. **Set Up Alerts** (optional)
   - Alert on unresolved errors > threshold
   - Alert on low data quality scores
   - Alert on failed enrichment jobs

---

## 🎯 Quick Reference Commands

```bash
# Start Grafana
docker-compose up -d

# View logs
docker-compose logs -f grafana

# Restart Grafana
docker-compose restart grafana

# Stop Grafana
docker-compose down

# Check if Grafana is running
docker-compose ps

# Access Grafana
# http://localhost:3000
# Username: admin
# Password: changeme
```

---

## 📚 Related Documentation

- **Grafana Setup Guide:** `grafana/README.md`
- **SVG-PLE Implementation:** `infra/SVG-PLE-IMPLEMENTATION-SUMMARY.md`
- **Verification Queries:** `infra/VERIFICATION_QUERIES.sql`
- **Database Schema:** `CURRENT_NEON_SCHEMA.md`
- **Quick Reference:** `SCHEMA_QUICK_REFERENCE.md`

---

## ✅ Configuration Summary

| Component | Status | Location |
|-----------|--------|----------|
| Environment Variables | ✅ Configured | `.env` |
| Neon Datasource | ✅ Configured | `grafana/provisioning/datasources/neon.yml` |
| Docker Compose | ✅ Ready | `docker-compose.yml` |
| Overview Dashboard | ✅ Auto-provisioned | Auto-loads on startup |
| SVG-PLE Dashboard | 📥 Ready to Import | `infra/grafana/svg-ple-dashboard.json` |

---

**Ready to start!** Run: `docker-compose up -d`

**Access:** http://localhost:3000

**Login:** admin / changeme

---

**Last Updated:** 2025-11-06
**Grafana Version:** Latest (10.x+)
**PostgreSQL Version:** 15.x (Neon)
**Status:** ✅ Ready to Launch
