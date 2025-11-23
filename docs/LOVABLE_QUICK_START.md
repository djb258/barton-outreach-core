# Lovable Edge Function - Quick Start Guide

## 🚀 TL;DR

You need to create an edge function in Lovable.dev to manage invalid records from validation failures.

**Tables**:
- `marketing.company_invalid` - Companies that failed validation
- `marketing.people_invalid` - People that failed validation

**Connection String**:
```
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

---

## 📋 What You Need to Do in Lovable

### 1. Create Supabase Edge Function

**Function Name**: `invalid-records-manager`

**Environment Variable**:
```
DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

### 2. Implement These Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/invalid-companies` | List invalid companies (with pagination) |
| GET | `/invalid-companies/:id` | Get single company details |
| PATCH | `/invalid-companies/:id` | Update company fields |
| DELETE | `/invalid-companies/:id` | Delete company permanently |
| POST | `/invalid-companies/:id/promote` | Re-validate and promote to valid |
| GET | `/invalid-people` | List invalid people (with pagination) |
| GET | `/invalid-people/:id` | Get single person details |
| PATCH | `/invalid-people/:id` | Update person fields |
| DELETE | `/invalid-people/:id` | Delete person permanently |
| POST | `/invalid-people/:id/promote` | Re-validate and promote to valid |

### 3. UI Components Needed

#### **Page 1: Invalid Companies**
- Table with columns: Name, Domain, Employee Count, Reason, Failed At, Reviewed
- Filters: Reviewed status, Batch ID, Search
- Actions: View, Edit, Delete, Promote

#### **Page 2: Invalid People**
- Table with columns: Name, Email, Title, Company, Reason, Failed At, Reviewed
- Filters: Reviewed status, Company, Batch ID, Search
- Actions: View, Edit, Delete, Promote

#### **Modal: Record Details**
- Show all fields
- Display validation errors (JSONB)
- Inline editing
- "Promote to Valid" button
- "Mark as Reviewed" checkbox

---

## 🔑 Key Concepts

### What is "Bidirectional"?

**READ** (View data):
- List all invalid records
- See validation errors
- Filter by reviewed status
- Search records

**WRITE** (Update data):
- Edit fields to fix errors (e.g., change employee_count from 30 to 150)
- Mark records as reviewed
- Delete records permanently
- **Promote** records to valid tables after fixing

### Promotion Flow

1. User fixes validation errors in UI (e.g., updates employee_count to 150)
2. User clicks "Promote to Valid"
3. Edge function re-runs validation rules
4. If valid:
   - INSERT into `marketing.company_master`
   - DELETE from `marketing.company_invalid`
   - CREATE 3 slots (CEO, CFO, HR) in `marketing.company_slot`
5. If still invalid:
   - Show errors, don't promote

---

## 📊 Sample Data Structure

### Invalid Company Record
```json
{
  "id": 1,
  "company_unique_id": "04.04.02.04.30000.001",
  "company_name": "Small Corp",
  "domain": "smallcorp.com",
  "website": "https://smallcorp.com",
  "employee_count": 30,
  "linkedin_url": "https://linkedin.com/company/smallcorp",
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
  "batch_id": "batch_2025_11_19_001"
}
```

### Invalid Person Record
```json
{
  "id": 1,
  "unique_id": "04.04.02.04.20000.001",
  "full_name": "John Smith",
  "email": "john@smallcorp.com",
  "title": "Finance Manager",
  "company_name": "Small Corp",
  "company_unique_id": "04.04.02.04.30000.001",
  "linkedin_url": "",
  "validation_status": "FAILED",
  "reason_code": "missing_ceo_title",
  "validation_errors": [
    {
      "field": "title",
      "rule": "title_executive",
      "message": "Title must include CEO, CFO, or HR-related keywords",
      "severity": "error",
      "current_value": "Finance Manager"
    },
    {
      "field": "linkedin_url",
      "rule": "linkedin_url_required",
      "message": "LinkedIn URL is required",
      "severity": "error",
      "current_value": ""
    }
  ],
  "reviewed": false,
  "failed_at": "2025-11-19T10:00:00Z"
}
```

---

## ✅ Validation Rules (What Makes a Record Invalid)

### Company Rules
- ❌ **company_name** < 3 characters
- ❌ **website** doesn't start with "http://" or "https://"
- ❌ **employee_count** ≤ 50
- ❌ **linkedin_url** doesn't contain "linkedin.com/company/"
- ❌ Missing **CEO, CFO, or HR slots**

### Person Rules
- ❌ **full_name** doesn't contain a space (needs first + last)
- ❌ **email** invalid format
- ❌ **title** doesn't include "CEO", "CFO", or HR keywords
- ❌ **company_unique_id** doesn't exist in `company_master`
- ❌ **linkedin_url** doesn't contain "linkedin.com/in/"

---

## 🛠️ Testing the Setup

### Step 1: Test Connection
```sql
SELECT COUNT(*) FROM marketing.company_invalid;
SELECT COUNT(*) FROM marketing.people_invalid;
```

### Step 2: Test GET Endpoint
```bash
curl https://your-edge-function.supabase.co/invalid-companies?page=1&limit=10
```

### Step 3: Test PATCH Endpoint
```bash
curl -X PATCH https://your-edge-function.supabase.co/invalid-companies/1 \
  -H "Content-Type: application/json" \
  -d '{"employee_count": 150, "reviewed": true}'
```

### Step 4: Test Promotion
```bash
curl -X POST https://your-edge-function.supabase.co/invalid-companies/1/promote \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

---

## 📚 Full Documentation

For complete details, see: `docs/LOVABLE_EDGE_FUNCTION_SETUP.md`

---

**Last Updated**: 2025-11-19
**Status**: Ready for Implementation
