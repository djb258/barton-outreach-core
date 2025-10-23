<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/nodes
Barton ID: 04.04.22
Unique ID: CTB-6C8BCAA3
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# Error Model Design (20k)

**Altitude**: 20k (Design only - no implementation)
**Status**: Error taxonomy, shapes, and retry classification

## Overview

This document defines the comprehensive error model for the Render-for-DB API, including error shapes, classification of retryable vs. fatal errors, and error handling strategies for different failure scenarios.

## Error Shape Standard

### Base Error Structure
All API errors follow a consistent JSON structure:

```json
{
  "error_code": "MACHINE_READABLE_CODE",
  "message": "Human-readable description",
  "details": {
    "field": "problematic_field",
    "value": "invalid_value", 
    "constraint": "validation_rule"
  },
  "request_id": "req_unique_identifier",
  "timestamp": "2024-08-28T15:30:00Z",
  "retry_after": 60,
  "documentation_url": "https://docs.render-for-db.com/errors/MACHINE_READABLE_CODE"
}
```

### Required Fields
- **error_code**: Machine-readable error identifier (UPPER_SNAKE_CASE)
- **message**: Human-readable error description
- **request_id**: Unique request identifier for debugging/tracing

### Optional Fields  
- **details**: Additional context object (varies by error type)
- **timestamp**: Error occurrence time (ISO 8601 format)
- **retry_after**: Seconds to wait before retry (for rate limits/temporary errors)
- **documentation_url**: Link to error-specific documentation

## Error Categories

### 1. Client Errors (4xx)

#### Authentication Errors
```json
{
  "error_code": "INVALID_API_KEY",
  "message": "The provided API key is invalid or expired",
  "details": {
    "key_format": "Expected format: rdb_[32_chars]",
    "expiration_policy": "Keys expire after 90 days"
  },
  "request_id": "req_auth_001"
}
```

```json
{
  "error_code": "API_KEY_EXPIRED", 
  "message": "API key has expired and needs renewal",
  "details": {
    "expired_at": "2024-08-01T00:00:00Z",
    "renewal_url": "https://dashboard.render-for-db.com/api-keys"
  },
  "request_id": "req_auth_002"
}
```

#### Validation Errors
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "email",
        "value": "invalid-email",
        "constraint": "format",
        "message": "Must be valid email format"
      },
      {
        "field": "company_uid",
        "value": "INVALID-123",
        "constraint": "pattern",
        "message": "Must match pattern: CO-YYYYMMDD-######"
      }
    ]
  },
  "request_id": "req_val_001"
}
```

#### Business Logic Errors
```json
{
  "error_code": "COMPANY_NOT_FOUND",
  "message": "Referenced company does not exist",
  "details": {
    "company_uid": "CO-20240828-999999",
    "suggestion": "Verify company_uid or create company first"
  },
  "request_id": "req_biz_001"
}
```

```json
{
  "error_code": "SLOT_CONFLICT",
  "message": "Target slot is already occupied by another person",
  "details": {
    "slot_uid": "SL-CO-20240828-000001-CEO",
    "current_occupant": "PE-20240801-000123",
    "resolution_options": ["force_reassign", "assign_to_different_slot", "manual_review"]
  },
  "request_id": "req_biz_002"
}
```

### 2. Server Errors (5xx)

#### Temporary Server Errors
```json
{
  "error_code": "TEMPORARY_UNAVAILABLE",
  "message": "Service temporarily unavailable due to maintenance",
  "details": {
    "maintenance_window": "2024-08-28T02:00:00Z to 2024-08-28T04:00:00Z",
    "expected_resolution": "2024-08-28T04:00:00Z"
  },
  "retry_after": 3600,
  "request_id": "req_temp_001"
}
```

#### Database Errors
```json
{
  "error_code": "DATABASE_CONNECTION_ERROR",
  "message": "Unable to connect to database",
  "details": {
    "database": "neon_primary",
    "error_type": "connection_timeout",
    "retry_recommended": true
  },
  "retry_after": 30,
  "request_id": "req_db_001"
}
```

#### External Service Errors
```json
{
  "error_code": "VALIDATION_SERVICE_ERROR",
  "message": "Email validation service unavailable", 
  "details": {
    "provider": "millionverifier",
    "provider_error": "service_maintenance",
    "fallback_available": true,
    "fallback_provider": "zerobounce"
  },
  "retry_after": 300,
  "request_id": "req_ext_001"
}
```

## Error Classification

### Retryable Errors
Errors that may succeed if retried with appropriate backoff:

#### Immediate Retry (No Delay)
- `NETWORK_TIMEOUT` - Temporary network issue
- `CONNECTION_RESET` - Network connection interrupted

#### Short Delay Retry (1-5 minutes)
- `DATABASE_CONNECTION_ERROR` - Database temporarily unavailable
- `EXTERNAL_SERVICE_TIMEOUT` - External API timeout
- `TEMPORARY_UNAVAILABLE` - Service maintenance

#### Long Delay Retry (15+ minutes)  
- `RATE_LIMIT_EXCEEDED` - API rate limit hit
- `QUOTA_EXCEEDED` - Daily/monthly quota reached
- `SERVICE_OVERLOADED` - High system load

### Fatal Errors (Non-Retryable)
Errors that will not succeed on retry without fixing the request:

#### Client Configuration Errors
- `INVALID_API_KEY` - Authentication failure
- `API_KEY_EXPIRED` - Expired credentials
- `INSUFFICIENT_PERMISSIONS` - Access denied

#### Request Format Errors
- `VALIDATION_ERROR` - Invalid request data
- `MALFORMED_JSON` - Invalid JSON syntax
- `UNSUPPORTED_CONTENT_TYPE` - Wrong content type header

#### Business Logic Errors
- `COMPANY_NOT_FOUND` - Referenced entity doesn't exist
- `DUPLICATE_RECORD` - Record already exists (with different idempotency key)
- `BUSINESS_RULE_VIOLATION` - Request violates business constraints

### Conditional Retry Errors
Errors that may be retryable depending on context:

- `SLOT_CONFLICT` - May resolve if other process frees slot
- `VALIDATION_QUEUE_FULL` - May resolve when queue processes
- `IDEMPOTENCY_CONFLICT` - Fatal if payloads different, retryable if same

## Retry Strategy Design

### Exponential Backoff Algorithm
```javascript
// DESIGN ONLY - NO IMPLEMENTATION
const calculateBackoff = (attempt, baseDelay = 1000, maxDelay = 300000) => {
  const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
  const jitter = Math.random() * 0.1 * exponentialDelay;
  return Math.min(exponentialDelay + jitter, maxDelay);
};
```

### Retry Configuration by Error Type
```yaml
# DESIGN ONLY - NO IMPLEMENTATION
retry_policies:
  NETWORK_TIMEOUT:
    max_attempts: 5
    base_delay_ms: 100
    max_delay_ms: 5000
    backoff_multiplier: 1.5
    
  DATABASE_CONNECTION_ERROR:
    max_attempts: 3
    base_delay_ms: 1000  
    max_delay_ms: 60000
    backoff_multiplier: 2.0
    
  RATE_LIMIT_EXCEEDED:
    max_attempts: 3
    base_delay_ms: 60000
    max_delay_ms: 900000
    respect_retry_after: true
    
  VALIDATION_ERROR:
    max_attempts: 0  # No retry
    fatal: true
```

## Error Context Enrichment

### Request Tracing
- **request_id**: Unique identifier per request
- **trace_id**: Distributed tracing identifier  
- **user_agent**: Client identification
- **api_version**: API version used
- **endpoint**: Specific endpoint called

### Environmental Context
- **timestamp**: Exact error occurrence time
- **server_id**: Which server instance handled request
- **database_shard**: Which database shard was involved
- **external_service**: Which external service caused error (if applicable)

### User Context (when available)
- **api_key_id**: Obfuscated API key identifier
- **account_id**: Customer account (if available)
- **request_source**: Origin of request (ingest-repo, direct API, etc.)

## Error Monitoring & Alerting

### Error Metrics
- **Error Rate**: Percentage of requests resulting in errors
- **Error Distribution**: Count by error_code
- **Response Time Impact**: How errors affect response times
- **Retry Success Rate**: Percentage of retries that succeed

### Alert Thresholds
```yaml
# DESIGN ONLY - NO IMPLEMENTATION
alerts:
  high_error_rate:
    condition: "error_rate > 5%"
    window: "5_minutes"
    action: "slack_alert"
    
  database_errors:
    condition: "database_errors > 10 in 1_minute"
    action: "page_on_call"
    
  external_service_down:
    condition: "external_service_errors > 20 in 5_minutes"
    action: "switch_provider"
```

## Error Documentation

### Error Code Registry
Maintain centralized registry of all error codes with:
- **Description**: What the error means
- **Causes**: Common reasons for this error
- **Resolution**: How to fix the issue
- **Examples**: Sample error responses
- **Related Errors**: Similar or related error codes

### Client SDK Integration
Error codes designed for easy client SDK integration:

```javascript
// DESIGN ONLY - NO IMPLEMENTATION  
class RenderDBError extends Error {
  constructor(errorResponse) {
    super(errorResponse.message);
    this.code = errorResponse.error_code;
    this.details = errorResponse.details;
    this.requestId = errorResponse.request_id;
    this.retryable = this.isRetryable(errorResponse.error_code);
  }
  
  isRetryable(errorCode) {
    const retryableCodes = [
      'NETWORK_TIMEOUT',
      'DATABASE_CONNECTION_ERROR', 
      'RATE_LIMIT_EXCEEDED',
      'TEMPORARY_UNAVAILABLE'
    ];
    return retryableCodes.includes(errorCode);
  }
}
```

## Error Response Examples

### Complete Success Response (for comparison)
```json
{
  "company_uid": "CO-20240828-000001",
  "status": "created",
  "slots_created": 3,
  "created_at": "2024-08-28T15:30:00Z",
  "request_id": "req_success_001"
}
```

### Complete Error Response
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed on multiple fields",
  "details": {
    "errors": [
      {
        "field": "name",
        "value": "",
        "constraint": "required",
        "message": "Company name is required"
      },
      {
        "field": "website", 
        "value": "not-a-url",
        "constraint": "format",
        "message": "Website must be valid URL"
      }
    ],
    "total_errors": 2
  },
  "request_id": "req_val_error_001",
  "timestamp": "2024-08-28T15:30:00Z",
  "documentation_url": "https://docs.render-for-db.com/errors/VALIDATION_ERROR"
}
```

## Integration with External Systems

### Ingest Repository Error Handling
- Map external errors to internal error codes
- Preserve original error context in details
- Add retry recommendations for ingest processes

### Scraper Repository Integration
- Handle scraping failures gracefully
- Differentiate between rate limits and data unavailability
- Provide fallback strategies for critical scraping errors

### Neon Database Error Mapping
- Translate database-specific errors to generic codes
- Handle connection pool exhaustion
- Manage transaction rollback scenarios

## 20k Constraints

⚠️ **Design Only**: Complete error model specification
❌ **No Implementation**: No actual error handling code
❌ **No Monitoring**: No actual alerting or metrics collection
✅ **Design Framework**: Comprehensive error taxonomy and handling strategy