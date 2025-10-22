# 🌐 GLOBAL POLICY: All Tools Via Composio MCP

**Date**: 2025-10-22
**Authority**: imo-creator repo global configuration
**Status**: MANDATORY - NO EXCEPTIONS

---

## 🚨 ABSOLUTE RULE

**ALL TOOLS - INTERNAL AND EXTERNAL - MUST BE CALLED VIA COMPOSIO MCP**

This is a **GLOBAL ARCHITECTURAL REQUIREMENT** that applies to:
- ✅ Database operations (Neon, PostgreSQL)
- ✅ External APIs (Apify, Gmail, Drive, etc.)
- ✅ Internal services (Firebase, validation, enrichment)
- ✅ File operations
- ✅ AI/LLM calls (when integrated)
- ✅ **EVERYTHING**

---

## 📋 The One True Pattern

### Composio MCP Endpoint
```
http://localhost:3001/tool?user_id={COMPOSIO_USER_ID}
```

### HEIR/ORBT Payload Format (MANDATORY)
```json
{
  "tool": "tool_name_here",
  "data": {
    // Tool-specific parameters
  },
  "unique_id": "HEIR-YYYY-MM-SYSTEM-MODE-VN",
  "process_id": "PRC-SYSTEM-EPOCHTIMESTAMP",
  "orbt_layer": 2,
  "blueprint_version": "1.0"
}
```

### Example: Neon Database Operation
```javascript
const payload = {
  tool: 'neon_execute_sql',
  data: {
    sql: 'SELECT * FROM marketing.company_master LIMIT 10;',
    database_url: process.env.NEON_DATABASE_URL
  },
  unique_id: `HEIR-2025-10-QUERY-${Date.now()}`,
  process_id: `PRC-DB-QUERY-${Date.now()}`,
  orbt_layer: 2,
  blueprint_version: '1.0'
};

const response = await fetch(
  `http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }
);
```

---

## ❌ FORBIDDEN PATTERNS

### DO NOT USE - Direct Database Connections
```javascript
// ❌ FORBIDDEN - Direct neon connection
import { neon } from '@neondatabase/serverless';
const sql = neon(connectionString);
await sql`SELECT * FROM table`;

// ❌ FORBIDDEN - Direct pg client
import pg from 'pg';
const client = new pg.Client({ connectionString });
await client.connect();
```

### DO NOT USE - Direct SDK Calls
```javascript
// ❌ FORBIDDEN - Direct Composio SDK
import { Composio } from '@composio/core';
const composio = new Composio({ apiKey });
await composio.actions.execute(...);

// ❌ FORBIDDEN - Direct API calls
await fetch('https://backend.composio.dev/api/...', ...);
```

### DO NOT USE - Direct External APIs
```javascript
// ❌ FORBIDDEN - Direct Apify
await fetch('https://api.apify.com/v2/...', ...);

// ❌ FORBIDDEN - Direct Gmail API
const gmail = google.gmail({ version: 'v1', auth });
await gmail.users.messages.list(...);
```

---

## ✅ CORRECT PATTERNS

### Database Migrations
```javascript
// ✅ CORRECT - Via Composio MCP
const migrationSQL = await fs.readFile('migration.sql', 'utf8');

const payload = {
  tool: 'neon_execute_sql',
  data: {
    sql: migrationSQL,
    database_url: process.env.NEON_DATABASE_URL
  },
  unique_id: `HEIR-2025-10-MIGRATION-${Date.now()}`,
  process_id: `PRC-MIGRATION-${Date.now()}`,
  orbt_layer: 2,
  blueprint_version: '1.0'
};

await fetch(`http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});
```

### External Service Calls
```javascript
// ✅ CORRECT - Via Composio MCP
const payload = {
  tool: 'apify_run_actor',
  data: {
    actorId: 'code_crafter~leads-finder',
    runInput: {
      company_domain: ['example.com'],
      contact_job_title: ['CEO', 'CFO']
    }
  },
  unique_id: `HEIR-2025-10-APIFY-${Date.now()}`,
  process_id: `PRC-ENRICHMENT-${Date.now()}`,
  orbt_layer: 2,
  blueprint_version: '1.0'
};

await fetch(`http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});
```

---

## 🔒 Why This Is Absolute

### 1. **Centralized Control**
- All tool calls flow through single MCP endpoint
- Easy to monitor, log, and debug
- Single source of truth for integrations

### 2. **HEIR/ORBT Compliance**
- Every operation tracked with unique_id
- Process lineage maintained via process_id
- Altitude tracking for data elevation
- Blueprint versioning for schema evolution

### 3. **Configuration Management**
- Tool configurations managed in imo-creator repo
- Changes propagate globally
- No scattered API keys or credentials
- Centralized rate limiting and quotas

### 4. **Audit Trail**
- Complete history of all operations
- Barton Doctrine compliance
- Error tracking and debugging
- Performance monitoring

### 5. **Abstraction Layer**
- Services can be swapped without code changes
- Composio handles authentication/authorization
- Automatic retry logic and error handling
- Connection pooling and optimization

---

## 📖 Available Composio Tools

### Database Operations
- `neon_execute_sql` - Execute any SQL statement
- `neon_query` - Read-only queries
- `neon_insert` - Insert operations
- `neon_update` - Update operations
- `neon_delete` - Delete operations

### External Services
- `apify_run_actor` - Execute Apify actor
- `apify_get_dataset` - Retrieve Apify results
- `gmail_send_email` - Send email via Gmail
- `gmail_list_messages` - List Gmail messages
- `drive_upload_file` - Upload to Google Drive
- `drive_list_files` - List Drive files
- `sheets_append_row` - Add row to Google Sheets
- `sheets_read_range` - Read from Google Sheets

### Firebase Operations
- `firebase_write` - Write to Firebase
- `firebase_read` - Read from Firebase
- `firebase_update` - Update Firebase document
- `firebase_delete` - Delete from Firebase

*(Full list available via `GET http://localhost:3001/tools`)*

---

## 🔄 Configuration Authority

### Global Configuration Location
```
imo-creator/
├── composio-config.json       # Global tool configurations
├── .env.composio              # Composio credentials
└── mcp-server/
    └── tool-registry.json     # Available tools and endpoints
```

### Configuration Changes
**ONLY** the imo-creator repository can modify:
- Available tools
- Tool endpoints
- Authentication methods
- Payload formats
- MCP server behavior

**Changes to imo-creator propagate to all projects:**
- barton-outreach-core
- ingest-companies-people
- outreach-process-manager
- All dependent repositories

---

## ⚠️ Enforcement

### Code Review Checklist
- [ ] All database calls use `neon_execute_sql` via Composio MCP
- [ ] All external API calls use Composio MCP tools
- [ ] All payloads include HEIR/ORBT metadata
- [ ] No direct SDK imports (pg, @neondatabase/serverless, @composio/core)
- [ ] No direct API calls to external services
- [ ] All operations have unique_id and process_id

### Automated Checks
```bash
# Scan for forbidden patterns
npm run check:composio-compliance

# Verify all imports route through MCP
npm run lint:mcp-only
```

### Migration Existing Code
If you find code with direct connections:

1. **Identify the tool**
   - Database? → `neon_execute_sql`
   - Apify? → `apify_run_actor`
   - Gmail? → `gmail_send_email`

2. **Convert to Composio pattern**
   - Wrap operation in HEIR/ORBT payload
   - POST to `http://localhost:3001/tool?user_id=${COMPOSIO_USER_ID}`

3. **Remove direct imports**
   - Delete SDK imports
   - Delete connection string references
   - Delete API key environment variables

4. **Test via Composio**
   - Verify operation works through MCP
   - Confirm HEIR/ORBT metadata present
   - Check audit logs

---

## 📚 Documentation References

- **Primary**: `/COMPOSIO_INTEGRATION.md` - Composio setup and examples
- **Architecture**: `/apps/outreach-process-manager/API-MIDDLE-LAYER.md` - MCP flow
- **Migrations**: `/analysis/INTELLIGENCE_MIGRATION_GUIDE.md` - Database migrations via MCP
- **Compliance**: `/FINAL_AUDIT_SUMMARY.md` - Audit compliance patterns

---

## 🎯 Summary

**ONE RULE TO RULE THEM ALL:**

```
IF (need_to_call_tool) {
  POST http://localhost:3001/tool?user_id={COMPOSIO_USER_ID}
  WITH HEIR/ORBT payload
}

NEVER {
  direct database connections
  direct SDK calls
  direct API requests
}
```

**Configuration Authority**: imo-creator repo ONLY

**No Exceptions**: This is absolute

**Questions?** Check imo-creator/composio-config.json first

---

**Last Updated**: 2025-10-22
**Enforced By**: imo-creator global configuration
**Compliance**: Mandatory for all Barton Doctrine projects
