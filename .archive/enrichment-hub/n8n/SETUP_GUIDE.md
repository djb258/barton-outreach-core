# n8n Workflow Setup Guide

Complete step-by-step guide for setting up the Enrichment Hub data promotion workflow.

## Prerequisites

- ✅ n8n instance running (cloud or self-hosted)
- ✅ Supabase project with enrichment tables
- ✅ Neon PostgreSQL database
- ✅ Database credentials available
- ✅ Required tables created (see Database Setup below)

## Quick Start

### 1. Database Setup

Before importing the workflow, ensure all required tables exist.

**Run these migrations:**

```bash
# Navigate to migrations directory
cd ctb/data/migrations/

# Apply Supabase migrations
psql $SUPABASE_CONNECTION_STRING -f supabase_enrichment_tables.sql

# Apply Neon migrations
psql $DATABASE_URL -f neon_marketing_tables.sql
```

See [Database Setup](#database-setup) section for detailed SQL.

### 2. Import Workflow to n8n

**Option A: Via n8n UI**

1. Open n8n web interface
2. Click **Workflows** in sidebar
3. Click **Import from File** button
4. Select `pull_from_enrichment_hub.json`
5. Click **Import**

**Option B: Via n8n CLI**

```bash
# If using n8n CLI
n8n import:workflow --input=./n8n/pull_from_enrichment_hub.json
```

### 3. Configure Credentials

#### Supabase PostgreSQL Credentials

1. In n8n, go to **Credentials** → **New**
2. Search for "Postgres"
3. Configure:

```yaml
Name: Supabase PostgreSQL
Host: db.YOUR_PROJECT.supabase.co
Port: 5432
Database: postgres
Schema: public
User: postgres
Password: YOUR_SUPABASE_DB_PASSWORD
SSL Mode: require
```

4. Click **Create**
5. **Copy the credential ID** (shown in URL or list)

#### Neon PostgreSQL Credentials

1. In n8n, go to **Credentials** → **New**
2. Search for "Postgres"
3. Configure:

```yaml
Name: Neon PostgreSQL
Connection String: YOUR_NEON_DATABASE_URL
SSL Mode: require
```

4. Click **Create**
5. **Copy the credential ID**

### 4. Update Workflow with Credential IDs

**Open the workflow in n8n:**

1. Click on each PostgreSQL node
2. Update credentials dropdown
3. Select appropriate credential (Supabase or Neon)

**Or edit JSON before import:**

Replace these placeholders:
```json
"{{SUPABASE_CREDENTIALS_ID}}" → "actual-supabase-cred-id"
"{{NEON_CREDENTIALS_ID}}" → "actual-neon-cred-id"
```

### 5. Test the Workflow

**Initial Test:**

1. Click **Execute Workflow** button
2. Select **Manual Trigger**
3. Watch execution progress
4. Review execution summary

**Verify Results:**

```sql
-- Check Neon tables
SELECT COUNT(*) FROM marketing.company_master;
SELECT COUNT(*) FROM marketing.people_master;

-- Check audit log
SELECT * FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
ORDER BY timestamp DESC LIMIT 1;
```

### 6. Activate Scheduled Execution

1. Toggle **Active** switch to ON
2. Workflow will run daily at 2:00 AM
3. Monitor in **Executions** tab

## Database Setup

### Supabase Tables

**Create enrichment tables in Supabase:**

```sql
-- Company enrichment table
CREATE TABLE IF NOT EXISTS public.company_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_name VARCHAR(255) NOT NULL,
  domain VARCHAR(255),
  industry VARCHAR(100),
  employee_count INTEGER,
  revenue DECIMAL(15,2),
  location VARCHAR(255),
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status VARCHAR(50) DEFAULT 'PENDING',
  enriched_at TIMESTAMP DEFAULT NOW(),
  enriched_by VARCHAR(100),
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- People enrichment table
CREATE TABLE IF NOT EXISTS public.people_needs_enrichment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(50),
  title VARCHAR(255),
  company_id UUID,
  company_name VARCHAR(255),
  linkedin_url TEXT,
  enrichment_data JSONB,
  validation_status VARCHAR(50) DEFAULT 'PENDING',
  enriched_at TIMESTAMP DEFAULT NOW(),
  enriched_by VARCHAR(100),
  promoted_at TIMESTAMP,
  promoted_to_neon BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_validation_status
  ON public.company_needs_enrichment(validation_status, enriched_at);

CREATE INDEX IF NOT EXISTS idx_people_validation_status
  ON public.people_needs_enrichment(validation_status, enriched_at);

CREATE INDEX IF NOT EXISTS idx_company_promoted
  ON public.company_needs_enrichment(promoted_at)
  WHERE promoted_to_neon = TRUE;

CREATE INDEX IF NOT EXISTS idx_people_promoted
  ON public.people_needs_enrichment(promoted_at)
  WHERE promoted_to_neon = TRUE;
```

### Neon Tables

**Create marketing tables in Neon:**

```sql
-- Create marketing schema
CREATE SCHEMA IF NOT EXISTS marketing;
CREATE SCHEMA IF NOT EXISTS shq;

-- Company master table
CREATE TABLE IF NOT EXISTS marketing.company_master (
  id SERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  domain VARCHAR(255) UNIQUE,
  industry VARCHAR(100),
  employee_count INTEGER,
  revenue DECIMAL(15,2),
  location VARCHAR(255),
  linkedin_url TEXT,
  enrichment_source VARCHAR(50) DEFAULT 'enrichment_hub',
  enriched_at TIMESTAMP,
  validation_status VARCHAR(50) DEFAULT 'PASSED',
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- People master table
CREATE TABLE IF NOT EXISTS marketing.people_master (
  id SERIAL PRIMARY KEY,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(50),
  title VARCHAR(255),
  company_id INTEGER REFERENCES marketing.company_master(id),
  company_name VARCHAR(255),
  linkedin_url TEXT,
  enrichment_source VARCHAR(50) DEFAULT 'enrichment_hub',
  enriched_at TIMESTAMP,
  validation_status VARCHAR(50) DEFAULT 'PASSED',
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Validation log table
CREATE TABLE IF NOT EXISTS shq.validation_log (
  id SERIAL PRIMARY KEY,
  workflow_name VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  action VARCHAR(50) NOT NULL,
  record_count INTEGER DEFAULT 0,
  status VARCHAR(50) NOT NULL,
  timestamp TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_company_master_domain
  ON marketing.company_master(domain);

CREATE INDEX IF NOT EXISTS idx_people_master_email
  ON marketing.people_master(email);

CREATE INDEX IF NOT EXISTS idx_people_master_company
  ON marketing.people_master(company_id);

CREATE INDEX IF NOT EXISTS idx_validation_log_workflow
  ON shq.validation_log(workflow_name, timestamp DESC);
```

### Migration Files

Save these as migration files:

**File: `ctb/data/migrations/20251107_create_supabase_enrichment_tables.sql`**
```sql
-- Supabase enrichment tables (see SQL above)
```

**File: `ctb/data/migrations/20251107_create_neon_marketing_tables.sql`**
```sql
-- Neon marketing tables (see SQL above)
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Supabase
VITE_SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
VITE_SUPABASE_PUBLISHABLE_KEY="your-anon-key"
SUPABASE_DB_PASSWORD="your-db-password"

# Neon
DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# n8n (if self-hosted)
N8N_BASIC_AUTH_USER="admin"
N8N_BASIC_AUTH_PASSWORD="your-password"
N8N_ENCRYPTION_KEY="your-encryption-key"
```

### Workflow Settings

**Schedule Configuration:**

Default: Daily at 2:00 AM

To change:
1. Open workflow in n8n
2. Click "Schedule Trigger" node
3. Modify cron expression:
   - Every 6 hours: `0 */6 * * *`
   - Twice daily: `0 2,14 * * *`
   - Weekly: `0 2 * * 0`

**Retention Configuration:**

Default: 7 days for promoted records

To change:
1. Open "Cleanup Old Companies" node
2. Modify interval:
   ```sql
   INTERVAL '30 days'  -- Change to 30 days
   ```

## Testing

### Test with Sample Data

**Insert test records:**

```sql
-- Supabase: Create test companies
INSERT INTO public.company_needs_enrichment
  (company_name, domain, industry, validation_status)
VALUES
  ('Test Company 1', 'test1.com', 'Technology', 'READY'),
  ('Test Company 2', 'test2.com', 'Healthcare', 'READY');

-- Supabase: Create test people
INSERT INTO public.people_needs_enrichment
  (first_name, last_name, email, validation_status)
VALUES
  ('John', 'Doe', 'john@test1.com', 'READY'),
  ('Jane', 'Smith', 'jane@test2.com', 'READY');
```

**Run workflow:**
1. Execute via Manual Trigger
2. Check execution log
3. Verify records in Neon

**Cleanup test data:**
```sql
-- Neon
DELETE FROM marketing.people_master WHERE email LIKE '%@test%.com';
DELETE FROM marketing.company_master WHERE domain LIKE 'test%.com';

-- Supabase
DELETE FROM public.company_needs_enrichment WHERE domain LIKE 'test%.com';
DELETE FROM public.people_needs_enrichment WHERE email LIKE '%@test%.com';
```

### Validation Queries

**Check record counts:**

```sql
-- Supabase ready records
SELECT
  'Companies READY' as type,
  COUNT(*) as count
FROM public.company_needs_enrichment
WHERE validation_status = 'READY'
UNION ALL
SELECT
  'People READY',
  COUNT(*)
FROM public.people_needs_enrichment
WHERE validation_status = 'READY';

-- Neon promoted records
SELECT
  'Companies in Neon' as type,
  COUNT(*) as count
FROM marketing.company_master
WHERE enrichment_source = 'enrichment_hub'
UNION ALL
SELECT
  'People in Neon',
  COUNT(*)
FROM marketing.people_master
WHERE enrichment_source = 'enrichment_hub';
```

**Check audit log:**

```sql
SELECT
  workflow_name,
  entity_type,
  action,
  record_count,
  status,
  timestamp
FROM shq.validation_log
ORDER BY timestamp DESC
LIMIT 10;
```

## Monitoring

### n8n Dashboard

Monitor in n8n:
1. **Executions** tab - View all workflow runs
2. **Activity Log** - Detailed execution logs
3. **Error Workflow** - Configure error handling

### Database Monitoring

**Create monitoring view:**

```sql
-- Neon: Create monitoring view
CREATE OR REPLACE VIEW shq.enrichment_promotion_stats AS
SELECT
  DATE(timestamp) as promotion_date,
  entity_type,
  SUM(record_count) as total_promoted,
  COUNT(*) as execution_count
FROM shq.validation_log
WHERE workflow_name = 'Pull from Enrichment Hub'
GROUP BY DATE(timestamp), entity_type
ORDER BY promotion_date DESC;

-- Query daily stats
SELECT * FROM shq.enrichment_promotion_stats
WHERE promotion_date >= CURRENT_DATE - INTERVAL '7 days';
```

### Alerts

**Set up n8n error workflow:**

1. Create new workflow: "Enrichment Promotion Errors"
2. Add "Error Trigger" node
3. Add notification node (email/Slack)
4. Configure to trigger on errors in main workflow

## Troubleshooting

### Common Issues

**1. Credential Errors**

```
Error: Invalid credentials
```

**Solution:**
- Verify credential IDs in workflow nodes
- Test credentials in n8n Credentials page
- Check connection strings in .env
- Verify database is accessible

**2. No Records Found**

```
No records to process
```

**Solution:**
```sql
-- Check if records exist with READY status
SELECT COUNT(*) FROM public.company_needs_enrichment
WHERE validation_status = 'READY';

-- Update records to READY for testing
UPDATE public.company_needs_enrichment
SET validation_status = 'READY'
WHERE id IN (SELECT id LIMIT 5);
```

**3. SQL Errors**

```
ERROR: column "xyz" does not exist
```

**Solution:**
- Verify table schemas match workflow
- Run migration scripts
- Check for column name typos

**4. Connection Timeouts**

```
Error: Connection timeout
```

**Solution:**
- Check network connectivity
- Verify SSL settings
- Increase timeout in n8n settings
- Check firewall rules

### Debug Mode

**Enable verbose logging:**

1. In n8n settings, enable debug mode
2. Check n8n logs:
   ```bash
   # Docker
   docker logs n8n

   # PM2
   pm2 logs n8n

   # npm
   npm run start --log-level debug
   ```

### Testing Individual Nodes

Test each node separately:

1. Select node
2. Click "Execute Node"
3. Review output
4. Fix issues before testing full workflow

## Production Deployment

### Pre-Production Checklist

- [ ] All database tables created
- [ ] Credentials configured and tested
- [ ] Workflow imported successfully
- [ ] Manual test execution passed
- [ ] Monitoring and alerts configured
- [ ] Error handling verified
- [ ] Performance tested with production data volume
- [ ] Documentation reviewed
- [ ] Team trained on workflow

### Go-Live Steps

1. **Final Testing:**
   ```bash
   # Run with production-like data volume
   # Verify timing and performance
   # Check resource usage
   ```

2. **Activate Workflow:**
   - Toggle Active switch
   - Verify schedule is correct
   - Monitor first scheduled execution

3. **Post-Launch Monitoring:**
   - Check first 3 executions
   - Review audit logs
   - Verify data quality
   - Monitor for errors

### Rollback Plan

If issues occur:

1. **Disable workflow** (toggle Active OFF)
2. **Identify issue** in execution logs
3. **Fix workflow** or data issue
4. **Test fix** via manual execution
5. **Re-enable workflow**

## Maintenance

### Regular Tasks

**Weekly:**
- Review execution logs
- Check error rates
- Verify data quality
- Monitor performance

**Monthly:**
- Review and optimize queries
- Check database indexes
- Update credentials if needed
- Review retention policies

**Quarterly:**
- Performance tuning
- Workflow optimization
- Documentation updates
- Team training refresher

## Support

### Getting Help

1. Check n8n execution logs
2. Review this setup guide
3. Check CTB documentation
4. Open issue on GitHub
5. Contact project maintainers

### Resources

- **n8n Docs:** https://docs.n8n.io
- **CTB System:** ../../CTB_README.md
- **Workflow README:** ./README.md
- **Database Migrations:** ../../ctb/data/migrations/

---

**Version:** 1.0.0
**Last Updated:** 2025-11-07
**Project:** Enricha Vision (4.svg.marketing.enricha-vision)
