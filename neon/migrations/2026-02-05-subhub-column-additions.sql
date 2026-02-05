-- ==============================================================================
-- SUB-HUB COLUMN ADDITIONS
-- ==============================================================================
-- Date: 2026-02-05
-- Purpose: Add columns to sub-hubs for clean Hunter data mapping
--
-- DOCTRINE: Each sub-hub OWNS specific data. Every Hunter column goes to exactly ONE place.
--
-- CT (04.04.01) - Company-level targeting intelligence
-- PEOPLE (04.04.02) - Person-level contact data
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- COMPANY TARGET (CT) - Add company-level columns from hunter_company
-- ==============================================================================

-- Industry classification
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS industry VARCHAR(255);

COMMENT ON COLUMN outreach.company_target.industry IS
'CT.IND | Industry classification from Hunter. Format: Hunter taxonomy. Example: Construction';

-- Employee count (exact number from 5500 or other authoritative source)
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS employees INTEGER;

COMMENT ON COLUMN outreach.company_target.employees IS
'CT.EMP | Exact employee count from Form 5500 or authoritative source. Format: positive integer. Example: 251';

-- Country
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS country VARCHAR(10);

COMMENT ON COLUMN outreach.company_target.country IS
'CT.COUNTRY | ISO 3166-1 alpha-2 country code. Format: 2 letters. Example: US';

-- State
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS state VARCHAR(50);

COMMENT ON COLUMN outreach.company_target.state IS
'CT.STATE | State/province/region. Format: abbreviation or full name. Example: PA';

-- City
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS city VARCHAR(100);

COMMENT ON COLUMN outreach.company_target.city IS
'CT.CITY | City name. Format: title case. Example: Pittsburgh';

-- Postal code
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20);

COMMENT ON COLUMN outreach.company_target.postal_code IS
'CT.POSTAL | ZIP or postal code. Format: varies by country. Example: 15213';

-- Data year (year this data reflects, e.g., Form 5500 filing year)
ALTER TABLE outreach.company_target
ADD COLUMN IF NOT EXISTS data_year INTEGER;

COMMENT ON COLUMN outreach.company_target.data_year IS
'CT.YEAR | Year this data reflects (e.g., Form 5500 filing year). Format: YYYY. Example: 2024';

-- Add indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_company_target_industry ON outreach.company_target(industry);
CREATE INDEX IF NOT EXISTS idx_company_target_state ON outreach.company_target(state);
CREATE INDEX IF NOT EXISTS idx_company_target_employees ON outreach.company_target(employees);

-- ==============================================================================
-- PEOPLE MASTER - Add person-level columns from hunter_contact
-- ==============================================================================

-- Is decision maker flag
ALTER TABLE people.people_master
ADD COLUMN IF NOT EXISTS is_decision_maker BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN people.people_master.is_decision_maker IS
'PM.IS_DM | Whether this contact is a decision maker. Format: true/false. Example: true';

-- Add index for decision maker queries
CREATE INDEX IF NOT EXISTS idx_people_master_decision_maker ON people.people_master(is_decision_maker) WHERE is_decision_maker = TRUE;

COMMIT;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

-- Verify CT columns added
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_schema = 'outreach' AND table_name = 'company_target'
-- AND column_name IN ('industry', 'employees', 'country', 'state', 'city', 'postal_code', 'data_year');

-- Verify PEOPLE column added
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_schema = 'people' AND table_name = 'people_master'
-- AND column_name = 'is_decision_maker';

-- ==============================================================================
-- SUMMARY
-- ==============================================================================
--
-- CT columns added (7):
--   - industry (varchar 255)
--   - employees (integer) - exact count from 5500 or authoritative source
--   - country (varchar 10)
--   - state (varchar 50)
--   - city (varchar 100)
--   - postal_code (varchar 20)
--   - data_year (integer) - year this data reflects
--
-- PEOPLE columns added (1):
--   - is_decision_maker (boolean)
--
-- Indexes added (4):
--   - idx_company_target_industry
--   - idx_company_target_state
--   - idx_company_target_employees
--   - idx_people_master_decision_maker
-- ==============================================================================
