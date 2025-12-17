# n8n Workflow Quick Reference

## pull_from_enrichment_hub.json

Quick reference guide for the enrichment data promotion workflow.

### At a Glance

| Property | Value |
|----------|-------|
| **Workflow Name** | Pull from Enrichment Hub |
| **Purpose** | Promote validated enrichment data to production |
| **Schedule** | Daily at 2:00 AM |
| **Runtime** | ~2-5 minutes (depends on volume) |
| **Source** | Supabase (enrichment tables) |
| **Destination** | Neon (marketing tables) |

### Tables

**Source (Supabase):**
```
public.company_needs_enrichment  → WHERE validation_status='READY'
public.people_needs_enrichment   → WHERE validation_status='READY'
```

**Destination (Neon):**
```
marketing.company_master         ← Promoted companies
marketing.people_master          ← Promoted people
shq.validation_log               ← Audit trail
```

### Workflow Steps

```
1. Trigger (Schedule/Manual)
   ↓
2. Query READY records from Supabase
   ↓
3. Insert into Neon marketing tables
   ↓
4. Update status to PASSED in Supabase
   ↓
5. Cleanup old promoted records (7 days)
   ↓
6. Log to audit table
   ↓
7. Generate markdown summary
```

### Common Commands

**Execute Manually:**
```
1. Open n8n
2. Go to "Pull from Enrichment Hub" workflow
3. Click "Execute Workflow"
4. Select "Manual Trigger"
```

**Check Last Execution:**
```sql
-- In Neon
SELECT * FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
ORDER BY timestamp DESC LIMIT 1;
```

**View Records Ready for Promotion:**
```sql
-- In Supabase
SELECT
  'Companies' as type,
  COUNT(*) as ready_count
FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
UNION ALL
SELECT
  'People',
  COUNT(*)
FROM public.people_needs_enrichment
WHERE validation_status = 'READY';
```

**Check Promoted Records:**
```sql
-- In Neon
SELECT
  'Companies' as type,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE enrichment_source = 'enrichment_hub') as from_hub
FROM marketing.company_master
UNION ALL
SELECT
  'People',
  COUNT(*),
  COUNT(*) FILTER (WHERE enrichment_source = 'enrichment_hub')
FROM marketing.people_master;
```

### Quick Fixes

**No Records Processing?**
```sql
-- Mark records as READY for testing
UPDATE public.company_needs_enrichment
SET validation_status = 'READY'
WHERE validation_status = 'PENDING'
LIMIT 5;
```

**Workflow Failed?**
1. Check n8n execution log
2. Verify credentials are valid
3. Test database connections
4. Check for SQL errors in log

**Need to Rollback?**
```sql
-- In Neon (use with caution!)
-- Delete recently promoted records
DELETE FROM marketing.company_master
WHERE created_at > NOW() - INTERVAL '1 hour';

-- In Supabase
-- Reset status back to READY
UPDATE public.company_needs_enrichment
SET validation_status = 'READY',
    promoted_at = NULL,
    promoted_to_neon = FALSE
WHERE promoted_at > NOW() - INTERVAL '1 hour';
```

### Monitoring Queries

**Daily Promotion Stats:**
```sql
SELECT * FROM shq.enrichment_promotion_stats
WHERE promotion_date >= CURRENT_DATE - 7
ORDER BY promotion_date DESC;
```

**Enrichment Source Summary:**
```sql
SELECT * FROM marketing.company_enrichment_summary;
SELECT * FROM marketing.people_enrichment_summary;
```

**Check for Duplicates:**
```sql
SELECT * FROM marketing.check_duplicate_companies();
SELECT * FROM marketing.check_duplicate_people();
```

**Audit Trail:**
```sql
SELECT
  DATE(timestamp) as date,
  entity_type,
  SUM(record_count) as total,
  COUNT(*) as executions
FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), entity_type
ORDER BY date DESC;
```

### Credentials

**Required in n8n:**

1. **Supabase PostgreSQL**
   - Host: `db.YOUR_PROJECT.supabase.co`
   - Database: `postgres`
   - Port: `5432`
   - SSL: Required

2. **Neon PostgreSQL**
   - Connection String: `${DATABASE_URL}`
   - SSL: Required

### Environment Variables

Add to `.env`:
```bash
VITE_SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
SUPABASE_DB_PASSWORD="your-password"
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
```

### Cron Expression

Default: `0 2 * * *` (2:00 AM daily)

**Common schedules:**
- Every 6 hours: `0 */6 * * *`
- Twice daily: `0 2,14 * * *`
- Hourly: `0 * * * *`
- Weekly: `0 2 * * 0`

### Output Example

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

### Troubleshooting Checklist

- [ ] Are credentials configured correctly?
- [ ] Do tables exist in both databases?
- [ ] Are there READY records to process?
- [ ] Is the schedule active?
- [ ] Are database connections working?
- [ ] Check execution logs for errors
- [ ] Verify data in audit log

### Performance Metrics

**Expected:**
- Query time: <1 second per 100 records
- Insert time: <2 seconds per 100 records
- Total workflow: 2-5 minutes for typical volume

**Optimization needed if:**
- Total time >10 minutes
- Query time >10 seconds
- High error rate (>5%)

### Links

- **Full Documentation:** [README.md](./README.md)
- **Setup Guide:** [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **Migrations:** [../ctb/data/migrations/](../ctb/data/migrations/)
- **CTB System:** [../CTB_README.md](../CTB_README.md)

### Support

**Quick Help:**
1. Check execution log in n8n
2. Review SQL in workflow nodes
3. Test credentials in n8n
4. Check database connectivity

**Detailed Help:**
- See [README.md](./README.md) for comprehensive documentation
- See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for setup instructions
- Check [../ctb/docs/](../ctb/docs/) for CTB documentation

---

**Version:** 1.0.0
**Project:** Enricha Vision (4.svg.marketing.enricha-vision)
