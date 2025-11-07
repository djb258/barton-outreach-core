# Grafana Setup for Barton Outreach Core

Complete setup guide for Grafana monitoring and visualization with Neon PostgreSQL integration.

---

## 📋 Quick Start

### 1. Configure Environment Variables

Copy the example environment file and fill in your Neon credentials:

```bash
# From repository root
cp .env.example .env
```

Edit `.env` and replace placeholder values with your actual Neon database credentials:

```env
GRAFANA_ADMIN_PASSWORD=your_secure_password_here
NEON_HOST=your-project-ep-xxx.us-east-2.aws.neon.tech
NEON_DATABASE=neondb
NEON_USER=your_neon_user
NEON_ENDPOINT_ID=ep-xxx-xxx-xxx
NEON_PASSWORD=your_neon_password
```

**Finding your Neon credentials:**
- Login to [Neon Console](https://console.neon.tech)
- Select your project
- Go to "Connection Details"
- Use the "Direct connection" parameters

### 2. Create Neon Datasource Configuration

```bash
# Copy the example datasource config
cp grafana/provisioning/datasources/neon.yml.example grafana/provisioning/datasources/neon.yml
```

The `neon.yml` file will automatically use environment variables from your `.env` file.

### 3. Start Grafana

```bash
docker-compose up -d
```

### 4. Access Grafana

Open your browser and navigate to:
```
http://localhost:3000
```

**Default credentials:**
- Username: `admin`
- Password: Value of `GRAFANA_ADMIN_PASSWORD` from your `.env` file (default: `changeme`)

**⚠️ IMPORTANT:** Change the default password on first login!

---

## 📊 Available Dashboards

### 1. Barton Outreach — Overview Dashboard
**Auto-provisioned on startup**

**Panels:**
- 🏢 **Total Companies** - Company count from `marketing.company_master`
- 👥 **Total Contacts** - Contact count from `marketing.people_master`
- ✅ **Filled Slots** - Count of filled company slots (CEO/CFO/HR)
- ⚠️ **Unresolved Errors** - Critical issues requiring attention
- 📊 **Filled Slots by Role** - Pie chart breakdown (CFO/CEO/HR)
- 🏆 **Top 20 Companies by Contact Count** - Table with industry and website
- 🚨 **Resolution Queue Breakdown** - Unresolved errors sorted by severity
- 📈 **Company Growth** - 30-day trend of new companies
- 👤 **Contact Growth** - 30-day trend of new contacts

**Refresh Rate:** 30 seconds
**Time Range:** Last 30 days

### 2. SVG-PLE — BIT + Enrichment Dashboard
**Located at:** `infra/grafana/svg-ple-dashboard.json`

**To Import:**
1. Navigate to Dashboards → Import
2. Upload `infra/grafana/svg-ple-dashboard.json`
3. Select datasource: "Neon PostgreSQL"
4. Click Import

**Panels:**
- 🎯 **BIT Heatmap** - Company intent scores with tier coloring
- 💰 **Enrichment ROI** - Cost per success by agent
- 📅 **Renewal Pipeline** - Companies in 120-day renewal window
- 📊 **Score Distribution** - Donut chart of score tiers
- 🔥 **Hot Companies** - Gauge of high-intent companies
- 📡 **Signal Types** - Bar chart of BIT signals by category

---

## 🔧 Configuration

### Docker Compose Settings

**File:** `docker-compose.yml`

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: barton-outreach-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-changeme}
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/provisioning/datasources:/etc/grafana/provisioning/datasources
      - ./grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped
```

### Neon Datasource Settings

**File:** `grafana/provisioning/datasources/neon.yml`

Key settings:
- **SSL Mode:** `require` (required for Neon)
- **PostgreSQL Version:** 15.0
- **Max Connections:** 10 open, 10 idle
- **Connection Lifetime:** 4 hours (14400s)

### Dashboard Provisioning

**File:** `grafana/provisioning/dashboards/dashboard.yml`

Settings:
- **Update Interval:** 10 seconds
- **Allow UI Updates:** Yes (dashboards can be edited in Grafana)
- **Disable Deletion:** No (dashboards can be deleted from UI)

---

## 🚀 Common Tasks

### Starting Grafana
```bash
docker-compose up -d
```

### Stopping Grafana
```bash
docker-compose down
```

### Restarting Grafana (after config changes)
```bash
docker-compose restart
```

### Viewing Logs
```bash
docker-compose logs -f grafana
```

### Updating Dashboard
1. Edit `grafana/provisioning/dashboards/barton-outreach-dashboard.json`
2. Restart Grafana:
   ```bash
   docker-compose restart
   ```
3. Dashboard will auto-update within 10 seconds

### Importing Additional Dashboards

**Method 1: Manual Import**
1. Navigate to Dashboards → Import
2. Upload JSON file or paste JSON content
3. Select datasource: "Neon PostgreSQL"
4. Click Import

**Method 2: Auto-Provisioning**
1. Place dashboard JSON in `grafana/provisioning/dashboards/`
2. Restart Grafana: `docker-compose restart`

### Changing Admin Password
```bash
# Edit .env file
GRAFANA_ADMIN_PASSWORD=new_secure_password

# Restart Grafana
docker-compose restart
```

### Resetting Grafana (clean slate)
```bash
# WARNING: This deletes all Grafana data including custom dashboards!
docker-compose down -v
docker volume rm barton-outreach-core_grafana-storage
docker-compose up -d
```

---

## 🔍 Troubleshooting

### Issue: Can't connect to Neon database

**Check datasource configuration:**
```bash
cat grafana/provisioning/datasources/neon.yml
```

**Verify environment variables:**
```bash
cat .env | grep NEON
```

**Common fixes:**
- Ensure `neon.yml` exists (not just `neon.yml.example`)
- Verify Neon credentials are correct in `.env`
- Check Neon endpoint format: `endpoint=${NEON_ENDPOINT_ID};${NEON_PASSWORD}`
- Ensure SSL mode is set to `require`

**Test connection manually:**
```bash
docker-compose exec grafana wget -O- http://localhost:3000/api/datasources
```

### Issue: Dashboard shows "No Data"

**Verify database has data:**
```bash
# Connect to your Neon database
psql $DATABASE_URL

# Check table counts
SELECT COUNT(*) FROM marketing.company_master;
SELECT COUNT(*) FROM marketing.people_master;
```

**Check Grafana logs:**
```bash
docker-compose logs -f grafana | grep -i error
```

### Issue: Dashboard not auto-loading

**Verify provisioning configuration:**
```bash
ls -la grafana/provisioning/dashboards/
```

**Check provisioning logs:**
```bash
docker-compose logs grafana | grep -i provisioning
```

**Force reload:**
```bash
docker-compose restart
```

### Issue: Permission denied errors

**Fix file permissions:**
```bash
# Linux/macOS
chmod -R 755 grafana/

# Windows (run as Administrator)
icacls grafana /grant Everyone:F /T
```

### Issue: Port 3000 already in use

**Option 1: Change Grafana port**

Edit `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Changed from 3000:3000
```

**Option 2: Find and stop conflicting process**
```bash
# Linux/macOS
lsof -i :3000
kill -9 <PID>

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

## 📚 Additional Resources

### Grafana Documentation
- [Official Grafana Docs](https://grafana.com/docs/grafana/latest/)
- [PostgreSQL Datasource](https://grafana.com/docs/grafana/latest/datasources/postgres/)
- [Dashboard Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/#dashboards)

### Neon Documentation
- [Neon Connection Guide](https://neon.tech/docs/connect/connect-from-any-app)
- [Connection Pooling](https://neon.tech/docs/connect/connection-pooling)

### Schema Documentation
- **Full Schema:** `CURRENT_NEON_SCHEMA.md` (4,000+ lines)
- **Quick Reference:** `SCHEMA_QUICK_REFERENCE.md`
- **Implementation Guide:** `infra/SVG-PLE-IMPLEMENTATION-SUMMARY.md`

---

## 🎯 Next Steps

After setup is complete:

1. **Verify Dashboard Loads**
   - Navigate to http://localhost:3000
   - Check "Barton Outreach — Overview Dashboard" appears

2. **Import SVG-PLE Dashboard**
   - Import `infra/grafana/svg-ple-dashboard.json`
   - Requires BIT migration: `infra/migrations/2025-11-06-bit-enrichment.sql`

3. **Run Database Migration** (if not done)
   ```bash
   psql $DATABASE_URL -f infra/migrations/2025-11-06-bit-enrichment.sql
   ```

4. **Verify Data Flow**
   - Check panels populate with real data
   - Verify 30-second refresh works
   - Test time range selector

5. **Customize Dashboards**
   - Edit panels to match your needs
   - Add custom queries
   - Create new dashboards

---

## 🔐 Security Notes

1. **Change default admin password** immediately after first login
2. **Never commit** `neon.yml` to git (it's in `.gitignore`)
3. **Never commit** `.env` file to git (it's in `.gitignore`)
4. **Use strong passwords** for Grafana admin account
5. **Rotate Neon credentials** periodically
6. **Limit Neon user permissions** to read-only if possible

---

## 📝 File Structure

```
barton-outreach-core/
├── docker-compose.yml                          # Grafana container config
├── .env.example                                # Environment template
├── .env                                        # Your credentials (gitignored)
├── grafana/
│   ├── README.md                               # This file
│   └── provisioning/
│       ├── datasources/
│       │   ├── neon.yml.example                # Template datasource
│       │   └── neon.yml                        # Your datasource (gitignored)
│       └── dashboards/
│           ├── dashboard.yml                   # Provisioning config
│           └── barton-outreach-dashboard.json  # Overview dashboard
└── infra/
    └── grafana/
        └── svg-ple-dashboard.json              # BIT + Enrichment dashboard
```

---

**Last Updated:** 2025-11-06
**Grafana Version:** Latest (10.x+)
**PostgreSQL Version:** 15.x (Neon)
**Schema Version:** Outreach Doctrine A→Z v1.3.2
