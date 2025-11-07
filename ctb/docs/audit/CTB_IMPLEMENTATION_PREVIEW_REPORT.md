# CTB Implementation Preview Report
**Repository**: barton-outreach-core
**Generated**: 2025-11-07
**CTB Version**: 1.3.3
**Status**: PREVIEW ONLY - NO CHANGES MADE

---

## Executive Summary

This report analyzes the barton-outreach-core repository against the CTB (Christmas Tree Backbone) Doctrine requirements from global-config and identifies all changes needed for 100% compliance.

**Current State**:
- ✅ CTB directory structure exists
- ✅ 5/6 main branches present (sys, ai, data, docs, ui, meta)
- ⚠️ Many files still at root level outside CTB
- ⚠️ Several required sys/* subdirectories missing
- ⚠️ Configuration files need to be added

**Estimated Impact**:
- **Files to move**: ~120+ files
- **Directories to create**: ~15-20
- **Config files to add**: ~10
- **Documentation updates**: ~5 files
- **Risk Level**: MEDIUM (many file moves, potential import breakages)

---

## 1. Current Repository Analysis

### 1.1 Existing CTB Structure

The repository has a `ctb/` directory with the following branches:

#### ✅ **Present Branches (5/6)**:

**ctb/sys/** - System Infrastructure
- Contains: activepieces, api, chartdb, claude-skills, cli, composio-mcp, factory, firebase, firebase-workbench, github-factory, github-projects, global-factory, grafana, libs, mechanic, modules, n8n, neon-vault, nodes, ops, security-audit, services, tests, tools, windmill
- Status: ✅ Most infrastructure present

**ctb/ai/** - AI/Agent Layer
- Contains: AGENT_GUIDE.md, garage-bay/, agents/, mcp-tasks/, models/, prompts/, scripts/, testing/, tools/
- Status: ✅ Well-organized

**ctb/data/** - Data Layer
- Contains: infra/, migrations/
- Status: ✅ Basic structure present

**ctb/docs/** - Documentation Layer
- Contains: analysis/, archive/, audit/, blueprints/, branches/, config/, diagrams/, examples/, obsidian-vault/, pages/, scripts/, toolbox/, wiki/
- Status: ✅ Comprehensive documentation structure

**ctb/ui/** - UI Layer
- Contains: apps/, components/, lovable/, packages/, pages/, placeholders/, public/, src/, templates/
- Status: ✅ UI structure present

**ctb/meta/** - Meta Configuration Layer
- Contains: .devcontainer/, .gitingest/, config/, global-config/
- Status: ✅ Meta layer present

#### ⚠️ **Missing Branch**:
- **ops/** - Operations branch (for automation scripts, reporting) - MISSING at CTB level

### 1.2 Root-Level Directories (Outside CTB)

The following directories exist at root level and need evaluation:

1. **apps/** - UI applications (should move to ctb/ui/apps or stay at root?)
2. **archive/** - Historical files (should move to ctb/docs/archive)
3. **dist/** - Build artifacts (should stay at root - gitignored)
4. **docs/** - Documentation (DUPLICATE - already exists in ctb/docs)
5. **doctrine/** - Doctrine files (should move to ctb/meta or ctb/docs)
6. **global-config/** - Global configuration (should move to ctb/meta/global-config)
7. **grafana/** - Grafana configs (should move to ctb/sys/grafana or ctb/meta/config)
8. **HEIR-AGENT-SYSTEM/** - HEIR agent files (should move to ctb/ai/agents)
9. **ids/** - ID-related files (should move to ctb/meta or ctb/data)
10. **infra/** - Infrastructure configs (should move to ctb/sys or ctb/data/infra)
11. **libs/** - Shared libraries (should move to ctb/sys/libs)
12. **logs/** - Log files (should stay at root - gitignored)
13. **migrations/** - Database migrations (should move to ctb/data/migrations)
14. **node_modules/** - Dependencies (should stay at root - gitignored)
15. **ops/** - Operations scripts (should move to ctb/sys/ops or create ctb/ops)
16. **src/** - Source code (should move to ctb/ai or appropriate branch)
17. **ui/** - UI files (DUPLICATE - already exists in ctb/ui)
18. **ui_specs/** - UI specifications (should move to ctb/ui/specs or ctb/docs)
19. **workflows/** - N8N workflows (should move to ctb/sys/n8n or ctb/ai)

---

## 2. Required CTB Structure (from global-config)

### 2.1 Six CTB Branches (from ctb.branchmap.yaml)

According to the CTB Doctrine, repositories should have these branches at altitude levels:

#### **40k Altitude - Doctrine Core** (System Infrastructure)
Required sys/* subdirectories:
1. ✅ sys/composio-mcp
2. ✅ sys/neon-vault
3. ✅ sys/firebase-workbench
4. ⚠️ **sys/bigquery-warehouse** - MISSING
5. ✅ sys/github-factory
6. ⚠️ **sys/builder-bridge** - MISSING
7. ✅ sys/security-audit
8. ✅ sys/chartdb
9. ✅ sys/activepieces
10. ✅ sys/windmill
11. ✅ sys/claude-skills
12. ⚠️ **sys/deepwiki** - MISSING (doctrine_id: 04.04.11)

#### **Other Branches**
- ✅ ai/ - Present
- ✅ data/ - Present
- ✅ docs/ - Present
- ✅ ui/ - Present
- ✅ meta/ - Present
- ⚠️ **ops/** - Should be created at ctb/ops level (per doctrine)

### 2.2 Required Configuration Files (from repo_organization_standard.yaml)

#### Root Level Required Files:
1. ✅ README.md - Present
2. ✅ CLAUDE.md - Present
3. ⚠️ **LLM_ONBOARDING.md** - MISSING
4. ✅ .env.example - Present
5. ✅ .gitignore - Present
6. ✅ LICENSE - Present
7. ✅ package.json - Present
8. ✅ requirements.txt - Present

#### .barton/ Directory (Should exist at root):
- ⚠️ **.barton/** - Directory MISSING
  - ⚠️ **.barton/repo_config.yaml** - MISSING
  - ⚠️ **.barton/doctrine_id.txt** - MISSING
  - ⚠️ **.barton/hive_assignment.txt** - MISSING

#### config/ Directory (Should exist at root):
- ⚠️ **config/** - Directory MISSING at root level
  - ⚠️ **config/mcp_registry.json** - MISSING (exists in ctb/meta/config but should also be at root)
  - ⚠️ **config/deployment_config.yaml** - MISSING
  - ⚠️ **config/feature_flags.json** - MISSING

#### CTB-specific Configuration:
- ⚠️ **ctb/meta/config/ctb_config.json** - MISSING
- ✅ ctb/meta/global-config/ - Present (has CTB_DOCTRINE.md, ctb.branchmap.yaml, etc.)
- ⚠️ **ctb/sys/README.md** - MISSING (branch overview)
- ⚠️ **ctb/ai/README.md** - Could be enhanced
- ⚠️ **ctb/data/README.md** - MISSING
- ⚠️ **ctb/docs/README.md** - MISSING
- ⚠️ **ctb/ui/README.md** - MISSING
- ⚠️ **ctb/meta/README.md** - MISSING

---

## 3. Gap Analysis

### 3.1 Missing Directories

#### System Infrastructure (ctb/sys/):
```
CREATE: ctb/sys/deepwiki/
CREATE: ctb/sys/bigquery-warehouse/
CREATE: ctb/sys/builder-bridge/
```

#### Operations Branch:
```
CREATE: ctb/ops/
CREATE: ctb/ops/automation-scripts/
CREATE: ctb/ops/report-builder/
```

#### Root Configuration:
```
CREATE: .barton/
CREATE: config/
```

#### Branch Documentation:
```
CREATE: ctb/sys/README.md
CREATE: ctb/ai/README.md  (enhance existing)
CREATE: ctb/data/README.md
CREATE: ctb/docs/README.md
CREATE: ctb/ui/README.md
CREATE: ctb/meta/README.md
CREATE: ctb/ops/README.md
```

### 3.2 Missing Configuration Files

#### Root Level:
```
CREATE: LLM_ONBOARDING.md
CREATE: .barton/repo_config.yaml
CREATE: .barton/doctrine_id.txt
CREATE: .barton/hive_assignment.txt
CREATE: config/mcp_registry.json  (symlink or copy from ctb/meta/config)
CREATE: config/deployment_config.yaml
CREATE: config/feature_flags.json
```

#### CTB Configuration:
```
CREATE: ctb/meta/config/ctb_config.json
CREATE: ctb/sys/deepwiki/README.md
CREATE: ctb/sys/deepwiki/deepwiki_index.json
CREATE: ctb/sys/bigquery-warehouse/README.md
CREATE: ctb/sys/builder-bridge/README.md
```

### 3.3 Files in Wrong Locations

#### Documentation Files (Root → ctb/docs/):
```
MOVE: ARCHITECTURE_SUMMARY.md → ctb/docs/architecture/ARCHITECTURE_SUMMARY.md
MOVE: BUILDER_IO_INTEGRATION_COMPLETE.md → ctb/docs/integration/BUILDER_IO_INTEGRATION.md
MOVE: BIG_UPDATE_SUMMARY.md → ctb/docs/changelog/BIG_UPDATE_SUMMARY.md
MOVE: COMPOSIO_AGENT_TEMPLATE.md → ctb/ai/templates/COMPOSIO_AGENT_TEMPLATE.md
MOVE: CONTRIBUTING.md → ctb/docs/CONTRIBUTING.md
MOVE: CTB_AUDIT_REPORT.md → ctb/docs/audit/CTB_AUDIT_REPORT.md
MOVE: CTB_COMPLIANCE_REPORT_2025-10-24.md → ctb/docs/audit/CTB_COMPLIANCE_REPORT.md
MOVE: CTB_ENFORCEMENT.md → ctb/meta/CTB_ENFORCEMENT.md
MOVE: CTB_INDEX.md → ctb/meta/CTB_INDEX.md
MOVE: CTB_REMEDIATION_SUMMARY.md → ctb/docs/audit/CTB_REMEDIATION_SUMMARY.md
MOVE: CTB_TAGGING_REPORT.md → ctb/docs/audit/CTB_TAGGING_REPORT.md
MOVE: CTB_VERIFICATION_CHECKLIST.md → ctb/meta/CTB_VERIFICATION_CHECKLIST.md
MOVE: CURRENT_NEON_SCHEMA.md → ctb/data/schemas/CURRENT_NEON_SCHEMA.md
MOVE: DEPENDENCIES.md → ctb/docs/DEPENDENCIES.md
MOVE: ENTRYPOINT.md → ctb/docs/ENTRYPOINT.md
MOVE: EVENT_DRIVEN_SYSTEM_README.md → ctb/docs/architecture/EVENT_DRIVEN_SYSTEM.md
MOVE: GLOBAL_CONFIG_COMPLETE_SYNC.md → ctb/docs/changelog/GLOBAL_CONFIG_SYNC.md
MOVE: GLOBAL_CONFIG_IMPLEMENTATION.md → ctb/meta/global-config/IMPLEMENTATION.md
MOVE: GLOBAL_CONFIG_SYNC_COMPLETE.md → ctb/docs/changelog/GLOBAL_CONFIG_SYNC_COMPLETE.md
MOVE: GRAFANA_*.md (all 8 files) → ctb/sys/grafana/docs/
MOVE: INTEGRATION_GUIDE.md → ctb/docs/guides/INTEGRATION_GUIDE.md
MOVE: N8N_*.md (2 files) → ctb/sys/n8n/docs/
MOVE: NEON_CONNECTION_GUIDE.md → ctb/sys/neon-vault/docs/CONNECTION_GUIDE.md
MOVE: NEW_INTEGRATIONS_SUMMARY.md → ctb/docs/integration/INTEGRATIONS_SUMMARY.md
MOVE: NO_DOCKER_ALTERNATIVES.md → ctb/docs/guides/NO_DOCKER_ALTERNATIVES.md
MOVE: QUICKREF.md → ctb/docs/QUICKREF.md
MOVE: REPO_STRUCTURE.md → ctb/docs/REPO_STRUCTURE.md
MOVE: SCHEMA_QUICK_REFERENCE.md → ctb/data/schemas/QUICK_REFERENCE.md
MOVE: SESSION_SUMMARY_2025-10-24.md → ctb/docs/sessions/SESSION_SUMMARY_2025-10-24.md
MOVE: SUPER_PROMPT_COMPLETION.md → ctb/docs/changelog/SUPER_PROMPT_COMPLETION.md
```

#### Python Scripts (Root → appropriate CTB branch):
```
MOVE: add_email_verification_tracking.py → ctb/data/migrations/add_email_verification_tracking.py
MOVE: assign_messages_to_contacts.py → ctb/data/migrations/assign_messages_to_contacts.py
MOVE: check_companies.py → ctb/sys/tools/check_companies.py
MOVE: check_db_schema.py → ctb/sys/tools/check_db_schema.py
MOVE: check_message_status.py → ctb/sys/tools/check_message_status.py
MOVE: check_pipeline_events.py → ctb/sys/tools/check_pipeline_events.py
MOVE: create_db_views.py → ctb/data/migrations/create_db_views.py
MOVE: setup_messaging_system.py → ctb/sys/tools/setup_messaging_system.py
MOVE: trigger_enrichment.py → ctb/ai/scripts/trigger_enrichment.py
MOVE: start_server.py → ctb/sys/tools/start_server.py
```

#### Source Code (Root src/ → ctb/):
```
MOVE: src/main.py → ctb/ai/main.py  (or ctb/sys/api/main.py if it's API entry point)
```

#### Directories to Move:
```
MOVE: doctrine/ → ctb/meta/doctrine/ or ctb/docs/doctrine/
MOVE: HEIR-AGENT-SYSTEM/ → ctb/ai/agents/HEIR-AGENT-SYSTEM/
MOVE: ids/ → ctb/meta/ids/
MOVE: infra/ → ctb/sys/infra/  (merge with existing ctb/data/infra if overlap)
MOVE: libs/imo_tools/ → ctb/sys/libs/imo_tools/
MOVE: migrations/ → ctb/data/migrations/  (merge with existing)
MOVE: ops/ → ctb/ops/automation-scripts/ or ctb/sys/ops/  (evaluate per file)
MOVE: ui_specs/ → ctb/ui/specs/
MOVE: workflows/ → ctb/sys/n8n/workflows/ or ctb/ai/workflows/
```

#### Configuration Files:
```
MOVE: global-config.yaml → ctb/meta/global-config/global-config.yaml
MOVE: render.yaml → ctb/sys/deployment/render.yaml
MOVE: vercel.json → ctb/sys/deployment/vercel.json
```

#### Special Handling - Duplicate Directories:

**docs/** (Root vs ctb/docs):
- Root `docs/` appears to be duplicate or older
- ACTION: Compare contents, merge into ctb/docs/, delete root docs/

**ui/** (Root vs ctb/ui):
- Root `ui/` appears to be duplicate or older
- ACTION: Compare contents, merge into ctb/ui/, delete root ui/

**global-config/** (Root vs ctb/meta/global-config):
- Root `global-config/` is canonical source
- ACTION: Ensure ctb/meta/global-config is symlink or copy is up-to-date

**grafana/** (Root vs ctb/sys/grafana):
- Root `grafana/` contains configs
- ACTION: Move all to ctb/sys/grafana/

### 3.4 Documentation Gaps

#### Branch README Files Needed:
1. **ctb/sys/README.md** - Overview of all system infrastructure branches
2. **ctb/ai/README.md** - Overview of AI/agent layer (enhance existing AGENT_GUIDE.md)
3. **ctb/data/README.md** - Overview of data layer, schemas, migrations
4. **ctb/docs/README.md** - Documentation navigation guide
5. **ctb/ui/README.md** - UI structure and component guide
6. **ctb/meta/README.md** - Meta-configuration and CTB doctrine guide
7. **ctb/ops/README.md** - Operations and automation guide

#### Missing Required Documentation:
1. **LLM_ONBOARDING.md** (root) - Comprehensive AI agent onboarding
2. **ctb/sys/deepwiki/README.md** - DeepWiki integration guide
3. **ctb/sys/bigquery-warehouse/README.md** - BigQuery setup guide
4. **ctb/sys/builder-bridge/README.md** - Builder.io integration guide

#### Integration Documentation:
1. **ctb/docs/integration/** - Directory for all integration guides
2. **ctb/docs/guides/** - Directory for how-to guides
3. **ctb/docs/architecture/** - Directory for architecture docs
4. **ctb/docs/changelog/** - Directory for change summaries

---

## 4. Proposed Changes Preview

### 4.A. Directories to Create

#### System Infrastructure:
```bash
# Missing sys/* branches
mkdir -p ctb/sys/deepwiki
mkdir -p ctb/sys/bigquery-warehouse
mkdir -p ctb/sys/builder-bridge

# DeepWiki structure
mkdir -p ctb/sys/deepwiki/docs
mkdir -p ctb/sys/deepwiki/output
mkdir -p ctb/sys/deepwiki/config

# BigQuery structure
mkdir -p ctb/sys/bigquery-warehouse/queries
mkdir -p ctb/sys/bigquery-warehouse/dashboards
mkdir -p ctb/sys/bigquery-warehouse/schemas

# Builder.io structure
mkdir -p ctb/sys/builder-bridge/templates
mkdir -p ctb/sys/builder-bridge/components
mkdir -p ctb/sys/builder-bridge/figma
```

#### Operations Branch:
```bash
# Create ops branch at CTB level
mkdir -p ctb/ops
mkdir -p ctb/ops/automation-scripts
mkdir -p ctb/ops/report-builder
```

#### Root Configuration:
```bash
# Create .barton directory
mkdir -p .barton

# Create config directory
mkdir -p config
```

#### Documentation Structure:
```bash
# Organize documentation
mkdir -p ctb/docs/architecture
mkdir -p ctb/docs/integration
mkdir -p ctb/docs/guides
mkdir -p ctb/docs/changelog
mkdir -p ctb/docs/sessions
```

#### Data Organization:
```bash
# Data branch organization
mkdir -p ctb/data/schemas
```

#### UI Organization:
```bash
# UI structure
mkdir -p ctb/ui/specs
```

#### Meta Organization:
```bash
# Meta structure
mkdir -p ctb/meta/doctrine
mkdir -p ctb/meta/ids
```

### 4.B. Configuration Files to Add

#### Root Level Configuration:

**1. LLM_ONBOARDING.md**
```markdown
# AI Agent Onboarding Guide - Barton Outreach Core

## Repository Overview
[Comprehensive orientation for AI agents]
- CTB Architecture explanation
- Branch organization (40k/20k/10k/5k ft)
- HEIR/ORBT concepts
- Security policies
- Common tasks and FAQs
```

**2. .barton/repo_config.yaml**
```yaml
metadata:
  repo_name: "barton-outreach-core"
  hive: "shq"  # SHQ (Strategic HeadQuarters)
  doctrine_id: "SHQ.001"
  ctb_version: "1.3.3"
  last_updated: "2025-11-07"

ctb_compliance:
  version: "1.3.3"
  branches_present:
    - sys
    - ai
    - data
    - docs
    - ui
    - meta
    - ops
```

**3. .barton/doctrine_id.txt**
```
SHQ.001
```

**4. .barton/hive_assignment.txt**
```
shq
```

**5. config/mcp_registry.json**
```json
{
  "engine_version": "1.3.3",
  "last_updated": "2025-11-07",
  "production_urls": {
    "composio_mcp": "http://localhost:3001",
    "firebase": "https://firestore.googleapis.com",
    "neon": "postgres://user@host/db"
  },
  "engine_capabilities": [
    "apify_run_actor",
    "gmail_send",
    "sheets_append",
    "drive_upload"
  ]
}
```

**6. config/deployment_config.yaml**
```yaml
environments:
  development:
    database: "neon-dev"
    api_base: "http://localhost:8000"
  staging:
    database: "neon-staging"
    api_base: "https://staging.barton-outreach.com"
  production:
    database: "neon-prod"
    api_base: "https://api.barton-outreach.com"
```

**7. config/feature_flags.json**
```json
{
  "features": {
    "deepwiki_automation": true,
    "heir_agent_system": true,
    "realtime_sync": false,
    "ai_enrichment": true
  }
}
```

#### CTB-Specific Configuration:

**8. ctb/meta/config/ctb_config.json**
```json
{
  "ctb_version": "1.3.3",
  "branches": {
    "sys": {
      "altitude": "40k",
      "description": "System infrastructure",
      "subdirectories": [
        "composio-mcp", "neon-vault", "firebase-workbench",
        "bigquery-warehouse", "github-factory", "builder-bridge",
        "security-audit", "chartdb", "activepieces", "windmill",
        "claude-skills", "deepwiki"
      ]
    },
    "ai": {
      "altitude": "20k",
      "description": "AI and agent layer"
    },
    "data": {
      "altitude": "20k",
      "description": "Data schemas and migrations"
    },
    "docs": {
      "altitude": "10k",
      "description": "Documentation"
    },
    "ui": {
      "altitude": "10k",
      "description": "User interface components"
    },
    "meta": {
      "altitude": "40k",
      "description": "Meta-configuration and CTB doctrine"
    },
    "ops": {
      "altitude": "5k",
      "description": "Operations and automation"
    }
  }
}
```

**9. ctb/sys/deepwiki/README.md**
```markdown
# DeepWiki - AI-Powered Documentation Generator

Doctrine ID: 04.04.11

## Purpose
Automatically generates and maintains comprehensive repository documentation.

## Setup
[Installation and configuration instructions]

## Integration
- Runs nightly via GitHub Actions
- Outputs to /deep_wiki directory
- Indexes all code and documentation
```

**10. ctb/sys/bigquery-warehouse/README.md**
```markdown
# BigQuery Data Warehouse

## Purpose
Analytics and historical data storage using BigQuery.

## Schema
STACKED (Structured Table Architecture for Calculated Knowledge & Event Data)

## Setup
[Connection and configuration instructions]
```

### 4.C. Files to Move

#### High Priority Moves (120+ files):

**Documentation Files (35+ files)**:
```bash
# Architecture documentation
mv ARCHITECTURE_SUMMARY.md ctb/docs/architecture/
mv EVENT_DRIVEN_SYSTEM_README.md ctb/docs/architecture/
mv REPO_STRUCTURE.md ctb/docs/

# Integration documentation
mv BUILDER_IO_INTEGRATION_COMPLETE.md ctb/docs/integration/BUILDER_IO.md
mv NEW_INTEGRATIONS_SUMMARY.md ctb/docs/integration/SUMMARY.md
mv INTEGRATION_GUIDE.md ctb/docs/guides/

# Audit reports
mv CTB_AUDIT_REPORT.md ctb/docs/audit/
mv CTB_COMPLIANCE_REPORT_2025-10-24.md ctb/docs/audit/
mv CTB_REMEDIATION_SUMMARY.md ctb/docs/audit/
mv CTB_TAGGING_REPORT.md ctb/docs/audit/

# CTB enforcement/meta
mv CTB_ENFORCEMENT.md ctb/meta/
mv CTB_INDEX.md ctb/meta/
mv CTB_VERIFICATION_CHECKLIST.md ctb/meta/

# Change logs
mv BIG_UPDATE_SUMMARY.md ctb/docs/changelog/
mv GLOBAL_CONFIG_COMPLETE_SYNC.md ctb/docs/changelog/
mv GLOBAL_CONFIG_SYNC_COMPLETE.md ctb/docs/changelog/
mv SUPER_PROMPT_COMPLETION.md ctb/docs/changelog/
mv SESSION_SUMMARY_2025-10-24.md ctb/docs/sessions/

# System-specific docs
mv GRAFANA_CLOUD_SETUP_GUIDE.md ctb/sys/grafana/docs/CLOUD_SETUP.md
mv GRAFANA_LOGIN_TROUBLESHOOTING.md ctb/sys/grafana/docs/TROUBLESHOOTING.md
mv GRAFANA_SETUP.md ctb/sys/grafana/docs/SETUP.md
mv GRAFANA_*.md ctb/sys/grafana/docs/  # (all remaining grafana files)

mv N8N_HOSTED_SETUP_GUIDE.md ctb/sys/n8n/docs/HOSTED_SETUP.md
mv N8N_MESSAGING_SETUP.md ctb/sys/n8n/docs/MESSAGING.md

mv NEON_CONNECTION_GUIDE.md ctb/sys/neon-vault/docs/CONNECTION.md
mv CURRENT_NEON_SCHEMA.md ctb/data/schemas/CURRENT_SCHEMA.md
mv SCHEMA_QUICK_REFERENCE.md ctb/data/schemas/QUICK_REFERENCE.md

# General documentation
mv CONTRIBUTING.md ctb/docs/
mv DEPENDENCIES.md ctb/docs/
mv ENTRYPOINT.md ctb/docs/
mv NO_DOCKER_ALTERNATIVES.md ctb/docs/guides/
mv QUICKREF.md ctb/docs/
mv COMPOSIO_AGENT_TEMPLATE.md ctb/ai/templates/
```

**Python Scripts (10 files)**:
```bash
# Database migration scripts
mv add_email_verification_tracking.py ctb/data/migrations/
mv assign_messages_to_contacts.py ctb/data/migrations/
mv create_db_views.py ctb/data/migrations/

# System tools
mv check_companies.py ctb/sys/tools/
mv check_db_schema.py ctb/sys/tools/
mv check_message_status.py ctb/sys/tools/
mv check_pipeline_events.py ctb/sys/tools/
mv setup_messaging_system.py ctb/sys/tools/
mv start_server.py ctb/sys/tools/

# AI scripts
mv trigger_enrichment.py ctb/ai/scripts/
```

**Source Code**:
```bash
# Main entry point
mv src/main.py ctb/ai/main.py
# OR if it's primarily API:
# mv src/main.py ctb/sys/api/main.py
```

**Configuration Files**:
```bash
# Deployment configs
mkdir -p ctb/sys/deployment
mv render.yaml ctb/sys/deployment/
mv vercel.json ctb/sys/deployment/

# Global config
mv global-config.yaml ctb/meta/global-config/
```

**Directories**:
```bash
# Doctrine files
mv doctrine/ ctb/meta/doctrine/

# HEIR Agent System
mv HEIR-AGENT-SYSTEM/ ctb/ai/agents/HEIR-AGENT-SYSTEM/

# IDs
mv ids/ ctb/meta/ids/

# Infrastructure (evaluate overlap with ctb/data/infra first)
# If separate:
mv infra/ ctb/sys/infra/
# If overlapping:
# cp -r infra/* ctb/sys/infra/ && rm -rf infra/

# Libraries
mv libs/imo_tools/ ctb/sys/libs/imo_tools/
rmdir libs/  # if empty

# Migrations (merge with existing ctb/data/migrations)
cp -r migrations/* ctb/data/migrations/
rm -rf migrations/

# Operations
mv ops/ ctb/ops/automation-scripts/

# UI specs
mv ui_specs/ ctb/ui/specs/

# Workflows
mv workflows/ ctb/sys/n8n/workflows/
```

**Handle Duplicates**:
```bash
# Compare and merge docs/
diff -qr docs/ ctb/docs/
# After merging:
rm -rf docs/

# Compare and merge ui/
diff -qr ui/ ctb/ui/
# After merging:
rm -rf ui/

# Compare and merge grafana/
cp -r grafana/* ctb/sys/grafana/
rm -rf grafana/
```

### 4.D. Documentation to Update

**1. README.md** (root)
```markdown
# Add CTB structure explanation section

## CTB Structure

This repository follows the CTB (Christmas Tree Backbone) Doctrine v1.3.3.

### Branch Organization

- **ctb/sys/** - System infrastructure (40k altitude)
- **ctb/ai/** - AI and agent layer (20k altitude)
- **ctb/data/** - Data schemas and migrations (20k altitude)
- **ctb/docs/** - Documentation (10k altitude)
- **ctb/ui/** - User interface (10k altitude)
- **ctb/meta/** - Meta-configuration (40k altitude)
- **ctb/ops/** - Operations and automation (5k altitude)

See [ctb/meta/CTB_INDEX.md](ctb/meta/CTB_INDEX.md) for complete structure.
```

**2. CLAUDE.md** (root)
```markdown
# Update repository structure map to reflect CTB organization

## 📁 REPOSITORY STRUCTURE MAP

```
barton-outreach-core/
├── ctb/                          # CTB (Christmas Tree Backbone)
│   ├── sys/                      # System Infrastructure (40k ft)
│   │   ├── composio-mcp/        # MCP integrations
│   │   ├── neon-vault/          # Database schemas
│   │   ├── firebase-workbench/  # Firestore configs
│   │   ├── deepwiki/            # Documentation automation
│   │   ├── chartdb/             # Schema visualization
│   │   └── ...
│   ├── ai/                       # AI Layer (20k ft)
│   ├── data/                     # Data Layer (20k ft)
│   ├── docs/                     # Documentation (10k ft)
│   ├── ui/                       # UI Layer (10k ft)
│   ├── meta/                     # Meta Config (40k ft)
│   └── ops/                      # Operations (5k ft)
├── apps/                         # Application workspace
├── .barton/                      # Barton Enterprises config
└── config/                       # Runtime configuration
```
```

**3. ARCHITECTURE_SUMMARY.md** → **ctb/docs/architecture/ARCHITECTURE_SUMMARY.md**
```markdown
# Add CTB architecture diagram and explanation
```

**4. ENTRYPOINT.md** → **ctb/docs/ENTRYPOINT.md**
```markdown
# Update paths to reflect CTB structure
```

**5. Create new branch README files** (7 files):
- ctb/sys/README.md
- ctb/ai/README.md
- ctb/data/README.md
- ctb/docs/README.md
- ctb/ui/README.md
- ctb/meta/README.md
- ctb/ops/README.md

---

## 5. Impact Assessment

### 5.1 Quantitative Impact

**Files Affected**:
- Documentation files to move: ~35
- Python scripts to move: ~10
- Configuration files to move: ~5
- Total files to move: **~120+ files**

**Directories Affected**:
- Directories to create: **~20**
- Directories to move: **~10**
- Directories to merge: **3** (docs/, ui/, grafana/)
- Directories to evaluate: **2** (apps/, infra/)

**Configuration Files**:
- New config files to create: **~10**
- Existing config files to update: **~5**

**Documentation**:
- New README files: **7**
- Documentation files to update: **5**
- Total documentation changes: **~50 files**

### 5.2 Potential Breaking Changes

#### Import Path Changes:
```python
# Python imports will break if not updated
# OLD:
from libs.imo_tools import ParserTool

# NEW:
from ctb.sys.libs.imo_tools import ParserTool
```

**Risk**: HIGH - All Python imports need updating
**Mitigation**: Search-and-replace all import statements, run full test suite

#### File Reference Changes:
```javascript
// Configuration paths will break
// OLD:
const config = require('./global-config.yaml');

// NEW:
const config = require('./ctb/meta/global-config/global-config.yaml');
```

**Risk**: MEDIUM - Config loading needs updating
**Mitigation**: Update all require/import paths, test configuration loading

#### Relative Path Breakages:
```markdown
<!-- Documentation links will break -->
<!-- OLD: -->
[See Architecture](ARCHITECTURE_SUMMARY.md)

<!-- NEW: -->
[See Architecture](ctb/docs/architecture/ARCHITECTURE_SUMMARY.md)
```

**Risk**: LOW - Documentation links
**Mitigation**: Use absolute paths from root, or use tool to update all links

#### GitHub Actions Paths:
```yaml
# Workflow paths will break
# OLD:
- run: python check_db_schema.py

# NEW:
- run: python ctb/sys/tools/check_db_schema.py
```

**Risk**: MEDIUM - CI/CD failures
**Mitigation**: Update all workflow files in .github/workflows/

#### Deployment Configurations:
```yaml
# OLD (render.yaml at root):
buildCommand: npm run build

# NEW (at ctb/sys/deployment/render.yaml):
buildCommand: npm run build
```

**Risk**: LOW - Deployment configs can stay at root or use symlinks
**Mitigation**: Keep deployment configs at root, or symlink from ctb/sys/deployment/

### 5.3 Risk Level: MEDIUM

**Risk Factors**:
1. ⚠️ HIGH: Python import path changes (all imports need updating)
2. ⚠️ MEDIUM: Configuration file path changes
3. ⚠️ MEDIUM: GitHub Actions path updates
4. ⚠️ LOW: Documentation link updates
5. ⚠️ LOW: Deployment config locations

**Overall Risk**: **MEDIUM**
- Many file moves required
- Import path changes will break code
- CI/CD pipelines need updates
- But: Repository is well-structured and changes are systematic

---

## 6. Rollback Plan

### 6.1 Version Control Strategy

Before making ANY changes:

```bash
# 1. Create a pre-CTB-migration tag
git tag pre-ctb-migration-$(date +%Y%m%d-%H%M%S)
git push origin --tags

# 2. Create a backup branch
git checkout -b backup/pre-ctb-migration
git push -u origin backup/pre-ctb-migration

# 3. Work on a feature branch
git checkout main
git checkout -b feature/ctb-full-implementation
```

### 6.2 Rollback Commands

If changes need to be undone:

```bash
# Option 1: Soft rollback (keep changes as uncommitted)
git reset --soft pre-ctb-migration-$(date +%Y%m%d-%H%M%S)

# Option 2: Hard rollback (discard all changes)
git reset --hard pre-ctb-migration-$(date +%Y%m%d-%H%M%S)

# Option 3: Revert to backup branch
git checkout backup/pre-ctb-migration
git branch -D feature/ctb-full-implementation
```

### 6.3 Safety Checklist

Before proceeding with changes:
- [ ] Create git tag: `pre-ctb-migration-YYYYMMDD`
- [ ] Create backup branch: `backup/pre-ctb-migration`
- [ ] Run full test suite and document results
- [ ] Export list of all current file paths to `pre-migration-files.txt`
- [ ] Document all import statements to `pre-migration-imports.txt`
- [ ] Backup database (if applicable)
- [ ] Notify team of impending changes

After making changes:
- [ ] Update all Python imports
- [ ] Update all JavaScript/TypeScript imports
- [ ] Update all documentation links
- [ ] Update GitHub Actions workflows
- [ ] Run full test suite
- [ ] Test deployment configuration
- [ ] Verify CI/CD pipelines pass
- [ ] Test application startup and basic functionality

### 6.4 Testing Strategy

**Phase 1: Structural Changes**
1. Create directories
2. Add configuration files
3. Verify structure with: `bash global-config/scripts/ctb_verify.sh`

**Phase 2: File Moves (Do in batches)**
1. Move documentation files first (lowest risk)
2. Move scripts and tools
3. Move source code (highest risk)
4. Update imports/paths after each batch

**Phase 3: Integration Testing**
1. Run Python tests: `pytest`
2. Run JavaScript tests: `npm test`
3. Test GitHub Actions: Trigger workflow runs
4. Test deployment: Deploy to staging environment
5. Verify all services: Check MCP, database, API endpoints

### 6.5 Rollback Criteria

Abort and rollback if:
- [ ] More than 25% of tests fail after changes
- [ ] Critical imports cannot be resolved
- [ ] Deployment fails to staging environment
- [ ] CI/CD pipelines fail repeatedly
- [ ] Team consensus to rollback

---

## 7. Implementation Recommendations

### 7.1 Phased Approach

**Phase 1: Foundation (Low Risk)**
- ✅ Create all missing directories
- ✅ Add all configuration files
- ✅ Create branch README files
- **Duration**: 1-2 hours
- **Risk**: LOW

**Phase 2: Documentation (Low Risk)**
- ✅ Move all documentation files
- ✅ Update documentation links
- ✅ Update README.md and CLAUDE.md
- **Duration**: 2-3 hours
- **Risk**: LOW

**Phase 3: Scripts & Tools (Medium Risk)**
- ✅ Move Python scripts
- ✅ Update script paths in workflows
- ✅ Test script execution
- **Duration**: 2-3 hours
- **Risk**: MEDIUM

**Phase 4: Source Code (High Risk)**
- ✅ Move source code files
- ✅ Update all imports
- ✅ Run full test suite
- **Duration**: 4-6 hours
- **Risk**: HIGH

**Phase 5: Verification (Critical)**
- ✅ Run CTB verification script
- ✅ Test full application stack
- ✅ Deploy to staging
- ✅ Monitor for errors
- **Duration**: 2-4 hours
- **Risk**: MEDIUM

**Total Estimated Duration**: 12-18 hours (1.5-2 days)

### 7.2 Order of Operations

1. **Pre-work** (30 min):
   - Create backup tag and branch
   - Run and document current test results
   - Export current file structure

2. **Phase 1** (1-2 hours):
   - Create directory structure
   - Add configuration files
   - Commit: "feat: add CTB directory structure and configs"

3. **Phase 2** (2-3 hours):
   - Move documentation files in batches of 10
   - Test after each batch
   - Commit: "refactor: reorganize documentation into CTB structure"

4. **Phase 3** (2-3 hours):
   - Move scripts and tools
   - Update workflow files
   - Test script execution
   - Commit: "refactor: move scripts and tools to CTB structure"

5. **Phase 4** (4-6 hours):
   - Move source code
   - Update imports (may require find-replace across codebase)
   - Run tests after each file moved
   - Commit: "refactor: migrate source code to CTB structure"

6. **Phase 5** (2-4 hours):
   - Run CTB verification
   - Fix any remaining issues
   - Deploy to staging
   - Commit: "chore: finalize CTB migration and verify compliance"

### 7.3 Critical Success Factors

1. **Team Communication**
   - Notify team before starting
   - Block other merges during migration
   - Pair program on high-risk changes

2. **Automated Testing**
   - Ensure test suite is comprehensive
   - Run tests after each phase
   - Monitor CI/CD pipelines

3. **Incremental Commits**
   - Commit after each successful phase
   - Write descriptive commit messages
   - Push to remote frequently

4. **Validation**
   - Use `global-config/scripts/ctb_verify.sh` after each phase
   - Verify application functionality manually
   - Check all integrations (MCP, database, APIs)

---

## 8. Quick Reference Checklist

### Pre-Migration Checklist
- [ ] Read this entire report
- [ ] Get team approval
- [ ] Schedule migration window
- [ ] Create backup tag: `git tag pre-ctb-migration-$(date +%Y%m%d)`
- [ ] Create backup branch: `git checkout -b backup/pre-ctb-migration`
- [ ] Export current file list: `find . -type f > pre-migration-files.txt`
- [ ] Run and document current test results
- [ ] Block other PRs/merges

### Migration Execution Checklist

**Phase 1: Foundation**
- [ ] Create missing sys/* directories (deepwiki, bigquery-warehouse, builder-bridge)
- [ ] Create ctb/ops directory and subdirectories
- [ ] Create .barton directory at root
- [ ] Create config directory at root
- [ ] Create documentation directories (architecture, integration, guides, etc.)
- [ ] Add LLM_ONBOARDING.md
- [ ] Add .barton/repo_config.yaml
- [ ] Add .barton/doctrine_id.txt
- [ ] Add .barton/hive_assignment.txt
- [ ] Add config/mcp_registry.json
- [ ] Add config/deployment_config.yaml
- [ ] Add config/feature_flags.json
- [ ] Add ctb/meta/config/ctb_config.json
- [ ] Add all branch README files (7 files)
- [ ] Add sys subdirectory README files (deepwiki, bigquery, builder-bridge)
- [ ] Commit: "feat: add CTB directory structure and configs"

**Phase 2: Documentation**
- [ ] Move ARCHITECTURE_SUMMARY.md → ctb/docs/architecture/
- [ ] Move EVENT_DRIVEN_SYSTEM_README.md → ctb/docs/architecture/
- [ ] Move all CTB audit reports → ctb/docs/audit/
- [ ] Move all CTB enforcement docs → ctb/meta/
- [ ] Move all integration docs → ctb/docs/integration/
- [ ] Move all guide docs → ctb/docs/guides/
- [ ] Move all changelog docs → ctb/docs/changelog/
- [ ] Move all session summaries → ctb/docs/sessions/
- [ ] Move Grafana docs → ctb/sys/grafana/docs/
- [ ] Move N8N docs → ctb/sys/n8n/docs/
- [ ] Move Neon docs → ctb/sys/neon-vault/docs/
- [ ] Move schema docs → ctb/data/schemas/
- [ ] Move general docs (CONTRIBUTING, DEPENDENCIES, etc.)
- [ ] Update README.md with CTB structure
- [ ] Update CLAUDE.md with CTB paths
- [ ] Update ARCHITECTURE_SUMMARY.md paths
- [ ] Find and update all documentation links
- [ ] Commit: "refactor: reorganize documentation into CTB structure"

**Phase 3: Scripts & Tools**
- [ ] Move migration scripts → ctb/data/migrations/
- [ ] Move system tools → ctb/sys/tools/
- [ ] Move AI scripts → ctb/ai/scripts/
- [ ] Update .github/workflows/ script paths
- [ ] Test script execution paths
- [ ] Commit: "refactor: move scripts and tools to CTB structure"

**Phase 4: Source Code** (HIGHEST RISK)
- [ ] Move src/main.py → ctb/ai/main.py (or ctb/sys/api/)
- [ ] Update all Python imports
- [ ] Update all JavaScript imports (if applicable)
- [ ] Run Python test suite
- [ ] Run JavaScript test suite
- [ ] Fix any import errors
- [ ] Commit: "refactor: migrate source code to CTB structure"

**Phase 5: Directories**
- [ ] Compare and merge docs/ with ctb/docs/
- [ ] Compare and merge ui/ with ctb/ui/
- [ ] Compare and merge grafana/ with ctb/sys/grafana/
- [ ] Move doctrine/ → ctb/meta/doctrine/
- [ ] Move HEIR-AGENT-SYSTEM/ → ctb/ai/agents/
- [ ] Move ids/ → ctb/meta/ids/
- [ ] Move infra/ → ctb/sys/infra/ (or merge with ctb/data/infra)
- [ ] Move libs/imo_tools/ → ctb/sys/libs/imo_tools/
- [ ] Move migrations/ → ctb/data/migrations/ (merge)
- [ ] Move ops/ → ctb/ops/automation-scripts/
- [ ] Move ui_specs/ → ctb/ui/specs/
- [ ] Move workflows/ → ctb/sys/n8n/workflows/
- [ ] Remove empty directories
- [ ] Commit: "refactor: consolidate directories into CTB structure"

**Phase 6: Configuration**
- [ ] Move global-config.yaml → ctb/meta/global-config/
- [ ] Move render.yaml → ctb/sys/deployment/
- [ ] Move vercel.json → ctb/sys/deployment/
- [ ] Update configuration loading paths in code
- [ ] Test configuration loading
- [ ] Commit: "refactor: organize configuration files"

**Phase 7: Verification**
- [ ] Run: `bash global-config/scripts/ctb_verify.sh`
- [ ] Fix any CTB compliance issues
- [ ] Run full Python test suite
- [ ] Run full JavaScript test suite
- [ ] Test application startup
- [ ] Test MCP integrations
- [ ] Test database connections
- [ ] Test API endpoints
- [ ] Deploy to staging environment
- [ ] Smoke test staging deployment
- [ ] Run CTB enforcement: `bash global-config/scripts/ctb_enforce.sh`
- [ ] Commit: "chore: finalize CTB migration and verify compliance"

### Post-Migration Checklist
- [ ] Merge feature branch to main
- [ ] Tag release: `git tag ctb-migration-complete-$(date +%Y%m%d)`
- [ ] Deploy to production
- [ ] Monitor error logs for 24 hours
- [ ] Update team documentation
- [ ] Archive backup branch (do not delete yet)
- [ ] Celebrate! 🎉

---

## 9. Automation Opportunities

Several steps in this migration can be automated:

### 9.1 Automated File Moving Script

```bash
#!/bin/bash
# auto_ctb_migrate.sh

# This script automates Phase 2 (Documentation moves)
# Run with: bash auto_ctb_migrate.sh --dry-run (to preview)
# Run with: bash auto_ctb_migrate.sh --execute (to execute)

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
  DRY_RUN=true
fi

move_file() {
  local src="$1"
  local dest="$2"

  if [ "$DRY_RUN" == true ]; then
    echo "[DRY-RUN] Would move: $src → $dest"
  else
    mkdir -p "$(dirname "$dest")"
    mv "$src" "$dest"
    echo "[MOVED] $src → $dest"
  fi
}

# Documentation moves
move_file "ARCHITECTURE_SUMMARY.md" "ctb/docs/architecture/ARCHITECTURE_SUMMARY.md"
move_file "EVENT_DRIVEN_SYSTEM_README.md" "ctb/docs/architecture/EVENT_DRIVEN_SYSTEM.md"
# ... (add all other moves)
```

### 9.2 Import Path Update Script

```python
# update_imports.py
# Automatically updates Python import paths

import re
import os
from pathlib import Path

OLD_PATTERNS = [
    (r'from libs\.imo_tools', 'from ctb.sys.libs.imo_tools'),
    (r'from src\.main', 'from ctb.ai.main'),
    # ... add more patterns
]

def update_file_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    modified = False
    for old, new in OLD_PATTERNS:
        if re.search(old, content):
            content = re.sub(old, new, content)
            modified = True

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated: {file_path}")

# Run on all .py files
for py_file in Path('.').rglob('*.py'):
    update_file_imports(py_file)
```

### 9.3 Link Update Script

```bash
#!/bin/bash
# update_docs_links.sh
# Updates all documentation links to use new CTB paths

find ctb/docs -name "*.md" -type f -exec sed -i 's|(ARCHITECTURE_SUMMARY.md)|(ctb/docs/architecture/ARCHITECTURE_SUMMARY.md)|g' {} +
find ctb/docs -name "*.md" -type f -exec sed -i 's|(EVENT_DRIVEN_SYSTEM_README.md)|(ctb/docs/architecture/EVENT_DRIVEN_SYSTEM.md)|g' {} +
# ... add more replacements
```

---

## 10. Summary & Next Steps

### 10.1 What We Found

✅ **Strengths**:
- CTB directory structure already exists with 5/6 main branches
- Most system infrastructure already in place (chartdb, composio-mcp, etc.)
- Good documentation foundation
- Global-config files are present and up-to-date

⚠️ **Gaps**:
- 3 sys/* subdirectories missing (deepwiki, bigquery-warehouse, builder-bridge)
- ops/ branch missing at CTB level
- 120+ files still at root level that should be in CTB structure
- Missing configuration files (.barton/, config/, ctb/meta/config/)
- Missing branch README files
- No LLM_ONBOARDING.md

### 10.2 Estimated Effort

**Total Time**: 12-18 hours (1.5-2 days)
- Phase 1 (Foundation): 1-2 hours
- Phase 2 (Documentation): 2-3 hours
- Phase 3 (Scripts): 2-3 hours
- Phase 4 (Source Code): 4-6 hours
- Phase 5 (Verification): 2-4 hours

**Risk Level**: MEDIUM
- High: Python import path changes
- Medium: CI/CD pipeline updates
- Low: Documentation moves

### 10.3 Recommended Next Steps

1. **Review & Approve** (30 min)
   - Review this report with team
   - Approve migration plan
   - Schedule migration window

2. **Prepare** (30 min)
   - Create backup tag and branch
   - Run current test suite
   - Export current file structure
   - Block other PRs

3. **Execute** (12-18 hours)
   - Follow phased approach
   - Commit after each phase
   - Test continuously
   - Monitor for errors

4. **Verify** (2-4 hours)
   - Run CTB verification
   - Deploy to staging
   - Smoke test
   - Get team sign-off

5. **Deploy** (1 hour)
   - Merge to main
   - Tag release
   - Deploy to production
   - Monitor

### 10.4 Decision Required

**USER MUST DECIDE:**

Before proceeding, please confirm:
- [ ] Approve this migration plan
- [ ] Schedule migration window (when should this happen?)
- [ ] Confirm team availability (who will help?)
- [ ] Approve estimated downtime (if any)
- [ ] Confirm rollback criteria
- [ ] Authorize proceeding with Phase 1 (low-risk foundation changes)

**Or request modifications:**
- Do you want a different phased approach?
- Should any files stay at root?
- Are there additional considerations?
- Should we automate more steps?

---

## Appendix A: File Inventory

### Root-Level Files (50+ files to evaluate)

Documentation files: 35+
- ARCHITECTURE_SUMMARY.md
- BUILDER_IO_INTEGRATION_COMPLETE.md
- BIG_UPDATE_SUMMARY.md
- COMPOSIO_AGENT_TEMPLATE.md
- CONTRIBUTING.md
- CTB_AUDIT_REPORT.md
- CTB_COMPLIANCE_REPORT_2025-10-24.md
- CTB_ENFORCEMENT.md
- CTB_INDEX.md
- CTB_REMEDIATION_SUMMARY.md
- CTB_TAGGING_REPORT.md
- CTB_VERIFICATION_CHECKLIST.md
- CURRENT_NEON_SCHEMA.md
- DEPENDENCIES.md
- ENTRYPOINT.md
- EVENT_DRIVEN_SYSTEM_README.md
- GLOBAL_CONFIG_CHANGES_LOG.txt
- GLOBAL_CONFIG_COMPLETE_SYNC.md
- GLOBAL_CONFIG_IMPLEMENTATION.md
- GLOBAL_CONFIG_SYNC_COMPLETE.md
- GRAFANA_CLOUD_SETUP_GUIDE.md
- GRAFANA_LOGIN_SOLUTION.txt
- GRAFANA_LOGIN_TROUBLESHOOTING.md
- GRAFANA_NO_AUTH_SETUP.txt
- GRAFANA_READY.txt
- GRAFANA_SETUP.md
- GRAFANA_SETUP_COMPLETE.md
- INTEGRATION_GUIDE.md
- N8N_HOSTED_SETUP_GUIDE.md
- N8N_MESSAGING_SETUP.md
- NEON_CONNECTION_GUIDE.md
- NEW_INTEGRATIONS_SUMMARY.md
- NO_DOCKER_ALTERNATIVES.md
- QUICKREF.md
- REPO_STRUCTURE.md
- SCHEMA_QUICK_REFERENCE.md
- SESSION_SUMMARY_2025-10-24.md
- SUPER_PROMPT_COMPLETION.md

Python scripts: 10
- add_email_verification_tracking.py
- assign_messages_to_contacts.py
- check_companies.py
- check_db_schema.py
- check_message_status.py
- check_pipeline_events.py
- create_db_views.py
- setup_messaging_system.py
- trigger_enrichment.py
- start_server.py

Configuration: 5+
- global-config.yaml
- render.yaml
- vercel.json
- docker-compose.yml
- .env.example

### Root-Level Directories (20 directories)

Currently at root:
1. apps/ - Application workspaces
2. archive/ - Historical files
3. ctb/ - CTB structure (correct location)
4. dist/ - Build artifacts
5. docs/ - Documentation (DUPLICATE)
6. doctrine/ - Doctrine files
7. global-config/ - Global config
8. grafana/ - Grafana configs
9. HEIR-AGENT-SYSTEM/ - HEIR agent system
10. ids/ - ID files
11. infra/ - Infrastructure configs
12. libs/ - Shared libraries
13. logs/ - Log files
14. migrations/ - Database migrations
15. node_modules/ - Node dependencies
16. ops/ - Operations scripts
17. src/ - Source code
18. ui/ - UI files (DUPLICATE)
19. ui_specs/ - UI specifications
20. workflows/ - N8N workflows

---

## Appendix B: CTB Compliance Score

### Current Compliance: ~65%

**Breakdown:**
- CTB Structure Exists: ✅ (20 points)
- 5/6 Main Branches Present: ⚠️ (15/18 points)
- Required sys/* Subdirectories: ⚠️ (9/12 points, 3 missing)
- Configuration Files: ⚠️ (3/10 points, 7 missing)
- File Organization: ⚠️ (20/40 points, ~120 files misplaced)

**After Full Implementation: 100%**

All CTB Doctrine requirements will be met.

---

## Appendix C: Questions for User

Before proceeding, please answer:

1. **apps/** directory - This contains UI workspaces. Should this:
   - [ ] Stay at root level (for easy access during development)
   - [ ] Move to ctb/ui/apps/
   - [ ] Other: ___________

2. **src/main.py** - This appears to be the main entry point. Should it go to:
   - [ ] ctb/ai/main.py (if it's AI/agent-focused)
   - [ ] ctb/sys/api/main.py (if it's primarily an API server)
   - [ ] Stay at root as src/main.py
   - [ ] Other: ___________

3. **Deployment configs** (render.yaml, vercel.json) - Should they:
   - [ ] Stay at root (for easy deployment tool detection)
   - [ ] Move to ctb/sys/deployment/ (with symlinks from root)
   - [ ] Move to ctb/sys/deployment/ (update deployment tools)
   - [ ] Other: ___________

4. **Documentation consolidation** - Root docs/ vs ctb/docs/:
   - [ ] Merge everything into ctb/docs/, delete root docs/
   - [ ] Keep both separate for different purposes
   - [ ] Other: ___________

5. **Timeline** - When should this migration happen?
   - [ ] Immediately (I approve, let's start)
   - [ ] Within 1 week (schedule a specific date)
   - [ ] Within 1 month
   - [ ] After [specific milestone]
   - [ ] Other: ___________

---

## Appendix D: Automated Migration Script

If approved, this script can automate 80% of the migration:

```bash
#!/bin/bash
# CTB_FULL_MIGRATION.sh
# Automated CTB migration for barton-outreach-core

set -e  # Exit on error

# Configuration
DRY_RUN=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: bash CTB_FULL_MIGRATION.sh [--dry-run] [--verbose]"
      exit 0
      ;;
  esac
done

# Helper functions
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

move_file() {
  local src="$1"
  local dest="$2"

  if [ "$DRY_RUN" == true ]; then
    echo "[DRY-RUN] Would move: $src → $dest"
  else
    mkdir -p "$(dirname "$dest")"
    mv "$src" "$dest"
    log "Moved: $src → $dest"
  fi
}

# Phase 1: Create directory structure
log "Phase 1: Creating directory structure..."
# (commands from section 4.A)

# Phase 2: Add configuration files
log "Phase 2: Adding configuration files..."
# (commands from section 4.B)

# Phase 3: Move documentation files
log "Phase 3: Moving documentation files..."
# (commands from section 4.C - documentation)

# Phase 4: Move scripts
log "Phase 4: Moving scripts..."
# (commands from section 4.C - scripts)

# Phase 5: Move source code
log "Phase 5: Moving source code..."
# (commands from section 4.C - source)

# Phase 6: Update imports
log "Phase 6: Updating imports..."
# python update_imports.py

# Phase 7: Verification
log "Phase 7: Running verification..."
bash global-config/scripts/ctb_verify.sh

log "Migration complete!"
```

---

**END OF REPORT**

This is a PREVIEW ONLY. No changes have been made to the repository.

Please review, ask questions, and approve before proceeding with implementation.
