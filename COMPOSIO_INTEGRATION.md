# Composio MCP Integration Guide

## Overview

This project uses Composio as a Model Context Protocol (MCP) server to integrate with external services including Neon (PostgreSQL), Apify (web scraping), Vercel (deployment), GitHub, and MillionVerifier (email validation). This document provides comprehensive information on how Composio is configured and used throughout the system.

## 🔧 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Composio MCP  │
│   (React/JS)    │───▶│   (Node.js)     │───▶│   Server        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  External APIs  │
                                              │  • Neon DB      │
                                              │  • Apify        │
                                              │  • Vercel       │
                                              │  • GitHub       │
                                              │  • MillionVerif │
                                              └─────────────────┘
```

### **🚨 CRITICAL: Database Access Rules**

```
✅ ALLOWED DATABASE FLOW:
Frontend → Backend API → ComposioNeonBridge → Composio MCP → Neon DB

❌ FORBIDDEN DATABASE FLOW:
Frontend → Backend API → Direct Neon Connection (pg client, etc.)
```

**All database operations MUST use Composio MCP Bridge:**
- No direct PostgreSQL client connections
- No direct DATABASE_URL usage
- All SQL operations through `ComposioNeonBridge.executeNeonOperation()`
- Fallback to mock data when Composio is unavailable

## 🌐 Connected Services

### **1. Neon Database (PostgreSQL)**
- **Purpose**: Primary database for storing outreach data, audit logs, scraping results
- **Connection Status**: ✅ Active via Composio MCP Bridge
- **Access Method**: **COMPOSIO ONLY** - No direct database connections
- **Database**: `outreach_manager_db`
- **Bridge Class**: `ComposioNeonBridge`
- **Tables**:
  - `marketing.company_promotion_log`
  - `marketing.data_scraping_log`
  - `marketing.unified_audit_log`
  - `marketing.email_validation_log`
  - `marketing.people_raw_intake` (planned)
  - `marketing.people_audit_log` (planned)

### **2. Apify (Web Scraping)**
- **Purpose**: Web scraping, data extraction, social media crawling
- **Connection Status**: ✅ Active
- **Connected Account ID**: `ca_yGfXDKPv3hz6`
- **Bearer Token**: `apify_api_[REDACTED_FOR_SECURITY]`
- **Available Actors**: 7,210+ public actors
- **Cost**: $5 monthly free tier, ~$0.30 per compute unit

### **3. Vercel (Deployment)**
- **Purpose**: Frontend deployment, environment variable management
- **Connection Status**: ✅ Active
- **Connected Account ID**: `ca_vkXglNynIxjm`
- **Bearer Token**: `[REDACTED_FOR_SECURITY]`
- **Projects**:
  - `outreach-process-manager` (ID: `prj_oXtHnd0Ushg3ExPFrdW7Jkn2VA0s`)
  - `imo-creator` (ID: `prj_nOFsShEtrEMIzrgk3iXf0uUDXr08`)

### **4. GitHub**
- **Purpose**: Version control, repository management (potential future integration)
- **Connection Status**: ⚠️ Configured but not actively used (using direct Git)

### **5. MillionVerifier**
- **Purpose**: Email validation and verification
- **Connection Status**: ⚠️ Not yet implemented

## 🔑 Authentication & Configuration

### **Composio API Configuration**
```javascript
const composioApiKey = 'ak_t-[REDACTED_FOR_SECURITY]';
const composioBaseUrl = 'https://backend.composio.dev';
```

### **Environment Variables**
```bash
# Composio MCP Integration
COMPOSIO_API_KEY=ak_t-[YOUR_API_KEY_HERE]
MCP_API_URL=https://backend.composio.dev

# Connected Account IDs
NEON_ACCOUNT_ID=<not_set>
APIFY_ACCOUNT_ID=ca_[YOUR_ACCOUNT_ID]
VERCEL_ACCOUNT_ID=ca_[YOUR_ACCOUNT_ID]
```

## 💻 Implementation Examples

### **1. Neon Database Operations (COMPOSIO ONLY)**
```javascript
// apps/outreach-process-manager/api/lib/composio-neon-bridge.js
import ComposioNeonBridge from './lib/composio-neon-bridge.js';

const bridge = new ComposioNeonBridge();

// ✅ CORRECT: All database operations through Composio MCP Bridge
const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
  sql: 'SELECT * FROM marketing.company_promotion_log',
  mode: 'read',
  return_type: 'rows'
});

// ✅ CORRECT: Audit log insertion via Composio
const insertResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
  sql: `INSERT INTO marketing.unified_audit_log
        (unique_id, process_id, altitude, timestamp, status, source)
        VALUES ('${uniqueId}', '${processId}', 10000, NOW(), '${status}', 'scrape-log')`,
  mode: 'write'
});

// ❌ NEVER DO: Direct database connections
// const client = new Client({ connectionString: neonUrl }); // FORBIDDEN
```

### **2. Apify Web Scraping**
```javascript
// Direct Apify API usage through Composio connection
const apifyToken = 'apify_api_[YOUR_TOKEN_FROM_COMPOSIO]';
const baseUrl = 'https://api.apify.com/v2';

// Execute actor (web scraper)
const response = await fetch(`${baseUrl}/acts/apify/website-content-crawler/runs`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apifyToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com',
    maxPages: 10,
    outputFormat: 'json'
  })
});

// Available popular actors:
// - apify/website-content-crawler
// - clockworks/tiktok-scraper
// - compass/crawler-google-places
// - apify/instagram-scraper
// - apidojo/tweet-scraper
```

### **3. Vercel Environment Management**
```javascript
// Direct Vercel API usage through Composio connection
const vercelToken = '[YOUR_VERCEL_TOKEN_FROM_COMPOSIO]';
const projectId = 'prj_[YOUR_PROJECT_ID]';

// Set environment variable
const response = await fetch(`https://api.vercel.com/v10/projects/${projectId}/env`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${vercelToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    key: 'VITE_API_URL',
    value: 'https://api.example.com',
    target: ['production', 'preview', 'development'],
    type: 'encrypted'
  })
});
```

## 🔄 API Endpoints & Usage Patterns

### **Working Composio Endpoints**
```bash
# Connected Accounts
GET https://backend.composio.dev/api/v3/connected_accounts
Headers:
  x-api-key: [YOUR_COMPOSIO_API_KEY]
  Authorization: Bearer [YOUR_COMPOSIO_API_KEY]

# Available Tools/Apps
GET https://backend.composio.dev/api/v3/tools
GET https://backend.composio.dev/api/v1/apps
```

### **Tool Execution Patterns**
⚠️ **Important**: Composio's tool execution endpoints return 404/405 errors:
- `/api/v1/actions/execute` ❌
- `/api/v3/tools/execute` ❌
- `/api/v3/actions/execute` ❌

**Workaround**: Use direct API access with extracted bearer tokens from connected accounts.

## 📁 File Structure

### **Core Integration Files**
```
apps/outreach-process-manager/api/
├── lib/
│   └── composio-neon-bridge.js     # Neon database bridge
├── audit-log.js                   # Audit log API
├── scrape-log.ts                  # Scraping log API (posts to audit)
├── validate-email.js              # Email validation API
└── promote-company.js             # Company promotion API

apps/outreach-ui/src/
└── pages/
    ├── audit-log-console/          # Unified audit trail
    ├── scraping-console/           # Web scraping interface
    ├── validation-console/         # Email validation
    └── promotion-console/          # Company promotion
```

### **Configuration Files**
```
├── .env                           # Environment variables
├── COMPOSIO_INTEGRATION.md        # This documentation
└── test-files/
    ├── test-composio-endpoints.js
    ├── test-working-composio-execution.js
    └── test-final-composio-execution.js
```

## 🎯 Usage Guidelines

### **1. Database Operations (Neon) - COMPOSIO ONLY**
- **MANDATORY**: Always use `ComposioNeonBridge` class for ALL database operations
- **FORBIDDEN**: Never use direct database connections (pg, node-postgres, etc.)
- **PATTERN**: All SQL operations must go through `bridge.executeNeonOperation()`
- Include proper error handling and fallback strategies
- Use parameterized queries to prevent SQL injection
- Follow Barton Doctrine for unique ID generation

**Correct Pattern:**
```javascript
const bridge = new ComposioNeonBridge();
const result = await bridge.executeNeonOperation('EXECUTE_SQL', { sql, mode: 'read' });
```

**Forbidden Pattern:**
```javascript
// ❌ NEVER DO THIS
const client = new Client({ connectionString: process.env.DATABASE_URL });
await client.query('SELECT * FROM users');
```

### **2. Web Scraping (Apify)**
- Use direct API calls with bearer token authentication
- Monitor usage costs (free tier: $5/month)
- Implement rate limiting and error handling
- Choose appropriate actors for specific scraping needs

### **3. Deployment (Vercel)**
- Use direct API for environment variable management
- Target appropriate environments (production/preview/development)
- Use encrypted storage for sensitive values
- Monitor deployment status and costs

### **4. Error Handling**
```javascript
// Standard error handling pattern
try {
  const result = await composioOperation();
  if (!result.success) {
    console.warn('Composio operation failed, using fallback');
    return fallbackOperation();
  }
  return result.data;
} catch (error) {
  console.error('Composio error:', error);
  return fallbackOperation();
}
```

## 🧪 Testing & Validation

### **Test Scripts**
- `test-composio-endpoints.js` - Validates API connectivity
- `test-working-composio-execution.js` - Tests working patterns
- `test-final-composio-execution.js` - Comprehensive execution tests

### **Test Commands**
```bash
# Test Composio connectivity
node test-composio-endpoints.js

# Test Apify integration
node test-working-composio-execution.js

# Test Vercel integration
node test-final-composio-execution.js
```

## 🔒 Security Considerations

### **API Key Management**
- Store API keys in environment variables only
- Never commit keys to version control
- Use encrypted environment variables in Vercel
- Rotate keys periodically

### **Access Control**
- Connected accounts have limited scope access
- Bearer tokens are service-specific
- Use read-only access where possible
- Monitor usage and costs regularly

## 🚨 Known Limitations

### **1. Tool Execution**
- Composio's wrapper tools don't work via standard API endpoints
- Must use direct API access with extracted bearer tokens
- No unified tool execution interface

### **2. Error Handling**
- Composio proxy endpoints are not responsive
- Fallback strategies required for production reliability
- Mock data used for development when services unavailable

### **3. Cost Monitoring**
- Apify usage incurs costs beyond free tier
- Vercel environment variable operations may have limits
- Database operations through Composio may have quotas

## 🔄 Unified Audit Trail

The system implements a unified audit trail that aggregates logs from all sources:

### **Sources**
- `promotion` - Company promotion operations
- `scrape-log` - Web scraping operations
- `validation` - Email validation operations

### **Implementation**
```javascript
// Auto-logging to unified audit trail
await postToAuditLog({
  unique_id: generateDoctrineId(),
  process_id: 'Scrape Company Data',
  altitude: 10000,
  timestamp: new Date().toISOString(),
  status: 'Success',
  errors: [],
  source: 'scrape-log'
});
```

### **Navigation**
- `/audit-log-console` - All logs
- `/audit-log-console?source=scrape-log` - Filtered by source
- JSON export includes source field for analysis

## 📞 Support & Troubleshooting

### **Common Issues**
1. **404 on tool execution** → Use direct API access pattern
2. **Authentication errors** → Check bearer token validity
3. **Database connection failed** → Verify Neon connection status
4. **Scraping failures** → Check Apify account credits and actor availability

### **Debug Steps**
1. Test connectivity with `test-composio-endpoints.js`
2. Verify connected account status in Composio dashboard
3. Check bearer token extraction and validity
4. Review error logs for specific failure patterns

### **Contact Information**
- Composio Documentation: https://docs.composio.dev
- API Support: Available through Composio dashboard
- Repository Issues: Use GitHub issues for integration problems

---

**Last Updated**: January 2025
**Version**: v2.1.0
**Maintainer**: Barton Outreach Core Team