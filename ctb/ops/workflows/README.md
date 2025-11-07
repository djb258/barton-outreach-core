# N8N Outreach Automation Workflows

Automated workflows for the barton-outreach-core marketing database operations.

---

## Overview

This directory contains 5 n8n workflows that automate the entire outreach data pipeline:

| # | Workflow | Purpose | Trigger |
|---|----------|---------|---------|
| 1 | **Validation Gatekeeper** | Validates company data in intake | Manual/On-demand |
| 2 | **Promotion Runner** | Promotes validated companies to master | Every 6 hours |
| 3 | **Slot Creator** | Creates company slots for new records | Every hour |
| 4 | **Apify Enrichment** | Enriches companies with LinkedIn data | Manual/On-demand |
| 5 | **MillionVerify Checker** | Verifies email addresses | Manual/On-demand |

---

## Quick Start

### 1. Prerequisites

- **n8n installed** (local, cloud, or self-hosted)
- **n8n API access** (API key required)
- **Neon database** with n8n_user configured
- **Node.js** 14+ (for bootstrap script)

### 2. Setup

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Edit .env and add your values:
#    - N8N_API_URL (your n8n instance URL)
#    - N8N_API_KEY (get from n8n Settings → API)
#    - NEON_PASSWORD (from migrations/N8N_CREDENTIALS.txt)
nano .env

# 3. Run bootstrap script
node bootstrap_n8n.js
```

### 3. Verify

```bash
# Check workflows in n8n UI
# All 5 workflows should be imported and ready to activate
```

---

## Configuration

### Environment Variables

Create a `.env` file (never commit this):

```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_api_key_here
NEON_PASSWORD=n8n_secure_ivq5lxz3ej
```

**How to get N8N_API_KEY:**
1. Open n8n
2. Go to Settings → API
3. Click "Create API Key"
4. Copy and paste into `.env`

---

## Workflows

### 1. Validation Gatekeeper

**File:** `01-validation-gatekeeper.json`

**What it does:**
- Fetches unvalidated companies from `intake.company_raw_intake`
- Checks if required fields are present (company name, website)
- Marks records as validated (TRUE) or failed (FALSE)
- Logs validation results

**Trigger:** Manual (click "Test workflow" in n8n)

**Frequency:** On-demand

**Tables Used:**
- READ: `intake.company_raw_intake`
- WRITE: `intake.company_raw_intake` (validated, validated_at, validated_by)

**Sample Output:**
```
✅ 8/10 companies validated
❌ 2/10 companies failed validation
```

---

### 2. Promotion Runner

**File:** `02-promotion-runner.json`

**What it does:**
- Finds batches with validated companies
- Calls `shq.promote_company_records()` function
- Moves validated companies from intake → master table
- Logs promotion results

**Trigger:** Schedule (every 6 hours)

**Frequency:** Automated

**Tables Used:**
- READ: `intake.company_raw_intake`
- WRITE: `marketing.company_master`, `public.shq_validation_log`

**Note:** Uses the promotion function created in Migration 003

---

### 3. Slot Creator

**File:** `03-slot-creator.json`

**What it does:**
- Finds companies in master table without slots
- Generates Barton IDs (04.04.05.XX.XXXXX.XXX)
- Creates company slots for people assignment
- Processes up to 50 companies per run

**Trigger:** Schedule (every hour)

**Frequency:** Automated

**Tables Used:**
- READ: `marketing.company_master`, `marketing.company_slots`
- WRITE: `marketing.company_slots`

**Why:** Slots are required before adding people to `marketing.people_master`

---

### 4. Apify Enrichment

**File:** `04-apify-enrichment.json`

**What it does:**
- Finds companies needing executive enrichment
- Triggers Apify LinkedIn People Scraper
- Waits for results
- *TODO: Add people insert logic*

**Trigger:** Manual (click "Test workflow" in n8n)

**Frequency:** On-demand

**Tables Used:**
- READ: `marketing.company_master`, `marketing.company_slots`
- WRITE: *(future)* `marketing.people_master`

**Requirements:**
- Apify API key
- Apify account with LinkedIn scraper access

---

### 5. MillionVerify Checker

**File:** `05-millionverify-checker.json`

**What it does:**
- Fetches people with unverified emails
- Verifies emails via MillionVerifier API
- Updates `email_verified` flag
- Processes 50 emails per run

**Trigger:** Manual (click "Test workflow" in n8n)

**Frequency:** On-demand (run after enrichment)

**Tables Used:**
- READ: `marketing.people_master`
- WRITE: `marketing.people_master` (email_verified, updated_at)

**Requirements:**
- MillionVerifier API key

---

## Bootstrap Script

### `bootstrap_n8n.js`

Automated setup script that:

1. ✅ Tests n8n API connection
2. 🔐 Creates "Neon Marketing DB" credential
3. 📥 Imports all 5 workflows
4. ⚡ Enables workflows (optional)

**Usage:**

```bash
# Basic usage (with .env file)
node bootstrap_n8n.js

# Or with environment variables
N8N_API_URL=http://localhost:5678 \
N8N_API_KEY=your_key \
NEON_PASSWORD=your_password \
node bootstrap_n8n.js
```

**Output:**

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
  ℹ️  Manual trigger: Apify Enrichment
  ℹ️  Manual trigger: MillionVerify Checker

═══════════════════════════════════════════════════════════════
📊 SUMMARY

| Workflow                  | ID  | Status    | Active |
|---------------------------|-----|-----------|--------|
| Validation Gatekeeper     | 1   | ✅ imported | ✅   |
| Promotion Runner          | 2   | ✅ imported | ✅   |
| Slot Creator              | 3   | ✅ imported | ✅   |
| Apify Enrichment          | 4   | ✅ imported | ❌   |
| MillionVerify Checker     | 5   | ✅ imported | ❌   |

✅ Bootstrap complete: 5/5 workflows imported
⚡ Active workflows: 3/5
🔗 n8n URL: http://localhost:5678
```

---

## Manual Import (Alternative)

If you prefer to import workflows manually:

1. Open n8n UI
2. Go to Workflows
3. Click "Import from File"
4. Select workflow JSON file
5. Open workflow
6. Update Postgres credential to "Neon Marketing DB"
7. Save and activate

---

## Testing Workflows

### Test Validation Gatekeeper

```bash
# 1. Add test company to intake
psql <neon-connection-string> -c "
INSERT INTO intake.company_raw_intake (company, website)
VALUES ('Test Company', 'https://test.com');
"

# 2. Run workflow in n8n (click "Test workflow")

# 3. Check results
psql <neon-connection-string> -c "
SELECT company, validated, validation_notes
FROM intake.company_raw_intake
WHERE company = 'Test Company';
"
```

### Test Promotion Runner

```bash
# 1. Mark company as validated
psql <neon-connection-string> -c "
UPDATE intake.company_raw_intake
SET validated = TRUE, import_batch_id = 'TEST-001'
WHERE company = 'Test Company';
"

# 2. Run workflow in n8n

# 3. Verify promotion
psql <neon-connection-string> -c "
SELECT company_name, company_unique_id
FROM marketing.company_master
WHERE import_batch_id = 'TEST-001';
"
```

---

## Troubleshooting

### API Connection Failed

**Error:** `Connection refused` or `ECONNREFUSED`

**Solutions:**
1. Verify n8n is running: `curl http://localhost:5678`
2. Check N8N_API_URL is correct
3. Ensure n8n API is enabled (check n8n settings)

### Authentication Failed

**Error:** `401 Unauthorized` or `403 Forbidden`

**Solutions:**
1. Verify N8N_API_KEY is correct
2. Generate new API key in n8n
3. Check API key has proper permissions

### Database Connection Failed

**Error:** `permission denied` or `relation does not exist`

**Solutions:**
1. Verify Neon credentials are correct
2. Check `migrations/N8N_CREDENTIALS.txt` for password
3. Test connection with psql:
   ```bash
   psql postgresql://n8n_user:<password>@<host>/Marketing%20DB
   ```
4. Verify n8n_user has required permissions

### Workflow Import Failed

**Error:** `Invalid workflow JSON`

**Solutions:**
1. Check workflow JSON syntax
2. Ensure credential placeholder `{{NEON_CREDENTIAL_ID}}` is replaced
3. Try manual import via n8n UI

---

## Security

### Credentials

✅ **DO:**
- Store credentials in `.env` file
- Add `.env` to `.gitignore`
- Use environment variables for API keys
- Rotate API keys regularly

❌ **DON'T:**
- Commit `.env` to git
- Share credentials via email/chat
- Hardcode credentials in workflows
- Use the same password across environments

### API Keys

| Key | Purpose | Get From |
|-----|---------|----------|
| N8N_API_KEY | n8n REST API access | n8n Settings → API |
| NEON_PASSWORD | Database access | migrations/N8N_CREDENTIALS.txt |
| APIFY_API_KEY | LinkedIn scraping | Apify dashboard |
| MILLIONVERIFY_API_KEY | Email verification | MillionVerifier dashboard |

---

## Maintenance

### Update Workflows

```bash
# Re-run bootstrap to update all workflows
node bootstrap_n8n.js
```

### Monitor Executions

```bash
# Check workflow execution history in n8n UI
# Or via API:
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  http://localhost:5678/api/v1/executions
```

### Backup Workflows

```bash
# Export all workflows
mkdir -p backups
curl -H "X-N8N-API-KEY: $N8N_API_KEY" \
  http://localhost:5678/api/v1/workflows > backups/workflows_$(date +%Y%m%d).json
```

---

## Related Documentation

- **migrations/N8N_CREDENTIALS.txt** - Database credentials
- **migrations/N8N_USER_SETUP_GUIDE.md** - Database user setup
- **migrations/MIGRATION_LOG.md** - Database schema changes
- **migrations/DATABASE_CLEANUP_REPORT.md** - Database cleanup

---

## Support

### Common Issues

1. **"Credential not found"**
   - Ensure "Neon Marketing DB" credential exists in n8n
   - Re-run bootstrap script

2. **"Workflow execution failed"**
   - Check n8n execution logs
   - Verify database permissions
   - Test SQL queries manually

3. **"Function does not exist"**
   - Run Migration 003 (promotion function)
   - Check `shq` schema exists

### Getting Help

1. Check workflow execution logs in n8n
2. Review n8n system logs
3. Test database connection manually
4. Verify API keys are valid

---

**Created:** 2025-10-24
**Status:** Ready for deployment
**Total Workflows:** 5
**Automation Level:** 60% (3/5 automated)
