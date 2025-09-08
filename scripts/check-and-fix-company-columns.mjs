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

async function checkAndFixColumns() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        // First check what columns exist
        const existingColumns = await client.query(`
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'marketing' 
            AND table_name = 'company_raw_intake'
            ORDER BY ordinal_position
        `);

        console.log('📋 Current columns found:', existingColumns.rows.length);
        if (existingColumns.rows.length > 0) {
            console.log('Existing columns:', existingColumns.rows.map(r => r.column_name).join(', '));
        }

        // Define all columns that should exist based on your CSV header
        const requiredColumns = [
            // Basic fields
            { name: 'company', type: 'TEXT' },
            { name: 'company_name_for_emails', type: 'TEXT' },
            { name: 'account', type: 'TEXT' },
            { name: 'lists', type: 'TEXT' },
            
            // Company details
            { name: 'num_employees', type: 'INTEGER' },
            { name: 'industry', type: 'TEXT' },
            { name: 'account_owner', type: 'TEXT' },
            { name: 'website', type: 'TEXT' },
            { name: 'company_linkedin_url', type: 'TEXT' },
            { name: 'facebook_url', type: 'TEXT' },
            { name: 'twitter_url', type: 'TEXT' },
            
            // Address
            { name: 'company_street', type: 'TEXT' },
            { name: 'company_city', type: 'TEXT' },
            { name: 'company_state', type: 'TEXT' },
            { name: 'company_country', type: 'TEXT' },
            { name: 'company_postal_code', type: 'TEXT' },
            { name: 'company_address', type: 'TEXT' },
            { name: 'company_phone', type: 'TEXT' },
            
            // Business info
            { name: 'technologies', type: 'TEXT' },
            { name: 'total_funding', type: 'TEXT' },
            { name: 'latest_funding', type: 'TEXT' },
            { name: 'latest_funding_amount', type: 'DECIMAL(15,2)' },
            { name: 'last_raised_at', type: 'DATE' },
            { name: 'annual_revenue', type: 'TEXT' },
            { name: 'number_of_retail_locations', type: 'INTEGER' },
            
            // IDs and codes
            { name: 'apollo_account_id', type: 'TEXT' },
            { name: 'sic_codes', type: 'TEXT' },
            { name: 'naics_codes', type: 'TEXT' },
            
            // Metadata
            { name: 'founded_year', type: 'INTEGER' },
            { name: 'logo_url', type: 'TEXT' },
            { name: 'subsidiary_of', type: 'TEXT' },
            { name: 'short_description', type: 'TEXT' },
            { name: 'keywords', type: 'TEXT' },
            
            // Intent data
            { name: 'primary_intent_topic', type: 'TEXT' },
            { name: 'primary_intent_score', type: 'DECIMAL(5,2)' },
            { name: 'secondary_intent_topic', type: 'TEXT' },
            { name: 'secondary_intent_score', type: 'DECIMAL(5,2)' }
        ];

        // Check which columns are missing
        const existingColumnNames = existingColumns.rows.map(r => r.column_name);
        const missingColumns = requiredColumns.filter(col => !existingColumnNames.includes(col.name));

        if (missingColumns.length > 0) {
            console.log(`\n⚠️  Found ${missingColumns.length} missing columns. Adding them now...`);
            
            for (const col of missingColumns) {
                try {
                    const alterQuery = `ALTER TABLE marketing.company_raw_intake ADD COLUMN IF NOT EXISTS ${col.name} ${col.type}`;
                    await client.query(alterQuery);
                    console.log(`   ✅ Added column: ${col.name} (${col.type})`);
                } catch (error) {
                    console.error(`   ❌ Failed to add column ${col.name}: ${error.message}`);
                }
            }
        } else {
            console.log('\n✅ All required columns already exist!');
        }

        // Verify final state
        const finalColumns = await client.query(`
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'marketing' 
            AND table_name = 'company_raw_intake'
            ORDER BY ordinal_position
        `);

        console.log('\n📊 Final table structure:');
        console.log('═══════════════════════════════════════════════');
        finalColumns.rows.forEach(col => {
            const isRequired = requiredColumns.some(rc => rc.name === col.column_name);
            const marker = isRequired ? '✅' : '  ';
            console.log(`${marker} ${col.column_name.padEnd(35)} ${col.data_type}`);
        });

        console.log('\n🎉 Table marketing.company_raw_intake is ready!');
        console.log('   Total columns:', finalColumns.rows.length);
        console.log('   Required columns added:', missingColumns.length);

    } catch (error) {
        console.error('❌ Error checking/fixing columns:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

checkAndFixColumns();