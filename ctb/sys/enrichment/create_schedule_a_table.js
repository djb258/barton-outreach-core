#!/usr/bin/env node
/**
 * Schedule A Table Creation
 *
 * Creates table for DOL Schedule A filings (insurance information)
 * Attached to both Form 5500 (large plans) and Form 5500-SF (small plans)
 *
 * Based on 2023 F_SCH_A data dictionary / file layout
 * Primary key: id (auto-increment)
 * Join key: ACK_ID (joins to form_5500.ack_id or form_5500_sf.ack_id)
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('❌ ERROR: NEON_CONNECTION_STRING not found in .env');
    process.exit(1);
}

async function createScheduleATable() {
    const client = new Client({ connectionString });

    try {
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        console.log('═'.repeat(80));
        console.log('CREATING SCHEDULE A TABLE (INSURANCE INFORMATION)');
        console.log('═'.repeat(80));

        // Create schedule_a table
        console.log('\n1. Creating marketing.schedule_a table...');
        await client.query(`
            BEGIN;

            CREATE TABLE IF NOT EXISTS marketing.schedule_a (
                -- Primary key and system metadata
                id SERIAL PRIMARY KEY,
                ack_id VARCHAR(30) NOT NULL,  -- FK to form_5500 or form_5500_sf

                -- Plan year dates
                sch_a_plan_year_begin_date DATE,
                sch_a_plan_year_end_date DATE,

                -- Insurance carrier information
                insurance_company_name VARCHAR(140),
                insurance_company_ein VARCHAR(9),
                contract_number VARCHAR(50),

                -- Policy dates (for renewal analysis)
                policy_year_begin_date DATE,
                policy_year_end_date DATE,
                renewal_month INT,  -- Derived from policy_year_end_date (1-12)
                renewal_year INT,   -- Derived from policy_year_end_date (YYYY)

                -- Coverage information
                covered_lives INT,  -- Number of persons covered at end of year

                -- Insurance type indicators (key welfare benefits)
                wlfr_bnft_health_ind VARCHAR(1),
                wlfr_bnft_dental_ind VARCHAR(1),
                wlfr_bnft_vision_ind VARCHAR(1),
                wlfr_bnft_life_ind VARCHAR(1),
                wlfr_bnft_stdisd_ind VARCHAR(1),  -- Short-term disability
                wlfr_bnft_ltdisd_ind VARCHAR(1),  -- Long-term disability

                -- Financial information
                insurance_commissions_fees NUMERIC(15, 2),
                total_premiums_paid NUMERIC(15, 2),

                -- Raw payload for complete data (90 columns)
                raw_payload JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_schedule_a_ack_id ON marketing.schedule_a(ack_id);
            CREATE INDEX IF NOT EXISTS idx_schedule_a_insurance_ein ON marketing.schedule_a(insurance_company_ein);
            CREATE INDEX IF NOT EXISTS idx_schedule_a_insurance_name ON marketing.schedule_a(LOWER(insurance_company_name));
            CREATE INDEX IF NOT EXISTS idx_schedule_a_renewal_month ON marketing.schedule_a(renewal_month) WHERE renewal_month IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_schedule_a_renewal_year ON marketing.schedule_a(renewal_year) WHERE renewal_year IS NOT NULL;

            -- Composite index for renewal timing queries
            CREATE INDEX IF NOT EXISTS idx_schedule_a_renewal_timing
            ON marketing.schedule_a(renewal_year, renewal_month, policy_year_end_date)
            WHERE renewal_month IS NOT NULL;

            -- GIN index for JSONB queries
            CREATE INDEX IF NOT EXISTS idx_schedule_a_raw_payload_gin
            ON marketing.schedule_a USING gin(raw_payload);

            -- Partial indexes for benefit types
            CREATE INDEX IF NOT EXISTS idx_schedule_a_health
            ON marketing.schedule_a(wlfr_bnft_health_ind)
            WHERE wlfr_bnft_health_ind = '1';

            CREATE INDEX IF NOT EXISTS idx_schedule_a_dental
            ON marketing.schedule_a(wlfr_bnft_dental_ind)
            WHERE wlfr_bnft_dental_ind = '1';

            CREATE INDEX IF NOT EXISTS idx_schedule_a_life
            ON marketing.schedule_a(wlfr_bnft_life_ind)
            WHERE wlfr_bnft_life_ind = '1';

            COMMIT;
        `);
        console.log('   ✓ Table created: marketing.schedule_a');
        console.log('   ✓ 10 indexes created');

        // Add constraints
        console.log('\n2. Adding constraints...');
        await client.query(`
            BEGIN;

            -- CHECK constraint for EIN format (9 digits)
            ALTER TABLE marketing.schedule_a
            ADD CONSTRAINT chk_schedule_a_ein_format
            CHECK (insurance_company_ein IS NULL OR insurance_company_ein ~ '^[0-9]{9}$');

            -- CHECK constraint for renewal_month (1-12)
            ALTER TABLE marketing.schedule_a
            ADD CONSTRAINT chk_schedule_a_renewal_month
            CHECK (renewal_month IS NULL OR (renewal_month >= 1 AND renewal_month <= 12));

            -- CHECK constraint for covered_lives (non-negative)
            ALTER TABLE marketing.schedule_a
            ADD CONSTRAINT chk_schedule_a_covered_lives
            CHECK (covered_lives IS NULL OR covered_lives >= 0);

            COMMIT;
        `);
        console.log('   ✓ CHECK constraint: chk_schedule_a_ein_format');
        console.log('   ✓ CHECK constraint: chk_schedule_a_renewal_month');
        console.log('   ✓ CHECK constraint: chk_schedule_a_covered_lives');

        // Add column comments
        console.log('\n3. Adding column comments...');
        await client.query(`
            COMMENT ON TABLE marketing.schedule_a IS 'DOL Schedule A - Insurance information attached to Form 5500/5500-SF';
            COMMENT ON COLUMN marketing.schedule_a.ack_id IS 'DOL filing ID - joins to form_5500.ack_id or form_5500_sf.ack_id';
            COMMENT ON COLUMN marketing.schedule_a.insurance_company_ein IS 'Insurance carrier EIN (9 digits)';
            COMMENT ON COLUMN marketing.schedule_a.insurance_company_name IS 'Insurance carrier name';
            COMMENT ON COLUMN marketing.schedule_a.contract_number IS 'Insurance policy/contract number';
            COMMENT ON COLUMN marketing.schedule_a.policy_year_end_date IS 'Policy end date - used to calculate renewal timing';
            COMMENT ON COLUMN marketing.schedule_a.renewal_month IS 'Month of renewal (1-12) - derived from policy_year_end_date';
            COMMENT ON COLUMN marketing.schedule_a.renewal_year IS 'Year of renewal (YYYY) - derived from policy_year_end_date';
            COMMENT ON COLUMN marketing.schedule_a.covered_lives IS 'Number of persons covered at end of year';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_health_ind IS '1=Health insurance benefit, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_dental_ind IS '1=Dental benefit, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_vision_ind IS '1=Vision benefit, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_life_ind IS '1=Life insurance benefit, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_stdisd_ind IS '1=Short-term disability, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.wlfr_bnft_ltdisd_ind IS '1=Long-term disability, blank=No';
            COMMENT ON COLUMN marketing.schedule_a.raw_payload IS 'Complete raw CSV data (all 90 columns) from DOL';
        `);
        console.log('   ✓ Column comments added');

        // Create staging table
        console.log('\n4. Creating staging table...');
        await client.query(`
            BEGIN;

            CREATE TABLE IF NOT EXISTS marketing.schedule_a_staging (
                ack_id TEXT,
                form_plan_year_begin_date TEXT,
                sch_a_plan_year_begin_date TEXT,
                sch_a_plan_year_end_date TEXT,
                form_tax_prd TEXT,
                type_of_plan_entity_cd TEXT,
                insurance_company_name TEXT,
                insurance_company_ein TEXT,
                insurance_company_phone_num TEXT,
                contract_number TEXT,
                covered_lives TEXT,
                policy_year_begin_date TEXT,
                policy_year_end_date TEXT,
                -- All other columns stored as TEXT for flexible import
                raw_payload_text TEXT
            );

            COMMENT ON TABLE marketing.schedule_a_staging IS 'Staging table for Schedule A CSV imports';

            COMMIT;
        `);
        console.log('   ✓ Staging table created: marketing.schedule_a_staging');

        // Create processing procedure
        console.log('\n5. Creating processing procedure...');
        await client.query(`
            BEGIN;

            CREATE OR REPLACE PROCEDURE marketing.process_schedule_a_staging()
            LANGUAGE plpgsql AS $$
            DECLARE
                v_row RECORD;
                v_count INT := 0;
                v_renewal_month INT;
                v_renewal_year INT;
            BEGIN
                FOR v_row IN SELECT * FROM marketing.schedule_a_staging LOOP
                    -- Calculate renewal month and year from policy_year_end_date
                    v_renewal_month := NULL;
                    v_renewal_year := NULL;

                    IF v_row.policy_year_end_date IS NOT NULL AND v_row.policy_year_end_date != '' THEN
                        BEGIN
                            v_renewal_month := EXTRACT(MONTH FROM v_row.policy_year_end_date::DATE);
                            v_renewal_year := EXTRACT(YEAR FROM v_row.policy_year_end_date::DATE);
                        EXCEPTION WHEN OTHERS THEN
                            -- Invalid date format, leave as NULL
                            v_renewal_month := NULL;
                            v_renewal_year := NULL;
                        END;
                    END IF;

                    -- Insert into main table
                    INSERT INTO marketing.schedule_a (
                        ack_id,
                        sch_a_plan_year_begin_date,
                        sch_a_plan_year_end_date,
                        insurance_company_name,
                        insurance_company_ein,
                        contract_number,
                        policy_year_begin_date,
                        policy_year_end_date,
                        renewal_month,
                        renewal_year,
                        covered_lives
                    ) VALUES (
                        v_row.ack_id,
                        NULLIF(v_row.sch_a_plan_year_begin_date, '')::DATE,
                        NULLIF(v_row.sch_a_plan_year_end_date, '')::DATE,
                        v_row.insurance_company_name,
                        v_row.insurance_company_ein,
                        v_row.contract_number,
                        NULLIF(v_row.policy_year_begin_date, '')::DATE,
                        NULLIF(v_row.policy_year_end_date, '')::DATE,
                        v_renewal_month,
                        v_renewal_year,
                        NULLIF(REGEXP_REPLACE(v_row.covered_lives, '[^0-9]', '', 'g'), '')::INT
                    );

                    v_count := v_count + 1;

                    -- Progress notification every 50k records
                    IF v_count % 50000 = 0 THEN
                        RAISE NOTICE 'Processed % Schedule A records...', v_count;
                    END IF;
                END LOOP;

                RAISE NOTICE 'Processed % Schedule A records total', v_count;

                -- Clear staging table
                TRUNCATE marketing.schedule_a_staging;
            END;
            $$;

            COMMENT ON PROCEDURE marketing.process_schedule_a_staging IS 'Process Schedule A staging table with renewal date calculation';

            COMMIT;
        `);
        console.log('   ✓ Procedure created: marketing.process_schedule_a_staging()');

        // Verification
        console.log('\n' + '═'.repeat(80));
        console.log('VERIFICATION');
        console.log('═'.repeat(80));

        const indexes = await client.query(`
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'marketing'
            AND tablename = 'schedule_a'
            ORDER BY indexname;
        `);

        console.log('\nIndexes on marketing.schedule_a:');
        indexes.rows.forEach(row => {
            console.log(`  ✓ ${row.indexname}`);
        });

        const constraints = await client.query(`
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'marketing'
            AND table_name = 'schedule_a'
            AND constraint_type IN ('UNIQUE', 'CHECK', 'PRIMARY KEY')
            ORDER BY constraint_name;
        `);

        console.log('\nConstraints on marketing.schedule_a:');
        constraints.rows.forEach(row => {
            console.log(`  ✓ ${row.constraint_name} (${row.constraint_type})`);
        });

        console.log('\n' + '═'.repeat(80));
        console.log('SCHEDULE A TABLE CREATION COMPLETE');
        console.log('═'.repeat(80));
        console.log('\n✅ Ready to import DOL Schedule A CSV data');
        console.log('\nNext steps:');
        console.log('1. Download CSV: F_SCH_A_2023_latest.csv from DOL');
        console.log('2. Import: \\COPY marketing.schedule_a_staging FROM \'schedule_a_data.csv\' CSV HEADER;');
        console.log('3. Process: CALL marketing.process_schedule_a_staging();');
        console.log('4. Verify: SELECT COUNT(*) FROM marketing.schedule_a;');
        console.log('5. Check renewals: SELECT COUNT(*) FROM marketing.schedule_a WHERE renewal_month IS NOT NULL;');

    } catch (err) {
        console.error('\n❌ ERROR:', err.message);
        console.error(err.stack);
        process.exit(1);
    } finally {
        await client.end();
    }
}

createScheduleATable();
