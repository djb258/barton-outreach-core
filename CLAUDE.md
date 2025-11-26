# 🚀 Claude Bootstrap Guide - Barton Outreach Core & IMO Creator

## 📋 INSTANT REPO OVERVIEW

**Repository Name**: Barton Outreach Core
**Primary Purpose**: Marketing intelligence & executive enrichment platform (PLE - Perpetual Lead Engine)
**Sister Repository**: IMO Creator (AI-powered interface creation with Google Workspace integration)
**Database**: Neon PostgreSQL (serverless)
**Integration Hub**: Composio MCP server (port 3001) managing 100+ services

---

## 🌐 ECOSYSTEM ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────────┐
│                    BARTON OUTREACH ECOSYSTEM                      │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐         ┌─────────────────────────────┐
│   BARTON OUTREACH CORE      │         │      IMO CREATOR            │
│   (Marketing Intelligence)  │◀───────▶│   (Interface Builder)       │
└─────────────────────────────┘         └─────────────────────────────┘
           │                                        │
           │                                        │
     ┌─────▼──────┐                          ┌─────▼──────┐
     │   Neon     │                          │  Composio  │
     │ PostgreSQL │                          │  MCP :3001 │
     └────────────┘                          └────────────┘
                                                   │
                                                   │
                                             ┌─────▼──────┐
                                             │   Google   │
                                             │ Workspace  │
                                             └────────────┘

SHARED FOUNDATIONS:
├── Barton Doctrine (ID Format: NN.NN.NN.NN.NNNNN.NNN)
├── HEIR/ORBT Payload Format
├── MCP Protocol
└── Firebase Integration
```

---

## 🎯 CRITICAL PATHS & STARTUP SEQUENCES

### Barton Outreach Core Startup

```bash
# Check database connection
psql postgresql://<NEON_USER>:<NEON_PASSWORD>@<NEON_HOST>:5432/<NEON_DATABASE>?sslmode=require

# Run enrichment sync
cd infra/scripts
./sync-svg-ple-to-github-projects.sh --once

# Check error logs
psql -c "SELECT * FROM public.shq_error_log ORDER BY created_at DESC LIMIT 10;"
```

### IMO Creator Startup (Sister Repo)

```bash
# 1. Start Composio MCP Server (MANDATORY for both repos)
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js

# 2. Start FastAPI server
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\imo-creator"
python main.py

# 3. Test integrations
curl -X POST http://localhost:3001/tool -H "Content-Type: application/json" -d '{"tool": "get_composio_stats", "data": {}, "unique_id": "HEIR-2025-09-BOOT-01", "process_id": "PRC-BOOT-001", "orbt_layer": 2, "blueprint_version": "1.0"}'
```

---

## 📁 BARTON OUTREACH CORE STRUCTURE

```
barton-outreach-core/
├── 🔥 CLAUDE.md                          # This bootstrap file
├── 🔥 FINAL_AUDIT_SUMMARY.md             # 100% compliance audit
├── 🔥 OUTREACH_DOCTRINE_A_Z_v1.3.2.md    # Complete system documentation
│
├── infra/                                # Infrastructure & deployment
│   ├── docs/
│   │   ├── ENRICHMENT_TRACKING_QUERIES.sql        # Executive enrichment monitoring
│   │   ├── svg-ple-todo.md                        # Project tracker (53% complete)
│   │   ├── AUTO_SYNC_GITHUB_PROJECTS.md           # Auto-sync documentation
│   │   └── GITHUB_PROJECTS_SETUP.md               # GitHub Projects integration
│   │
│   ├── scripts/
│   │   ├── sync-svg-ple-to-github-projects.sh     # Sync to-dos to GitHub
│   │   ├── auto-sync-svg-ple-github.sh            # Auto-sync with watch mode
│   │   ├── setup-pre-commit-hook.sh               # Git hook installer
│   │   └── schema-refresh.js                      # Neon schema refresh
│   │
│   └── migrations/
│       └── 001_create_shq_error_log.sql           # Error logging table
│
├── repo-data-diagrams/                   # PLE schema documentation
│   ├── README.md                         # Central index for schema docs
│   ├── PLE_SCHEMA_ERD.md                 # Mermaid ERD diagram
│   ├── PLE_SCHEMA_REFERENCE.md           # Complete column reference
│   └── ple_schema.json                   # Machine-readable schema
│
├── docs/
│   └── schema_map.json                   # Neon database schema (auto-generated)
│
├── .github/
│   └── workflows/
│       └── sync-svg-ple-todo.yml         # Auto-sync GitHub Actions
│
├── .env                                  # Environment variables (see below)
└── package.json                          # Node.js dependencies
```

---

## 📁 IMO CREATOR STRUCTURE (Sister Repo)

```
imo-creator/
├── 🔥 COMPOSIO_INTEGRATION.md            # CRITICAL: Read first for API integrations
├── 🚀 CLAUDE.md                          # IMO Creator bootstrap
├── main.py                               # FastAPI entry point (Render)
├── Procfile                              # Render deployment
├── render.yaml                           # Render configuration
├── runtime.txt                           # Python 3.11.9
├── requirements.txt                      # Python dependencies
├── firebase_mcp.js                       # Firebase MCP server
│
├── src/
│   └── server/
│       └── main.py                       # Core FastAPI application
│
└── docs/
    └── composio_connection.md            # Composio details

Related (External):
├── scraping-tool/imo-creator/mcp-servers/
│   └── composio-mcp/                     # **CRITICAL**: Main integration hub (port 3001)
```

---

## 🗄️ DATABASE ARCHITECTURE

### Neon PostgreSQL Connection

**Host**: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
**Port**: `5432`
**Database**: `Marketing DB`
**User**: `Marketing DB_owner`
**Password**: `endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT`
**SSL Mode**: `require`
**Version**: PostgreSQL 15+

### Schema Structure

#### **marketing** Schema (Core Data)

**company_master** (Barton ID: `04.04.02.04.30000.###`)
- `company_unique_id` (PK)
- `company_name`
- `industry`
- `employee_count`
- `created_at`, `updated_at`
- **Purpose**: Master company records

**company_slot** (Barton ID: `04.04.02.04.10000.###`)
- `company_slot_unique_id` (PK)
- `company_unique_id` (FK → company_master)
- `person_unique_id` (FK → people_master)
- `slot_type` (CEO/CFO/HR)
- `is_filled`
- `filled_at`, `last_refreshed_at`
- **Purpose**: Executive position tracking

**people_master** (Barton ID: `04.04.02.04.20000.###`)
- `unique_id` (PK)
- `full_name`
- `email`
- `linkedin_url`
- `title`
- `company_unique_id` (FK → company_master)
- **Purpose**: Contact/executive data

**data_enrichment_log**
- `enrichment_id` (PK)
- `company_unique_id` (FK → company_master)
- `agent_name` (Apify, Abacus, Firecrawl, etc.)
- `enrichment_type` (executive, linkedin, profile)
- `status` (pending, running, success, failed, timeout, rate_limited)
- `started_at`, `completed_at`
- `error_message`
- `cost_credits`
- `data_quality_score`
- `movement_detected`
- **Purpose**: Track enrichment job performance

**pipeline_errors**
- Error tracking for data pipeline
- Stage-specific error logging
- Resolution queue management

**duplicate_queue**
- Duplicate detection and resolution
- Merge candidates
- Conflict resolution tracking

#### **intake** Schema (Data Ingestion)

**company_raw_intake**
- CSV upload staging
- Raw data before validation
- Source tracking

#### **public** Schema (System)

**shq_error_log** (Barton ID: `04.04.02.04.40000.###`)
- `error_id` (PK)
- `error_code`
- `error_message`
- `severity` (info, warning, error, critical)
- `component`
- `stack_trace`
- `user_id`
- `request_id`
- `resolution_status`
- `created_at`, `updated_at`
- **Purpose**: System-wide error tracking

**linkedin_refresh_jobs**
- `job_id` (PK)
- `person_unique_id` (FK → people_master)
- `status`
- `requested_at`, `started_at`, `completed_at`
- `apify_run_id`
- `error_message`
- **Purpose**: LinkedIn-specific enrichment tracking

#### **bit** Schema (Buyer Intent Tool)

**events**
- `event_id` (PK)
- `company_unique_id` (FK → company_master)
- `event_type`
- `event_payload`
- `detected_at`
- `movement_type`
- **Purpose**: Buyer intent signal detection

---

## ✅ VERIFIED INTEGRATIONS

### Google Workspace (via Composio MCP - IMO Creator)

- **Gmail**: 3 accounts
  - service@svg.agency
  - djb258@gmail.com
  - dbarton@svg.agency
- **Google Drive**: 3 accounts (all active with full API access)
- **Google Calendar**: 1 account (service@svg.agency)
- **Google Sheets**: 1 account (service@svg.agency)

### Infrastructure

- **Neon PostgreSQL**: Active (Marketing DB)
- **Render**: Deployment environment (IMO Creator)
- **Vercel**: Frontend deployment (IMO Creator)
- **Firebase**: MCP server ready
- **Composio MCP**: 100+ services on port 3001

### Enrichment Agents

- **Apify**: LinkedIn scraping, profile enrichment
- **Abacus**: Data validation, enrichment
- **Firecrawl**: Web scraping, company data
- Status tracked in `marketing.data_enrichment_log`

---

## 🔑 ENVIRONMENT VARIABLES

### Barton Outreach Core (.env)

```bash
# Neon Database
NEON_HOST=ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
NEON_DATABASE=Marketing DB
NEON_USER=Marketing DB_owner
NEON_PASSWORD=<YOUR_NEON_PASSWORD>
NEON_ENDPOINT_ID=ep-ancient-waterfall-a42vy0du

# Barton Doctrine
DOCTRINE_SUBHIVE=04
DOCTRINE_APP=outreach
DOCTRINE_LAYER=04
DOCTRINE_SCHEMA=02
DOCTRINE_VERSION=04
```

### IMO Creator (.env)

```bash
# LLM Providers
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
LLM_DEFAULT_PROVIDER=openai

# HEIR/MCP Integration
IMOCREATOR_MCP_URL=http://localhost:7001
IMOCREATOR_SIDECAR_URL=http://localhost:8000
IMOCREATOR_BEARER_TOKEN=local-dev-token

# Doctrine ID Generation
DOCTRINE_DB=shq
DOCTRINE_SUBHIVE=03
DOCTRINE_APP=imo
DOCTRINE_VER=1

# Garage-MCP Integration
GARAGE_MCP_URL=http://localhost:7001
GARAGE_MCP_TOKEN=dev-local
SUBAGENT_REGISTRY_PATH=/registry/subagents

# CORS Configuration
ALLOW_ORIGIN=https://your-vercel-project.vercel.app
PORT=7002

# Composio Integration
COMPOSIO_API_KEY=ak_t-F0AbvfZHUZSUrqAGNn
MCP_API_URL=https://backend.composio.dev
```

---

## 🚨 NEVER DO THESE THINGS

### For Barton Outreach Core

❌ **NEVER** install Docker Desktop (conflicts with npx/node/Claude Code)
❌ **NEVER** modify Barton ID format (must be: NN.NN.NN.NN.NNNNN.NNN)
❌ **NEVER** skip error logging to `shq_error_log` table
❌ **NEVER** bypass RLS (Row Level Security) in Neon
❌ **NEVER** hardcode database credentials (use .env)
❌ **NEVER** commit `.env` files to Git

### For IMO Creator

❌ **NEVER** create custom Google API integrations (use Composio MCP)
❌ **NEVER** set up individual OAuth flows (handled by Composio)
❌ **NEVER** use environment variables for Google services (use MCP interface)
❌ **NEVER** ignore HEIR/ORBT payload format
❌ **NEVER** deploy without testing MCP server first

### For Both

❌ **NEVER** mix up Barton ID schemas between repos
❌ **NEVER** skip the audit trail (all changes must be logged)
❌ **NEVER** use raw SQL without parameterization (SQL injection risk)

---

## 🎯 COMMON TASK PATTERNS

### Working with Neon Database

```bash
# Connect to database
psql postgresql://Marketing_DB_owner:endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require

# Check table schemas
\dt marketing.*
\d marketing.company_master

# Run enrichment tracking queries
# See: infra/docs/ENRICHMENT_TRACKING_QUERIES.sql

# Refresh schema map
node infra/scripts/schema-refresh.js

# Check recent errors
SELECT * FROM public.shq_error_log
WHERE severity IN ('error', 'critical')
ORDER BY created_at DESC LIMIT 20;
```

### Working with Google Services (via Composio MCP)

```bash
# 1. Start Composio MCP Server (from IMO Creator repo)
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js

# 2. Verify MCP is running
curl http://localhost:3001/mcp/health

# 3. List connected accounts
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{"tool": "manage_connected_account", "data": {"action": "list"}, "unique_id": "HEIR-2025-11-VERIFY-01", "process_id": "PRC-VERIFY-001", "orbt_layer": 2, "blueprint_version": "1.0"}'

# 4. Use HEIR/ORBT format for all calls
# See: imo-creator/COMPOSIO_INTEGRATION.md
```

### GitHub Projects Sync

```bash
# One-time sync
cd infra/scripts
./auto-sync-svg-ple-github.sh --once

# Continuous watch mode
./auto-sync-svg-ple-github.sh --watch

# Set up pre-commit hook
./setup-pre-commit-hook.sh
```

### Enrichment Monitoring

```bash
# Check pending enrichments
psql -c "SELECT COUNT(*) FROM marketing.company_slot WHERE slot_type IN ('CEO','CFO','HR') AND (last_refreshed_at IS NULL OR last_refreshed_at < NOW() - INTERVAL '3 days');"

# Check running jobs
psql -c "SELECT COUNT(*) FROM marketing.data_enrichment_log WHERE status IN ('pending','running') AND enrichment_type IN ('executive','linkedin','profile');"

# Check agent performance
psql -c "SELECT agent_name, COUNT(*) total, COUNT(*) FILTER (WHERE status='success') successful, ROUND(100.0 * COUNT(*) FILTER (WHERE status='success') / NULLIF(COUNT(*), 0), 1) AS success_rate FROM marketing.data_enrichment_log WHERE created_at >= NOW() - INTERVAL '7 days' AND enrichment_type IN ('executive','linkedin','profile') GROUP BY agent_name ORDER BY success_rate DESC;"
```

---

## 🔧 DEBUGGING QUICK REFERENCE

### Database Connection Issues

```bash
# Test connection
psql postgresql://Marketing_DB_owner:endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require -c "SELECT NOW();"

# Check if tables exist
psql -c "\dt marketing.*"

# Verify RLS policies
psql -c "\d marketing.company_master"

# Check connection limits
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

### MCP Server Issues (IMO Creator)

```bash
# Check if Composio MCP is running
curl http://localhost:3001/mcp/health

# List all connected accounts
curl -X POST http://localhost:3001/tool -H "Content-Type: application/json" -d '{"tool": "manage_connected_account", "data": {"action": "list"}, "unique_id": "HEIR-2025-11-DEBUG-01", "process_id": "PRC-DEBUG-001", "orbt_layer": 2, "blueprint_version": "1.0"}'

# Check Google account status
# See: imo-creator/COMPOSIO_INTEGRATION.md
```

### Enrichment Agent Issues

```bash
# Check recent failures
psql -c "SELECT agent_name, enrichment_type, status, error_message, started_at FROM marketing.data_enrichment_log WHERE status IN ('failed','timeout','rate_limited') AND created_at >= NOW() - INTERVAL '24 hours' ORDER BY started_at DESC LIMIT 20;"

# Check slow jobs (>5 minutes)
psql -c "SELECT agent_name, enrichment_type, started_at, EXTRACT(MINUTE FROM NOW() - started_at) as minutes_running FROM marketing.data_enrichment_log WHERE status IN ('pending','running') AND started_at < NOW() - INTERVAL '5 minutes' ORDER BY started_at ASC;"

# Check agent success rates
psql -c "SELECT agent_name, COUNT(*) total, ROUND(100.0 * COUNT(*) FILTER (WHERE status='success') / NULLIF(COUNT(*), 0), 1) success_rate FROM marketing.data_enrichment_log WHERE enrichment_type IN ('executive','linkedin','profile') GROUP BY agent_name;"
```

---

## 📖 ESSENTIAL DOCUMENTATION FILES

### Barton Outreach Core

1. **OUTREACH_DOCTRINE_A_Z_v1.3.2.md** - Complete system documentation (ALWAYS READ FIRST)
2. **FINAL_AUDIT_SUMMARY.md** - 100% compliance audit & achievement summary
3. **infra/docs/ENRICHMENT_TRACKING_QUERIES.sql** - All enrichment monitoring queries
4. **infra/docs/svg-ple-todo.md** - Project tracker (53% complete, GitHub Projects synced)
5. **repo-data-diagrams/** - PLE schema documentation (ERD, reference, JSON)
6. **docs/schema_map.json** - Auto-generated Neon database schema reference

### IMO Creator (Sister Repo)

1. **COMPOSIO_INTEGRATION.md** - Primary integration guide (ALWAYS READ FIRST for MCP)
2. **CLAUDE.md** - IMO Creator bootstrap guide
3. **docs/composio_connection.md** - Additional connection details
4. **render.yaml** - Deployment configuration
5. **firebase_mcp.js** - Firebase integration patterns

---

## 📊 OUTREACH PHASE REGISTRY

### What is the Phase Registry?

The **Outreach Phase Registry** (`ctb/sys/toolbox-hub/backend/outreach_phase_registry.py`) is a central catalog that maps each phase of the outreach pipeline to callable functions. This enables:
- **Error Handling & Retries:** "Retry Phase 2 for company XYZ"
- **Phase-Based Execution:** Track which phase a company/person is in
- **Automated Workflows:** Execute phases in sequence
- **Claude Code Integration:** Direct function calls from phase_id

### 7 Pipeline Phases

```
Phase 0: Intake Load
    ↓
Phase 1: Company Validation ✅ IMPLEMENTED
    ↓
Phase 2: Person Validation ✅ IMPLEMENTED
    ↓
Phase 3: Outreach Readiness Evaluation ✅ IMPLEMENTED
    ↓
Phase 4: BIT Trigger Check (planned)
    ↓
Phase 5: BIT Score Calculation (planned)
    ↓
Phase 6: Promotion to Outreach Log (planned)
```

**Current Completion:** 42.86% (3/7 phases implemented)

### Using the Phase Registry

```python
from backend.outreach_phase_registry import get_phase_entry, execute_phase

# Get phase details
phase = get_phase_entry(2)  # Person Validation
print(f"Phase: {phase['phase_name']}")
print(f"File: {phase['file']}")
print(f"Function: {phase['function']}")

# Execute phase function
result = execute_phase(2, person_record, valid_company_ids)
print(f"Valid: {result['valid']}")

# Get all implemented phases
from backend.outreach_phase_registry import get_implemented_phases
for phase in get_implemented_phases():
    print(f"✅ Phase {phase['phase_id']}: {phase['phase_name']}")
```

### Phase Details Reference

| Phase ID | Name | Status | File | Function |
|----------|------|--------|------|----------|
| 0 | Intake Load | Planned | `backend/intake/load_intake_data.py` | `load_raw_records` |
| 1 | Company Validation | ✅ Implemented | `backend/validator/validation_rules.py` | `validate_company` |
| 2 | Person Validation | ✅ Implemented | `backend/validator/validation_rules.py` | `validate_person` |
| 3 | Outreach Readiness | ✅ Implemented | `backend/enrichment/evaluate_outreach_readiness.py` | `evaluate_company_readiness` |
| 4 | BIT Trigger Check | Planned | `backend/bit_engine/bit_trigger.py` | `check_bit_trigger_conditions` |
| 5 | BIT Score Calculation | Planned | `backend/bit_engine/bit_score.py` | `calculate_bit_score` |
| 6 | Promotion to Outreach Log | Planned | `backend/outreach/promote_to_log.py` | `promote_contact_to_outreach` |

### Integration Points

**Database Tables:**
- `shq.error_master.phase_id` - Error tracking by phase
- `marketing.pipeline_events.phase_id` - Event logging by phase
- `marketing.company_manual_override` - Manual override table

**Doctrine Entry:**
```json
{
  "doctrine_id": "04.04.02.04.ple.validation_pipeline",
  "description": "Outreach validation and enrichment lifecycle",
  "phases": [0, 1, 2, 3, 4, 5, 6],
  "barton_id_format": "04.04.02.04.XXXXX.###"
}
```

### Helper Functions

```python
# Get phase by name
phase = get_phase_by_name("Person Validation")

# Get phase dependencies
deps = get_phase_dependencies(3)  # Returns [Phase 1, Phase 2]

# Get next phase
next_phase = get_next_phase(2)  # Returns Phase 3

# Validate phase sequence
is_valid = validate_phase_sequence([1, 2, 3])  # True

# Get completion status
summary = get_phase_status_summary()
# {'total': 7, 'implemented': 3, 'planned': 4, 'completion_pct': 42.86}
```

### Claude Code Usage Pattern

When asked to retry or execute a phase:

```python
# Example: "Retry Phase 2 for company XYZ"

# 1. Get phase details
from backend.outreach_phase_registry import get_phase_entry, get_phase_function

phase = get_phase_entry(2)  # Person Validation
print(f"Executing Phase {phase['phase_id']}: {phase['phase_name']}")

# 2. Get the function
validate_person = get_phase_function(2)

# 3. Load data
person = load_person_by_company("company_xyz")
valid_company_ids = load_valid_company_ids()

# 4. Execute
result = validate_person(person, valid_company_ids)

# 5. Log to pipeline_events
log_pipeline_event("person_validation_check", {
    "person_id": person["person_id"],
    "valid": result["valid"],
    "reason": result["reason"],
    "phase_id": 2
})
```

**See:** `ctb/sys/toolbox-hub/backend/outreach_phase_registry.py` for complete API

---

## 🔄 TYPICAL WORKFLOWS

### Development Session Start

```bash
# 1. Check database connectivity
psql postgresql://Marketing_DB_owner:endpoint=ep-ancient-waterfall-a42vy0du;npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing_DB?sslmode=require -c "SELECT 'DB Connected' as status;"

# 2. Check recent errors
psql -c "SELECT error_code, error_message, severity, created_at FROM public.shq_error_log WHERE severity IN ('error','critical') ORDER BY created_at DESC LIMIT 10;"

# 3. If using Google services: Start Composio MCP
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\scraping-tool\imo-creator\mcp-servers\composio-mcp"
node server.js &

# 4. Review project status
cat infra/docs/svg-ple-todo.md
```

### Adding New Company Data

```sql
-- 1. Insert to intake.company_raw_intake (staging)
INSERT INTO intake.company_raw_intake (company_name, industry, employee_count, source)
VALUES ('Example Corp', 'Technology', 500, 'CSV Upload');

-- 2. Promote to marketing.company_master (generates Barton ID: 04.04.02.04.30000.###)
-- (This should be done by your data pipeline, not manually)

-- 3. Create executive slots (generates Barton IDs: 04.04.02.04.10000.###)
-- (Auto-created by pipeline for CEO/CFO/HR positions)

-- 4. Verify
SELECT * FROM marketing.company_master WHERE company_name = 'Example Corp';
SELECT * FROM marketing.company_slot WHERE company_unique_id = '<company_unique_id>';
```

### Triggering Executive Enrichment

```bash
# Manual trigger via API (if you have enrichment API set up)
curl -X POST http://localhost:8000/api/v1/enrichment/trigger \
  -H "Content-Type: application/json" \
  -d '{"company_unique_id": "04.04.02.04.30000.001", "slot_type": "CEO"}'

# Check enrichment status
psql -c "SELECT * FROM marketing.data_enrichment_log WHERE company_unique_id = '04.04.02.04.30000.001' ORDER BY started_at DESC LIMIT 5;"
```

### Deploying to Production

```bash
# 1. Run compliance check
npm run compliance:complete

# 2. Sync GitHub Projects
./infra/scripts/auto-sync-svg-ple-github.sh --once

# 3. Refresh schema map
node infra/scripts/schema-refresh.js

# 4. Commit changes
git add .
git commit -m "feat: description of changes

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. Push to GitHub
git push origin main

# 6. Monitor deployment logs
# (If using Render/Vercel for IMO Creator)
```

---

## 💡 OPTIMIZATION TIPS

### For Barton Outreach Core

- **Use Neon Console for quick queries**: https://console.neon.tech
- **Use DBeaver for advanced SQL work** (won't conflict with development tools)
- **Auto-sync GitHub Projects** with watch mode for real-time updates
- **Batch enrichment jobs** to avoid rate limiting
- **Monitor `shq_error_log`** table daily for systemic issues
- **Use prepared statements** for all SQL queries (security + performance)

### For IMO Creator

- **Use Task tool** for complex multi-file operations
- **Batch curl commands** for parallel MCP testing
- **Reference existing patterns** before creating new integrations
- **Keep MCP server running** throughout development session
- **Test with curl first** before implementing in code

### For Both

- **Follow Barton Doctrine** for all ID generation
- **Use HEIR/ORBT format** for all MCP calls
- **Log everything** to appropriate error/audit tables
- **Read the docs first** (OUTREACH_DOCTRINE_A_Z, COMPOSIO_INTEGRATION)
- **Use `.env` files** for all credentials (never hardcode)

---

## 🆘 EMERGENCY CONTACTS & RESOURCES

### Documentation

- **Barton Outreach Doctrine**: `OUTREACH_DOCTRINE_A_Z_v1.3.2.md`
- **100% Compliance Audit**: `FINAL_AUDIT_SUMMARY.md`
- **PLE Schema Reference**: `repo-data-diagrams/`
- **Composio Docs**: https://docs.composio.dev
- **MCP Specification**: https://modelcontextprotocol.io
- **Neon Docs**: https://neon.tech/docs

### Services

- **Neon Console**: https://console.neon.tech
- **Composio Dashboard**: https://app.composio.dev
- **GitHub Projects**: https://github.com/users/dbarton/projects

### Key Files Quick Reference

```bash
# Database credentials
cat .env | grep NEON

# Enrichment queries
cat infra/docs/ENRICHMENT_TRACKING_QUERIES.sql

# Schema reference
cat docs/schema_map.json

# PLE ERD
cat repo-data-diagrams/PLE_SCHEMA_ERD.md

# Project status
cat infra/docs/svg-ple-todo.md

# Error log
psql -c "SELECT * FROM public.shq_error_log ORDER BY created_at DESC LIMIT 20;"
```

---

## 📊 CURRENT PROJECT STATUS

### Barton Outreach Core

**Overall Progress**: 100% Compliant with Outreach Doctrine A→Z v1.3.2

**Completed** (✅):
1. ✅ Structural Integrity: All folders and files present
2. ✅ Schema Validation: `shq_error_log` table created with 8 indexes
3. ✅ Numbering System: 222+ occurrences of 6-part Barton IDs
4. ✅ Error Logging: Database table + sync scripts operational
5. ✅ Composio Integration: MCP integration complete, legacy archived
6. ✅ Firebase: 11 Firebase widgets configured
7. ✅ Automation Scripts: schema:refresh, sync:errors, compliance:complete
8. ✅ Documentation Cross-Links: Section 14 added (162 lines)
9. ✅ PLE Schema Documentation: ERD, Reference, JSON in repo-data-diagrams/

**In Progress** (🔄):
- SVG-PLE Implementation: 53% complete (16/30 tasks)
  - Phase 1: Environment & Baseline (100%)
  - Phase 2: BIT Infrastructure (100%)
  - Phase 3: Enrichment Spoke (80%)
  - Phase 4: Renewal & PLE Integration (40%)
  - Phase 6: Verification & QA (17%)

### IMO Creator (Sister Repo)

**Status**: All systems verified and operational
- Composio MCP: Running on port 3001
- Google Workspace: 3 Gmail, 3 Drive, 1 Calendar, 1 Sheets accounts
- Render deployment: Active
- Vercel deployment: 2 projects active
- Firebase MCP: Ready

---

## 🎯 REMEMBER

**For Barton Outreach Core**:
- ✅ Neon PostgreSQL is your single source of truth
- ✅ All enrichment tracking via SQL queries
- ✅ Barton IDs: `04.04.02.04.#####.###`
- ✅ Log everything to `shq_error_log`
- ✅ PLE schema docs in `repo-data-diagrams/`

**For IMO Creator**:
- ✅ Composio MCP handles ALL external API integrations
- ✅ Use HEIR/ORBT payload format for MCP calls
- ✅ Google services via Composio (never direct API)
- ✅ Render for backend, Vercel for frontend

**For Both**:
- ✅ Everything is pre-configured and tested
- ✅ Don't reinvent - use existing patterns
- ✅ Read the docs first (saves time and prevents errors)
- ✅ Follow Barton Doctrine for consistency

---

**Last Updated**: 2025-11-26
**Barton Outreach Core Status**: 100% Compliant, Production Ready
**IMO Creator Status**: All Systems Operational
**Total Achievement**: 1,800+ lines of code/docs, 20+ files, 4 commits, Production-ready monitoring
