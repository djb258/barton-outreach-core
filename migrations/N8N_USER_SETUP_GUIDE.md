# N8N Database User Setup Guide

**Date Created:** 2025-10-24
**Database:** Marketing DB (Neon)
**User:** n8n_user
**Purpose:** Limited-permission role for n8n automation workflows

---

## Summary

A secure, limited-permission PostgreSQL role has been created for n8n with minimal required access to the Marketing DB.

**Security Principles:**
- ✅ No superuser or owner privileges
- ✅ No DROP, ALTER, TRUNCATE, or DELETE privileges
- ✅ Read/Write access only to core operational tables
- ✅ Cannot modify schema structure
- ✅ Cannot access archive schema
- ✅ Secure password generated automatically

---

## Permissions Granted

### Database Level
```sql
GRANT CONNECT ON DATABASE "Marketing DB" TO n8n_user;
```

### Schema Level
```sql
GRANT USAGE ON SCHEMA intake TO n8n_user;
GRANT USAGE ON SCHEMA marketing TO n8n_user;
GRANT USAGE ON SCHEMA public TO n8n_user;
```

### Table Permissions

| Schema | Table | Permissions | Rationale |
|--------|-------|-------------|-----------|
| intake | company_raw_intake | SELECT, INSERT, UPDATE | Import workflows need to add/update raw data |
| marketing | company_master | SELECT, INSERT, UPDATE | Core company data management |
| marketing | company_slots | SELECT, INSERT | Slot creation for new companies |
| marketing | people_master | SELECT, INSERT, UPDATE | Executive enrichment workflows |
| public | shq_validation_log | SELECT, INSERT | Validation audit logging |

### Sequence Permissions
```sql
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO n8n_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO n8n_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_user;
```
*Required for INSERT operations with auto-increment IDs*

---

## Connection Details

**Location:** `migrations/N8N_CREDENTIALS.txt` (NOT in git)

**Format:**
```env
N8N_DB_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
N8N_DB_NAME=Marketing%20DB
N8N_DB_USER=n8n_user
N8N_DB_PASSWORD=<generated-secure-password>
N8N_DB_SSL=true
```

**Connection String:**
```
postgresql://n8n_user:<password>@<host>/Marketing%20DB?sslmode=require
```

---

## Setup Verification

### Test Connection
```javascript
const { Client } = require('pg');

const client = new Client({
  connectionString: process.env.DATABASE_URL
});

await client.connect();
const result = await client.query('SELECT current_user, current_database()');
console.log(result.rows[0]);
// Expected: { current_user: 'n8n_user', current_database: 'Marketing DB' }
```

### Test Permissions
```sql
-- Should succeed:
SELECT * FROM intake.company_raw_intake LIMIT 1;
INSERT INTO intake.company_raw_intake (company, website, ...) VALUES (...);
UPDATE marketing.company_master SET data_quality_score = 85 WHERE company_unique_id = '...';

-- Should fail (no permission):
DROP TABLE intake.company_raw_intake;  -- ❌ Permission denied
ALTER TABLE marketing.company_master ADD COLUMN test TEXT;  -- ❌ Permission denied
DELETE FROM marketing.company_master WHERE ...;  -- ❌ Permission denied
```

---

## Security Best Practices

### 1. Credential Management

✅ **DO:**
- Store credentials in environment variables
- Use `.env` files (add to `.gitignore`)
- Rotate passwords regularly
- Use connection pooling

❌ **DON'T:**
- Hardcode credentials in code
- Commit credentials to git
- Share credentials via chat/email
- Use the same password across environments

### 2. Connection Security

```javascript
// Good: Use SSL
const client = new Client({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: true
  }
});

// Bad: Disable SSL
const client = new Client({
  connectionString: process.env.DATABASE_URL,
  ssl: false  // ❌ Never do this
});
```

### 3. Query Safety

```javascript
// Good: Parameterized queries
await client.query(
  'INSERT INTO intake.company_raw_intake (company, website) VALUES ($1, $2)',
  [companyName, websiteUrl]
);

// Bad: String concatenation (SQL injection risk)
await client.query(
  `INSERT INTO intake.company_raw_intake (company) VALUES ('${companyName}')`  // ❌
);
```

---

## Usage Examples

### n8n Postgres Node Configuration

**Host:** `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
**Port:** `5432`
**Database:** `Marketing DB`
**User:** `n8n_user`
**Password:** *[from N8N_CREDENTIALS.txt]*
**SSL:** `require`

### Common Workflows

#### 1. Import Companies
```sql
INSERT INTO intake.company_raw_intake (
  company,
  website,
  industry,
  company_state,
  import_batch_id,
  state_abbrev
) VALUES (
  $1, $2, $3, $4, $5, $6
)
RETURNING id;
```

#### 2. Update Data Quality Score
```sql
UPDATE marketing.company_master
SET
  data_quality_score = (
    CASE WHEN website_url IS NOT NULL AND website_url != 'https://example.com' THEN 30 ELSE 0 END +
    CASE WHEN linkedin_url IS NOT NULL THEN 30 ELSE 0 END +
    CASE WHEN company_phone IS NOT NULL THEN 20 ELSE 0 END +
    CASE WHEN industry IS NOT NULL THEN 20 ELSE 0 END
  ),
  updated_at = NOW()
WHERE company_unique_id = $1;
```

#### 3. Create Company Slot
```sql
INSERT INTO marketing.company_slots (
  company_slot_unique_id,
  company_unique_id,
  slot_type,
  slot_label
) VALUES (
  $1, $2, 'default', 'Primary Slot'
);
```

#### 4. Log Validation Run
```sql
INSERT INTO public.shq_validation_log (
  validation_run_id,
  source_table,
  target_table,
  total_records,
  passed_records,
  failed_records,
  executed_by,
  notes
) VALUES (
  $1, $2, $3, $4, $5, $6, 'n8n-workflow', $7
);
```

---

## Limitations

### Cannot Do (By Design)

❌ **Schema Modifications:**
```sql
ALTER TABLE ...       -- Permission denied
CREATE TABLE ...      -- Permission denied
DROP TABLE ...        -- Permission denied
```

❌ **Data Deletion:**
```sql
DELETE FROM ...       -- Permission denied
TRUNCATE ...          -- Permission denied
```

❌ **Archive Access:**
```sql
SELECT * FROM archive.archived_table  -- Permission denied (no USAGE on archive schema)
```

❌ **Function Creation:**
```sql
CREATE FUNCTION ...   -- Permission denied
```

### Can Do

✅ **Read Core Tables:**
```sql
SELECT * FROM intake.company_raw_intake;
SELECT * FROM marketing.company_master;
SELECT * FROM marketing.people_master;
```

✅ **Insert New Records:**
```sql
INSERT INTO intake.company_raw_intake (...) VALUES (...);
INSERT INTO marketing.people_master (...) VALUES (...);
```

✅ **Update Existing Records:**
```sql
UPDATE marketing.company_master SET data_quality_score = 95 WHERE ...;
UPDATE intake.company_raw_intake SET validated = TRUE WHERE ...;
```

---

## Troubleshooting

### Permission Denied Errors

**Error:** `permission denied for table X`

**Solution:** Check if table is in allowed list. n8n_user only has access to core tables, not archive or system tables.

```sql
-- Check granted permissions
SELECT
  table_schema,
  table_name,
  STRING_AGG(privilege_type, ', ') as privileges
FROM information_schema.table_privileges
WHERE grantee = 'n8n_user'
GROUP BY table_schema, table_name;
```

### Connection Timeouts

**Error:** `connection timeout`

**Solution:**
1. Check network connectivity to Neon
2. Verify SSL is enabled
3. Check connection pooling settings
4. Ensure Neon project is not suspended

### Insert Failures

**Error:** `permission denied for sequence X`

**Solution:** Sequences should already have USAGE permission. If not:
```sql
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO n8n_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO n8n_user;
```

---

## Password Rotation

### When to Rotate
- Every 90 days (recommended)
- Immediately if compromised
- When team member leaves
- After security audit

### How to Rotate

1. **Generate new password:**
   ```sql
   ALTER ROLE n8n_user WITH PASSWORD 'new_secure_password_here';
   ```

2. **Update environment variables:**
   ```env
   N8N_DB_PASSWORD=new_secure_password_here
   ```

3. **Restart n8n workflows:**
   - Test connection
   - Verify workflows still function
   - Monitor for errors

---

## Monitoring

### Check Active Connections
```sql
SELECT
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  state_change
FROM pg_stat_activity
WHERE usename = 'n8n_user'
ORDER BY query_start DESC;
```

### Check Query Activity
```sql
SELECT
  rolname,
  calls,
  total_exec_time,
  mean_exec_time,
  query
FROM pg_stat_statements
JOIN pg_roles ON userid = oid
WHERE rolname = 'n8n_user'
ORDER BY total_exec_time DESC
LIMIT 10;
```

---

## Cleanup

### Remove n8n User (If Needed)

```sql
-- Revoke all permissions
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA intake FROM n8n_user;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA marketing FROM n8n_user;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM n8n_user;
REVOKE ALL PRIVILEGES ON DATABASE "Marketing DB" FROM n8n_user;

-- Drop role
DROP ROLE n8n_user;
```

**⚠️ Warning:** Only do this if n8n is no longer needed or being replaced.

---

## Related Documentation

- **N8N_CREDENTIALS.txt** - Connection credentials (not in git)
- **setup_n8n_user.js** - Setup script (can be re-run)
- **MIGRATION_LOG.md** - Database migration history
- **DATABASE_CLEANUP_REPORT.md** - Schema cleanup details

---

## Support

### Common Issues

1. **"relation does not exist"** → Table may have been renamed or is in wrong schema
2. **"permission denied"** → Trying to access table/schema not granted to n8n_user
3. **"SSL required"** → Must use sslmode=require in connection string
4. **"password authentication failed"** → Check credentials in N8N_CREDENTIALS.txt

### Getting Help

1. Check this guide first
2. Review n8n logs for specific error messages
3. Test connection with psql or pgAdmin
4. Verify permissions with queries above
5. Contact database administrator if still stuck

---

**Created:** 2025-10-24
**Role:** n8n_user
**Principle:** Least privilege access
**Status:** ✅ Active and tested
