#!/usr/bin/env node
/**
 * Company Intelligence Enrichment Layer
 *
 * Implements:
 * - Form 5500 data tables
 * - DOL violations tracking
 * - Email pattern detection
 * - Phone on slots (role-level)
 * - Company federal IDs
 * - Enrichment functions and views
 *
 * Architecture: COMPANY = asset (rich), PEOPLE = occupants (minimal)
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('❌ ERROR: NEON_CONNECTION_STRING not found in .env');
    process.exit(1);
}

const tasks = [
    // TASK 1A: Form 5500 Data Table
    {
        id: '1A',
        name: 'Create form_5500 table',
        sql: `
BEGIN;

CREATE TABLE IF NOT EXISTS marketing.form_5500 (
    id SERIAL PRIMARY KEY,
    company_unique_id TEXT REFERENCES marketing.company_master(company_unique_id),
    ack_id VARCHAR(30),
    ein VARCHAR(9) NOT NULL,
    plan_number VARCHAR(3),
    plan_name VARCHAR(140),
    sponsor_name VARCHAR(70),
    address VARCHAR(35),
    city VARCHAR(22),
    state VARCHAR(2),
    zip VARCHAR(12),
    date_received DATE,
    plan_codes VARCHAR(59),
    participant_count INT,
    total_assets NUMERIC(15,2),
    filing_year INT,
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_5500_ein ON marketing.form_5500(ein);
CREATE INDEX IF NOT EXISTS idx_5500_company ON marketing.form_5500(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_5500_state ON marketing.form_5500(state);
CREATE INDEX IF NOT EXISTS idx_5500_year ON marketing.form_5500(filing_year);

COMMIT;
        `
    },

    // TASK 1B: DOL Violations Table
    {
        id: '1B',
        name: 'Create dol_violations table',
        sql: `
BEGIN;

CREATE TABLE IF NOT EXISTS marketing.dol_violations (
    id SERIAL PRIMARY KEY,
    company_unique_id TEXT REFERENCES marketing.company_master(company_unique_id),
    ein VARCHAR(9) NOT NULL,
    violation_type VARCHAR(100),
    violation_date DATE,
    resolution_date DATE,
    penalty_amount NUMERIC(12,2),
    description TEXT,
    source_url VARCHAR(500),
    raw_payload JSONB,
    detected_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_violations_ein ON marketing.dol_violations(ein);
CREATE INDEX IF NOT EXISTS idx_violations_company ON marketing.dol_violations(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_violations_type ON marketing.dol_violations(violation_type);

COMMIT;
        `
    },

    // TASK 1C: Email Pattern Columns
    {
        id: '1C',
        name: 'Add email pattern columns to company_master',
        sql: `
BEGIN;

ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS email_pattern VARCHAR(50),
ADD COLUMN IF NOT EXISTS email_pattern_confidence INT,
ADD COLUMN IF NOT EXISTS email_pattern_source VARCHAR(50),
ADD COLUMN IF NOT EXISTS email_pattern_verified_at TIMESTAMP;

COMMENT ON COLUMN marketing.company_master.email_pattern IS 'Pattern: {first}.{last}@, {f}{last}@, etc.';
COMMENT ON COLUMN marketing.company_master.email_pattern_confidence IS 'Confidence 0-100';
COMMENT ON COLUMN marketing.company_master.email_pattern_source IS 'Source: hunter, manual, enrichment';

COMMIT;
        `
    },

    // TASK 1D: Phone on Slots
    {
        id: '1D',
        name: 'Add phone columns to company_slot',
        sql: `
BEGIN;

ALTER TABLE marketing.company_slot
ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS phone_extension VARCHAR(10),
ADD COLUMN IF NOT EXISTS phone_verified_at TIMESTAMP;

COMMENT ON COLUMN marketing.company_slot.phone IS 'Phone for this role/slot (not person-specific)';

COMMIT;
        `
    },

    // TASK 1E: Federal ID Columns
    {
        id: '1E',
        name: 'Add federal ID columns to company_master',
        sql: `
BEGIN;

ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS ein VARCHAR(9),
ADD COLUMN IF NOT EXISTS duns VARCHAR(9),
ADD COLUMN IF NOT EXISTS cage_code VARCHAR(5);

CREATE INDEX IF NOT EXISTS idx_company_ein ON marketing.company_master(ein);

COMMENT ON COLUMN marketing.company_master.ein IS 'Employer Identification Number';
COMMENT ON COLUMN marketing.company_master.duns IS 'Dun & Bradstreet Number';
COMMENT ON COLUMN marketing.company_master.cage_code IS 'Commercial And Government Entity Code';

COMMIT;
        `
    },

    // TASK 2A: Generate Email Function
    {
        id: '2A',
        name: 'Create generate_email function',
        sql: `
BEGIN;

CREATE OR REPLACE FUNCTION marketing.generate_email(
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_pattern VARCHAR,
    p_domain VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_email VARCHAR;
    v_first VARCHAR;
    v_last VARCHAR;
    v_f CHAR(1);
    v_l CHAR(1);
BEGIN
    v_first := LOWER(TRIM(p_first_name));
    v_last := LOWER(TRIM(p_last_name));
    v_f := LEFT(v_first, 1);
    v_l := LEFT(v_last, 1);

    v_email := p_pattern;
    v_email := REPLACE(v_email, '{first}', v_first);
    v_email := REPLACE(v_email, '{last}', v_last);
    v_email := REPLACE(v_email, '{f}', v_f);
    v_email := REPLACE(v_email, '{l}', v_l);
    v_email := v_email || p_domain;

    RETURN v_email;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.generate_email IS 'Generate email from pattern: {first}.{last}@, {f}{last}@, etc.';

COMMIT;
        `
    },

    // TASK 2B: Match 5500 to Company Function
    {
        id: '2B',
        name: 'Create match_5500_to_company function',
        sql: `
BEGIN;

CREATE OR REPLACE FUNCTION marketing.match_5500_to_company(
    p_sponsor_name VARCHAR,
    p_city VARCHAR,
    p_state VARCHAR
) RETURNS TEXT AS $$
DECLARE
    v_company_uid TEXT;
BEGIN
    -- Exact match on name + state
    SELECT company_unique_id INTO v_company_uid
    FROM marketing.company_master
    WHERE LOWER(company_name) = LOWER(p_sponsor_name)
    AND address_state = p_state
    LIMIT 1;

    IF v_company_uid IS NULL THEN
        -- Fuzzy match: name contains + city + state
        SELECT company_unique_id INTO v_company_uid
        FROM marketing.company_master
        WHERE LOWER(company_name) LIKE '%' || LOWER(p_sponsor_name) || '%'
        AND LOWER(address_city) = LOWER(p_city)
        AND address_state = p_state
        LIMIT 1;
    END IF;

    RETURN v_company_uid;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.match_5500_to_company IS 'Match Form 5500 sponsor to existing company record';

COMMIT;
        `
    },

    // TASK 3A: Enrichment Status View
    {
        id: '3A',
        name: 'Create v_company_enrichment_status view',
        sql: `
BEGIN;

CREATE OR REPLACE VIEW marketing.v_company_enrichment_status AS
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.address_state,
    -- Enrichment flags
    CASE WHEN cm.ein IS NOT NULL THEN 1 ELSE 0 END as has_ein,
    CASE WHEN cm.email_pattern IS NOT NULL THEN 1 ELSE 0 END as has_email_pattern,
    CASE WHEN cm.linkedin_url IS NOT NULL THEN 1 ELSE 0 END as has_linkedin,
    CASE WHEN cm.website_url IS NOT NULL THEN 1 ELSE 0 END as has_website,
    CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END as has_5500,
    -- Slot coverage
    (SELECT COUNT(*) FROM marketing.company_slot cs
     WHERE cs.company_unique_id = cm.company_unique_id
     AND cs.person_unique_id IS NOT NULL) as slots_filled,
    (SELECT COUNT(*) FROM marketing.company_slot cs
     WHERE cs.company_unique_id = cm.company_unique_id
     AND cs.phone IS NOT NULL) as slots_with_phone,
    -- Enrichment score (0-100)
    (
        (CASE WHEN cm.ein IS NOT NULL THEN 15 ELSE 0 END) +
        (CASE WHEN cm.email_pattern IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN cm.linkedin_url IS NOT NULL THEN 10 ELSE 0 END) +
        (CASE WHEN cm.website_url IS NOT NULL THEN 10 ELSE 0 END) +
        (CASE WHEN f.id IS NOT NULL THEN 15 ELSE 0 END) +
        LEAST(30, (SELECT COUNT(*) * 10 FROM marketing.company_slot cs
                   WHERE cs.company_unique_id = cm.company_unique_id
                   AND cs.person_unique_id IS NOT NULL))
    ) as enrichment_score
FROM marketing.company_master cm
LEFT JOIN marketing.form_5500 f ON f.company_unique_id = cm.company_unique_id;

COMMENT ON VIEW marketing.v_company_enrichment_status IS 'Company enrichment completeness score (0-100)';

COMMIT;
        `
    },

    // TASK 3B: Companies Needing Enrichment View
    {
        id: '3B',
        name: 'Create v_companies_need_enrichment view',
        sql: `
BEGIN;

CREATE OR REPLACE VIEW marketing.v_companies_need_enrichment AS
SELECT
    company_unique_id,
    company_name,
    address_state,
    CASE
        WHEN ein IS NULL THEN 'ein'
        WHEN email_pattern IS NULL THEN 'email_pattern'
        ELSE 'complete'
    END as next_enrichment_needed,
    CASE WHEN ein IS NULL THEN 1 ELSE 0 END as missing_ein,
    CASE WHEN email_pattern IS NULL THEN 1 ELSE 0 END as missing_email_pattern,
    CASE WHEN linkedin_url IS NULL THEN 1 ELSE 0 END as missing_linkedin,
    CASE WHEN website_url IS NULL THEN 1 ELSE 0 END as missing_website
FROM marketing.company_master
WHERE ein IS NULL OR email_pattern IS NULL OR linkedin_url IS NULL OR website_url IS NULL
ORDER BY
    CASE WHEN ein IS NULL AND email_pattern IS NULL THEN 1
         WHEN ein IS NULL THEN 2
         WHEN email_pattern IS NULL THEN 3
         ELSE 4 END;

COMMENT ON VIEW marketing.v_companies_need_enrichment IS 'Companies prioritized by enrichment needs';

COMMIT;
        `
    },

    // TASK 4A: 5500 Staging Table
    {
        id: '4A',
        name: 'Create form_5500_staging table',
        sql: `
BEGIN;

CREATE TABLE IF NOT EXISTS marketing.form_5500_staging (
    ack_id VARCHAR(30),
    ein VARCHAR(9),
    plan_number VARCHAR(3),
    plan_name VARCHAR(140),
    sponsor_name VARCHAR(70),
    address VARCHAR(35),
    city VARCHAR(22),
    state VARCHAR(2),
    zip VARCHAR(12),
    date_received VARCHAR(10),
    plan_codes VARCHAR(59),
    participant_count VARCHAR(20),
    total_assets VARCHAR(30),
    imported_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE marketing.form_5500_staging IS 'Staging table for CSV import of Form 5500 data';

COMMIT;
        `
    },

    // TASK 4B: Process Staging Procedure
    {
        id: '4B',
        name: 'Create process_5500_staging procedure',
        sql: `
BEGIN;

CREATE OR REPLACE PROCEDURE marketing.process_5500_staging()
LANGUAGE plpgsql AS $$
DECLARE
    v_row RECORD;
    v_company_uid TEXT;
    v_count INT := 0;
    v_matched INT := 0;
BEGIN
    FOR v_row IN SELECT * FROM marketing.form_5500_staging LOOP
        -- Try to match to existing company
        v_company_uid := marketing.match_5500_to_company(
            v_row.sponsor_name,
            v_row.city,
            v_row.state
        );

        IF v_company_uid IS NOT NULL THEN
            v_matched := v_matched + 1;
        END IF;

        -- Insert into main table
        INSERT INTO marketing.form_5500 (
            company_unique_id,
            ack_id,
            ein,
            plan_number,
            plan_name,
            sponsor_name,
            address,
            city,
            state,
            zip,
            date_received,
            plan_codes,
            participant_count,
            total_assets,
            filing_year
        ) VALUES (
            v_company_uid,
            v_row.ack_id,
            v_row.ein,
            v_row.plan_number,
            v_row.plan_name,
            v_row.sponsor_name,
            v_row.address,
            v_row.city,
            v_row.state,
            v_row.zip,
            TO_DATE(v_row.date_received, 'MM/DD/YYYY'),
            v_row.plan_codes,
            NULLIF(REGEXP_REPLACE(v_row.participant_count, '[^0-9]', '', 'g'), '')::INT,
            NULLIF(REGEXP_REPLACE(v_row.total_assets, '[^0-9.]', '', 'g'), '')::NUMERIC,
            EXTRACT(YEAR FROM TO_DATE(v_row.date_received, 'MM/DD/YYYY'))
        )
        ON CONFLICT DO NOTHING;

        -- Update company with EIN if matched
        IF v_company_uid IS NOT NULL THEN
            UPDATE marketing.company_master
            SET ein = v_row.ein
            WHERE company_unique_id = v_company_uid
            AND ein IS NULL;
        END IF;

        v_count := v_count + 1;
    END LOOP;

    RAISE NOTICE 'Processed % records, matched % to existing companies', v_count, v_matched;

    -- Clear staging
    TRUNCATE marketing.form_5500_staging;
END;
$$;

COMMENT ON PROCEDURE marketing.process_5500_staging IS 'Process Form 5500 staging records into main table';

COMMIT;
        `
    },

    // TASK 5A: Detect Email Pattern Function
    {
        id: '5A',
        name: 'Create detect_email_pattern function',
        sql: `
BEGIN;

CREATE OR REPLACE FUNCTION marketing.detect_email_pattern(
    p_email VARCHAR,
    p_first_name VARCHAR,
    p_last_name VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_local VARCHAR;
    v_domain VARCHAR;
    v_first VARCHAR;
    v_last VARCHAR;
    v_f CHAR(1);
    v_l CHAR(1);
BEGIN
    v_local := SPLIT_PART(p_email, '@', 1);
    v_domain := SPLIT_PART(p_email, '@', 2);
    v_first := LOWER(TRIM(p_first_name));
    v_last := LOWER(TRIM(p_last_name));
    v_f := LEFT(v_first, 1);
    v_l := LEFT(v_last, 1);

    -- Check patterns in order of specificity
    IF v_local = v_first || '.' || v_last THEN
        RETURN '{first}.{last}@';
    ELSIF v_local = v_first || v_last THEN
        RETURN '{first}{last}@';
    ELSIF v_local = v_f || v_last THEN
        RETURN '{f}{last}@';
    ELSIF v_local = v_first || v_l THEN
        RETURN '{first}{l}@';
    ELSIF v_local = v_f || '.' || v_last THEN
        RETURN '{f}.{last}@';
    ELSIF v_local = v_first || '_' || v_last THEN
        RETURN '{first}_{last}@';
    ELSIF v_local = v_last || '.' || v_first THEN
        RETURN '{last}.{first}@';
    ELSIF v_local = v_last || v_f THEN
        RETURN '{last}{f}@';
    ELSIF v_local = v_first THEN
        RETURN '{first}@';
    ELSIF v_local = v_last THEN
        RETURN '{last}@';
    ELSE
        RETURN NULL; -- Unknown pattern
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.detect_email_pattern IS 'Reverse engineer email pattern from known email address';

COMMIT;
        `
    },

    // TASK 5B: Update Company Email Pattern Procedure
    {
        id: '5B',
        name: 'Create update_company_email_pattern procedure',
        sql: `
BEGIN;

CREATE OR REPLACE PROCEDURE marketing.update_company_email_pattern(
    p_company_unique_id TEXT,
    p_email VARCHAR,
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_source VARCHAR DEFAULT 'enrichment'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_pattern VARCHAR;
    v_domain VARCHAR;
BEGIN
    v_pattern := marketing.detect_email_pattern(p_email, p_first_name, p_last_name);
    v_domain := SPLIT_PART(p_email, '@', 2);

    IF v_pattern IS NOT NULL THEN
        UPDATE marketing.company_master
        SET
            email_pattern = v_pattern,
            email_pattern_confidence = 80,
            email_pattern_source = p_source,
            email_pattern_verified_at = NOW(),
            website_url = COALESCE(website_url, v_domain)
        WHERE company_unique_id = p_company_unique_id
        AND email_pattern IS NULL;
    END IF;
END;
$$;

COMMENT ON PROCEDURE marketing.update_company_email_pattern IS 'Update company email pattern from verified email';

COMMIT;
        `
    }
];

async function executeTask(client, task) {
    try {
        await client.query(task.sql);
        return { success: true, error: null };
    } catch (err) {
        return { success: false, error: err.message };
    }
}

async function verifySchema(client) {
    console.log(`\n${'='.repeat(80)}`);
    console.log('VERIFICATION');
    console.log('='.repeat(80));

    // Check new columns on company_master
    const companyColumns = await client.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
        AND table_name = 'company_master'
        AND column_name IN ('ein', 'duns', 'cage_code', 'email_pattern',
                           'email_pattern_confidence', 'email_pattern_source',
                           'email_pattern_verified_at')
        ORDER BY column_name;
    `);

    // Check new columns on company_slot
    const slotColumns = await client.query(`
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
        AND table_name = 'company_slot'
        AND column_name IN ('phone', 'phone_extension', 'phone_verified_at')
        ORDER BY column_name;
    `);

    // Check new tables
    const newTables = await client.query(`
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'marketing'
        AND table_name IN ('form_5500', 'form_5500_staging', 'dol_violations')
        ORDER BY table_name;
    `);

    // Check functions
    const functions = await client.query(`
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'marketing'
        AND routine_type = 'FUNCTION'
        AND routine_name IN ('generate_email', 'match_5500_to_company', 'detect_email_pattern')
        ORDER BY routine_name;
    `);

    // Check procedures
    const procedures = await client.query(`
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'marketing'
        AND routine_type = 'PROCEDURE'
        AND routine_name IN ('process_5500_staging', 'update_company_email_pattern')
        ORDER BY routine_name;
    `);

    // Check views
    const views = await client.query(`
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'marketing'
        AND table_name LIKE 'v_company%'
        ORDER BY table_name;
    `);

    // Check indexes
    const indexes = await client.query(`
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'marketing'
        AND indexname LIKE '%5500%' OR indexname LIKE '%violation%' OR indexname = 'idx_company_ein'
        ORDER BY indexname;
    `);

    console.log('\n📋 COMPANY_MASTER NEW COLUMNS:');
    console.log('-'.repeat(80));
    companyColumns.rows.forEach(col => {
        console.log(`  ✓ ${col.column_name.padEnd(35)} ${col.data_type}`);
    });

    console.log('\n📋 COMPANY_SLOT NEW COLUMNS:');
    console.log('-'.repeat(80));
    slotColumns.rows.forEach(col => {
        console.log(`  ✓ ${col.column_name.padEnd(35)} ${col.data_type}`);
    });

    console.log('\n📊 NEW TABLES:');
    console.log('-'.repeat(80));
    newTables.rows.forEach(tbl => {
        console.log(`  ✓ marketing.${tbl.table_name}`);
    });

    console.log('\n⚙️  FUNCTIONS:');
    console.log('-'.repeat(80));
    functions.rows.forEach(fn => {
        console.log(`  ✓ marketing.${fn.routine_name}()`);
    });

    console.log('\n⚙️  PROCEDURES:');
    console.log('-'.repeat(80));
    procedures.rows.forEach(proc => {
        console.log(`  ✓ marketing.${proc.routine_name}()`);
    });

    console.log('\n👁️  VIEWS:');
    console.log('-'.repeat(80));
    views.rows.forEach(vw => {
        console.log(`  ✓ marketing.${vw.table_name}`);
    });

    console.log('\n🔍 INDEXES:');
    console.log('-'.repeat(80));
    indexes.rows.forEach(idx => {
        console.log(`  ✓ ${idx.indexname}`);
    });

    return {
        columnsAdded: companyColumns.rows.length + slotColumns.rows.length,
        tablesCreated: newTables.rows.length,
        functionsCreated: functions.rows.length,
        proceduresCreated: procedures.rows.length,
        viewsCreated: views.rows.length,
        indexesCreated: indexes.rows.length
    };
}

async function main() {
    console.log('='.repeat(80));
    console.log('COMPANY INTELLIGENCE ENRICHMENT LAYER');
    console.log('='.repeat(80));
    console.log('Architecture: COMPANY = asset (rich), PEOPLE = occupants (minimal)');
    console.log('='.repeat(80));

    const client = new Client({ connectionString });

    try {
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        const results = [];

        for (const task of tasks) {
            process.stdout.write(`Task ${task.id}: ${task.name}... `);
            const result = await executeTask(client, task);

            if (result.success) {
                console.log('✓ SUCCESS');
                results.push({ id: task.id, name: task.name, status: 'SUCCESS' });
            } else {
                console.log(`✗ FAILED\n  Error: ${result.error}`);
                results.push({ id: task.id, name: task.name, status: 'FAILED', error: result.error });
            }
        }

        // Verify schema
        const summary = await verifySchema(client);

        // Print execution report
        console.log(`\n${'='.repeat(80)}`);
        console.log('EXECUTION REPORT');
        console.log('='.repeat(80));
        console.log('\n| Task | Description | Status |');
        console.log('|------|-------------|--------|');
        results.forEach(r => {
            const status = r.status === 'SUCCESS' ? '✓ SUCCESS' : '✗ FAILED';
            console.log(`| ${r.id.padEnd(4)} | ${r.name.slice(0, 50).padEnd(50)} | ${status} |`);
        });

        // Schema summary
        console.log(`\n${'='.repeat(80)}`);
        console.log('SCHEMA SUMMARY');
        console.log('='.repeat(80));
        console.log(`Tables created: ${summary.tablesCreated}`);
        console.log(`Columns added: ${summary.columnsAdded}`);
        console.log(`Functions created: ${summary.functionsCreated}`);
        console.log(`Procedures created: ${summary.proceduresCreated}`);
        console.log(`Views created: ${summary.viewsCreated}`);
        console.log(`Indexes created: ${summary.indexesCreated}`);

        // Next steps
        console.log(`\n${'='.repeat(80)}`);
        console.log('NEXT STEPS');
        console.log('='.repeat(80));
        console.log('1. Import Form 5500 CSV to marketing.form_5500_staging');
        console.log('   COPY marketing.form_5500_staging FROM \'5500_data.csv\' CSV HEADER;');
        console.log('\n2. Process staging records:');
        console.log('   CALL marketing.process_5500_staging();');
        console.log('\n3. Check enrichment status:');
        console.log('   SELECT * FROM marketing.v_company_enrichment_status LIMIT 10;');
        console.log('\n4. Test email generation:');
        console.log('   SELECT marketing.generate_email(\'John\', \'Smith\', \'{f}{last}@\', \'acme.com\');');
        console.log('\n5. Test pattern detection:');
        console.log('   SELECT marketing.detect_email_pattern(\'jsmith@acme.com\', \'John\', \'Smith\');');
        console.log('\n6. Set up Hunter.io API for email pattern detection');
        console.log('7. Configure MillionVerifier for email validation');

        const successCount = results.filter(r => r.status === 'SUCCESS').length;
        const failureCount = results.filter(r => r.status === 'FAILED').length;

        console.log(`\n${'='.repeat(80)}`);
        console.log(`COMPLETE: ${successCount}/${results.length} tasks succeeded`);
        if (failureCount > 0) {
            console.log(`WARNING: ${failureCount} tasks failed`);
        }
        console.log('='.repeat(80));

    } catch (err) {
        console.error('\n❌ FATAL ERROR:', err.message);
        console.error(err.stack);
        process.exit(1);
    } finally {
        await client.end();
    }
}

main();
