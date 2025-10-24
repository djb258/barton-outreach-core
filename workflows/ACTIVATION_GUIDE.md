# N8N Workflow Activation Guide

**Date:** 2025-10-24
**n8n Instance:** https://dbarton.app.n8n.cloud

## ✅ Current Status

All 5 workflows have been successfully imported:

| Workflow                  | ID               | Active | Priority |
|---------------------------|------------------|--------|----------|
| Validation Gatekeeper     | qvKf2iqxEZrCYPoI | ❌ No  | Manual   |
| Promotion Runner          | KFLye1yXNjvXgAn1 | ❌ No  | **HIGH** |
| Slot Creator              | BQU4q99xBcdE0LaH | ❌ No  | **HIGH** |
| Apify Enrichment          | euSD6SOXPrqnsFxc | ❌ No  | Low      |
| MillionVerify Checker     | RAeFH4CStkDcDAnm | ❌ No  | Low      |

## 📋 Activation Instructions

### Step 1: Open n8n Cloud
Navigate to: https://dbarton.app.n8n.cloud

### Step 2: Activate High-Priority Workflows

#### 2.1 Promotion Runner (Every 6 hours)
1. Click on **"Promotion Runner"** workflow
2. Click the **toggle switch** in the top-right to activate
3. Verify schedule is set to: **Every 6 hours**
4. Click **"Save"**

**What it does:** Auto-promotes validated companies from `intake.company_raw_intake` to `marketing.company_master`

---

#### 2.2 Slot Creator (Every hour)
1. Click on **"Slot Creator"** workflow
2. Click the **toggle switch** in the top-right to activate
3. Verify schedule is set to: **Every hour**
4. Click **"Save"**

**What it does:** Creates company slots (3 per company: CEO, CFO, HR) with Barton IDs

---

### Step 3: Test Manual Workflows

#### 3.1 Validation Gatekeeper
1. Click on **"Validation Gatekeeper"** workflow
2. Click **"Test workflow"** button
3. Check execution results
4. Verify companies are validated in database

**When to run:** After importing new company data to `intake.company_raw_intake`

---

### Step 4: Optional - Configure Enrichment Workflows

#### 4.1 Apify Enrichment (Requires API Key)
1. Add Apify credentials in n8n
2. Test with a small batch
3. Enable when ready

#### 4.2 MillionVerify Checker (Requires API Key)
1. Add MillionVerifier credentials in n8n
2. Test with 10-20 emails
3. Enable when ready

---

## 🔐 Credentials Check

The bootstrap script created: **"Neon Marketing DB"** credential

To verify:
1. Go to **Settings** → **Credentials**
2. Look for **"Neon Marketing DB"** (Type: PostgreSQL)
3. If not found, create manually:
   - **Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
   - **Port:** 5432
   - **Database:** Marketing DB
   - **User:** n8n_user
   - **Password:** `n8n_secure_ivq5lxz3ej`
   - **SSL:** Enable

---

## 📊 Execution Order

The workflows run in this sequence:

```
1. [Manual] Validation Gatekeeper
   ↓ validates intake data

2. [Auto] Promotion Runner (every 6 hours)
   ↓ promotes validated companies

3. [Auto] Slot Creator (every hour)
   ↓ creates company slots

4. [Manual] Apify Enrichment
   ↓ fetches executive data

5. [Manual] MillionVerify Checker
   ↓ verifies email addresses
```

---

## ✅ Verification Checklist

After activation, verify:

- [ ] Promotion Runner is active and scheduled
- [ ] Slot Creator is active and scheduled
- [ ] Validation Gatekeeper can be manually triggered
- [ ] Database credential is configured
- [ ] Test batch `20251024-WV-B1` validates successfully

---

## 🧪 Test Commands

### Test Database Connection
```bash
psql "postgresql://n8n_user:n8n_secure_ivq5lxz3ej@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing DB?sslmode=require" -c "\dt intake.*"
```

### Check Validation Status
```sql
SELECT
  import_batch_id,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE validated = TRUE) as validated,
  COUNT(*) FILTER (WHERE validated = FALSE) as failed
FROM intake.company_raw_intake
WHERE import_batch_id = '20251024-WV-B1'
GROUP BY import_batch_id;
```

### Check Promotion Status
```sql
SELECT COUNT(*) as promoted_count
FROM marketing.company_master
WHERE import_batch_id = '20251024-WV-B1';
```

### Check Slot Creation
```sql
SELECT
  c.company_name,
  COUNT(cs.slot_id) as slot_count
FROM marketing.company_master c
LEFT JOIN marketing.company_slots cs ON c.company_unique_id = cs.company_unique_id
WHERE c.import_batch_id = '20251024-WV-B1'
GROUP BY c.company_name
LIMIT 10;
```

---

## 🔧 Troubleshooting

### Issue: Workflow won't activate
**Solution:** Check that the database credential is properly configured

### Issue: Execution fails with "permission denied"
**Solution:** Verify n8n_user permissions (see `migrations/N8N_USER_SETUP_GUIDE.md`)

### Issue: No data in workflows
**Solution:** Ensure intake table has data with correct `import_batch_id`

---

**Status:** ✅ All workflows imported and ready for activation
**Next Step:** Activate Promotion Runner and Slot Creator in n8n UI
