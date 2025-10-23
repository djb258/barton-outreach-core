<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-6BFA5153
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# 🚀 IMMEDIATE DEPLOYMENT INSTRUCTIONS

## ❌ Current Status: Project Not Deployed
The URL `https://outreach-process-manager.vercel.app` returns 404 because the project hasn't been deployed to Vercel yet.

## ✅ Deploy Now (3 Simple Steps)

### **Step 1: Click Deploy Link**
👉 **[DEPLOY OUTREACH PROCESS MANAGER](https://vercel.com/new/git/external?repository-url=https://github.com/djb258/barton-outreach-core&branch=ui&project-name=outreach-process-manager)**

### **Step 2: Verify Build Settings**
Vercel should auto-detect these settings:
```
Framework: Vite
Build Command: cd apps/outreach-ui && npm install && npm run build
Output Directory: apps/outreach-ui/dist
Install Command: cd apps/outreach-ui && npm install
Root Directory: /
```

### **Step 3: Set Environment Variables**
In Vercel Dashboard → Project Settings → Environment Variables, add:

```env
MCP_API_URL=https://composio-mcp-server.vercel.app
NEON_DB_URL=postgresql://neon_user:password@localhost:5432/outreach_db
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
COMPOSIO_BASE_URL=https://backend.composio.dev
DOCTRINE_HASH=STAMPED_v2.1.0
NODE_ENV=production
VITE_API_URL=https://outreach-process-manager.vercel.app
```

## 🎯 Alternative Deployment URLs

If `outreach-process-manager` is taken, Vercel will suggest:
- `outreach-process-manager-1.vercel.app`
- `outreach-process-manager-{random}.vercel.app`

## 📱 What You'll See After Deployment

### **Live Application Routes:**
- `/` - Data Intake Dashboard (Step 1)
- `/data-validation-console` - Data Validation (Step 2)
- `/validation-adjuster-console` - Manual Adjustments (Step 3)
- `/promotion-console` - Data Promotion (Step 4)
- `/audit-log-console` - Audit Logs (Step 5)
- `/scraping-console` - **NEW!** Scraping Console (Step 6)

### **API Endpoints:**
- `POST /api/ingest` - CSV data ingestion
- `POST /api/validate` - STAMPED validation
- `POST /api/promote` - Data promotion
- `POST /api/audit-log` - Audit log viewer
- `POST /api/scrape-log` - **NEW!** Scraping data logs
- `GET /api/logs/[logId]` - Download audit logs

## ⚡ Expected Deployment Time
- **Build time**: ~2-3 minutes
- **Deploy time**: ~30 seconds
- **Total**: Under 5 minutes

## 🔍 Troubleshooting

### If Build Fails:
1. Check that `apps/outreach-ui/package.json` exists
2. Verify Build Command is correct
3. Ensure all dependencies are listed

### If 404 After Deploy:
1. Check Output Directory is `apps/outreach-ui/dist`
2. Verify `index.html` exists in dist folder
3. Check Vercel Functions tab for API endpoints

### If APIs Don't Work:
1. Verify environment variables are set
2. Check Vercel Functions logs
3. Confirm MCP endpoints are accessible

## 🎉 Success Indicators

✅ **Homepage loads** showing Data Intake Dashboard
✅ **Navigation works** between all 6 consoles
✅ **API calls succeed** (may show mock data initially)
✅ **No console errors** in browser dev tools

---

**🚀 Ready to deploy? Click the deploy link above!**