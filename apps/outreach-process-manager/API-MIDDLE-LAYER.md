# Outreach Process Manager - Middle Layer API

## Overview

The Middle Layer (M in IMO) connects the Rocket.new UI to Composio MCP tools for Neon database operations. All database logic goes through Composio MCP → Neon with no direct database connections.

## Architecture

```
┌──────────────────┐
│   Rocket.new UI  │ (Input/Output)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Middle Layer    │ (Orchestration)
│   API Endpoints  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Composio MCP    │
│     Bridge       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Neon Database   │
│   PostgreSQL     │
└──────────────────┘
```

## API Endpoints

### 1. `/api/ingest` - CSV Data Ingestion

**Method:** POST

**Purpose:** Accepts parsed CSV rows from Rocket UI and ingests them into `marketing.company_raw_intake`

**Request Body:**
```json
{
  "rows": [
    {
      "company_name": "Example Corp",
      "industry": "Technology",
      "employees": 500,
      // ... other fields
    }
  ],
  "metadata": {
    "source": "csv_upload",
    "uploaded_by": "user@example.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "rows_ingested": 10,
  "rows_validated": 8,
  "rows_failed": 2,
  "error_log": [
    {
      "step": "validation",
      "row": 5,
      "field": "email",
      "message": "Invalid email format",
      "severity": "error",
      "doctrine_violation": false,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "step_unique_ids": ["BTN_1234_ABC", "BTN_1234_DEF"],
  "barton_doctrine": {
    "process_id": "PROC_20240101_1234_ABC",
    "altitude": "middle_layer",
    "timestamp": "2024-01-01T12:00:00Z",
    "completion_timestamp": "2024-01-01T12:00:05Z",
    "total_processing_time_ms": 5000
  }
}
```

### 2. `/api/promote` - Data Promotion

**Method:** POST

**Purpose:** Promotes validated data from `company_raw_intake` to `company` table

**Request Body:**
```json
{
  "filter": {
    "validated": true,
    "created_after": "2024-01-01"
  },
  "sourceTable": "marketing.company_raw_intake",
  "targetTable": "marketing.company",
  "limit": 1000
}
```

**Response:**
```json
{
  "success": true,
  "rows_promoted": 50,
  "promotion_timestamp": "2024-01-01T12:00:00Z",
  "promoted_unique_ids": ["BTN_1234_ABC", "BTN_1234_DEF"],
  "slot_creation_triggered": true,
  "slot_details": {
    "slots_created": 50,
    "slot_type": "company_slot",
    "slot_status": "active"
  },
  "barton_doctrine": {
    "process_id": "PROC_20240101_5678_XYZ",
    "altitude": "promotion_layer",
    "source_altitude": "raw_intake",
    "target_altitude": "production"
  },
  "audit_trail": {
    "promoted_by": "middle_layer_orchestration",
    "promotion_method": "composio_mcp_neon",
    "verification_status": "verified"
  }
}
```

## Barton Doctrine Metadata

Every response includes Barton Doctrine metadata:

- **unique_id**: Unique identifier with BTN prefix
- **process_id**: Process tracking ID
- **altitude**: Data elevation level
  - `ground_level`: Raw data
  - `low_altitude`: Raw intake
  - `mid_altitude`: Validated
  - `high_altitude`: Production
  - `cruising_altitude`: Promoted
  - `stratosphere`: Archived

## STAMPED Compliance

All data follows STAMPED doctrine:
- **S**ource: Origin of data
- **T**imestamp: When data was created/modified
- **A**ctor: Who/what performed the action
- **M**ethod: How the action was performed
- **P**rocess: Process ID for tracking
- **E**nvironment: Execution environment
- **D**ata: Additional metadata

## Composio MCP Operations

All database operations go through Composio MCP tools:

1. **neon.insert_rows**: Insert data into tables
2. **neon.validate_schema**: Validate against STAMPED
3. **neon.promote_rows**: Move data between tables
4. **neon.query_rows**: Query data with filters
5. **neon.execute_sql**: Execute custom SQL

## UI Component Integration

The API responses are designed to update these UI components:

- **ProcessingStatusPanel**: Shows ingestion state
- **ValidationResultsTable**: Displays row-level validation results
- **WorkflowSidebar**: Shows doctrine step completion
- **IntegrationStatusIndicator**: Displays connection status

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message",
  "barton_doctrine": {
    "process_id": "PROC_ERROR_123",
    "altitude": "error_layer",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Environment Variables

Required configuration:

```env
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
COMPOSIO_BASE_URL=https://backend.composio.dev
NEON_DATABASE_URL=postgresql://user:pass@host/db
NEON_CONNECTION_ID=neon_barton_outreach
MCP_SERVER_URL=http://localhost:3001
```

## Testing

Test the endpoints with curl:

```bash
# Test ingest endpoint
curl -X POST http://localhost:3000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"rows":[{"company_name":"Test Corp"}]}'

# Test promote endpoint
curl -X POST http://localhost:3000/api/promote \
  -H "Content-Type: application/json" \
  -d '{"filter":{"validated":true}}'
```

## Implementation Notes

1. **No Direct DB Connections**: All operations go through Composio MCP
2. **Orchestration Only**: Middle layer only orchestrates, doesn't process
3. **JSON Responses**: All responses are JSON for UI consumption
4. **Metadata Rich**: Every response includes Barton Doctrine metadata
5. **Error Resilient**: Graceful error handling with detailed logging