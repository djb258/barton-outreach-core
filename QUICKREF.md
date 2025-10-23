# 🚀 Quick Reference

One-page cheat sheet for common operations.

## 🏃 Quick Start Commands

```bash
# FIRST: Install CTB enforcement hooks (one-time)
cd .githooks && ./setup-hooks.sh  # or .bat on Windows

# API Server
cd ctb/sys/api && node server.js

# Frontend
cd ctb/ui/apps/amplify-client && npm run dev

# Database setup
psql $DATABASE_URL -f ctb/data/infra/neon.sql

# Run migrations
node ctb/ai/scripts/run_migrations.js

# MCP Server
cd ctb/ai/garage-bay && python services/mcp/main.py
```

---

## 🔑 Environment Variables

```bash
# Required
DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require&channel_binding=require"

# Optional
COMPOSIO_API_KEY="your-key-here"
ANTHROPIC_API_KEY="your-key-here"
API_URL="http://localhost:3000"
NODE_ENV="development"
PORT="3000"
```

---

## 📁 Key Files by Task

### Want to...

**Add API endpoint**: `ctb/sys/api/routes/neon/*.js`

**Run migrations**: `ctb/data/migrations/YYYY-MM-DD_*.sql`

**Change database schema**: `ctb/data/infra/neon.sql` + create migration

**Deploy frontend**: `ctb/ai/scripts/vercel-mcp-deploy.js`

**Add React page**: `ctb/ui/apps/amplify-client/src/pages/*.tsx`

**Configure GitHub Actions**: `ctb/sys/github-factory/.github/workflows/*.yml`

**Add MCP integration**: `ctb/ai/garage-bay/services/mcp/main.py`

**Update documentation**: `ctb/docs/*.md`

---

## 🗄️ Key Database Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `intake.raw_loads` | Staging for raw data | `load_id`, `batch_id`, `raw_data`, `status` |
| `vault.contacts` | Validated contacts | `contact_id`, `email`, `name`, `score`, `status` |
| `company.master` | Company golden records | `id`, `domain`, `name`, `industry` |
| `people.master` | People golden records | `id`, `email`, `name`, `company_id` |
| `marketing.campaigns` | Campaign definitions | `campaign_id`, `name`, `type`, `status` |
| `marketing.outreach_history` | Contact history | `person_id`, `campaign_id`, `sent_at`, `status` |

---

## 🌐 Ports & URLs

| Service | Dev Port | Production URL |
|---------|----------|----------------|
| API | 3000 | https://barton-outreach-api.onrender.com |
| Frontend | 5173 | https://barton-amplify.vercel.app |
| Database | - | ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432 |
| MCP Server | 8000 | - |

---

## 🔍 Common SQL Queries

### Ingest data
```sql
SELECT * FROM intake.f_ingest_json(
  ARRAY['{"email":"john@example.com","name":"John Doe"}'::jsonb],
  'apollo',
  'batch-123'
);
```

### Promote contacts
```sql
SELECT * FROM vault.f_promote_contacts(NULL);  -- Promote all pending
```

### Get pending loads
```sql
SELECT load_id, batch_id, raw_data->>'email' as email
FROM intake.raw_loads
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 100;
```

### Find high-value leads
```sql
SELECT email, name, company, score
FROM vault.contacts
WHERE score >= 80 AND status = 'active'
ORDER BY score DESC;
```

### Campaign performance
```sql
SELECT
  name,
  sent_count,
  response_count,
  ROUND(100.0 * response_count / NULLIF(sent_count, 0), 2) as response_rate
FROM marketing.campaigns
WHERE status = 'active';
```

---

## 🔌 API Endpoints

```bash
# Health check
curl http://localhost:3000/health

# Ingest data
curl -X POST http://localhost:3000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"apollo","batch_id":"test","rows":[{"email":"test@example.com"}]}'

# Promote contacts
curl -X POST http://localhost:3000/api/promote

# Get contacts
curl http://localhost:3000/api/contacts?limit=10

# Get single contact
curl http://localhost:3000/api/contacts/123

# Update contact
curl -X PATCH http://localhost:3000/api/contacts/123 \
  -H "Content-Type: application/json" \
  -d '{"score":90,"tags":["hot-lead"]}'
```

---

## 🔄 Git Workflow

```bash
# Start work
git checkout -b feature/my-feature

# Check status
git status

# Stage changes
git add .

# Commit (include CTB tags if new files)
git commit -m "feat: Add new feature

- Added X component
- Updated Y service
- Fixed Z issue

Barton ID: XX.XX.XX"

# Push to remote
git push origin feature/my-feature

# After PR merged, update main
git checkout main && git pull
```

---

## 🛠️ Troubleshooting

### Database connection failed
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check environment variable
echo $DATABASE_URL
```

### Port already in use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

### Cannot find module
```bash
# Reinstall dependencies
cd <directory-with-package.json>
rm -rf node_modules package-lock.json
npm install
```

### Build failed
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Migration failed
```bash
# Check migration status
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 5"

# Rollback and retry
# (Manual rollback required - no automated rollback)
```

---

## 📋 CTB Barton IDs

| Branch | ID Range | Purpose |
|--------|----------|---------|
| `data/` | 05.01.* | Database schemas, migrations |
| `sys/` | 04.04.* | APIs, CI/CD, infrastructure |
| `ai/` | 03.01.* | Agents, MCP, automation |
| `ui/` | 07.01.* | Frontend applications |
| `docs/` | 06.01.* | Documentation |
| `meta/` | 08.01.* | Configuration, metadata |

---

## 🧪 Testing

```bash
# Integration tests
cd ctb/ai/testing
node test-all-mcp-integrations.js

# Schema validation
cd ctb/ai/scripts
node verify-schema.mjs

# CTB compliance audit
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../
```

---

## 🛡️ CTB Enforcement

```bash
# Install enforcement hooks (one-time after clone)
cd .githooks && ./setup-hooks.sh  # or .bat on Windows

# Check compliance manually
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../../../ctb/

# Fix compliance issues
python ctb_remediation.py ../../../../ctb/

# Tag new file manually
python ctb_metadata_tagger.py path/to/file.js

# Bypass pre-commit hook (NOT RECOMMENDED)
git commit --no-verify

# View enforcement status
git config core.hooksPath  # Should show .githooks
```

---

## 📊 Monitoring

```bash
# Check API health
curl http://localhost:3000/health

# View audit log
psql $DATABASE_URL -c "SELECT * FROM intake.audit_log ORDER BY timestamp DESC LIMIT 10"

# Dashboard metrics
curl http://localhost:3000/api/analytics/dashboard

# Check pending promotions
psql $DATABASE_URL -c "SELECT COUNT(*) FROM intake.raw_loads WHERE status = 'pending'"
```

---

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd ctb/ai/scripts
node vercel-mcp-deploy.js --app amplify-client
```

### Backend (Render)
```bash
# Auto-deploys on push to main
git push origin main
```

### Database Migrations
```bash
# Run before deploying API
node ctb/ai/scripts/run_migrations.js
```

---

## 📚 Documentation Map

| Task | Document |
|------|----------|
| Getting started | `ENTRYPOINT.md` |
| Find anything | `ENTRYPOINT.md` → role/topic sections |
| API reference | `ctb/sys/api/API.md` |
| Database schema | `ctb/data/SCHEMA.md` |
| Dependencies | `DEPENDENCIES.md` |
| System architecture | `ctb/sys/README.md` |
| Deployment | `ctb/docs/COMPLETE_DEPLOYMENT.md` |
| Troubleshooting | `ctb/docs/TROUBLESHOOTING.md` |

---

## ⚡ Performance Tips

### Database Queries
- Use indexes: `WHERE email = 'x'` (indexed) vs `WHERE email LIKE '%x%'` (slow)
- Limit results: Always add `LIMIT` to prevent full table scans
- Use time filters: `WHERE created_at > NOW() - INTERVAL '7 days'`

### API Optimization
- Use pagination: `?limit=100&offset=0`
- Cache responses: Check `Cache-Control` headers
- Batch operations: Use array parameters when available

### Frontend Performance
- Lazy load routes: Use React.lazy() for code splitting
- Memoize expensive computations: Use useMemo/useCallback
- Virtualize long lists: Use react-window for 100+ items

---

**Last Updated**: 2025-10-23
**Quick Reference Version**: 1.0
**For Comprehensive Docs**: See `ENTRYPOINT.md`
