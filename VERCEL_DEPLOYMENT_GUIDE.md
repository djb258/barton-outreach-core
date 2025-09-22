# Vercel Deployment Guide - Outreach Process Manager

## Project Overview
Complete IMO (Input-Middle-Output) console for outreach process management with 5 integrated steps and audit logging.

## 🚀 Quick Deploy to Vercel

### Option 1: Web Interface (Recommended)
1. Go to [vercel.com/new](https://vercel.com/new)
2. Connect GitHub account and select repository: `djb258/barton-outreach-core`
3. Select branch: `ui`
4. Project name: `outreach-process-manager`

### Build Settings
```
Framework: Vite
Root Directory: /
Build Command: cd apps/outreach-ui && npm install && npm run build
Output Directory: apps/outreach-ui/dist
Install Command: cd apps/outreach-ui && npm install
```

### Environment Variables
Add these in Vercel Dashboard > Project Settings > Environment Variables:

```env
MCP_API_URL=https://composio-mcp-server.vercel.app
NEON_DB_URL=postgresql://neon_user:password@localhost:5432/outreach_db
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
COMPOSIO_BASE_URL=https://backend.composio.dev
DOCTRINE_HASH=STAMPED_v2.1.0
NODE_ENV=production
VITE_API_URL=https://outreach-process-manager.vercel.app
```

### Option 2: CLI Deployment
```bash
# 1. Login to Vercel
npx vercel login

# 2. Deploy from root directory
npx vercel --prod

# 3. Follow prompts:
#    - Link to existing project or create new
#    - Set project name: outreach-process-manager
#    - Confirm settings
```

## 📱 Application Structure

### Frontend Routes (React/Vite)
- `/` - Data Intake Dashboard (Step 1)
- `/data-intake-dashboard` - CSV upload and processing
- `/data-validation-console` - Data validation (Step 2)
- `/validation-adjuster-console` - Manual validation adjustments (Step 3)
- `/promotion-console` - Data promotion to production (Step 4)
- `/audit-log-console` - Audit trail viewer (Step 5)

### API Endpoints (Vercel Functions)
- `POST /api/ingest` - CSV data ingestion via MCP
- `POST /api/validate` - Data validation pipeline
- `POST /api/promote` - Promotion to production tables
- `POST /api/audit-log` - Audit log querying with filters
- `GET /api/logs/[logId]` - Download specific audit logs

## 🔧 Technical Configuration

### Vercel.json Configuration
```json
{
  "version": 2,
  "name": "outreach-process-manager",
  "builds": [
    {
      "src": "apps/outreach-ui/package.json",
      "use": "@vercel/static-build",
      "config": {
        "buildCommand": "npm run build",
        "distDir": "dist",
        "framework": "vite"
      }
    },
    {
      "src": "apps/outreach-process-manager/api/**/*.js",
      "use": "@vercel/node"
    }
  ]
}
```

### Build Process
1. **Frontend**: Vite builds React app to `apps/outreach-ui/dist/`
2. **Backend**: Node.js functions in `apps/outreach-process-manager/api/`
3. **Routing**: API calls routed to serverless functions
4. **Static**: UI assets served from build directory

## 🔐 Security & Integration

### MCP Integration
- All database operations through Composio MCP
- No direct Neon connections from Vercel functions
- API key authentication for Composio services

### Database Schema
Target tables in Neon (via MCP):
- `marketing.company_raw_intake` - Raw data ingestion
- `marketing.company` - Validated production data
- `marketing.company_promotion_log` - Audit trail
- `marketing.company_slots` - Promotion tracking

### STAMPED Doctrine Compliance
- Altitude: 10000 (production level)
- Doctrine: STAMPED v2.1.0
- All responses include doctrine metadata
- Individual row audit tracking

## 📊 Expected Features After Deployment

### Step 1: Data Intake Dashboard
- CSV file upload interface
- Data preview and validation
- Batch processing status
- Integration with `/api/ingest`

### Step 2: Data Validation Console
- STAMPED schema validation
- Email verification (MillionVerify MCP)
- Duplicate detection
- Integration with `/api/validate`

### Step 3: Validation Adjuster Console
- Manual validation overrides
- Error correction interface
- Batch adjustment tools

### Step 4: Promotion Console
- Staging to production promotion
- Slot creation for companies
- Bulk promotion management
- Integration with `/api/promote`

### Step 5: Audit Log Console
- Date range filtering
- Status filtering (PROMOTED/FAILED)
- Batch ID filtering
- Download audit logs as JSON
- Integration with `/api/audit-log`

## 🎯 Post-Deployment Verification

### 1. Frontend Verification
- [ ] All routes load correctly
- [ ] Components render properly
- [ ] Navigation works between steps
- [ ] API calls succeed

### 2. Backend Verification
- [ ] `/api/ingest` processes CSV data
- [ ] `/api/validate` runs validation pipeline
- [ ] `/api/promote` creates promotions and slots
- [ ] `/api/audit-log` returns filtered results
- [ ] Environment variables are set correctly

### 3. MCP Integration Verification
- [ ] Composio API key works
- [ ] Neon database connections succeed
- [ ] Audit logging writes to correct tables
- [ ] STAMPED doctrine metadata included

## 🔗 Expected Live URL
**Primary**: `https://outreach-process-manager.vercel.app`
**Alternative**: `https://outreach-process-manager-[hash].vercel.app`

## 🎉 Success Criteria
✅ Complete IMO process workflow (Steps 1-5)
✅ MCP-only database operations
✅ Audit logging with individual row tracking
✅ STAMPED doctrine compliance
✅ Vercel serverless deployment
✅ GitHub integration for continuous deployment