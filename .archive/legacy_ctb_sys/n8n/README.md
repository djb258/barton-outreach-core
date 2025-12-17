# n8n Workflow Automation Integration

n8n is a powerful workflow automation platform for connecting Barton Outreach Core with external services and automating repetitive tasks.

## 🚀 Quick Start

### Option 1: Self-Hosted (Docker)

```bash
# Using docker-compose
cd ctb/sys/n8n
docker-compose up -d

# Access n8n at http://localhost:5678
```

### Option 2: n8n Cloud (Recommended)

1. Sign up at https://n8n.io
2. Create new workflow
3. Import workflows from `workflows/` directory
4. Configure credentials

### Option 3: npm Global Install

```bash
npm install n8n -g
n8n start
```

## 📁 Structure

```
n8n/
├── workflows/               # Workflow JSON exports
│   ├── outreach-pipeline.json
│   ├── error-notifications.json
│   ├── database-sync.json
│   └── linkedin-refresh.json
├── credentials/            # Credential templates (DO NOT commit actual creds)
│   ├── neon-db.json
│   ├── composio-api.json
│   └── github-api.json
├── docker-compose.yml      # Self-hosted setup
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

# Database (for workflow storage)
DB_TYPE=postgresdb
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=n8n_password

# Webhook URL (for external triggers)
WEBHOOK_URL=https://your-n8n-instance.com/webhook

# Integrations
NEON_CONNECTION_STRING=postgresql://user:pass@host/db
COMPOSIO_API_KEY=your_composio_key
GITHUB_TOKEN=your_github_token
FIREBASE_SERVICE_ACCOUNT=./path/to/service-account.json
```

## 🎯 Pre-built Workflows

### 1. Outreach Pipeline Automation

**File**: `workflows/outreach-pipeline.json`

**Trigger**: Webhook or Schedule
**Steps**:
1. Fetch new leads from Neon database
2. Enrich with LinkedIn data (via Composio/Apify)
3. Validate email addresses (Million Verifier)
4. Update database with enriched data
5. Notify team in Slack/Email

**Schedule**: Every 4 hours
**Doctrine ID**: 04.04.F1-01

### 2. Error Notification System

**File**: `workflows/error-notifications.json`

**Trigger**: Database Trigger (shq_error_log changes)
**Steps**:
1. Monitor shq_error_log table
2. Filter critical errors
3. Format error message
4. Send to Slack channel
5. Create GitHub issue if needed

**Run**: On database change
**Doctrine ID**: 04.04.F1-02

### 3. Database Sync

**File**: `workflows/database-sync.json`

**Trigger**: Schedule
**Steps**:
1. Query Neon production database
2. Transform data
3. Sync to Firebase staging
4. Update Grafana annotations
5. Log sync status

**Schedule**: Every 30 minutes
**Doctrine ID**: 04.04.F1-03

### 4. LinkedIn Profile Refresh

**File**: `workflows/linkedin-refresh.json`

**Trigger**: Manual or Schedule
**Steps**:
1. Get stale profiles from database (>30 days old)
2. Batch request to Apify LinkedIn scraper
3. Wait for results
4. Update people_master table
5. Update linkedin_refresh_jobs log

**Schedule**: Daily at 2 AM
**Doctrine ID**: 04.04.F1-04

### 5. GitHub Project Sync

**File**: `workflows/github-project-sync.json`

**Trigger**: GitHub Webhook
**Steps**:
1. Receive issue/PR event
2. Update GitHub Project fields
3. Log to database
4. Update Obsidian notes
5. Send status update

**Trigger**: GitHub webhook
**Doctrine ID**: 04.04.F1-05

## 🔌 Node Configurations

### Neon Database Node

```json
{
  "name": "Neon PostgreSQL",
  "type": "n8n-nodes-base.postgres",
  "credentials": {
    "postgres": {
      "host": "ep-xxx.us-east-2.aws.neon.tech",
      "port": 5432,
      "database": "marketing",
      "user": "your_user",
      "password": "your_password",
      "ssl": {
        "rejectUnauthorized": true
      }
    }
  }
}
```

### Composio MCP Node

```json
{
  "name": "Composio API",
  "type": "n8n-nodes-base.httpRequest",
  "credentials": {
    "httpHeaderAuth": {
      "name": "x-api-key",
      "value": "={{$credentials.composio_api_key}}"
    }
  },
  "parameters": {
    "url": "https://backend.composio.dev/api/v1/actions/execute",
    "method": "POST",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "x-api-key",
          "value": "={{$credentials.composio_api_key}}"
        }
      ]
    }
  }
}
```

### Firebase Node

```json
{
  "name": "Firebase",
  "type": "n8n-nodes-base.firebase",
  "credentials": {
    "firebaseServiceAccount": {
      "serviceAccount": "={{$json}}"
    }
  },
  "parameters": {
    "operation": "create",
    "collection": "staging",
    "dataPropertyName": "data"
  }
}
```

## 🎨 Workflow Design Patterns

### Error Handling

```javascript
// Add error workflow in every workflow
nodes.forEach(node => {
  node.continueOnFail = true;
  node.onError = "errorHandler";
});

// Error handler node
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.function",
  "parameters": {
    "functionCode": `
      const error = $input.item.json;

      // Log to shq_error_log
      await $http.post({
        url: 'http://localhost:3001/tool',
        body: {
          tool: 'LOG_ERROR',
          data: {
            unique_id: 'N8N-' + Date.now(),
            error_message: error.message,
            stack_trace: error.stack,
            context: 'n8n_workflow'
          }
        }
      });

      return $input.all();
    `
  }
}
```

### Rate Limiting

```javascript
// Add delay between API calls
{
  "name": "Rate Limit",
  "type": "n8n-nodes-base.wait",
  "parameters": {
    "time": 1,
    "unit": "seconds"
  }
}
```

### Batch Processing

```javascript
// Split large datasets into batches
{
  "name": "Batch Splitter",
  "type": "n8n-nodes-base.splitInBatches",
  "parameters": {
    "batchSize": 100
  }
}
```

## 🔐 Credentials Setup

### Required Credentials

1. **Neon PostgreSQL**
   - Host, Port, Database
   - User, Password
   - SSL enabled

2. **Composio API**
   - API Key: `COMPOSIO_API_KEY`
   - Base URL: https://backend.composio.dev

3. **GitHub**
   - Personal Access Token
   - Scopes: repo, workflow, project

4. **Firebase**
   - Service Account JSON
   - Project ID, Database URL

5. **Apify** (via Composio)
   - API Token via Composio connected account

6. **Slack** (optional)
   - Webhook URL or OAuth token

## 📊 Monitoring

### Workflow Execution Logs
```bash
# View logs in n8n UI
# Or query executions table if using PostgreSQL backend

SELECT
  id,
  workflow_name,
  execution_status,
  started_at,
  finished_at,
  execution_time
FROM executions
WHERE started_at > NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

### Metrics Integration
```javascript
// Send metrics to Grafana
{
  "name": "Send Metrics",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://localhost:3000/api/annotations",
    "method": "POST",
    "body": {
      "text": "n8n workflow completed",
      "tags": ["n8n", "automation"],
      "time": "={{new Date().getTime()}}"
    }
  }
}
```

## 🚀 Deployment

### Docker Compose

See `docker-compose.yml` for complete setup including:
- n8n container
- PostgreSQL database for workflows
- Redis for queuing
- Nginx reverse proxy

### Cloud Deployment

**n8n Cloud (Easiest)**
- Hosted service
- No infrastructure management
- Import/export workflows

**Self-Hosted Options**
- Railway.app
- Render.com
- DigitalOcean App Platform
- AWS ECS/Fargate

## 🔄 Webhook Endpoints

### Incoming Webhooks

```bash
# Trigger outreach pipeline
curl -X POST http://localhost:5678/webhook/outreach-pipeline \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}'

# Report error
curl -X POST http://localhost:5678/webhook/error-notification \
  -H "Content-Type: application/json" \
  -d '{"error_id": "ERR-12345"}'
```

### Outgoing Webhooks

Configure in workflow settings to call external services.

## 🎯 Use Cases

### Data Pipeline
1. Ingest leads from multiple sources
2. Enrich with external APIs
3. Validate and clean data
4. Store in Neon database
5. Trigger outreach campaigns

### Monitoring & Alerts
1. Monitor database changes
2. Check API health
3. Alert on errors
4. Create tickets for issues

### Reporting
1. Generate daily reports
2. Aggregate metrics
3. Export to CSV/PDF
4. Email to stakeholders

### Integration Bridge
1. Connect disconnected systems
2. Transform data between formats
3. Sync across databases
4. Maintain data consistency

## 📚 Resources

- **n8n Docs**: https://docs.n8n.io
- **Community Workflows**: https://n8n.io/workflows
- **Docker Setup**: https://docs.n8n.io/hosting/installation/docker/
- **API Reference**: https://docs.n8n.io/api/

---

**Created:** 2025-11-06
**CTB Branch:** sys/n8n
**Doctrine ID:** 04.04.F1
**Status:** Active
