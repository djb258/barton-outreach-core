# Using the Outreach Orchestrators

## Overview

The Barton Outreach Core orchestration system coordinates multi-branch workflows for lead processing, message composition, and delivery management. The system runs as a separate Node.js worker process and communicates via webhooks and API endpoints.

## Important Architecture Notes

- **Do not call orchestrators from React pages** - The orchestration system runs in the worker process (`server/index.ts`), not in the browser
- **State Management** - All orchestrator state is maintained in the worker process; React components should use the API endpoints to check status
- **Process Key Enforcement** - Master orchestrator enforces Barton IDs via `shq_process_key_reference`; unmapped IDs will error out

## Workflow Types

| Workflow | Description | Branches Used |
|----------|-------------|---------------|
| `full_pipeline` | Complete lead → messaging → delivery flow | Lead, Messaging, Delivery |
| `lead_only` | Lead ingestion and validation only | Lead |
| `messaging_only` | Message composition and approval | Messaging |
| `custom` | User-defined workflow configuration | Configurable |

## Webhook Endpoints

### Apify (Lead Scraping)
```bash
POST /webhooks/apify
Content-Type: application/json

{
  "event": "scrape_done" | "scrape_failed",
  "payload": {
    "slot_ids": ["slot_123", "slot_456"],
    "contacts": [...],
    "unique_id": "04.01.01.04.20000.003",
    "process_id": "PLE-001"
  }
}
```

### Delivery Providers (Instantly/HeyReach)
```bash
POST /webhooks/delivery
Content-Type: application/json

{
  "event": "send_result" | "reply_event" | "bounce_event",
  "payload": {
    "message_ids": ["msg_123"],
    "success": true,
    "external_id": "instantly_abc123",
    "unique_id": "04.01.01.04.20000.003"
  }
}
```

### Email Validation (MillionVerifier)
```bash
POST /webhooks/validator
Content-Type: application/json

{
  "event": "validate_result",
  "payload": {
    "results": [
      {
        "person_id": "person_123",
        "email": "test@example.com",
        "status": "valid",
        "score": 0.95
      }
    ]
  }
}
```

### Provider-Specific Webhooks

#### Instantly
```bash
POST /webhooks/instantly
{
  "event_type": "email_opened" | "email_clicked" | "email_replied",
  "data": { ... }
}
```

#### HeyReach
```bash
POST /webhooks/heyreach
{
  "type": "message_sent" | "message_replied",
  "payload": { ... }
}
```

## Manual Testing

### CLI Usage
```bash
# Basic workflows
npm run kickoff lead_only
npm run kickoff full_pipeline
npm run kickoff messaging_only

# With environment variables
BLUEPRINT_ID=PLE-002 BATCH_SIZE=25 npm run kickoff lead_only

# Show help
npm run kickoff --help
```

### Environment Variables
```bash
# Required
NEON_DATABASE_URL=postgresql://...
BLUEPRINT_ID=PLE-001
LEAD_UNIQUE_ID=04.01.01.04.20000.003

# Optional
TEST_COMPANY_ID=cmp_12345
BATCH_SIZE=50
CSV_FILE_PATH=/path/to/leads.csv

# Lead Processing
INCLUDE_CEO=true
INCLUDE_CFO=true  
INCLUDE_HR=true
VALIDATION_PROVIDER=MillionVerifier
VALIDATION_THRESHOLD=0.8

# Rate Limits
EMAIL_RATE_LIMIT=100
LINKEDIN_RATE_LIMIT=50
```

## API Endpoints

### System Status
```bash
GET /health
# Returns orchestration system status and health

GET /webhooks/status  
# Returns detailed system status including branch progress
```

### Manual Workflow Triggers
```bash
POST /webhooks/trigger/full_pipeline
Content-Type: application/json

{
  "batch_size": 25,
  "blueprint_id": "PLE-001",
  "unique_id": "04.01.01.04.20000.003"
}
```

## Process Key Reference

All workflow steps must have corresponding entries in `shq_process_key_reference`:

| Field | Description | Example |
|-------|-------------|---------|
| `unique_id` | Barton process step identifier | `04.01.01.04.20000.003` |
| `process_id` | Blueprint identifier | `PLE-001` |
| `blueprint_version_hash` | Version hash | `v1.0.0` |
| `human_description` | Step description | `Lead Intake - Email Validation` |
| `branch_id` | Orchestrator branch | `01-lead-intake` |
| `step_name` | Step name within branch | `validate_emails` |

**Critical**: Unmapped `unique_id` values will cause workflow failures. Ensure all process steps are registered before execution.

## Error Handling

### Common Error Scenarios

1. **Unmapped Process Keys**
   - Error: `UNMAPPED UNIQUE_ID: xyz not found in shq_process_key_reference`
   - Solution: Insert missing mapping in database

2. **Database Connection Issues**
   - Check `NEON_DATABASE_URL` environment variable
   - Verify database accessibility from worker process

3. **Rate Limit Violations**
   - Check `shq_guardrails` table for current limits
   - Adjust rate limit configuration in orchestrator config

4. **Webhook Timeout**
   - Webhooks have 30-second timeout
   - Long-running processes should use async processing

### Debugging

```bash
# Check orchestrator logs
docker logs <worker-container>

# Check system status
curl http://localhost:8080/health

# Check webhook processing
curl http://localhost:8080/webhooks/status
```

## Development Setup

```bash
# Start worker in development
npm run dev

# Run specific workflow test
npm run test:lead

# Full pipeline test
npm run test:full
```

## Production Deployment

1. **Environment Setup**
   - Set all required environment variables
   - Ensure database connectivity
   - Configure webhook URLs in external services

2. **Health Monitoring**
   - Monitor `/health` endpoint
   - Set up alerts for orchestration failures
   - Track processing metrics via system status

3. **Scaling Considerations**
   - Orchestrators run in single worker process
   - Use horizontal scaling for multiple workers
   - Implement proper load balancing for webhooks