# Lovable.dev Database Credentials

## ✅ Role Created Successfully

A new PostgreSQL role has been created specifically for Lovable.dev edge functions, avoiding SCRAM authentication issues.

**Date Created**: 2025-11-19
**Status**: ✅ Tested and Verified

---

## 🔑 Connection Credentials

### Role Details

```
Role Name: marketing_db_owner
Password: G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb
Database: Marketing DB
Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port: 5432
SSL Mode: require
```

### Connection String (URL Encoded)

**For Lovable.dev Environment Variables**:
```
postgresql://marketing_db_owner:G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

**Plain Text (for reference)**:
```
postgresql://marketing_db_owner:G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing DB?sslmode=require
```

---

## 🚀 Setup in Lovable.dev

### Step 1: Create Supabase Edge Function

1. In your Lovable.dev project, create a new Supabase Edge Function
2. Name it: `invalid-records-manager`

### Step 2: Set Environment Variable

Add the following environment variable to your edge function:

**Variable Name**:
```
DATABASE_URL
```

**Variable Value** (copy exactly):
```
postgresql://marketing_db_owner:G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### Step 3: Install Deno PostgreSQL Library

In your edge function code, import the Postgres library:

```typescript
import { Pool } from "https://deno.land/x/postgres@v0.17.0/mod.ts";
```

### Step 4: Initialize Connection

```typescript
const databaseUrl = Deno.env.get("DATABASE_URL");
const pool = new Pool(databaseUrl, 3, true);

// Get connection
const connection = await pool.connect();

// Run queries
const result = await connection.queryObject`
  SELECT * FROM marketing.company_invalid LIMIT 10
`;

// Release connection
connection.release();
```

---

## 🔒 Permissions Granted

The `marketing_db_owner` role has been granted the following permissions:

### Schema Access
- ✅ `public` - Full access
- ✅ `marketing` - Full access (contains `company_invalid` and `people_invalid`)
- ✅ `intake` - Full access
- ✅ `bit` - Full access
- ✅ `shq` - Full access
- ✅ `ple` - Full access
- ✅ `PLE` - Full access
- ✅ `BIT` - Full access

### Table Permissions
- ✅ SELECT - Read data
- ✅ INSERT - Create new records
- ✅ UPDATE - Modify existing records
- ✅ DELETE - Remove records

### Sequence Permissions
- ✅ USAGE - Use sequences for auto-increment IDs
- ✅ SELECT - Read sequence values

### Function Permissions
- ✅ EXECUTE - Run stored procedures and functions

### Database Permissions
- ✅ TEMP - Create temporary tables for complex queries

---

## 🧪 Verified Test Results

All CRUD operations have been tested and verified:

```
✅ Connection successful
✅ Schema access verified (5 schemas)
✅ Invalid tables accessible (company_invalid, people_invalid)
✅ SELECT queries work (119 invalid companies, 21 invalid people)
✅ INSERT permission verified
✅ UPDATE permission verified
✅ DELETE permission verified
```

---

## 📊 Accessible Tables

### Primary Tables for Edge Function

**marketing.company_invalid** (119 records)
- Contains companies that failed validation
- Fields: company_unique_id, company_name, website, employee_count, etc.
- validation_errors (JSONB) - Detailed error information

**marketing.people_invalid** (21 records)
- Contains people that failed validation
- Fields: unique_id, full_name, email, title, company_unique_id, etc.
- validation_errors (JSONB) - Detailed error information

### Other Accessible Schemas
- `intake.*` - Raw intake tables
- `bit.*` - Buyer Intent Tool tables
- `shq.*` - Error logging tables
- `public.*` - System tables

---

## 🔐 Security Notes

1. **Password Storage**: Store the password securely in Lovable.dev environment variables only
2. **Connection Pooling**: Use connection pooling (max 3 connections recommended)
3. **SSL Mode**: Always use `sslmode=require` for encrypted connections
4. **Rate Limiting**: Neon enforces connection limits; pool connections appropriately
5. **Read-Only Option**: If you need read-only access, create a separate role with only SELECT

---

## 🛠️ Troubleshooting

### Connection Fails with "SCRAM authentication failed"

**Solution**: Ensure you're using the exact connection string with URL encoding:
- Database name must be: `Marketing%20DB` (with %20 for space)
- Password: `G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb` (no special characters)

### "Permission denied for table"

**Solution**: The role has full permissions. Check:
1. Table name is correct: `marketing.company_invalid` (not just `company_invalid`)
2. Schema prefix is included in query
3. Connection string is correct

### "Too many connections"

**Solution**: Use connection pooling:
```typescript
const pool = new Pool(databaseUrl, 3, true); // Max 3 connections
```

### "SSL connection required"

**Solution**: Ensure connection string ends with `?sslmode=require`

---

## 📚 Related Documentation

- **Complete API Specification**: `docs/LOVABLE_EDGE_FUNCTION_SETUP.md`
- **Quick Start Guide**: `docs/LOVABLE_QUICK_START.md`
- **Validation Rules**: `ctb/sys/toolbox-hub/backend/validator/validation_rules.py`
- **Invalid Tables Schema**: `ctb/data/validation-framework/sql/create_invalid_tables.sql`

---

## 🔄 Regenerating Credentials (If Needed)

If you need to regenerate the password or recreate the role:

```bash
# Regenerate password
node infra/scripts/generate-secure-password.js

# Recreate role
node infra/scripts/create-lovable-role-v2.js

# Test connection
node infra/scripts/test-lovable-role.js
```

---

**Last Updated**: 2025-11-19
**Role Status**: ✅ Active and Verified
**Next Step**: Copy connection string to Lovable.dev environment variables
