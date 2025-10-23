/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-60AFC587
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

import { Client } from 'pg';
import dotenv from 'dotenv';

// Load environment variables
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

async function addCompanyRawIntakeColumns() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        console.log('📊 Creating marketing.company_raw_intake table with all columns...');

        // First create the marketing schema if it doesn't exist
        await client.query(`CREATE SCHEMA IF NOT EXISTS marketing;`);

        // Create the company_raw_intake table with all the columns from your CSV header
        const createTableQuery = `
            CREATE TABLE IF NOT EXISTS marketing.company_raw_intake (
                -- Primary key
                intake_id BIGSERIAL PRIMARY KEY,
                
                -- Company basic info
                company TEXT,
                company_name_for_emails TEXT,
                account TEXT,
                lists TEXT,
                
                -- Company details
                num_employees INTEGER,
                industry TEXT,
                account_owner TEXT,
                website TEXT,
                company_linkedin_url TEXT,
                facebook_url TEXT,
                twitter_url TEXT,
                
                -- Address information
                company_street TEXT,
                company_city TEXT,
                company_state TEXT,
                company_country TEXT,
                company_postal_code TEXT,
                company_address TEXT,
                
                -- Contact info
                company_phone TEXT,
                
                -- Business info
                technologies TEXT,
                total_funding TEXT,
                latest_funding TEXT,
                latest_funding_amount DECIMAL(15,2),
                last_raised_at DATE,
                annual_revenue TEXT,
                number_of_retail_locations INTEGER,
                
                -- External IDs and codes
                apollo_account_id TEXT,
                sic_codes TEXT,
                naics_codes TEXT,
                
                -- Company metadata
                founded_year INTEGER,
                logo_url TEXT,
                subsidiary_of TEXT,
                short_description TEXT,
                keywords TEXT,
                
                -- Intent data
                primary_intent_topic TEXT,
                primary_intent_score DECIMAL(5,2),
                secondary_intent_topic TEXT,
                secondary_intent_score DECIMAL(5,2),
                
                -- Tracking fields
                batch_id TEXT,
                source TEXT DEFAULT 'csv_import',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                processed_at TIMESTAMPTZ,
                error_message TEXT
            );
        `;

        await client.query(createTableQuery);
        console.log('✅ Created marketing.company_raw_intake table');

        // Create indexes for better performance
        console.log('🔧 Creating indexes...');
        
        const indexes = [
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_company ON marketing.company_raw_intake(company);',
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_website ON marketing.company_raw_intake(website);',
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_status ON marketing.company_raw_intake(status);',
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_batch_id ON marketing.company_raw_intake(batch_id);',
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_created_at ON marketing.company_raw_intake(created_at);',
            'CREATE INDEX IF NOT EXISTS idx_company_raw_intake_apollo_id ON marketing.company_raw_intake(apollo_account_id);'
        ];

        for (const indexQuery of indexes) {
            await client.query(indexQuery);
        }
        console.log('✅ Created indexes');

        // Add update trigger for updated_at
        await client.query(`
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        `);

        await client.query(`
            DROP TRIGGER IF EXISTS update_company_raw_intake_updated_at ON marketing.company_raw_intake;
            
            CREATE TRIGGER update_company_raw_intake_updated_at 
            BEFORE UPDATE ON marketing.company_raw_intake
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        `);
        console.log('✅ Created update trigger');

        // Verify the table structure
        const columnsResult = await client.query(`
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'marketing' 
            AND table_name = 'company_raw_intake'
            ORDER BY ordinal_position;
        `);

        console.log('\n📋 Table structure created:');
        console.log('══════════════════════════════════════════');
        columnsResult.rows.forEach(col => {
            console.log(`  ${col.column_name.padEnd(30)} ${col.data_type.padEnd(20)} ${col.is_nullable}`);
        });

        // Create a function to ingest CSV data into this table
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
                    INSERT INTO marketing.company_raw_intake (
                        company,
                        company_name_for_emails,
                        account,
                        lists,
                        num_employees,
                        industry,
                        account_owner,
                        website,
                        company_linkedin_url,
                        facebook_url,
                        twitter_url,
                        company_street,
                        company_city,
                        company_state,
                        company_country,
                        company_postal_code,
                        company_phone,
                        technologies,
                        total_funding,
                        latest_funding,
                        latest_funding_amount,
                        annual_revenue,
                        apollo_account_id,
                        sic_codes,
                        naics_codes,
                        founded_year,
                        short_description,
                        keywords,
                        batch_id
                    ) VALUES (
                        v_row->>'Company',
                        v_row->>'Company Name for Emails',
                        v_row->>'Account',
                        v_row->>'Lists',
                        (v_row->>'# Employees')::integer,
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
                        (v_row->>'Latest Funding Amount')::decimal,
                        v_row->>'Annual Revenue',
                        v_row->>'Apollo Account Id',
                        v_row->>'SIC Codes',
                        v_row->>'NAICS Codes',
                        (v_row->>'Founded Year')::integer,
                        v_row->>'Short Description',
                        v_row->>'Keywords',
                        v_batch_id
                    );
                    v_inserted := v_inserted + 1;
                END LOOP;
                
                RETURN QUERY SELECT v_inserted, v_batch_id, 'Successfully ingested ' || v_inserted || ' company records';
            END;
            $$;
        `);
        console.log('✅ Created ingestion function');

        console.log('\n🎉 Successfully created marketing.company_raw_intake table!');
        console.log('\n📝 Usage:');
        console.log('   • Table: marketing.company_raw_intake');
        console.log('   • Function: marketing.f_ingest_company_csv(jsonb[], text)');
        console.log('   • All columns from your CSV header are now available');
        console.log('\n🔗 Next steps:');
        console.log('   1. Use the API endpoint POST /ingest/csv to upload your data');
        console.log('   2. Or use the ingestion function directly');
        console.log('   3. Data will be stored in marketing.company_raw_intake');

    } catch (error) {
        console.error('❌ Error creating company_raw_intake table:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

addCompanyRawIntakeColumns();