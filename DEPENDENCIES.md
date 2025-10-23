# 🔗 Dependency Map

Shows what depends on what across the CTB structure.

## Dependency Flow

```
┌─────────────────────────────────────────────┐
│  data/    (Foundation - No upstream deps)   │
│  Schemas, migrations, data contracts        │
└──────────────────┬──────────────────────────┘
                   │
                   ├─────────────────┐
                   ↓                 ↓
      ┌────────────────────┐  ┌─────────────────┐
      │  sys/              │  │  ai/            │
      │  APIs, CI/CD       │  │  Agents, tools  │
      │  Reads from data/  │  │  Writes to data/│
      └────────┬───────────┘  └────────┬────────┘
               │                       │
               └───────┬───────────────┘
                       ↓
              ┌────────────────┐
              │  ui/           │
              │  Frontend      │
              │  Consumes APIs │
              └────────────────┘
```

## Detailed Dependencies

### data/ (05.01.*)
**Upstream**: None (foundation layer)
**Downstream**:
- `sys/api/` - Reads from schemas
- `ai/agents/` - Writes to schemas
- `ui/apps/` - Indirect (via API)

**Files**:
- `infra/neon.sql` → Defines all schemas
- `migrations/*.sql` → Updates schemas

**Critical Path**: All services depend on data/ being correct

---

### sys/ (04.04.*)
**Upstream**:
- `data/` - Reads schemas for API responses

**Downstream**:
- `ui/apps/` - Frontend calls API endpoints
- `ai/agents/` - Agents call API for operations

**Files**:
- `api/server.js` → Main API entry point
- `api/routes/neon/*` → Database queries
- `github-factory/scripts/*` → CI/CD automation

**Critical Path**: API must be running for UI and agents to work

---

### ai/ (03.01.*)
**Upstream**:
- `data/` - Writes to schemas (enrichment, scraping)
- `sys/api/` - Calls endpoints for operations

**Downstream**: None (top of execution hierarchy)

**Files**:
- `garage-bay/services/mcp/main.py` → MCP orchestrator
- `agents/specialists/*.js` → Specialized runners
- `scripts/*.js` → Automation & deployment

**Critical Path**: Agents write data that API serves to UI

---

### ui/ (07.01.*)
**Upstream**:
- `sys/api/` - Fetches all data via REST endpoints

**Downstream**: None (top of user-facing stack)

**Files**:
- `apps/amplify-client/src/App.tsx` → Main React app
- `apps/outreach-process-manager/` → Outreach UI

**Critical Path**: UI depends on API being available

---

### docs/ (06.01.*)
**Upstream**: All branches (documents entire system)
**Downstream**: None (pure documentation)

**Purpose**: Reference material, not executable code

---

### meta/ (08.01.*)
**Upstream**: All branches reference configs
**Downstream**: None (pure configuration)

**Files**:
- `ctb_registry.json` - File index
- `config/*` - App configuration

---

## Runtime Dependencies

### API Server (`sys/api/server.js`)
```
Requires:
  - DATABASE_URL environment variable
  - Neon schemas exist (data/infra/neon.sql applied)
  - Port 3000 available

Provides:
  - REST endpoints for UI
  - Data access for agents
```

### Frontend (`ui/apps/amplify-client`)
```
Requires:
  - API server running
  - API_URL configured
  - Node.js 18+

Provides:
  - User interface
  - Data visualization
```

### Garage Bay (`ai/garage-bay/services/mcp/main.py`)
```
Requires:
  - API server running
  - DATABASE_URL
  - COMPOSIO_API_KEY
  - Python 3.9+

Provides:
  - MCP orchestration
  - Multi-service automation
```

### Migrations (`data/migrations/*.sql`)
```
Requires:
  - DATABASE_URL
  - psql or Node.js migration runner

Affects:
  - All services reading from database
  - Must run before API starts
```

---

## Startup Order

### Development
```bash
# 1. Database (foundation)
psql $DATABASE_URL -f ctb/data/infra/neon.sql

# 2. API (middle layer)
cd ctb/sys/api && node server.js &

# 3. Frontend (top layer)
cd ctb/ui/apps/amplify-client && npm run dev &

# 4. Optional: Agents
cd ctb/ai/garage-bay && python services/mcp/main.py &
```

### Production
```bash
# 1. Database migrations (automated)
node ctb/ai/scripts/run_migrations.js

# 2. API deployment (Render auto-deploys on push)
git push render main

# 3. Frontend deployment (Vercel auto-deploys on push)
git push origin main

# 4. Agents (run on-demand or cron)
```

---

## Breaking Change Impact

### If `data/` schema changes:
- ❌ API queries may break
- ❌ UI may display incorrect data
- ❌ Agents may fail writes
- ✅ Must run migrations first
- ✅ Update API queries
- ✅ Test UI flows

### If `sys/api/` changes:
- ❌ UI API calls may break
- ❌ Agents may fail operations
- ✅ Update frontend API client
- ✅ Update agent integrations
- ✅ Version API endpoints

### If `ai/agents/` changes:
- ⚠️ Data writes may stop
- ⚠️ Automation may pause
- ✅ Independent of UI
- ✅ Can deploy separately

### If `ui/` changes:
- ✅ No downstream impact
- ✅ API and data unaffected
- ✅ Deploy anytime

---

## Package Dependencies

### JavaScript/TypeScript
```json
{
  "express": "API server",
  "pg": "PostgreSQL client",
  "react": "UI framework",
  "@composio/core": "MCP integrations"
}
```

### Python
```python
# requirements.txt
anthropic  # Claude AI
composio   # MCP server
pg8000     # PostgreSQL
```

### System
- Node.js 18+
- Python 3.9+
- PostgreSQL 14+ (Neon)
- Git

---

## Circular Dependency Prevention

### ✅ Allowed
```
ui/ → sys/api/ → data/
ai/agents/ → sys/api/ → data/
ai/agents/ → data/ (direct writes)
```

### ❌ Forbidden
```
data/ → sys/  (data should be pure schemas)
sys/ → ui/    (backend shouldn't know frontend)
ui/ → ai/     (frontend shouldn't call agents directly)
```

---

## Critical Path Analysis

**Most Critical** (affects everything):
1. `data/infra/neon.sql` - Master schema
2. `sys/api/server.js` - API entry point
3. `DATABASE_URL` - Connection string

**Medium Critical** (affects some):
1. `sys/api/routes/neon/*.js` - API endpoints
2. `ui/apps/amplify-client/src/` - Frontend code
3. `ai/garage-bay/services/mcp/main.py` - MCP server

**Low Critical** (isolated):
1. `docs/*` - Documentation
2. `ai/scripts/*` - Deployment scripts
3. `meta/config/*` - Configuration

---

**Last Updated**: 2025-10-23
**Maintained By**: Platform Team
