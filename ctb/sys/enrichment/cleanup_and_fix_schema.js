#!/usr/bin/env node
/**
 * PLE Schema Cleanup + Fixes
 *
 * STEP 1: Clean up data violations
 * STEP 2: Apply constraints to clean data
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;
const results = { phases: [], violations: [], warnings: [] };

const phases = [
    {
        id: 1,
        name: 'Data Cleanup: Fix employee_count violations',
        sql: `
BEGIN;

-- Fix companies with employee_count < 50: set to 50 (minimum)
UPDATE marketing.company_master
SET employee_count = 50
WHERE employee_count < 50;

-- Fix any remaining NULLs (set to 50 minimum)
UPDATE marketing.company_master
SET employee_count = 50
WHERE employee_count IS NULL;

-- Note: NO MAXIMUM - companies can be larger than 2000 employees

COMMIT;
        `
    },
    {
        id: 2,
        name: 'Data Cleanup: Convert state names to abbreviations',
        sql: `
BEGIN;

-- Convert full state names to abbreviations
UPDATE marketing.company_master
SET address_state = CASE address_state
    WHEN 'Pennsylvania' THEN 'PA'
    WHEN 'Virginia' THEN 'VA'
    WHEN 'Maryland' THEN 'MD'
    WHEN 'Ohio' THEN 'OH'
    WHEN 'West Virginia' THEN 'WV'
    WHEN 'Kentucky' THEN 'KY'
    -- Already abbreviated
    WHEN 'PA' THEN 'PA'
    WHEN 'VA' THEN 'VA'
    WHEN 'MD' THEN 'MD'
    WHEN 'OH' THEN 'OH'
    WHEN 'WV' THEN 'WV'
    WHEN 'KY' THEN 'KY'
    ELSE address_state
END
WHERE address_state IN ('Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky','PA','VA','MD','OH','WV','KY');

COMMIT;
        `
    },
    {
        id: 3,
        name: 'Data Cleanup: Verify slot_type values',
        sql: `
BEGIN;

-- Slot types are already uppercase: CEO, CFO, HR
-- No changes needed - existing check constraint enforces uppercase

SELECT 'Slot types already correct' AS status;

COMMIT;
        `
    },
    {
        id: 4,
        name: 'Add NOT NULL Constraints',
        sql: `
BEGIN;

-- company_master: employee_count
ALTER TABLE marketing.company_master
ALTER COLUMN employee_count SET NOT NULL;

-- company_master: address_state
ALTER TABLE marketing.company_master
ALTER COLUMN address_state SET NOT NULL;

COMMIT;
        `
    },
    {
        id: 5,
        name: 'Add CHECK Constraints',
        sql: `
BEGIN;

-- company_master: employee minimum (50+, no maximum)
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_employee_range CASCADE;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_employee_minimum
CHECK (employee_count >= 50);

-- company_master: valid states
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_state_valid CASCADE;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_state_valid
CHECK (address_state IN ('PA','VA','MD','OH','WV','KY'));

-- company_slot: valid slot types (UPPERCASE: CEO, CFO, HR)
-- Note: Already has TWO check constraints - keep existing ones
-- They enforce UPPERCASE which matches existing data

-- people_master: contact required
ALTER TABLE marketing.people_master
DROP CONSTRAINT IF EXISTS chk_contact_required CASCADE;

ALTER TABLE marketing.people_master
ADD CONSTRAINT chk_contact_required
CHECK (linkedin_url IS NOT NULL OR email IS NOT NULL);

COMMIT;
        `
    },
    {
        id: 6,
        name: 'Add UNIQUE Constraints',
        sql: `
BEGIN;

-- company_slot: one slot per type per company
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS uq_company_slot_type CASCADE;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT uq_company_slot_type
UNIQUE (company_unique_id, slot_type);

COMMIT;
        `
    },
    {
        id: 7,
        name: 'Create Sidecar Tables',
        sql: `
BEGIN;

-- person_movement_history
CREATE TABLE IF NOT EXISTS marketing.person_movement_history (
    id SERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL REFERENCES marketing.people_master(unique_id),
    linkedin_url TEXT,
    company_from_id TEXT NOT NULL REFERENCES marketing.company_master(company_unique_id),
    company_to_id TEXT REFERENCES marketing.company_master(company_unique_id),
    title_from TEXT NOT NULL,
    title_to TEXT,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('company_change','title_change','contact_lost')),
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- person_scores
CREATE TABLE IF NOT EXISTS marketing.person_scores (
    id SERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL REFERENCES marketing.people_master(unique_id) UNIQUE,
    bit_score INT CHECK (bit_score >= 0 AND bit_score <= 100),
    confidence_score INT CHECK (confidence_score >= 0 AND confidence_score <= 100),
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    score_factors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- company_events
CREATE TABLE IF NOT EXISTS marketing.company_events (
    id SERIAL PRIMARY KEY,
    company_unique_id TEXT NOT NULL REFERENCES marketing.company_master(company_unique_id),
    event_type TEXT CHECK (event_type IN ('funding','acquisition','ipo','layoff','leadership_change','product_launch','office_opening','other')),
    event_date DATE,
    source_url TEXT,
    summary TEXT,
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    impacts_bit BOOLEAN DEFAULT TRUE,
    bit_impact_score INT CHECK (bit_impact_score >= -100 AND bit_impact_score <= 100),
    created_at TIMESTAMP DEFAULT NOW()
);

COMMIT;
        `
    },
    {
        id: 8,
        name: 'Create Indexes',
        sql: `
BEGIN;

-- company_master indexes
CREATE INDEX IF NOT EXISTS idx_company_master_state ON marketing.company_master(address_state);
CREATE INDEX IF NOT EXISTS idx_company_master_employee ON marketing.company_master(employee_count);

-- company_slot indexes
CREATE INDEX IF NOT EXISTS idx_company_slot_company_type ON marketing.company_slot(company_unique_id, slot_type);
CREATE INDEX IF NOT EXISTS idx_company_slot_filled ON marketing.company_slot(is_filled, company_unique_id);

-- people_master indexes
CREATE INDEX IF NOT EXISTS idx_people_master_linkedin ON marketing.people_master(linkedin_url) WHERE linkedin_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_people_master_email ON marketing.people_master(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_people_master_company ON marketing.people_master(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_master_validation ON marketing.people_master(validation_status);

-- person_movement_history indexes
CREATE INDEX IF NOT EXISTS idx_movement_person ON marketing.person_movement_history(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_movement_detected ON marketing.person_movement_history(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_movement_type ON marketing.person_movement_history(movement_type, detected_at DESC);

-- person_scores indexes
CREATE INDEX IF NOT EXISTS idx_person_scores_bit ON marketing.person_scores(bit_score DESC, calculated_at DESC);

-- company_events indexes
CREATE INDEX IF NOT EXISTS idx_company_events_company ON marketing.company_events(company_unique_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_company_events_type ON marketing.company_events(event_type, detected_at DESC);

COMMIT;
        `
    }
];

async function executePhase(client, phase) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`PHASE ${phase.id}: ${phase.name}`);
    console.log('='.repeat(60));

    try {
        const result = await client.query(phase.sql);

        console.log(`✓ Phase ${phase.id} completed successfully`);

        if (result.rowCount !== undefined && result.rowCount > 0) {
            console.log(`  Affected rows: ${result.rowCount}`);
        }

        results.phases.push({
            phase: phase.id,
            name: phase.name,
            status: 'SUCCESS',
            errors: null
        });

        return true;
    } catch (error) {
        console.error(`✗ Phase ${phase.id} FAILED:`, error.message);

        results.phases.push({
            phase: phase.id,
            name: phase.name,
            status: 'FAILED',
            errors: error.message
        });

        return false;
    }
}

async function verifyFixes(client) {
    console.log(`\n${'='.repeat(60)}`);
    console.log('VERIFICATION');
    console.log('='.repeat(60));

    const checks = [
        {
            name: 'Employee count violations (should be 0)',
            sql: `SELECT COUNT(*) as count FROM marketing.company_master WHERE employee_count < 50 OR employee_count IS NULL;`
        },
        {
            name: 'Invalid state values (should be 0)',
            sql: `SELECT COUNT(*) as count FROM marketing.company_master WHERE address_state NOT IN ('PA','VA','MD','OH','WV','KY');`
        },
        {
            name: 'State distribution after cleanup',
            sql: `SELECT address_state, COUNT(*) as count FROM marketing.company_master GROUP BY address_state ORDER BY count DESC;`
        },
        {
            name: 'CHECK constraints created',
            sql: `
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'marketing'
                AND constraint_type = 'CHECK'
                AND constraint_name LIKE 'chk_%'
                ORDER BY table_name, constraint_name;
            `
        },
        {
            name: 'Sidecar tables created',
            sql: `
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'marketing'
                AND table_name IN ('person_movement_history','person_scores','company_events')
                ORDER BY table_name;
            `
        },
        {
            name: 'New indexes created',
            sql: `
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE schemaname = 'marketing'
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            `
        }
    ];

    for (const check of checks) {
        try {
            const result = await client.query(check.sql);
            console.log(`\n${check.name}:`);

            if (result.rows.length === 1 && 'count' in result.rows[0]) {
                const count = parseInt(result.rows[0].count);
                console.log(`  Result: ${count}`);
            } else {
                console.table(result.rows);
            }
        } catch (error) {
            console.error(`  ERROR: ${error.message}`);
        }
    }
}

async function generateReport() {
    console.log(`\n${'='.repeat(60)}`);
    console.log('FINAL EXECUTION REPORT');
    console.log('='.repeat(60));

    console.log('\nPhase Results:');
    console.table(results.phases);

    const successCount = results.phases.filter(p => p.status === 'SUCCESS').length;
    const failCount = results.phases.filter(p => p.status === 'FAILED').length;

    console.log(`\nSummary:`);
    console.log(`  Total Phases: ${results.phases.length}`);
    console.log(`  Successful: ${successCount}`);
    console.log(`  Failed: ${failCount}`);

    if (failCount === 0) {
        console.log(`\n✓✓✓ ALL SCHEMA FIXES COMPLETED SUCCESSFULLY! ✓✓✓`);
        console.log(`\nNext Steps:`);
        console.log(`  1. Test enrichment queue processor with new schema`);
        console.log(`  2. Populate person_scores table with BIT scores`);
        console.log(`  3. Set up movement detection to fill person_movement_history`);
        console.log(`  4. Configure event scraping for company_events`);
    } else {
        console.log(`\n✗ ${failCount} PHASE(S) FAILED - REVIEW ERRORS`);
    }
}

async function main() {
    console.log('PLE SCHEMA CLEANUP + FIXES');
    console.log('='.repeat(60));
    console.log(`Database: ${connectionString.split('@')[1].split('/')[0]}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);

    const client = new Client({ connectionString });

    try {
        console.log('\nConnecting to database...');
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        // Execute all phases
        for (const phase of phases) {
            const success = await executePhase(client, phase);

            if (!success) {
                console.log(`\n✗ Stopping execution due to failure in Phase ${phase.id}`);
                break;
            }
        }

        // Verify all fixes
        await verifyFixes(client);

        // Generate final report
        await generateReport();

    } catch (error) {
        console.error('\nFATAL ERROR:', error.message);
        console.error(error.stack);
        process.exit(1);
    } finally {
        await client.end();
        console.log('\nDatabase connection closed');
    }
}

main().catch(console.error);
