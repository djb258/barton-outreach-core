# AI Coding Agent Instructions

## Repository Structure

**CTB (Christmas Tree Backbone) Standard**: This repository follows the CTB organizational pattern with a strict hierarchical structure:

```
ctb/
├── ai/        # AI agents, MCP servers, automation (Python/Node.js)
├── data/      # Database schemas, migrations (Foundation layer)
├── docs/      # Documentation and analysis
├── meta/      # Root package.json, configs, monorepo orchestration
├── sys/       # Backend APIs, CI/CD, infrastructure (Node.js/FastAPI)
└── ui/        # Frontend React apps (Vite + TypeScript)
```

**Key Principles**:
- Files outside `ctb/` are doctrine-level documentation only (README.md, ARCHITECTURE_SUMMARY.md, etc.)
- All executable code lives inside `ctb/` branches
- Never create root-level code files - follow the CTB categorization
- Check `CTB_INDEX.md` for complete file inventory
- Consult `ENTRYPOINT.md` for navigation and quick start commands

## Database Architecture

**Primary Database**: Check `SCHEMA_QUICK_REFERENCE.md` or `CURRENT_NEON_SCHEMA.md` for schema details

**Common Patterns**:
- Always use `_unique_id` or `_id` suffixes for primary keys (never plain `id`)
- Always include `created_at`, `updated_at` timestamp columns
- Use RLS policies for sensitive schemas (intake.*, vault.*)
- Use `TEXT` type for all ID columns (not UUID or INTEGER)
- Enum checks via `CHECK (column IN ('val1', 'val2'))` not separate enum types

**Error Logging**: Log all errors to `public.shq_error_log` with:
- Severity levels: `critical`, `high`, `medium`, `low`
- Include `source_system`, `error_type`, `error_message`, optional `stack_trace`
- Set `resolved = FALSE` by default

**Data Flow Pattern**: Raw intake → validation → promotion → master tables → enrichment

## Event-Driven Systems

**Pattern**: Database triggers → event tables → webhook/automation → workflows

**Implementation**: Check if `EVENT_DRIVEN_SYSTEM_README.md` exists for:
- PostgreSQL trigger definitions
- Event queue tables
- Webhook registry
- n8n or other automation tool integration

**Monitoring**: Hybrid approach (API for real-time, database queries for historical)

## Development Workflows

### Starting Development
Check `package.json` in `ctb/meta/` or root for available scripts:
```bash
npm install          # Install dependencies
npm run bootstrap    # Build shared packages (if monorepo)
npm run dev          # Start development servers
```

### Database Operations
```bash
# Apply schemas (check for migration scripts in ctb/data/)
npm run db:migrate   # or psql $DATABASE_URL -f ctb/data/infra/*.sql

# Refresh schema map after DB changes
npm run schema:refresh
```

### Service-Specific Commands
```bash
# Frontend (check ctb/ui/apps/)
npm run dev:factory-imo
npm run dev:amplify-client

# Backend API (check ctb/sys/api/)
npm run dev:api

# Python services (check requirements.txt or ctb/ai/)
python main.py
uvicorn main:app --reload
```

## Project-Specific Conventions

### File Organization (CTB Enforcement)
- **Never** create root-level code files - all code goes in `ctb/`
- Python scripts: `ctb/ai/scripts/` or `ctb/sys/` depending on purpose
- Node.js services: `ctb/sys/api/` or `ctb/ai/agents/`
- React components: `ctb/ui/apps/{app-name}/src/components/`
- Check `CTB_INDEX.md` or `DEPENDENCIES.md` for structure guidance

### Naming Conventions
- Database tables: `snake_case` (e.g., `company_master`, `pipeline_events`)
- React components: `PascalCase` (e.g., `CompanyCard`, `DashboardLayout`)
- Files: `kebab-case.ts` or `snake_case.py`
- Database schemas: `lowercase` (e.g., `marketing`, `intake`, `vault`)

### API Response Format
```typescript
// Success
{ success: true, data: {...}, message?: string }

// Error
{ success: false, error: string, details?: {...} }
```

## Integration Points

### Common External Services
- **Neon/PostgreSQL**: Primary database (via `@neondatabase/serverless` or psycopg2)
- **Vercel**: Frontend deployment (check for `vercel.json`)
- **n8n/Automation**: Workflow automation (check for webhook registry)
- **Grafana**: Monitoring dashboards (check `grafana/` directory or `docker-compose.yml`)

### Check Repository for Specific Integrations
Look for configuration files or documentation mentioning:
- Apollo.io, Apify, or other data providers
- Email services (SendGrid, Instantly, HeyReach)
- Verification services (MillionVerifier, ZeroBounce)
- Payment processors (Stripe, etc.)

### Internal Communication Patterns
- Frontend → Backend: REST API calls (check `ctb/sys/api/`)
- Backend → Database: Direct SQL via pg or psycopg2
- Agents → Database: Direct writes to intake or master schemas
- Event-driven: Database triggers → webhooks → automation

## HEIR Agent System (If Applicable)

If the repository includes HEIR agents (check for `HEIR-AGENT-SYSTEM/` or `ctb/ai/agents/`):

**Organization**: 3-level hierarchy
- **Level 1 (Orchestrators)**: CEO Orchestrator, Project Planner - strategic coordination
- **Level 2 (Managers)**: Backend, Integration, Frontend, DevOps managers - tactical management
- **Level 3 (Specialists)**: Database, Scraping, Email, Auth, Payment, UI - technical execution

**Configuration**: Check for `heir.doctrine.yaml` or `agent-catalog.json`
**Agent Guide**: Look for `AGENT_GUIDE.md` or `agent-guide-for-gpt.md`

## Critical Files to Check First

- `README.md` - Project overview and setup instructions
- `ENTRYPOINT.md` - Quick start navigation guide
- `ARCHITECTURE_SUMMARY.md` - High-level system design
- `CTB_INDEX.md` - Complete file inventory and structure
- `DEPENDENCIES.md` - Dependency flow between ctb branches
- `SCHEMA_QUICK_REFERENCE.md` or `CURRENT_NEON_SCHEMA.md` - Database schema
- `package.json` (in ctb/meta/ or root) - Available npm scripts
- `requirements.txt` - Python dependencies

## Testing & Compliance

Check `package.json` for test and compliance commands:
```bash
npm run test              # Run tests
npm run compliance:check  # Run compliance audit
npm run lint              # Lint code
```

For Python projects, check for:
```bash
pytest                    # Run Python tests
python -m ruff check      # Lint Python code
```

## Common Pitfalls to Avoid

1. **Don't** create files outside `ctb/` unless it's doctrine-level documentation
2. **Don't** use generic `id` columns - always use descriptive `_unique_id` or `_id` suffixes
3. **Don't** bypass event systems - let triggers handle workflow progression (if applicable)
4. **Don't** hardcode URLs or credentials - use environment variables
5. **Don't** commit sensitive files - check `.gitignore` for patterns
6. **Don't** create new database schemas without documenting in schema reference files
7. **Always** read existing documentation (`ENTRYPOINT.md`, `README.md`) before making changes

## Repository-Specific Notes

_This section should be customized per repository. Check the README.md and other documentation for:_
- Specific business logic or domain concepts
- Custom workflows or deployment procedures  
- Unique architectural decisions
- Team conventions or style guides
- Known issues or technical debt
