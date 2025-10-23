# AI & Agents (ai/)

**Barton ID Range**: 03.01.*
**Enforcement**: HEIR (Hierarchical Execution Intelligence & Repair)

## Purpose
AI agents, orchestration tools, automation scripts, and testing frameworks for intelligent system operation.

## Key Directories

### `garage-bay/` - MCP Orchestration System
- **Entry Point**: `services/mcp/main.py` - MCP server
- **Purpose**: Multi-domain orchestration (backend, frontend, database)
- **Drivers**: Backend (Render, Fly.io), DB (Neon, Firebase), Frontend (Vercel, Netlify)
- **Modules**:
  - `modules/domains/` - Domain-specific orchestration
  - `modules/intake/` - Data ingestion & mapping
  - `modules/core/` - Git, FS, HEIR operations
- **Run**: `cd garage-bay && python services/mcp/main.py`

### `agents/specialists/` - Specialized Runners
- `apifyRunner.js` - Apify actor execution
- `millionVerifyRunner.js` - Email verification
- `outreachRunner.js` - Outreach campaign automation

### `scripts/` - Automation & Deployment
- Database migrations runners
- Vercel/Render deployment scripts
- Schema validation & sync tools
- Composio integration helpers

### `testing/` - Integration Tests
- MCP integration tests
- Composio endpoint verification
- People/company schema validation

### `tools/` - Utility Scripts
- `repo_mcp_orchestrator.py` - Repository-level orchestration

## Common Tasks

### Run Garage Bay MCP Server
```bash
cd ctb/ai/garage-bay
pip install -r requirements.txt
python services/mcp/main.py
```

### Run Apify Actor
```bash
cd ctb/ai/agents/specialists
node apifyRunner.js --actor leads-finder --input companies.json
```

### Deploy to Vercel
```bash
cd ctb/ai/scripts
node vercel-mcp-deploy.js --app amplify-client
```

### Run Tests
```bash
cd ctb/ai/testing
node test-all-mcp-integrations.js
```

## Environment Variables
```bash
COMPOSIO_API_KEY=<your-key>
APIFY_API_KEY=<your-key>
DATABASE_URL=<neon-connection-string>
```

## Dependencies
- **Upstream**: `ctb/sys/api/` for API endpoints
- **Upstream**: `ctb/data/` for database schemas
- **Downstream**: None (top of execution hierarchy)

## Key Patterns

### HEIR Enforcement
Files in ai/ enforce system correctness through:
- Validators (schema compliance)
- Tests (integration checks)
- Agents (autonomous repair)
- Orchestrators (multi-service coordination)

### MCP Protocol
Garage Bay implements Model Context Protocol for:
- Tool registration
- Function calling
- Resource management
- Prompt handling

## Owners
- AI Agents: AI/ML team
- Garage Bay: Platform team
- Testing: QA team
