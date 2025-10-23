-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-C5C41D83
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

-- ============================================================================
-- Migration: Create marketing.upsert_people_intelligence_changes()
-- Date: 2025-10-23
-- Purpose: Detect and log LinkedIn profile changes for monthly refresh workflow
-- Barton Doctrine: People intelligence tracking (04.04.04.XX.XXXXX.XXX)
-- ============================================================================

-- ============================================================================
-- FUNCTION: marketing.upsert_people_intelligence_changes()
-- ============================================================================
-- Compares new LinkedIn data against existing people_master records
-- and creates people_intelligence entries for detected changes
--
-- Integration: Monthly LinkedIn refresh workflow via linkedin_refresh_jobs
-- Doctrine Reference: 04.04.04 (People Intelligence microprocess)
--
-- Parameters:
--   new_data: JSONB array of LinkedIn profile objects with structure:
--     [{
--       "linkedin_url": "https://linkedin.com/in/johndoe",
--       "title": "Chief Revenue Officer",
--       "company": "Acme Corp",
--       "location": "San Francisco, CA",
--       ...
--     }]
--   job_id: Reference to linkedin_refresh_jobs.job_unique_id for audit trail
--
-- Behavior:
--   - Iterates through JSONB array of LinkedIn profiles
--   - Looks up existing person in people_master by linkedin_url
--   - Compares current title vs new title
--   - Inserts people_intelligence record if title changed
--   - Skips profiles not found in people_master (not yet promoted)
--
-- Change Detection:
--   - Title changes: Maps to 'role_change' in people_intelligence
--   - Uses IS DISTINCT FROM for NULL-safe comparison
--   - Generates Barton ID via generate_people_intelligence_barton_id()
--
-- Audit Trail:
--   - Stores job_id in metadata for tracking refresh job
--   - Records linkedin_url for source verification
--   - Sets source_type to 'linkedin' for all changes
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.upsert_people_intelligence_changes(
    new_data JSONB,
    job_id TEXT
)
RETURNS VOID AS $$
DECLARE
    rec JSONB;
    current_title TEXT;
    current_company TEXT;
    person_id TEXT;
    company_id TEXT;
    change_count INTEGER := 0;
BEGIN
    -- Validate job_id format (should be linkedin_refresh_jobs Barton ID)
    IF job_id !~ '^04\\.04\\.06\\.[0-9]{2}\\.[0-9]{5}\\.[0-9]{3}$' THEN
        RAISE WARNING 'Invalid job_id format: %. Expected 04.04.06.XX.XXXXX.XXX', job_id;
    END IF;

    -- Iterate through each LinkedIn profile in the JSONB array
    FOR rec IN SELECT * FROM jsonb_array_elements(new_data)
    LOOP
        -- Look up existing person by LinkedIn URL
        SELECT
            pm.unique_id,
            pm.company_unique_id,
            pm.title
        INTO
            person_id,
            company_id,
            current_title
        FROM marketing.people_master pm
        WHERE pm.linkedin_url = rec->>'linkedin_url';

        -- Skip if person not found in people_master (not yet promoted)
        IF person_id IS NULL THEN
            CONTINUE;
        END IF;

        -- Detect title change (NULL-safe comparison)
        IF current_title IS DISTINCT FROM rec->>'title' THEN
            -- Insert people_intelligence record for title change
            INSERT INTO marketing.people_intelligence (
                intel_unique_id,
                person_unique_id,
                company_unique_id,
                change_type,
                previous_title,
                new_title,
                detected_at,
                verified,
                verification_method,
                metadata
            )
            VALUES (
                marketing.generate_people_intelligence_barton_id(),
                person_id,
                company_id,
                'role_change',  -- Maps title changes to role_change type
                current_title,
                rec->>'title',
                NOW(),
                TRUE,  -- LinkedIn data is considered verified
                'linkedin_refresh',
                jsonb_build_object(
                    'job_id', job_id,
                    'linkedin_url', rec->>'linkedin_url',
                    'source', 'linkedin_monthly_refresh',
                    'detected_via', 'upsert_people_intelligence_changes'
                )
            );

            change_count := change_count + 1;
        END IF;

        -- TODO: Add company change detection
        -- TODO: Add location change detection
        -- TODO: Add profile completeness tracking
    END LOOP;

    -- Log summary
    RAISE NOTICE 'LinkedIn sync completed. Changes detected: %', change_count;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error in upsert_people_intelligence_changes: % (SQLSTATE: %)', SQLERRM, SQLSTATE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION COMMENTS
-- ============================================================================

COMMENT ON FUNCTION marketing.upsert_people_intelligence_changes(JSONB, TEXT) IS
    'Barton Doctrine 04.04.04: People Intelligence Change Detection

    Compares new LinkedIn profile data against existing people_master records
    and creates people_intelligence entries for detected changes.

    Use Case: Monthly LinkedIn refresh workflow
    Integration: Called by LinkedIn sync orchestration after Apify data fetch

    Parameters:
      - new_data: JSONB array of LinkedIn profile objects
      - job_id: Reference to linkedin_refresh_jobs.job_unique_id

    Change Detection:
      - Title changes → role_change in people_intelligence
      - NULL-safe comparison via IS DISTINCT FROM
      - Skips profiles not in people_master

    Audit Trail:
      - Links to linkedin_refresh_jobs via metadata.job_id
      - Records linkedin_url for verification
      - Sets verified=TRUE (LinkedIn is authoritative source)
      - Sets verification_method=linkedin_refresh

    Returns: VOID (inserts records, raises notice with change count)

    Example Usage:
      SELECT marketing.upsert_people_intelligence_changes(
        ''[
          {"linkedin_url": "https://linkedin.com/in/johndoe", "title": "CRO"},
          {"linkedin_url": "https://linkedin.com/in/janedoe", "title": "VP Sales"}
        ]''::jsonb,
        ''04.04.06.84.48151.001''
      );';

-- ============================================================================
-- HELPER FUNCTION: get_linkedin_sync_summary()
-- ============================================================================
-- Returns summary of changes detected by most recent LinkedIn sync
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.get_linkedin_sync_summary(
    p_job_id TEXT DEFAULT NULL,
    p_days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    job_id TEXT,
    change_type TEXT,
    change_count BIGINT,
    example_person_name TEXT,
    example_old_title TEXT,
    example_new_title TEXT,
    detected_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (pi.metadata->>'job_id')::TEXT AS job_id,
        pi.change_type,
        COUNT(*)::BIGINT AS change_count,
        MAX(pm.full_name) AS example_person_name,
        MAX(pi.previous_title) AS example_old_title,
        MAX(pi.new_title) AS example_new_title,
        MAX(pi.detected_at) AS detected_at
    FROM marketing.people_intelligence pi
    JOIN marketing.people_master pm ON pi.person_unique_id = pm.unique_id
    WHERE pi.metadata->>'detected_via' = 'upsert_people_intelligence_changes'
      AND (p_job_id IS NULL OR pi.metadata->>'job_id' = p_job_id)
      AND pi.detected_at >= NOW() - (p_days_back || ' days')::INTERVAL
    GROUP BY (pi.metadata->>'job_id')::TEXT, pi.change_type
    ORDER BY detected_at DESC, change_count DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.get_linkedin_sync_summary(TEXT, INTEGER) IS
    'Returns summary of changes detected by LinkedIn sync jobs.
    Groups by job_id and change_type with counts and examples.';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Basic LinkedIn sync with title changes
-- SELECT marketing.upsert_people_intelligence_changes(
--     '[
--         {
--             "linkedin_url": "https://linkedin.com/in/john-doe",
--             "title": "Chief Revenue Officer",
--             "company": "Acme Corp"
--         },
--         {
--             "linkedin_url": "https://linkedin.com/in/jane-smith",
--             "title": "VP of Engineering",
--             "company": "TechCo"
--         }
--     ]'::jsonb,
--     '04.04.06.84.48151.001'
-- );

-- Example 2: Get summary of changes from latest job
-- SELECT * FROM marketing.get_linkedin_sync_summary('04.04.06.84.48151.001');

-- Example 3: Get all LinkedIn sync changes from last 30 days
-- SELECT * FROM marketing.get_linkedin_sync_summary(NULL, 30);

-- Example 4: Find people whose titles changed in last sync
-- SELECT
--     pm.full_name,
--     pm.title AS current_title_in_db,
--     pi.previous_title AS old_title,
--     pi.new_title AS new_title_from_linkedin,
--     pi.detected_at,
--     pi.metadata->>'job_id' AS sync_job_id
-- FROM marketing.people_intelligence pi
-- JOIN marketing.people_master pm ON pi.person_unique_id = pm.unique_id
-- WHERE pi.metadata->>'detected_via' = 'upsert_people_intelligence_changes'
--   AND pi.detected_at >= NOW() - INTERVAL '7 days'
-- ORDER BY pi.detected_at DESC;

-- Example 5: Update people_master with new titles after review
-- UPDATE marketing.people_master pm
-- SET title = pi.new_title,
--     updated_at = NOW()
-- FROM marketing.people_intelligence pi
-- WHERE pm.unique_id = pi.person_unique_id
--   AND pi.change_type = 'role_change'
--   AND pi.verified = TRUE
--   AND pi.detected_at >= NOW() - INTERVAL '1 day'
--   AND pi.metadata->>'detected_via' = 'upsert_people_intelligence_changes';

-- ============================================================================
-- INTEGRATION WORKFLOW
-- ============================================================================
--
-- Monthly LinkedIn Refresh Process:
--
-- 1. Create LinkedIn refresh job:
--    job_id = insert_linkedin_refresh_job('code_crafter~leads-finder', 1500);
--
-- 2. Call Apify via Composio MCP:
--    - Fetch LinkedIn profiles for all people_master.linkedin_url
--    - Store results in JSONB array
--
-- 3. Detect changes and log to people_intelligence:
--    SELECT marketing.upsert_people_intelligence_changes(apify_results_jsonb, job_id);
--
-- 4. Update job metrics:
--    SELECT marketing.update_linkedin_job_status(
--        job_id,
--        'completed',
--        total_profiles,
--        profiles_changed,
--        profiles_skipped
--    );
--
-- 5. Review changes and update people_master:
--    - Query people_intelligence for new titles
--    - Human review if needed
--    - Batch UPDATE people_master with verified changes
--
-- 6. Generate audit report:
--    SELECT * FROM marketing.get_linkedin_sync_summary(job_id);
--
-- ============================================================================

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT EXECUTE ON FUNCTION marketing.upsert_people_intelligence_changes(JSONB, TEXT) TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.get_linkedin_sync_summary(TEXT, INTEGER) TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Function: marketing.upsert_people_intelligence_changes() (created)
-- Helper Function: marketing.get_linkedin_sync_summary() (created)
-- Doctrine Reference: 04.04.04 (People Intelligence)
-- Integration: linkedin_refresh_jobs + people_intelligence tables
-- Purpose: LinkedIn monthly refresh change detection
-- Change Types: role_change (title changes)
-- Future: company_change, location_change, profile_completeness
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Change Type Mapping:
--    - Title changes → 'role_change' (valid in people_intelligence CHECK constraint)
--    - Future: Detect promotions vs lateral moves via title parsing
--    - Future: Detect company changes → 'job_change' or 'left_company'
--
-- 2. Verification:
--    - All LinkedIn changes marked as verified=TRUE
--    - verification_method='linkedin_refresh'
--    - LinkedIn is considered authoritative for current titles
--
-- 3. Null Safety:
--    - Uses IS DISTINCT FROM for NULL-safe title comparison
--    - Handles cases where current_title or new_title is NULL
--
-- 4. Audit Trail:
--    - metadata.job_id links to linkedin_refresh_jobs
--    - metadata.linkedin_url preserves source
--    - metadata.detected_via='upsert_people_intelligence_changes'
--    - detected_at captures exact timestamp
--
-- 5. Performance:
--    - Single query per profile (lookup by linkedin_url)
--    - Batch insert via single function call
--    - Indexed on people_master.linkedin_url (should exist)
--    - Indexed on people_intelligence.detected_at, change_type
--
-- 6. Error Handling:
--    - Validates job_id format (warns if invalid)
--    - Skips profiles not in people_master (CONTINUE)
--    - Wraps in exception handler with detailed error message
--    - Raises NOTICE with change count summary
--
-- 7. Future Enhancements:
--    - Add company change detection (current_company vs new company)
--    - Add location change tracking
--    - Add profile completeness score
--    - Add promotion detection (title hierarchy analysis)
--    - Add batch update mode (auto-update people_master)
--    - Add dry-run mode (return changes without inserting)
--    - Add conflict resolution (multiple changes for same person)
--
-- 8. Integration Points:
--    - Requires: people_master (linkedin_url, unique_id, title)
--    - Requires: people_intelligence (full schema)
--    - Requires: linkedin_refresh_jobs (job_unique_id)
--    - Requires: generate_people_intelligence_barton_id() function
--
-- ============================================================================
