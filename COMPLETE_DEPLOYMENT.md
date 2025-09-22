# 🚀 COMPLETE VERCEL DEPLOYMENT WITH ALL VARIABLES

## ❌ Current Issue: 404 Error
The URL returns 404 because the project hasn't been deployed yet. Here's how to deploy it properly with all the required environment variables.

## 🎯 Step 1: Deploy to Vercel

### **👉 Click to Deploy:**
**https://vercel.com/new/git/external?repository-url=https://github.com/djb258/barton-outreach-core&branch=ui&project-name=outreach-process-manager**

### **Build Settings (Auto-detected):**
```
Framework: Vite
Build Command: cd apps/outreach-ui && npm install && npm run build
Output Directory: apps/outreach-ui/dist
Install Command: cd apps/outreach-ui && npm install
Root Directory: /
```

## 🔐 Step 2: Set Environment Variables

Go to **Vercel Dashboard → Project Settings → Environment Variables** and add these:

### **🔑 Core MCP & Database (REQUIRED)**
```env
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
COMPOSIO_BASE_URL=https://backend.composio.dev
NEON_DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require
DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require
NEON_API_KEY=napi_63qzjus8mdpkmdskniycx1hn8momw2lk3te19g27j3f0rxh7i446ewc8xwgar9y7
```

### **🤖 AI/LLM Configuration**
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
LLM_DEFAULT_PROVIDER=anthropic
```

### **📧 External Service APIs**
```env
APIFY_TOKEN=your-apify-token-here
MILLIONVERIFIER_API_KEY=your-millionverifier-key-here
APOLLO_API_KEY=your-apollo-key-here
INSTANTLY_API_KEY=your-instantly-key-here
HEYREACH_API_KEY=your-heyreach-key-here
```

### **🏗️ HEIR Doctrine Configuration**
```env
DOCTRINE_DB=shq
DOCTRINE_SUBHIVE=03
DOCTRINE_APP=outreach
DOCTRINE_VER=2
DOCTRINE_HASH=STAMPED_v2.1.0
```

### **🔧 Application Configuration**
```env
NODE_ENV=production
PORT=8080
FRONTEND_URL=https://outreach-process-manager.vercel.app
VITE_API_URL=https://outreach-process-manager.vercel.app
```

### **🎨 UI Builder Integration (Optional)**
```env
VITE_BUILDER_IO_KEY=your-builder-io-key
VITE_PLASMIC_PROJECT_ID=your-plasmic-project-id
VITE_PLASMIC_PROJECT_TOKEN=your-plasmic-token
FIGMA_ACCESS_TOKEN=your-figma-token
LOVEABLE_API_KEY=your-loveable-key
```

### **📊 Process Configuration**
```env
BLUEPRINT_ID=OPM-001
BLUEPRINT_VERSION_HASH=production
BATCH_SIZE=50
VALIDATION_THRESHOLD=0.8
EMAIL_RATE_LIMIT=100
DAILY_SEND_LIMIT=1000
```

## 🎯 Step 3: Deployment Verification

### **Expected Live URLs:**
- **Primary**: `https://outreach-process-manager.vercel.app`
- **Alternative**: `https://outreach-process-manager-[hash].vercel.app`

### **✅ Application Routes (All 6 Steps):**
1. `/` - Data Intake Dashboard
2. `/data-validation-console` - STAMPED Validation
3. `/validation-adjuster-console` - Manual Adjustments
4. `/promotion-console` - Staging to Production
5. `/audit-log-console` - Audit Trail Viewer
6. `/scraping-console` - **NEW!** Data Scraping Logs

### **🚀 API Endpoints:**
- `POST /api/ingest` - CSV data ingestion via MCP
- `POST /api/validate` - STAMPED validation pipeline
- `POST /api/promote` - Data promotion with audit logging
- `POST /api/audit-log` - Audit log viewer with filtering
- `POST /api/scrape-log` - **NEW!** Scraping data logs
- `GET /api/logs/[logId]` - Download audit logs

## 🔍 Step 4: Test Deployment

### **Homepage Test:**
```bash
curl https://outreach-process-manager.vercel.app
# Should return HTML with React app
```

### **API Test:**
```bash
curl -X POST https://outreach-process-manager.vercel.app/api/audit-log \
  -H "Content-Type: application/json" \
  -d '{"filters": {"status": "ALL"}}'
# Should return JSON with audit logs
```

### **UI Test:**
1. Visit homepage - should show Data Intake Dashboard
2. Navigate to `/audit-log-console` - should show audit logs
3. Try `/scraping-console` - should show scraping data
4. Check browser console for any errors

## ⚡ Deployment Timeline

- **Build Time**: ~3-4 minutes (Vite + Node.js functions)
- **Environment Variables**: ~2 minutes to set
- **Total**: Under 10 minutes for complete deployment

## 🚨 Troubleshooting

### **If 404 Persists:**
1. Check build logs in Vercel dashboard
2. Verify `apps/outreach-ui/dist/index.html` exists after build
3. Confirm Output Directory is set correctly

### **If APIs Don't Work:**
1. Check Functions tab in Vercel dashboard
2. Verify environment variables are set
3. Check function logs for MCP connection errors

### **If MCP Calls Fail:**
1. Verify `COMPOSIO_API_KEY` is valid
2. Check `NEON_DATABASE_URL` connection
3. Confirm all external API keys are active

## 🎉 Success Indicators

✅ **Homepage loads** with Data Intake Dashboard
✅ **All 6 console routes** navigate correctly
✅ **API endpoints respond** with JSON data
✅ **MCP integration works** (database queries succeed)
✅ **No 404 errors** on main routes
✅ **Environment variables** properly configured

---

**🚀 Ready to deploy? Use the deployment link above and follow the steps!**

After deployment, the Outreach Process Manager will be fully functional with complete IMO workflow, MCP integration, and audit logging capabilities.