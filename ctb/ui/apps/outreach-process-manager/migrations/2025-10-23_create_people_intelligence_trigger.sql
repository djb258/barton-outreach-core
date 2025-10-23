-- ============================================================================
-- Migration: Create people_intelligence INSERT Trigger
-- Date: 2025-10-23
-- Purpose: Auto-log to unified_audit_log and trigger PLE workflow
-- Barton Doctrine: People intelligence automation (04.04.04.XX.XXXXX.XXX)
-- ============================================================================

-- ============================================================================
-- FUNCTION: marketing.after_people_intelligence_insert()
-- ============================================================================
-- Trigger function that executes after INSERT on people_intelligence
--
-- Actions:
--   1. Logs the change to marketing.unified_audit_log
--   2. Triggers PLE (Promoted Lead Enrichment) via Composio MCP
--
-- Doctrine Reference: 04.04.04 (People Intelligence microprocess)
-- Integration: Unified audit trail + PLE workflow automation
--
-- Audit Log Entry:
--   - unique_id: person_unique_id from new intelligence record
--   - process_id: '04.04.04' (people intelligence Barton ID segment)
--   - status: 'success' (intelligence successfully recorded)
--   - actor: 'linkedin_sync' (source of the change detection)
--   - source: 'linkedin' (data source)
--   - action: 'update_person' (intelligence update action)
--   - step: 'step_2b_enrich' (enrichment phase in pipeline)
--   - record_type: 'people' (person record)
--   - after_values: JSONB with new_title and change_type
--
-- PLE Trigger:
--   - Calls composio_post_to_tool() to enqueue lead in PLE workflow
--   - Sends person_id, company_id, change_type, source
--   - Tool: 'ple_enqueue_lead' (PLE workflow entry point)
--   - MCP integration via Composio global policy
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.after_people_intelligence_insert()
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
        before_values,
        after_values
    )
    VALUES (
        NEW.person_unique_id,
        '04.04.04',  -- People intelligence Barton ID segment
        'success',
        'linkedin_sync',
        'linkedin',
        'update_person',
        'step_2b_enrich',  -- Enrichment phase
        'people',
        NULL,  -- No before values for new intelligence record
        jsonb_build_object(
            'new_title', NEW.new_title,
            'change_type', NEW.change_type,
            'previous_title', NEW.previous_title,
            'detected_at', NEW.detected_at,
            'intel_unique_id', NEW.intel_unique_id,
            'verified', NEW.verified
        )
    );

    -- Trigger PLE workflow via Composio MCP
    -- Note: composio_post_to_tool() must be implemented via pg_http extension or external notification
    PERFORM marketing.composio_post_to_tool(
        'ple_enqueue_lead',
        jsonb_build_object(
            'person_id', NEW.person_unique_id,
            'company_id', NEW.company_unique_id,
            'change_type', NEW.change_type,
            'source', 'linkedin',
            'intel_id', NEW.intel_unique_id,
            'priority', CASE
                WHEN NEW.change_type IN ('promotion', 'new_company') THEN 'high'
                ELSE 'medium'
            END
        )
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.after_people_intelligence_insert() IS
    'Trigger function for people_intelligence INSERT events.

    Actions:
      1. Logs change to marketing.unified_audit_log
      2. Triggers PLE (Promoted Lead Enrichment) via Composio MCP

    Doctrine: 04.04.04 (People Intelligence)
    Integration: Audit trail + PLE workflow automation

    Requires:
      - marketing.unified_audit_log table
      - marketing.composio_post_to_tool() function (MCP integration)
      - PLE workflow endpoint configured in Composio';

-- ============================================================================
-- TRIGGER: trg_after_people_intelligence_insert
-- ============================================================================
-- Fires after each INSERT on marketing.people_intelligence
-- Executes after_people_intelligence_insert() function
-- ============================================================================

CREATE TRIGGER trg_after_people_intelligence_insert
    AFTER INSERT ON marketing.people_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION marketing.after_people_intelligence_insert();

COMMENT ON TRIGGER trg_after_people_intelligence_insert ON marketing.people_intelligence IS
    'Auto-logs intelligence changes to unified_audit_log and triggers PLE workflow.
    Fires after every INSERT on people_intelligence table.';

-- ============================================================================
-- HELPER FUNCTION: marketing.composio_post_to_tool()
-- ============================================================================
-- Wrapper for Composio MCP HTTP POST calls from PostgreSQL
-- Requires: pg_http extension or external notification system
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.composio_post_to_tool(
    tool_name TEXT,
    tool_data JSONB
)
RETURNS VOID AS $$
DECLARE
    composio_url TEXT;
    composio_user_id TEXT;
    payload JSONB;
    http_request_id BIGINT;
BEGIN
    -- Get Composio MCP configuration from environment or settings table
    -- In production, these should be stored in a configuration table
    composio_url := 'http://localhost:3001/tool';
    composio_user_id := 'usr_default';  -- Should be loaded from config

    -- Build HEIR/ORBT compliant payload
    payload := jsonb_build_object(
        'tool', tool_name,
        'data', tool_data,
        'unique_id', 'HEIR-' || to_char(NOW(), 'YYYY-MM') || '-PLE-TRIGGER-' || extract(epoch from NOW())::text,
        'process_id', 'PRC-PLE-' || extract(epoch from NOW())::text,
        'orbt_layer', 2,
        'blueprint_version', '1.0'
    );

    -- Make HTTP POST to Composio MCP
    -- Note: This requires pg_http extension to be installed
    -- Alternative: Use NOTIFY/LISTEN and external worker process

    BEGIN
        -- Using pg_http extension (if available)
        -- http_request_id := http_post(
        --     composio_url || '?user_id=' || composio_user_id,
        --     payload::text,
        --     'application/json'
        -- );

        -- Fallback: Use PostgreSQL NOTIFY for external worker
        PERFORM pg_notify(
            'composio_mcp_request',
            jsonb_build_object(
                'tool', tool_name,
                'data', tool_data,
                'url', composio_url,
                'user_id', composio_user_id,
                'timestamp', NOW()
            )::text
        );

        RAISE NOTICE 'Composio MCP tool call queued: % with data: %', tool_name, tool_data;

    EXCEPTION
        WHEN OTHERS THEN
            -- Log error but don't fail the transaction
            RAISE WARNING 'Failed to call Composio MCP tool %: % (SQLSTATE: %)',
                tool_name, SQLERRM, SQLSTATE;
    END;

END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.composio_post_to_tool(TEXT, JSONB) IS
    'Wrapper for Composio MCP HTTP POST calls from PostgreSQL triggers.

    Implementation Options:
      1. pg_http extension - Direct HTTP POST to Composio MCP
      2. NOTIFY/LISTEN - Queue requests for external worker
      3. Foreign Data Wrapper - Async job queue

    Current Implementation: NOTIFY pattern (most compatible)
    Requires: External worker process listening on composio_mcp_request channel

    Parameters:
      - tool_name: Composio tool to execute (e.g., ple_enqueue_lead)
      - tool_data: JSONB payload for the tool

    Returns: VOID (async operation)';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Manual insert that will trigger audit + PLE
-- INSERT INTO marketing.people_intelligence (
--     intel_unique_id,
--     person_unique_id,
--     company_unique_id,
--     change_type,
--     previous_title,
--     new_title,
--     detected_at,
--     verified
-- ) VALUES (
--     marketing.generate_people_intelligence_barton_id(),
--     '04.04.02.84.48151.001',
--     '04.04.01.84.48151.001',
--     'promotion',
--     'VP of Sales',
--     'Chief Revenue Officer',
--     NOW(),
--     TRUE
-- );
--
-- Result:
--   1. New row in people_intelligence
--   2. Audit log entry in unified_audit_log
--   3. PLE workflow triggered via Composio MCP

-- Example 2: View audit log for recent intelligence changes
-- SELECT
--     unique_id,
--     action,
--     step,
--     after_values->>'new_title' AS new_title,
--     after_values->>'change_type' AS change_type,
--     created_at
-- FROM marketing.unified_audit_log
-- WHERE process_id = '04.04.04'
--   AND action = 'update_person'
-- ORDER BY created_at DESC
-- LIMIT 20;

-- Example 3: Check if trigger is active
-- SELECT
--     trigger_name,
--     event_manipulation,
--     action_timing,
--     action_statement
-- FROM information_schema.triggers
-- WHERE event_object_table = 'people_intelligence'
--   AND trigger_schema = 'marketing';

-- ============================================================================
-- EXTERNAL WORKER INTEGRATION
-- ============================================================================
--
-- Python/Node.js worker process example to handle NOTIFY messages:
--
-- // Node.js example using pg library
-- const client = new Client({ connectionString: NEON_DATABASE_URL });
-- await client.connect();
--
-- await client.query('LISTEN composio_mcp_request');
--
-- client.on('notification', async (msg) => {
--   const payload = JSON.parse(msg.payload);
--
--   // Make Composio MCP HTTP POST
--   const response = await fetch(`${payload.url}?user_id=${payload.user_id}`, {
--     method: 'POST',
--     headers: { 'Content-Type': 'application/json' },
--     body: JSON.stringify({
--       tool: payload.tool,
--       data: payload.data,
--       unique_id: `HEIR-${Date.now()}`,
--       process_id: `PRC-PLE-${Date.now()}`,
--       orbt_layer: 2,
--       blueprint_version: '1.0'
--     })
--   });
--
--   console.log(`Composio MCP call completed: ${payload.tool}`);
-- });
--
-- ============================================================================

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT EXECUTE ON FUNCTION marketing.after_people_intelligence_insert() TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.composio_post_to_tool(TEXT, JSONB) TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Function: marketing.after_people_intelligence_insert() (created)
-- Function: marketing.composio_post_to_tool() (created)
-- Trigger: trg_after_people_intelligence_insert (created)
-- Table: marketing.people_intelligence (trigger added)
-- Integration: unified_audit_log + Composio MCP PLE workflow
-- Automation: Every people_intelligence INSERT → audit log + PLE trigger
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Trigger Workflow:
--    INSERT people_intelligence
--      → after_people_intelligence_insert() fires
--      → INSERT unified_audit_log (audit trail)
--      → composio_post_to_tool('ple_enqueue_lead', {...}) (PLE workflow)
--      → External worker receives NOTIFY
--      → Worker POSTs to Composio MCP
--      → PLE workflow executes
--
-- 2. Audit Log Structure:
--    - unique_id: person_unique_id (links to person)
--    - process_id: '04.04.04' (people intelligence Barton segment)
--    - status: 'success' (intelligence recorded)
--    - actor: 'linkedin_sync' (automated source)
--    - source: 'linkedin' (data origin)
--    - action: 'update_person' (change type)
--    - step: 'step_2b_enrich' (enrichment phase)
--    - after_values: JSONB with change details
--
-- 3. PLE Trigger:
--    - Tool: 'ple_enqueue_lead' (PLE workflow entry)
--    - Data: person_id, company_id, change_type, source, intel_id
--    - Priority: 'high' for promotions/new_company, 'medium' otherwise
--    - Composio MCP handles workflow orchestration
--
-- 4. Implementation Options:
--    a) pg_http extension - Direct HTTP calls (requires extension)
--    b) NOTIFY/LISTEN - External worker pattern (current)
--    c) Foreign Data Wrapper - Queue-based (complex setup)
--
-- 5. Error Handling:
--    - Composio MCP failures don't rollback transaction
--    - Warnings logged but intelligence record persists
--    - Audit log entry always created
--    - External worker can retry failed MCP calls
--
-- 6. Performance Considerations:
--    - Trigger adds ~5-10ms per INSERT
--    - NOTIFY is async and doesn't block
--    - External worker processes MCP calls in parallel
--    - Audit log insert is fast (indexed on unique_id, created_at)
--
-- 7. Testing:
--    - Insert test intelligence record
--    - Verify audit log entry created
--    - Check NOTIFY message sent (pg_stat_activity)
--    - Confirm external worker receives message
--    - Validate Composio MCP endpoint receives POST
--
-- 8. Future Enhancements:
--    - Add retry logic for failed MCP calls
--    - Implement priority queue (high/medium/low)
--    - Add rate limiting for MCP calls
--    - Create monitoring dashboard for trigger performance
--    - Add circuit breaker for MCP endpoint failures
--    - Implement dead letter queue for failed jobs
--
-- 9. Required Components:
--    - marketing.people_intelligence table (exists)
--    - marketing.unified_audit_log table (exists)
--    - External worker process (Node.js/Python/Go)
--    - Composio MCP server running on localhost:3001
--    - PLE workflow configured in Composio
--
-- 10. Configuration:
--     - Composio MCP URL: Should be in config table or environment
--     - Composio user_id: Should be loaded from config
--     - External worker: Should be deployed as systemd service/PM2
--     - NOTIFY channel: 'composio_mcp_request'
--
-- ============================================================================
