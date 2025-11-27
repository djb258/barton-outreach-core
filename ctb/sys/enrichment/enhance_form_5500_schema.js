#!/usr/bin/env node
/**
 * Form 5500 Schema Enhancement
 *
 * Based on DOL Form 5500 Dataset Guide:
 * - ACK_ID is the unique identifier for each filing (primary key for joining)
 * - Need unique constraint on ACK_ID to prevent duplicate filings
 * - Add indexes for performance on common lookup patterns
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

if (!connectionString) {
    console.error('❌ ERROR: NEON_CONNECTION_STRING not found in .env');
    process.exit(1);
}

async function enhanceSchema() {
    const client = new Client({ connectionString });

    try {
        await client.connect();
        console.log('✓ Connected to Neon PostgreSQL\n');

        console.log('='.repeat(80));
        console.log('ENHANCING FORM 5500 SCHEMA FOR DOL DATASET');
        console.log('='.repeat(80));

        // Enhancement 1: Add unique constraint on ACK_ID
        console.log('\n1. Adding unique constraint on ack_id (DOL unique filing ID)...');
        try {
            await client.query(`
                ALTER TABLE marketing.form_5500
                ADD CONSTRAINT uq_form_5500_ack_id UNIQUE (ack_id);
            `);
            console.log('   ✓ Unique constraint added: uq_form_5500_ack_id');
        } catch (err) {
            if (err.message.includes('already exists')) {
                console.log('   ✓ Unique constraint already exists');
            } else {
                throw err;
            }
        }

        // Enhancement 2: Add composite index for sponsor matching
        console.log('\n2. Adding composite index for sponsor name matching...');
        try {
            await client.query(`
                CREATE INDEX IF NOT EXISTS idx_5500_sponsor_state
                ON marketing.form_5500(LOWER(sponsor_name), state);
            `);
            console.log('   ✓ Index created: idx_5500_sponsor_state');
        } catch (err) {
            console.log(`   ⚠ Warning: ${err.message}`);
        }

        // Enhancement 3: Add index on date_received for temporal queries
        console.log('\n3. Adding index on date_received...');
        try {
            await client.query(`
                CREATE INDEX IF NOT EXISTS idx_5500_date_received
                ON marketing.form_5500(date_received);
            `);
            console.log('   ✓ Index created: idx_5500_date_received');
        } catch (err) {
            console.log(`   ⚠ Warning: ${err.message}`);
        }

        // Enhancement 4: Add index on participant_count for filtering
        console.log('\n4. Adding index on participant_count...');
        try {
            await client.query(`
                CREATE INDEX IF NOT EXISTS idx_5500_participant_count
                ON marketing.form_5500(participant_count)
                WHERE participant_count IS NOT NULL;
            `);
            console.log('   ✓ Partial index created: idx_5500_participant_count');
        } catch (err) {
            console.log(`   ⚠ Warning: ${err.message}`);
        }

        // Enhancement 5: Add GIN index on raw_payload for JSONB queries
        console.log('\n5. Adding GIN index on raw_payload (JSONB)...');
        try {
            await client.query(`
                CREATE INDEX IF NOT EXISTS idx_5500_raw_payload_gin
                ON marketing.form_5500 USING gin(raw_payload);
            `);
            console.log('   ✓ GIN index created: idx_5500_raw_payload_gin');
        } catch (err) {
            console.log(`   ⚠ Warning: ${err.message}`);
        }

        // Enhancement 6: Add check constraint for valid EIN format
        console.log('\n6. Adding check constraint for EIN format (9 digits)...');
        try {
            await client.query(`
                ALTER TABLE marketing.form_5500
                ADD CONSTRAINT chk_form_5500_ein_format
                CHECK (ein ~ '^[0-9]{9}$');
            `);
            console.log('   ✓ Check constraint added: chk_form_5500_ein_format');
        } catch (err) {
            if (err.message.includes('already exists')) {
                console.log('   ✓ Check constraint already exists');
            } else {
                console.log(`   ⚠ Warning: ${err.message}`);
            }
        }

        // Enhancement 7: Add comments for documentation
        console.log('\n7. Adding column comments for documentation...');
        await client.query(`
            COMMENT ON COLUMN marketing.form_5500.ack_id IS 'DOL unique filing ID - use for joining schedules';
            COMMENT ON COLUMN marketing.form_5500.ein IS 'Employer Identification Number (9 digits) - links to IRS';
            COMMENT ON COLUMN marketing.form_5500.sponsor_name IS 'Plan sponsor name (company name from DOL filing)';
            COMMENT ON COLUMN marketing.form_5500.participant_count IS 'Number of plan participants (employees in plan)';
            COMMENT ON COLUMN marketing.form_5500.total_assets IS 'Total plan assets in dollars';
            COMMENT ON COLUMN marketing.form_5500.filing_year IS 'Form year (not calendar year)';
            COMMENT ON COLUMN marketing.form_5500.raw_payload IS 'Complete raw CSV data from DOL (for schedules A-I)';
        `);
        console.log('   ✓ Column comments added');

        // Verification
        console.log('\n' + '='.repeat(80));
        console.log('VERIFICATION');
        console.log('='.repeat(80));

        const verification = await client.query(`
            SELECT
                constraint_name,
                constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'marketing'
            AND table_name = 'form_5500'
            AND constraint_type IN ('UNIQUE', 'CHECK')
            ORDER BY constraint_name;
        `);

        console.log('\nConstraints on marketing.form_5500:');
        verification.rows.forEach(row => {
            console.log(`  ✓ ${row.constraint_name} (${row.constraint_type})`);
        });

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

        console.log('\n' + '='.repeat(80));
        console.log('SCHEMA ENHANCEMENT COMPLETE');
        console.log('='.repeat(80));
        console.log('\n✅ Ready to import DOL Form 5500 CSV data');
        console.log('\nNext steps:');
        console.log('1. Download CSV from: https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin');
        console.log('2. Import to staging: COPY marketing.form_5500_staging FROM \'5500_data.csv\' CSV HEADER;');
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

enhanceSchema();
