# 📂 Repository Structure

**Project:** Barton Outreach Core (Event-Driven Pipeline)
**Architecture:** Neon PostgreSQL + n8n Cloud Orchestration
**Last Updated:** 2025-10-24

---

## 🗂️ Directory Overview

```
barton-outreach-core/
│
├── migrations/                    # Database schema migrations
│   ├── 001_initial_schema.sql
│   ├── 002_barton_ids.sql
│   ├── 003_*.sql
│   ├── 004_*.sql
│   ├── 005_neon_pipeline_triggers.sql    ← Event-driven triggers
│   ├── 006_pipeline_error_log.sql        ← Error logging system
│   └── MIGRATION_LOG.md                  # Migration history
│
├── workflows/                     # n8n workflow definitions & scripts
│   ├── 01-validation-gatekeeper-updated.json
│   ├── 02-promotion-runner.json
│   ├── 03-slot-creator.json
│   ├── 04-apify-enrichment-throttled.json
│   ├── 05-millionverify-checker-updated.json
│   ├── n8n_webhook_registry.json         # Webhook URL mappings
│   ├── bootstrap_n8n.js                  # Deploy workflows to n8n
│   ├── deploy_event_system.js            # Deploy event triggers
│   ├── deploy_with_owner.js              # Deploy with DB owner
│   ├── run_simple_pipeline.js            # Manual pipeline test
│   ├── complete_slots.js                 # Slot creation utility
│   └── .env                              # Environment variables (gitignored)
│
├── docs/                          # Documentation
│   ├── PIPELINE_EVENT_FLOW.md            # Event chain diagrams
│   ├── EVENT_DRIVEN_DEPLOYMENT_GUIDE.md  # Deployment instructions
│   └── *.md                              # Other docs
│
├── ui_specs/                      # UI specifications & wireframes
│   └── README.md                         # UI design guidelines
│
├── ops/                           # Operations & monitoring
│   └── README_OUTREACH_OPS.md            # Operational runbook
│
├── ctb/                           # Codebase organization (existing)
│   ├── ai/                               # AI/ML components
│   ├── docs/                             # Legacy docs
│   ├── meta/                             # Metadata
│   ├── sys/                              # System utilities
│   └── ui/                               # UI components
│
├── libs/                          # Shared libraries
├── logs/                          # Application logs (gitignored)
├── node_modules/                  # NPM dependencies (gitignored)
│
├── .gitignore                     # Git ignore rules
├── package.json                   # Node.js dependencies
├── EVENT_DRIVEN_SYSTEM_README.md  # Quick start guide
├── PIPELINE_SUCCESS_REPORT.md     # Initial deployment report
└── REPO_STRUCTURE.md              # This file
```

---

## 📊 Key Components by Phase

### Phase 1: Enrichment (Data Gathering)

**Database Tables:**
- `intake.company_raw_intake` - CSV imports
- `marketing.company_master` - Validated companies
- `marketing.company_slots` - Executive slots
- `marketing.contact_enrichment` - LinkedIn data
- `marketing.email_verification` - Email validation

**Workflows:**
- `01-validation-gatekeeper-updated.json` - Validate companies
- `02-promotion-runner.json` - Promote to master
- `03-slot-creator.json` - Create exec slots
- `04-apify-enrichment-throttled.json` - LinkedIn enrichment
- `05-millionverify-checker-updated.json` - Email verification

**Scripts:**
- `workflows/run_simple_pipeline.js` - Test full pipeline
- `workflows/complete_slots.js` - Backfill missing slots

---

### Phase 2: Messaging (Planned)

**Database Tables (To Be Created):**
- `marketing.campaigns` - Campaign definitions
- `marketing.campaign_contacts` - Contact assignments
- `marketing.message_templates` - Email templates
- `marketing.message_queue` - Queued messages
- `marketing.delivery_log` - Send results

**Workflows (To Be Created):**
- Campaign Segment Builder
- Message Personalizer
- Campaign Scheduler
- Email Sender
- Delivery Tracker

---

### Phase 3: Delivery & Engagement (Planned)

**Database Tables (To Be Created):**
- `marketing.engagement_events` - Opens, clicks, replies
- `marketing.responses` - Email replies
- `marketing.lead_scores` - Lead scoring
- `marketing.crm_sync_log` - CRM integration
- `marketing.follow_up_queue` - Follow-up automation

**Workflows (To Be Created):**
- Engagement Tracker
- Response Processor
- Lead Scorer
- CRM Syncer
- Follow-Up Automator

---

## 🔧 Configuration Files

### Environment Variables (.env)

**Location:** `workflows/.env` (gitignored)

```env
# Database
NEON_PASSWORD=n8n_secure_ivq5lxz3ej

# n8n Cloud
N8N_API_URL=https://dbarton.app.n8n.cloud
N8N_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Keys
APIFY_TOKEN=your_apify_token
MILLIONVERIFIER_KEY=your_millionverifier_key
```

### Webhook Registry

**Location:** `workflows/n8n_webhook_registry.json`

Maps event types to n8n webhook URLs:
- `company_created` → `/webhook/validate-company`
- `company_validated` → `/webhook/promote-company`
- `company_promoted` → `/webhook/create-slots`
- etc.

---

## 🚀 Quick Start Commands

### Deploy Event System

```bash
cd workflows
node deploy_with_owner.js
```

### Run Pipeline Test

```bash
cd workflows
node run_simple_pipeline.js
```

### Bootstrap n8n Workflows

```bash
cd workflows
node bootstrap_n8n.js
```

### Check Event Queue

```sql
SELECT * FROM marketing.pipeline_events
WHERE status = 'pending'
ORDER BY created_at DESC;
```

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| `EVENT_DRIVEN_SYSTEM_README.md` | Quick start guide |
| `PIPELINE_SUCCESS_REPORT.md` | Initial deployment report |
| `docs/PIPELINE_EVENT_FLOW.md` | Event chain & flow diagrams |
| `docs/EVENT_DRIVEN_DEPLOYMENT_GUIDE.md` | Step-by-step deployment |
| `ops/README_OUTREACH_OPS.md` | Operational runbook |
| `ui_specs/README.md` | UI design guidelines |
| `migrations/MIGRATION_LOG.md` | Database migration history |
| `REPO_STRUCTURE.md` | This file |

---

## 🔐 Security Notes

### Sensitive Files (Gitignored)

- `workflows/.env` - Environment variables
- `*_CREDENTIALS.txt` - API credentials
- `*_API_KEY.txt` - API keys
- `workflows/*_backup.json` - Workflow backups
- `n8n-data/` - n8n local data

### Access Control

- **Database Owner:** Full schema/trigger creation
- **n8n User:** Table read/write, function execution
- **Application User:** Query-only access (future)

---

## 🛠️ Development Workflow

### 1. Database Changes

```bash
# Create new migration
echo "-- Migration XXX_description.sql" > migrations/XXX_description.sql

# Test migration
node -e "/* run migration */"

# Document in MIGRATION_LOG.md
```

### 2. n8n Workflow Changes

```bash
# Export workflow from n8n UI
# Save to workflows/XX-workflow-name.json

# Update webhook registry if URLs changed
# Edit workflows/n8n_webhook_registry.json
```

### 3. Documentation Updates

```bash
# Update relevant docs
# - EVENT_DRIVEN_DEPLOYMENT_GUIDE.md for deployment changes
# - README_OUTREACH_OPS.md for operational changes
# - PIPELINE_EVENT_FLOW.md for event chain changes
```

---

## 📈 Monitoring Locations

### Real-Time
- **n8n UI:** https://dbarton.app.n8n.cloud
- **n8n API:** `GET /api/v1/executions`

### Historical
- **Event Queue:** `marketing.pipeline_events`
- **Error Log:** `marketing.pipeline_errors`
- **Performance:** `marketing.vw_error_rate_24h`

---

## 🎯 Current Status

| Component | Status |
|-----------|--------|
| **Database Triggers** | ✅ Deployed (005, 006) |
| **Event Queue** | ✅ Active |
| **Error Logging** | ✅ Active |
| **n8n Workflows (Phase 1)** | ✅ Deployed |
| **Enrichment Pipeline** | ✅ Tested & Working |
| **Messaging Pipeline (Phase 2)** | 📋 Planned |
| **Delivery Pipeline (Phase 3)** | 📋 Planned |
| **UI Dashboard** | 📋 Planned |
| **Intelligence (PLE/BIT)** | 📋 Planned |

---

## 🚦 Next Steps

1. ✅ ~~Deploy event-driven triggers~~
2. ✅ ~~Test enrichment pipeline~~
3. ✅ ~~Create operational documentation~~
4. 🔄 Create n8n webhook workflows
5. 🔄 Update webhook registry with production URLs
6. 📋 Design Phase 2 (Messaging) schema
7. 📋 Implement campaign management workflows
8. 📋 Build monitoring dashboard UI
9. 📋 Add PLE (Pipeline Learning Engine)
10. 📋 Add BIT (Barton Intelligence Tracker)

---

**Repo Status:** 🟢 Production Ready (Phase 1)
**Last Updated:** 2025-10-24
**Maintained By:** Pipeline Team
