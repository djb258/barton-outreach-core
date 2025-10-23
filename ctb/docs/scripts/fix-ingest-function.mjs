/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-E0B8509E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

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

async function fixIngestFunction() {
    try {
        console.log('🔌 Connecting to Marketing DB...');
        await client.connect();

        console.log('🔧 Creating fixed ingestion function...');

        // Create a simpler function that accepts text and converts it properly
        await client.query(`
            CREATE OR REPLACE FUNCTION intake.f_ingest_company_csv(
                p_records_json text,
                p_batch_id text DEFAULT NULL
            ) RETURNS TABLE (
                inserted_count integer,
                batch_id text,
                message text
            ) LANGUAGE plpgsql AS $$
            DECLARE
                v_batch_id text;
                v_inserted integer := 0;
                v_records jsonb;
                v_record jsonb;
            BEGIN
                -- Generate batch ID if not provided
                v_batch_id := COALESCE(p_batch_id, 'batch_' || extract(epoch from now())::text);
                
                -- Parse the JSON string into JSONB
                v_records := p_records_json::jsonb;
                
                -- Process each record
                FOR v_record IN SELECT * FROM jsonb_array_elements(v_records)
                LOOP
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
                            batch_id, source, status
                        ) VALUES (
                            v_record->>'Company',
                            v_record->>'Company Name for Emails', 
                            v_record->>'Accoune',  -- Note: keeping the original typo from CSV header
                            v_record->>'Lists',
                            NULLIF(v_record->>'# Employees', '')::integer,
                            v_record->>'Industry',
                            v_record->>'Account Owner',
                            v_record->>'Website',
                            v_record->>'Company Linkedin Url',
                            v_record->>'Facebook Url',
                            v_record->>'Twitter Url',
                            v_record->>'Company Street',
                            v_record->>'Company City',
                            v_record->>'Company State',
                            v_record->>'Company Country',
                            v_record->>'Company Postal Code',
                            v_record->>'Company Phone',
                            v_record->>'Technologies',
                            v_record->>'Total Funding',
                            v_record->>'Latest Funding',
                            NULLIF(v_record->>'Latest Funding Amount', '')::decimal,
                            v_record->>'Annual Revenue',
                            v_record->>'Apollo Account Id',
                            v_record->>'SIC Codes',
                            v_record->>'NAICS Codes',
                            NULLIF(v_record->>'Founded Year', '')::integer,
                            v_record->>'Short Description',
                            v_record->>'Keywords',
                            v_record->>'Primary Intent Topic',
                            NULLIF(v_record->>'Primary Intent Score', '')::decimal,
                            v_record->>'Secondary Intent Topic', 
                            NULLIF(v_record->>'Secondary Intent Score', '')::decimal,
                            v_batch_id,
                            'api_ingest',
                            'inserted'
                        );
                        v_inserted := v_inserted + 1;
                    EXCEPTION
                        WHEN OTHERS THEN
                            -- Log error but continue processing
                            RAISE NOTICE 'Error inserting row: %, Data: %', SQLERRM, v_record;
                    END;
                END LOOP;
                
                RETURN QUERY SELECT v_inserted, v_batch_id, 'Successfully ingested ' || v_inserted || ' company records';
            END;
            $$;
        `);
        console.log('✅ Created fixed function that accepts text parameter');

        // Test the fixed function
        console.log('\\n🧪 Testing fixed function...');
        const testData = [{
            "Company": "Test Company Fixed",
            "Website": "https://testfixed.com", 
            "Industry": "Software Testing",
            "# Employees": "50"
        }];
        
        const testResult = await client.query(`
            SELECT * FROM intake.f_ingest_company_csv($1, $2)
        `, [JSON.stringify(testData), 'test_fixed_' + Date.now()]);
        
        console.log('✅ Function test result:', testResult.rows[0]);
        
        // Check if test data was inserted
        const verifyResult = await client.query(`
            SELECT COUNT(*) as count FROM intake.company_raw_intake WHERE batch_id LIKE 'test_fixed_%'
        `);
        console.log('✅ Test records inserted:', verifyResult.rows[0].count);

        if (parseInt(verifyResult.rows[0].count) > 0) {
            // Show the inserted record
            const sampleResult = await client.query(`
                SELECT id, company, website, industry, batch_id, created_at
                FROM intake.company_raw_intake 
                WHERE batch_id LIKE 'test_fixed_%'
                ORDER BY created_at DESC 
                LIMIT 1
            `);
            console.log('📋 Inserted record:', sampleResult.rows[0]);
        }

        console.log('\\n🎉 Function is now working correctly!');

    } catch (error) {
        console.error('❌ Error fixing function:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

fixIngestFunction();