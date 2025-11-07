# 🚀 Import Your 3 Existing Dashboards to Grafana Cloud

## 📊 The 3 Dashboards to Import:

1. **Barton Outreach Overview** → `grafana/provisioning/dashboards/barton-outreach-dashboard.json`
2. **Executive Enrichment Monitoring** → `grafana/provisioning/dashboards/executive-enrichment-monitoring.json`
3. **SVG-PLE Dashboard** → `infra/grafana/svg-ple-dashboard.json`

---

## ✅ SIMPLE IMPORT (Repeat 3 Times)

### Dashboard 1: Barton Outreach Overview

1. **Go to:** https://dbarton.grafana.net
2. **Click:** ☰ menu (top left) → **Dashboards**
3. **Click:** Blue **"New"** button (top right) → **"Import"**
4. **Click:** **"Upload JSON file"** button
5. **Select file:** `grafana/provisioning/dashboards/barton-outreach-dashboard.json`
   - Navigate to: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\grafana\provisioning\dashboards\`
   - Click: `barton-outreach-dashboard.json`
   - Click: **Open**
6. **You'll see:** Import dashboard screen
7. **Under "Select a PostgreSQL data source":**
   - Choose your Neon PostgreSQL data source from dropdown
   - (Should be named something like "Neon PostgreSQL" or "Marketing DB")
8. **Click:** **"Import"** button (bottom)
9. **Success!** Dashboard should load

---

### Dashboard 2: Executive Enrichment Monitoring

**Repeat steps 1-9 above**, but in step 5, select:
`grafana/provisioning/dashboards/executive-enrichment-monitoring.json`

---

### Dashboard 3: SVG-PLE Dashboard

**Repeat steps 1-9 above**, but in step 5, select:
`infra/grafana/svg-ple-dashboard.json`

---

## ⏱️ TIME: 5 Minutes Total

- Dashboard 1: ~2 minutes
- Dashboard 2: ~2 minutes
- Dashboard 3: ~2 minutes

---

## 🆘 IF YOU SEE ERRORS

### Error: "Data source not found"
**Fix:**
1. After import, click on any panel showing error
2. Click the **Edit** button (pencil icon)
3. In the panel editor, look for **"Data source"** dropdown
4. Select your Neon PostgreSQL data source
5. Click **"Apply"**
6. Click **"Save dashboard"** (top right)

### Error: "Table does not exist"
**This means:** The SQL query references a table that doesn't exist in your database.

**Check:** Do you have these tables in your Neon database?
- `marketing.company_master`
- `marketing.company_slots`
- `marketing.people_master`
- `marketing.data_enrichment_log`
- `marketing.pipeline_errors`
- `marketing.duplicate_queue`
- `intake.company_raw_intake`

If tables are missing, the dashboard panels won't work.

### Panels show "No data"
**This is normal if:** Your tables are empty or have no recent data.

**To verify:**
1. Click panel → Edit
2. Look at the SQL query
3. Run the query manually in Neon console to see if it returns data

---

## ✅ AFTER IMPORT

Once all 3 dashboards are imported, send me:

1. **Dashboard URLs:**
   - Barton Outreach: https://dbarton.grafana.net/d/________
   - Enrichment Monitoring: https://dbarton.grafana.net/d/________
   - SVG-PLE: https://dbarton.grafana.net/d/________

2. **Did they import successfully?**
   - ☐ Yes, all 3 dashboards loaded
   - ☐ No, got errors (tell me which errors)

3. **Do the panels show data?**
   - ☐ Yes, seeing real data
   - ☐ No, showing "No data" (expected if tables are empty)

Then I'll help you:
- Configure embedding for your web app
- Set up public sharing URLs
- Provide the JSON configuration you requested

---

## 🎯 NEXT STEPS AFTER IMPORT

1. ✅ Test dashboards (verify data appears)
2. ✅ Enable anonymous access for embedding
3. ✅ Get embed URLs for web app
4. ✅ Provide you with complete JSON configuration

---

## 📝 QUICK CHECKLIST

- [ ] Import Dashboard 1: Barton Outreach Overview
- [ ] Import Dashboard 2: Executive Enrichment Monitoring
- [ ] Import Dashboard 3: SVG-PLE Dashboard
- [ ] Verify all dashboards show data (or "No data" if tables empty)
- [ ] Send me dashboard URLs
- [ ] I'll configure embedding and give you the JSON config

---

Ready to start? Go to https://dbarton.grafana.net and follow the steps! 🚀
