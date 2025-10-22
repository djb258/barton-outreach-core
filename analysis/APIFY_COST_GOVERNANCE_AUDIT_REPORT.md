# APIFY COST GOVERNANCE AUDIT REPORT
**Doctrine Segment**: 04.04.07
**Generated**: 2025-10-22
**Audit Scope**: Four-Layer Cost Protection System

---

## 🎯 Executive Summary

This audit verifies the complete Apify cost-governance stack including:
- **Layer 1**: Pre-flight Validation (validateApifyInput.js)
- **Layer 2**: MCP Policy Firewall (COMPOSIO_MCP_POLICY_APIFY_LIMITS.json)
- **Layer 3**: Neon Ledger (marketing.actor_usage_log)
- **Layer 4**: Daily Cost Guard (apify_cost_guard.json)
- **Layer 5**: Apify Console Limits (native platform)

---

## 📋 AUDIT CHECK 1: Component Presence Verification

### Required Files

| Component | Path | Status | Layer |
|-----------|------|--------|-------|
| MCP Policy File | `analysis/COMPOSIO_MCP_POLICY_APIFY_LIMITS.json` | ✅ PRESENT | Layer 2 |
| Neon Ledger Migration | `apps/outreach-process-manager/migrations/2025-10-24_create_actor_usage_log.sql` | ✅ PRESENT | Layer 3 |
| Daily Cost Guard Job | `apps/outreach-process-manager/jobs/apify_cost_guard.json` | ✅ PRESENT | Layer 4 |
| Pre-flight Validation | `apps/outreach-process-manager/utils/validateApifyInput.js` | ✅ PRESENT | Layer 1 |
| Governance Documentation | `analysis/APIFY_COST_GOVERNANCE.md` | ✅ PRESENT | Documentation |

**Result**: ✅ **ALL COMPONENTS PRESENT**

---

## 📊 AUDIT CHECK 2: Budget Overrun Simulation

### Simulation Parameters

**Budget Limit**: $25.00/day
**Test Total**: $27.00
**Overage**: $2.00 (8% over limit)

### Dummy Runs to Insert

| Run | Actor | Cost | Items | Run ID |
|-----|-------|------|-------|--------|
| 1 | code_crafter~leads-finder | $5.50 | 275 | audit_run_{timestamp}_1 |
| 2 | code_crafter~leads-finder | $6.25 | 312 | audit_run_{timestamp}_2 |
| 3 | apify~linkedin-profile-scraper | $4.75 | 150 | audit_run_{timestamp}_3 |
| 4 | code_crafter~leads-finder | $5.00 | 250 | audit_run_{timestamp}_4 |
| 5 | apify~linkedin-profile-scraper | $5.50 | 175 | audit_run_{timestamp}_5 |
| **TOTAL** | | **$27.00** | **1,162** | |

### SQL: Insert Dummy Runs

```sql
-- Run 1: $5.50
INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    dataset_id,
    tool_name,
    estimated_cost,
    total_items,
    run_started_at,
    run_completed_at,
    status,
    notes
) VALUES (
    'audit_run_' || EXTRACT(EPOCH FROM NOW())::bigint || '_1',
    'code_crafter~leads-finder',
    'dataset_audit_1',
    'apify_run_actor_sync_get_dataset_items',
    5.50,
    275,
    CURRENT_DATE + TIME '09:00:00',
    CURRENT_DATE + TIME '09:15:00',
    'success',
    'Audit simulation run 1 - Cost governance test'
);

-- Run 2: $6.25
INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    dataset_id,
    tool_name,
    estimated_cost,
    total_items,
    run_started_at,
    run_completed_at,
    status,
    notes
) VALUES (
    'audit_run_' || EXTRACT(EPOCH FROM NOW())::bigint || '_2',
    'code_crafter~leads-finder',
    'dataset_audit_2',
    'apify_run_actor_sync_get_dataset_items',
    6.25,
    312,
    CURRENT_DATE + TIME '09:30:00',
    CURRENT_DATE + TIME '09:45:00',
    'success',
    'Audit simulation run 2 - Cost governance test'
);

-- Run 3: $4.75
INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    dataset_id,
    tool_name,
    estimated_cost,
    total_items,
    run_started_at,
    run_completed_at,
    status,
    notes
) VALUES (
    'audit_run_' || EXTRACT(EPOCH FROM NOW())::bigint || '_3',
    'apify~linkedin-profile-scraper',
    'dataset_audit_3',
    'apify_run_actor_sync_get_dataset_items',
    4.75,
    150,
    CURRENT_DATE + TIME '10:00:00',
    CURRENT_DATE + TIME '10:15:00',
    'success',
    'Audit simulation run 3 - Cost governance test'
);

-- Run 4: $5.00
INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    dataset_id,
    tool_name,
    estimated_cost,
    total_items,
    run_started_at,
    run_completed_at,
    status,
    notes
) VALUES (
    'audit_run_' || EXTRACT(EPOCH FROM NOW())::bigint || '_4',
    'code_crafter~leads-finder',
    'dataset_audit_4',
    'apify_run_actor_sync_get_dataset_items',
    5.00,
    250,
    CURRENT_DATE + TIME '11:00:00',
    CURRENT_DATE + TIME '11:15:00',
    'success',
    'Audit simulation run 4 - Cost governance test'
);

-- Run 5: $5.50
INSERT INTO marketing.actor_usage_log (
    run_id,
    actor_id,
    dataset_id,
    tool_name,
    estimated_cost,
    total_items,
    run_started_at,
    run_completed_at,
    status,
    notes
) VALUES (
    'audit_run_' || EXTRACT(EPOCH FROM NOW())::bigint || '_5',
    'apify~linkedin-profile-scraper',
    'dataset_audit_5',
    'apify_run_actor_sync_get_dataset_items',
    5.50,
    175,
    CURRENT_DATE + TIME '12:00:00',
    CURRENT_DATE + TIME '12:15:00',
    'success',
    'Audit simulation run 5 - Cost governance test'
);
```

### MCP Execution Command

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "<INSERT_ALL_5_STATEMENTS_ABOVE>"
    },
    "unique_id": "HEIR-2025-10-AUDIT-SIM-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

**Expected Result**: 5 rows inserted, total cost = $27.00

---

## 📊 AUDIT CHECK 3: Cost Guard Trigger Verification

### Verification Query

This query replicates the logic from `apify_cost_guard.json` to verify the pause trigger.

```sql
-- Cost Guard Verification Query (from apify_cost_guard.json)
SELECT
    SUM(estimated_cost) AS total_cost,
    COUNT(*) as total_runs,
    CASE
        WHEN SUM(estimated_cost) > 25 THEN 'PAUSE_REQUIRED'
        ELSE 'WITHIN_BUDGET'
    END as action_required,
    ARRAY_AGG(
        json_build_object(
            'run_id', run_id,
            'actor_id', actor_id,
            'cost', estimated_cost,
            'items', total_items
        )
    ) as run_details
FROM marketing.actor_usage_log
WHERE date(run_started_at) = current_date
  AND notes LIKE '%Audit simulation%';
```

### MCP Execution Command

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "SELECT SUM(estimated_cost) AS total_cost, COUNT(*) as total_runs, CASE WHEN SUM(estimated_cost) > 25 THEN '\''PAUSE_REQUIRED'\'' ELSE '\''WITHIN_BUDGET'\'' END as action_required FROM marketing.actor_usage_log WHERE date(run_started_at) = current_date AND notes LIKE '\''%Audit simulation%'\'';"
    },
    "unique_id": "HEIR-2025-10-AUDIT-VERIFY-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

**Expected Result**:
```json
{
  "total_cost": 27.00,
  "total_runs": 5,
  "action_required": "PAUSE_REQUIRED"
}
```

**Trigger Condition**: `total_cost > 25` ✅ **TRUE** ($27.00 > $25.00)

**Expected Action**: Per `apify_cost_guard.json`, the `composio_pause_tool` should be called automatically with:
```json
{
  "tool_name": "apify_run_actor_sync_get_dataset_items"
}
```

---

## 📝 AUDIT CHECK 4: Audit Log Entry Verification

### Query: Find Pause Event

```sql
-- Verify audit log contains "paused_for_budget_exceed" entry
SELECT
    id,
    event_type,
    event_description,
    metadata,
    created_at
FROM marketing.validation_log
WHERE (
    event_description LIKE '%paused_for_budget_exceed%'
    OR event_description LIKE '%Apify tool paused%'
    OR event_description LIKE '%budget exceeded%'
    OR metadata::text LIKE '%budget_exceeded%'
)
ORDER BY created_at DESC
LIMIT 5;
```

### Alternative: Check company_audit_log

```sql
-- If using company_audit_log for cost governance events
SELECT
    id,
    event_type,
    event_subtype,
    event_data,
    created_at
FROM marketing.company_audit_log
WHERE event_type = 'cost_governance'
  AND event_data::text LIKE '%paused%'
ORDER BY created_at DESC
LIMIT 5;
```

### MCP Execution Command

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "SELECT id, event_type, event_description, metadata, created_at FROM marketing.validation_log WHERE (event_description LIKE '\''%paused_for_budget_exceed%'\'' OR event_description LIKE '\''%Apify tool paused%'\'' OR metadata::text LIKE '\''%budget_exceeded%'\'') ORDER BY created_at DESC LIMIT 5;"
    },
    "unique_id": "HEIR-2025-10-AUDIT-LOG-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

**Expected Result**: At least 1 entry with:
- `event_type`: "cost_governance" or "tool_paused"
- `event_description`: Contains "paused_for_budget_exceed"
- `metadata`: Includes `{"tool_name": "apify_run_actor_sync_get_dataset_items", "reason": "daily_budget_exceeded", "daily_cost": 27.00, "limit": 25.00}`

---

## 🔧 AUDIT CHECK 5: Rollback - Resume Tool

### MCP Command: Resume Tool

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "composio_resume_tool",
    "data": {
      "tool_name": "apify_run_actor_sync_get_dataset_items"
    },
    "unique_id": "HEIR-2025-10-AUDIT-RESUME-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

### Alternative: Check Tool Status First

```bash
# Get current tool status
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "composio_get_tool_status",
    "data": {
      "tool_name": "apify_run_actor_sync_get_dataset_items"
    },
    "unique_id": "HEIR-2025-10-AUDIT-STATUS-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

**Expected Before Resume**: `status: "paused"` or `status: "disabled"`
**Expected After Resume**: `status: "active"` or `status: "enabled"`

---

## ✅ AUDIT CHECK 6: Resume Event Verification

### Query: Find Resume Event

```sql
-- Verify audit log contains resume event
SELECT
    id,
    event_type,
    event_description,
    metadata,
    created_at
FROM marketing.validation_log
WHERE (
    event_description LIKE '%resumed%'
    OR event_description LIKE '%Apify tool activated%'
    OR event_description LIKE '%manually activated%'
    OR metadata::text LIKE '%status%resumed%'
    OR metadata::text LIKE '%status%active%'
)
ORDER BY created_at DESC
LIMIT 5;
```

### MCP Execution Command

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "SELECT id, event_type, event_description, metadata, created_at FROM marketing.validation_log WHERE (event_description LIKE '\''%resumed%'\'' OR event_description LIKE '\''%Apify tool activated%'\'' OR metadata::text LIKE '\''%status%resumed%'\'') ORDER BY created_at DESC LIMIT 5;"
    },
    "unique_id": "HEIR-2025-10-AUDIT-RESUME-VERIFY-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

**Expected Result**: Entry with:
- `event_type`: "cost_governance" or "tool_resumed"
- `event_description`: Contains "tool_resumed" or "manually_activated"
- `metadata`: Includes `{"tool_name": "apify_run_actor_sync_get_dataset_items", "resumed_by": "manual", "timestamp": "2025-10-22T..."}`

---

## 🧹 CLEANUP: Remove Audit Simulation Data

### Cleanup SQL

```sql
-- Step 1: Remove audit simulation runs from ledger
DELETE FROM marketing.actor_usage_log
WHERE notes LIKE '%Audit simulation%'
  AND run_id LIKE 'audit_run_%';

-- Step 2: Remove audit log entries for this test
DELETE FROM marketing.validation_log
WHERE event_description LIKE '%Cost governance test%'
   OR metadata::text LIKE '%audit_simulation%';

-- Step 3: Verify cleanup
SELECT
    COUNT(*) as remaining_audit_records
FROM marketing.actor_usage_log
WHERE notes LIKE '%Audit simulation%';

-- Expected: remaining_audit_records = 0
```

### MCP Execution Command

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "DELETE FROM marketing.actor_usage_log WHERE notes LIKE '\''%Audit simulation%'\'' AND run_id LIKE '\''audit_run_%'\''; DELETE FROM marketing.validation_log WHERE event_description LIKE '\''%Cost governance test%'\'' OR metadata::text LIKE '\''%audit_simulation%'\''; SELECT COUNT(*) as remaining_audit_records FROM marketing.actor_usage_log WHERE notes LIKE '\''%Audit simulation%'\'';"
    },
    "unique_id": "HEIR-2025-10-AUDIT-CLEANUP-01",
    "process_id": "PRC-COST-AUDIT-001",
    "orbt_layer": 3,
    "blueprint_version": "1.0"
  }'
```

---

## 📊 PASS/FAIL MATRIX

| Layer | Component | Status | Score | Notes |
|-------|-----------|--------|-------|-------|
| **Layer 1** | **Pre-flight Validation** | ⏳ MANUAL | TBD | validateApifyInput.js enforces limits |
| | File Exists | ✅ PASS | 100% | apps/outreach-process-manager/utils/validateApifyInput.js |
| | Max Domains: 50 | ⏳ PENDING | TBD | Test with 51 domains (should reject) |
| | Max Leads: 500 | ⏳ PENDING | TBD | Test with 501 leads (should cap to 500) |
| | Max Cost: $1.50 | ⏳ PENDING | TBD | Test with $1.51 input (should reject) |
| | Cost Calculation | ⏳ PENDING | TBD | Formula: (leads × $0.002) + $0.02 base |
| **Layer 2** | **MCP Policy Firewall** | ⏳ MANUAL | TBD | COMPOSIO_MCP_POLICY_APIFY_LIMITS.json |
| | File Exists | ✅ PASS | 100% | analysis/COMPOSIO_MCP_POLICY_APIFY_LIMITS.json |
| | Daily Run Limit: 20 | ⏳ PENDING | TBD | Test 21st run (should block) |
| | Concurrent Runs: 3 | ⏳ PENDING | TBD | Test 4th concurrent (should queue) |
| | Monthly Budget: $25 | ❌ EXCEEDED | 108% | Simulation: $27.00 (over by $2.00) |
| | Auto-Pause Action | ⏳ PENDING | TBD | Verify composio_pause_tool called |
| **Layer 3** | **Neon Ledger** | ⏳ MANUAL | TBD | marketing.actor_usage_log |
| | Migration File Exists | ✅ PASS | 100% | apps/outreach-process-manager/migrations/2025-10-24_create_actor_usage_log.sql |
| | Table Schema | ⏳ PENDING | TBD | Verify via information_schema.tables |
| | Insert Dummy Runs | ⏳ PENDING | TBD | 5 runs totaling $27.00 |
| | Cost Calculation | ⏳ PENDING | TBD | SUM(estimated_cost) = $27.00 |
| | Query Performance | ⏳ PENDING | TBD | Cost Guard query < 100ms |
| **Layer 4** | **Daily Cost Guard** | ⏳ MANUAL | TBD | apify_cost_guard.json |
| | Job File Exists | ✅ PASS | 100% | apps/outreach-process-manager/jobs/apify_cost_guard.json |
| | Schedule Valid | ⏳ PENDING | TBD | RRULE:FREQ=DAILY;BYHOUR=23;BYMINUTE=0 |
| | Threshold Check | ⏳ PENDING | TBD | Query returns total_cost > $25 |
| | Auto-Pause Trigger | ⏳ PENDING | TBD | composio_pause_tool called |
| | Audit Log Entry | ⏳ PENDING | TBD | "paused_for_budget_exceed" logged |
| **Layer 5** | **Apify Console Limits** | ⚠️ WARN | N/A | Native platform controls |
| | Account Limits | ⏳ MANUAL | TBD | Check Apify dashboard settings |
| | Billing Alerts | ⏳ MANUAL | TBD | Verify email notifications enabled |
| | Hard Stop | ⏳ MANUAL | TBD | Confirm auto-pause at account level |
| **Rollback** | **Manual Resume** | ⏳ MANUAL | TBD | composio_resume_tool command |
| | Resume Command | ⏳ PENDING | TBD | MCP tool call successful |
| | Tool Activation | ⏳ PENDING | TBD | Tool status = "active" |
| | Audit Log Entry | ⏳ PENDING | TBD | Resume event logged |

---

## 📋 Audit Checklist

Use this checklist to track manual audit progress:

- [ ] **Component Presence**: All 5 files present and accessible
- [ ] **Simulation Setup**: 5 dummy runs inserted via MCP ($27 total)
- [ ] **Cost Calculation**: Query returns SUM(estimated_cost) = $27.00
- [ ] **Threshold Breach**: action_required = "PAUSE_REQUIRED"
- [ ] **Auto-Pause**: Tool paused via composio_pause_tool
- [ ] **Audit Log**: "paused_for_budget_exceed" entry found
- [ ] **Manual Resume**: Tool resumed via composio_resume_tool
- [ ] **Resume Log**: Resume event logged in validation_log
- [ ] **Cleanup**: All audit simulation data removed (0 remaining)

---

## 🎯 Success Criteria

### ✅ PASS Criteria

1. All component files present
2. Simulation data inserted successfully ($27 total)
3. Cost Guard query detects budget breach (> $25)
4. Tool auto-paused via MCP policy firewall
5. Audit log contains "paused_for_budget_exceed" entry
6. Tool successfully resumed via MCP command
7. Resume event logged in audit trail
8. Cleanup successful (0 remaining test records)

### ⚠️ WARN Criteria

- Some layers operational but manual intervention required
- Pause triggered but audit log missing
- Resume successful but not logged

### ❌ FAIL Criteria

- Critical component missing (Layer 3 or 4)
- Cost Guard query fails
- Auto-pause does not trigger despite breach
- Unable to resume tool via MCP
- Cost governance compromised

---

## 🔄 Execution Workflow

### Phase 1: Setup
1. Verify all component files exist
2. Review MCP policy and Cost Guard configuration
3. Ensure Composio MCP server running on port 3001

### Phase 2: Simulation
4. Execute INSERT statements via `neon_execute_sql` tool
5. Verify 5 rows inserted with total_cost = $27.00
6. Confirm timestamps are today's date

### Phase 3: Verification
7. Run Cost Guard query to detect breach
8. Verify `action_required = "PAUSE_REQUIRED"`
9. Check audit log for pause event

### Phase 4: Pause Testing
10. Verify tool status = "paused" or "disabled"
11. Attempt to run Apify actor (should be blocked)
12. Confirm audit log entry exists

### Phase 5: Rollback
13. Execute `composio_resume_tool` via MCP
14. Verify tool status = "active" or "enabled"
15. Confirm resume event logged

### Phase 6: Cleanup
16. Execute cleanup SQL to remove test data
17. Verify 0 remaining audit records
18. Confirm audit log cleaned

---

## 📈 Scoring System

| Score | Status | Meaning |
|-------|--------|---------|
| 100% | ✅ PASS | All checks passed, layer fully operational |
| 75-99% | ⚠️ WARN | Most checks passed, minor issues detected |
| 50-74% | ⚠️ WARN | Half of checks passed, significant gaps |
| 0-49% | ❌ FAIL | Critical failures, layer compromised |
| N/A | ⏳ PENDING | Manual execution required |

**Overall System Status**:
- **PASS**: All 5 layers score ≥ 75%
- **WARN**: 3-4 layers score ≥ 75%
- **FAIL**: < 3 layers score ≥ 75%

---

## 🛠️ Troubleshooting

### Issue: Simulation data not inserted
**Solution**: Verify Neon database connection and table schema exists

### Issue: Cost Guard query returns 0
**Solution**: Check date filters and ensure run_started_at is current_date

### Issue: Pause not triggered
**Solution**: Verify apify_cost_guard.json schedule and MCP connectivity

### Issue: Audit log empty
**Solution**: Check if validation_log table exists and has write permissions

### Issue: Resume command fails
**Solution**: Verify tool_name spelling and Composio API credentials

---

## 📝 Additional Testing Scenarios

### Scenario 1: Under Budget
- Insert 3 runs totaling $18.00
- Expected: action_required = "WITHIN_BUDGET", no pause

### Scenario 2: Exactly at Limit
- Insert runs totaling $25.00
- Expected: action_required = "WITHIN_BUDGET", no pause

### Scenario 3: Multiple Breaches
- Insert $30 total, verify pause
- Resume tool
- Insert another $30 total, verify pause again

### Scenario 4: Pre-flight Rejection
- Call validateApifyInput() with 501 leads
- Expected: Function throws error before MCP call

---

## 📚 Reference Documentation

- **Cost Governance**: `analysis/APIFY_COST_GOVERNANCE.md`
- **Pre-flight Validation**: `apps/outreach-process-manager/utils/validateApifyInput.js`
- **MCP Policy**: `analysis/COMPOSIO_MCP_POLICY_APIFY_LIMITS.json`
- **Cost Guard Job**: `apps/outreach-process-manager/jobs/apify_cost_guard.json`
- **Ledger Schema**: `apps/outreach-process-manager/migrations/2025-10-24_create_actor_usage_log.sql`

---

**Doctrine Reference**: 04.04.07 - Apify Cost Governance
**Audit Script**: `analysis/audit_apify_cost_governance.js`
**Report File**: `analysis/APIFY_COST_GOVERNANCE_AUDIT_REPORT.md`
**Generated**: 2025-10-22
**Report Version**: 1.0
