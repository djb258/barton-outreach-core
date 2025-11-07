# CTB (Centralized Template Base) - Barton Outreach Core

**CTB Version**: 1.3.3
**Repository**: barton-outreach-core
**Compliance Level**: Implementing...

## Overview

This repository follows the **CTB (Centralized Template Base) Doctrine v1.3.3**, Barton Enterprises' organizational framework for managing code repositories through a hierarchical branch structure based on altitude-based development philosophy.

The CTB structure organizes all code, configuration, documentation, and infrastructure into seven main branches, each serving a specific purpose at different "altitudes" of abstraction.

## The Seven Branches

### 🛠️ sys/ - System Infrastructure (40k ft)

**Purpose**: Core system infrastructure including APIs, databases, integrations, and deployment tools.

**Altitude**: 40,000 ft (Doctrine Core)

**Key Subdirectories**:
- `api/` - Backend API services
- `composio-mcp/` - MCP integrations (100+ tools)
- `neon-vault/` - PostgreSQL database management
- `firebase-workbench/` - Firestore configuration
- `github-factory/` - CI/CD automation and compliance
- `deepwiki/` - AI-powered documentation generator
- `bigquery-warehouse/` - Analytics data warehouse
- `builder-bridge/` - Design-to-code integration
- `chartdb/` - Database schema visualization
- `activepieces/` - Workflow automation
- `windmill/` - Workflow engine
- `claude-skills/` - Claude AI integrations
- `security-audit/` - Security compliance tools

[Read more](sys/README.md)

---

### 🤖 ai/ - AI & Agent Layer (20k ft)

**Purpose**: AI model configuration, prompts, agents, and machine learning workflows.

**Altitude**: 20,000 ft (Business Logic)

**Key Subdirectories**:
- `agents/` - AI agent configurations
- `prompts/` - Prompt templates
- `models/` - Model configurations
- `scripts/` - AI automation scripts
- `garage-bay/` - AI processing queue

**Providers Configured**:
- Anthropic (Claude) - Default
- OpenAI (GPT-4)
- Google (Gemini)

[Read more](ai/README.md)

---

### 💾 data/ - Data Layer (20k ft)

**Purpose**: Database schemas, migrations, data infrastructure, and master data management.

**Altitude**: 20,000 ft (Business Logic)

**Key Subdirectories**:
- `infra/` - Base schema definitions
- `migrations/` - Schema changes and updates
- `schemas/` - JSON schema definitions

**Database Schemas**:
- `company.*` - Company master data
- `people.*` - People master data
- `marketing.*` - Marketing campaigns & outreach
- `bit.*` - Business Intelligence Tables
- `ple.*` - People Lead Enrichment

[Read more](data/README.md)

---

### 📚 docs/ - Documentation (10k ft)

**Purpose**: Comprehensive project documentation, guides, architecture, and knowledge base.

**Altitude**: 10,000 ft (UI/UX Layer)

**Key Subdirectories**:
- `architecture/` - Architecture diagrams and decisions
- `guides/` - How-to guides and tutorials
- `api/` - API documentation
- `audit/` - Compliance and audit reports
- `changelog/` - Version history
- `integration/` - Integration guides
- `wiki/` - General documentation

[Read more](docs/README.md)

---

### 🎨 ui/ - User Interface (10k ft)

**Purpose**: User interface components, pages, and visual systems.

**Altitude**: 10,000 ft (UI/UX Layer)

**Key Subdirectories**:
- `apps/` - Full applications
- `components/` - Reusable UI components
- `pages/` - Page templates
- `templates/` - UI templates
- `lovable/` - Lovable.dev integration
- `packages/` - UI packages

**Technologies**:
- React / Next.js
- Tailwind CSS
- Builder.io integration
- Figma design sync

[Read more](ui/README.md)

---

### ⚙️ meta/ - Meta Configuration (40k ft)

**Purpose**: CTB metadata, global configuration, doctrine enforcement, and registry.

**Altitude**: 40,000 ft (Doctrine Core)

**Key Subdirectories**:
- `config/` - Configuration files
- `global-config/` - Global CTB doctrine files
- `.devcontainer/` - Development container configuration
- `.gitingest/` - Git ingestion configuration

**Configuration Files**:
- `ctb_config.json` - CTB branch configuration
- `mcp_registry.json` - MCP tool registry
- `CTB_DOCTRINE.md` - CTB framework documentation

[Read more](meta/README.md)

---

### 🚀 ops/ - Operations (5k ft)

**Purpose**: Operational tooling, automation scripts, CI/CD, deployment, and monitoring.

**Altitude**: 5,000 ft (Operations Layer)

**Key Subdirectories**:
- `docker/` - Docker configurations
- `scripts/` - Automation scripts
- `ci-cd/` - CI/CD pipeline configurations

**Common Operations**:
- Deployment automation
- Database backups
- Health monitoring
- Log management
- Maintenance scripts

[Read more](ops/README.md)

---

## CTB Architecture

### Altitude Philosophy

The CTB structure follows an altitude-based hierarchy:

```
        5k ft (ops)      - Daily Operations
       10k ft (ui/docs)  - User Interface & Documentation
       20k ft (ai/data)  - Business Logic & Data
       40k ft (sys/meta) - System Infrastructure & Doctrine
```

**Merge Flow**: Changes flow upward like sap in a tree
```
Operations (5k) → UI (10k) → Business (20k) → Systems (40k) → Main
```

### The Christmas Tree Analogy

```
                    ⭐ (Operations - 5k)
                   /|\
                  / | \
                 /  |  \   (UI Layer - 10k)
                /   |   \
               /    |    \
              /     |     \  (Business Logic - 20k)
             /      |      \
            /       |       \
           /________|________\  (System Infrastructure - 40k)
                   |||
                   |||  (Main Trunk - Doctrine Core)
                   |||
```

## Quick Navigation

### For Developers

- **API Development**: Start in [ctb/sys/api/](sys/api/)
- **AI/Agent Work**: Start in [ctb/ai/](ai/)
- **UI Development**: Start in [ctb/ui/](ui/)
- **Database Changes**: Start in [ctb/data/migrations/](data/migrations/)

### For Operations

- **Deployment**: See [ctb/ops/scripts/](ops/scripts/)
- **Monitoring**: See [ctb/sys/grafana/](sys/grafana/)
- **CI/CD**: See [ctb/ops/ci-cd/](ops/ci-cd/)

### For Documentation

- **Architecture**: See [ctb/docs/architecture/](docs/architecture/)
- **Guides**: See [ctb/docs/guides/](docs/guides/)
- **API Docs**: See [ctb/docs/api/](docs/api/)

## Common Commands

### Development

```bash
# Start API server
cd ctb/sys/api && npm install && node server.js

# Run AI enrichment
cd ctb/ai && python scripts/trigger_enrichment.py

# Start UI development server
cd ctb/ui/apps && npm run dev
```

### Operations

```bash
# Deploy to staging
bash ctb/ops/scripts/deploy-staging.sh

# Run database migration
psql $DATABASE_URL -f ctb/data/migrations/latest.sql

# Generate compliance audit
python ctb/sys/github-factory/scripts/ctb_audit_generator.py
```

### Verification

```bash
# Verify CTB compliance
bash global-config/scripts/ctb_verify.sh

# Run security scan
bash global-config/scripts/security_lockdown.sh

# Check branch structure
bash global-config/scripts/ctb_enforce.sh
```

## CTB Compliance

This repository strives for 100% CTB compliance. Current compliance status is tracked via:

- **Verification Script**: `global-config/scripts/ctb_verify.sh`
- **Enforcement Script**: `global-config/scripts/ctb_enforce.sh`
- **Audit Reports**: `ctb/docs/audit/`

### Compliance Requirements

- ✅ All 7 CTB branches present
- ✅ Required subdirectories created
- ✅ Configuration files in place
- ✅ Documentation up to date
- ⚠️ Files organized in correct branches (in progress)

## File Organization Rules

Files should be placed according to their purpose:

| File Type | Location | Example |
|-----------|----------|---------|
| API endpoints | `ctb/sys/api/` | `server.js`, `routes/` |
| AI agents | `ctb/ai/agents/` | `enrichment_agent.py` |
| Database schemas | `ctb/data/infra/` | `neon.sql` |
| Migrations | `ctb/data/migrations/` | `2025-11-07_add_column.sql` |
| Documentation | `ctb/docs/` | `ARCHITECTURE.md` |
| UI components | `ctb/ui/components/` | `Button.tsx` |
| Build configs | `ctb/meta/config/` | `ctb_config.json` |
| Deploy scripts | `ctb/ops/scripts/` | `deploy.sh` |

## Integration with Global Config

This repository inherits configuration from the global CTB doctrine:

- **Source**: `global-config/CTB_DOCTRINE.md`
- **Branch Map**: `global-config/ctb.branchmap.yaml`
- **Organization Standard**: `global-config/repo_organization_standard.yaml`

Updates from `imo-creator` are synced periodically.

## Best Practices

1. **Keep branches focused** - Each branch has a specific purpose
2. **Use correct altitude** - Place files at the right level
3. **Document as you go** - Update READMEs when adding features
4. **Follow naming conventions** - Use kebab-case for directories
5. **Run verification** - Check compliance before committing
6. **Security first** - Never commit secrets, use MCP vault

## Getting Help

- **CTB Doctrine**: See [global-config/CTB_DOCTRINE.md](../global-config/CTB_DOCTRINE.md)
- **Quick Reference**: See [QUICKREF.md](../QUICKREF.md)
- **Claude Onboarding**: See [CLAUDE.md](../CLAUDE.md)
- **Architecture**: See [ctb/docs/architecture/](docs/architecture/)

## Version History

- **v1.3.3** (2025-11-07) - Full CTB restructure implementation
- **v1.3.2** (2025-10-24) - Added compliance reporting
- **v1.3.0** (2025-10-18) - Initial CTB adoption

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Enterprises DevOps Team

For questions or issues, run `bash global-config/scripts/ctb_verify.sh` for diagnostic information.
