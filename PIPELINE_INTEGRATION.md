# Complete Pipeline Integration: Ingestor → Neon → Apify → PLE → Bit

This document describes the complete data pipeline integration for Barton Outreach Core, connecting all components from data ingestion to component sharing.

## Pipeline Overview

```
Ingestor → Neon → Apify → PLE → Bit
   ↓        ↓      ↓     ↓    ↓
 Data    Store   Scrape Process Share
 Input   in DB   More   with   Code
                 Data   Logic  Components
```

## Components

### 1. Ingestor (ingest-companies-people app)
- **Purpose**: Front-end application for data input and CSV uploads
- **Location**: `C:\Users\CUSTOMER PC\Cursor Repo\ingest-companies-people`
- **Integration**: Sends data to Barton Outreach Core API endpoints
- **API Endpoint**: `http://localhost:3000/insert` and `/pipeline/execute`

### 2. Neon Database
- **Purpose**: PostgreSQL database for storing and processing data
- **Connection**: Via Composio MCP (primary) with PostgreSQL fallback
- **Schemas**: `intake` (raw data), `vault` (processed data)
- **Environment**: `NEON_DATABASE_URL` in `.env`

### 3. Apify Integration
- **Purpose**: Web scraping for additional contact data
- **Client**: `ApifyMCPClient` (`packages/mcp-clients/src/clients/apify-mcp-client.ts`)
- **Features**: LinkedIn scraping, website email extraction
- **Environment**: `APIFY_API_KEY` in `.env`

### 4. PLE (Pipeline Logic Engine)
- **Purpose**: Orchestrates the complete data flow and business logic
- **Orchestrator**: `PLEOrchestrator` (`packages/mcp-clients/src/clients/ple-orchestrator.ts`)
- **Features**: Data promotion, validation, error handling
- **Environment**: `PLE_*` settings in `.env`

### 5. Bit.dev Integration
- **Purpose**: Component sharing and version management
- **Client**: `BitMCPClient` (`packages/mcp-clients/src/clients/bit-mcp-client.ts`)
- **Features**: Auto-generate React components from data
- **Environment**: `BIT_TOKEN` and `BIT_SCOPE` in `.env`

## API Endpoints

### Complete Pipeline Execution
```http
POST /pipeline/execute
Content-Type: application/json

{
  "data": [
    {
      "email": "contact@example.com",
      "name": "John Doe",
      "company": "Example Corp",
      "website": "https://example.com"
    }
  ],
  "jobConfig": {
    "jobId": "pipeline_123",
    "source": "api",
    "enableScraping": true,
    "enablePromotion": true,
    "enableBitSync": false,
    "notificationWebhook": "https://webhook.example.com"
  }
}
```

### Pipeline Health Check
```http
GET /pipeline/health
```

### Pipeline Status
```http
GET /pipeline/status/{jobId}
```

## Environment Configuration

Add these variables to your `.env` file:

```bash
# ===========================================
# Composio MCP Configuration (REQUIRED)
# ===========================================
COMPOSIO_API_KEY=your_composio_key
COMPOSIO_UUID=your_composio_uuid
NEON_API_KEY=your_neon_key

# ===========================================
# Database Configuration
# ===========================================
NEON_DATABASE_URL=postgresql://...
DATABASE_URL=postgresql://...

# ===========================================
# External Service API Keys
# ===========================================
APIFY_TOKEN=your_apify_token
APIFY_API_KEY=your_apify_key

# ===========================================
# Bit.dev Configuration
# ===========================================
BIT_TOKEN=your_bit_token
BIT_SCOPE=barton-outreach

# ===========================================
# PLE (Pipeline Logic Engine) Configuration
# ===========================================
PLE_WEBHOOK_URL=https://webhook.internal/ple-notifications
PLE_BATCH_SIZE=50
PLE_MAX_RETRIES=3
```

## Data Flow

### Step 1: Data Ingestion
1. User uploads CSV or enters data in ingest-companies-people app
2. Data is sent to `/pipeline/execute` endpoint
3. PLE Orchestrator validates and processes the request

### Step 2: Neon Database Storage
1. Data is inserted into `intake.raw_loads` table via Composio MCP
2. Raw data is stored as JSONB with metadata
3. Batch tracking is enabled with unique batch IDs

### Step 3: Apify Scraping (Optional)
1. Extract website URLs from ingested data
2. Use Apify to scrape additional contact information
3. Store scraped data back to Neon database
4. Merge with original records

### Step 4: PLE Processing
1. Apply business logic and validation rules
2. Promote qualified records to `vault.contacts` table
3. Handle duplicates and data quality issues
4. Track promotion status and errors

### Step 5: Bit Component Sync (Optional)
1. Generate React components from promoted data
2. Create reusable contact cards and data displays
3. Version and publish components to Bit.dev
4. Enable component sharing across projects

## Testing

Run the complete pipeline test:

```bash
cd /path/to/barton-outreach-core
node scripts/test-complete-pipeline.mjs
```

This will test:
- Pipeline health checks
- Complete data flow execution
- Status monitoring
- Individual component functionality

## Error Handling

The pipeline includes comprehensive error handling:

1. **Network Errors**: Automatic retries with exponential backoff
2. **API Failures**: Graceful degradation with fallback mechanisms
3. **Data Validation**: Schema validation at each step
4. **Rate Limiting**: Batch processing to respect API limits
5. **Monitoring**: Real-time status tracking and notifications

## Monitoring

### Health Checks
- **Endpoint**: `GET /pipeline/health`
- **Checks**: Composio, Apify, Neon, Bit connectivity
- **Frequency**: Real-time on demand

### Job Status
- **Endpoint**: `GET /pipeline/status/{jobId}`
- **Tracking**: Records processed, promoted, failed
- **Real-time**: Live status updates during execution

### Notifications
- **Webhooks**: Configurable notification endpoints
- **Events**: Pipeline completion, errors, status changes
- **Format**: JSON with detailed execution metrics

## Performance

### Batch Processing
- **Default Size**: 50 records per batch
- **Configurable**: Via `PLE_BATCH_SIZE` environment variable
- **Rate Limiting**: Built-in delays between API calls

### Concurrent Processing
- **Database**: Connection pooling with fallback
- **API Calls**: Parallel processing where safe
- **Resource Management**: Automatic cleanup and optimization

## Security

### Authentication
- **API Keys**: Secured in environment variables
- **Database**: SSL-enabled connections with certificate validation
- **MCP**: Composio-mediated secure connections

### Data Protection
- **Encryption**: TLS for all API communications
- **Validation**: Schema validation and sanitization
- **Audit Trail**: Complete logging of all operations

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check API keys in `.env` file
   - Verify network connectivity
   - Review firewall settings

2. **Database Issues**
   - Confirm Neon database URL is correct
   - Check database permissions
   - Verify schema exists

3. **Scraping Failures**
   - Validate Apify API key
   - Check website accessibility
   - Review rate limiting settings

4. **Component Sync Issues**
   - Verify Bit.dev token
   - Check collection permissions
   - Review component templates

### Debug Mode

Enable debug logging:
```bash
NODE_ENV=development
LOG_LEVEL=debug
```

### Health Checks

Run individual health checks:
```bash
# Complete pipeline health
curl http://localhost:3000/pipeline/health

# API server health
curl http://localhost:3000/health

# Database connection
curl http://localhost:3000/db/health
```

## Future Enhancements

1. **Real-time Processing**: WebSocket connections for live updates
2. **Advanced Analytics**: Machine learning for data quality scoring
3. **Workflow Automation**: Visual pipeline designer
4. **Multi-tenant Support**: Organization-specific pipelines
5. **Data Lineage**: Complete audit trail and data provenance tracking

## Support

For issues or questions:
1. Check the health endpoints for system status
2. Review logs in development mode
3. Test individual components using the test script
4. Verify environment configuration
5. Contact the development team for advanced troubleshooting