<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/activepieces
Barton ID: 04.04.08
Unique ID: CTB-B22FF26D
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Activepieces Integration

**Doctrine ID**: 04.04.08
**CTB Branch**: `sys/activepieces`
**Altitude**: 40k (Doctrine Core - System Infrastructure)

---

## Purpose

Activepieces provides no-code workflow automation for the CTB ecosystem. It enables:

- Visual workflow creation without coding
- 100+ pre-built integrations (Google, Slack, GitHub, etc.)
- Event-driven automation triggers
- Scheduled task execution
- Webhook-based integrations
- Flow orchestration across services

---

## Integration Flow

```
┌─────────────────────────────────────────┐
│   Trigger Event                         │
│   (Webhook, Schedule, Manual, etc.)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Activepieces Flow Engine              │
│   - Visual workflow execution            │
│   - Data transformation                  │
│   - Conditional logic                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Composio MCP Integration              │
│   Endpoint: http://localhost:3001/tool  │
│   Doctrine ID: 04.04.08                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   External Services                     │
│   (APIs, Databases, Tools, etc.)        │
└─────────────────────────────────────────┘
```

---

## Example Usage

### Create and Execute Flow

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "Activepieces",
    "action": "CREATE_FLOW",
    "data": {
      "name": "Data Sync Workflow",
      "trigger": "webhook",
      "steps": [
        {"action": "fetch_data", "source": "neon"},
        {"action": "transform", "method": "normalize"},
        {"action": "send_data", "destination": "firebase"}
      ]
    },
    "unique_id": "HEIR-2025-10-ACTIVEPIECES-001",
    "process_id": "PRC-FLOW-001",
    "orbt_layer": 1,
    "blueprint_version": "1.0"
  }'
```

### Schedule Recurring Task

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "Activepieces",
    "action": "SCHEDULE_FLOW",
    "data": {
      "flow_id": "flow_abc123",
      "schedule": "0 */6 * * *",
      "timezone": "UTC"
    },
    "unique_id": "HEIR-2025-10-ACTIVEPIECES-002",
    "process_id": "PRC-SCHEDULE-001",
    "orbt_layer": 1
  }'
```

---

## Toolkit Tools

- `CREATE_FLOW` - Design and create new automation workflows
- `EXECUTE_FLOW` - Manually trigger flow execution
- `LIST_FLOWS` - View all configured workflows
- `UPDATE_FLOW` - Modify existing workflow configuration
- `DELETE_FLOW` - Remove workflows
- `GET_FLOW_RUNS` - View execution history and logs
- `TRIGGER_WEBHOOK` - Activate webhook-triggered flows
- `SCHEDULE_FLOW` - Set up recurring automated tasks

---

## Local Development

Activepieces runs on port 80 (or 4200 for frontend):

```bash
# Start Activepieces locally
cd activepieces/
npm install
npm start

# Access UI at http://localhost:4200
# API at http://localhost:80
```

---

## Common Use Cases

1. **Data Synchronization**: Sync data between Neon, Firebase, and BigQuery
2. **Notification Workflows**: Send alerts via Slack, Email, SMS
3. **Content Publishing**: Auto-publish content to multiple platforms
4. **Data Processing**: ETL pipelines with transformation steps
5. **Integration Orchestration**: Connect 100+ services without code

---

## CTB Compliance

- **Doctrine ID**: 04.04.08 (mandatory for all CTB repos)
- **MCP Endpoint**: Registered in `config/mcp_registry.json`
- **Branch**: Must exist in all CTB-compliant repositories
- **Enforcement**: Validated by `global-config/scripts/ctb_enforce.sh`

---

## Documentation

- Full integration docs: `sys/activepieces/` directory in this branch
- CTB Doctrine: `global-config/CTB_DOCTRINE.md`
- MCP Registry: `config/mcp_registry.json`
- Activepieces Docs: https://www.activepieces.com/docs

---

**Status**: Active
**Version**: 1.0
**Last Updated**: 2025-10-18
