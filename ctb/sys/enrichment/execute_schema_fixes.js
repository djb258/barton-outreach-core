#!/usr/bin/env node
/**
 * PLE Schema Fixes Executor
 *
 * Executes all 6 phases of schema fixes for marketing schema in Neon PostgreSQL
 *
 * Usage: node execute_schema_fixes.js
 */

const { Client } = require('pg');
require('dotenv').config();

// Connection config
const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('ERROR: No database connection string found in .env');
    console.error('Set NEON_CONNECTION_STRING or DATABASE_URL');
    process.exit(1);
}

// Execution results tracking
const results = {
    phases: [],
    violations: [],
    warnings: []
};

// SQL for each phase
const phases = [
    {
        id: 1,
        name: 'Add Missing Columns',
        sql: `
BEGIN;

-- marketing.people_master - add 3 missing columns
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS validation_status VARCHAR GENERATED ALWAYS AS (
    CASE
      WHEN linkedin_url IS NOT NULL AND email IS NOT NULL THEN 'full'
      WHEN linkedin_url IS NOT NULL THEN 'linkedin_only'
      WHEN email IS NOT NULL THEN 'email_only'
      ELSE 'invalid'
    END
) STORED;

ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMP;

ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMP;

-- Backfill last_verified_at with created_at or NOW() for existing records
UPDATE marketing.people_master
SET last_verified_at = COALESCE(created_at, NOW())
WHERE last_verified_at IS NULL;

-- Now set NOT NULL after backfill
ALTER TABLE marketing.people_master
ALTER COLUMN last_verified_at SET NOT NULL;

-- Set default for future inserts
ALTER TABLE marketing.people_master
ALTER COLUMN last_verified_at SET DEFAULT NOW();

-- marketing.company_slot - add vacated_at
ALTER TABLE marketing.company_slot
ADD COLUMN IF NOT EXISTS vacated_at TIMESTAMP;

COMMIT;
        `
    },
    {
        id: 2,
        name: 'Add NOT NULL Constraints',
        sql: `
BEGIN;

-- Check for violations before each constraint
-- company_master
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE name IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_master.name - fix data first';
    ELSE
        ALTER TABLE marketing.company_master ALTER COLUMN name SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE employee_count IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_master.employee_count - fix data first';
    ELSE
        ALTER TABLE marketing.company_master ALTER COLUMN employee_count SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE state IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_master.state - fix data first';
    ELSE
        ALTER TABLE marketing.company_master ALTER COLUMN state SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE source IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_master.source - fix data first';
    ELSE
        ALTER TABLE marketing.company_master ALTER COLUMN source SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE created_at IS NULL) THEN
        UPDATE marketing.company_master SET created_at = NOW() WHERE created_at IS NULL;
    END IF;
    ALTER TABLE marketing.company_master ALTER COLUMN created_at SET NOT NULL;
    ALTER TABLE marketing.company_master ALTER COLUMN created_at SET DEFAULT NOW();
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_master WHERE company_uid IS NULL) THEN
        UPDATE marketing.company_master SET company_uid = gen_random_uuid() WHERE company_uid IS NULL;
    END IF;
    ALTER TABLE marketing.company_master ALTER COLUMN company_uid SET NOT NULL;
    ALTER TABLE marketing.company_master ALTER COLUMN company_uid SET DEFAULT gen_random_uuid();
END $$;

-- company_slot
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_slot WHERE slot_uid IS NULL) THEN
        UPDATE marketing.company_slot SET slot_uid = gen_random_uuid() WHERE slot_uid IS NULL;
    END IF;
    ALTER TABLE marketing.company_slot ALTER COLUMN slot_uid SET NOT NULL;
    ALTER TABLE marketing.company_slot ALTER COLUMN slot_uid SET DEFAULT gen_random_uuid();
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_slot WHERE company_id IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_slot.company_id - fix data first';
    ELSE
        ALTER TABLE marketing.company_slot ALTER COLUMN company_id SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.company_slot WHERE slot_type IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in company_slot.slot_type - fix data first';
    ELSE
        ALTER TABLE marketing.company_slot ALTER COLUMN slot_type SET NOT NULL;
    END IF;
END $$;

-- people_master
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE person_uid IS NULL) THEN
        UPDATE marketing.people_master SET person_uid = gen_random_uuid() WHERE person_uid IS NULL;
    END IF;
    ALTER TABLE marketing.people_master ALTER COLUMN person_uid SET NOT NULL;
    ALTER TABLE marketing.people_master ALTER COLUMN person_uid SET DEFAULT gen_random_uuid();
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE company_id IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in people_master.company_id - fix data first';
    ELSE
        ALTER TABLE marketing.people_master ALTER COLUMN company_id SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE first_name IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in people_master.first_name - fix data first';
    ELSE
        ALTER TABLE marketing.people_master ALTER COLUMN first_name SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE last_name IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in people_master.last_name - fix data first';
    ELSE
        ALTER TABLE marketing.people_master ALTER COLUMN last_name SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE title IS NULL) THEN
        RAISE NOTICE 'WARNING: NULL values in people_master.title - fix data first';
    ELSE
        ALTER TABLE marketing.people_master ALTER COLUMN title SET NOT NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM marketing.people_master WHERE created_at IS NULL) THEN
        UPDATE marketing.people_master SET created_at = NOW() WHERE created_at IS NULL;
    END IF;
    ALTER TABLE marketing.people_master ALTER COLUMN created_at SET NOT NULL;
    ALTER TABLE marketing.people_master ALTER COLUMN created_at SET DEFAULT NOW();
END $$;

COMMIT;
        `
    },
    {
        id: 3,
        name: 'Add CHECK Constraints',
        sql: `
BEGIN;

-- company_master: employee range
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_employee_range;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_employee_range
CHECK (employee_count >= 50 AND employee_count <= 2000);

-- company_master: valid states
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS chk_state_valid;

ALTER TABLE marketing.company_master
ADD CONSTRAINT chk_state_valid
CHECK (state IN ('PA','VA','MD','OH','WV','KY'));

-- company_slot: valid slot types
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS chk_slot_type;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT chk_slot_type
CHECK (slot_type IN ('ceo','cfo','hr'));

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

-- company_master: company_uid unique
ALTER TABLE marketing.company_master
DROP CONSTRAINT IF EXISTS uq_company_uid;

ALTER TABLE marketing.company_master
ADD CONSTRAINT uq_company_uid UNIQUE (company_uid);

-- company_slot: slot_uid unique
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS uq_slot_uid;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT uq_slot_uid UNIQUE (slot_uid);

-- company_slot: one slot per type per company
ALTER TABLE marketing.company_slot
DROP CONSTRAINT IF EXISTS uq_company_slot_type;

ALTER TABLE marketing.company_slot
ADD CONSTRAINT uq_company_slot_type UNIQUE (company_id, slot_type);

-- people_master: person_uid unique
ALTER TABLE marketing.people_master
DROP CONSTRAINT IF EXISTS uq_person_uid;

ALTER TABLE marketing.people_master
ADD CONSTRAINT uq_person_uid UNIQUE (person_uid);

COMMIT;
        `
    },
    {
        id: 5,
        name: 'Create Sidecar Tables',
        sql: `
BEGIN;

-- person_movement_history
CREATE TABLE IF NOT EXISTS marketing.person_movement_history (
    id SERIAL PRIMARY KEY,
    person_id INT NOT NULL REFERENCES marketing.people_master(id),
    linkedin_url VARCHAR,
    company_id_from INT NOT NULL REFERENCES marketing.company_master(id),
    company_id_to INT REFERENCES marketing.company_master(id),
    title_from VARCHAR NOT NULL,
    title_to VARCHAR,
    movement_type VARCHAR NOT NULL CHECK (movement_type IN ('company_change','title_change','contact_lost')),
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_payload JSONB
);

-- person_scores
CREATE TABLE IF NOT EXISTS marketing.person_scores (
    id SERIAL PRIMARY KEY,
    person_id INT NOT NULL REFERENCES marketing.people_master(id) UNIQUE,
    bit_score INT,
    confidence_score INT,
    calculated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    score_factors JSONB
);

-- company_events
CREATE TABLE IF NOT EXISTS marketing.company_events (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES marketing.company_master(id),
    event_type VARCHAR,
    event_date DATE,
    source_url VARCHAR,
    summary TEXT,
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    impacts_bit BOOLEAN DEFAULT TRUE
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
CREATE INDEX IF NOT EXISTS idx_company_master_uid ON marketing.company_master(company_uid);
CREATE INDEX IF NOT EXISTS idx_company_master_state ON marketing.company_master(state);

-- company_slot indexes
CREATE INDEX IF NOT EXISTS idx_company_slot_uid ON marketing.company_slot(slot_uid);
CREATE INDEX IF NOT EXISTS idx_company_slot_company_type ON marketing.company_slot(company_id, slot_type);

-- people_master indexes
CREATE INDEX IF NOT EXISTS idx_people_master_uid ON marketing.people_master(person_uid);
CREATE INDEX IF NOT EXISTS idx_people_master_linkedin ON marketing.people_master(linkedin_url) WHERE linkedin_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_people_master_email ON marketing.people_master(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_people_master_company ON marketing.people_master(company_id);
CREATE INDEX IF NOT EXISTS idx_people_master_validation ON marketing.people_master(validation_status);

-- person_movement_history indexes
CREATE INDEX IF NOT EXISTS idx_movement_person ON marketing.person_movement_history(person_id);
CREATE INDEX IF NOT EXISTS idx_movement_detected ON marketing.person_movement_history(detected_at);

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

        // Extract any NOTICE messages
        const notices = result.notices || [];
        notices.forEach(notice => {
            console.log(`NOTICE: ${notice.message}`);
            results.warnings.push({
                phase: phase.id,
                message: notice.message
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
            name: 'people_master columns',
            sql: `
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name = 'people_master'
                AND column_name IN ('validation_status', 'last_verified_at', 'last_enrichment_attempt')
                ORDER BY column_name;
            `
        },
        {
            name: 'company_slot vacated_at',
            sql: `
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name = 'company_slot'
                AND column_name = 'vacated_at';
            `
        },
        {
            name: 'NOT NULL constraints',
            sql: `
                SELECT table_name, column_name, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'marketing'
                AND table_name IN ('company_master', 'company_slot', 'people_master')
                AND is_nullable = 'NO'
                ORDER BY table_name, column_name;
            `
        },
        {
            name: 'CHECK constraints',
            sql: `
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'marketing'
                AND constraint_type = 'CHECK'
                ORDER BY table_name, constraint_name;
            `
        },
        {
            name: 'UNIQUE constraints',
            sql: `
                SELECT constraint_name, table_name
                FROM information_schema.table_constraints
                WHERE table_schema = 'marketing'
                AND constraint_type = 'UNIQUE'
                ORDER BY table_name, constraint_name;
            `
        },
        {
            name: 'Sidecar tables',
            sql: `
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'marketing'
                AND table_name IN ('person_movement_history', 'person_scores', 'company_events')
                ORDER BY table_name;
            `
        },
        {
            name: 'Indexes',
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
            console.log(`  Found ${result.rows.length} items`);

            if (result.rows.length > 0 && result.rows.length <= 10) {
                console.table(result.rows);
            } else if (result.rows.length > 10) {
                console.log(`  (showing first 10 of ${result.rows.length})`);
                console.table(result.rows.slice(0, 10));
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
    console.log(`  Warnings: ${results.warnings.length}`);

    if (failCount === 0) {
        console.log(`\n✓ ALL SCHEMA FIXES APPLIED SUCCESSFULLY!`);
    } else {
        console.log(`\n✗ ${failCount} PHASE(S) FAILED - REVIEW ERRORS ABOVE`);
    }
}

async function main() {
    console.log('PLE SCHEMA FIXES EXECUTOR');
    console.log('='.repeat(60));
    console.log(`Database: ${connectionString.split('@')[1].split('/')[0]}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);

    const client = new Client({ connectionString });

    try {
        console.log('\nConnecting to database...');
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL');

        // Execute all phases
        for (const phase of phases) {
            const success = await executePhase(client, phase);

            if (!success) {
                console.log(`\nStopping execution due to failure in Phase ${phase.id}`);
                break;
            }
        }

        // Verify schema
        await verifySchema(client);

        // Generate report
        await generateReport();

    } catch (error) {
        console.error('\nFATAL ERROR:', error.message);
        process.exit(1);
    } finally {
        await client.end();
        console.log('\nDatabase connection closed');
    }
}

// Run
main().catch(console.error);
