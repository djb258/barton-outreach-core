# Barton Toolbox Hub - Backend Integration

## Overview

The Barton Toolbox Hub is a comprehensive suite of 7 backend tools integrated into the `barton-outreach-core` repository following the CTB (Comprehensive Toolbox Branch) structure and Barton Doctrine specifications.

**Blueprint ID:** `04.svg.marketing.outreach.v1`
**Integration Date:** 2025-11-13
**Repository:** barton-outreach-core
**Branch:** `sys/outreach-tools-backend`

---

## Architecture

```
ctb/sys/toolbox-hub/
├── backend/                    # Backend implementations (Python)
│   ├── router/                 # Messy Logic Router
│   ├── validator/              # Neon-powered Validator
│   ├── mapper/                 # Field Mapper
│   ├── parser/                 # Document Parser
│   ├── docfiller/              # Template Filler
│   ├── logger/                 # Logger/Monitor
│   ├── documentation/          # Self-documenting system
│   └── migrations/             # Database migrations
├── frontend/                   # Lovable frontend (React/TypeScript)
│   └── src/                    # Frontend source code
├── config/                     # Configuration files
│   ├── tools_registry.json     # Master tool registry
│   └── n8n_endpoints.config.json  # N8N webhook configs
└── docs/                       # Documentation
    └── integration-summary.md  # Integration details
```

---

## Tools Overview

### 1. Router (Messy Logic)
**Barton ID:** `04.04.02.04.10000.001`
**Altitude:** 20,000 ft
**Purpose:** Routes invalid data to Google Sheets for manual review

**Key Features:**
- Automatic error detection and routing
- Google Sheets integration for manual fixes
- Kill switch at 50% error rate
- HEIR/ORBT payload format support

**API Endpoints:**
- `POST /api/messyflow/route` - Route error to sheet
- `POST /api/messyflow/sheet/create` - Create review sheet
- `GET /api/messyflow/health` - Health check

### 2. Validator (Neon Agent)
**Barton ID:** `04.04.02.04.10000.002`
**Altitude:** 18,000 ft
**Purpose:** Validation engine powered by Neon-stored rules

**Key Features:**
- Dynamic rule loading from Neon database
- Field-level validation (required, format, range)
- Severity levels (info, warning, error, critical)
- Automatic pipeline error logging

**API Endpoints:**
- `POST /api/validator/validate` - Validate record
- `GET /api/validator/rules` - Get validation rules
- `GET /api/validator/stats` - Validation statistics

### 3. Mapper
**Barton ID:** `04.04.02.04.10000.003`
**Altitude:** 16,000 ft
**Purpose:** Field mapping from CSV/API to STAMPED schema

**Key Features:**
- Flexible mapping configurations
- Multiple source format support (CSV, JSON, API)
- Transformation logic support
- Mapping error tracking

**API Endpoints:**
- `POST /api/mapper/map` - Execute mapping
- `GET /api/mapper/mappings` - Get mapping configs

### 4. Parser
**Barton ID:** `04.04.02.04.10000.004`
**Altitude:** 14,000 ft
**Purpose:** Extract structured data from PDF/DOCX files

**Key Features:**
- PDF parsing (PyPDF2)
- DOCX parsing (python-docx)
- Structured data extraction
- Auto-save to intake tables

**API Endpoints:**
- `POST /api/parser/parse` - Parse document
- `GET /api/parser/health` - Health check

### 5. Doc Filler
**Barton ID:** `04.04.02.04.10000.005`
**Altitude:** 12,000 ft
**Purpose:** Fill templates with enriched company/executive data

**Key Features:**
- Jinja2 template engine
- Google Docs integration (optional)
- Multi-template support
- Variable validation

**API Endpoints:**
- `POST /api/doc-filler/fill` - Fill template
- `GET /api/doc-filler/templates` - List templates

### 6. Logger / Monitor
**Barton ID:** `04.04.02.04.10000.006`
**Altitude:** 10,000 ft
**Purpose:** Central dashboard for audit and error tracking

**Key Features:**
- Real-time error monitoring
- Audit log management
- System-wide statistics
- Grafana integration

**API Endpoints:**
- `POST /api/logger/log` - Create log entry
- `GET /api/logger/errors` - Get recent errors
- `GET /api/logger/stats` - System statistics

### 7. Documentation
**Barton ID:** `04.04.02.04.10000.007`
**Altitude:** 8,000 ft
**Purpose:** Self-documenting system with search

**Key Features:**
- Markdown-based documentation
- Full-text search
- Category organization
- Auto-generated API docs

**API Endpoints:**
- `GET /api/docs` - Browse documentation
- `GET /api/docs/search` - Search docs

---

## Database Schema

### New Tables Created

#### `marketing.validation_rules`
Stores validation rules for the Validator tool.

#### `config.field_mappings`
Stores field mapping configurations for the Mapper tool.

#### `config.document_templates`
Stores document templates for the Doc Filler tool.

#### `config.documentation`
Stores self-documentation for the Documentation tool.

### Existing Tables Used

- `marketing.company_master` - Company records
- `marketing.people_master` - Contact/executive data
- `marketing.company_slot` - Executive position tracking
- `marketing.data_enrichment_log` - Enrichment tracking
- `marketing.pipeline_errors` - Error routing
- `marketing.duplicate_queue` - Duplicate management
- `shq.audit_log` - System-wide audit log
- `shq.error_master` - System-wide error log
- `intake.company_raw_intake` - Raw data staging

---

## Setup Instructions

### 1. Prerequisites

- Neon PostgreSQL database access
- Python 3.9+ with pip
- Node.js 18+ (for frontend)
- Google Workspace account (for Router and DocFiller)
- N8N instance (optional, for webhook automation)

### 2. Environment Configuration

Copy `.env.template` to `.env`:

```bash
cp ctb/sys/toolbox-hub/.env.template .env
```

Update with your credentials:
- `NEON_CONNECTION_STRING` - Neon database URL
- `GOOGLE_SHEETS_API_KEY` - Google Sheets API key
- `GOOGLE_SERVICE_ACCOUNT_EMAIL` - Service account email
- `GRAFANA_API_TOKEN` - Grafana Cloud token (optional)
- `N8N_API_KEY` - N8N API key (optional)

### 3. Database Migrations

Run all migrations in order:

```bash
psql $NEON_CONNECTION_STRING -f ctb/sys/toolbox-hub/backend/migrations/001_create_validation_rules.sql
psql $NEON_CONNECTION_STRING -f ctb/sys/toolbox-hub/backend/migrations/002_create_field_mappings.sql
psql $NEON_CONNECTION_STRING -f ctb/sys/toolbox-hub/backend/migrations/003_create_document_templates.sql
psql $NEON_CONNECTION_STRING -f ctb/sys/toolbox-hub/backend/migrations/004_create_documentation_table.sql
```

### 4. Install Dependencies

```bash
# Python dependencies (backend)
pip install psycopg2-binary python-dotenv jinja2

# Optional: PDF/DOCX parsing
pip install PyPDF2 python-docx pandas

# Frontend dependencies
cd ctb/sys/toolbox-hub/frontend
npm install
```

### 5. Run Tools

Each tool can be run independently:

```bash
# Router
python ctb/sys/toolbox-hub/backend/router/main.py

# Validator
python ctb/sys/toolbox-hub/backend/validator/main.py

# Mapper
python ctb/sys/toolbox-hub/backend/mapper/main.py

# Logger
python ctb/sys/toolbox-hub/backend/logger/main.py
```

### 6. Frontend Development

```bash
cd ctb/sys/toolbox-hub/frontend
npm run dev
```

Access at: `http://localhost:5173`

---

## N8N Integration

All tools support N8N webhook integration. See `config/n8n_endpoints.config.json` for complete webhook specifications.

### Example: Trigger Validation via N8N

```bash
curl -X POST https://n8n.barton.com/hooks/validator \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $N8N_API_KEY" \
  -d '{
    "event_type": "validation.requested",
    "table_name": "company_master",
    "record_id": "04.04.02.04.30000.001",
    "heir_id": "HEIR-2025-11-VALIDATE-001",
    "process_id": "PRC-VALIDATE-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

---

## Kill Switches

Each tool has configurable kill switches for safety:

| Tool | Condition | Threshold | Action |
|------|-----------|-----------|--------|
| Router | Error rate | 50% | Halt and notify |
| Validator | Validation failures | 100 | Halt and notify |
| Mapper | Mapping errors | 50 | Halt and notify |
| Parser | Parse failures | 20 | Halt and notify |
| DocFiller | Template errors | 10 | Halt and notify |
| Logger | Critical errors | 5 | Halt and notify |

---

## Monitoring

### Grafana Dashboards

All tools log to Neon tables that can be visualized in Grafana Cloud:

- **System Health Dashboard** - Overall toolbox health
- **Error Tracking Dashboard** - Real-time error monitoring
- **Tool Performance Dashboard** - Individual tool metrics

Access at: https://dbarton.grafana.net

### Database Queries

Key monitoring queries:

```sql
-- Recent errors across all tools
SELECT * FROM shq.error_master
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Tool audit trail
SELECT * FROM shq.audit_log
WHERE barton_id LIKE '04.04.02.04.10000.%'
ORDER BY created_at DESC;

-- Validation rule effectiveness
SELECT rule_name, COUNT(*) as uses
FROM marketing.validation_rules
GROUP BY rule_name
ORDER BY uses DESC;
```

---

## Development

### Adding a New Tool

1. Create tool directory: `ctb/sys/toolbox-hub/backend/{tool_name}/`
2. Create `tool.config.json` with Barton ID
3. Create `main.py` with tool logic
4. Add to `config/tools_registry.json`
5. Create migration if needed
6. Update documentation

### Code Style

- Follow PEP 8 for Python
- Use type hints
- Include docstrings
- Log all actions to `shq.audit_log`
- Log errors to `shq.error_master`
- Use Barton Doctrine IDs in all logs

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $NEON_CONNECTION_STRING -c "SELECT NOW();"

# Check tables exist
psql $NEON_CONNECTION_STRING -c "\dt marketing.*"
```

### Google Sheets Integration

If sheets aren't creating:
- Verify `GOOGLE_SHEETS_API_KEY` is set
- Check service account has Sheet creation permissions
- Review logs in `shq.error_master`

### N8N Webhooks

If webhooks aren't triggering:
- Verify `N8N_API_KEY` is correct
- Check webhook URLs in `config/n8n_endpoints.config.json`
- Test with curl first

---

## Support

For issues or questions:
- Check `config/documentation` table in Neon
- Review `docs/integration-summary.md`
- Check audit logs: `SELECT * FROM shq.audit_log ORDER BY created_at DESC LIMIT 100;`
- Review error logs: `SELECT * FROM shq.error_master WHERE severity = 'critical';`

---

## License

Part of the Barton Outreach Core ecosystem.

**Last Updated:** 2025-11-13
**Version:** 1.0.0
**Status:** Production Ready ✅
