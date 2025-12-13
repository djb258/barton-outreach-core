# Enrichment Agents - Universal Enrichment System

**Barton Doctrine ID**: `04.04.02.04.50000.000`

## 🎯 What This Does

Automatically enriches invalid records (companies and people) by:
1. **Pulling batches** from `marketing.company_invalid` and `marketing.people_invalid`
2. **Analyzing validation errors** to see what fields are missing
3. **Routing to agents** (Apify, Abacus, Firecrawl) to find missing data
4. **Populating fields** with enriched data
5. **Re-validating** records after enrichment
6. **Promoting** to master tables if now valid

## 🔧 Agents

### 1. Apify (LinkedIn & Google Maps Scraping)
- **linkedin_company_scraper**: Extract company data from LinkedIn
- **linkedin_profile_scraper**: Extract person data from LinkedIn profiles
- **google_maps_scraper**: Extract business info from Google Maps

### 2. Abacus (Data Validation & Enrichment)
- **email_validation**: Validate and verify email addresses
- **company_enrichment**: Enrich company data (employee count, industry, etc.)
- **person_enrichment**: Enrich person data (email, title, LinkedIn)

### 3. Firecrawl (Website Scraping)
- **scrape_company_website**: Extract structured data from company websites
- **search_company**: Search for company website and LinkedIn URL

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install asyncpg aiohttp python-dotenv
```

### 2. Set API Keys

Add to your `.env` file:

```bash
# Enrichment Agent API Keys
APIFY_API_KEY=your_apify_api_key_here
ABACUS_API_KEY=your_abacus_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Database (already set)
DATABASE_URL=postgresql://marketing_db_owner:G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### 3. Run Enrichment

```bash
# Enrich 10 companies
python run_enrichment.py --table company_invalid --limit 10

# Enrich 5 people
python run_enrichment.py --table people_invalid --limit 5

# Enrich both (10 each)
python run_enrichment.py --table both --limit 10

# Continuous mode (run every 5 minutes)
python run_enrichment.py --continuous --interval 300
```

## 📊 How It Works

### Field Routing (Automatic)

The system automatically routes fields to agents based on `config/agent_config.json`:

**Company Fields**:
- `website` → Firecrawl (search), Abacus (enrichment)
- `employee_count` → Apify (LinkedIn), Firecrawl (scrape), Abacus (enrichment)
- `linkedin_url` → Apify (LinkedIn), Firecrawl (search)
- `industry` → Firecrawl (scrape), Abacus (enrichment)
- `address` → Apify (Google Maps), Firecrawl (scrape)
- `phone` → Apify (Google Maps), Firecrawl (scrape)

**Person Fields**:
- `email` → Abacus (validation), Abacus (enrichment)
- `linkedin_url` → Apify (LinkedIn), Abacus (enrichment)
- `title` → Apify (LinkedIn), Abacus (enrichment)

### Throttle Controls (Prevents Runaway Agents)

From `config/agent_config.json`:

```json
"throttle_rules": {
  "max_time_per_record_seconds": 180,     // Max 3 minutes per record
  "max_agents_per_field": 2,              // Try max 2 agents per field
  "skip_if_cost_exceeds": 0.50,           // Skip if cost > $0.50
  "abort_if_no_progress_after_attempts": 3 // Stop after 3 failed attempts
}
```

Each agent also has:
- **Individual timeouts** (30-120 seconds per call)
- **Rate limits** (e.g., Apify: 30/min, Abacus: 100/min, Firecrawl: 50/min)
- **Retry logic** with exponential backoff

### Example Enrichment Flow

**Input**: Company with missing `employee_count` and `linkedin_url`

```
1. Pull record from company_invalid
   - company_name: "Acme Corp"
   - website: "https://acme.com"
   - employee_count: NULL ❌
   - linkedin_url: NULL ❌

2. Analyze validation_errors:
   - Field: employee_count, Error: "required"
   - Field: linkedin_url, Error: "required"

3. Route to agents:
   - employee_count → Apify (linkedin_company_scraper)
   - linkedin_url → Apify (linkedin_company_scraper)

4. Call Apify:
   - Input: {company_name: "Acme Corp"}
   - Output: {employee_count: 250, linkedin_url: "https://linkedin.com/company/acme"}
   - Duration: 12.5s
   - Cost: $0.01

5. Update record:
   - employee_count: 250 ✅
   - linkedin_url: "https://linkedin.com/company/acme" ✅

6. Re-validate:
   - All required fields present: ✅

7. Promote:
   - INSERT into marketing.company_master
   - CREATE 3 slots (CEO, CFO, HR)
   - DELETE from marketing.company_invalid
```

## 📈 Monitoring

### Real-time Output

```
🔄 Enriching: Acme Corp (ID: 123)
   Found 2 validation errors
   Enrichment plan: 2 agent calls
   → Calling apify.linkedin_company_scraper for field 'employee_count'
      ✅ Success: ['employee_count', 'linkedin_url', 'industry']
   ✍️  Updated 3 fields
   🎉 Promoted to master table!
```

### Stats

```
📊 Batch Summary:
   Processed:  10
   Enriched:   7
   Promoted:   3
   Failed:     0
   Cost:       $0.08

📊 Agent Statistics:
   APIFY:
      Total calls: 15
      Total cost:  $0.15
      Status:      OK

   ABACUS:
      Total calls: 8
      Total cost:  $0.02
      Status:      OK
```

## ⚙️ Configuration

### Agent Timeouts

Edit `config/agent_config.json`:

```json
{
  "agents": {
    "apify": {
      "timeout_seconds": 120,  // Global timeout
      "capabilities": {
        "linkedin_company_scraper": {
          "timeout_seconds": 90  // Capability-specific timeout
        }
      }
    }
  }
}
```

### Rate Limits

```json
{
  "agents": {
    "apify": {
      "rate_limit": {
        "calls_per_minute": 30,
        "calls_per_hour": 500
      }
    }
  }
}
```

### Batch Size

```json
{
  "enrichment_config": {
    "batch_size": 10,              // Pull 10 records per batch
    "max_concurrent_agents": 3     // Run max 3 agents at once
  }
}
```

## 🔒 Safety Features

1. **Timeouts**: No agent runs forever
   - Per-agent timeouts (30-120s)
   - Per-record timeout (180s max)
   - Global timeout (300s)

2. **Rate Limiting**: Respects API limits
   - Per-minute limits
   - Per-hour limits
   - Automatic backoff

3. **Cost Controls**:
   - Skip if cost exceeds threshold
   - Track costs per agent/call
   - Show cumulative costs

4. **Retry Logic**:
   - Max 2 retries per call
   - Exponential backoff (2s, 4s)
   - No retry on rate limits/timeouts

5. **Progress Tracking**:
   - `last_enrichment_attempt` timestamp
   - Avoid enriching same record repeatedly
   - Skip recently attempted records (1 hour cooldown)

## 📊 Database Schema Changes Needed

Add to `marketing.company_invalid` and `marketing.people_invalid`:

```sql
-- Add enrichment tracking columns
ALTER TABLE marketing.company_invalid
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ;

ALTER TABLE marketing.people_invalid
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ;
```

## 🧪 Testing

### Test Single Record

```python
from orchestrator.enrichment_orchestrator import EnrichmentOrchestrator

# Load config
config = json.load(open('config/agent_config.json'))

# Create orchestrator
orchestrator = EnrichmentOrchestrator(config, db_connection)

# Test single record
result = await orchestrator._enrich_single_record(
    record={'id': 123, 'company_name': 'Test Corp', ...},
    table_name='company_invalid',
    record_type='company'
)
```

### Test Agent Directly

```python
from agents.apify_agent import ApifyAgent

# Create agent
config = {...}
agent = ApifyAgent(config)

# Test capability
result = await agent.enrich_with_retry(
    'linkedin_company_scraper',
    {'company_name': 'Acme Corp'},
    timeout_seconds=60
)

print(result)
# {'success': True, 'data': {...}, 'cost': 0.01, 'duration': 12.5}
```

## 🚨 Troubleshooting

### "API key not found"

Add API keys to `.env`:
```bash
APIFY_API_KEY=your_key_here
```

### "Rate limit exceeded"

Increase interval or reduce batch size in `agent_config.json`

### "Timeout"

Increase timeout in `agent_config.json` for specific capability

### "No enrichment agents available"

Check `field_routing` in config - field might not be mapped to any agent

## 📚 Files

```
ctb/sys/enrichment-agents/
├── README.md                           # This file
├── run_enrichment.py                   # CLI runner
├── config/
│   └── agent_config.json               # Agent configuration
├── agents/
│   ├── base_agent.py                   # Base agent class
│   ├── apify_agent.py                  # Apify integration
│   ├── abacus_agent.py                 # Abacus integration
│   └── firecrawl_agent.py              # Firecrawl integration
└── orchestrator/
    └── enrichment_orchestrator.py      # Main orchestrator
```

## 🎯 Next Steps

1. **Add API keys** to `.env`
2. **Test with small batch**: `python run_enrichment.py --limit 5`
3. **Check results** in `company_invalid` / `people_invalid`
4. **Monitor costs** in output
5. **Tune timeouts** if needed
6. **Set up continuous mode** for monthly runs

## 💡 Monthly Enrichment Strategy

```bash
# Option 1: Cron job (runs every night at 2 AM)
0 2 * * * cd /path/to/enrichment-agents && python run_enrichment.py --limit 50

# Option 2: Continuous mode (always running)
python run_enrichment.py --continuous --interval 3600  # Every hour

# Option 3: Manual monthly runs
python run_enrichment.py --table both --limit 100
```

---

**Status**: ✅ Ready for Testing
**Date**: 2025-11-19
**Invalid Records**: 119 companies, 21 people
