#!/usr/bin/env node

import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

if (!DATABASE_URL) {
    console.error('❌ No database URL found. Please set NEON_DATABASE_URL');
    process.exit(1);
}

const client = new Client({
    connectionString: DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function addColumnsToIntakeCompanyRaw() {
    try {
        console.log('🔌 Connecting to Marketing DB...');
        await client.connect();

        console.log('🔧 Adding all CSV columns to intake.company_raw_intake...');

        // Define all the columns from your CSV header
        const columnsToAdd = [
            // Company basic info
            { name: 'company', type: 'TEXT' },
            { name: 'company_name_for_emails', type: 'TEXT' },
            { name: 'account', type: 'TEXT' },
            { name: 'lists', type: 'TEXT' },
            { name: 'num_employees', type: 'INTEGER' },
            { name: 'industry', type: 'TEXT' },
            { name: 'account_owner', type: 'TEXT' },
            { name: 'website', type: 'TEXT' },
            
            // Social URLs
            { name: 'company_linkedin_url', type: 'TEXT' },
            { name: 'facebook_url', type: 'TEXT' },
            { name: 'twitter_url', type: 'TEXT' },
            
            // Address information
            { name: 'company_street', type: 'TEXT' },
            { name: 'company_city', type: 'TEXT' },
            { name: 'company_state', type: 'TEXT' },
            { name: 'company_country', type: 'TEXT' },
            { name: 'company_postal_code', type: 'TEXT' },
            { name: 'company_address', type: 'TEXT' },
            { name: 'company_phone', type: 'TEXT' },
            
            // Business information
            { name: 'technologies', type: 'TEXT' },
            { name: 'total_funding', type: 'TEXT' },
            { name: 'latest_funding', type: 'TEXT' },
            { name: 'latest_funding_amount', type: 'DECIMAL(15,2)' },
            { name: 'last_raised_at', type: 'DATE' },
            { name: 'annual_revenue', type: 'TEXT' },
            { name: 'number_of_retail_locations', type: 'INTEGER' },
            
            // External identifiers
            { name: 'apollo_account_id', type: 'TEXT' },
            { name: 'sic_codes', type: 'TEXT' },
            { name: 'naics_codes', type: 'TEXT' },
            
            // Company metadata
            { name: 'founded_year', type: 'INTEGER' },
            { name: 'logo_url', type: 'TEXT' },
            { name: 'subsidiary_of', type: 'TEXT' },
            { name: 'short_description', type: 'TEXT' },
            { name: 'keywords', type: 'TEXT' },
            
            // Intent data
            { name: 'primary_intent_topic', type: 'TEXT' },
            { name: 'primary_intent_score', type: 'DECIMAL(5,2)' },
            { name: 'secondary_intent_topic', type: 'TEXT' },
            { name: 'secondary_intent_score', type: 'DECIMAL(5,2)' },
            
            // Processing fields
            { name: 'batch_id', type: 'TEXT' },
            { name: 'source', type: 'TEXT DEFAULT \'csv_import\'' },
            { name: 'status', type: 'TEXT DEFAULT \'pending\'' },
            { name: 'created_at', type: 'TIMESTAMPTZ DEFAULT NOW()' },
            { name: 'updated_at', type: 'TIMESTAMPTZ DEFAULT NOW()' },
            { name: 'processed_at', type: 'TIMESTAMPTZ' },
            { name: 'error_message', type: 'TEXT' }
        ];

        let addedCount = 0;
        let errorCount = 0;

        for (const col of columnsToAdd) {
            try {
                const alterQuery = `ALTER TABLE intake.company_raw_intake ADD COLUMN IF NOT EXISTS ${col.name} ${col.type}`;
                await client.query(alterQuery);
                console.log(`   ✅ Added: ${col.name} (${col.type})`);
                addedCount++;
            } catch (error) {
                console.error(`   ❌ Failed to add ${col.name}: ${error.message}`);
                errorCount++;
            }
        }

        console.log(`\\n📊 Column addition complete:`);
        console.log(`   ✅ Successfully added: ${addedCount} columns`);
        console.log(`   ❌ Failed to add: ${errorCount} columns`);

        // Verify final structure
        const finalColumns = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'intake' 
            AND table_name = 'company_raw_intake'
            ORDER BY ordinal_position
        `);

        console.log(`\\n📋 Final table structure (${finalColumns.rows.length} columns):`);
        console.log('═══════════════════════════════════════════════════════');
        finalColumns.rows.forEach(col => {
            console.log(`  ${col.column_name.padEnd(30)} ${col.data_type}`);
        });

        // Create an ingestion function for intake schema
        console.log('\\n🔧 Creating ingestion function for intake schema...');
        await client.query(`
            CREATE OR REPLACE FUNCTION intake.f_ingest_company_csv(
                p_rows jsonb[],
                p_batch_id text DEFAULT NULL
            ) RETURNS TABLE (
                inserted_count integer,
                batch_id text,
                message text
            ) LANGUAGE plpgsql AS $$
            DECLARE
                v_batch_id text;
                v_inserted integer := 0;
                v_row jsonb;
            BEGIN
                -- Generate batch ID if not provided
                v_batch_id := COALESCE(p_batch_id, 'batch_' || extract(epoch from now())::text);
                
                -- Process each row
                FOREACH v_row IN ARRAY p_rows LOOP
                    BEGIN
                        INSERT INTO intake.company_raw_intake (
                            company, company_name_for_emails, account, lists,
                            num_employees, industry, account_owner, website,
                            company_linkedin_url, facebook_url, twitter_url,
                            company_street, company_city, company_state, company_country,
                            company_postal_code, company_phone,
                            technologies, total_funding, latest_funding, latest_funding_amount,
                            annual_revenue, apollo_account_id, sic_codes, naics_codes,
                            founded_year, short_description, keywords,
                            primary_intent_topic, primary_intent_score,
                            secondary_intent_topic, secondary_intent_score,
                            batch_id
                        ) VALUES (
                            v_row->>'Company',
                            v_row->>'Company Name for Emails', 
                            v_row->>'Account',
                            v_row->>'Lists',
                            NULLIF(v_row->>'# Employees', '')::integer,
                            v_row->>'Industry',
                            v_row->>'Account Owner',
                            v_row->>'Website',
                            v_row->>'Company Linkedin Url',
                            v_row->>'Facebook Url',
                            v_row->>'Twitter Url',
                            v_row->>'Company Street',
                            v_row->>'Company City',
                            v_row->>'Company State',
                            v_row->>'Company Country',
                            v_row->>'Company Postal Code',
                            v_row->>'Company Phone',
                            v_row->>'Technologies',
                            v_row->>'Total Funding',
                            v_row->>'Latest Funding',
                            NULLIF(v_row->>'Latest Funding Amount', '')::decimal,
                            v_row->>'Annual Revenue',
                            v_row->>'Apollo Account Id',
                            v_row->>'SIC Codes',
                            v_row->>'NAICS Codes',
                            NULLIF(v_row->>'Founded Year', '')::integer,
                            v_row->>'Short Description',
                            v_row->>'Keywords',
                            v_row->>'Primary Intent Topic',
                            NULLIF(v_row->>'Primary Intent Score', '')::decimal,
                            v_row->>'Secondary Intent Topic', 
                            NULLIF(v_row->>'Secondary Intent Score', '')::decimal,
                            v_batch_id
                        );
                        v_inserted := v_inserted + 1;
                    EXCEPTION
                        WHEN OTHERS THEN
                            -- Log error but continue processing
                            RAISE NOTICE 'Error inserting row: %', SQLERRM;
                    END;
                END LOOP;
                
                RETURN QUERY SELECT v_inserted, v_batch_id, 'Successfully ingested ' || v_inserted || ' company records';
            END;
            $$;
        `);
        console.log('✅ Created intake.f_ingest_company_csv() function');

        console.log('\\n🎉 intake.company_raw_intake table is ready!');
        console.log('   ✅ All CSV columns added to intake schema');
        console.log('   ✅ Function: intake.f_ingest_company_csv()');
        console.log('   ✅ Ready to receive data from ingest-companies-people app');

    } catch (error) {
        console.error('❌ Error adding columns:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

addColumnsToIntakeCompanyRaw();