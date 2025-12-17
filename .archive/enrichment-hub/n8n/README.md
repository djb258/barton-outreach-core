# n8n Workflows

This directory contains n8n workflow definitions for the Enricha Vision project.

## Workflows

### pull_from_enrichment_hub.json

**Purpose:** Automatically promote cleaned and validated records from Supabase enrichment tables to Neon production tables.

**Schedule:** Daily at 2:00 AM (configurable)

**Direction:** Supabase (Enrichment Hub) → Neon (Production)

**Flow:**
1. Query READY records from Supabase enrichment tables
2. Insert records into Neon marketing tables
3. Update validation status to PASSED
4. Cleanup old promoted records (7-day retention)
5. Log promotion to audit table
6. Generate summary report

**Tables Involved:**

**Source (Supabase):**
- `public.company_needs_enrichment`
- `public.people_needs_enrichment`

**Destination (Neon):**
- `marketing.company_master`
- `marketing.people_master`

**Audit:**
- `shq.validation_log`

---

### pull_from_external_source.json

**Purpose:** Universal enrichment receiver that pulls failed or pending validation records from any external Neon/Postgres database into Enrichment Hub Supabase workspace for review and repair.

**Schedule:** Every 30 minutes (configurable)

**Direction:** External Neon/Postgres → Supabase (Enrichment Hub)

**Flow:**
1. Query failed/pending records from external source database
2. Transform and add metadata (batch_id, source_repo, timestamps)
3. Insert into Enrichment Hub Supabase tables
4. Log to audit trail
5. Optionally mark source records as promoted
6. Generate summary report

**Tables Involved:**

**Source (External Neon/Postgres):**
- Configurable via `/config/source_bridge.env`
- Default: `company_invalid`, `people_invalid`
- Filtered by: `WHERE promoted_to IS NULL` (configurable)

**Destination (Supabase - Enrichment Hub):**
- `public.company_needs_enrichment`
- `public.people_needs_enrichment`

**Audit:**
- `shq.audit_log` (in Neon)

**Documentation:**
- Full Setup Guide: [`EXTERNAL_SOURCE_GUIDE.md`](./EXTERNAL_SOURCE_GUIDE.md)
- Configuration Templates: [`/config/source_bridge.env`](../config/source_bridge.env), [`/config/enrichment_bridge.env`](../config/enrichment_bridge.env)

---

## Data Flow Architecture

The two workflows work together to create a complete data enrichment pipeline:

```
External DB (Failed Records)
         ↓
  [pull_from_external_source]
         ↓
Enrichment Hub (Supabase)
    → Manual Review
    → Data Enrichment
    → Quality Validation
         ↓
  [pull_from_enrichment_hub]
         ↓
Production DB (Neon Marketing)
```

**Use Cases:**
1. **Import Failed Records:** Pull failed validations from production → Enrichment Hub
2. **Enrich & Fix:** Manual or automated data enrichment in Supabase
3. **Promote Clean Data:** Push validated records → Production

---

## Setup Instructions

### 1. Import Workflow

**In n8n:**
1. Go to Workflows
2. Click "Import from File"
3. Select `pull_from_enrichment_hub.json`
4. Click "Import"

### 2. Configure Credentials

You need to set up two PostgreSQL connections:

**Supabase Connection:**
1. Go to Credentials → Add Credential → Postgres
2. Name: "Supabase PostgreSQL"
3. Configure:
   ```
   Host: ${VITE_SUPABASE_URL} (from .env)
   Database: postgres
   User: postgres
   Password: ${SUPABASE_DB_PASSWORD}
   Port: 5432
   SSL: Required
   ```
4. Save and note the credential ID
5. Replace `{{SUPABASE_CREDENTIALS_ID}}` in workflow

**Neon Connection:**
1. Go to Credentials → Add Credential → Postgres
2. Name: "Neon PostgreSQL"
3. Configure:
   ```
   Connection String: ${DATABASE_URL} (from .env)
   SSL: Required
   ```
4. Save and note the credential ID
5. Replace `{{NEON_CREDENTIALS_ID}}` in workflow

### 3. Update Credential IDs

In the workflow JSON, replace placeholders:

```json
"credentials": {
  "postgres": {
    "id": "{{SUPABASE_CREDENTIALS_ID}}",  // Replace with actual ID
    "name": "Supabase PostgreSQL"
  }
}
```

### 4. Test Workflow

**Manual Test:**
1. Click "Execute Workflow"
2. Choose "Manual Trigger"
3. Verify execution completes successfully
4. Check summary output

**Verify Data:**
```sql
-- Check Neon tables
SELECT COUNT(*) FROM marketing.company_master;
SELECT COUNT(*) FROM marketing.people_master;

-- Check audit log
SELECT * FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
ORDER BY timestamp DESC
LIMIT 10;

-- Check Supabase status
SELECT validation_status, COUNT(*)
FROM public.company_needs_enrichment
GROUP BY validation_status;
```

### 5. Activate Workflow

1. Toggle "Active" switch in n8n
2. Workflow will run daily at 2:00 AM
3. Monitor executions in n8n dashboard

## Workflow Details

### Node 1: Schedule Trigger

**Type:** Schedule Trigger
**Cron:** `0 2 * * *` (2:00 AM daily)
**Purpose:** Automatic daily execution

### Node 2: Manual Trigger

**Type:** Manual Trigger
**Purpose:** Testing and on-demand execution

### Node 3-4: Query Ready Records

**Type:** PostgreSQL Query
**Connection:** Supabase

**Companies Query:**
```sql
SELECT
  id, company_name, domain, industry,
  employee_count, revenue, location, linkedin_url,
  enrichment_data, validation_status,
  enriched_at, enriched_by
FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
ORDER BY enriched_at ASC;
```

**People Query:**
```sql
SELECT
  id, first_name, last_name, email, phone, title,
  company_id, company_name, linkedin_url,
  enrichment_data, validation_status,
  enriched_at, enriched_by
FROM public.people_needs_enrichment
WHERE validation_status = 'READY'
ORDER BY enriched_at ASC;
```

### Node 5-6: Insert to Neon

**Type:** PostgreSQL Insert
**Connection:** Neon
**Tables:**
- `marketing.company_master`
- `marketing.people_master`

**Batching:** Independent (processes records individually)

### Node 7-8: Update Status

**Type:** PostgreSQL Update
**Connection:** Supabase

Updates records to:
- `validation_status = 'PASSED'`
- `promoted_at = NOW()`
- `promoted_to_neon = TRUE`

### Node 9-10: Cleanup Old Records

**Type:** PostgreSQL Delete
**Connection:** Supabase

Deletes records:
- `validation_status = 'PASSED'`
- `promoted_at < NOW() - INTERVAL '7 days'`

**Retention:** 7 days for audit trail

### Node 11-12: Audit Logging

**Type:** PostgreSQL Insert
**Connection:** Neon
**Table:** `shq.validation_log`

**Logged Data:**
- Workflow name
- Entity type (company/people)
- Action (promotion)
- Record count
- Status
- Timestamp
- Metadata (JSON)

### Node 13: Generate Summary

**Type:** Code (JavaScript)
**Purpose:** Aggregate results and create markdown report

**Output:**
```markdown
# Enrichment Hub → Neon Promotion Summary

**Workflow:** Pull from Enrichment Hub
**Timestamp:** 2025-11-07T02:00:00Z
**Status:** ✅ Completed

## Records Promoted

| Entity Type | Records Promoted | Status |
|-------------|------------------|--------|
| Companies   | 145              | ✅ Success |
| People      | 523              | ✅ Success |
| **TOTAL**   | **668**          | ✅ Success |
```

### Node 14: Output Summary

**Type:** Respond to Webhook
**Purpose:** Display final summary in execution log

## Monitoring

### Execution History

View in n8n:
1. Go to Executions
2. Filter by workflow name
3. Review success/failure status
4. Check execution time

### Logs

**Audit Logs:**
```sql
SELECT
  workflow_name,
  entity_type,
  record_count,
  status,
  timestamp,
  metadata
FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
ORDER BY timestamp DESC;
```

**Failed Records:**
```sql
-- Records that failed to promote
SELECT * FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
  AND enriched_at < NOW() - INTERVAL '1 day';
```

### Alerts

Set up alerts in n8n for:
- ❌ Workflow execution failures
- ⚠️ Zero records processed
- ⚠️ High error rate
- 📊 Daily summary reports

## Troubleshooting

### No Records Processed

**Check:**
1. Are there READY records in Supabase?
   ```sql
   SELECT COUNT(*) FROM public.company_needs_enrichment
   WHERE validation_status = 'READY';
   ```
2. Are credentials valid?
3. Is Supabase accessible?

### Execution Failures

**Common Issues:**

1. **Credential Errors:**
   - Verify credential IDs in workflow
   - Test connections in Credentials page
   - Check .env file for correct values

2. **SQL Errors:**
   - Check table schemas match
   - Verify column names
   - Check data types compatibility

3. **Network Issues:**
   - Verify Supabase URL
   - Check Neon connection string
   - Verify SSL requirements

### Data Validation Errors

If records fail to insert:

1. Check data format in enrichment tables
2. Verify required fields are populated
3. Check for NULL values in NOT NULL columns
4. Verify foreign key constraints

**Debug Query:**
```sql
-- Find problematic records
SELECT * FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
  AND (company_name IS NULL OR domain IS NULL);
```

## Customization

### Change Schedule

Edit the Schedule Trigger node:

```json
"cronExpression": "0 2 * * *"  // 2 AM daily
```

**Common schedules:**
- Every 6 hours: `0 */6 * * *`
- Every hour: `0 * * * *`
- Twice daily: `0 2,14 * * *` (2 AM and 2 PM)
- Weekly: `0 2 * * 0` (Sunday 2 AM)

### Change Retention Period

Edit Cleanup nodes:

```sql
-- Change from 7 days to 30 days
WHERE promoted_at < NOW() - INTERVAL '30 days'
```

### Add Email Notifications

Add a node after "Generate Summary":

1. Add "Gmail" or "SMTP" node
2. Connect to Generate Summary
3. Configure email with summary content
4. Send to stakeholders

### Add Slack Notifications

Add a node for Slack alerts:

1. Add "Slack" node
2. Configure webhook URL
3. Send summary as message
4. Tag relevant team members

## Performance Optimization

### Batch Processing

For large volumes (>1000 records):

1. Add pagination to queries:
   ```sql
   LIMIT 1000 OFFSET 0
   ```

2. Use loop nodes to process in batches

3. Add delay between batches to avoid rate limits

### Parallel Processing

For better performance:

1. Use "Split In Batches" node
2. Process companies and people in parallel
3. Merge results at the end

### Indexing

Ensure indexes exist:

```sql
-- Supabase indexes
CREATE INDEX IF NOT EXISTS idx_company_validation
ON public.company_needs_enrichment(validation_status, enriched_at);

CREATE INDEX IF NOT EXISTS idx_people_validation
ON public.people_needs_enrichment(validation_status, enriched_at);

-- Neon indexes
CREATE INDEX IF NOT EXISTS idx_company_master_domain
ON marketing.company_master(domain);

CREATE INDEX IF NOT EXISTS idx_people_master_email
ON marketing.people_master(email);
```

## Security Considerations

### Credentials

- ✅ Use n8n credential management
- ✅ Never hardcode credentials in workflow
- ✅ Use environment variables
- ✅ Rotate credentials regularly

### Data Privacy

- ⚠️ PII data is being transferred
- ✅ Use SSL/TLS for all connections
- ✅ Ensure compliance with data regulations
- ✅ Audit log all data movements

### Access Control

- ✅ Limit workflow edit permissions
- ✅ Review execution logs regularly
- ✅ Monitor for unauthorized executions

## Integration with CTB System

This workflow integrates with the CTB system:

**CTB Branch:** `ctb/data/`
**Related Configs:**
- `ctb/sys/neon/neon.config.json`
- `ctb/sys/firebase/firebase.json` (for Supabase)

**Audit Trail:**
- All operations logged to `shq.validation_log`
- Complies with CTB compliance requirements
- Maintains data lineage

## Related Workflows

**Active Workflows:**

1. ✅ `pull_from_enrichment_hub.json` - Promote validated records (Supabase → Neon)
2. ✅ `pull_from_external_source.json` - Import failed records (External → Supabase)

**Future workflows to add:**

1. `validate_enrichment_quality.json` - Automated data quality checks
2. `rollback_failed_promotions.json` - Rollback mechanism for failed promotions
3. `scheduled_enrichment_requests.json` - Auto-request enrichment from providers
4. `data_quality_report.json` - Generate quality metrics and reports

## Support

**Issues:**
- Check n8n execution logs
- Review audit logs in `shq.validation_log`
- Verify credentials and connections
- Check CTB documentation

**Documentation:**
- n8n Docs: https://docs.n8n.io
- CTB System: `../../CTB_README.md`
- Database Schemas: `../../ctb/data/migrations/`

---

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Project:** Enricha Vision (4.svg.marketing.enricha-vision)
