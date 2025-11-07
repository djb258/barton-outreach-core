# 🚀 Repository Navigation Guide

**Quick Start**: Get from clone to running in 5 minutes.

## 📍 Starting Points

### I want to...

#### **Run the API Server**
```bash
cd ctb/sys/api
npm install
node server.js
# API running on http://localhost:3000
```

#### **Set Up the Database**
```bash
# 1. Get Neon connection string
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# 2. Apply base schema
psql $DATABASE_URL -f ctb/data/infra/neon.sql

# 3. Run migrations
cd ctb/ai/scripts
node run_migrations.js
```

#### **Run the Frontend**
```bash
cd ctb/ui/apps/amplify-client
npm install
npm run dev
# UI running on http://localhost:5173
```

#### **Deploy to Production**
```bash
# Vercel (Frontend)
cd ctb/ai/scripts
node vercel-mcp-deploy.js --app amplify-client

# Render (Backend)
cd ctb/sys/api
git push render main
```

#### **Run Compliance Audit**
```bash
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../
# Generates CTB_AUDIT_REPORT.md
```

## 🗺️ Repository Structure

```
barton-outreach-core/
├── ctb/                        # 🌲 Christmas Tree Backbone
│   ├── sys/                    # System infrastructure (APIs, CI/CD)
│   │   ├── api/                # ➤ Backend API server
│   │   ├── github-factory/     # ➤ CI/CD & automation scripts
│   │   ├── composio-mcp/       # Composio integrations
│   │   └── neon-vault/         # Database operations
│   │
│   ├── ai/                     # AI agents & automation
│   │   ├── garage-bay/         # ➤ MCP orchestration system
│   │   ├── agents/             # Specialized runners (Apify, etc.)
│   │   ├── scripts/            # Deployment & automation
│   │   └── testing/            # Integration tests
│   │
│   ├── data/                   # Database schemas & migrations
│   │   ├── infra/              # ➤ Base schemas (neon.sql)
│   │   └── migrations/         # Schema changes
│   │
│   ├── docs/                   # Documentation
│   │   ├── analysis/           # Technical analysis reports
│   │   └── examples/           # Code examples & guides
│   │
│   ├── ui/                     # Frontend applications
│   │   ├── apps/               # ➤ React applications
│   │   └── packages/           # Shared UI packages
│   │
│   └── meta/                   # Configuration & metadata
│       ├── ctb_registry.json   # File index
│       └── config/             # App configuration
│
├── ENTRYPOINT.md              # ➤ YOU ARE HERE
├── README.md                   # Project overview
├── CTB_INDEX.md               # File movement map
├── CTB_AUDIT_REPORT.md        # Compliance report
└── .gitignore                  # Git exclusions
```

## 🎯 Common Tasks

### Development

#### Add New API Endpoint
```bash
# 1. Create route file
cd ctb/sys/api/routes/neon
cp analytics.js my-new-endpoint.js

# 2. Edit route
# - Change endpoint path
# - Update SQL queries
# - Test locally

# 3. Register in index.js
# Add: router.use('/my-endpoint', require('./my-new-endpoint'));
```

#### Add Database Migration
```bash
# 1. Create migration file
cd ctb/data/migrations
cat > $(date +%Y-%m-%d)_my_change.sql << 'EOF'
-- CTB Metadata header here
BEGIN;
-- Your migration SQL
COMMIT;
EOF

# 2. Test in development
psql $DATABASE_URL -f $(date +%Y-%m-%d)_my_change.sql

# 3. Deploy to production
node ctb/ai/scripts/run_migrations.js
```

#### Add New Frontend Page
```bash
cd ctb/ui/apps/amplify-client/src/pages
cp Dashboard.tsx MyNewPage.tsx
# Edit component, add route in App.tsx
```

### Operations

#### Check System Health
```bash
# API health
curl http://localhost:3000/health

# Database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Frontend build
cd ctb/ui/apps/amplify-client && npm run build
```

#### View Logs
```bash
# API logs
cd ctb/sys/api && tail -f logs/app.log

# GitHub Actions
# Visit: https://github.com/djb258/barton-outreach-core/actions

# Vercel deployments
cd ctb/ai/scripts && node vercel-mcp-deploy.js --logs
```

#### Run Tests
```bash
# Integration tests
cd ctb/ai/testing
node test-all-mcp-integrations.js

# Schema validation
cd ctb/ai/scripts
node verify-schema.mjs
```

### Compliance

#### Tag New Files
```bash
cd ctb/sys/github-factory/scripts
python ctb_metadata_tagger.py ../../ai/my-new-module/
```

#### Generate Audit
```bash
python ctb_audit_generator.py ../../
# Creates CTB_AUDIT_REPORT.md with score
```

#### Fix Compliance Issues
```bash
python ctb_remediation.py ../../
# Auto-fixes metadata issues
```

## 📚 Documentation Map

### By Role

**Developer** (writing code):
1. `ENTRYPOINT.md` (this file)
2. `ctb/sys/README.md` - System architecture
3. `ctb/data/README.md` - Database schemas
4. `ctb/docs/DATABASE_SCHEMA.md` - Schema details

**DevOps** (deploying/monitoring):
1. `ctb/docs/COMPLETE_DEPLOYMENT.md`
2. `ctb/sys/github-factory/.github/workflows/`
3. `ctb/docs/TROUBLESHOOTING.md`

**Data Engineer** (schemas/migrations):
1. `ctb/data/README.md`
2. `ctb/docs/SCHEMA_DIAGRAM.md`
3. `ctb/data/migrations/`

**QA** (testing):
1. `ctb/ai/testing/`
2. `ctb/docs/TROUBLESHOOTING.md`
3. `CTB_AUDIT_REPORT.md`

### By Topic

**Architecture**:
- `ctb/docs/ARCHITECTURE.md` - System design
- `ctb/docs/PIPELINE_ARCHITECTURE.md` - Data pipeline
- `ctb/docs/OUTREACH_ALTITUDE_MAP.md` - Altitude organization

**Integrations**:
- `ctb/docs/COMPOSIO_INTEGRATION.md` - Composio setup
- `ctb/docs/NEON_INTEGRATION.md` - Database
- `ctb/docs/APOLLO_INGEST_INTEGRATION.md` - Apollo data

**Compliance**:
- `CTB_AUDIT_REPORT.md` - Current score
- `CTB_REMEDIATION_SUMMARY.md` - Fixes applied
- `ctb/docs/COMPLIANCE_STATUS.md` - Status overview

## 🔧 Troubleshooting

### Common Issues

**"Cannot find module"**
```bash
# Install dependencies
cd <directory-with-package.json>
npm install
```

**"Database connection failed"**
```bash
# Check DATABASE_URL
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:5432/db?sslmode=require

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**"Port already in use"**
```bash
# Kill process on port 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

**"Build failed"**
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Get Help

1. Check `ctb/docs/TROUBLESHOOTING.md`
2. Search issues: `grep -r "error message" ctb/docs/`
3. Check logs: `cd ctb/sys/api && tail -f logs/app.log`
4. Run diagnostics: `python ctb/sys/github-factory/scripts/ctb_audit_generator.py ctb/`

## 🏗️ Project Philosophy

### CTB (Christmas Tree Backbone)
- **Altitude-based organization**: High-level (40k) → Low-level (5k)
- **Branch structure**: sys, ai, data, docs, ui, meta
- **Metadata headers**: Every file tagged with Barton ID
- **Enforcement**: HEIR (agents/validators) vs ORBT (operations/migrations)

### Barton Doctrine
- **Zero-wandering queues**: Auto-populating work queues
- **30-day TTL**: Automatic data lifecycle
- **Deterministic IDs**: database.subhive.table.timestamp.random.sequence
- **MCP integration**: 100+ tools via Composio

### Development Workflow
1. Create branch from `main`
2. Make changes (follow CTB structure)
3. Tag new files: `python ctb_metadata_tagger.py`
4. Test locally
5. Create PR
6. CI runs audit (must score ≥90)
7. Merge to `main`
8. Auto-deploy

## 🚦 Quick Health Check

```bash
# Run this to verify everything works
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../

# Should output:
# CTB Compliance Score: 72/100 (FAIR)
# If score < 70, run: python ctb_remediation.py ../../
```

## 🛡️ CTB Enforcement System

**IMPORTANT**: After cloning, run the setup script to enable automatic CTB enforcement:

### One-Time Setup

```bash
# Linux/Mac
cd .githooks && ./setup-hooks.sh

# Windows
cd .githooks && setup-hooks.bat
```

**What this does**:
- Installs pre-commit hook that validates every commit
- Auto-tags new files with Barton IDs
- Blocks commits with compliance < 70/100
- Ensures zero exceptions to CTB structure

**Enforcement Layers**:
1. **Pre-commit Hook** - Validates locally before commit
2. **GitHub Actions** - Validates in CI on every PR
3. **Scheduled Audits** - Weekly compliance checks

For full details, see: [CTB_ENFORCEMENT.md](CTB_ENFORCEMENT.md)

## 📞 Support

- **Docs**: Browse `ctb/docs/`
- **Issues**: https://github.com/djb258/barton-outreach-core/issues
- **Questions**: Check branch READMEs (ctb/*/README.md)

---

**Last Updated**: 2025-10-23
**Compliance Score**: 72/100
**Status**: ✅ Production Ready
