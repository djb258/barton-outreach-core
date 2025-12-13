# Enrichment Agents Setup Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies

```bash
cd ctb/sys/enrichment-agents
pip install -r requirements.txt
```

**Dependencies**:
- `asyncpg` - Async PostgreSQL driver
- `aiohttp` - Async HTTP client for API calls
- `python-dotenv` - Environment variable management

### Step 2: Add API Keys

Edit `.env` in the root directory and add your API keys:

```bash
# Enrichment Agent API Keys
APIFY_API_KEY=your_apify_api_key_here
ABACUS_API_KEY=your_abacus_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

**Where to get API keys**:
- **Apify**: https://console.apify.com/account/integrations
- **Abacus**: https://abacus.ai/app/profile/apikey
- **Firecrawl**: https://firecrawl.dev/app/api-keys

### Step 3: Run Database Migration

Add enrichment tracking columns to invalid tables:

```bash
# Using psql
psql "$DATABASE_URL" -f ../../infra/migrations/007_add_enrichment_tracking_columns.sql

# Or using Node.js
node ../../infra/scripts/run-migration.js 007_add_enrichment_tracking_columns.sql
```

### Step 4: Test Connection

```bash
python run_enrichment.py --limit 1
```

**Expected output**:
```
✅ Connected to database
🤖 Enrichment Orchestrator Ready
   Agents enabled: ['apify', 'abacus', 'firecrawl']
   Batch size: 10
   Max time per record: 180s

📦 Starting batch enrichment for company_invalid
   Pulled 1 records

🔄 Enriching: Acme Corp (ID: 123)
   ...
```

---

## 📊 Current Invalid Records

**As of 2025-11-19**:
- **119 invalid companies** in `marketing.company_invalid`
- **21 invalid people** in `marketing.people_invalid`

**Total potential enrichment**: 140 records

---

## 🎯 Usage Examples

### Example 1: Enrich Small Batch (Testing)

```bash
# Test with 3 companies
python run_enrichment.py --table company_invalid --limit 3
```

### Example 2: Enrich All Invalid Records

```bash
# Process all invalid companies
python run_enrichment.py --table company_invalid --limit 119

# Process all invalid people
python run_enrichment.py --table people_invalid --limit 21
```

### Example 3: Continuous Enrichment (Monthly Run)

```bash
# Run continuously, check every 5 minutes
python run_enrichment.py --continuous --interval 300
```

This will:
1. Pull batch of 10 records
2. Enrich them
3. Wait 5 minutes
4. Repeat

### Example 4: Scheduled Enrichment (Cron)

Add to crontab for daily enrichment at 2 AM:

```bash
0 2 * * * cd /path/to/barton-outreach-core/ctb/sys/enrichment-agents && python run_enrichment.py --limit 50 >> /tmp/enrichment.log 2>&1
```

---

## ⚙️ Configuration

### Adjust Batch Size

Edit `config/agent_config.json`:

```json
{
  "enrichment_config": {
    "batch_size": 20,  // Increase from 10 to 20
    "max_concurrent_agents": 5  // Increase from 3 to 5
  }
}
```

### Adjust Timeouts

```json
{
  "throttle_rules": {
    "max_time_per_record_seconds": 300,  // Increase from 180 to 300
    "max_agents_per_field": 3  // Increase from 2 to 3
  }
}
```

### Enable/Disable Agents

```json
{
  "agents": {
    "apify": {
      "enabled": true  // Set to false to disable
    },
    "abacus": {
      "enabled": false  // Disabled
    }
  }
}
```

---

## 🔍 Monitoring

### Check Progress

```bash
# Check how many invalid records remain
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM marketing.company_invalid;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM marketing.people_invalid;"
```

### View Recent Enrichments

```bash
# Recent enrichment attempts
psql "$DATABASE_URL" -c "
SELECT company_name, last_enrichment_attempt, enrichment_attempt_count
FROM marketing.company_invalid
WHERE last_enrichment_attempt IS NOT NULL
ORDER BY last_enrichment_attempt DESC
LIMIT 10;
"
```

### View Promoted Records

```bash
# Recently promoted companies
psql "$DATABASE_URL" -c "
SELECT company_name, created_at
FROM marketing.company_master
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
"
```

---

## 💰 Cost Estimation

Based on configuration:

| Agent | Cost per Call | Typical Calls per Record | Cost per Record |
|-------|---------------|-------------------------|-----------------|
| Apify | $0.01 | 1-2 | $0.01-$0.02 |
| Abacus | $0.002 | 1-3 | $0.002-$0.006 |
| Firecrawl | $0.005 | 1-2 | $0.005-$0.01 |

**Estimated total cost for 140 records**: $2.50 - $5.00

**Monthly budget recommendation**: $10-$20 (includes retries and failures)

---

## 🐛 Troubleshooting

### Issue: "API key not found"

**Solution**: Add API key to `.env`:
```bash
APIFY_API_KEY=apify_api_xyz123
```

### Issue: "Connection refused"

**Solution**: Check database URL:
```bash
echo $DATABASE_URL
```

Should output:
```
postgresql://marketing_db_owner:G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### Issue: "Rate limit exceeded"

**Solution**: Reduce batch size or increase interval:
```bash
python run_enrichment.py --limit 5 --continuous --interval 600
```

### Issue: "Timeout"

**Solution**: Increase timeout in `config/agent_config.json`:
```json
{
  "throttle_rules": {
    "max_time_per_record_seconds": 300
  }
}
```

### Issue: "No enrichment agents available"

**Cause**: Field not mapped in `field_routing`

**Solution**: Add field mapping to `config/agent_config.json`:
```json
{
  "field_routing": {
    "company": {
      "your_field_name": ["agent.capability"]
    }
  }
}
```

---

## 📈 Success Metrics

After running enrichment, you should see:

✅ **Reduced invalid count**
```sql
-- Before: 119 invalid companies
-- After: 80 invalid companies (39 promoted)
```

✅ **Increased master table records**
```sql
-- Before: 458 valid companies
-- After: 497 valid companies (+39)
```

✅ **Filled validation errors**
```sql
-- Records with enriched data
SELECT company_name, last_enrichment_attempt
FROM marketing.company_invalid
WHERE last_enrichment_attempt IS NOT NULL;
```

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Add API keys to `.env`
3. ✅ Run database migration
4. ✅ Test with small batch (`--limit 3`)
5. ✅ Review results in database
6. ✅ Monitor costs
7. ✅ Adjust configuration as needed
8. ✅ Set up continuous/scheduled enrichment

---

**Status**: Ready for Production
**Date**: 2025-11-19
**Invalid Records**: 119 companies, 21 people
**Estimated Cost**: $2.50-$5.00 total
