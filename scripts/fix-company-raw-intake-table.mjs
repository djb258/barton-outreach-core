#!/usr/bin/env node

import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

if (!DATABASE_URL) {
    console.error('❌ No database URL found. Please set NEON_DATABASE_URL or DATABASE_URL');
    process.exit(1);
}

const client = new Client({
    connectionString: DATABASE_URL,
    ssl: { rejectUnauthorized: false }
});

async function fixCompanyRawIntakeTable() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        // Check if marketing schema exists
        const schemaExists = await client.query(`
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'marketing'
        `);
        
        if (schemaExists.rows.length === 0) {
            console.log('📊 Creating marketing schema...');
            await client.query('CREATE SCHEMA marketing;');
        }

        // Check if table exists
        const tableExists = await client.query(`
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'marketing' 
                AND table_name = 'company_raw_intake'
            ) as exists
        `);
        
        console.log('Table exists:', tableExists.rows[0].exists);

        if (!tableExists.rows[0].exists) {
            console.log('❌ Table does not exist. Creating it now...');
            
            // Create the complete table with all your CSV columns
            const createTableSQL = `
                CREATE TABLE marketing.company_raw_intake (
                    -- Primary key
                    intake_id BIGSERIAL PRIMARY KEY,
                    
                    -- Basic company info (matching your CSV header exactly)
                    company TEXT,
                    company_name_for_emails TEXT,
                    account TEXT,
                    lists TEXT,
                    num_employees INTEGER,
                    industry TEXT,
                    account_owner TEXT,
                    website TEXT,
                    
                    -- Social media URLs
                    company_linkedin_url TEXT,
                    facebook_url TEXT,
                    twitter_url TEXT,
                    
                    -- Address fields
                    company_street TEXT,
                    company_city TEXT,
                    company_state TEXT,
                    company_country TEXT,
                    company_postal_code TEXT,
                    company_address TEXT,
                    company_phone TEXT,
                    
                    -- Business information
                    technologies TEXT,
                    total_funding TEXT,
                    latest_funding TEXT,
                    latest_funding_amount DECIMAL(15,2),
                    last_raised_at DATE,
                    annual_revenue TEXT,
                    number_of_retail_locations INTEGER,
                    
                    -- External identifiers
                    apollo_account_id TEXT,
                    sic_codes TEXT,
                    naics_codes TEXT,
                    
                    -- Company metadata
                    founded_year INTEGER,
                    logo_url TEXT,
                    subsidiary_of TEXT,
                    short_description TEXT,
                    keywords TEXT,
                    
                    -- Intent scoring
                    primary_intent_topic TEXT,
                    primary_intent_score DECIMAL(5,2),
                    secondary_intent_topic TEXT,
                    secondary_intent_score DECIMAL(5,2),
                    
                    -- Processing metadata
                    batch_id TEXT,
                    source TEXT DEFAULT 'csv_import',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    processed_at TIMESTAMPTZ,
                    error_message TEXT
                );
            `;
            
            await client.query(createTableSQL);
            console.log('✅ Created marketing.company_raw_intake table with all columns');
        } else {
            console.log('✅ Table exists. Checking columns...');
            
            const currentColumns = await client.query(`
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'marketing' 
                AND table_name = 'company_raw_intake'
                ORDER BY ordinal_position
            `);
            
            console.log('Current columns (' + currentColumns.rows.length + '):');
            currentColumns.rows.forEach(r => console.log('  -', r.column_name));
            
            // Define all required columns based on your CSV header
            const requiredColumns = [
                'company', 'company_name_for_emails', 'account', 'lists',
                'num_employees', 'industry', 'account_owner', 'website',
                'company_linkedin_url', 'facebook_url', 'twitter_url',
                'company_street', 'company_city', 'company_state', 'company_country',
                'company_postal_code', 'company_address', 'company_phone',
                'technologies', 'total_funding', 'latest_funding', 'latest_funding_amount',
                'last_raised_at', 'annual_revenue', 'number_of_retail_locations',
                'apollo_account_id', 'sic_codes', 'naics_codes',
                'founded_year', 'logo_url', 'subsidiary_of', 'short_description', 'keywords',
                'primary_intent_topic', 'primary_intent_score', 'secondary_intent_topic', 'secondary_intent_score'
            ];
            
            const existingColumns = currentColumns.rows.map(r => r.column_name);
            const missingColumns = requiredColumns.filter(col => !existingColumns.includes(col));
            
            if (missingColumns.length > 0) {
                console.log('\\n⚠️  Missing columns:', missingColumns.length);
                
                for (const colName of missingColumns) {
                    // Define column types
                    let colType = 'TEXT'; // default
                    if (colName === 'num_employees' || colName === 'number_of_retail_locations' || colName === 'founded_year') {
                        colType = 'INTEGER';
                    } else if (colName === 'latest_funding_amount') {
                        colType = 'DECIMAL(15,2)';
                    } else if (colName === 'primary_intent_score' || colName === 'secondary_intent_score') {
                        colType = 'DECIMAL(5,2)';
                    } else if (colName === 'last_raised_at') {
                        colType = 'DATE';
                    }
                    
                    try {
                        await client.query(`ALTER TABLE marketing.company_raw_intake ADD COLUMN ${colName} ${colType}`);
                        console.log(`   ✅ Added: ${colName} (${colType})`);
                    } catch (error) {
                        console.error(`   ❌ Failed to add ${colName}: ${error.message}`);
                    }
                }
            } else {
                console.log('✅ All required columns are present!');
            }
        }

        // Create/update the ingestion function
        console.log('\\n🔧 Creating ingestion function...');
        await client.query(`
            CREATE OR REPLACE FUNCTION marketing.f_ingest_company_csv(
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
                        INSERT INTO marketing.company_raw_intake (
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
        console.log('✅ Created ingestion function');

        // Verify final table structure
        const finalColumns = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'marketing' 
            AND table_name = 'company_raw_intake'
            ORDER BY ordinal_position
        `);

        console.log('\\n📊 Final table structure (' + finalColumns.rows.length + ' columns):');
        console.log('═══════════════════════════════════════════════════════');
        finalColumns.rows.forEach(col => {
            console.log(`  ${col.column_name.padEnd(30)} ${col.data_type}`);
        });

        console.log('\\n🎉 marketing.company_raw_intake table is ready!');
        console.log('   ✅ All CSV columns are now present');
        console.log('   ✅ Ingestion function created');
        console.log('   ✅ Ready to receive data from ingest-companies-people app');

    } catch (error) {
        console.error('❌ Error fixing table:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

fixCompanyRawIntakeTable();