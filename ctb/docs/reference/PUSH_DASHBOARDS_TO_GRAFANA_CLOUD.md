# 🚀 Push Existing Dashboards to Grafana Cloud

## 📊 What We Already Have

You have **3 complete dashboards** ready to import:

### 1. **Barton Outreach Overview Dashboard**
**File:** `grafana/provisioning/dashboards/barton-outreach-dashboard.json`
**Contains:**
- 🏢 Total Companies (stat)
- 👥 Total Contacts (stat)
- ✅ Filled Slots (stat)
- ⚠️ Unresolved Errors (stat)
- 📊 Filled Slots by Role (CFO/CEO/HR) - pie chart
- 🏆 Top 20 Companies by Contact Count - table
- 🚨 Resolution Queue Breakdown - bar chart
- 📈 Company Growth (Last 30 Days) - time series
- 👤 Contact Growth (Last 30 Days) - time series

**Matches:** Data Pipeline Flow + Data Integrity (partial)

---

### 2. **Executive Enrichment Monitoring**
**File:** `grafana/provisioning/dashboards/executive-enrichment-monitoring.json`
**Contains:**
- Pending Jobs, Running Jobs, Failed Jobs (stats)
- Success Rate %, Avg Duration (stats)
- Executive Slots Pending Enrichment (table)
- Enrichment Jobs In Progress (table)
- Failed Enrichment Jobs (Last 24h) - table
- Agent Performance (Last 7 Days) - bar chart
- Enrichment Timeline (Last 24h) - time series

**Matches:** Error & Quality Monitoring (partial)

---

### 3. **SVG-PLE Dashboard (BIT + Enrichment)**
**File:** `infra/grafana/svg-ple-dashboard.json`
**Contains:**
- 🎯 BIT Heatmap — Company Intent Scores
- 💰 Enrichment ROI — Cost Per Success by Agent
- 📅 Renewal Pipeline — Next 120 Days
- 🎯 Score Distribution
- 🔥 Hot Companies
- 📊 Signal Types (Last 30 Days)

**Matches:** Advanced analytics

---

## ✅ STEP-BY-STEP: Import to Grafana Cloud

### BEFORE IMPORTING: Fix the Data Source UID

The dashboards reference a datasource with `uid: "neon"`, but your Grafana Cloud instance may have a different UID.

**Option A: Find Your Data Source UID**
1. Go to https://dbarton.grafana.net
2. Click ☰ → **Connections** → **Data sources**
3. Click on your **PostgreSQL** (Neon) data source
4. Look at the URL: `https://dbarton.grafana.net/connections/datasources/edit/XXXXXXXXX`
5. The `XXXXXXXXX` is your data source UID
6. **Write it down:** `_______________________`

**Option B: Use the Default PostgreSQL UID**
- Most likely: `postgres` or `P1234567890ABCDEF`
- We'll update the JSON files to match

---

### METHOD 1: Import via Grafana UI (EASIEST)

#### Dashboard 1: Barton Outreach Overview

1. Go to https://dbarton.grafana.net
2. Click ☰ → **Dashboards**
3. Click **"New"** → **"Import"**
4. Click **"Upload JSON file"**
5. Select: `grafana/provisioning/dashboards/barton-outreach-dashboard.json`
6. **IMPORTANT:** Before clicking "Import":
   - Under "Select a data source", choose your **PostgreSQL (Neon)** data source
   - Change "Folder" to "General" or create a new folder
   - Click **"Import"**
7. Dashboard should load! 🎉

If you see errors:
- Click on any panel with error
- Edit panel → Check "Query" tab
- Verify table names match your schema

#### Dashboard 2: Executive Enrichment Monitoring

Repeat steps 1-7 above, but select:
`grafana/provisioning/dashboards/executive-enrichment-monitoring.json`

#### Dashboard 3: SVG-PLE Dashboard

Repeat steps 1-7 above, but select:
`infra/grafana/svg-ple-dashboard.json`

---

### METHOD 2: Import via Grafana API (ADVANCED)

Use this if you want to automate or have multiple dashboards to import.

#### Step 1: Get Your API Key

You already have a token:
```
<YOUR_GRAFANA_API_TOKEN>
```

**Note:** This token is for the Neon integration, you may need a separate API key for importing dashboards.

To create a new API key:
1. Go to https://dbarton.grafana.net
2. Click ☰ → **Administration** → **Service accounts**
3. Click **"Add service account"**
4. Name: `Dashboard Import`
5. Role: **Editor**
6. Click **"Create"**
7. Click **"Add service account token"**
8. Name: `import-token`
9. Click **"Generate token"**
10. **COPY THE TOKEN** (you won't see it again!)

#### Step 2: Prepare JSON Files

First, update the datasource UID in each JSON file.

I can create a script to do this automatically - would you like me to?

#### Step 3: Import via curl

```bash
curl -X POST https://dbarton.grafana.net/api/dashboards/db \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d @grafana/provisioning/dashboards/barton-outreach-dashboard.json
```

Repeat for each dashboard.

---

### METHOD 3: Let Me Create an Import Script

I can create a PowerShell script that:
1. Updates all datasource UIDs automatically
2. Imports all 3 dashboards via API
3. Returns the dashboard URLs

Would you like me to create this? Just send me:
- Your Grafana API key (from Step 1 above)
- Your PostgreSQL data source UID (from "Find Your Data Source UID" section)

---

## 🆘 TROUBLESHOOTING

### "Data source not found" error
- Go to panel with error → Edit
- Change "Data source" dropdown to your Neon PostgreSQL
- Click "Apply"
- Repeat for all panels with error

### "Table does not exist" error
- Check that your Neon database has these tables:
  - `marketing.company_master`
  - `marketing.company_slots`
  - `marketing.people_master`
  - `marketing.pipeline_errors`
  - `marketing.duplicate_queue`
  - `intake.company_raw_intake`

### Panels show "No data"
- Click on panel → Edit
- Check "Query" tab - verify SQL is correct
- Click "Run query" manually
- Check if data exists in those tables

---

## 🎯 WHAT'S MISSING

To fully match your requirements, we need to **create 1 more dashboard:**

### Dashboard 4: **Barton ID Generation**
- Latest Company ID, Slot ID, Contact ID (stat panels)
- ID generation rate (per hour/day)
- ID sequence tracking over time

Would you like me to create this one? It's not in the existing files.

---

## ✅ NEXT STEPS

**Option 1: Manual Import (5 minutes)**
1. Use METHOD 1 above
2. Import all 3 dashboards via UI
3. Let me know if you see any errors
4. I'll create the 4th dashboard (Barton ID Generation)

**Option 2: Automated Import (I create script)**
1. Send me your Grafana API key
2. Send me your PostgreSQL data source UID
3. I'll create a script to import all dashboards
4. You run one command, all dashboards appear

**Option 3: Create New Dashboards from Scratch**
1. Skip importing existing ones
2. I create 4 brand new dashboards matching your exact specs
3. You import those instead

Which option do you prefer?

---

## 📋 SUMMARY

**What we have:**
- ✅ Dashboard 1: Data Pipeline Flow (mostly done - "Barton Outreach Overview")
- ✅ Dashboard 2: Error & Quality Monitoring (mostly done - "Executive Enrichment")
- ✅ Dashboard 3: Advanced Analytics (SVG-PLE Dashboard)
- ❌ Dashboard 4: Barton ID Generation (need to create)

**How to proceed:**
1. Import the 3 existing dashboards (METHOD 1 is easiest)
2. Let me create Dashboard 4
3. Customize any panels that don't match your exact needs
4. Enable embedding for web app integration

Let me know which method you want to use! 🚀
