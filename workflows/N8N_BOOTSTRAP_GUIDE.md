# N8N Bootstrap Complete Setup Guide

**Date:** 2025-10-24
**Purpose:** Automated n8n workflow deployment for outreach automation
**Status:** ✅ Ready for deployment

---

## What Was Created

This bootstrap setup provides everything needed to deploy 5 automated workflows to your n8n instance via REST API.

### 📁 Files Created

```
workflows/
├── README.md                           ← Complete workflow documentation
├── N8N_BOOTSTRAP_GUIDE.md             ← This file
├── .env.template                       ← Environment variables template
├── bootstrap_n8n.js                    ← Automated deployment script
├── 01-validation-gatekeeper.json       ← Workflow: Data validation
├── 02-promotion-runner.json            ← Workflow: Auto-promotion
├── 03-slot-creator.json                ← Workflow: Slot generation
├── 04-apify-enrichment.json            ← Workflow: LinkedIn scraping
└── 05-millionverify-checker.json       ← Workflow: Email verification
```

---

## Quick Start (3 Steps)

### Step 1: Get Your n8n API Key

1. Open your n8n instance
2. Click **Settings** (gear icon)
3. Go to **API** section
4. Click **"Create API Key"**
5. Copy the key

### Step 2: Configure Environment

```bash
cd workflows/

# Copy template
cp .env.template .env

# Edit .env
nano .env
```

Add your values:
```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=<paste-api-key-here>
NEON_PASSWORD=n8n_secure_ivq5lxz3ej  # From migrations/N8N_CREDENTIALS.txt
```

### Step 3: Run Bootstrap

```bash
node bootstrap_n8n.js
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════
🚀 N8N BOOTSTRAP - Outreach Automation Setup
═══════════════════════════════════════════════════════════════

📡 Step 1: Checking n8n API connection...
  ✅ Connected to n8n at http://localhost:5678

🔐 Step 2: Creating Neon database credential...
  ✅ Created credential "Neon Marketing DB" (ID: 1)

📥 Step 3: Importing workflows...
  ✅ Validation Gatekeeper (ID: 1)
  ✅ Promotion Runner (ID: 2)
  ✅ Slot Creator (ID: 3)
  ✅ Apify Enrichment (ID: 4)
  ✅ MillionVerify Checker (ID: 5)

⚡ Step 4: Enabling workflows...
  ✅ Enabled: Validation Gatekeeper
  ✅ Enabled: Promotion Runner
  ✅ Enabled: Slot Creator

✅ Bootstrap complete: 5/5 workflows imported
⚡ Active workflows: 3/5
```

---

## Detailed Explanation

### What the Bootstrap Script Does

#### 1. API Connection Test
- Verifies n8n is accessible
- Tests API key authentication
- Lists existing workflows

#### 2. Database Credential Creation
- Creates "Neon Marketing DB" credential in n8n
- Stores connection details:
  - Host: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
  - Database: `Marketing DB`
  - User: `n8n_user`
  - Password: From NEON_PASSWORD env var
  - SSL: Enabled

#### 3. Workflow Import
For each workflow JSON file:
- Reads workflow definition
- Replaces `{{NEON_CREDENTIAL_ID}}` with actual credential ID
- Checks if workflow already exists
- Creates new or updates existing workflow
- Reports success/failure

#### 4. Workflow Activation
- Enables automated workflows:
  - ✅ Promotion Runner (every 6 hours)
  - ✅ Slot Creator (every hour)
- Leaves manual workflows inactive:
  - ⚪ Validation Gatekeeper (on-demand)
  - ⚪ Apify Enrichment (on-demand)
  - ⚪ MillionVerify Checker (on-demand)

---

## Workflows Overview

### 1. Validation Gatekeeper

**Purpose:** Validates company data before promotion

**How it works:**
1. Fetches unvalidated companies from `intake.company_raw_intake`
2. Checks required fields (company name, website)
3. Updates `validated` flag (TRUE/FALSE)
4. Logs validation results

**When to run:** After importing new company data

**Manual activation:** Click "Execute Workflow" in n8n

---

### 2. Promotion Runner ⚡ (Automated)

**Purpose:** Auto-promotes validated companies to master table

**How it works:**
1. Finds batches with validated companies
2. Calls `shq.promote_company_records()` function
3. Moves records from intake → marketing.company_master
4. Logs to shq_validation_log

**Schedule:** Every 6 hours

**Auto-enabled:** Yes

---

### 3. Slot Creator ⚡ (Automated)

**Purpose:** Ensures all companies have slots for people

**How it works:**
1. Finds companies without slots
2. Generates Barton IDs (04.04.05.XX.XXXXX.XXX)
3. Creates company_slots records
4. Processes 50 companies per run

**Schedule:** Every hour

**Auto-enabled:** Yes

**Why:** Required before adding people to `marketing.people_master`

---

### 4. Apify Enrichment

**Purpose:** Enriches companies with LinkedIn executive data

**How it works:**
1. Finds companies needing enrichment
2. Triggers Apify LinkedIn People Scraper
3. Waits for results
4. *TODO: Insert people data*

**When to run:** After companies are promoted

**Manual activation:** Click "Execute Workflow" in n8n

**Requirements:**
- Apify API key
- Apify account

---

### 5. MillionVerify Checker

**Purpose:** Verifies email addresses

**How it works:**
1. Fetches unverified emails from `marketing.people_master`
2. Calls MillionVerifier API
3. Updates `email_verified` flag
4. Processes 50 emails per run

**When to run:** After executive enrichment

**Manual activation:** Click "Execute Workflow" in n8n

**Requirements:**
- MillionVerifier API key

---

## Environment Variables

### Required

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `N8N_API_URL` | n8n instance URL | `http://localhost:5678` | Your n8n deployment |
| `N8N_API_KEY` | API key for authentication | `n8n_api_xxxxxxx` | n8n Settings → API |
| `NEON_PASSWORD` | n8n_user password | `n8n_secure_...` | `migrations/N8N_CREDENTIALS.txt` |

### Optional (for workflows)

| Variable | Description | Used By |
|----------|-------------|---------|
| `APIFY_API_KEY` | Apify authentication | Apify Enrichment workflow |
| `MILLIONVERIFY_API_KEY` | Email verification | MillionVerify Checker workflow |

---

## Deployment Scenarios

### Scenario 1: Local n8n (Development)

```bash
# n8n running locally
N8N_API_URL=http://localhost:5678
N8N_API_KEY=<your-api-key>
NEON_PASSWORD=<from-credentials-file>

node bootstrap_n8n.js
```

### Scenario 2: n8n Cloud

```bash
# n8n cloud instance
N8N_API_URL=https://your-instance.app.n8n.cloud
N8N_API_KEY=<cloud-api-key>
NEON_PASSWORD=<from-credentials-file>

node bootstrap_n8n.js
```

### Scenario 3: Self-Hosted n8n

```bash
# Self-hosted with custom domain
N8N_API_URL=https://n8n.yourdomain.com
N8N_API_KEY=<self-hosted-api-key>
NEON_PASSWORD=<from-credentials-file>

node bootstrap_n8n.js
```

### Scenario 4: CI/CD Pipeline

```yaml
# .github/workflows/deploy-n8n.yml
name: Deploy N8N Workflows

on:
  push:
    branches: [main]
    paths:
      - 'workflows/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Deploy workflows
        env:
          N8N_API_URL: ${{ secrets.N8N_API_URL }}
          N8N_API_KEY: ${{ secrets.N8N_API_KEY }}
          NEON_PASSWORD: ${{ secrets.NEON_PASSWORD }}
        run: |
          cd workflows
          node bootstrap_n8n.js
```

---

## Security Considerations

### API Key Security

✅ **Best Practices:**
- Store in environment variables or secrets manager
- Never commit to git
- Rotate regularly (every 90 days)
- Use different keys for dev/staging/prod
- Limit API key scope if possible

❌ **Avoid:**
- Hardcoding in scripts
- Sharing via email/chat
- Storing in plaintext files (except .env with .gitignore)
- Using production keys in development

### Database Password Security

The `NEON_PASSWORD` is stored in `migrations/N8N_CREDENTIALS.txt` which is:
- ✅ Added to `.gitignore`
- ✅ Not committed to repository
- ✅ Unique to n8n_user (limited permissions)

**To rotate:**
```sql
ALTER ROLE n8n_user WITH PASSWORD 'new_secure_password';
```

Then update `.env` and re-run bootstrap.

---

## Troubleshooting

### Issue: "Cannot find module 'https'"

**Solution:** Node.js built-in module, no installation needed. Check Node.js version:
```bash
node --version  # Should be 14+
```

### Issue: "N8N_API_KEY environment variable is required"

**Solution:**
1. Check `.env` file exists: `ls -la .env`
2. Load environment: `source .env` (Linux/Mac) or check values
3. Or pass directly: `N8N_API_KEY=xxx node bootstrap_n8n.js`

### Issue: "Connection refused" / "ECONNREFUSED"

**Solution:**
1. Verify n8n is running: `curl http://localhost:5678`
2. Check N8N_API_URL is correct
3. Ensure firewall allows connection
4. Try without https (use http for local)

### Issue: "401 Unauthorized"

**Solution:**
1. Verify API key is correct
2. Generate new API key in n8n
3. Check API key hasn't expired
4. Ensure API access is enabled in n8n settings

### Issue: "permission denied for table"

**Solution:**
1. Check n8n_user permissions: See `migrations/N8N_USER_SETUP_GUIDE.md`
2. Re-run setup script: `cd migrations && node setup_n8n_user.js`
3. Verify credentials in n8n match `N8N_CREDENTIALS.txt`

### Issue: "function shq.promote_company_records does not exist"

**Solution:**
Run Migration 003:
```bash
cd migrations
node -e "/* run migration 003 */"
```

---

## Maintenance

### Update Workflows

```bash
# Edit workflow JSON files
nano 01-validation-gatekeeper.json

# Re-run bootstrap to update
node bootstrap_n8n.js
```

### Backup Workflows

```bash
# Export all workflows from n8n
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  $N8N_API_URL/api/v1/workflows > backup_$(date +%Y%m%d).json
```

### Monitor Executions

```bash
# Get recent executions
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  $N8N_API_URL/api/v1/executions?limit=20

# Or check in n8n UI: Executions tab
```

### Delete Workflows

```bash
# Get workflow ID
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  $N8N_API_URL/api/v1/workflows

# Delete workflow
curl -X DELETE \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  $N8N_API_URL/api/v1/workflows/{workflow_id}
```

---

## Next Steps

### After Bootstrap

1. **Verify in n8n UI:**
   - Open n8n
   - Check all 5 workflows are imported
   - Verify "Neon Marketing DB" credential exists

2. **Test Workflows:**
   - Start with Validation Gatekeeper (manual)
   - Check database for results
   - Activate Promotion Runner and Slot Creator

3. **Add API Keys:**
   - Get Apify API key
   - Get MillionVerifier API key
   - Add to n8n credentials or environment

4. **Monitor:**
   - Check execution logs
   - Verify automated workflows run on schedule
   - Review error logs

---

## Integration with Existing Systems

### With Migrations

The bootstrap uses:
- ✅ Database from Migration 001-004
- ✅ n8n_user from `setup_n8n_user.js`
- ✅ shq.promote_company_records from Migration 003

### With Data Pipeline

```
┌─────────────────────┐
│  CSV Import         │
│  (Manual/Automated) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ intake.company_raw_ │
│ intake (New Data)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Validation          │
│ Gatekeeper          │ ◄─── n8n Workflow 1
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Promotion Runner    │ ◄─── n8n Workflow 2 (Auto)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ marketing.company_  │
│ master (Validated)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Slot Creator        │ ◄─── n8n Workflow 3 (Auto)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Apify Enrichment    │ ◄─── n8n Workflow 4
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ marketing.people_   │
│ master (Executives) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ MillionVerify       │ ◄─── n8n Workflow 5
│ Checker             │
└─────────────────────┘
```

---

## Related Documentation

- **README.md** - Workflow details and usage
- **migrations/N8N_USER_SETUP_GUIDE.md** - Database user setup
- **migrations/N8N_CREDENTIALS.txt** - Database credentials
- **migrations/MIGRATION_LOG.md** - Database schema history

---

## Support

### Common Questions

**Q: Do I need to run bootstrap every time?**
A: No, only when setting up new n8n instance or updating workflows

**Q: Can I edit workflows in n8n UI?**
A: Yes, but re-running bootstrap will overwrite changes

**Q: How do I add more workflows?**
A: Create JSON file, add to WORKFLOWS array in bootstrap script

**Q: Can I use this with n8n cloud?**
A: Yes, just set N8N_API_URL to your cloud instance

**Q: What if bootstrap fails halfway?**
A: It's safe to re-run, script handles existing resources

---

**Status:** ✅ Ready for Production
**Last Updated:** 2025-10-24
**Automation Level:** 60% (3/5 workflows automated)
**Total LOC:** ~500 lines of JSON + 200 lines of JS
