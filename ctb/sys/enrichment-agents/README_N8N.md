# Enrichment Agents with n8n Integration

**Complete automated enrichment system using n8n for orchestration**

## 🎯 System Overview

```
┌──────────────────────────────────────────────────────────┐
│                    n8n Cloud                              │
│         https://dbarton.app.n8n.cloud                    │
│                                                           │
│  • Scheduled workflows (every 6 hours, daily, weekly)   │
│  • Webhook triggers (on-demand enrichment)              │
│  • Monitoring & alerts (Slack, Email)                   │
│  • Cost tracking & reporting                            │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP API Calls
                     ↓
┌──────────────────────────────────────────────────────────┐
│              Enrichment API (FastAPI)                     │
│            http://localhost:8001                          │
│                                                           │
│  Endpoints:                                              │
│  • GET  /health          - Health check                 │
│  • GET  /invalid/count   - Count invalid records        │
│  • POST /enrich          - Trigger enrichment           │
│  • POST /enrich/company  - Enrich companies             │
│  • POST /enrich/people   - Enrich people                │
│  • GET  /stats           - Get statistics               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│           Enrichment Orchestrator (Python)                │
│                                                           │
│  • Pulls batches from company_invalid/people_invalid    │
│  • Analyzes validation_errors automatically             │
│  • Routes to correct agent (Apify/Abacus/Firecrawl)     │
│  • Merges enriched data back to records                 │
│  • Re-validates after enrichment                        │
│  • Promotes to master tables if valid                   │
│  • Throttles & times out (max 180s per record)          │
└────────────────────┬─────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌──────────┐
    │ Apify  │  │ Abacus │  │Firecrawl │
    │LinkedIn│  │Validate│  │ Website  │
    └────────┘  └────────┘  └──────────┘
         │           │           │
    ┌────────┐  ┌────────┐  ┌──────────┐
    │Scraper │  │ZenRows │  │Scraping  │
    │  API   │  │AI Parse│  │   Bee    │
    └────────┘  └────────┘  └──────────┘
         │           │           │
         └───────────┴───────────┘
                     ↓
         ┌───────────────────────┐
         │  Neon PostgreSQL      │
         │  marketing.           │
         │  • company_invalid    │
         │  • people_invalid     │
         │  • company_master     │
         │  • people_master      │
         └───────────────────────┘
```

## 🚀 Quick Start (4 Steps)

### Step 1: Install Dependencies

```bash
cd ctb/sys/enrichment-agents
pip install -r requirements.txt
```

**What gets installed**:
- `asyncpg` - Database driver
- `aiohttp` - HTTP client for agent APIs
- `fastapi` - API server
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variables

### Step 2: Add API Keys to .env

Edit `.env` in project root:

```bash
# Enrichment Agent API Keys
APIFY_API_KEY=your_actual_apify_key
ABACUS_API_KEY=your_actual_abacus_key
FIRECRAWL_API_KEY=your_actual_firecrawl_key
```

**Where to get keys**:
- Apify: https://console.apify.com/account/integrations
- Abacus: https://abacus.ai/app/profile/apikey
- Firecrawl: https://firecrawl.dev/app/api-keys

### Step 3: Start API Server

```bash
# Windows
start_api.bat

# Linux/Mac
./start_api.sh

# Or directly
python api/enrichment_api.py
```

**Test it works**:
```bash
# Health check
curl http://localhost:8001/health

# Check invalid count (should show 119 companies, 21 people)
curl http://localhost:8001/invalid/count

# View API docs (interactive)
open http://localhost:8001/docs
```

### Step 4: Import n8n Workflows

1. Go to https://dbarton.app.n8n.cloud
2. Click **Workflows** → **Add workflow** → **Import from File**
3. Import `n8n-workflows/scheduled-enrichment.json`
4. Import `n8n-workflows/webhook-enrichment.json`
5. In each workflow, update HTTP Request nodes:
   - Change URL from `localhost:8001` to your API URL
   - If API is on same server as n8n: use `localhost:8001`
   - If API is remote: use `http://your-server-ip:8001`
6. Activate workflows

**Done!** Your enrichment runs automatically every 6 hours.

---

## 📋 Available API Endpoints

### Status Endpoints

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/health` | GET | Check API health | `curl http://localhost:8001/health` |
| `/invalid/count` | GET | Count invalid records | `curl http://localhost:8001/invalid/count` |
| `/stats` | GET | Get enrichment stats | `curl http://localhost:8001/stats` |
| `/invalid/recent` | GET | Get recent failures | `curl http://localhost:8001/invalid/recent?limit=10` |

### Enrichment Endpoints

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/enrich` | POST | Enrich any table | `curl -X POST http://localhost:8001/enrich -d '{"table":"company_invalid","limit":10}'` |
| `/enrich/company` | POST | Enrich companies | `curl -X POST http://localhost:8001/enrich/company?limit=10` |
| `/enrich/people` | POST | Enrich people | `curl -X POST http://localhost:8001/enrich/people?limit=5` |

---

## 🔄 n8n Workflows Explained

### Workflow 1: Scheduled Enrichment

**File**: `n8n-workflows/scheduled-enrichment.json`

**What it does**:
1. **Runs every 6 hours** (customizable)
2. Checks if there are invalid records (`GET /invalid/count`)
3. If yes:
   - Enriches 10 companies
   - Enriches 10 people
   - Sends email notification with results
4. If no:
   - Skips and waits for next run

**Customize**:
- **Change schedule**: Edit "Schedule Trigger" node (hourly, daily, weekly)
- **Change batch size**: Add `?limit=20` to HTTP Request URLs
- **Add Slack**: Replace Email node with Slack node
- **Add conditions**: Only run if cost < $5, or if > 50 records

**Example output**:
```
✅ Enrichment Complete

Companies:
- Processed: 10
- Enriched: 7
- Promoted: 3
- Cost: $0.08

People:
- Processed: 5
- Enriched: 4
- Promoted: 2
- Cost: $0.02
```

### Workflow 2: Webhook Triggered Enrichment

**File**: `n8n-workflows/webhook-enrichment.json`

**What it does**:
1. Listens for POST requests on webhook URL
2. Extracts `table` and `limit` from request body
3. Triggers enrichment via API
4. Returns success/error response

**Usage**:
```bash
# Get webhook URL from n8n (look for "Production URL" in webhook node)
WEBHOOK_URL="https://dbarton.app.n8n.cloud/webhook/enrichment-trigger"

# Trigger enrichment for 10 companies
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"table": "company_invalid", "limit": 10}'

# Trigger enrichment for 5 people
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"table": "people_invalid", "limit": 5}'
```

**Use cases**:
- Trigger from Lovable UI ("Enrich Now" button)
- Trigger from another n8n workflow
- Trigger after CSV upload
- Trigger from external system

---

## ⚙️ How It Works (Step by Step)

### Example: Enriching Invalid Company

**Initial State**:
```sql
-- Company in company_invalid table
company_name: "Acme Corp"
website: NULL  ❌
employee_count: NULL  ❌
linkedin_url: NULL  ❌
validation_errors: [
  {"field": "website", "message": "Website is required"},
  {"field": "employee_count", "message": "Employee count is required"},
  {"field": "linkedin_url", "message": "LinkedIn URL is required"}
]
```

**n8n triggers enrichment** (via scheduled workflow or webhook):

1. **API receives request**: `POST /enrich/company?limit=10`

2. **Orchestrator pulls batch**:
   ```sql
   SELECT * FROM marketing.company_invalid
   WHERE reviewed = FALSE
   LIMIT 10
   ```

3. **Analyzes validation errors**: Needs `website`, `employee_count`, `linkedin_url`

4. **Routes to agents**:
   - `website` → Firecrawl (search company)
   - `employee_count` → Apify (LinkedIn company scraper)
   - `linkedin_url` → Apify (LinkedIn company scraper)

5. **Calls Apify** (LinkedIn scraper):
   ```
   Input: {company_name: "Acme Corp"}
   ⏱️ Timeout: 90 seconds
   Result: {
     linkedin_url: "https://linkedin.com/company/acme-corp",
     employee_count: 250,
     industry: "Technology"
   }
   💰 Cost: $0.01
   ```

6. **Updates record**:
   ```sql
   UPDATE marketing.company_invalid
   SET
     website = 'https://acme.com',
     employee_count = 250,
     linkedin_url = 'https://linkedin.com/company/acme-corp',
     last_enrichment_attempt = NOW()
   WHERE id = 123
   ```

7. **Re-validates** (using validation_rules.py):
   - ✅ company_name: "Acme Corp" (valid)
   - ✅ website: "https://acme.com" (valid)
   - ✅ employee_count: 250 (valid, > 50)
   - ✅ linkedin_url: contains "linkedin.com/company/"
   - **Result**: ALL VALID! ✅

8. **Promotes to master**:
   ```sql
   -- Insert into company_master
   INSERT INTO marketing.company_master (...)
   VALUES (...);

   -- Create slots (CEO, CFO, HR)
   INSERT INTO marketing.company_slot (slot_type, is_filled)
   VALUES ('CEO', FALSE), ('CFO', FALSE), ('HR', FALSE);

   -- Delete from company_invalid
   DELETE FROM marketing.company_invalid WHERE id = 123;
   ```

9. **Returns result to n8n**:
   ```json
   {
     "success": true,
     "message": "Enriched 7 records, promoted 3",
     "stats": {
       "processed": 10,
       "enriched": 7,
       "promoted": 3,
       "failed": 0,
       "cost": 0.08
     }
   }
   ```

10. **n8n sends notification** (email/Slack)

---

## 🛡️ Safety Features (Throttles & Timeouts)

### Per-Record Timeout: 180 seconds (3 minutes)
If enriching one record takes longer than 3 minutes, it's aborted and moved to next record.

### Per-Agent Timeout: 30-120 seconds
- Apify LinkedIn: 90s
- Abacus enrichment: 30s
- Firecrawl scrape: 60s

### Rate Limits (per agent)
- Apify: 30 calls/minute, 500/hour
- Abacus: 100 calls/minute, 2000/hour
- Firecrawl: 50 calls/minute, 1000/hour

### Max Agents per Field: 2
If website is missing, only tries 2 agents (e.g., Firecrawl + Abacus), then moves on.

### Cost Cap: $0.50 per record
If enriching one record exceeds $0.50, it's skipped (configurable).

### Cooldown: 1 hour
Won't re-attempt same record within 1 hour (prevents infinite loops).

---

## 💰 Cost Estimation

### Per Record (Average)
- Apify: $0.01
- Abacus: $0.002
- Firecrawl: $0.005
- **Total**: ~$0.017 per record

### Current Invalid Records
- 119 companies × $0.017 = **$2.02**
- 21 people × $0.017 = **$0.36**
- **Total**: **$2.38**

### Monthly (with continuous enrichment)
- 10 records per run × 4 runs per day = 40 records/day
- 40 × 30 days = 1,200 records/month
- 1,200 × $0.017 = **$20.40/month**

**Budget recommendation**: $30-$50/month (includes retries, new uploads)

---

## 📊 Monitoring & Alerts

### Check API Health
```bash
curl http://localhost:8001/health
```

### Check Invalid Count
```bash
curl http://localhost:8001/invalid/count
```

### View Stats
```bash
curl http://localhost:8001/stats
```

### n8n Execution History
1. Go to n8n → Workflows
2. Click workflow name
3. Click "Executions" tab
4. See all past runs with results

### Set Up Alerts in n8n

**Create monitoring workflow**:
1. Schedule: Every hour
2. Check `/health` endpoint
3. If unhealthy → Send Slack/Email alert
4. Check `/invalid/count`
5. If > 100 records → Send alert ("backlog growing")
6. Check `/stats`
7. If daily cost > $5 → Send budget alert

---

## 🚀 Production Deployment

### Option 1: Run on Same Server as n8n (Recommended if self-hosted)

```bash
# Install as systemd service
sudo nano /etc/systemd/system/enrichment-api.service
```

```ini
[Unit]
Description=Enrichment API
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/barton-outreach-core/ctb/sys/enrichment-agents
Environment="DATABASE_URL=postgresql://..."
Environment="APIFY_API_KEY=..."
Environment="ABACUS_API_KEY=..."
Environment="FIRECRAWL_API_KEY=..."
ExecStart=/usr/bin/python3 api/enrichment_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable enrichment-api
sudo systemctl start enrichment-api
```

### Option 2: Deploy to Cloud (if using n8n Cloud)

**Deploy to Render** (example):
1. Connect GitHub repo to Render
2. Create new Web Service
3. Build command: `cd ctb/sys/enrichment-agents && pip install -r requirements.txt`
4. Start command: `python api/enrichment_api.py`
5. Add environment variables (DATABASE_URL, API keys)
6. Deploy
7. Get public URL: `https://your-api.onrender.com`
8. Update n8n workflows with new URL

---

## 🎯 Complete Setup Checklist

- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Add API keys to `.env` (Apify, Abacus, Firecrawl)
- [ ] Test API locally (`python api/enrichment_api.py`)
- [ ] Verify health check (`curl http://localhost:8001/health`)
- [ ] Import n8n workflows (2 workflows)
- [ ] Update HTTP Request node URLs in workflows
- [ ] Test webhook workflow with curl
- [ ] Activate scheduled workflow
- [ ] Monitor first run
- [ ] Set up email/Slack notifications
- [ ] Deploy API to production (if needed)
- [ ] Update n8n with production API URL
- [ ] Set up monitoring workflow
- [ ] Document monthly costs

---

**Status**: ✅ Ready for n8n Integration
**API Port**: 8001 (default)
**n8n URL**: https://dbarton.app.n8n.cloud
**Invalid Records**: 119 companies, 21 people
**Estimated Cost**: $2.38 (one-time) + $20-$50/month (continuous)
