-- ═══════════════════════════════════════════════════════════════════════════
-- Schema: DOL Violations (Fact Storage)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
-- Barton ID Prefix: 01.04.02.04.22000.5##
--
-- PURPOSE:
--   Store DOL violation facts linked to EIN-resolved companies.
--   This is FACT STORAGE ONLY — no scoring, no outreach triggers.
--
-- SOURCES:
--   - OSHA (Occupational Safety and Health Administration)
--   - EBSA (Employee Benefits Security Administration)
--   - WHD (Wage and Hour Division)
--   - OFCCP (Office of Federal Contract Compliance Programs)
--
-- ARCHITECTURE:
--   Company Target (EIN resolved) → DOL EIN Linkage → DOL Violations
--   Violations link TO existing EIN records, not the other way around.
--
-- DOWNSTREAM CONSUMERS:
--   - Outreach systems (read violation facts for messaging)
--   - Analytics (aggregate violation patterns)
--   - Compliance monitoring (track remediation)
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Create DOL schema if not exists
CREATE SCHEMA IF NOT EXISTS dol;

-- ═══════════════════════════════════════════════════════════════════════════
-- SEQUENCE: Violation IDs
-- ═══════════════════════════════════════════════════════════════════════════

CREATE SEQUENCE IF NOT EXISTS dol.violation_id_seq
  START WITH 1
  INCREMENT BY 1
  MINVALUE 1
  MAXVALUE 999999
  CYCLE;

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: dol.violations (APPEND-ONLY)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Stores individual DOL violations as facts.
-- Links to dol.ein_linkage via EIN (company must have resolved EIN).
--

CREATE TABLE IF NOT EXISTS dol.violations (
  -- Primary Key (Barton ID format: 01.04.02.04.22000.5XXXXX)
  violation_id VARCHAR(50) PRIMARY KEY DEFAULT CONCAT(
    '01.04.02.04.22000.5',
    LPAD(NEXTVAL('dol.violation_id_seq')::TEXT, 5, '0')
  ),
  
  -- Link to EIN (REQUIRED - company must have resolved EIN)
  ein VARCHAR(10) NOT NULL,
  
  -- Company reference (for convenience, but EIN is authoritative)
  company_unique_id VARCHAR(50),
  
  -- Violation source/agency
  source_agency VARCHAR(20) NOT NULL,
  
  -- Violation details
  case_number VARCHAR(50),
  violation_type VARCHAR(100) NOT NULL,
  violation_date DATE,
  discovery_date DATE NOT NULL DEFAULT CURRENT_DATE,
  
  -- Location (violations are often site-specific)
  site_name VARCHAR(255),
  site_address TEXT,
  site_city VARCHAR(100),
  site_state VARCHAR(2),
  site_zip VARCHAR(10),
  
  -- Severity and status
  severity VARCHAR(20),
  penalty_initial DECIMAL(12,2),
  penalty_current DECIMAL(12,2),
  penalty_paid DECIMAL(12,2),
  status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
  
  -- Citation details
  citation_id VARCHAR(100),
  citation_url TEXT,
  
  -- Narrative (raw from DOL)
  violation_description TEXT,
  
  -- Source tracking
  source_url TEXT NOT NULL,
  source_record_id VARCHAR(100),
  hash_fingerprint VARCHAR(64) NOT NULL,
  
  -- Audit
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  outreach_context_id VARCHAR(100),
  
  -- Constraints
  CONSTRAINT chk_ein_format CHECK (ein ~ '^\d{2}-\d{7}$'),
  CONSTRAINT chk_violation_id_format CHECK (violation_id ~ '^01\.04\.02\.04\.22000\.5\d{5}$'),
  CONSTRAINT chk_source_agency CHECK (source_agency IN ('OSHA', 'EBSA', 'WHD', 'OFCCP', 'MSHA', 'OTHER')),
  CONSTRAINT chk_severity CHECK (severity IS NULL OR severity IN ('WILLFUL', 'SERIOUS', 'OTHER_THAN_SERIOUS', 'REPEAT', 'FAILURE_TO_ABATE', 'UNCLASSIFIED')),
  CONSTRAINT chk_status CHECK (status IN ('OPEN', 'CONTESTED', 'SETTLED', 'PAID', 'ABATED', 'DELETED', 'UNKNOWN'))
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════

-- Primary lookup: Find violations by EIN
CREATE INDEX IF NOT EXISTS idx_dol_violations_ein 
  ON dol.violations (ein);

-- Find violations by company
CREATE INDEX IF NOT EXISTS idx_dol_violations_company 
  ON dol.violations (company_unique_id);

-- Find violations by agency
CREATE INDEX IF NOT EXISTS idx_dol_violations_agency 
  ON dol.violations (source_agency, violation_date DESC);

-- Find recent violations
CREATE INDEX IF NOT EXISTS idx_dol_violations_recent 
  ON dol.violations (discovery_date DESC);

-- Find open violations
CREATE INDEX IF NOT EXISTS idx_dol_violations_open 
  ON dol.violations (status, discovery_date DESC)
  WHERE status = 'OPEN';

-- Find by case number
CREATE INDEX IF NOT EXISTS idx_dol_violations_case 
  ON dol.violations (case_number);

-- Prevent duplicate violations
CREATE UNIQUE INDEX IF NOT EXISTS idx_dol_violations_unique 
  ON dol.violations (ein, source_agency, COALESCE(case_number, citation_id, source_record_id));

-- Find violations by outreach context (for targeting)
CREATE INDEX IF NOT EXISTS idx_dol_violations_outreach_context 
  ON dol.violations (outreach_context_id)
  WHERE outreach_context_id IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- APPEND-ONLY TRIGGERS
-- ═══════════════════════════════════════════════════════════════════════════

-- Prevent updates (append-only)
CREATE OR REPLACE FUNCTION dol.prevent_violation_updates()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    -- Allow status updates only
    IF (OLD.ein = NEW.ein 
        AND OLD.source_agency = NEW.source_agency 
        AND OLD.case_number IS NOT DISTINCT FROM NEW.case_number
        AND OLD.violation_type = NEW.violation_type) THEN
      -- Only allow: status, penalty_current, penalty_paid updates
      IF (OLD.ein != NEW.ein 
          OR OLD.violation_type != NEW.violation_type
          OR OLD.source_url != NEW.source_url) THEN
        RAISE EXCEPTION 'Core violation fields cannot be updated. This is an append-only table.';
      END IF;
      RETURN NEW;
    END IF;
    RAISE EXCEPTION 'Updates are not allowed on dol.violations table. This is an append-only table.';
  ELSIF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Deletes are not allowed on dol.violations table. This is an append-only table.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dol_violations_prevent_modifications
BEFORE UPDATE OR DELETE ON dol.violations
FOR EACH ROW
EXECUTE FUNCTION dol.prevent_violation_updates();

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: dol.violation_categories (Reference)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Standard violation categories for classification
--

CREATE TABLE IF NOT EXISTS dol.violation_categories (
  category_code VARCHAR(20) PRIMARY KEY,
  category_name VARCHAR(100) NOT NULL,
  agency VARCHAR(20) NOT NULL,
  description TEXT,
  outreach_relevant BOOLEAN DEFAULT TRUE
);

-- Seed OSHA categories
INSERT INTO dol.violation_categories (category_code, category_name, agency, description, outreach_relevant)
VALUES
  ('OSHA_WILLFUL', 'Willful Violation', 'OSHA', 'Employer intentionally and knowingly committed violation', TRUE),
  ('OSHA_SERIOUS', 'Serious Violation', 'OSHA', 'Substantial probability of death or serious physical harm', TRUE),
  ('OSHA_OTHER', 'Other-Than-Serious', 'OSHA', 'Direct relationship to job safety but probably not death/serious harm', TRUE),
  ('OSHA_REPEAT', 'Repeat Violation', 'OSHA', 'Same or substantially similar violation within 5 years', TRUE),
  ('OSHA_FTA', 'Failure to Abate', 'OSHA', 'Failure to correct prior violation', TRUE),
  ('EBSA_401K', '401(k) Violation', 'EBSA', 'ERISA violation related to 401(k) plan', TRUE),
  ('EBSA_HEALTH', 'Health Plan Violation', 'EBSA', 'ERISA violation related to health benefits', TRUE),
  ('EBSA_FIDUCIARY', 'Fiduciary Violation', 'EBSA', 'Breach of fiduciary duty under ERISA', TRUE),
  ('WHD_FLSA', 'FLSA Violation', 'WHD', 'Fair Labor Standards Act violation', TRUE),
  ('WHD_FMLA', 'FMLA Violation', 'WHD', 'Family and Medical Leave Act violation', TRUE)
ON CONFLICT (category_code) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Companies with Violations (Outreach Ready)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Join violations with EIN linkage for outreach targeting
-- Linkage Chain: Violation → EIN → Outreach Context → Sovereign ID
--

CREATE OR REPLACE VIEW dol.v_companies_with_violations AS
SELECT
  el.company_unique_id,          -- Sovereign ID (from CL via ein_linkage)
  v.outreach_context_id,         -- Outreach Context (targeting context)
  el.ein,
  v.violation_id,
  v.source_agency,
  v.violation_type,
  v.violation_date,
  v.discovery_date,
  v.severity,
  v.penalty_initial,
  v.penalty_current,
  v.status,
  v.site_state,
  v.citation_url,
  v.violation_description,
  el.source AS ein_source,
  el.filing_year AS ein_filing_year
FROM dol.ein_linkage el
JOIN dol.violations v ON el.ein = v.ein
WHERE v.status IN ('OPEN', 'CONTESTED')
ORDER BY v.discovery_date DESC;

COMMENT ON VIEW dol.v_companies_with_violations IS 
'Companies with EIN linkage that have open/contested DOL violations. Use for outreach targeting.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Violation Summary by Company
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW dol.v_violation_summary AS
SELECT
  el.company_unique_id,
  el.ein,
  COUNT(DISTINCT v.violation_id) AS total_violations,
  COUNT(DISTINCT v.violation_id) FILTER (WHERE v.status = 'OPEN') AS open_violations,
  COUNT(DISTINCT v.source_agency) AS agencies_with_violations,
  SUM(v.penalty_initial) AS total_initial_penalties,
  SUM(v.penalty_current) AS total_current_penalties,
  MIN(v.violation_date) AS earliest_violation,
  MAX(v.violation_date) AS latest_violation,
  MAX(v.discovery_date) AS last_discovery_date,
  ARRAY_AGG(DISTINCT v.source_agency) AS violation_agencies,
  ARRAY_AGG(DISTINCT v.severity) FILTER (WHERE v.severity IS NOT NULL) AS severity_levels
FROM dol.ein_linkage el
JOIN dol.violations v ON el.ein = v.ein
GROUP BY el.company_unique_id, el.ein;

COMMENT ON VIEW dol.v_violation_summary IS 
'Aggregate violation statistics by company. Shows total violations, open count, penalties, and agencies.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Recent Violations (Last 90 Days)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW dol.v_recent_violations AS
SELECT
  v.*,
  el.company_unique_id,
  CURRENT_DATE - v.discovery_date AS days_since_discovery
FROM dol.violations v
LEFT JOIN dol.ein_linkage el ON v.ein = el.ein
WHERE v.discovery_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY v.discovery_date DESC;

COMMENT ON VIEW dol.v_recent_violations IS 
'Violations discovered in the last 90 days. Prioritize for outreach.';

-- ═══════════════════════════════════════════════════════════════════════════
-- AIR EVENT TYPES FOR VIOLATIONS
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Add violation-specific AIR events (insert into existing air_log table)
--
-- Event Types:
--   VIOLATION_DISCOVERED - New violation found
--   VIOLATION_EIN_MATCHED - Violation matched to existing EIN
--   VIOLATION_EIN_NOT_FOUND - Violation found but no EIN linkage exists
--   VIOLATION_DUPLICATE - Duplicate violation detected (skipped)
--

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANTS (Adjust for your environment)
-- ═══════════════════════════════════════════════════════════════════════════

-- GRANT SELECT ON dol.violations TO outreach_service;
-- GRANT SELECT ON dol.v_companies_with_violations TO outreach_service;
-- GRANT SELECT ON dol.v_violation_summary TO outreach_service;
-- GRANT SELECT ON dol.v_recent_violations TO outreach_service;
-- GRANT INSERT ON dol.violations TO dol_scraper_service;
