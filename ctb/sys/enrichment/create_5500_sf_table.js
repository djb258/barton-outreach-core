#!/usr/bin/env node
/**
 * Form 5500-SF (Short Form) Table Creation
 *
 * Creates table for DOL Form 5500-SF filings (small plans < 100 participants)
 * Complements existing form_5500 table (large plans >= 100 participants)
 *
 * Based on 2023 F_5500_SF data dictionary / file layout
 * Primary key: ACK_ID (same as regular 5500 for consistent joins)
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('❌ ERROR: NEON_CONNECTION_STRING not found in .env');
    process.exit(1);
}

async function createForm5500SFTable() {
    const client = new Client({ connectionString });

    try {
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        console.log('═'.repeat(80));
        console.log('CREATING FORM 5500-SF TABLE (SHORT FORM)');
        console.log('═'.repeat(80));

        // Create form_5500_sf table
        console.log('\n1. Creating marketing.form_5500_sf table...');
        await client.query(`
            BEGIN;

            CREATE TABLE IF NOT EXISTS marketing.form_5500_sf (
                -- Primary key and system metadata
                id SERIAL PRIMARY KEY,
                ack_id VARCHAR(30) UNIQUE NOT NULL,
                company_unique_id TEXT REFERENCES marketing.company_master(company_unique_id),

                -- System metadata (DOL)
                filing_status VARCHAR(1),
                date_received DATE,
                valid_sig VARCHAR(1),
                form_type VARCHAR(10) DEFAULT '5500-SF',
                form_year INT,

                -- Sponsor/Company fields (SPONSOR_DFE_*)
                sponsor_dfe_ein VARCHAR(9) NOT NULL,
                sponsor_dfe_name VARCHAR(140),

                -- Mailing address
                spons_dfe_mail_us_address1 VARCHAR(35),
                spons_dfe_mail_us_address2 VARCHAR(35),
                spons_dfe_mail_us_city VARCHAR(22),
                spons_dfe_mail_us_state VARCHAR(2),
                spons_dfe_mail_us_zip VARCHAR(10),

                -- Location address
                spons_dfe_loc_us_address1 VARCHAR(35),
                spons_dfe_loc_us_address2 VARCHAR(35),
                spons_dfe_loc_us_city VARCHAR(22),
                spons_dfe_loc_us_state VARCHAR(2),
                spons_dfe_loc_us_zip VARCHAR(10),

                -- Contact
                spons_dfe_phone_num VARCHAR(15),
                business_code VARCHAR(6),

                -- Plan-level fields
                plan_name VARCHAR(140),
                plan_number VARCHAR(3),

                -- Plan type indicators
                plan_type_pension_ind VARCHAR(1),
                plan_type_welfare_ind VARCHAR(1),

                -- Funding indicators
                funding_insurance_ind VARCHAR(1),
                funding_trust_ind VARCHAR(1),
                funding_gen_assets_ind VARCHAR(1),

                -- Benefit indicators
                benefit_insurance_ind VARCHAR(1),
                benefit_trust_ind VARCHAR(1),
                benefit_gen_assets_ind VARCHAR(1),

                -- Participant counts
                tot_active_partcp_boy_cnt INT,
                tot_partcp_boy_cnt INT,
                tot_active_partcp_eoy_cnt INT,
                tot_partcp_eoy_cnt INT,
                participant_cnt_rptd_ind VARCHAR(1),

                -- Plan year and program flags
                short_plan_year_ind VARCHAR(1),
                dfvc_program_ind VARCHAR(1),

                -- Schedule attachment indicators
                sch_a_attached_ind VARCHAR(1),
                num_sch_a_attached_cnt INT,
                sch_c_attached_ind VARCHAR(1),
                sch_d_attached_ind VARCHAR(1),
                sch_g_attached_ind VARCHAR(1),
                sch_h_attached_ind VARCHAR(1),
                sch_i_attached_ind VARCHAR(1),
                sch_mb_attached_ind VARCHAR(1),
                sch_sb_attached_ind VARCHAR(1),
                sch_r_attached_ind VARCHAR(1),
                mewa_m1_attached_ind VARCHAR(1),

                -- Raw payload for complete data
                raw_payload JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_5500_sf_ack_id ON marketing.form_5500_sf(ack_id);
            CREATE INDEX IF NOT EXISTS idx_5500_sf_ein ON marketing.form_5500_sf(sponsor_dfe_ein);
            CREATE INDEX IF NOT EXISTS idx_5500_sf_company ON marketing.form_5500_sf(company_unique_id);
            CREATE INDEX IF NOT EXISTS idx_5500_sf_state ON marketing.form_5500_sf(spons_dfe_mail_us_state);
            CREATE INDEX IF NOT EXISTS idx_5500_sf_year ON marketing.form_5500_sf(form_year);
            CREATE INDEX IF NOT EXISTS idx_5500_sf_date_received ON marketing.form_5500_sf(date_received);

            -- Composite index for company matching
            CREATE INDEX IF NOT EXISTS idx_5500_sf_sponsor_state
            ON marketing.form_5500_sf(LOWER(sponsor_dfe_name), spons_dfe_mail_us_state);

            -- GIN index for JSONB queries
            CREATE INDEX IF NOT EXISTS idx_5500_sf_raw_payload_gin
            ON marketing.form_5500_sf USING gin(raw_payload);

            -- Partial index for pension plans
            CREATE INDEX IF NOT EXISTS idx_5500_sf_pension
            ON marketing.form_5500_sf(plan_type_pension_ind)
            WHERE plan_type_pension_ind = '1';

            -- Partial index for welfare plans
            CREATE INDEX IF NOT EXISTS idx_5500_sf_welfare
            ON marketing.form_5500_sf(plan_type_welfare_ind)
            WHERE plan_type_welfare_ind = '1';

            COMMIT;
        `);
        console.log('   ✓ Table created: marketing.form_5500_sf');
        console.log('   ✓ 10 indexes created');

        // Add constraints
        console.log('\n2. Adding constraints...');
        await client.query(`
            BEGIN;

            -- Unique constraint on ACK_ID
            ALTER TABLE marketing.form_5500_sf
            ADD CONSTRAINT uq_form_5500_sf_ack_id UNIQUE (ack_id);

            -- CHECK constraint for EIN format (9 digits)
            ALTER TABLE marketing.form_5500_sf
            ADD CONSTRAINT chk_form_5500_sf_ein_format
            CHECK (sponsor_dfe_ein ~ '^[0-9]{9}$');

            -- CHECK constraint for form_type
            ALTER TABLE marketing.form_5500_sf
            ADD CONSTRAINT chk_form_5500_sf_form_type
            CHECK (form_type IN ('5500-SF', '5500SF'));

            COMMIT;
        `);
        console.log('   ✓ Unique constraint: uq_form_5500_sf_ack_id');
        console.log('   ✓ CHECK constraint: chk_form_5500_sf_ein_format');
        console.log('   ✓ CHECK constraint: chk_form_5500_sf_form_type');

        // Add column comments
        console.log('\n3. Adding column comments...');
        await client.query(`
            COMMENT ON TABLE marketing.form_5500_sf IS 'DOL Form 5500-SF (Short Form) for small plans (<100 participants)';
            COMMENT ON COLUMN marketing.form_5500_sf.ack_id IS 'DOL unique filing ID - primary key for all schedule joins';
            COMMENT ON COLUMN marketing.form_5500_sf.sponsor_dfe_ein IS 'Employer Identification Number (9 digits)';
            COMMENT ON COLUMN marketing.form_5500_sf.sponsor_dfe_name IS 'Plan sponsor name (company name from DOL)';
            COMMENT ON COLUMN marketing.form_5500_sf.plan_type_pension_ind IS '1=Pension plan, blank=Not pension';
            COMMENT ON COLUMN marketing.form_5500_sf.plan_type_welfare_ind IS '1=Welfare plan, blank=Not welfare';
            COMMENT ON COLUMN marketing.form_5500_sf.tot_partcp_eoy_cnt IS 'Total participants at end of year';
            COMMENT ON COLUMN marketing.form_5500_sf.form_type IS 'Always 5500-SF for short form';
            COMMENT ON COLUMN marketing.form_5500_sf.form_year IS 'Form year (not calendar year)';
            COMMENT ON COLUMN marketing.form_5500_sf.raw_payload IS 'Complete raw CSV data from DOL';
        `);
        console.log('   ✓ Column comments added');

        // Create staging table
        console.log('\n4. Creating staging table...');
        await client.query(`
            BEGIN;

            CREATE TABLE IF NOT EXISTS marketing.form_5500_sf_staging (
                ack_id TEXT,
                filing_status TEXT,
                date_received TEXT,
                valid_sig TEXT,
                sponsor_dfe_ein TEXT,
                sponsor_dfe_name TEXT,
                spons_dfe_mail_us_address1 TEXT,
                spons_dfe_mail_us_address2 TEXT,
                spons_dfe_mail_us_city TEXT,
                spons_dfe_mail_us_state TEXT,
                spons_dfe_mail_us_zip TEXT,
                spons_dfe_loc_us_address1 TEXT,
                spons_dfe_loc_us_address2 TEXT,
                spons_dfe_loc_us_city TEXT,
                spons_dfe_loc_us_state TEXT,
                spons_dfe_loc_us_zip TEXT,
                spons_dfe_phone_num TEXT,
                business_code TEXT,
                plan_name TEXT,
                plan_number TEXT,
                plan_type_pension_ind TEXT,
                plan_type_welfare_ind TEXT,
                funding_insurance_ind TEXT,
                funding_trust_ind TEXT,
                funding_gen_assets_ind TEXT,
                benefit_insurance_ind TEXT,
                benefit_trust_ind TEXT,
                benefit_gen_assets_ind TEXT,
                tot_active_partcp_boy_cnt TEXT,
                tot_partcp_boy_cnt TEXT,
                tot_active_partcp_eoy_cnt TEXT,
                tot_partcp_eoy_cnt TEXT,
                participant_cnt_rptd_ind TEXT,
                short_plan_year_ind TEXT,
                dfvc_program_ind TEXT,
                sch_a_attached_ind TEXT,
                num_sch_a_attached_cnt TEXT,
                sch_c_attached_ind TEXT,
                sch_d_attached_ind TEXT,
                sch_g_attached_ind TEXT,
                sch_h_attached_ind TEXT,
                sch_i_attached_ind TEXT,
                sch_mb_attached_ind TEXT,
                sch_sb_attached_ind TEXT,
                sch_r_attached_ind TEXT,
                mewa_m1_attached_ind TEXT,
                form_year TEXT
            );

            COMMENT ON TABLE marketing.form_5500_sf_staging IS 'Staging table for Form 5500-SF CSV imports';

            COMMIT;
        `);
        console.log('   ✓ Staging table created: marketing.form_5500_sf_staging');

        // Create processing procedure
        console.log('\n5. Creating processing procedure...');
        await client.query(`
            BEGIN;

            CREATE OR REPLACE PROCEDURE marketing.process_5500_sf_staging()
            LANGUAGE plpgsql AS $$
            DECLARE
                v_row RECORD;
                v_company_uid TEXT;
                v_count INT := 0;
                v_matched INT := 0;
            BEGIN
                FOR v_row IN SELECT * FROM marketing.form_5500_sf_staging LOOP
                    -- Try to match to existing company
                    v_company_uid := marketing.match_5500_to_company(
                        v_row.sponsor_dfe_name,
                        v_row.spons_dfe_mail_us_city,
                        v_row.spons_dfe_mail_us_state
                    );

                    IF v_company_uid IS NOT NULL THEN
                        v_matched := v_matched + 1;
                    END IF;

                    -- Insert into main table
                    INSERT INTO marketing.form_5500_sf (
                        ack_id,
                        company_unique_id,
                        filing_status,
                        date_received,
                        valid_sig,
                        sponsor_dfe_ein,
                        sponsor_dfe_name,
                        spons_dfe_mail_us_address1,
                        spons_dfe_mail_us_address2,
                        spons_dfe_mail_us_city,
                        spons_dfe_mail_us_state,
                        spons_dfe_mail_us_zip,
                        spons_dfe_loc_us_address1,
                        spons_dfe_loc_us_address2,
                        spons_dfe_loc_us_city,
                        spons_dfe_loc_us_state,
                        spons_dfe_loc_us_zip,
                        spons_dfe_phone_num,
                        business_code,
                        plan_name,
                        plan_number,
                        plan_type_pension_ind,
                        plan_type_welfare_ind,
                        funding_insurance_ind,
                        funding_trust_ind,
                        funding_gen_assets_ind,
                        benefit_insurance_ind,
                        benefit_trust_ind,
                        benefit_gen_assets_ind,
                        tot_active_partcp_boy_cnt,
                        tot_partcp_boy_cnt,
                        tot_active_partcp_eoy_cnt,
                        tot_partcp_eoy_cnt,
                        participant_cnt_rptd_ind,
                        short_plan_year_ind,
                        dfvc_program_ind,
                        sch_a_attached_ind,
                        num_sch_a_attached_cnt,
                        sch_c_attached_ind,
                        sch_d_attached_ind,
                        sch_g_attached_ind,
                        sch_h_attached_ind,
                        sch_i_attached_ind,
                        sch_mb_attached_ind,
                        sch_sb_attached_ind,
                        sch_r_attached_ind,
                        mewa_m1_attached_ind,
                        form_year
                    ) VALUES (
                        v_row.ack_id,
                        v_company_uid,
                        v_row.filing_status,
                        NULLIF(v_row.date_received, '')::DATE,
                        v_row.valid_sig,
                        v_row.sponsor_dfe_ein,
                        v_row.sponsor_dfe_name,
                        v_row.spons_dfe_mail_us_address1,
                        v_row.spons_dfe_mail_us_address2,
                        v_row.spons_dfe_mail_us_city,
                        v_row.spons_dfe_mail_us_state,
                        v_row.spons_dfe_mail_us_zip,
                        v_row.spons_dfe_loc_us_address1,
                        v_row.spons_dfe_loc_us_address2,
                        v_row.spons_dfe_loc_us_city,
                        v_row.spons_dfe_loc_us_state,
                        v_row.spons_dfe_loc_us_zip,
                        v_row.spons_dfe_phone_num,
                        v_row.business_code,
                        v_row.plan_name,
                        v_row.plan_number,
                        v_row.plan_type_pension_ind,
                        v_row.plan_type_welfare_ind,
                        v_row.funding_insurance_ind,
                        v_row.funding_trust_ind,
                        v_row.funding_gen_assets_ind,
                        v_row.benefit_insurance_ind,
                        v_row.benefit_trust_ind,
                        v_row.benefit_gen_assets_ind,
                        NULLIF(REGEXP_REPLACE(v_row.tot_active_partcp_boy_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.tot_partcp_boy_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.tot_active_partcp_eoy_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.tot_partcp_eoy_cnt, '[^0-9]', '', 'g'), '')::INT,
                        v_row.participant_cnt_rptd_ind,
                        v_row.short_plan_year_ind,
                        v_row.dfvc_program_ind,
                        v_row.sch_a_attached_ind,
                        NULLIF(REGEXP_REPLACE(v_row.num_sch_a_attached_cnt, '[^0-9]', '', 'g'), '')::INT,
                        v_row.sch_c_attached_ind,
                        v_row.sch_d_attached_ind,
                        v_row.sch_g_attached_ind,
                        v_row.sch_h_attached_ind,
                        v_row.sch_i_attached_ind,
                        v_row.sch_mb_attached_ind,
                        v_row.sch_sb_attached_ind,
                        v_row.sch_r_attached_ind,
                        v_row.mewa_m1_attached_ind,
                        NULLIF(v_row.form_year, '')::INT
                    )
                    ON CONFLICT (ack_id) DO NOTHING;

                    -- Update company with EIN if matched
                    IF v_company_uid IS NOT NULL THEN
                        UPDATE marketing.company_master
                        SET ein = v_row.sponsor_dfe_ein
                        WHERE company_unique_id = v_company_uid
                        AND ein IS NULL;
                    END IF;

                    v_count := v_count + 1;
                END LOOP;

                RAISE NOTICE 'Processed % Form 5500-SF records, matched % to existing companies', v_count, v_matched;

                -- Clear staging table
                TRUNCATE marketing.form_5500_sf_staging;
            END;
            $$;

            COMMENT ON PROCEDURE marketing.process_5500_sf_staging IS 'Process Form 5500-SF staging table and match to companies';

            COMMIT;
        `);
        console.log('   ✓ Procedure created: marketing.process_5500_sf_staging()');

        // Verification
        console.log('\n' + '═'.repeat(80));
        console.log('VERIFICATION');
        console.log('═'.repeat(80));

        const indexes = await client.query(`
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'marketing'
            AND tablename = 'form_5500_sf'
            ORDER BY indexname;
        `);

        console.log('\nIndexes on marketing.form_5500_sf:');
        indexes.rows.forEach(row => {
            console.log(`  ✓ ${row.indexname}`);
        });

        const constraints = await client.query(`
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'marketing'
            AND table_name = 'form_5500_sf'
            AND constraint_type IN ('UNIQUE', 'CHECK', 'PRIMARY KEY')
            ORDER BY constraint_name;
        `);

        console.log('\nConstraints on marketing.form_5500_sf:');
        constraints.rows.forEach(row => {
            console.log(`  ✓ ${row.constraint_name} (${row.constraint_type})`);
        });

        console.log('\n' + '═'.repeat(80));
        console.log('FORM 5500-SF TABLE CREATION COMPLETE');
        console.log('═'.repeat(80));
        console.log('\n✅ Ready to import DOL Form 5500-SF CSV data');
        console.log('\nNext steps:');
        console.log('1. Download CSV: F_5500_SF_2023_latest.csv from DOL');
        console.log('2. Import: \\COPY marketing.form_5500_sf_staging FROM \\'5500_sf_data.csv\\' CSV HEADER;');
        console.log('3. Process: CALL marketing.process_5500_sf_staging();');
        console.log('4. Verify: SELECT COUNT(*) FROM marketing.form_5500_sf;');

    } catch (err) {
        console.error('\n❌ ERROR:', err.message);
        console.error(err.stack);
        process.exit(1);
    } finally {
        await client.end();
    }
}

createForm5500SFTable();
