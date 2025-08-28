# Validation Provider Contract (20k)

**Altitude**: 20k (Design only - no implementation)
**Status**: MillionVerifier API contract specification with mock examples

## Overview

This document defines the contract interface with email validation providers, specifically MillionVerifier as the primary service. All examples are mock/design-only and represent the expected API structure.

## MillionVerifier API Contract

### Authentication
```http
POST /api/v3/verify
Content-Type: application/json
Authorization: Bearer {API_KEY}
```

### Single Email Validation

#### Request Format
```json
{
  "email": "john.smith@acme.com",
  "timeout": 10,
  "quality_score": true,
  "disposable": true,
  "role_account": true,
  "free_provider": true,
  "mx_check": true
}
```

#### Response Format (Success)
```json
{
  "email": "john.smith@acme.com",
  "result": "ok",
  "result_code": 1,
  "reason": "mailbox_exists",
  "disposable": false,
  "role_account": false,
  "free_provider": false,
  "accept_all": false,
  "mx_found": true,
  "mx_record": "mail.acme.com",
  "smtp_check": true,
  "quality_score": 95,
  "estimated_time_sec": 2.3,
  "credits_used": 1,
  "request_id": "req_abc123def456"
}
```

#### Response Format (Invalid)
```json
{
  "email": "invalid.email@nonexistent-domain-12345.com",
  "result": "invalid",
  "result_code": 4,
  "reason": "no_mx_record",
  "disposable": false,
  "role_account": false,
  "free_provider": false,
  "accept_all": false,
  "mx_found": false,
  "mx_record": null,
  "smtp_check": false,
  "quality_score": 0,
  "estimated_time_sec": 0.8,
  "credits_used": 1,
  "request_id": "req_xyz789ghi012"
}
```

### Bulk Email Validation

#### Batch Request Format
```json
{
  "batch_id": "batch_20240828_001",
  "emails": [
    {
      "id": "person_001",
      "email": "ceo@techcorp.com"
    },
    {
      "id": "person_002", 
      "email": "cfo@innovate.io"
    },
    {
      "id": "person_003",
      "email": "hr@startup.net"
    }
  ],
  "callback_url": "https://our-api.render.com/validation/callback",
  "timeout": 30,
  "quality_score": true,
  "advanced_syntax": true
}
```

#### Batch Submission Response
```json
{
  "batch_id": "batch_20240828_001",
  "status": "processing",
  "total_emails": 3,
  "estimated_completion_minutes": 5,
  "credits_estimated": 3,
  "webhook_url": "https://our-api.render.com/validation/callback",
  "status_check_url": "https://api.millionverifier.com/api/v3/batches/batch_20240828_001/status"
}
```

#### Batch Results Response
```json
{
  "batch_id": "batch_20240828_001",
  "status": "completed",
  "processed_at": "2024-08-28T15:45:00Z",
  "total_emails": 3,
  "credits_used": 3,
  "processing_time_seconds": 287,
  "results": [
    {
      "id": "person_001",
      "email": "ceo@techcorp.com",
      "result": "ok",
      "result_code": 1,
      "reason": "mailbox_exists",
      "quality_score": 92,
      "disposable": false,
      "role_account": false,
      "mx_found": true
    },
    {
      "id": "person_002",
      "email": "cfo@innovate.io", 
      "result": "risky",
      "result_code": 3,
      "reason": "low_quality",
      "quality_score": 67,
      "disposable": false,
      "role_account": true,
      "mx_found": true
    },
    {
      "id": "person_003",
      "email": "hr@startup.net",
      "result": "invalid", 
      "result_code": 4,
      "reason": "mailbox_not_found",
      "quality_score": 15,
      "disposable": false,
      "role_account": false,
      "mx_found": true
    }
  ],
  "summary": {
    "valid": 1,
    "invalid": 1,
    "risky": 1,
    "unknown": 0
  }
}
```

## Result Code Mapping

### Standard Result Codes
- **1 (ok)**: Email is valid and deliverable
- **2 (catch_all)**: Server accepts all emails (risky)
- **3 (unknown)**: Cannot determine validity (risky)
- **4 (invalid)**: Email is invalid or undeliverable
- **5 (disposable)**: Temporary/disposable email service
- **6 (role_account)**: Generic role account (info@, admin@)

### Internal Status Mapping
```javascript
// DESIGN ONLY - NO IMPLEMENTATION
const mapProviderResult = (providerCode) => {
  switch(providerCode) {
    case 1: return 'valid';
    case 2: case 3: return 'risky'; 
    case 4: case 5: return 'invalid';
    case 6: return 'valid'; // Role accounts still usable
    default: return 'error';
  }
}
```

## Error Handling

### API Error Responses
```json
{
  "error": true,
  "error_code": "INVALID_API_KEY",
  "message": "The provided API key is invalid or expired",
  "request_id": "req_error_001",
  "timestamp": "2024-08-28T15:50:00Z"
}
```

### Common Error Codes
- **INVALID_API_KEY**: Authentication failure
- **INSUFFICIENT_CREDITS**: Account balance too low
- **RATE_LIMIT_EXCEEDED**: Too many requests per minute
- **INVALID_EMAIL_FORMAT**: Malformed email in request
- **BATCH_TOO_LARGE**: Batch exceeds maximum size limit
- **SERVICE_UNAVAILABLE**: Temporary service outage

### Error Recovery Strategies
```yaml
# DESIGN ONLY - NO IMPLEMENTATION
error_handling:
  INVALID_API_KEY:
    action: "alert_admin"
    retry: false
    fallback: "manual_review"
    
  RATE_LIMIT_EXCEEDED:
    action: "implement_backoff"
    retry: true
    delay_seconds: 300
    
  SERVICE_UNAVAILABLE:
    action: "switch_provider"
    retry: true
    max_retries: 3
```

## Webhook Integration

### Callback URL Specification
Our system provides webhook endpoint for async batch results:
```
POST https://our-api.render.com/validation/callback
Content-Type: application/json
```

### Webhook Payload
```json
{
  "batch_id": "batch_20240828_001",
  "status": "completed",
  "webhook_signature": "sha256=abc123...",
  "results_url": "https://api.millionverifier.com/api/v3/batches/batch_20240828_001/results"
}
```

### Webhook Security
- **Signature Verification**: HMAC-SHA256 signature validation
- **IP Allowlisting**: Restrict webhook source IPs
- **Idempotency**: Handle duplicate webhook deliveries
- **Timeout Handling**: Fallback to polling if webhook fails

## Rate Limiting & Quotas

### API Rate Limits
- **Single Email**: 10 requests/second
- **Batch Submission**: 5 batches/minute
- **Status Checks**: 60 requests/minute
- **Results Retrieval**: 30 requests/minute

### Credit Management
```json
{
  "account": {
    "credits_remaining": 9847,
    "credits_used_today": 153,
    "monthly_limit": 10000,
    "auto_recharge": true,
    "recharge_threshold": 1000,
    "next_billing_date": "2024-09-01"
  }
}
```

## Data Quality Features

### Advanced Validation Options
- **Syntax Check**: RFC 5322 compliance
- **MX Record Verification**: Domain has mail server
- **SMTP Validation**: Mailbox existence check  
- **Role Account Detection**: Generic vs. personal emails
- **Disposable Email Detection**: Temporary email services
- **Free Provider Detection**: Gmail, Yahoo, etc.
- **Accept-All Detection**: Catch-all mail servers

### Quality Score Calculation
```
Quality Score = Base Score (0-100)
  + MX Record Found (+10)
  + SMTP Validation (+20)  
  - Role Account (-15)
  - Free Provider (-10)
  - Disposable Email (-50)
  - Accept All Server (-25)
```

## Cost Structure

### Pricing Tiers (Mock Example)
- **0-1,000 emails**: $0.010 per email
- **1,001-5,000 emails**: $0.008 per email  
- **5,001-10,000 emails**: $0.006 per email
- **10,001+ emails**: $0.004 per email

### Cost Optimization Features
- **Bulk Discounts**: Lower per-email cost for larger batches
- **Monthly Plans**: Fixed monthly fee for high-volume users
- **Credit Rollover**: Unused credits carry to next month
- **Volume Commitments**: Annual contracts for best pricing

## Service Level Agreement

### Availability Targets
- **Uptime**: 99.9% monthly availability
- **Response Time**: <3 seconds for single email validation
- **Batch Processing**: <10 minutes for batches under 1,000 emails
- **Support Response**: <24 hours for technical issues

### Performance Monitoring
```json
{
  "service_status": {
    "status": "operational",
    "uptime_percentage": 99.95,
    "average_response_time_ms": 1847,
    "current_queue_size": 234,
    "estimated_wait_time_minutes": 2
  }
}
```

## Integration Testing

### Test Email Addresses (Provider Supplied)
```json
{
  "test_emails": {
    "valid": "test-valid@millionverifier.com",
    "invalid": "test-invalid@millionverifier.com", 
    "risky": "test-risky@millionverifier.com",
    "disposable": "test-disposable@10minutemail.com",
    "role": "test-role@millionverifier.com"
  }
}
```

### Mock Responses for Development
All responses in this document serve as mock examples for development and testing without actual API calls or charges.

## 20k Constraints

⚠️ **Design Only**: Complete API contract specification
❌ **No API Calls**: No actual validation service integration
❌ **Mock Data**: All examples are fictional/design-only
✅ **Contract Specification**: Full provider interface definition for implementation planning