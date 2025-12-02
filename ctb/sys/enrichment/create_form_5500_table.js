#!/usr/bin/env node
/**
 * Form 5500 (Regular) Table Creation
 *
 * Creates table for DOL Form 5500 filings (large plans >= 100 participants)
 * Complements form_5500_sf table (small plans < 100 participants)
 *
 * Based on 2023 F_5500 data dictionary / file layout
 * Primary key: ACK_ID (same as 5500-SF for consistent joins)
 */

const { Client } = require('pg');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../../.env') });

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('❌ ERROR: NEON_CONNECTION_STRING not found in .env');
    process.exit(1);
}

async function createForm5500Table() {
    const client = new Client({ connectionString });

    try {
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        console.log('═'.repeat(80));
        console.log('CREATING FORM 5500 TABLE (LARGE PLANS)');
        console.log('═'.repeat(80));

        // Create form_5500 table
        console.log('\n1. Creating marketing.form_5500 table...');
        await client.query(`
            BEGIN;

            CREATE TABLE IF NOT EXISTS marketing.form_5500 (
                -- Primary key and system metadata
                id SERIAL PRIMARY KEY,
                ack_id VARCHAR(30) UNIQUE NOT NULL,
                company_unique_id TEXT REFERENCES marketing.company_master(company_unique_id),

                -- System metadata (DOL)
                filing_status VARCHAR(50),
                date_received DATE,
                form_type VARCHAR(10) DEFAULT '5500',
                form_year INT,
                form_plan_year_begin_date DATE,
                form_tax_prd DATE,

                -- Plan entity type
                type_plan_entity_cd VARCHAR(1),
                type_dfe_plan_entity_cd VARCHAR(1),

                -- Filing flags
                initial_filing_ind VARCHAR(1),
                amended_ind VARCHAR(1),
                final_filing_ind VARCHAR(1),
                short_plan_yr_ind VARCHAR(1),
                collective_bargain_ind VARCHAR(1),

                -- Sponsor/Company fields (SPONSOR_DFE_*)
                sponsor_dfe_ein VARCHAR(9) NOT NULL,
                sponsor_dfe_name VARCHAR(70),
                spons_dfe_dba_name VARCHAR(70),
                spons_dfe_care_of_name VARCHAR(70),

                -- Mailing address
                spons_dfe_mail_us_address1 VARCHAR(35),
                spons_dfe_mail_us_address2 VARCHAR(35),
                spons_dfe_mail_us_city VARCHAR(22),
                spons_dfe_mail_us_state VARCHAR(2),
                spons_dfe_mail_us_zip VARCHAR(12),

                -- Location address
                spons_dfe_loc_us_address1 VARCHAR(35),
                spons_dfe_loc_us_address2 VARCHAR(35),
                spons_dfe_loc_us_city VARCHAR(22),
                spons_dfe_loc_us_state VARCHAR(2),
                spons_dfe_loc_us_zip VARCHAR(12),

                -- Contact
                spons_dfe_phone_num VARCHAR(10),
                business_code VARCHAR(6),

                -- Plan-level fields
                plan_name VARCHAR(140),
                plan_number VARCHAR(3),
                plan_eff_date DATE,

                -- Plan type codes
                type_pension_bnft_code VARCHAR(40),
                type_welfare_bnft_code VARCHAR(40),

                -- Funding indicators
                funding_insurance_ind VARCHAR(1),
                funding_sec412_ind VARCHAR(1),
                funding_trust_ind VARCHAR(1),
                funding_gen_asset_ind VARCHAR(1),

                -- Benefit indicators
                benefit_insurance_ind VARCHAR(1),
                benefit_sec412_ind VARCHAR(1),
                benefit_trust_ind VARCHAR(1),
                benefit_gen_asset_ind VARCHAR(1),

                -- Participant counts
                tot_partcp_boy_cnt INT,
                tot_active_partcp_cnt INT,
                rtd_sep_partcp_rcvg_cnt INT,
                rtd_sep_partcp_fut_cnt INT,
                subtl_act_rtd_sep_cnt INT,
                benef_rcvg_bnft_cnt INT,
                tot_act_rtd_sep_benef_cnt INT,
                partcp_account_bal_cnt INT,
                sep_partcp_partl_vstd_cnt INT,
                contrib_emplrs_cnt INT,

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

                -- Admin info
                admin_name VARCHAR(70),
                admin_ein VARCHAR(9),
                admin_us_state VARCHAR(2),

                -- Raw payload for complete data
                raw_payload JSONB,

                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_form_5500_ack_id ON marketing.form_5500(ack_id);
            CREATE INDEX IF NOT EXISTS idx_form_5500_ein ON marketing.form_5500(sponsor_dfe_ein);
            CREATE INDEX IF NOT EXISTS idx_form_5500_company ON marketing.form_5500(company_unique_id);
            CREATE INDEX IF NOT EXISTS idx_form_5500_state ON marketing.form_5500(spons_dfe_mail_us_state);
            CREATE INDEX IF NOT EXISTS idx_form_5500_year ON marketing.form_5500(form_year);
            CREATE INDEX IF NOT EXISTS idx_form_5500_date_received ON marketing.form_5500(date_received);

            -- Composite index for company matching
            CREATE INDEX IF NOT EXISTS idx_form_5500_sponsor_state
            ON marketing.form_5500(LOWER(sponsor_dfe_name), spons_dfe_mail_us_state);

            -- GIN index for JSONB queries
            CREATE INDEX IF NOT EXISTS idx_form_5500_raw_payload_gin
            ON marketing.form_5500 USING gin(raw_payload);

            -- Partial index for Schedule A attached
            CREATE INDEX IF NOT EXISTS idx_form_5500_sch_a_attached
            ON marketing.form_5500(sch_a_attached_ind)
            WHERE sch_a_attached_ind = '1';

            -- Partial index for large participant counts
            CREATE INDEX IF NOT EXISTS idx_form_5500_large_plans
            ON marketing.form_5500(tot_active_partcp_cnt)
            WHERE tot_active_partcp_cnt >= 100;

            COMMIT;
        `);
        console.log('   ✓ Table created: marketing.form_5500');
        console.log('   ✓ 10 indexes created');

        // Add constraints
        console.log('\n2. Adding constraints...');
        try {
            await client.query(`
                BEGIN;

                -- Unique constraint on ACK_ID
                ALTER TABLE marketing.form_5500
                ADD CONSTRAINT IF NOT EXISTS uq_form_5500_ack_id UNIQUE (ack_id);

                COMMIT;
            `);
        } catch (e) {
            // Constraint might already exist
            console.log('   (constraints already exist or being added)');
        }

        try {
            await client.query(`
                -- CHECK constraint for EIN format (9 digits)
                ALTER TABLE marketing.form_5500
                ADD CONSTRAINT chk_form_5500_ein_format
                CHECK (sponsor_dfe_ein ~ '^[0-9]{9}$');
            `);
            console.log('   ✓ CHECK constraint: chk_form_5500_ein_format');
        } catch (e) {
            console.log('   (EIN constraint already exists)');
        }

        // Add column comments
        console.log('\n3. Adding column comments...');
        await client.query(`
            COMMENT ON TABLE marketing.form_5500 IS 'DOL Form 5500 for large plans (>=100 participants)';
            COMMENT ON COLUMN marketing.form_5500.ack_id IS 'DOL unique filing ID - primary key for all schedule joins';
            COMMENT ON COLUMN marketing.form_5500.sponsor_dfe_ein IS 'Employer Identification Number (9 digits)';
            COMMENT ON COLUMN marketing.form_5500.sponsor_dfe_name IS 'Plan sponsor name (company name from DOL)';
            COMMENT ON COLUMN marketing.form_5500.tot_active_partcp_cnt IS 'Total active participants at end of year';
            COMMENT ON COLUMN marketing.form_5500.type_pension_bnft_code IS 'Pension benefit type codes';
            COMMENT ON COLUMN marketing.form_5500.type_welfare_bnft_code IS 'Welfare benefit type codes';
            COMMENT ON COLUMN marketing.form_5500.form_type IS 'Always 5500 for regular form';
            COMMENT ON COLUMN marketing.form_5500.form_year IS 'Form year (not calendar year)';
            COMMENT ON COLUMN marketing.form_5500.raw_payload IS 'Complete raw CSV data from DOL';
        `);
        console.log('   ✓ Column comments added');

        // Create staging table
        console.log('\n4. Creating staging table...');
        await client.query(`
            BEGIN;

            DROP TABLE IF EXISTS marketing.form_5500_staging;

            CREATE TABLE IF NOT EXISTS marketing.form_5500_staging (
                ack_id TEXT,
                form_plan_year_begin_date TEXT,
                form_tax_prd TEXT,
                type_plan_entity_cd TEXT,
                type_dfe_plan_entity_cd TEXT,
                initial_filing_ind TEXT,
                amended_ind TEXT,
                final_filing_ind TEXT,
                short_plan_yr_ind TEXT,
                collective_bargain_ind TEXT,
                plan_name TEXT,
                plan_number TEXT,
                plan_eff_date TEXT,
                sponsor_dfe_ein TEXT,
                sponsor_dfe_name TEXT,
                spons_dfe_dba_name TEXT,
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
                tot_partcp_boy_cnt TEXT,
                tot_active_partcp_cnt TEXT,
                rtd_sep_partcp_rcvg_cnt TEXT,
                rtd_sep_partcp_fut_cnt TEXT,
                subtl_act_rtd_sep_cnt TEXT,
                benef_rcvg_bnft_cnt TEXT,
                tot_act_rtd_sep_benef_cnt TEXT,
                partcp_account_bal_cnt TEXT,
                sep_partcp_partl_vstd_cnt TEXT,
                contrib_emplrs_cnt TEXT,
                type_pension_bnft_code TEXT,
                type_welfare_bnft_code TEXT,
                funding_insurance_ind TEXT,
                funding_sec412_ind TEXT,
                funding_trust_ind TEXT,
                funding_gen_asset_ind TEXT,
                benefit_insurance_ind TEXT,
                benefit_sec412_ind TEXT,
                benefit_trust_ind TEXT,
                benefit_gen_asset_ind TEXT,
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
                admin_name TEXT,
                admin_ein TEXT,
                admin_us_state TEXT,
                filing_status TEXT,
                date_received TEXT,
                form_year TEXT
            );

            COMMENT ON TABLE marketing.form_5500_staging IS 'Staging table for Form 5500 CSV imports';

            COMMIT;
        `);
        console.log('   ✓ Staging table created: marketing.form_5500_staging');

        // Check if match function exists, create if not
        console.log('\n5. Checking company matching function...');
        const funcExists = await client.query(`
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'marketing'
                AND p.proname = 'match_5500_to_company'
            ) as exists;
        `);

        if (!funcExists.rows[0].exists) {
            console.log('   Creating company matching function...');
            await client.query(`
                CREATE OR REPLACE FUNCTION marketing.match_5500_to_company(
                    p_sponsor_name TEXT,
                    p_city TEXT,
                    p_state TEXT
                )
                RETURNS TEXT AS $$
                DECLARE
                    v_company_uid TEXT;
                BEGIN
                    -- Try exact name + state match first
                    SELECT company_unique_id INTO v_company_uid
                    FROM marketing.company_master
                    WHERE LOWER(company_name) = LOWER(TRIM(p_sponsor_name))
                    AND address_state = p_state
                    LIMIT 1;

                    IF v_company_uid IS NOT NULL THEN
                        RETURN v_company_uid;
                    END IF;

                    -- Try fuzzy name match with state
                    SELECT company_unique_id INTO v_company_uid
                    FROM marketing.company_master
                    WHERE address_state = p_state
                    AND (
                        LOWER(company_name) LIKE LOWER(TRIM(p_sponsor_name)) || '%'
                        OR LOWER(TRIM(p_sponsor_name)) LIKE LOWER(company_name) || '%'
                    )
                    LIMIT 1;

                    RETURN v_company_uid;
                END;
                $$ LANGUAGE plpgsql;
            `);
            console.log('   ✓ Function created: marketing.match_5500_to_company()');
        } else {
            console.log('   ✓ Function already exists: marketing.match_5500_to_company()');
        }

        // Create processing procedure
        console.log('\n6. Creating processing procedure...');
        await client.query(`
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
                        v_row.sponsor_dfe_name,
                        v_row.spons_dfe_mail_us_city,
                        v_row.spons_dfe_mail_us_state
                    );

                    IF v_company_uid IS NOT NULL THEN
                        v_matched := v_matched + 1;
                    END IF;

                    -- Insert into main table
                    INSERT INTO marketing.form_5500 (
                        ack_id,
                        company_unique_id,
                        form_plan_year_begin_date,
                        form_tax_prd,
                        type_plan_entity_cd,
                        type_dfe_plan_entity_cd,
                        initial_filing_ind,
                        amended_ind,
                        final_filing_ind,
                        short_plan_yr_ind,
                        collective_bargain_ind,
                        plan_name,
                        plan_number,
                        plan_eff_date,
                        sponsor_dfe_ein,
                        sponsor_dfe_name,
                        spons_dfe_dba_name,
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
                        tot_partcp_boy_cnt,
                        tot_active_partcp_cnt,
                        rtd_sep_partcp_rcvg_cnt,
                        rtd_sep_partcp_fut_cnt,
                        subtl_act_rtd_sep_cnt,
                        benef_rcvg_bnft_cnt,
                        tot_act_rtd_sep_benef_cnt,
                        partcp_account_bal_cnt,
                        sep_partcp_partl_vstd_cnt,
                        contrib_emplrs_cnt,
                        type_pension_bnft_code,
                        type_welfare_bnft_code,
                        funding_insurance_ind,
                        funding_sec412_ind,
                        funding_trust_ind,
                        funding_gen_asset_ind,
                        benefit_insurance_ind,
                        benefit_sec412_ind,
                        benefit_trust_ind,
                        benefit_gen_asset_ind,
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
                        admin_name,
                        admin_ein,
                        admin_us_state,
                        filing_status,
                        date_received,
                        form_year
                    ) VALUES (
                        v_row.ack_id,
                        v_company_uid,
                        NULLIF(v_row.form_plan_year_begin_date, '')::DATE,
                        NULLIF(v_row.form_tax_prd, '')::DATE,
                        v_row.type_plan_entity_cd,
                        v_row.type_dfe_plan_entity_cd,
                        v_row.initial_filing_ind,
                        v_row.amended_ind,
                        v_row.final_filing_ind,
                        v_row.short_plan_yr_ind,
                        v_row.collective_bargain_ind,
                        v_row.plan_name,
                        v_row.plan_number,
                        NULLIF(v_row.plan_eff_date, '')::DATE,
                        v_row.sponsor_dfe_ein,
                        v_row.sponsor_dfe_name,
                        v_row.spons_dfe_dba_name,
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
                        NULLIF(REGEXP_REPLACE(v_row.tot_partcp_boy_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.tot_active_partcp_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.rtd_sep_partcp_rcvg_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.rtd_sep_partcp_fut_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.subtl_act_rtd_sep_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.benef_rcvg_bnft_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.tot_act_rtd_sep_benef_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.partcp_account_bal_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.sep_partcp_partl_vstd_cnt, '[^0-9]', '', 'g'), '')::INT,
                        NULLIF(REGEXP_REPLACE(v_row.contrib_emplrs_cnt, '[^0-9]', '', 'g'), '')::INT,
                        v_row.type_pension_bnft_code,
                        v_row.type_welfare_bnft_code,
                        v_row.funding_insurance_ind,
                        v_row.funding_sec412_ind,
                        v_row.funding_trust_ind,
                        v_row.funding_gen_asset_ind,
                        v_row.benefit_insurance_ind,
                        v_row.benefit_sec412_ind,
                        v_row.benefit_trust_ind,
                        v_row.benefit_gen_asset_ind,
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
                        v_row.admin_name,
                        v_row.admin_ein,
                        v_row.admin_us_state,
                        v_row.filing_status,
                        NULLIF(v_row.date_received, '')::DATE,
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

                    -- Progress notification every 50k records
                    IF v_count % 50000 = 0 THEN
                        RAISE NOTICE 'Processed % Form 5500 records...', v_count;
                    END IF;
                END LOOP;

                RAISE NOTICE 'Processed % Form 5500 records, matched % to existing companies', v_count, v_matched;

                -- Clear staging table
                TRUNCATE marketing.form_5500_staging;
            END;
            $$;

            COMMENT ON PROCEDURE marketing.process_5500_staging IS 'Process Form 5500 staging table and match to companies';
        `);
        console.log('   ✓ Procedure created: marketing.process_5500_staging()');

        // Verification
        console.log('\n' + '═'.repeat(80));
        console.log('VERIFICATION');
        console.log('═'.repeat(80));

        const indexes = await client.query(`
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'marketing'
            AND tablename = 'form_5500'
            ORDER BY indexname;
        `);

        console.log('\nIndexes on marketing.form_5500:');
        indexes.rows.forEach(row => {
            console.log(`  ✓ ${row.indexname}`);
        });

        console.log('\n' + '═'.repeat(80));
        console.log('FORM 5500 TABLE CREATION COMPLETE');
        console.log('═'.repeat(80));
        console.log('\n✅ Ready to import DOL Form 5500 CSV data');
        console.log('\nNext steps:');
        console.log('1. Run: python ctb/sys/enrichment/import_5500.py');
        console.log('2. Import: \\COPY marketing.form_5500_staging FROM \'output/form_5500_2023_staging.csv\' CSV HEADER;');
        console.log('3. Process: CALL marketing.process_5500_staging();');
        console.log('4. Verify: SELECT COUNT(*) FROM marketing.form_5500;');

    } catch (err) {
        console.error('\n❌ ERROR:', err.message);
        console.error(err.stack);
        process.exit(1);
    } finally {
        await client.end();
    }
}

createForm5500Table();
