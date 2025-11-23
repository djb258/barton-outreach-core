# Lovable Edge Function Setup - Invalid Records Management

## Overview

This guide provides everything needed to create a bidirectional edge function in Lovable.dev for managing validation failures (invalid companies and people records).

**Purpose**: View, review, edit, and promote records from `company_invalid` and `people_invalid` tables.

---

## Database Tables

### 1. `marketing.company_invalid`

**Purpose**: Stores company records that failed validation

**Schema**:
```sql
CREATE TABLE marketing.company_invalid (
  id BIGSERIAL PRIMARY KEY,
  company_unique_id TEXT UNIQUE NOT NULL,
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  website TEXT,
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.company_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
```

**Key Fields**:
- `id` - Auto-incrementing primary key
- `company_unique_id` - Barton ID format: `04.04.02.04.30000.###`
- `validation_status` - Always 'FAILED' for records in this table
- `reason_code` - Short failure reason (e.g., "employee_count_too_low")
- `validation_errors` - JSONB array of detailed errors:
  ```json
  [
    {
      "field": "employee_count",
      "rule": "employee_count_minimum",
      "message": "Employee count must be greater than 50 (current: 30)",
      "severity": "error",
      "current_value": "30"
    }
  ]
  ```
- `reviewed` - Boolean flag for manual review tracking
- `batch_id` - Links to upload batch

### 2. `marketing.people_invalid`

**Purpose**: Stores people records that failed validation

**Schema**:
```sql
CREATE TABLE marketing.people_invalid (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  full_name TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_name TEXT,
  company_unique_id TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.people_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);
```

**Key Fields**:
- `id` - Auto-incrementing primary key
- `unique_id` - Barton ID format: `04.04.02.04.20000.###`
- `validation_status` - Always 'FAILED' for records in this table
- `reason_code` - Short failure reason (e.g., "missing_ceo_title")
- `validation_errors` - JSONB array of detailed errors (same format as company)
- `company_unique_id` - Foreign key to company (may or may not be valid)
- `reviewed` - Boolean flag for manual review tracking

---

## Database Connection

### Neon PostgreSQL Credentials

**Connection String**:
```
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

**Individual Components**:
```
Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port: 5432
Database: Marketing DB
User: Marketing DB_owner
Password: npg_OsE4Z2oPCpiT
SSL Mode: require
```

**Environment Variable** (for Lovable):
```bash
DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

---

## Required RLS Policies

Neon PostgreSQL uses Row Level Security (RLS). You'll need to create policies for edge function access:

```sql
-- Enable RLS on tables (if not already enabled)
ALTER TABLE marketing.company_invalid ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketing.people_invalid ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users
CREATE POLICY "Allow all for authenticated users" ON marketing.company_invalid
  FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow all for authenticated users" ON marketing.people_invalid
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Grant permissions to role
GRANT SELECT, INSERT, UPDATE, DELETE ON marketing.company_invalid TO "Marketing DB_owner";
GRANT SELECT, INSERT, UPDATE, DELETE ON marketing.people_invalid TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE marketing.company_invalid_id_seq TO "Marketing DB_owner";
GRANT USAGE, SELECT ON SEQUENCE marketing.people_invalid_id_seq TO "Marketing DB_owner";
```

---

## API Endpoint Specifications

### Endpoint Structure

Create a Supabase Edge Function with the following routes:

#### 1. **GET /invalid-companies**
List all invalid companies with pagination and filtering.

**Query Parameters**:
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `reviewed` (optional: true/false)
- `batch_id` (optional: filter by batch)
- `search` (optional: search company_name or domain)

**Response**:
```json
{
  "data": [
    {
      "id": 1,
      "company_unique_id": "04.04.02.04.30000.001",
      "company_name": "Small Corp",
      "website": "https://smallcorp.com",
      "employee_count": 30,
      "reason_code": "employee_count_too_low",
      "validation_errors": [...],
      "validation_warnings": [...],
      "reviewed": false,
      "failed_at": "2025-11-19T10:00:00Z",
      "batch_id": "batch_2025_11_19_001"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "total_pages": 8
  }
}
```

**SQL Query**:
```sql
SELECT
  id, company_unique_id, company_name, domain, industry,
  employee_count, website, linkedin_url,
  validation_status, reason_code, validation_errors, validation_warnings,
  reviewed, failed_at, batch_id, created_at, updated_at
FROM marketing.company_invalid
WHERE ($3::BOOLEAN IS NULL OR reviewed = $3)
  AND ($4::TEXT IS NULL OR batch_id = $4)
  AND ($5::TEXT IS NULL OR company_name ILIKE '%' || $5 || '%' OR domain ILIKE '%' || $5 || '%')
ORDER BY failed_at DESC
LIMIT $1 OFFSET $2;
```

#### 2. **GET /invalid-companies/:id**
Get single invalid company by ID.

**Response**:
```json
{
  "id": 1,
  "company_unique_id": "04.04.02.04.30000.001",
  "company_name": "Small Corp",
  "domain": "smallcorp.com",
  "industry": "Technology",
  "employee_count": 30,
  "website": "https://smallcorp.com",
  "phone": "555-1234",
  "address": "123 Main St",
  "city": "Charleston",
  "state": "WV",
  "zip": "25301",
  "validation_status": "FAILED",
  "reason_code": "employee_count_too_low",
  "validation_errors": [
    {
      "field": "employee_count",
      "rule": "employee_count_minimum",
      "message": "Employee count must be greater than 50 (current: 30)",
      "severity": "error",
      "current_value": "30"
    }
  ],
  "validation_warnings": [],
  "reviewed": false,
  "failed_at": "2025-11-19T10:00:00Z",
  "batch_id": "batch_2025_11_19_001",
  "source_table": "marketing.company_raw_wv",
  "created_at": "2025-11-19T10:00:00Z",
  "updated_at": "2025-11-19T10:00:00Z"
}
```

#### 3. **GET /invalid-people**
List all invalid people with pagination and filtering.

**Query Parameters**:
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `reviewed` (optional: true/false)
- `batch_id` (optional: filter by batch)
- `company_unique_id` (optional: filter by company)
- `search` (optional: search full_name or email)

**Response**:
```json
{
  "data": [
    {
      "id": 1,
      "unique_id": "04.04.02.04.20000.001",
      "full_name": "John Smith",
      "email": "john@smallcorp.com",
      "title": "Finance Manager",
      "company_name": "Small Corp",
      "company_unique_id": "04.04.02.04.30000.001",
      "linkedin_url": "",
      "reason_code": "missing_ceo_title",
      "validation_errors": [...],
      "reviewed": false,
      "failed_at": "2025-11-19T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 234,
    "total_pages": 12
  }
}
```

#### 4. **GET /invalid-people/:id**
Get single invalid person by ID.

#### 5. **PATCH /invalid-companies/:id**
Update fields on an invalid company (for manual correction).

**Request Body**:
```json
{
  "company_name": "Updated Corp Name",
  "employee_count": 150,
  "website": "https://updated.com",
  "reviewed": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Company updated successfully",
  "data": { /* updated record */ }
}
```

**SQL Query**:
```sql
UPDATE marketing.company_invalid
SET
  company_name = COALESCE($2, company_name),
  employee_count = COALESCE($3, employee_count),
  website = COALESCE($4, website),
  reviewed = COALESCE($5, reviewed),
  updated_at = NOW()
WHERE id = $1
RETURNING *;
```

#### 6. **PATCH /invalid-people/:id**
Update fields on an invalid person (for manual correction).

**Request Body**:
```json
{
  "full_name": "Updated Name",
  "email": "updated@email.com",
  "title": "Chief Executive Officer",
  "reviewed": true
}
```

#### 7. **POST /invalid-companies/:id/promote**
Re-validate and promote company to `marketing.company_master` if now valid.

**Request Body**:
```json
{
  "force": false  // Set to true to skip re-validation
}
```

**Response**:
```json
{
  "success": true,
  "message": "Company promoted to company_master",
  "company_unique_id": "04.04.02.04.30000.001",
  "validation_result": {
    "valid": true,
    "reason": null,
    "failures": []
  }
}
```

**Logic**:
1. Re-run validation rules (using validation_rules.py logic)
2. If valid:
   - INSERT into `marketing.company_master`
   - DELETE from `marketing.company_invalid`
   - CREATE slots in `marketing.company_slot` (CEO, CFO, HR)
3. If still invalid:
   - Return validation errors

#### 8. **POST /invalid-people/:id/promote**
Re-validate and promote person to `marketing.people_master` if now valid.

#### 9. **DELETE /invalid-companies/:id**
Permanently delete an invalid company record.

**Response**:
```json
{
  "success": true,
  "message": "Company deleted permanently"
}
```

#### 10. **DELETE /invalid-people/:id**
Permanently delete an invalid person record.

---

## Validation Rules Reference

### Company Validation Rules

Defined in: `ctb/sys/toolbox-hub/backend/validator/validation_rules.py`

**Required Fields**:
1. `company_name` - Must be ≥ 3 characters
2. `website` - Must start with "http://" or "https://" and contain a domain (has ".")
3. `employee_count` - Must be integer > 50
4. `linkedin_url` - Must contain "linkedin.com/company/"
5. **Slots** - Must have CEO, CFO, and HR slots (even if unfilled)

**Severity Levels**:
- `CRITICAL` - Blocks promotion completely
- `ERROR` - Blocks promotion (standard validation failure)
- `WARNING` - Allows promotion but flags issue
- `INFO` - Informational only

### Person Validation Rules

**Required Fields**:
1. `full_name` - Must contain a space (first + last name)
2. `email` - Must be valid email format (regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
3. `title` - Must include "CEO", "CFO", or HR keywords ("HR", "Human Resources", "People", "Talent")
4. `company_unique_id` - Must exist in `marketing.company_master`
5. `linkedin_url` - Must include "linkedin.com/in/"
6. `timestamp_last_updated` - Must be present (WARNING level)

---

## Example Edge Function Code

### Deno/Supabase Edge Function Structure

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { Pool } from "https://deno.land/x/postgres@v0.17.0/mod.ts";

const databaseUrl = Deno.env.get("DATABASE_URL");
const pool = new Pool(databaseUrl, 3, true);

serve(async (req) => {
  const url = new URL(req.url);
  const path = url.pathname;
  const method = req.method;

  // CORS headers
  const headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
  };

  if (method === "OPTIONS") {
    return new Response(null, { headers, status: 204 });
  }

  try {
    const connection = await pool.connect();

    // GET /invalid-companies
    if (method === "GET" && path === "/invalid-companies") {
      const page = parseInt(url.searchParams.get("page") || "1");
      const limit = Math.min(parseInt(url.searchParams.get("limit") || "20"), 100);
      const offset = (page - 1) * limit;
      const reviewed = url.searchParams.get("reviewed");
      const batchId = url.searchParams.get("batch_id");
      const search = url.searchParams.get("search");

      // Get total count
      const countResult = await connection.queryObject`
        SELECT COUNT(*) as total
        FROM marketing.company_invalid
        WHERE (${reviewed}::BOOLEAN IS NULL OR reviewed = ${reviewed}::BOOLEAN)
          AND (${batchId}::TEXT IS NULL OR batch_id = ${batchId})
          AND (${search}::TEXT IS NULL OR company_name ILIKE '%' || ${search} || '%' OR domain ILIKE '%' || ${search} || '%')
      `;
      const total = countResult.rows[0]?.total || 0;

      // Get data
      const result = await connection.queryObject`
        SELECT
          id, company_unique_id, company_name, domain, industry,
          employee_count, website, linkedin_url,
          validation_status, reason_code, validation_errors, validation_warnings,
          reviewed, failed_at, batch_id, created_at, updated_at
        FROM marketing.company_invalid
        WHERE (${reviewed}::BOOLEAN IS NULL OR reviewed = ${reviewed}::BOOLEAN)
          AND (${batchId}::TEXT IS NULL OR batch_id = ${batchId})
          AND (${search}::TEXT IS NULL OR company_name ILIKE '%' || ${search} || '%' OR domain ILIKE '%' || ${search} || '%')
        ORDER BY failed_at DESC
        LIMIT ${limit} OFFSET ${offset}
      `;

      connection.release();

      return new Response(
        JSON.stringify({
          data: result.rows,
          pagination: {
            page,
            limit,
            total,
            total_pages: Math.ceil(total / limit),
          },
        }),
        { headers, status: 200 }
      );
    }

    // GET /invalid-companies/:id
    if (method === "GET" && path.startsWith("/invalid-companies/")) {
      const id = path.split("/")[2];
      const result = await connection.queryObject`
        SELECT * FROM marketing.company_invalid WHERE id = ${id}
      `;

      connection.release();

      if (result.rows.length === 0) {
        return new Response(
          JSON.stringify({ error: "Company not found" }),
          { headers, status: 404 }
        );
      }

      return new Response(JSON.stringify(result.rows[0]), { headers, status: 200 });
    }

    // PATCH /invalid-companies/:id
    if (method === "PATCH" && path.startsWith("/invalid-companies/")) {
      const id = path.split("/")[2];
      const body = await req.json();

      const result = await connection.queryObject`
        UPDATE marketing.company_invalid
        SET
          company_name = COALESCE(${body.company_name}, company_name),
          employee_count = COALESCE(${body.employee_count}, employee_count),
          website = COALESCE(${body.website}, website),
          linkedin_url = COALESCE(${body.linkedin_url}, linkedin_url),
          reviewed = COALESCE(${body.reviewed}, reviewed),
          updated_at = NOW()
        WHERE id = ${id}
        RETURNING *
      `;

      connection.release();

      if (result.rows.length === 0) {
        return new Response(
          JSON.stringify({ error: "Company not found" }),
          { headers, status: 404 }
        );
      }

      return new Response(
        JSON.stringify({
          success: true,
          message: "Company updated successfully",
          data: result.rows[0],
        }),
        { headers, status: 200 }
      );
    }

    // DELETE /invalid-companies/:id
    if (method === "DELETE" && path.startsWith("/invalid-companies/")) {
      const id = path.split("/")[2];
      const result = await connection.queryObject`
        DELETE FROM marketing.company_invalid WHERE id = ${id} RETURNING id
      `;

      connection.release();

      if (result.rows.length === 0) {
        return new Response(
          JSON.stringify({ error: "Company not found" }),
          { headers, status: 404 }
        );
      }

      return new Response(
        JSON.stringify({ success: true, message: "Company deleted permanently" }),
        { headers, status: 200 }
      );
    }

    // Similar patterns for /invalid-people endpoints...

    connection.release();
    return new Response(
      JSON.stringify({ error: "Route not found" }),
      { headers, status: 404 }
    );
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers, status: 500 }
    );
  }
});
```

---

## UI Components Needed

### 1. Invalid Companies Table

**Columns**:
- Company Name
- Domain
- Employee Count
- Reason (hover for details)
- Failed At
- Reviewed (checkbox)
- Actions (View, Edit, Delete, Promote)

**Filters**:
- Reviewed status (All / Reviewed / Not Reviewed)
- Batch ID dropdown
- Search by name/domain

**Sorting**:
- Failed At (DESC default)
- Company Name (A-Z)
- Employee Count

### 2. Invalid People Table

**Columns**:
- Full Name
- Email
- Title
- Company Name
- Reason (hover for details)
- Failed At
- Reviewed (checkbox)
- Actions (View, Edit, Delete, Promote)

**Filters**:
- Reviewed status
- Company (dropdown)
- Batch ID
- Search by name/email

### 3. Detail Modal (Company)

**Sections**:
- **Overview**: Name, Domain, Industry, Employee Count, Website
- **Location**: Address, City, State, Zip
- **LinkedIn**: LinkedIn URL
- **Validation Errors**: Expandable list with field, rule, message, severity
- **Validation Warnings**: Expandable list
- **Metadata**: Batch ID, Source Table, Failed At, Created At, Updated At
- **Actions**:
  - Edit Fields (inline editing)
  - Mark as Reviewed
  - Promote to Valid (with re-validation)
  - Delete Permanently

### 4. Detail Modal (Person)

**Sections**:
- **Overview**: Full Name, Email, Title
- **Company**: Company Name, Company ID (link to company detail)
- **LinkedIn**: LinkedIn URL
- **Contact**: Phone, City, State
- **Validation Errors**: Expandable list
- **Validation Warnings**: Expandable list
- **Metadata**: Batch ID, Source Table, Failed At
- **Actions**: Edit, Review, Promote, Delete

### 5. Batch Summary Dashboard

**Metrics**:
- Total Invalid Companies
- Total Invalid People
- % Reviewed
- Recent Batches (list with counts)
- Top Failure Reasons (chart)

---

## Testing Queries

### Check if tables exist:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'marketing'
  AND table_name LIKE '%invalid%';
```

### Get sample invalid companies:
```sql
SELECT id, company_name, reason_code, validation_errors, reviewed
FROM marketing.company_invalid
ORDER BY failed_at DESC
LIMIT 10;
```

### Get sample invalid people:
```sql
SELECT id, full_name, email, title, reason_code, validation_errors, reviewed
FROM marketing.people_invalid
ORDER BY failed_at DESC
LIMIT 10;
```

### Count by review status:
```sql
SELECT reviewed, COUNT(*) as count
FROM marketing.company_invalid
GROUP BY reviewed;

SELECT reviewed, COUNT(*) as count
FROM marketing.people_invalid
GROUP BY reviewed;
```

### Top failure reasons (companies):
```sql
SELECT reason_code, COUNT(*) as count
FROM marketing.company_invalid
GROUP BY reason_code
ORDER BY count DESC
LIMIT 10;
```

### Top failure reasons (people):
```sql
SELECT reason_code, COUNT(*) as count
FROM marketing.people_invalid
GROUP BY reason_code
ORDER BY count DESC
LIMIT 10;
```

---

## Next Steps

1. **Create the tables** (if they don't exist):
   - Run `ctb/data/validation-framework/sql/create_invalid_tables.sql`

2. **Set up RLS policies**:
   - Run the RLS policies from this document

3. **Deploy Edge Function in Lovable**:
   - Create new Supabase Edge Function
   - Copy the example code above
   - Add `DATABASE_URL` environment variable
   - Test each endpoint

4. **Build UI in Lovable**:
   - Create Invalid Companies page with table + filters
   - Create Invalid People page with table + filters
   - Create detail modals with edit functionality
   - Add "Promote" button with re-validation logic
   - Add batch summary dashboard

5. **Test Bidirectional Flow**:
   - View invalid records in UI
   - Edit a record (e.g., fix employee_count)
   - Mark as reviewed
   - Promote to valid tables
   - Verify record appears in `company_master` or `people_master`

---

**Last Updated**: 2025-11-19
**Database**: Neon PostgreSQL (Marketing DB)
**Tables**: `marketing.company_invalid`, `marketing.people_invalid`
