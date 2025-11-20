# n8n Setup Guide - Enrichment Agents

## 🎯 Overview

Instead of running Python scripts manually, we'll use **n8n** to:
- Schedule enrichment runs (every 6 hours, daily, weekly, etc.)
- Trigger enrichment via webhook (on-demand)
- Monitor invalid record counts
- Send notifications when enrichment completes
- Track costs and success rates

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      n8n Workflows                       │
│  (Scheduling, Webhooks, Notifications, Monitoring)      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP API Calls
                     ↓
┌─────────────────────────────────────────────────────────┐
│            Enrichment API (FastAPI)                      │
│           http://localhost:8001                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│           Enrichment Orchestrator                        │
│  (Batch Processing, Agent Routing, Validation)          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │ Apify  │  │ Abacus │  │Firecrawl│
    └────────┘  └────────┘  └────────┘
         │           │           │
         └───────────┴───────────┘
                     ↓
         ┌─────────────────────┐
         │  Neon PostgreSQL    │
         │ (company_invalid,   │
         │  people_invalid)    │
         └─────────────────────┘
```

## 🚀 Quick Setup

### Step 1: Install API Dependencies

```bash
cd ctb/sys/enrichment-agents
pip install fastapi uvicorn asyncpg aiohttp python-dotenv
```

### Step 2: Start the API Server

```bash
# Start in one terminal
python api/enrichment_api.py

# Or with custom port
ENRICHMENT_API_PORT=8001 python api/enrichment_api.py
```

**Expected output**:
```
🚀 Starting Enrichment API on port 8001
   Documentation: http://localhost:8001/docs
   Health check: http://localhost:8001/health

✅ Enrichment API started
   Agents: ['apify', 'abacus', 'firecrawl']
   Batch size: 10
```

**Test it**:
```bash
# Health check
curl http://localhost:8001/health

# Check invalid count
curl http://localhost:8001/invalid/count

# API docs (interactive)
open http://localhost:8001/docs
```

### Step 3: Import n8n Workflows

1. **Open n8n**: Go to https://dbarton.app.n8n.cloud
2. **Import workflows**:
   - Click "Workflows" → "Add workflow" → "Import from File"
   - Import `n8n-workflows/scheduled-enrichment.json`
   - Import `n8n-workflows/webhook-enrichment.json`

3. **Configure endpoints**:
   - In each HTTP Request node, change `localhost:8001` to your API URL
   - If running API on same server: `http://localhost:8001`
   - If running API remotely: `http://your-server-ip:8001`

---

## 📋 Available API Endpoints

### Health & Status

#### `GET /health`
Check API and database health
```bash
curl http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "agents": {
    "apify": {"enabled": true, "total_calls": 15, "rate_limit_status": "OK"},
    "abacus": {"enabled": true, "total_calls": 8, "rate_limit_status": "OK"},
    "firecrawl": {"enabled": true, "total_calls": 12, "rate_limit_status": "OK"}
  },
  "timestamp": "2025-11-19T10:30:00"
}
```

#### `GET /invalid/count`
Get count of invalid records (use in n8n conditionals)
```bash
curl http://localhost:8001/invalid/count
```

**Response**:
```json
{
  "company_invalid": 119,
  "people_invalid": 21,
  "total": 140,
  "timestamp": "2025-11-19T10:30:00"
}
```

#### `GET /stats`
Get enrichment statistics
```bash
curl http://localhost:8001/stats
```

### Enrichment Actions

#### `POST /enrich`
Enrich records from specified table
```bash
curl -X POST http://localhost:8001/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "table": "company_invalid",
    "limit": 10
  }'
```

**Response**:
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
  },
  "timestamp": "2025-11-19T10:35:00"
}
```

#### `POST /enrich/company`
Convenience endpoint for companies
```bash
curl -X POST "http://localhost:8001/enrich/company?limit=10"
```

#### `POST /enrich/people`
Convenience endpoint for people
```bash
curl -X POST "http://localhost:8001/enrich/people?limit=5"
```

---

## 🔄 n8n Workflow Examples

### Workflow 1: Scheduled Enrichment (Every 6 Hours)

**Purpose**: Automatically enrich invalid records every 6 hours

**Flow**:
1. **Schedule Trigger** → Every 6 hours
2. **Check Invalid Count** → `GET /invalid/count`
3. **Has Invalid Records?** → If total > 0
4. **Enrich Companies** → `POST /enrich/company`
5. **Enrich People** → `POST /enrich/people`
6. **Send Notification** → Email with results

**Import**: `n8n-workflows/scheduled-enrichment.json`

**Customize**:
- Change schedule: Edit "Schedule Trigger" node
- Change batch size: Add `?limit=20` to HTTP Request URL
- Add Slack notification instead of email

### Workflow 2: Webhook Triggered Enrichment

**Purpose**: Trigger enrichment on-demand via webhook

**Flow**:
1. **Webhook Trigger** → Receives POST request
2. **Extract Parameters** → Get `table` and `limit` from body
3. **Trigger Enrichment** → `POST /enrich`
4. **Check Success** → Validate response
5. **Respond** → Return success/error to caller

**Import**: `n8n-workflows/webhook-enrichment.json`

**Test webhook**:
```bash
# Get webhook URL from n8n (Production URL)
WEBHOOK_URL="https://dbarton.app.n8n.cloud/webhook/enrichment-trigger"

# Trigger enrichment
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "table": "company_invalid",
    "limit": 10
  }'
```

### Workflow 3: Daily Monitoring & Alerts

**Custom workflow** (you can build this):

**Flow**:
1. **Schedule Trigger** → Every day at 8 AM
2. **Check Invalid Count** → `GET /invalid/count`
3. **Check Stats** → `GET /stats`
4. **If > 50 invalid records** → Send Slack alert
5. **If enrichment cost > $5** → Send budget alert
6. **Get Recent Failures** → `GET /invalid/recent`
7. **Send Summary Email** → Daily report

---

## ⚙️ n8n Node Configuration Examples

### HTTP Request Node (Check Count)

```
Method: GET
URL: http://localhost:8001/invalid/count
Headers: (none)
Authentication: None
```

### HTTP Request Node (Enrich Companies)

```
Method: POST
URL: http://localhost:8001/enrich/company?limit=10
Body: (empty)
Headers: (none)
Authentication: None
```

### HTTP Request Node (Enrich with Body)

```
Method: POST
URL: http://localhost:8001/enrich
Body: JSON
{
  "table": "company_invalid",
  "limit": 10
}
```

### IF Node (Has Invalid Records?)

```
Conditions:
  - Number
    - Value 1: {{$json.total}}
    - Operation: larger
    - Value 2: 0
```

### Email Node (Notification)

```
To: your-email@company.com
Subject: Enrichment Complete - {{$now.format('YYYY-MM-DD HH:mm')}}
Body:
✅ Enrichment Complete

Companies:
- Processed: {{$node["Enrich Companies"].json.stats.processed}}
- Enriched: {{$node["Enrich Companies"].json.stats.enriched}}
- Promoted: {{$node["Enrich Companies"].json.stats.promoted}}
- Cost: ${{$node["Enrich Companies"].json.stats.cost}}

People:
- Processed: {{$node["Enrich People"].json.stats.processed}}
- Enriched: {{$node["Enrich People"].json.stats.enriched}}
- Promoted: {{$node["Enrich People"].json.stats.promoted}}
- Cost: ${{$node["Enrich People"].json.stats.cost}}
```

---

## 🔧 Running in Production

### Option 1: Run API on Same Server as n8n

If n8n is self-hosted, run API on same server:

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
sudo systemctl status enrichment-api
```

### Option 2: Run API in Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

COPY . .

CMD ["python", "api/enrichment_api.py"]
```

```bash
docker build -t enrichment-api .
docker run -d -p 8001:8001 \
  -e DATABASE_URL="postgresql://..." \
  -e APIFY_API_KEY="..." \
  -e ABACUS_API_KEY="..." \
  -e FIRECRAWL_API_KEY="..." \
  enrichment-api
```

### Option 3: Use n8n Cloud with Public API

Deploy API to cloud service (Render, Railway, Fly.io):

```bash
# Example: Deploy to Render
# 1. Create new Web Service
# 2. Connect to GitHub repo
# 3. Build command: pip install -r requirements.txt && pip install fastapi uvicorn
# 4. Start command: python ctb/sys/enrichment-agents/api/enrichment_api.py
# 5. Add environment variables (DATABASE_URL, API keys)
# 6. Deploy
```

Then update n8n workflows to use public URL: `https://your-api.render.com`

---

## 📊 Monitoring & Logging

### View API Logs

```bash
# If running with uvicorn
tail -f /tmp/enrichment-api.log

# If running as systemd service
sudo journalctl -u enrichment-api -f
```

### View n8n Execution History

1. Go to n8n → Workflows
2. Click on workflow name
3. Click "Executions" tab
4. See all past runs with success/failure status

### Create Monitoring Workflow

Build a workflow that:
1. Runs every hour
2. Checks `/health` endpoint
3. If unhealthy → Send alert
4. If healthy → Log to database

---

## 🎯 Monthly Enrichment Strategy

### Recommended Setup

**Workflow 1: Continuous Monitoring**
- Schedule: Every 6 hours
- Batch size: 10 records per run
- Total per day: 40 records (4 runs × 10)
- Total per month: ~1,200 records

**Workflow 2: Weekly Deep Clean**
- Schedule: Every Sunday at 2 AM
- Batch size: 50 records
- Enriches backlog

**Workflow 3: On-Demand**
- Webhook trigger
- Use when you upload new batch of records
- Batch size: User-specified

---

## 🐛 Troubleshooting

### API won't start

**Check**:
```bash
# Database connection
echo $DATABASE_URL

# Python dependencies
pip list | grep -E "fastapi|uvicorn|asyncpg"

# Port availability
lsof -i:8001
```

### n8n can't reach API

**Solutions**:
- If API is on localhost, ensure n8n is on same server
- If using n8n Cloud, deploy API to public URL
- Check firewall rules
- Test with curl first

### Enrichment times out

**Increase timeout in n8n HTTP Request node**:
- Options → Request Options → Timeout: 300000 (5 minutes)

---

## 🎉 Next Steps

1. ✅ Start API server: `python api/enrichment_api.py`
2. ✅ Test health: `curl http://localhost:8001/health`
3. ✅ Import n8n workflows
4. ✅ Configure HTTP Request nodes with correct URL
5. ✅ Test scheduled workflow
6. ✅ Monitor first run
7. ✅ Set up notifications (email/Slack)
8. ✅ Deploy to production

---

**Status**: Ready for n8n Integration
**API Port**: 8001 (default)
**n8n URL**: https://dbarton.app.n8n.cloud
**Invalid Records**: 119 companies, 21 people
