# Neon Analytics & Monitoring API

**Doctrine-aligned endpoints for Control Tower, Executive Overview, and Analytics dashboards.**

## Overview

The Neon API provides real-time access to system health, error tracking, data integrity, messaging performance, and comprehensive analytics. All endpoints query Neon PostgreSQL database using the `@neondatabase/serverless` driver.

**Architecture:**
- **Frontend:** Firebase-hosted UI (Control Tower, Executive Overview, Analytics pages)
- **Backend:** Express.js API routes mounted at `/neon/*`
- **Database:** Neon PostgreSQL (schemas: `shq`, `marketing`)
- **Connection:** Direct Neon serverless driver (not through Composio MCP)

---

## Base URL

```
http://localhost:3000/neon
```

In production: `https://your-render-deployment.onrender.com/neon`

---

## Endpoints

### 1. Health Check

**GET** `/neon/health`

Check Neon database connectivity and status.

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "database": "neon",
  "timestamp": "2025-10-14T12:30:45.123Z",
  "version": "PostgreSQL 15.3..."
}
```

**Error Response (503):**
```json
{
  "success": false,
  "status": "unhealthy",
  "database": "neon",
  "error": "Connection timeout"
}
```

---

### 2. Dashboard Summary

**GET** `/neon/dashboard-summary`

Executive-level KPI summary for Control Tower and Overview dashboards.

**Query Parameters:**
- `hours` (optional, default: 24): Time window in hours

**Sample Request:**
```bash
curl http://localhost:3000/neon/dashboard-summary?hours=24
```

**Response:**
```json
{
  "success": true,
  "data": {
    "errorStats": {
      "critical": 3,
      "high": 12,
      "medium": 45,
      "low": 18,
      "total": 78,
      "resolved": 62,
      "unresolved": 16
    },
    "processStats": {
      "total": 1234,
      "completed": 1180,
      "failed": 54,
      "successRate": 95.6,
      "avgDurationSeconds": 12.4
    },
    "agentStats": {
      "total": 8,
      "active": 7,
      "failing": 1,
      "healthyPercentage": 87.5
    },
    "performanceMetrics": {
      "avgLatencyMs": 245,
      "p95LatencyMs": 890,
      "p99LatencyMs": 1420
    }
  },
  "timeWindow": "24h",
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Tables:**
- `shq.master_error_log`
- `shq.process_registry`

---

### 3. Error Feed

**GET** `/neon/errors`

Retrieve error log with pagination and filtering for Control Tower.

**Query Parameters:**
- `limit` (optional, default: 100, max: 1000): Number of records
- `offset` (optional, default: 0): Pagination offset
- `severity` (optional): Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `agent_id` (optional): Filter by agent
- `resolved` (optional): Filter by resolution status (true/false)
- `source` (optional): Filter by source system

**Sample Request:**
```bash
curl "http://localhost:3000/neon/errors?limit=50&severity=CRITICAL&resolved=false"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "errorId": "err_abc123xyz",
      "occurredAt": "2025-10-14T12:15:30.456Z",
      "resolvedAt": null,
      "processId": "proc_xyz789",
      "blueprintId": "bp_email_outreach",
      "agentId": "agent_instantly",
      "stage": "output",
      "severity": "CRITICAL",
      "errorType": "API_RATE_LIMIT",
      "message": "Instantly API rate limit exceeded: 429 Too Many Requests",
      "escalationLevel": 2,
      "escalatedAt": "2025-10-14T12:20:00.000Z",
      "resolutionMethod": null,
      "occurrenceCount": 5,
      "patternId": "ptn_rate_limit_001",
      "context": {
        "source": "instantly",
        "campaignId": "camp_123",
        "endpoint": "/api/v1/campaigns/send"
      },
      "isResolved": false
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 156,
    "hasMore": true,
    "returned": 50
  },
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.master_error_log`

---

**GET** `/neon/errors/:errorId`

Get detailed information about a specific error including resolution attempts and pattern matching.

**Sample Request:**
```bash
curl http://localhost:3000/neon/errors/err_abc123xyz
```

**Response:**
```json
{
  "success": true,
  "data": {
    "errorId": "err_abc123xyz",
    "occurredAt": "2025-10-14T12:15:30.456Z",
    "resolvedAt": null,
    "processId": "proc_xyz789",
    "blueprintId": "bp_email_outreach",
    "planId": "plan_v2_outreach",
    "planVersion": 3,
    "agentId": "agent_instantly",
    "stage": "output",
    "severity": "CRITICAL",
    "errorType": "API_RATE_LIMIT",
    "message": "Instantly API rate limit exceeded: 429 Too Many Requests",
    "stacktrace": "Error: Rate limit...\n  at InstantlyClient.send...",
    "hdoSnapshot": { /* HDO state snapshot */ },
    "context": { /* Error context */ },
    "escalationLevel": 2,
    "escalatedAt": "2025-10-14T12:20:00.000Z",
    "escalationReason": "Multiple failures within 5 minutes",
    "resolutionMethod": null,
    "resolutionNotes": null,
    "resolvedBy": null,
    "occurrenceCount": 5,
    "firstOccurredAt": "2025-10-14T11:45:00.000Z",
    "pattern": {
      "patternId": "ptn_rate_limit_001",
      "signature": "API_RATE_LIMIT:instantly:/api/v1/campaigns/send",
      "knownSolution": "Implement exponential backoff with 60s initial delay",
      "autoResolutionAvailable": true,
      "totalOccurrences": 47
    },
    "resolutionAttempts": [
      {
        "attemptId": "att_001",
        "method": "auto_retry",
        "attemptedBy": "error_resolver_agent",
        "attemptedAt": "2025-10-14T12:16:00.000Z",
        "success": false,
        "durationSeconds": 3.2,
        "outcomeMessage": "Retry failed: rate limit still active"
      }
    ]
  },
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Tables:**
- `shq.master_error_log`
- `shq.error_patterns`
- `shq.error_resolution_attempts`

---

### 4. Data Integrity Audit

**GET** `/neon/integrity`

Data integrity audit records and trends for quality monitoring.

**Query Parameters:**
- `limit` (optional, default: 50, max: 500): Number of records
- `status` (optional): Filter by status (passed/failed)
- `hours` (optional, default: 24): Time window in hours

**Sample Request:**
```bash
curl "http://localhost:3000/neon/integrity?hours=168&status=failed"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total": 1456,
      "passed": 1398,
      "failed": 58,
      "passRate": 96.02,
      "timeWindow": "168h"
    },
    "records": [
      {
        "auditId": "audit_xyz789",
        "auditedAt": "2025-10-14T12:00:00.000Z",
        "dataSource": "apollo",
        "tableName": "marketing.marketing_apollo_raw",
        "checkName": "email_format_validation",
        "status": "failed",
        "recordsChecked": 1000,
        "recordsFailed": 23,
        "failureRate": 2.3,
        "details": { "invalid_emails": 23, "null_emails": 0 },
        "severity": "medium"
      }
    ],
    "trend": [
      {
        "hour": "2025-10-14T11:00:00.000Z",
        "totalChecks": 24,
        "failedChecks": 2,
        "avgFailureRate": 1.5
      }
    ]
  },
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.integrity_audit`

---

### 5. Missing Data Registry

**GET** `/neon/missing`

Missing/incomplete data records for data quality monitoring.

**Query Parameters:**
- `limit` (optional, default: 100, max: 500): Number of records
- `severity` (optional): Filter by severity (critical/high/medium/low)
- `resolved` (optional): Filter by resolution status (true/false)

**Sample Request:**
```bash
curl "http://localhost:3000/neon/missing?severity=critical&resolved=false"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total": 234,
      "critical": 12,
      "high": 45,
      "medium": 123,
      "low": 54,
      "resolved": 189,
      "unresolved": 45
    },
    "records": [
      {
        "id": "missing_abc123",
        "detectedAt": "2025-10-14T10:30:00.000Z",
        "resolvedAt": null,
        "entityType": "contact",
        "entityId": "contact_xyz789",
        "missingField": "company_website",
        "fieldImportance": "required_for_enrichment",
        "severity": "critical",
        "impactDescription": "Cannot enrich contact without company website",
        "suggestedSource": "apollo_api",
        "resolutionNotes": null,
        "isResolved": false
      }
    ]
  },
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.missing_data_registry`

---

### 6. Messaging Performance

**GET** `/neon/messaging`

Outbound campaign performance metrics for messaging dashboard.

**Query Parameters:**
- `hours` (optional, default: 24): Time window in hours
- `campaign_id` (optional): Filter by specific campaign
- `source` (optional): Filter by source (instantly, heyreach, etc.)

**Sample Request:**
```bash
curl "http://localhost:3000/neon/messaging?hours=168&source=instantly"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "sent": 5432,
      "delivered": 5198,
      "opened": 2145,
      "clicked": 234,
      "replied": 89,
      "bounced": 234,
      "openRate": 41.27,
      "clickThroughRate": 10.91,
      "replyRate": 1.64,
      "timeWindow": "168h"
    },
    "campaigns": [
      {
        "campaignId": "camp_outbound_001",
        "campaignName": "Q4 SaaS Outreach",
        "source": "instantly",
        "sent": 1234,
        "delivered": 1198,
        "opened": 512,
        "replied": 34,
        "openRate": 43,
        "replyRate": 3,
        "startedAt": "2025-10-07T08:00:00.000Z",
        "lastActivity": "2025-10-14T12:15:00.000Z"
      }
    ],
    "trend": [
      {
        "hour": "2025-10-14T11:00:00.000Z",
        "sent": 234,
        "opened": 98,
        "replied": 5,
        "openRate": 42
      }
    ]
  },
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `marketing.campaign_metrics`

---

### 7. Analytics - Error Trend

**GET** `/neon/analytics/error-trend`

Error trend data over time by severity for charting.

**Query Parameters:**
- `hours` (optional, default: 24): Time window in hours

**Sample Request:**
```bash
curl http://localhost:3000/neon/analytics/error-trend?hours=72
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2025-10-14T11:00:00.000Z",
      "total": 23,
      "critical": 2,
      "high": 5,
      "medium": 12,
      "low": 4,
      "resolved": 18,
      "unresolved": 5
    }
  ],
  "timeWindow": "72h",
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.master_error_log`

---

### 8. Analytics - Doctrine Compliance

**GET** `/neon/analytics/doctrine-compliance`

Barton Doctrine compliance metrics by process stage (input/middle/output).

**Query Parameters:**
- `hours` (optional, default: 168): Time window in hours (default 7 days)

**Sample Request:**
```bash
curl http://localhost:3000/neon/analytics/doctrine-compliance?hours=168
```

**Response:**
```json
{
  "success": true,
  "data": {
    "byStage": [
      {
        "stage": "input",
        "totalProcesses": 1234,
        "completed": 1198,
        "failed": 36,
        "completionRate": 97.08,
        "avgDurationSeconds": 8.4
      },
      {
        "stage": "middle",
        "totalProcesses": 1198,
        "completed": 1156,
        "failed": 42,
        "completionRate": 96.49,
        "avgDurationSeconds": 15.2
      },
      {
        "stage": "output",
        "totalProcesses": 1156,
        "completed": 1098,
        "failed": 58,
        "completionRate": 94.98,
        "avgDurationSeconds": 12.7
      }
    ],
    "overall": {
      "totalProcesses": 3588,
      "avgCompletionRate": 96
    }
  },
  "timeWindow": "168h",
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.process_registry`

---

### 9. Analytics - Latency

**GET** `/neon/analytics/latency`

System latency and performance metrics with percentiles.

**Query Parameters:**
- `hours` (optional, default: 24): Time window in hours

**Sample Request:**
```bash
curl http://localhost:3000/neon/analytics/latency?hours=24
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2025-10-14T11:00:00.000Z",
      "processCount": 123,
      "avgLatencyMs": 245,
      "minLatencyMs": 45,
      "maxLatencyMs": 3420,
      "p50LatencyMs": 198,
      "p95LatencyMs": 890,
      "p99LatencyMs": 1420
    }
  ],
  "timeWindow": "24h",
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.process_registry`

---

### 10. Analytics - Data Quality

**GET** `/neon/analytics/data-quality`

Data quality metrics over time based on integrity audits.

**Query Parameters:**
- `hours` (optional, default: 168): Time window in hours (default 7 days)

**Sample Request:**
```bash
curl http://localhost:3000/neon/analytics/data-quality?hours=168
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2025-10-14T00:00:00.000Z",
      "totalChecks": 234,
      "passed": 227,
      "failed": 7,
      "avgFailureRate": 1.2,
      "passRate": 97.01
    }
  ],
  "timeWindow": "168h",
  "timestamp": "2025-10-14T12:30:45.123Z"
}
```

**Database Table:** `shq.integrity_audit`

---

## Error Handling

All endpoints follow a consistent error response format:

**Error Response (500):**
```json
{
  "success": false,
  "error": "Failed to fetch dashboard summary",
  "source": "neon",
  "details": "Connection timeout after 30s" // Only in development mode
}
```

**Validation Error (400):**
```json
{
  "success": false,
  "error": "Invalid severity parameter",
  "details": "Severity must be one of: CRITICAL, HIGH, MEDIUM, LOW"
}
```

**Not Found (404):**
```json
{
  "success": false,
  "error": "Error not found",
  "errorId": "err_invalid_id"
}
```

---

## Environment Setup

### Required Environment Variable

Add to your `.env` file:

```bash
# Neon Database Connection
NEON_DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

### Installation

Install the Neon serverless driver:

```bash
npm install @neondatabase/serverless
```

---

## Testing

### Local Testing

1. Start the API server:
```bash
cd apps/api
npm run dev
```

2. Test health endpoint:
```bash
curl http://localhost:3000/neon/health
```

3. Test dashboard summary:
```bash
curl http://localhost:3000/neon/dashboard-summary?hours=24
```

### Sample Test Script

```bash
#!/bin/bash
BASE_URL="http://localhost:3000/neon"

echo "Testing Neon API endpoints..."

# Health check
curl -s "$BASE_URL/health" | jq

# Dashboard summary
curl -s "$BASE_URL/dashboard-summary?hours=24" | jq

# Errors (unresolved only)
curl -s "$BASE_URL/errors?resolved=false&limit=10" | jq

# Integrity audit
curl -s "$BASE_URL/integrity?hours=168" | jq

# Missing data
curl -s "$BASE_URL/missing?severity=critical" | jq

# Messaging metrics
curl -s "$BASE_URL/messaging?hours=168" | jq

# Analytics - error trend
curl -s "$BASE_URL/analytics/error-trend?hours=72" | jq

# Analytics - doctrine compliance
curl -s "$BASE_URL/analytics/doctrine-compliance" | jq

# Analytics - latency
curl -s "$BASE_URL/analytics/latency?hours=24" | jq

# Analytics - data quality
curl -s "$BASE_URL/analytics/data-quality?hours=168" | jq
```

---

## Integration with Firebase UI

### Fetch Dashboard Summary

```typescript
// apps/barton-outreach-firebase/src/hooks/useDashboardData.ts
import { useEffect, useState } from 'react';

interface DashboardData {
  errorStats: { critical: number; high: number; /* ... */ };
  processStats: { total: number; completed: number; /* ... */ };
  agentStats: { total: number; active: number; /* ... */ };
  performanceMetrics: { avgLatencyMs: number; /* ... */ };
}

export function useDashboardData(hours = 24) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/neon/dashboard-summary?hours=${hours}`
        );
        const result = await response.json();

        if (result.success) {
          setData(result.data);
        } else {
          throw new Error(result.error);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [hours]);

  return { data, loading, error };
}
```

### Environment Variable

Add to Firebase app `.env`:

```bash
VITE_API_URL=http://localhost:3000
# or in production:
# VITE_API_URL=https://your-render-deployment.onrender.com
```

---

## Database Schema Reference

### shq.master_error_log
- Stores all system errors with severity, resolution status, and pattern matching
- Columns: `error_id`, `occurred_at`, `resolved_at`, `process_id`, `blueprint_id`, `agent_id`, `stage`, `severity`, `error_type`, `message`, etc.

### shq.process_registry
- Tracks all processes through input/middle/output stages
- Columns: `process_id`, `stage`, `status`, `created_at`, `completed_at`, etc.

### shq.integrity_audit
- Data quality audit results
- Columns: `audit_id`, `audited_at`, `data_source`, `table_name`, `check_name`, `status`, `records_checked`, `records_failed`, `failure_rate`, etc.

### shq.missing_data_registry
- Tracks missing or incomplete data fields
- Columns: `id`, `detected_at`, `resolved_at`, `entity_type`, `entity_id`, `missing_field`, `severity`, `impact_description`, etc.

### marketing.campaign_metrics
- Outbound messaging campaign performance
- Columns: `campaign_id`, `campaign_name`, `source`, `created_at`, `status`, `opened_at`, `clicked_at`, `replied_at`, etc.

---

## Deployment

### Render Deployment

1. Update `render.yaml` (if exists) or create new service in Render dashboard
2. Set environment variable `NEON_DATABASE_URL`
3. Deploy from GitHub repository
4. Update Firebase app environment variable with production API URL

### Verify Deployment

```bash
curl https://your-render-deployment.onrender.com/neon/health
```

---

## Support & Troubleshooting

### Common Issues

**Connection Timeout:**
- Verify `NEON_DATABASE_URL` is correct
- Check Neon database is accessible (not paused)
- Verify SSL mode is enabled

**No Data Returned:**
- Tables may not have data yet
- Check time window parameters (try larger `hours` value)
- Verify schema names match: `shq.*`, `marketing.*`

**404 Endpoint Not Found:**
- Verify routes are registered in `server.js`
- Check endpoint path spelling
- Ensure Neon router is mounted at `/neon`

---

## Barton Doctrine Alignment

All endpoints follow **Barton Altitude 10000 (Execution Layer)** standards:
- **Doctrine ID:** `03.01.01.07.10000.*`
- **Purpose:** Real-time operational data delivery
- **Query Target:** Specific Neon tables and views
- **Response Format:** Standardized JSON with `success`, `data`, `timestamp`
- **Error Handling:** Consistent error objects with source attribution

---

**Last Updated:** October 14, 2025
**Version:** 1.0.0
**Maintainer:** Barton Outreach Core Team
