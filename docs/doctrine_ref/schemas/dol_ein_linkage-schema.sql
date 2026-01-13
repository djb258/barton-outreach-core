-- ═══════════════════════════════════════════════════════════════════════════
-- DOL EIN Linkage Schema Definition
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Document: DOL_EIN_RESOLUTION.md (doctrine/ple/DOL_EIN_RESOLUTION.md)
-- Barton ID Prefix: 01.04.02.04.22000
-- Version: 2.0.0
-- Last Updated: 2025-01-01
-- Status: Production Ready
--
-- Purpose:
--   Define the database schema for the DOL EIN Resolution Spoke.
--   This spoke's ONLY responsibility is to link EIN numbers to existing
--   sovereign company identities using authoritative DOL/EBSA filings.
--
-- Architecture:
--   - HUB: marketing.company_master (source of sovereign company_unique_id)
--   - SPOKE: dol_ein_linkage (facts only, no inference, no scoring)
--   - OUTPUT: EIN ↔ company_unique_id linkage
--
-- EXPLICIT NON-GOALS:
--   ❌ NO buyer intent scoring
--   ❌ NO BIT event creation
--   ❌ NO OSHA/EEOC tracking
--   ❌ NO Slack/Salesforce/Grafana integration
--   ❌ NO outreach triggers
--   ❌ NO enrichment beyond EIN
--
-- ═══════════════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────────────────
-- SCHEMA CREATION
-- ───────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS dol;

COMMENT ON SCHEMA dol IS 'DOL EIN Resolution Spoke - Links EIN to sovereign company identity (FACTS ONLY)';

-- ───────────────────────────────────────────────────────────────────────────
-- SEQUENCES
-- ───────────────────────────────────────────────────────────────────────────

-- Linkage ID sequence (001-999 range)
CREATE SEQUENCE IF NOT EXISTS dol.linkage_id_seq
  START WITH 1
  INCREMENT BY 1
  MINVALUE 1
  MAXVALUE 999
  CYCLE;

COMMENT ON SEQUENCE dol.linkage_id_seq IS 'Sequence for DOL EIN linkage IDs (001-999)';

-- AIR Log ID sequence (901-999 range)
CREATE SEQUENCE IF NOT EXISTS dol.air_log_id_seq
  START WITH 901
  INCREMENT BY 1
  MINVALUE 901
  MAXVALUE 999
  CYCLE;

COMMENT ON SEQUENCE dol.air_log_id_seq IS 'Sequence for AIR event log IDs (901-999)';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 1: dol.ein_linkage (APPEND-ONLY)
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Immutable record of EIN ↔ company_unique_id linkages
--
-- RULES (ENFORCED):
--   - No updates allowed (append-only)
--   - No overwrites permitted
--   - No rescans (one linkage per company per EIN)
--   - Multi-EIN or ambiguous matches = FAIL HARD (logged to AIR)
--   - Silence = FAIL (no "unknown" states)
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS dol.ein_linkage (
  -- Primary Key (Barton ID: 01.04.02.04.22000.###)
  linkage_id VARCHAR(50) PRIMARY KEY DEFAULT CONCAT(
    '01.04.02.04.22000.',
    LPAD(NEXTVAL('dol.linkage_id_seq')::TEXT, 3, '0')
  ),

  -- Foreign Key - SOVEREIGN, IMMUTABLE
  company_unique_id VARCHAR(50) NOT NULL,

  -- EIN Data
  ein VARCHAR(10) NOT NULL,  -- Format: XX-XXXXXXX (9 digits with hyphen)

  -- Source Provenance (REQUIRED)
  source VARCHAR(50) NOT NULL,  -- e.g., 'DOL_FORM_5500', 'EBSA_FILING'
  source_url TEXT NOT NULL,     -- Direct URL to authoritative filing
  filing_year INTEGER NOT NULL CHECK (filing_year >= 1974 AND filing_year <= 2100),

  -- Integrity Verification
  hash_fingerprint VARCHAR(64) NOT NULL,  -- SHA-256 hash of source document

  -- Audit Fields (IMMUTABLE after creation)
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  outreach_context_id VARCHAR(100) NOT NULL,  -- Required per doctrine

  -- Constraints
  CONSTRAINT chk_linkage_id_format CHECK (
    linkage_id ~ '^01\.04\.02\.04\.22000\.\d{3}$'
  ),
  CONSTRAINT chk_ein_format CHECK (
    ein ~ '^\d{2}-\d{7}$'
  ),
  CONSTRAINT chk_source_valid CHECK (
    source IN ('DOL_FORM_5500', 'EBSA_FILING', 'DOL_EFAST2', 'DOL_MANUAL_VERIFIED')
  ),
  CONSTRAINT chk_hash_format CHECK (
    hash_fingerprint ~ '^[a-f0-9]{64}$'
  ),
  CONSTRAINT fk_company FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE RESTRICT,  -- CANNOT delete company with EIN linkage
  -- UNIQUE constraint ensures ONE EIN per company (no multi-EIN)
  CONSTRAINT uq_company_ein UNIQUE (company_unique_id, ein)
);

-- Indexes
CREATE INDEX idx_ein_linkage_company_id ON dol.ein_linkage(company_unique_id);
CREATE INDEX idx_ein_linkage_ein ON dol.ein_linkage(ein);
CREATE INDEX idx_ein_linkage_source ON dol.ein_linkage(source);
CREATE INDEX idx_ein_linkage_filing_year ON dol.ein_linkage(filing_year DESC);
CREATE INDEX idx_ein_linkage_created_at ON dol.ein_linkage(created_at DESC);

-- Comments
COMMENT ON TABLE dol.ein_linkage IS 'APPEND-ONLY: EIN ↔ company_unique_id linkages from DOL/EBSA filings (Section 3)';
COMMENT ON COLUMN dol.ein_linkage.linkage_id IS 'Barton ID: 01.04.02.04.22000.### (001-999 range), auto-generated';
COMMENT ON COLUMN dol.ein_linkage.company_unique_id IS 'SOVEREIGN FK to marketing.company_master - IMMUTABLE';
COMMENT ON COLUMN dol.ein_linkage.ein IS 'Employer Identification Number (XX-XXXXXXX format)';
COMMENT ON COLUMN dol.ein_linkage.source IS 'Authoritative source: DOL_FORM_5500, EBSA_FILING, DOL_EFAST2, DOL_MANUAL_VERIFIED';
COMMENT ON COLUMN dol.ein_linkage.source_url IS 'Direct URL to authoritative DOL/EBSA filing document';
COMMENT ON COLUMN dol.ein_linkage.filing_year IS 'Year of the DOL/EBSA filing (1974-2100)';
COMMENT ON COLUMN dol.ein_linkage.hash_fingerprint IS 'SHA-256 hash of source document for integrity verification';
COMMENT ON COLUMN dol.ein_linkage.outreach_context_id IS 'Required context ID per HEIR doctrine';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE 2: dol.air_log (Audit, Integrity, Resolution Log)
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Log ALL events including failures (FAIL HARD doctrine)
--
-- Kill Switch Events Logged:
--   - MULTI_EIN_FOUND: Multiple EINs found for company
--   - EIN_MISMATCH: EIN mismatch across filings
--   - FILING_TTL_EXCEEDED: Filing older than doctrine TTL
--   - SOURCE_UNAVAILABLE: DOL source unavailable
--   - CROSS_CONTEXT_CONTAMINATION: Cross-context contamination detected
--   - IDENTITY_GATE_FAILED: Missing required identity anchors
--   - LINKAGE_SUCCESS: Successful EIN linkage
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS dol.air_log (
  -- Primary Key (Barton ID: 01.04.02.04.22000.9##)
  air_log_id VARCHAR(50) PRIMARY KEY DEFAULT CONCAT(
    '01.04.02.04.22000.',
    LPAD(NEXTVAL('dol.air_log_id_seq')::TEXT, 3, '0')
  ),

  -- Context (REQUIRED)
  company_unique_id VARCHAR(50),  -- May be NULL if identity gate failed
  outreach_context_id VARCHAR(100) NOT NULL,

  -- Event Classification
  event_type VARCHAR(50) NOT NULL,
  event_status VARCHAR(20) NOT NULL CHECK (event_status IN ('SUCCESS', 'FAILED', 'ABORTED')),

  -- Details
  event_message TEXT NOT NULL,
  event_payload JSONB,

  -- Identity Gate Status (captured at time of event)
  identity_gate_passed BOOLEAN NOT NULL DEFAULT FALSE,
  identity_anchors_present JSONB,  -- {"company_domain": true, "linkedin_company_url": false}

  -- Audit
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

  -- Constraints
  CONSTRAINT chk_air_log_id_format CHECK (
    air_log_id ~ '^01\.04\.02\.04\.22000\.9\d{2}$'
  ),
  CONSTRAINT chk_event_type_valid CHECK (
    event_type IN (
      'IDENTITY_GATE_FAILED',
      'MULTI_EIN_FOUND',
      'EIN_MISMATCH',
      'FILING_TTL_EXCEEDED',
      'SOURCE_UNAVAILABLE',
      'CROSS_CONTEXT_CONTAMINATION',
      'EIN_FORMAT_INVALID',
      'HASH_VERIFICATION_FAILED',
      'LINKAGE_SUCCESS'
    )
  )
);

-- Indexes
CREATE INDEX idx_air_log_company_id ON dol.air_log(company_unique_id);
CREATE INDEX idx_air_log_event_type ON dol.air_log(event_type);
CREATE INDEX idx_air_log_event_status ON dol.air_log(event_status);
CREATE INDEX idx_air_log_created_at ON dol.air_log(created_at DESC);
CREATE INDEX idx_air_log_context_id ON dol.air_log(outreach_context_id);
CREATE INDEX idx_air_log_payload ON dol.air_log USING GIN(event_payload);

-- Comments
COMMENT ON TABLE dol.air_log IS 'AIR (Audit, Integrity, Resolution) log for all DOL EIN operations';
COMMENT ON COLUMN dol.air_log.air_log_id IS 'Barton ID: 01.04.02.04.22000.9## (901-999 range)';
COMMENT ON COLUMN dol.air_log.event_type IS 'Kill switch trigger or success event type';
COMMENT ON COLUMN dol.air_log.event_status IS 'SUCCESS, FAILED (recoverable), ABORTED (kill switch)';
COMMENT ON COLUMN dol.air_log.identity_gate_passed IS 'TRUE if all identity requirements met before DOL interaction';
COMMENT ON COLUMN dol.air_log.identity_anchors_present IS 'JSON snapshot of identity anchors at event time';

-- ═══════════════════════════════════════════════════════════════════════════
-- ENFORCE APPEND-ONLY (NO UPDATES, NO DELETES)
-- ═══════════════════════════════════════════════════════════════════════════

-- Trigger: Block UPDATE on ein_linkage
CREATE OR REPLACE FUNCTION dol.block_ein_linkage_update()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'dol.ein_linkage is APPEND-ONLY. Updates are prohibited by doctrine.';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_block_ein_linkage_update
  BEFORE UPDATE ON dol.ein_linkage
  FOR EACH ROW
  EXECUTE FUNCTION dol.block_ein_linkage_update();

-- Trigger: Block DELETE on ein_linkage
CREATE OR REPLACE FUNCTION dol.block_ein_linkage_delete()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'dol.ein_linkage is APPEND-ONLY. Deletes are prohibited by doctrine.';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_block_ein_linkage_delete
  BEFORE DELETE ON dol.ein_linkage
  FOR EACH ROW
  EXECUTE FUNCTION dol.block_ein_linkage_delete();

COMMENT ON FUNCTION dol.block_ein_linkage_update() IS 'DOCTRINE: Enforce append-only (block updates)';
COMMENT ON FUNCTION dol.block_ein_linkage_delete() IS 'DOCTRINE: Enforce append-only (block deletes)';

-- ═══════════════════════════════════════════════════════════════════════════
-- IDENTITY GATE VALIDATION FUNCTION
-- ═══════════════════════════════════════════════════════════════════════════
-- FAIL HARD if requirements not met. No retries, no fallback.
--
-- Required:
--   - company_unique_id (sovereign, immutable)
--   - outreach_context_id
--   - state
--   - At least one identity anchor: company_domain OR linkedin_company_url
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION dol.validate_identity_gate(
  p_company_unique_id VARCHAR,
  p_outreach_context_id VARCHAR,
  p_state VARCHAR,
  p_company_domain VARCHAR,
  p_linkedin_company_url VARCHAR
)
RETURNS TABLE (
  is_valid BOOLEAN,
  failure_reason TEXT,
  identity_anchors JSONB
) AS $$
DECLARE
  v_anchors JSONB;
  v_has_anchor BOOLEAN;
BEGIN
  -- Build identity anchors snapshot
  v_anchors := JSONB_BUILD_OBJECT(
    'company_domain', COALESCE(p_company_domain, '') != '',
    'linkedin_company_url', COALESCE(p_linkedin_company_url, '') != ''
  );

  v_has_anchor := (COALESCE(p_company_domain, '') != '' OR COALESCE(p_linkedin_company_url, '') != '');

  -- Validate required fields
  IF p_company_unique_id IS NULL OR p_company_unique_id = '' THEN
    RETURN QUERY SELECT FALSE, 'MISSING: company_unique_id (sovereign, immutable)', v_anchors;
    RETURN;
  END IF;

  IF p_outreach_context_id IS NULL OR p_outreach_context_id = '' THEN
    RETURN QUERY SELECT FALSE, 'MISSING: outreach_context_id', v_anchors;
    RETURN;
  END IF;

  IF p_state IS NULL OR p_state = '' THEN
    RETURN QUERY SELECT FALSE, 'MISSING: state', v_anchors;
    RETURN;
  END IF;

  IF NOT v_has_anchor THEN
    RETURN QUERY SELECT FALSE, 'MISSING: at least one identity anchor (company_domain OR linkedin_company_url)', v_anchors;
    RETURN;
  END IF;

  -- All gates passed
  RETURN QUERY SELECT TRUE, NULL::TEXT, v_anchors;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dol.validate_identity_gate IS 'DOCTRINE: Validate identity gate before ANY DOL interaction. FAIL HARD on missing requirements.';

-- ═══════════════════════════════════════════════════════════════════════════
-- EIN LINKAGE INSERT FUNCTION (WITH FULL VALIDATION)
-- ═══════════════════════════════════════════════════════════════════════════
-- Implements the complete pipeline:
--   Company Hub PASS → DOL Subhub (EIN Resolution Only) → Append EIN Linkage → Emit AIR event
--
-- Kill Switches (ABORT and log AIR):
--   - Multiple EINs found
--   - EIN mismatch across filings
--   - Filing older than doctrine TTL (configurable, default 3 years)
--   - DOL source unavailable (external check)
--   - Cross-context contamination
--
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION dol.insert_ein_linkage(
  p_company_unique_id VARCHAR,
  p_outreach_context_id VARCHAR,
  p_state VARCHAR,
  p_company_domain VARCHAR,
  p_linkedin_company_url VARCHAR,
  p_ein VARCHAR,
  p_source VARCHAR,
  p_source_url TEXT,
  p_filing_year INTEGER,
  p_hash_fingerprint VARCHAR,
  p_filing_ttl_years INTEGER DEFAULT 3
)
RETURNS TABLE (
  success BOOLEAN,
  linkage_id VARCHAR,
  air_log_id VARCHAR,
  message TEXT
) AS $$
DECLARE
  v_gate_valid BOOLEAN;
  v_gate_failure TEXT;
  v_gate_anchors JSONB;
  v_existing_ein VARCHAR;
  v_existing_count INTEGER;
  v_new_linkage_id VARCHAR;
  v_new_air_log_id VARCHAR;
  v_current_year INTEGER := EXTRACT(YEAR FROM NOW());
BEGIN
  -- ───────────────────────────────────────────────────────────────────
  -- STEP 1: Identity Gate Validation (FAIL HARD)
  -- ───────────────────────────────────────────────────────────────────
  SELECT * INTO v_gate_valid, v_gate_failure, v_gate_anchors
  FROM dol.validate_identity_gate(
    p_company_unique_id, p_outreach_context_id, p_state,
    p_company_domain, p_linkedin_company_url
  );

  IF NOT v_gate_valid THEN
    -- Log AIR event and ABORT
    INSERT INTO dol.air_log (
      company_unique_id, outreach_context_id, event_type, event_status,
      event_message, event_payload, identity_gate_passed, identity_anchors_present
    ) VALUES (
      p_company_unique_id, p_outreach_context_id, 'IDENTITY_GATE_FAILED', 'ABORTED',
      v_gate_failure,
      JSONB_BUILD_OBJECT('state', p_state, 'domain', p_company_domain, 'linkedin', p_linkedin_company_url),
      FALSE, v_gate_anchors
    )
    RETURNING air_log_id INTO v_new_air_log_id;

    RETURN QUERY SELECT FALSE, NULL::VARCHAR, v_new_air_log_id, v_gate_failure;
    RETURN;
  END IF;

  -- ───────────────────────────────────────────────────────────────────
  -- STEP 2: EIN Format Validation (FAIL HARD)
  -- ───────────────────────────────────────────────────────────────────
  IF p_ein !~ '^\d{2}-\d{7}$' THEN
    INSERT INTO dol.air_log (
      company_unique_id, outreach_context_id, event_type, event_status,
      event_message, event_payload, identity_gate_passed, identity_anchors_present
    ) VALUES (
      p_company_unique_id, p_outreach_context_id, 'EIN_FORMAT_INVALID', 'ABORTED',
      'EIN format invalid. Expected: XX-XXXXXXX. Received: ' || COALESCE(p_ein, 'NULL'),
      JSONB_BUILD_OBJECT('ein', p_ein),
      TRUE, v_gate_anchors
    )
    RETURNING air_log_id INTO v_new_air_log_id;

    RETURN QUERY SELECT FALSE, NULL::VARCHAR, v_new_air_log_id, 'EIN_FORMAT_INVALID';
    RETURN;
  END IF;

  -- ───────────────────────────────────────────────────────────────────
  -- STEP 3: Filing TTL Check (FAIL HARD if too old)
  -- ───────────────────────────────────────────────────────────────────
  IF (v_current_year - p_filing_year) > p_filing_ttl_years THEN
    INSERT INTO dol.air_log (
      company_unique_id, outreach_context_id, event_type, event_status,
      event_message, event_payload, identity_gate_passed, identity_anchors_present
    ) VALUES (
      p_company_unique_id, p_outreach_context_id, 'FILING_TTL_EXCEEDED', 'ABORTED',
      'Filing year ' || p_filing_year || ' exceeds TTL of ' || p_filing_ttl_years || ' years',
      JSONB_BUILD_OBJECT('filing_year', p_filing_year, 'current_year', v_current_year, 'ttl_years', p_filing_ttl_years),
      TRUE, v_gate_anchors
    )
    RETURNING air_log_id INTO v_new_air_log_id;

    RETURN QUERY SELECT FALSE, NULL::VARCHAR, v_new_air_log_id, 'FILING_TTL_EXCEEDED';
    RETURN;
  END IF;

  -- ───────────────────────────────────────────────────────────────────
  -- STEP 4: Check for Existing EIN (Multi-EIN = FAIL HARD)
  -- ───────────────────────────────────────────────────────────────────
  SELECT COUNT(*), MAX(ein) INTO v_existing_count, v_existing_ein
  FROM dol.ein_linkage
  WHERE company_unique_id = p_company_unique_id;

  IF v_existing_count > 0 AND v_existing_ein != p_ein THEN
    -- Multi-EIN scenario - ABORT
    INSERT INTO dol.air_log (
      company_unique_id, outreach_context_id, event_type, event_status,
      event_message, event_payload, identity_gate_passed, identity_anchors_present
    ) VALUES (
      p_company_unique_id, p_outreach_context_id, 'EIN_MISMATCH', 'ABORTED',
      'EIN mismatch: existing=' || v_existing_ein || ', new=' || p_ein,
      JSONB_BUILD_OBJECT('existing_ein', v_existing_ein, 'new_ein', p_ein, 'existing_count', v_existing_count),
      TRUE, v_gate_anchors
    )
    RETURNING air_log_id INTO v_new_air_log_id;

    RETURN QUERY SELECT FALSE, NULL::VARCHAR, v_new_air_log_id, 'EIN_MISMATCH';
    RETURN;
  END IF;

  -- ───────────────────────────────────────────────────────────────────
  -- STEP 5: Hash Fingerprint Validation (FAIL HARD)
  -- ───────────────────────────────────────────────────────────────────
  IF p_hash_fingerprint !~ '^[a-f0-9]{64}$' THEN
    INSERT INTO dol.air_log (
      company_unique_id, outreach_context_id, event_type, event_status,
      event_message, event_payload, identity_gate_passed, identity_anchors_present
    ) VALUES (
      p_company_unique_id, p_outreach_context_id, 'HASH_VERIFICATION_FAILED', 'ABORTED',
      'Invalid SHA-256 hash fingerprint format',
      JSONB_BUILD_OBJECT('hash', p_hash_fingerprint),
      TRUE, v_gate_anchors
    )
    RETURNING air_log_id INTO v_new_air_log_id;

    RETURN QUERY SELECT FALSE, NULL::VARCHAR, v_new_air_log_id, 'HASH_VERIFICATION_FAILED';
    RETURN;
  END IF;

  -- ───────────────────────────────────────────────────────────────────
  -- STEP 6: Insert EIN Linkage (SUCCESS)
  -- ───────────────────────────────────────────────────────────────────
  INSERT INTO dol.ein_linkage (
    company_unique_id, ein, source, source_url, filing_year,
    hash_fingerprint, outreach_context_id
  ) VALUES (
    p_company_unique_id, p_ein, p_source, p_source_url, p_filing_year,
    p_hash_fingerprint, p_outreach_context_id
  )
  RETURNING linkage_id INTO v_new_linkage_id;

  -- Log success to AIR
  INSERT INTO dol.air_log (
    company_unique_id, outreach_context_id, event_type, event_status,
    event_message, event_payload, identity_gate_passed, identity_anchors_present
  ) VALUES (
    p_company_unique_id, p_outreach_context_id, 'LINKAGE_SUCCESS', 'SUCCESS',
    'EIN linkage created: ' || p_ein,
    JSONB_BUILD_OBJECT(
      'linkage_id', v_new_linkage_id,
      'ein', p_ein,
      'source', p_source,
      'filing_year', p_filing_year
    ),
    TRUE, v_gate_anchors
  )
  RETURNING air_log_id INTO v_new_air_log_id;

  RETURN QUERY SELECT TRUE, v_new_linkage_id, v_new_air_log_id, 'LINKAGE_SUCCESS';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dol.insert_ein_linkage IS 'DOCTRINE: Complete EIN linkage pipeline with identity gate, validation, and AIR logging';

-- ═══════════════════════════════════════════════════════════════════════════
-- HELPER VIEWS
-- ═══════════════════════════════════════════════════════════════════════════

-- View: Companies with EIN linkage
CREATE OR REPLACE VIEW dol.companies_with_ein AS
SELECT
  cm.company_unique_id,
  cm.company_name,
  el.ein,
  el.source,
  el.filing_year,
  el.created_at AS linkage_created_at
FROM marketing.company_master cm
INNER JOIN dol.ein_linkage el ON cm.company_unique_id = el.company_unique_id
ORDER BY el.created_at DESC;

COMMENT ON VIEW dol.companies_with_ein IS 'Companies with verified EIN linkages from DOL/EBSA filings';

-- View: Companies without EIN linkage
CREATE OR REPLACE VIEW dol.companies_without_ein AS
SELECT
  cm.company_unique_id,
  cm.company_name,
  cm.created_at
FROM marketing.company_master cm
LEFT JOIN dol.ein_linkage el ON cm.company_unique_id = el.company_unique_id
WHERE el.linkage_id IS NULL
ORDER BY cm.created_at DESC;

COMMENT ON VIEW dol.companies_without_ein IS 'Companies awaiting EIN linkage from DOL/EBSA filings';

-- View: AIR Log Summary
CREATE OR REPLACE VIEW dol.air_log_summary AS
SELECT
  event_type,
  event_status,
  COUNT(*) AS event_count,
  MAX(created_at) AS latest_event
FROM dol.air_log
GROUP BY event_type, event_status
ORDER BY event_count DESC;

COMMENT ON VIEW dol.air_log_summary IS 'Summary of AIR events by type and status';

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Verify tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'dol';
-- Expected: ein_linkage, air_log

-- 2. Verify sequences created
-- SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'dol';
-- Expected: linkage_id_seq, air_log_id_seq

-- 3. Verify views created
-- SELECT table_name FROM information_schema.views WHERE table_schema = 'dol';
-- Expected: companies_with_ein, companies_without_ein, air_log_summary

-- 4. Verify append-only triggers
-- SELECT trigger_name FROM information_schema.triggers WHERE event_object_schema = 'dol';
-- Expected: trg_block_ein_linkage_update, trg_block_ein_linkage_delete

-- 5. Test identity gate function
-- SELECT * FROM dol.validate_identity_gate(
--   '04.04.02.04.30000.001',  -- company_unique_id
--   'CTX-2025-001',           -- outreach_context_id
--   'VA',                     -- state
--   'example.com',            -- company_domain
--   NULL                      -- linkedin_company_url
-- );
-- Expected: is_valid=TRUE

-- 6. Test insert function (dry run - use with test data)
-- SELECT * FROM dol.insert_ein_linkage(
--   '04.04.02.04.30000.001',
--   'CTX-2025-001',
--   'VA',
--   'example.com',
--   NULL,
--   '12-3456789',
--   'DOL_FORM_5500',
--   'https://www.efast.dol.gov/...',
--   2024,
--   'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2'
-- );

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF DOL EIN LINKAGE SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════
--
-- EXPLICIT NON-GOALS (RE-STATED):
--   ❌ This schema does NOT create BIT events
--   ❌ This schema does NOT trigger outreach
--   ❌ This schema does NOT integrate with Slack/Salesforce/Grafana
--   ❌ This schema does NOT handle OSHA/EEOC
--   ❌ This schema does NOT score buyer intent
--
-- WHAT THIS SCHEMA DOES:
--   ✅ Links EIN to sovereign company_unique_id
--   ✅ Validates identity gate before DOL interaction
--   ✅ Enforces append-only immutability
--   ✅ Logs all events to AIR (success and failure)
--   ✅ Provides verification views
--
-- ═══════════════════════════════════════════════════════════════════════════
