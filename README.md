# Barton Outreach Core

## 🎯 Doctrinal Compliance: 90%+ → 100% in One Command

This repository implements the complete **Outreach Doctrine A→Z** standard with automated compliance verification.

**Current Status**: 90%+ compliant (documentation complete, database migration pending)

### Automated Compliance Completion

```bash
# Complete all remaining fixes via Composio MCP (100% compliance in ~30 seconds)
npm run compliance:complete

# Or dry-run first
npm run compliance:complete -- --dry-run
```

**What This Does**:
- ✅ Creates `shq_error_log` table via Composio database connector
- ✅ Refreshes schema map automatically
- ✅ Tests error sync script
- ✅ Generates compliance report

**See**: [NEXT_STEPS.md](./NEXT_STEPS.md) | [docs/audit_report.md](./docs/audit_report.md) | [docs/outreach-doctrine-a2z.md](./docs/outreach-doctrine-a2z.md)

---

## 🌲 CTB Structure - Centralized Template Base

This repository follows the **CTB (Centralized Template Base) Doctrine v1.3.3**, organizing all code into seven altitude-based branches:

### CTB Branches

- **[ctb/sys/](ctb/sys/README.md)** - System Infrastructure (40k ft)
  - APIs, databases, integrations, CI/CD, deployment tools
  - Includes: Composio MCP, Neon PostgreSQL, Firebase, GitHub Factory, DeepWiki, BigQuery, Builder Bridge

- **[ctb/ai/](ctb/ai/README.md)** - AI & Agent Layer (20k ft)
  - AI model configuration, prompts, agents, machine learning workflows
  - Providers: Anthropic (Claude), OpenAI, Google Gemini

- **[ctb/data/](ctb/data/README.md)** - Data Layer (20k ft)
  - Database schemas, migrations, master data management
  - Schemas: company, people, marketing, bit, ple

- **[ctb/docs/](ctb/docs/README.md)** - Documentation (10k ft)
  - Architecture, guides, API docs, audit reports, knowledge base

- **[ctb/ui/](ctb/ui/README.md)** - User Interface (10k ft)
  - React components, pages, templates, Lovable.dev integration

- **[ctb/meta/](ctb/meta/README.md)** - Meta Configuration (40k ft)
  - CTB metadata, global configuration, doctrine enforcement

- **[ctb/ops/](ctb/ops/README.md)** - Operations (5k ft)
  - Docker, automation scripts, CI/CD pipelines, deployment

See [ctb/README.md](ctb/README.md) for complete CTB documentation and navigation guide.

### File Location Guide

**Root Level (Deployment Critical)**
- `src/main.py`, `start_server.py` - Application entry points (required by Render)
- `render.yaml`, `vercel.json` - Deployment configs (required at root)
- `package.json`, `requirements.txt` - Dependency manifests
- `docker-compose.yml` - Container orchestration
- `apps/` - Active development workspace

**CTB Structure**
- `ctb/docs/architecture/` - Architecture summaries and system design
- `ctb/docs/audit/` - CTB compliance reports and verification checklists
- `ctb/docs/integration/` - Integration guides for Composio, Neon, Builder.io
- `ctb/docs/setup/` - Dependency management, contributing guides, entry points
- `ctb/docs/status/` - Completion markers and status files
- `ctb/docs/reference/` - Quick references, schemas, Grafana/N8N guides
- `ctb/sys/` - System integrations (Firebase, Neon, Composio, etc.)
- `ctb/sys/deployment/` - Deployment helper scripts (Grafana, Docker utilities)
- `ctb/ai/` - AI models and prompts
- `ctb/data/` - Database schemas and migrations
- `ctb/ui/` - User interface components
- `ctb/ops/` - Operations and deployment scripts
- `ctb/meta/` - Configuration and metadata

### CTB Quick Commands

```bash
# Verify CTB compliance
bash global-config/scripts/ctb_verify.sh

# Start API server
cd ctb/sys/api && npm install && node server.js

# Run database migration
psql $DATABASE_URL -f ctb/data/migrations/latest.sql

# Deploy to staging
bash ctb/ops/scripts/deploy-staging.sh
```

---

## Marketing > Outreach Doctrine (Barton)

Modular, altitude-based pages for Doctrine Tracker interactive drill-down:
- **30k**: docs/pages/30000-vision.md
- **20k**: docs/pages/20000-categories.md
- **10k**: docs/pages/10000-specialization.md
- **5k/1k**: docs/pages/05000-execution.md

### HEIR Agent System Integration

This project includes a complete HEIR (Hierarchical Execution Intelligence & Repair) agent system:
- Access the system at `/heir` route
- 12 specialized agents (orchestrators, managers, specialists)
- Real-time task management and system monitoring
- Integration with Apollo, Apify, MillionVerifier, Instantly, and HeyReach APIs

## Project info

**URL**: https://lovable.dev/projects/1c02fda0-b967-4efc-807c-309dfdd81983

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/1c02fda0-b967-4efc-807c-309dfdd81983) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Deployment Platform

✅ **Active**: **Vercel Serverless** (primary and only deployment platform)

❌ **Deprecated**: Render (legacy files archived in `archive/render-legacy/`)

### Deployment Architecture

All external service integrations flow through **Composio MCP** server (port 3001), which runs independently of the deployment platform. This enables:
- Serverless-first architecture (Vercel edge functions)
- 100+ service integrations via single MCP interface
- No direct API credentials in deployment environment
- Simplified deployment and scaling

See: [VERCEL_DEPLOYMENT_GUIDE.md](./VERCEL_DEPLOYMENT_GUIDE.md) for deployment instructions

See: [COMPOSIO_INTEGRATION.md](./COMPOSIO_INTEGRATION.md) for MCP integration details

**Note**: Legacy Render files have been archived as part of doctrinal compliance audit (October 2025). See [docs/audit_report.md](./docs/audit_report.md) for details.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/1c02fda0-b967-4efc-807c-309dfdd81983) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
