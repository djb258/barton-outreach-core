# API Reference

Complete catalog of all API endpoints in the Barton Outreach system.

## Base URLs

- **Development**: `http://localhost:3000`
- **Production**: `https://barton-outreach-api.onrender.com`

## Authentication

All endpoints require authentication via API key or session token.

```bash
Authorization: Bearer <token>
```

## Core Endpoints

### Health Check
```http
GET /health
```
Returns API health status.

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2025-10-23T12:00:00Z",
  "database": "connected"
}
```

---

## Database Operations

### Ingest Data
```http
POST /api/ingest
```
Ingest raw data into `intake.raw_loads` table.

**Body**:
```json
{
  "source": "apollo|apify|manual",
  "batch_id": "batch-123",
  "rows": [
    {
      "email": "john@example.com",
      "name": "John Doe",
      "company": "Acme Corp",
      "title": "CEO"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "batch_id": "batch-123",
  "inserted": 1,
  "skipped": 0,
  "message": "Batch batch-123: Inserted 1, Skipped 0 (duplicates)"
}
```

---

### Promote Contacts
```http
POST /api/promote
```
Promote contacts from `intake.raw_loads` to `vault.contacts`.

**Body**:
```json
{
  "load_ids": [123, 456, 789]
}
```
Leave empty to promote all pending contacts.

**Response**:
```json
{
  "success": true,
  "promoted_count": 3,
  "updated_count": 0,
  "failed_count": 0,
  "message": "Promoted 3 contacts"
}
```

---

### Get Contacts
```http
GET /api/contacts
```
List all contacts from `vault.contacts`.

**Query Parameters**:
- `limit` (int): Max results (default: 100)
- `offset` (int): Pagination offset (default: 0)
- `status` (string): Filter by status (active|inactive|bounced|unsubscribed)
- `source` (string): Filter by source

**Response**:
```json
{
  "contacts": [
    {
      "contact_id": 123,
      "email": "john@example.com",
      "name": "John Doe",
      "company": "Acme Corp",
      "title": "CEO",
      "source": "apollo",
      "score": 85.5,
      "status": "active",
      "created_at": "2025-10-20T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

---

### Get Single Contact
```http
GET /api/contacts/:id
```
Get contact by ID.

**Response**:
```json
{
  "contact_id": 123,
  "email": "john@example.com",
  "name": "John Doe",
  "company": "Acme Corp",
  "title": "CEO",
  "phone": "+1-555-0100",
  "source": "apollo",
  "tags": ["hot-lead", "enterprise"],
  "custom_fields": {
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "industry": "Technology"
  },
  "score": 85.5,
  "status": "active",
  "created_at": "2025-10-20T10:00:00Z",
  "updated_at": "2025-10-23T12:00:00Z",
  "last_activity_at": "2025-10-23T11:00:00Z"
}
```

---

### Update Contact
```http
PATCH /api/contacts/:id
```
Update contact fields.

**Body**:
```json
{
  "name": "John A. Doe",
  "score": 90.0,
  "tags": ["hot-lead", "enterprise", "decision-maker"],
  "custom_fields": {
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "notes": "Interested in Q1 2026"
  }
}
```

**Response**:
```json
{
  "success": true,
  "contact_id": 123,
  "updated_fields": ["name", "score", "tags", "custom_fields"]
}
```

---

### Search Contacts
```http
POST /api/contacts/search
```
Advanced contact search.

**Body**:
```json
{
  "query": "technology CEO",
  "filters": {
    "score_min": 80,
    "status": "active",
    "companies": ["Acme Corp", "TechStart Inc"],
    "tags": ["hot-lead"]
  },
  "sort": "score",
  "order": "desc",
  "limit": 50
}
```

---

## Analytics

### Dashboard Metrics
```http
GET /api/analytics/dashboard
```
Get dashboard metrics.

**Response**:
```json
{
  "total_contacts": 10234,
  "active_contacts": 8901,
  "pending_promotions": 456,
  "contacts_added_today": 123,
  "top_sources": [
    { "source": "apollo", "count": 5000 },
    { "source": "apify", "count": 3000 }
  ],
  "status_breakdown": {
    "active": 8901,
    "inactive": 1000,
    "bounced": 233,
    "unsubscribed": 100
  }
}
```

---

### Audit Log
```http
GET /api/audit
```
Get audit log entries.

**Query Parameters**:
- `action` (string): Filter by action type
- `start_date` (ISO date): Start date
- `end_date` (ISO date): End date
- `limit` (int): Max results

**Response**:
```json
{
  "entries": [
    {
      "log_id": 789,
      "action": "contact_promoted",
      "load_id": 123,
      "contact_id": 456,
      "details": { "email": "john@example.com" },
      "timestamp": "2025-10-23T12:00:00Z"
    }
  ]
}
```

---

## Webhooks

### Register Webhook
```http
POST /api/webhooks
```
Register a webhook for events.

**Body**:
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["contact.promoted", "contact.updated"],
  "secret": "your-webhook-secret"
}
```

---

### Test Webhook
```http
POST /api/webhooks/:id/test
```
Send test event to webhook.

---

## Error Responses

All errors follow this format:

```json
{
  "error": true,
  "code": "INVALID_INPUT",
  "message": "Email is required",
  "details": {
    "field": "email",
    "received": null
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | Invalid request body or parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE` | 409 | Duplicate entry (email already exists) |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `SERVER_ERROR` | 500 | Internal server error |
| `DATABASE_ERROR` | 503 | Database connection error |

---

## Rate Limiting

- **Standard**: 100 requests/minute
- **Burst**: 200 requests/minute (short duration)
- **Ingest endpoints**: 1000 rows per request max

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635000000
```

---

## Examples

### Ingest and Promote Workflow

```bash
# 1. Ingest data
curl -X POST https://api.example.com/api/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "apollo",
    "batch_id": "apollo-2025-10-23",
    "rows": [
      {
        "email": "john@example.com",
        "name": "John Doe",
        "company": "Acme Corp",
        "title": "CEO"
      }
    ]
  }'

# 2. Promote contacts
curl -X POST https://api.example.com/api/promote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# 3. Get contacts
curl -X GET https://api.example.com/api/contacts?limit=10 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Internal Endpoints

These endpoints are for internal use only (MCP, agents, CI/CD):

### LLM Endpoint
```http
POST /llm
```
Claude AI integration endpoint.

### Subagents
```http
POST /subagents
```
Trigger subagent execution.

### SSOT Save
```http
POST /ssot/save
```
Single Source of Truth persistence.

---

## Database Functions (Direct SQL)

If using direct database access:

```sql
-- Ingest data
SELECT * FROM intake.f_ingest_json(
  ARRAY['{"email":"john@example.com","name":"John Doe"}'::jsonb],
  'apollo',
  'batch-123'
);

-- Promote contacts
SELECT * FROM vault.f_promote_contacts(ARRAY[123, 456]);
```

---

**Last Updated**: 2025-10-23
**Version**: 1.0
**Maintained By**: Backend Team

For implementation details, see:
- Database schema: `ctb/data/SCHEMA.md`
- API source code: `ctb/sys/api/`
- Integration examples: `ctb/docs/examples/`
