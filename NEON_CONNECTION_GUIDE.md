# Neon Database Connection Guide
**Created:** 2025-10-24
**Status:** ✅ Successfully Connected

---

## ✅ Working Direct Neon API Connection

### Your Neon Setup

**API Key:** `napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1`

### Projects

You have 4 Neon projects:

| Project Name | Project ID | Region | Status |
|--------------|------------|--------|--------|
| **Marketing DB** ⭐ | white-union-26418370 | aws-us-east-1 | Active |
| Real Estate | solitary-glade-05914360 | aws-us-east-2 | Active |
| Student Profile | curly-dust-57914571 | aws-us-east-2 | Active |
| Command Ops | fancy-night-23676826 | aws-us-east-1 | Active |

### Marketing DB Details (Primary Database)

**Project Information:**
- **ID:** white-union-26418370
- **Region:** US East 1 (aws-us-east-1)
- **PostgreSQL Version:** 17
- **Proxy Host:** us-east-1.aws.neon.tech
- **Storage Size:** 42 MB
- **Last Active:** 2025-10-23 15:51:21Z

**Branch Information:**
- **Branch ID:** br-empty-sea-a4m64yyz
- **Name:** production
- **Status:** ready
- **Type:** primary, default
- **Created:** 2025-05-19T13:50:01Z
- **Created By:** David

**Database:**
- **Name:** Marketing DB
- **Owner:** Marketing DB_owner

**Connection String:**
```
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?channel_binding=require&sslmode=require
```

---

## 🚀 Working Example: Direct Neon API Access

### Using Node.js

```javascript
const https = require('https');

// List all projects
const options = {
  hostname: 'console.neon.tech',
  path: '/api/v2/projects',
  method: 'GET',
  headers: {
    'Authorization': 'Bearer napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1',
    'Accept': 'application/json'
  }
};

const req = https.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    const projects = JSON.parse(data);
    console.log('Projects:', projects);
  });
});

req.on('error', (e) => {
  console.error('Error:', e.message);
});

req.end();
```

### Common API Endpoints

```javascript
// List all projects
GET /api/v2/projects

// Get specific project
GET /api/v2/projects/{project_id}

// Get project branches
GET /api/v2/projects/{project_id}/branches

// Get databases for a branch
GET /api/v2/projects/{project_id}/branches/{branch_id}/databases

// Get connection string
GET /api/v2/projects/{project_id}/connection_uri?branch_id={branch_id}&database_name={db_name}&role_name={role_name}

// Create new branch
POST /api/v2/projects/{project_id}/branches

// Run SQL query
POST /api/v2/projects/{project_id}/branches/{branch_id}/databases/{database_name}/query
```

### Headers Required

```javascript
{
  'Authorization': 'Bearer napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1',
  'Accept': 'application/json',
  'Content-Type': 'application/json' // for POST/PUT requests
}
```

---

## 🔧 Composio MCP Integration (Next Steps)

### Current Status
- ✅ Composio CLI installed
- ⏳ Needs authentication

### Setup Steps

1. **Authenticate Composio CLI**
   ```bash
   composio login
   ```

2. **Add Neon App** (after auth)
   ```bash
   composio add neon
   ```

3. **Configure MCP Server**
   - Get MCP URL from: https://mcp.composio.dev/neon
   - Setup command:
     ```bash
     composio mcp https://mcp.composio.dev/neon --client claude
     ```

4. **Available Composio Packages**
   - @composio/client@0.1.0-alpha.36
   - @composio/core@0.1.52
   - @composio/json-schema-to-zod@0.1.15

---

## 📋 Environment Variables

Add these to your `.env` files:

```bash
# Neon Configuration
NEON_API_KEY=napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1
NEON_PROJECT_ID=white-union-26418370
NEON_BRANCH_ID=br-empty-sea-a4m64yyz

# Database Connection
DATABASE_URL=postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?channel_binding=require&sslmode=require

# Composio (when authenticated)
COMPOSIO_API_KEY=your-composio-api-key
```

---

## 🔍 Testing Connection

### Test with psql
```bash
psql "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?channel_binding=require&sslmode=require"
```

### Test with Node.js pg
```javascript
const { Client } = require('pg');

const client = new Client({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: true
  }
});

client.connect()
  .then(() => {
    console.log('Connected to Neon!');
    return client.query('SELECT version()');
  })
  .then(result => {
    console.log('PostgreSQL Version:', result.rows[0].version);
    return client.end();
  })
  .catch(err => {
    console.error('Connection error:', err);
  });
```

---

## 📊 Available Neon Actions via Composio (When Connected)

Based on research, Composio provides **69+ tools** for Neon:

### Project Management
- `NEON_CREATE_PROJECT_WITH_QUOTA_AND_SETTINGS`
- `NEON_DELETE_PROJECT_BY_ID`
- `NEON_RETRIEVE_PROJECT_LIST`

### Branch Operations
- `NEON_CREATE_BRANCH_DATABASE`
- `NEON_RETRIEVE_BRANCH_DATABASE_DETAILS`

### Database Management
- Create, delete, and manage databases
- Configure compute endpoints
- Manage API keys

---

## 🎯 Next Actions

1. ✅ **COMPLETED:** Direct Neon API connection working
2. ✅ **COMPLETED:** Retrieved all project information
3. ✅ **COMPLETED:** Got connection strings
4. ⏳ **TODO:** Authenticate Composio CLI (`composio login`)
5. ⏳ **TODO:** Add Neon app to Composio
6. ⏳ **TODO:** Test Composio MCP actions

---

## 📚 Resources

- **Neon API Docs:** https://api-docs.neon.tech/reference/getting-started-with-neon-api
- **Composio Neon MCP:** https://mcp.composio.dev/neon
- **Composio Docs:** https://docs.composio.dev
- **Your Neon Console:** https://console.neon.tech/app/projects

---

**Status:** Direct API connection fully functional. Composio MCP ready for setup after authentication.
