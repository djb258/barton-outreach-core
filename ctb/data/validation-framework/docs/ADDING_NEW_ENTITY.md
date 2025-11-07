# 📝 Adding a New Entity - Step-by-Step Guide

This guide shows you exactly how to add a new entity to the validation framework in **3 simple steps**.

---

## Example: Adding "Client" Entity

Let's walk through adding a `client` entity that validates client data before promoting to the master table.

---

## Step 1: Update Configuration (5 minutes)

### 1.1 Edit `config/validation_config.yaml`

Add your entity to the `entities` section:

```yaml
entities:
  # ... existing entities ...

  client:
    enabled: true
    description: "Client data validation and promotion pipeline"

    # Neon Source & Target
    source_table: "intake.client_raw_intake"
    target_table: "marketing.client_master"
    key_field: "unique_id"

    # Supabase Workspace
    workspace_table: "client_needs_enrichment"
    workspace_schema: "public"

    # Field Mapping (source → target)
    field_mapping:
      client_name: client_name
      industry: industry
      contact_email: contact_email
      contact_phone: contact_phone
      website: website
      unique_id: client_unique_id

    # Validation Rules
    rules:
      - field: client_name
        rule: not_null
        severity: critical
        error_message: "Client name is required"

      - field: client_name
        rule: min_length
        params: { length: 2 }
        severity: critical
        error_message: "Client name must be at least 2 characters"

      - field: contact_email
        rule: email_format
        severity: critical
        error_message: "Invalid email format"

      - field: contact_phone
        rule: phone_format
        severity: warning
        error_message: "Invalid phone format"

      - field: website
        rule: url_format
        severity: warning
        error_message: "Invalid URL format"

    # Promotion Settings
    promotion:
      require_all_critical: true
      allow_warnings: true
      update_existing: true
      conflict_resolution: "prefer_new"

    # Enrichment Settings
    enrichment:
      required_fields: ["contact_email", "website"]
      agents: ["clearbit", "apollo"]
      max_retry: 3
```

---

## Step 2: Create Supabase Tables (5 minutes)

### 2.1 Create SQL Migration

Create file: `sql/migrations/002_add_client_entity.sql`

```sql
-- ============================================================================
-- Add Client Entity to Validation Framework
-- ============================================================================

-- Create workspace table for client validation
CREATE TABLE IF NOT EXISTS public.client_needs_enrichment (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  payload JSONB NOT NULL,

  -- Validation Status
  validation_status TEXT DEFAULT 'PENDING' CHECK (
    validation_status IN ('PENDING', 'PASSED', 'FAILED', 'ENRICHING', 'PROMOTED')
  ),
  validation_errors JSONB,
  validation_warnings JSONB,
  last_validated_at TIMESTAMP,

  -- Enrichment Status
  enrichment_status TEXT,
  enrichment_agent TEXT,
  enrichment_attempts INTEGER DEFAULT 0,
  last_enrichment_at TIMESTAMP,

  -- Promotion Status
  promoted BOOLEAN DEFAULT false,
  promoted_at TIMESTAMP,
  promotion_error TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  processed_by TEXT
);

-- Create indexes
CREATE INDEX idx_client_enrichment_unique_id
  ON public.client_needs_enrichment(unique_id);

CREATE INDEX idx_client_enrichment_validation_status
  ON public.client_needs_enrichment(validation_status);

CREATE INDEX idx_client_enrichment_promoted
  ON public.client_needs_enrichment(promoted);

CREATE INDEX idx_client_enrichment_created_at
  ON public.client_needs_enrichment(created_at DESC);

-- Create auto-update trigger
CREATE TRIGGER update_client_enrichment_updated_at
  BEFORE UPDATE ON public.client_needs_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add to pending validations view
CREATE OR REPLACE VIEW public.vw_pending_validations AS
SELECT 'company' AS entity, unique_id, created_at
FROM public.company_needs_enrichment
WHERE validation_status = 'PENDING'
UNION ALL
SELECT 'person' AS entity, unique_id, created_at
FROM public.people_needs_enrichment
WHERE validation_status = 'PENDING'
UNION ALL
SELECT 'client' AS entity, unique_id, created_at
FROM public.client_needs_enrichment
WHERE validation_status = 'PENDING'
ORDER BY created_at ASC;

-- Add to failed validations view
CREATE OR REPLACE VIEW public.vw_failed_validations AS
SELECT 'company' AS entity, unique_id, validation_errors, created_at
FROM public.company_needs_enrichment
WHERE validation_status = 'FAILED'
UNION ALL
SELECT 'person' AS entity, unique_id, validation_errors, created_at
FROM public.people_needs_enrichment
WHERE validation_status = 'FAILED'
UNION ALL
SELECT 'client' AS entity, unique_id, validation_errors, created_at
FROM public.client_needs_enrichment
WHERE validation_status = 'FAILED'
ORDER BY created_at DESC;

-- Add to ready for promotion view
CREATE OR REPLACE VIEW public.vw_ready_for_promotion AS
SELECT 'company' AS entity, unique_id, payload, last_validated_at
FROM public.company_needs_enrichment
WHERE validation_status = 'PASSED' AND promoted = false
UNION ALL
SELECT 'person' AS entity, unique_id, payload, last_validated_at
FROM public.people_needs_enrichment
WHERE validation_status = 'PASSED' AND promoted = false
UNION ALL
SELECT 'client' AS entity, unique_id, payload, last_validated_at
FROM public.client_needs_enrichment
WHERE validation_status = 'PASSED' AND promoted = false
ORDER BY last_validated_at ASC;

COMMENT ON TABLE public.client_needs_enrichment IS 'Workspace for client data validation and enrichment';
```

### 2.2 Run Migration

```bash
psql $SUPABASE_DATABASE_URL -f sql/migrations/002_add_client_entity.sql
```

---

## Step 3: Run Validation (1 minute)

### 3.1 Test with Dry Run

```bash
python scripts/python/validator.py --entity client --dry-run
```

### 3.2 Run for Real

```bash
python scripts/python/validator.py --entity client --batch-size 100
```

### 3.3 Check Results

```sql
-- In Supabase
SELECT
  validation_status,
  COUNT(*) as count
FROM public.client_needs_enrichment
GROUP BY validation_status;
```

---

## ✅ You're Done!

That's it! Your new entity is fully integrated into the framework.

The validator will now:
- ✅ Fetch unprocessed records from `intake.client_raw_intake`
- ✅ Load them into `client_needs_enrichment` workspace
- ✅ Run all validation rules
- ✅ Promote PASSED records to `marketing.client_master`
- ✅ Flag FAILED records for enrichment
- ✅ Log everything to audit trail

---

## 🔄 Optional: Add to n8n Workflow

If using n8n automation:

1. Open your n8n workflow
2. Find the "Set Entity Config" node
3. Duplicate it and change to:

```json
{
  "entity": "client",
  "source_table": "intake.client_raw_intake",
  "target_table": "marketing.client_master",
  "workspace_table": "client_needs_enrichment",
  "batch_size": "100"
}
```

4. Connect to trigger for automation

---

## 📊 Monitoring Your New Entity

### View Validation Stats

```sql
SELECT * FROM validation_log
WHERE entity = 'client'
ORDER BY timestamp DESC
LIMIT 20;
```

### Check Pending Validations

```sql
SELECT * FROM vw_pending_validations
WHERE entity = 'client';
```

### Review Failures

```sql
SELECT
  unique_id,
  validation_errors,
  created_at
FROM client_needs_enrichment
WHERE validation_status = 'FAILED'
ORDER BY created_at DESC;
```

---

## 🎯 Quick Reference Checklist

When adding a new entity, ensure:

- [ ] Added to `validation_config.yaml`
- [ ] Specified source_table and target_table
- [ ] Defined validation rules
- [ ] Created workspace table in Supabase
- [ ] Added indexes to workspace table
- [ ] Updated helper views (pending, failed, ready)
- [ ] Tested with --dry-run
- [ ] Ran first batch successfully
- [ ] (Optional) Added to n8n workflow

---

## 💡 Pro Tips

### Tip 1: Start with Minimal Rules

Begin with just `not_null` rules, then add more as you understand your data:

```yaml
rules:
  - field: client_name
    rule: not_null
    severity: critical
```

Test, review failures, then add more sophisticated rules.

### Tip 2: Use Warnings First

Mark new rules as `warning` severity first:

```yaml
rules:
  - field: website
    rule: url_format
    severity: warning  # Start as warning
```

Once you're confident, change to `critical`.

### Tip 3: Copy from Similar Entity

If your new entity is similar to an existing one, copy its config and modify:

```bash
# Copy company config as template
cp config/entities/company.yaml config/entities/client.yaml
# Edit to match your needs
```

---

## 🐛 Common Issues

### Issue: "Entity not found in configuration"

**Cause**: YAML indentation wrong or entity name mismatch

**Fix**: Check `entities:` section, ensure proper indentation

### Issue: "Table does not exist"

**Cause**: Workspace table not created in Supabase

**Fix**: Run the SQL migration (Step 2)

### Issue: "No records fetched"

**Cause**: Source table empty or all records already processed

**Fix**: Check Neon source table:
```sql
SELECT COUNT(*) FROM intake.client_raw_intake
WHERE processed_at IS NULL;
```

---

## 📚 Additional Resources

- **Main README**: Framework overview
- **ARCHITECTURE.md**: How it all works
- **TROUBLESHOOTING.md**: Common problems

---

**Time to Complete**: ~10 minutes per entity
**Difficulty**: Easy (just config + SQL)
**Result**: Fully automated validation pipeline
