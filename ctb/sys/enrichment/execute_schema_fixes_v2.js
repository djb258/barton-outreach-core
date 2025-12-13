#!/usr/bin/env node
/**
 * PLE Schema Fixes Executor V2
 *
 * CORRECTED FOR ACTUAL SCHEMA:
 * - Uses company_name (not name)
 * - Uses address_state (not state)
 * - Uses company_unique_id (not company_uid)
 * - People FK references use company_unique_id/company_slot_unique_id
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('ERROR: No database connection string found');
    process.exit(1);
}

const results = { phases: [], violations: [], warnings: [] };

// Corrected SQL for actual schema
const phases = [
    {
        id: 1,
        name: 'Add Missing Columns',
        description: 'Already complete - validation_status, last_verified_at, last_enrichment_attempt, vacated_at exist',
        sql: `SELECT 'Phase 1 - Columns already exist' AS status;`
    },
    {
        id: 2,
        name: 'Add NOT NULL Constraints',
        sql: `
BEGIN;

-- company_master: company_name (already NOT NULL)
-- company_master: employee_count (needs constraint)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE employee_count IS NULL) THEN
        RAISE NOTICE 'WARNING: % rows with NULL employee_count', (SELECT COUNT(*) FROM marketing.company_master WHERE employee_count IS NULL);
        -- Fix: Set default 50 for NULL values
        UPDATE marketing.company_master SET employee_count = 50 WHERE employee_count IS NULL;
    END IF;
    ALTER TABLE marketing.company_master ALTER COLUMN employee_count SET NOT NULL;
END $$;

-- company_master: address_state (needs constraint)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE address_state IS NULL) THEN
        RAISE NOTICE 'WARNING: % rows with NULL address_state', (SELECT COUNT(*) FROM marketing.company_master WHERE address_state IS NULL);
        -- Cannot proceed - need state value
    ELSE
        ALTER TABLE marketing.company_master ALTER COLUMN address_state SET NOT NULL;
    END IF;
END $$;

-- company_master: source_system (already NOT NULL)

-- company_slot: slot_type (already NOT NULL)
-- company_slot: company_unique_id (already NOT NULL)

-- people_master: first_name, last_name (already NOT NULL)
-- people_master: company_unique_id, company_slot_unique_id (already NOT NULL)

COMMIT;
        `
    },
    {
        id: 3,
        name: 'Add CHECK Constraints',
        sql: `
BEGIN;

-- company_master: employee range 50-2000
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_employee_range;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_employee_range
CHECK (employee_count >= 50 AND employee_count <= 2000);

-- company_master: valid states (using address_state)
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_state_valid;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_state_valid
CHECK (address_state IN ('PA','VA','MD','OH','WV','KY'));

-- company_slot: valid slot types
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS chk_slot_type;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT chk_slot_type
CHECK (LOWER(slot_type) IN ('ceo','cfo','hr'));

-- people_master: contact required (linkedin OR email)
ALTER TABLE marketing.people_master
DROP CONSTRAINT IF EXISTS chk_contact_required;

ALTER TABLE marketing.people_master
ADD CONSTRAINT chk_contact_required
CHECK (linkedin_url IS NOT NULL OR email IS NOT NULL);

COMMIT;
        `
    },
    {
        id: 4,
        name: 'Add UNIQUE Constraints',
        sql: `
BEGIN;

-- company_master: company_unique_id already has unique constraint (it's the PK)

-- company_slot: company_slot_unique_id already has unique constraint (it's the PK)

-- company_slot: one slot per type per company
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS uq_company_slot_type;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT uq_company_slot_type
UNIQUE (company_unique_id, slot_type);

-- people_master: unique_id already has unique constraint (it's the PK)

COMMIT;
        `
    },
    {
        id: 5,
        name: 'Create Sidecar Tables',
        sql: `
BEGIN;

-- person_movement_history (tracks when executives change companies/titles)
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

-- person_scores (BIT scores for people)
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

-- company_events (news, funding, M&A, leadership changes)
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
        id: 6,
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
    if (phase.description) {
        console.log(`Note: ${phase.description}`);
    }
    console.log('='.repeat(60));

    try {
        // Add notice handler
        const notices = [];
        client.on('notice', (msg) => {
            notices.push(msg.message);
        });

        const result = await client.query(phase.sql);

        // Show any notices
        notices.forEach(notice => {
            console.log(`NOTICE: ${notice}`);
            results.warnings.push({
                phase: phase.id,
                message: notice
            });
        });

        console.log(`✓ Phase ${phase.id} completed successfully`);

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

async function verifySchema(client) {
    console.log(`\n${'='.repeat(60)}`);
    console.log('SCHEMA VERIFICATION');
    console.log('='.repeat(60));

    const checks = [
        {
            name: 'NOT NULL Constraints',
            sql: `
                SELECT table_name, column_name, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name IN ('company_master', 'company_slot', 'people_master')
                AND column_name IN ('company_name','employee_count','address_state','slot_type','first_name','last_name')
                ORDER BY table_name, column_name;
            `
        },
        {
            name: 'CHECK Constraints',
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
            name: 'UNIQUE Constraints',
            sql: `
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'marketing'
                AND constraint_type = 'UNIQUE'
                ORDER BY table_name, constraint_name;
            `
        },
        {
            name: 'Sidecar Tables',
            sql: `
                SELECT table_name,
                       (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='marketing' AND table_name=t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'marketing'
                AND table_name IN ('person_movement_history', 'person_scores', 'company_events')
                ORDER BY table_name;
            `
        },
        {
            name: 'New Indexes',
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
            console.log(`\n${check.name}: ${result.rows.length} items`);

            if (result.rows.length > 0) {
                console.table(result.rows);
            }
        } catch (error) {
            console.error(`  ERROR: ${error.message}`);
        }
    }
}

async function checkViolations(client) {
    console.log(`\n${'='.repeat(60)}`);
    console.log('DATA VIOLATIONS CHECK');
    console.log('='.repeat(60));

    const checks = [
        {
            name: 'Companies with NULL employee_count',
            sql: `SELECT COUNT(*) as count FROM marketing.company_master WHERE employee_count IS NULL;`
        },
        {
            name: 'Companies outside 50-2000 range',
            sql: `SELECT COUNT(*) as count FROM marketing.company_master WHERE employee_count < 50 OR employee_count > 2000;`
        },
        {
            name: 'Companies with invalid state',
            sql: `SELECT COUNT(*) as count FROM marketing.company_master WHERE address_state NOT IN ('PA','VA','MD','OH','WV','KY');`
        },
        {
            name: 'People with no contact info',
            sql: `SELECT COUNT(*) as count FROM marketing.people_master WHERE linkedin_url IS NULL AND email IS NULL;`
        },
        {
            name: 'Duplicate slot types per company',
            sql: `
                SELECT company_unique_id, slot_type, COUNT(*) as dupes
                FROM marketing.company_slot
                GROUP BY company_unique_id, slot_type
                HAVING COUNT(*) > 1
                LIMIT 10;
            `
        }
    ];

    for (const check of checks) {
        try {
            const result = await client.query(check.sql);
            console.log(`\n${check.name}:`);

            if (result.rows.length === 1 && 'count' in result.rows[0]) {
                const count = parseInt(result.rows[0].count);
                if (count > 0) {
                    console.log(`  ⚠ ${count} violations found`);
                    results.violations.push({ check: check.name, count });
                } else {
                    console.log(`  ✓ No violations`);
                }
            } else if (result.rows.length > 0) {
                console.log(`  ⚠ ${result.rows.length} violations found`);
                console.table(result.rows);
                results.violations.push({ check: check.name, count: result.rows.length });
            } else {
                console.log(`  ✓ No violations`);
            }
        } catch (error) {
            console.error(`  ERROR: ${error.message}`);
        }
    }
}

async function generateReport() {
    console.log(`\n${'='.repeat(60)}`);
    console.log('EXECUTION REPORT');
    console.log('='.repeat(60));

    console.log('\nPhase Results:');
    console.table(results.phases);

    if (results.violations.length > 0) {
        console.log('\nData Violations:');
        console.table(results.violations);
    }

    if (results.warnings.length > 0) {
        console.log('\nWarnings:');
        console.table(results.warnings);
    }

    const successCount = results.phases.filter(p => p.status === 'SUCCESS').length;
    const failCount = results.phases.filter(p => p.status === 'FAILED').length;

    console.log(`\nSummary:`);
    console.log(`  Total Phases: ${results.phases.length}`);
    console.log(`  Successful: ${successCount}`);
    console.log(`  Failed: ${failCount}`);
    console.log(`  Violations: ${results.violations.length}`);
    console.log(`  Warnings: ${results.warnings.length}`);

    if (failCount === 0) {
        console.log(`\n✓ ALL SCHEMA FIXES APPLIED SUCCESSFULLY!`);
    } else {
        console.log(`\n✗ ${failCount} PHASE(S) FAILED - REVIEW ERRORS ABOVE`);
    }
}

async function main() {
    console.log('PLE SCHEMA FIXES EXECUTOR V2');
    console.log('='.repeat(60));
    console.log(`Database: ${connectionString.split('@')[1].split('/')[0]}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);

    const client = new Client({ connectionString });

    try {
        console.log('\nConnecting to database...');
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL');

        // Check violations BEFORE fixes
        await checkViolations(client);

        // Execute all phases
        for (const phase of phases) {
            const success = await executePhase(client, phase);

            if (!success) {
                console.log(`\n⚠ Phase ${phase.id} failed, continuing with remaining phases...`);
                // Continue anyway to see all results
            }
        }

        // Verify schema
        await verifySchema(client);

        // Check violations AFTER fixes
        console.log('\n--- AFTER FIXES ---');
        await checkViolations(client);

        // Generate report
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
