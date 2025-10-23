# /api/validate - Vercel Serverless Validation Endpoint

## Overview

The `/api/validate` endpoint implements the Middle (M) layer validation orchestration for the IMO Outreach Process Manager. It validates company records against STAMPED doctrine through Composio MCP tools with no direct database connections.

## Endpoint Specification

**Path:** `/api/validate`
**Method:** `POST`
**Format:** Vercel-ready serverless function
**Timeout:** 30 seconds

## Request Format

```json
{
  "batch_id": "2025-09-21-001",
  "filters": {
    "validated": null
  },
  "limit": 1000
}
```

### Parameters

- **batch_id** (optional): Specific batch to validate. Default = most recent ingestion
- **filters** (optional): Row selection criteria
  - `validated: null` - All rows
  - `validated: true` - Only validated rows
  - `validated: false` - Only failed rows
- **limit** (optional): Maximum rows to process (default: 1000)

## Response Format

```json
{
  "success": true,
  "rows_validated": 95,
  "rows_failed": 5,
  "results": [
    {
      "unique_id": "02.01.03.04.10000.001",
      "process_id": "Validate Company Record",
      "company_name": "Acme Corp",
      "validated": true,
      "errors": [],
      "enrichment_applied": true,
      "dedupe_status": "unique",
      "email_validation": {
        "valid": true,
        "quality_score": 0.92,
        "provider": "google"
      }
    },
    {
      "unique_id": "02.01.03.04.10000.002",
      "process_id": "Validate Company Record",
      "company_name": "Bad Email LLC",
      "validated": false,
      "errors": ["missing_email", "duplicate_domain"],
      "enrichment_applied": false,
      "dedupe_status": "duplicate",
      "duplicate_of": "02.01.03.04.10000.050"
    }
  ],
  "altitude": 10000,
  "doctrine": "STAMPED",
  "process_metadata": {
    "batch_id": "2025-09-21-001",
    "process_id": "VALIDATE_20250921_1234_ABC",
    "started_at": "2025-09-21T12:00:00Z",
    "completed_at": "2025-09-21T12:00:02Z",
    "total_processing_time_ms": 2500,
    "performance_grade": "A"
  }
}
```

## Validation Pipeline

### 1. Schema Validation (STAMPED Doctrine)

Validates against required fields and data types:

```javascript
const STAMPED_SCHEMA = {
  required_fields: [
    'company_name', 'industry', 'contact_email',
    'contact_phone', 'address', 'website_url', 'employee_count'
  ],
  field_types: {
    company_name: 'string',
    contact_email: 'email',
    contact_phone: 'phone',
    website_url: 'url',
    employee_count: 'number'
  }
}
```

### 2. Dedupe Check

Queries master company table via Composio MCP:

```sql
SELECT unique_id, company_name, website_url
FROM marketing.company
WHERE LOWER(company_name) = LOWER('{company_name}')
   OR website_url = '{website_url}'
```

### 3. Email Validation (MillionVerify MCP)

Validates email deliverability through Composio MCP:

```javascript
await bridge.executeNeonOperation('MILLIONVERIFY_VALIDATE', {
  email: row.contact_email,
  timeout: 5000
})
```

### 4. Data Enrichment (Apify MCP)

Enriches missing company data:

```javascript
await bridge.executeNeonOperation('APIFY_ENRICH_COMPANY', {
  website_url: row.website_url,
  company_name: row.company_name
})
```

## MCP Tool Integration

### Neon Database Operations
- `NEON_QUERY_ROWS` - Fetch rows from staging table
- `NEON_EXECUTE_SQL` - Execute custom SQL queries
- `NEON_UPDATE_ROWS` - Update validation results

### Enrichment Services
- `MILLIONVERIFY_VALIDATE_EMAIL` - Email validation
- `APIFY_EXTRACT_COMPANY_DATA` - Company data enrichment
- `TWILIO_PHONE_LOOKUP` - Phone validation

## Error Categories

### Schema Errors
- `missing_company_name`
- `missing_email`
- `invalid_email_format`
- `invalid_phone_format`
- `invalid_employee_count_range`

### Business Rule Errors
- `duplicate_company`
- `blacklisted_domain`
- `invalid_industry`

### Validation Errors
- `email_undeliverable`
- `phone_invalid`
- `website_unreachable`

### System Errors
- `validation_system_error`
- `mcp_timeout`
- `database_error`

## STAMPED Doctrine Compliance

Every response includes doctrine metadata:

```json
{
  "altitude": 10000,
  "doctrine": "STAMPED",
  "process_metadata": {
    "process_id": "VALIDATE_20250921_1234_ABC",
    "stamped": {
      "s": "validation_middleware",
      "t": "2025-09-21T12:00:00Z",
      "a": "composio_mcp_orchestrator",
      "m": "stamped_validation_pipeline",
      "p": "VALIDATE_20250921_1234_ABC",
      "e": "production",
      "d": { "validation_metadata": "..." }
    }
  }
}
```

## Performance Metrics

Performance grading based on processing time:
- **A+**: < 100ms
- **A**: < 500ms
- **B**: < 1000ms
- **C**: < 3000ms
- **D**: < 5000ms
- **F**: > 5000ms

## Environment Configuration

Required environment variables:

```env
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
COMPOSIO_BASE_URL=https://backend.composio.dev
NEON_CONNECTION_ID=neon_barton_outreach
DOCTRINE_HASH=STAMPED_v2.1.0
MILLIONVERIFY_API_KEY=your_key_here
APIFY_API_TOKEN=your_token_here
```

## Testing

### Local Testing

Use the test endpoint:

```bash
curl -X POST http://localhost:3000/api/validate-test \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Production Testing

```bash
curl -X POST https://your-vercel-app.vercel.app/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "2025-09-21-001",
    "filters": {"validated": null}
  }'
```

## Integration with UI

The validation endpoint integrates with these UI components:

- **ValidationAdjusterConsole**: Shows validation results
- **ValidationResultsTable**: Displays row-level validation status
- **ValidationSummaryCard**: Shows validation metrics
- **ProcessingStatusPanel**: Updates validation progress

## Error Handling

All errors return structured responses:

```json
{
  "success": false,
  "error": "Validation failed",
  "message": "Detailed error description",
  "rows_validated": 0,
  "rows_failed": 0,
  "altitude": 10000,
  "doctrine": "STAMPED",
  "process_metadata": {
    "error_timestamp": "2025-09-21T12:00:00Z",
    "error_details": {
      "message": "Error details",
      "stack": "Stack trace"
    }
  }
}
```

## Deployment

Deploy to Vercel:

1. Ensure all environment variables are configured
2. The function automatically deploys as a serverless endpoint
3. Accessible at `/api/validate` on your Vercel domain
4. Scales automatically based on demand

## Security

- No direct database connections (MCP only)
- API key authentication through Composio
- Environment variable configuration
- Structured error responses (no sensitive data exposure)