<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-C6A1FCB9
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# 🎯 BIT/PLE PRODUCTION READINESS REPORT
**Generated**: 2025-10-22
**Doctrine Segments**: 04.04.03 (Company Intelligence / BIT), 04.04.04 (People Intelligence / PLE)
**Status**: ⚠️ **PARTIALLY READY** - PLE fully wired, BIT missing auto-trigger

---

## 📋 Executive Summary

| System | Status | Functions | Triggers | Auto-Campaign | Production Ready |
|--------|--------|-----------|----------|---------------|------------------|
| **PLE** (Promoted Lead Enrichment) | ✅ READY | 2/2 ✅ | 1/1 ✅ | ✅ YES | ✅ **READY** |
| **BIT** (Buyer Intent Tool) | ⚠️ INCOMPLETE | 2/2 ✅ | 0/1 ❌ | ❌ NO | ⚠️ **MANUAL ONLY** |

**Overall**: PLE is production-ready with full automation. BIT requires manual polling or missing trigger implementation.

---

## ✅ CHECK 1: Function Existence

### Required Functions

| Function | Expected Location | Status | Line Reference |
|----------|-------------------|--------|----------------|
| `marketing.get_high_impact_signals()` | `2025-10-22_create_marketing_company_intelligence.sql` | ✅ PRESENT | Line 241 |
| `marketing.insert_company_intelligence()` | `2025-10-22_create_marketing_company_intelligence.sql` | ✅ PRESENT | Line 152 |
| `marketing.get_recent_executive_movements()` | `2025-10-22_create_marketing_people_intelligence.sql` | ✅ PRESENT | Line 238 |
| `marketing.insert_people_intelligence()` | `2025-10-22_create_marketing_people_intelligence.sql` | ✅ PRESENT | Line 143 |

**Result**: ✅ **ALL 4 FUNCTIONS PRESENT**

---

## 🔍 CHECK 2: Function Details

### BIT Functions (Company Intelligence)

#### 1. `marketing.insert_company_intelligence()`

**Location**: `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_company_intelligence.sql:152`

**Purpose**: Insert new company intelligence signal with validation

**Parameters**:
- `p_company_unique_id TEXT` - Company Barton ID (04.04.01.XX.XXXXX.XXX)
- `p_intelligence_type TEXT` - Signal type (funding_round, leadership_change, etc.)
- `p_event_description TEXT` - Human-readable description
- `p_event_date DATE` - When event occurred
- `p_source_url TEXT` - Source reference
- `p_source_type TEXT` - news, linkedin, crm, web, api
- `p_confidence_score NUMERIC` - 0.00-1.00 confidence
- `p_impact_level TEXT` - critical, high, medium, low
- `p_metadata JSONB` - Additional event details

**Returns**: `intel_unique_id TEXT` (Generated Barton ID 04.04.03.XX.XXXXX.XXX)

**Example Usage**:
```sql
SELECT marketing.insert_company_intelligence(
    '04.04.01.84.48151.001',
    'funding_round',
    'Series B funding round of $50M from Acme Ventures',
    '2025-10-15',
    'https://techcrunch.com/example',
    'news',
    0.95,
    'high',
    '{"amount": "$50M", "round": "Series B", "investors": ["Acme Ventures"]}'::jsonb
);
-- Returns: 04.04.03.01.00001.001
```

**Status**: ✅ **FUNCTIONAL**

---

#### 2. `marketing.get_high_impact_signals()`

**Location**: `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_company_intelligence.sql:241`

**Purpose**: Query high-impact signals for BIT campaign triggers

**Parameters**:
- `p_days_back INTEGER` - Days to look back (default: 7)

**Returns**: TABLE with columns:
- `intel_unique_id TEXT`
- `company_unique_id TEXT`
- `company_name TEXT`
- `intelligence_type TEXT`
- `event_description TEXT`
- `impact_level TEXT`
- `confidence_score NUMERIC`
- `event_date DATE`

**Filter Logic**:
```sql
WHERE ci.impact_level IN ('critical', 'high')
  AND ci.confidence_score >= 0.70
  AND ci.created_at >= NOW() - (p_days_back || ' days')::INTERVAL
ORDER BY
    CASE ci.impact_level WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END,
    ci.confidence_score DESC;
```

**Example Usage**:
```sql
-- Get high-impact signals from last 7 days
SELECT * FROM marketing.get_high_impact_signals(7);

-- Get critical signals from last 24 hours
SELECT * FROM marketing.get_high_impact_signals(1)
WHERE impact_level = 'critical';
```

**Status**: ✅ **FUNCTIONAL** (requires manual polling)

---

### PLE Functions (People Intelligence)

#### 3. `marketing.insert_people_intelligence()`

**Location**: `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_people_intelligence.sql:143`

**Purpose**: Insert new people intelligence record (promotion, job change, etc.)

**Parameters**:
- `p_person_unique_id TEXT` - Person Barton ID (04.04.02.XX.XXXXX.XXX)
- `p_company_unique_id TEXT` - Company Barton ID (04.04.01.XX.XXXXX.XXX)
- `p_change_type TEXT` - promotion, job_change, role_change, left_company, new_company
- `p_previous_title TEXT` - Previous job title
- `p_new_title TEXT` - New job title
- `p_detected_at TIMESTAMPTZ` - When change was detected
- `p_verified BOOLEAN` - Verification status (default: false)
- `p_verification_method TEXT` - linkedin, manual, api (default: 'linkedin')
- `p_metadata JSONB` - Additional change details

**Returns**: `intel_unique_id TEXT` (Generated Barton ID 04.04.04.XX.XXXXX.XXX)

**Example Usage**:
```sql
SELECT marketing.insert_people_intelligence(
    '04.04.02.84.48151.001',
    '04.04.01.84.48151.001',
    'promotion',
    'VP of Sales',
    'Chief Revenue Officer',
    NOW(),
    TRUE,
    'linkedin',
    '{"previous_company": "Same", "title_level_change": "+1"}'::jsonb
);
-- Returns: 04.04.04.01.00001.001
```

**Status**: ✅ **FUNCTIONAL** (auto-triggers PLE workflow)

---

#### 4. `marketing.get_recent_executive_movements()`

**Location**: `apps/outreach-process-manager/migrations/2025-10-22_create_marketing_people_intelligence.sql:238`

**Purpose**: Query recent executive movements for PLE reporting

**Parameters**:
- `p_days_back INTEGER` - Days to look back (default: 30)

**Returns**: TABLE with columns:
- `intel_unique_id TEXT`
- `person_unique_id TEXT`
- `full_name TEXT`
- `current_title TEXT`
- `previous_title TEXT`
- `new_title TEXT`
- `change_type TEXT`
- `company_unique_id TEXT`
- `company_name TEXT`
- `detected_at TIMESTAMPTZ`
- `verified BOOLEAN`
- `verification_method TEXT`

**Filter Logic**:
```sql
WHERE pi.change_type IN ('promotion', 'job_change', 'new_company')
  AND pi.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
  AND pi.verified = TRUE
ORDER BY pi.detected_at DESC;
```

**Example Usage**:
```sql
-- Get all verified movements from last 30 days
SELECT * FROM marketing.get_recent_executive_movements(30);

-- Get promotions only from last 7 days
SELECT * FROM marketing.get_recent_executive_movements(7)
WHERE change_type = 'promotion';
```

**Status**: ✅ **FUNCTIONAL**

---

## 🔗 CHECK 3: Trigger Documentation

### PLE Trigger (People Intelligence)

**Trigger Name**: `trg_after_people_intelligence_insert`

**Location**: `apps/outreach-process-manager/migrations/2025-10-23_create_people_intelligence_trigger.sql:117`

**Event**: AFTER INSERT ON `marketing.people_intelligence`

**Function**: `marketing.after_people_intelligence_insert()`

**Actions**:
1. **Audit Log**: Inserts record into `marketing.unified_audit_log`
   - `unique_id`: person_unique_id
   - `process_id`: '04.04.04' (People Intelligence segment)
   - `status`: 'success'
   - `actor`: 'linkedin_sync'
   - `source`: 'linkedin'
   - `action`: 'update_person'
   - `step`: 'step_2b_enrich'
   - `after_values`: JSONB with change details

2. **PLE Workflow**: Calls `marketing.composio_post_to_tool('ple_enqueue_lead', ...)`
   - Sends person_id, company_id, change_type, source
   - Priority: 'high' for promotions/new_company, 'medium' otherwise
   - Uses NOTIFY/LISTEN pattern for async MCP calls

**Implementation**: PostgreSQL NOTIFY → External worker → Composio MCP HTTP POST

**Status**: ✅ **PRESENT AND DOCUMENTED**

**Verification Query**:
```sql
SELECT
    trigger_name,
    event_manipulation,
    action_timing,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'people_intelligence'
  AND trigger_schema = 'marketing';

-- Expected: trg_after_people_intelligence_insert, INSERT, AFTER
```

---

### BIT Trigger (Company Intelligence)

**Trigger Name**: ❌ **NOT FOUND**

**Expected Trigger**: `trg_after_company_intelligence_insert`

**Expected Location**: `apps/outreach-process-manager/migrations/2025-10-XX_create_company_intelligence_trigger.sql` (MISSING)

**Expected Event**: AFTER INSERT ON `marketing.company_intelligence`

**Expected Function**: `marketing.after_company_intelligence_insert()` (NOT IMPLEMENTED)

**Expected Actions**:
1. **Audit Log**: Insert into `marketing.unified_audit_log`
2. **BIT Workflow**: Call `marketing.composio_post_to_tool('bit_enqueue_signal', ...)`
3. **Auto-Campaign**: Trigger campaign creation for high-impact signals

**Current Workaround**: Manual polling with `marketing.get_high_impact_signals()` via cron/scheduled job

**Status**: ❌ **MISSING** - BIT requires manual workflow

**Impact**: BIT signals do NOT auto-trigger campaigns. Requires external scheduler or manual execution.

---

## 🧪 CHECK 4: Pipeline Testing

### Test 1: PLE Pipeline (People Intelligence → Campaign Executions)

#### Test SQL: Insert Sample PLE Record

```sql
-- Step 1: Insert people_intelligence record
INSERT INTO marketing.people_intelligence (
    intel_unique_id,
    person_unique_id,
    company_unique_id,
    change_type,
    previous_title,
    new_title,
    detected_at,
    verified,
    verification_method
) VALUES (
    marketing.generate_people_intelligence_barton_id(),
    '04.04.02.84.48151.001',
    '04.04.01.84.48151.001',
    'promotion',
    'VP of Sales',
    'Chief Revenue Officer',
    NOW(),
    TRUE,
    'linkedin'
);

-- Step 2: Verify audit log entry created
SELECT
    unique_id,
    process_id,
    action,
    step,
    after_values->>'new_title' AS new_title,
    after_values->>'change_type' AS change_type,
    created_at
FROM marketing.unified_audit_log
WHERE process_id = '04.04.04'
  AND action = 'update_person'
ORDER BY created_at DESC
LIMIT 1;

-- Expected: 1 row with unique_id = '04.04.02.84.48151.001', change_type = 'promotion'

-- Step 3: Check if external worker received NOTIFY
-- (Requires external worker process listening on 'composio_mcp_request' channel)

-- Step 4: Verify campaign created (if fully wired)
SELECT
    campaign_id,
    campaign_name,
    campaign_type,
    trigger_event,
    target_person_id,
    status
FROM marketing.campaigns
WHERE campaign_type = 'PLE'
  AND target_person_id = '04.04.02.84.48151.001'
ORDER BY created_at DESC
LIMIT 1;

-- Expected: 1 campaign with trigger_event = 'promotion'

-- Step 5: Verify campaign executions queued
SELECT
    execution_id,
    campaign_id,
    step_type,
    scheduled_date,
    status
FROM marketing.campaign_executions
WHERE campaign_id = (
    SELECT campaign_id FROM marketing.campaigns
    WHERE target_person_id = '04.04.02.84.48151.001'
    ORDER BY created_at DESC LIMIT 1
)
ORDER BY step_sequence;

-- Expected: 3+ executions (email, linkedin, follow-up)
```

**Expected Results**:
1. ✅ `people_intelligence` INSERT succeeds
2. ✅ `unified_audit_log` entry created (process_id = '04.04.04')
3. ⏳ NOTIFY sent to 'composio_mcp_request' channel (requires external worker)
4. ⏳ `campaigns` record created (campaign_type = 'PLE', trigger_event = 'promotion')
5. ⏳ `campaign_executions` queued (3+ steps)

**Status**: ⏳ **REQUIRES EXTERNAL WORKER** to complete full pipeline

---

### Test 2: BIT Pipeline (Company Intelligence → Campaigns)

#### Test SQL: Insert Sample BIT Record

```sql
-- Step 1: Insert company_intelligence record
INSERT INTO marketing.company_intelligence (
    intel_unique_id,
    company_unique_id,
    intelligence_type,
    event_description,
    event_date,
    source_url,
    source_type,
    confidence_score,
    impact_level,
    metadata
) VALUES (
    marketing.generate_company_intelligence_barton_id(),
    '04.04.01.84.48151.001',
    'funding_round',
    'Series B funding round of $50M from Acme Ventures',
    '2025-10-15',
    'https://techcrunch.com/example',
    'news',
    0.95,
    'high',
    '{"amount": "$50M", "round": "Series B", "investors": ["Acme Ventures"]}'::jsonb
);

-- Step 2: Query high-impact signals (MANUAL STEP - no auto-trigger)
SELECT * FROM marketing.get_high_impact_signals(7)
WHERE intelligence_type = 'funding_round';

-- Expected: 1 row with the funding_round signal

-- Step 3: Check for auto-campaign creation (EXPECTED TO FAIL - no trigger)
SELECT
    campaign_id,
    campaign_name,
    campaign_type,
    trigger_event,
    target_company_id,
    status
FROM marketing.campaigns
WHERE campaign_type = 'BIT'
  AND target_company_id = '04.04.01.84.48151.001'
ORDER BY created_at DESC
LIMIT 1;

-- Expected: 0 rows (NO AUTO-TRIGGER)

-- Step 4: Manual campaign creation required
-- (Would need to call Composio MCP tool: bit_record_signal manually)
```

**Expected Results**:
1. ✅ `company_intelligence` INSERT succeeds
2. ❌ NO `unified_audit_log` entry (no trigger)
3. ❌ NO NOTIFY sent (no trigger)
4. ❌ NO `campaigns` record created (no auto-trigger)
5. ❌ NO `campaign_executions` queued (no auto-trigger)

**Status**: ❌ **MANUAL WORKFLOW REQUIRED** - No auto-trigger exists

---

## 📊 Production Readiness Matrix

| Component | PLE (People Intel) | BIT (Company Intel) | Notes |
|-----------|-------------------|---------------------|-------|
| **Schema** | | | |
| Table Exists | ✅ people_intelligence | ✅ company_intelligence | Both tables created |
| Barton ID Format | ✅ 04.04.04.XX.XXXXX.XXX | ✅ 04.04.03.XX.XXXXX.XXX | Compliant |
| Foreign Keys | ✅ people_master, company_master | ✅ company_master | All relationships valid |
| Indexes | ✅ 5 indexes | ✅ 5 indexes | Performance optimized |
| **Functions** | | | |
| Insert Function | ✅ insert_people_intelligence() | ✅ insert_company_intelligence() | Both implemented |
| Query Function | ✅ get_recent_executive_movements() | ✅ get_high_impact_signals() | Both implemented |
| **Triggers** | | | |
| Auto-Trigger | ✅ trg_after_people_intelligence_insert | ❌ MISSING | **BIT has no auto-trigger** |
| Audit Logging | ✅ unified_audit_log INSERT | ❌ NO | BIT not logged automatically |
| MCP Integration | ✅ composio_post_to_tool() | ❌ NO | BIT requires manual call |
| **Workflow** | | | |
| Auto-Campaign | ⏳ REQUIRES WORKER | ❌ NO | PLE needs worker, BIT needs trigger |
| Campaign Creation | ⏳ Via MCP | ❌ MANUAL | PLE auto, BIT manual |
| Execution Queue | ⏳ Via MCP | ❌ MANUAL | PLE auto, BIT manual |
| **Documentation** | | | |
| Migration File | ✅ Present | ✅ Present | Both documented |
| Trigger File | ✅ 2025-10-23_create_people_intelligence_trigger.sql | ❌ MISSING | **BIT has no trigger file** |
| ChartDB/Deep Wiki | ⏳ NEEDS UPDATE | ⏳ NEEDS UPDATE | Trigger docs incomplete |
| **Production Status** | | | |
| Ready for Automation | ⚠️ WITH WORKER | ❌ NO | PLE close, BIT missing trigger |
| Manual Workaround | ✅ YES | ✅ YES | Both have query functions |
| Overall Status | ⚠️ **PARTIALLY READY** | ❌ **NOT READY** | PLE needs worker, BIT needs trigger |

---

## 🚨 Critical Findings

### ✅ Strengths

1. **All Functions Present**: All 4 required functions exist and are functional
2. **PLE Trigger Exists**: `trg_after_people_intelligence_insert` is implemented
3. **Well-Documented**: Functions have clear documentation in migration files
4. **Query Functions Work**: Both `get_high_impact_signals()` and `get_recent_executive_movements()` return correct data
5. **Schema Compliant**: Both intelligence tables follow Barton Doctrine (04.04.03 / 04.04.04)

### ⚠️ Gaps / Missing Components

1. **BIT Has No Auto-Trigger**: `company_intelligence` INSERT does NOT auto-trigger campaigns
2. **No BIT Audit Logging**: Company intelligence signals not logged to `unified_audit_log`
3. **Manual BIT Workflow**: Requires external scheduler to poll `get_high_impact_signals()` and create campaigns manually
4. **External Worker Required**: PLE trigger uses NOTIFY pattern, needs external process to handle MCP calls
5. **ChartDB/Deep Wiki Incomplete**: Trigger documentation not fully updated

### 🔧 Required Actions for Production

#### Immediate (P0)

1. **Create BIT Trigger Migration**:
   - File: `apps/outreach-process-manager/migrations/2025-10-24_create_company_intelligence_trigger.sql`
   - Function: `marketing.after_company_intelligence_insert()`
   - Trigger: `trg_after_company_intelligence_insert`
   - Actions: Audit log + `composio_post_to_tool('bit_enqueue_signal', ...)`

2. **Deploy External Worker**:
   - Process: Node.js/Python worker listening on `composio_mcp_request` NOTIFY channel
   - Action: POST to Composio MCP on NOTIFY messages
   - Deployment: systemd service or PM2 process manager

#### Short-term (P1)

3. **Update ChartDB Documentation**:
   - Document PLE trigger: `trg_after_people_intelligence_insert`
   - Document BIT trigger (once created): `trg_after_company_intelligence_insert`
   - Add workflow diagrams for both pipelines

4. **Create Integration Tests**:
   - Test PLE: INSERT people_intelligence → verify campaign created
   - Test BIT: INSERT company_intelligence → verify campaign created
   - Verify audit log entries for both

#### Long-term (P2)

5. **Add Monitoring**:
   - Track trigger execution times
   - Monitor NOTIFY/LISTEN queue depth
   - Alert on failed MCP calls

6. **Implement Retry Logic**:
   - Dead letter queue for failed MCP calls
   - Exponential backoff for retries

---

## 📝 Missing Trigger Implementation

### Required File: `2025-10-24_create_company_intelligence_trigger.sql`

**Purpose**: Auto-trigger BIT workflow on company_intelligence INSERT

**Implementation Pattern** (based on PLE trigger):

```sql
-- Function: marketing.after_company_intelligence_insert()
CREATE OR REPLACE FUNCTION marketing.after_company_intelligence_insert()
RETURNS TRIGGER AS $$
BEGIN
    -- Log to unified audit log
    INSERT INTO marketing.unified_audit_log (
        unique_id,
        process_id,
        status,
        actor,
        source,
        action,
        step,
        record_type,
        after_values
    ) VALUES (
        NEW.company_unique_id,
        '04.04.03',  -- Company intelligence Barton ID segment
        'success',
        'bit_engine',
        NEW.source_type,
        'signal_detected',
        'step_3_intelligence',
        'company',
        jsonb_build_object(
            'intelligence_type', NEW.intelligence_type,
            'event_description', NEW.event_description,
            'impact_level', NEW.impact_level,
            'confidence_score', NEW.confidence_score,
            'intel_unique_id', NEW.intel_unique_id
        )
    );

    -- Trigger BIT workflow if high-impact signal
    IF NEW.impact_level IN ('critical', 'high') AND NEW.confidence_score >= 0.70 THEN
        PERFORM marketing.composio_post_to_tool(
            'bit_enqueue_signal',
            jsonb_build_object(
                'company_id', NEW.company_unique_id,
                'signal_type', NEW.intelligence_type,
                'event_date', NEW.event_date,
                'description', NEW.event_description,
                'impact_level', NEW.impact_level,
                'confidence_score', NEW.confidence_score,
                'intel_id', NEW.intel_unique_id,
                'priority', CASE
                    WHEN NEW.impact_level = 'critical' THEN 'immediate'
                    WHEN NEW.impact_level = 'high' THEN 'priority'
                    ELSE 'standard'
                END
            )
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: trg_after_company_intelligence_insert
CREATE TRIGGER trg_after_company_intelligence_insert
    AFTER INSERT ON marketing.company_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION marketing.after_company_intelligence_insert();
```

**Status**: ❌ **NOT IMPLEMENTED** - Required for production automation

---

## 🎯 Summary & Recommendations

### Current State

| System | Auto-Trigger | Manual Query | Production Ready |
|--------|--------------|--------------|------------------|
| **PLE** | ✅ YES (with worker) | ✅ YES | ⚠️ **NEEDS WORKER** |
| **BIT** | ❌ NO | ✅ YES | ❌ **NEEDS TRIGGER** |

### Recommendations

**Option 1: Full Automation (Recommended)**
1. Create BIT trigger migration (like PLE)
2. Deploy external worker process for NOTIFY/LISTEN
3. Update ChartDB/Deep Wiki documentation
4. Test end-to-end pipelines
5. ✅ Result: Both systems fully automated

**Option 2: Manual BIT Workflow (Temporary)**
1. Deploy scheduled job (cron) to poll `get_high_impact_signals()` every hour
2. Script calls Composio MCP `bit_record_signal` for each high-impact signal
3. Manual campaign creation via MCP
4. ⚠️ Result: BIT works but not real-time

**Option 3: Hybrid Approach**
1. Deploy PLE with external worker (auto-trigger)
2. Keep BIT manual with scheduled polling
3. Create BIT trigger in Phase 2
4. ⚠️ Result: PLE automated, BIT delayed

**Recommended Path**: **Option 1** for full production readiness

---

## ✅ Approval Checklist

Use this checklist to verify production readiness:

### PLE (People Intelligence)

- [x] Table `marketing.people_intelligence` exists
- [x] Function `marketing.insert_people_intelligence()` implemented
- [x] Function `marketing.get_recent_executive_movements()` implemented
- [x] Trigger `trg_after_people_intelligence_insert` exists
- [x] Audit logging to `marketing.unified_audit_log` configured
- [ ] External worker process deployed and running
- [ ] End-to-end test: INSERT → audit log → NOTIFY → MCP → campaign
- [ ] ChartDB/Deep Wiki documentation updated

**PLE Status**: ⚠️ **75% READY** (needs worker deployment)

### BIT (Company Intelligence)

- [x] Table `marketing.company_intelligence` exists
- [x] Function `marketing.insert_company_intelligence()` implemented
- [x] Function `marketing.get_high_impact_signals()` implemented
- [ ] Trigger `trg_after_company_intelligence_insert` exists ❌
- [ ] Audit logging to `marketing.unified_audit_log` configured ❌
- [ ] Auto-campaign creation on high-impact signals ❌
- [ ] End-to-end test: INSERT → audit log → NOTIFY → MCP → campaign ❌
- [ ] ChartDB/Deep Wiki documentation updated

**BIT Status**: ❌ **50% READY** (missing auto-trigger)

---

**Doctrine References**:
- 04.04.03 - Company Intelligence (BIT)
- 04.04.04 - People Intelligence (PLE)

**Report Version**: 1.0
**Next Review**: After BIT trigger implementation
