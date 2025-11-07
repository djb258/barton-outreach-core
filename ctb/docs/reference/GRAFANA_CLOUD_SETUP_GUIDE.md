# 🚀 Grafana Cloud Setup Guide (No Docker Required!)

## ✅ Why Grafana Cloud?

- **Free tier:** 10,000 series metrics, 50 GB logs, 3 users
- **No installation:** Works in browser, won't conflict with npx/node
- **Hosted:** No Docker, no local setup
- **Perfect for:** Your 4 dashboards + Neon PostgreSQL

---

## 📝 STEP-BY-STEP SETUP (15 Minutes)

### STEP 1: Create Grafana Cloud Account

1. **Go to:** https://grafana.com/auth/sign-up/create-user
2. **Fill in:**
   - Email: (your email)
   - Username: (choose a username)
   - Password: (create password)
   - Organization name: `Barton Outreach` (or your company name)
3. **Click:** "Create account"
4. **Verify email:** Check your inbox, click verification link
5. **Click:** "Continue to Grafana Cloud"

---

### STEP 2: Set Up Your Stack

After email verification, you'll be asked to create a stack:

1. **Stack Name:** `barton-outreach` (or your preferred name)
   - This becomes your URL: `barton-outreach.grafana.net`
2. **Region:** Choose closest to you:
   - US: `us-east-1` or `us-west-2`
   - Europe: `eu-central-1`
3. **Plan:** Select **"Free"** (forever free tier)
4. **Click:** "Create stack"

Wait 1-2 minutes while Grafana creates your instance.

---

### STEP 3: Access Your Grafana Instance

Once stack is ready:

1. **You'll see:** "Your stack is ready!"
2. **Click:** "Go to your Grafana instance"
   - OR manually go to: `https://your-stack-name.grafana.net`
3. **Log in** with your email/password

You should now see the Grafana home page!

---

### STEP 4: Add Neon PostgreSQL Data Source

Now we connect your Neon database:

1. **Click:** ☰ menu (left sidebar) → **"Connections"** → **"Data sources"**
2. **Click:** "Add new data source" (blue button)
3. **Search:** Type "PostgreSQL"
4. **Click:** "PostgreSQL" from results
5. **Fill in connection details:**

```
Name: Neon PostgreSQL
Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432
Database: Marketing DB
User: Marketing DB_owner
Password: endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT
TLS/SSL Mode: require
Version: 15+ (select from dropdown)
Max open connections: 10
Max idle connections: 10
Connection max lifetime: 14400
```

6. **Scroll down** to "PostgreSQL details"
   - **Enable:** "TLS/SSL Mode" → Select **"require"**
7. **Click:** "Save & test" (bottom of page)
8. **You should see:** ✅ "Database Connection OK"

If you see an error, double-check:
- Host includes `:5432` at the end
- Password includes the `endpoint=...` prefix
- TLS/SSL Mode is set to "require"

---

### STEP 5: Enable Anonymous Access (For Embedding)

This allows you to embed dashboards in your web app without login:

1. **Click:** ☰ menu → **"Administration"** → **"Settings"**
2. **Look for:** "Auth" section in left sidebar
3. **Click:** "Anonymous auth"
4. **Toggle ON:** "Enable anonymous access"
5. **Set:** "Organization role" → **"Viewer"** (read-only)
6. **Click:** "Save"

This makes your dashboards publicly viewable (perfect for embedding).

---

### STEP 6: Collect Information for Me

Once you've completed Steps 1-5, **send me this information:**

```
✅ SEND ME THESE DETAILS:

1. Your Grafana Cloud URL:
   Example: https://barton-outreach.grafana.net
   Yours: https://_____________________.grafana.net

2. Is anonymous access enabled?
   ☐ Yes, I enabled it in Step 5
   ☐ No, I skipped it (I'll do it later)

3. Did the Neon PostgreSQL connection test succeed?
   ☐ Yes - "Database Connection OK" appeared
   ☐ No - I got an error (paste error message)

4. Your Neon database has these schemas/tables, right?
   ☐ intake.company_raw_intake
   ☐ marketing.company_master
   ☐ marketing.company_slots
   ☐ marketing.people_master
   ☐ marketing.pipeline_errors
   ☐ marketing.duplicate_queue
```

---

## 🎯 WHAT HAPPENS NEXT

Once you send me that info, I will:

1. ✅ Create 4 dashboards with SQL queries:
   - Data Pipeline Flow
   - Error & Quality Monitoring
   - Barton ID Generation
   - Data Integrity

2. ✅ Provide you with the exact JSON configuration:
   - Dashboard URLs (public + embed)
   - API keys for programmatic access
   - SQL queries used in each panel

3. ✅ Give you embed code for your web application:
   - HTML iframe snippets
   - CORS configuration
   - Security settings

---

## 🆘 TROUBLESHOOTING

### "Database Connection OK" not appearing?

**Check these:**
- Host format: `host-name.neon.tech:5432` (includes port)
- Password includes: `endpoint=ep-xxxxx;npg_xxxxx`
- TLS/SSL Mode: "require" is selected
- Database name: `Marketing DB` (with space, exact match)

### Can't find "Anonymous auth" settings?

1. Click ☰ menu → "Administration"
2. Look for "Settings" or "Configuration"
3. Look for "auth.anonymous" section
4. If you don't see it, you may need admin role - check your user role

### Forgot my Grafana Cloud URL?

1. Go to: https://grafana.com/login
2. Log in with your email
3. Click on your stack name
4. URL is shown at top: `https://your-stack.grafana.net`

---

## ⏱️ TIME ESTIMATE

- **Step 1-2:** 5 minutes (account + stack creation)
- **Step 3:** 1 minute (access instance)
- **Step 4:** 5 minutes (add data source)
- **Step 5:** 2 minutes (enable anonymous access)
- **Step 6:** 2 minutes (collect info for me)

**Total:** ~15 minutes

---

## 📊 WHAT YOU'LL GET

After you send me the info from Step 6, I'll create:

**Dashboard 1: Data Pipeline Flow**
- Table row counts (gauges)
- Daily intake volume (time series)
- Data flow between tables

**Dashboard 2: Error & Quality Monitoring**
- Errors by stage (bar chart)
- Error trends (line chart)
- Duplicate queue size
- Top 10 errors (table)

**Dashboard 3: Barton ID Generation**
- Latest IDs (stat panels)
- ID generation rate
- Sequence tracking

**Dashboard 4: Data Integrity**
- Orphaned records detection
- Data completeness %
- Relationship health

All with:
- ✅ Public/embed URLs
- ✅ Complete SQL queries
- ✅ Embed code for your web app
- ✅ API keys for programmatic access

---

## ✅ READY?

1. Follow Steps 1-5 above
2. Send me the info from Step 6
3. I'll create all 4 dashboards for you!

No Docker. No local installation. No conflicts with npx/node. 🎉
