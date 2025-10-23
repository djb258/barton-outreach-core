# System Infrastructure (sys/)

**Barton ID Range**: 04.04.*
**Enforcement**: ORBT (Operation, Repair, Build, Training)

## Purpose
Core system infrastructure including APIs, CI/CD automation, database operations, and service integrations.

## Key Directories

### `api/` - Backend API Services
- **Entry Point**: `server.js` - Main Express server
- **Routes**: `routes/neon/` - Database API endpoints
- **Purpose**: RESTful API for outreach platform
- **Run**: `cd api && npm install && node server.js`

### `github-factory/` - CI/CD & Automation
- **Scripts**: `scripts/` - Metadata tagging, auditing, remediation
- **Workflows**: `.github/workflows/` - GitHub Actions CI/CD
- **Key Files**:
  - `ctb_metadata_tagger.py` - Tag files with CTB metadata
  - `ctb_audit_generator.py` - Generate compliance reports
  - `ctb_remediation.py` - Auto-fix compliance issues
- **Run**: `python scripts/ctb_audit_generator.py ../`

### `composio-mcp/` - Composio Integration
- **Purpose**: MCP server for Composio tool integrations
- **Status**: 100+ tools integrated (Apify, Vercel, etc.)

### `neon-vault/` - Database Operations
- **Purpose**: Neon PostgreSQL connection management
- **Schemas**: Company, People, Marketing, BIT, PLE

## Common Tasks

### Run API Server
```bash
cd ctb/sys/api
npm install
node server.js
```

### Generate Compliance Audit
```bash
cd ctb/sys/github-factory/scripts
python ctb_audit_generator.py ../../
```

### Tag New Files
```bash
cd ctb/sys/github-factory/scripts
python ctb_metadata_tagger.py ../../ai/
```

## Environment Variables
See `.env.example` files in each service directory.

## Dependencies
- **Upstream**: None (top-level infrastructure)
- **Downstream**: All other branches depend on sys/

## Owners
- System Infrastructure: DevOps team
- API Services: Backend team
- CI/CD: Platform team
