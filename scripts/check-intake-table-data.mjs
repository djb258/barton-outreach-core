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

async function checkIntakeTableData() {
    try {
        console.log('🔌 Connecting to Marketing DB...');
        await client.connect();

        // Check if there's any data in intake.company_raw_intake
        console.log('📊 Checking intake.company_raw_intake table data...');
        
        const countResult = await client.query(`
            SELECT COUNT(*) as total_count FROM intake.company_raw_intake
        `);
        console.log('📋 Total records:', countResult.rows[0].total_count);

        if (parseInt(countResult.rows[0].total_count) > 0) {
            // Show sample data
            const sampleData = await client.query(`
                SELECT id, company, website, industry, batch_id, created_at
                FROM intake.company_raw_intake
                ORDER BY created_at DESC
                LIMIT 5
            `);
            
            console.log('\\n📋 Recent records:');
            sampleData.rows.forEach(row => {
                console.log(`  • ID: ${row.id}, Company: ${row.company}, Website: ${row.website}, Batch: ${row.batch_id}`);
            });

            // Check batch IDs
            const batchResult = await client.query(`
                SELECT batch_id, COUNT(*) as count, MAX(created_at) as latest
                FROM intake.company_raw_intake
                GROUP BY batch_id
                ORDER BY latest DESC
                LIMIT 10
            `);
            
            console.log('\\n📦 Recent batches:');
            batchResult.rows.forEach(row => {
                console.log(`  • Batch: ${row.batch_id}, Count: ${row.count}, Latest: ${row.latest}`);
            });
        } else {
            console.log('⚠️  No data found in intake.company_raw_intake table');
            
            // Check if the function exists and test it
            console.log('\\n🔧 Testing intake.f_ingest_company_csv function...');
            
            try {
                const testData = [{
                    "Company": "Test Company",
                    "Website": "https://test.com", 
                    "Industry": "Software",
                    "# Employees": "100"
                }];
                
                const testResult = await client.query(`
                    SELECT * FROM intake.f_ingest_company_csv($1::jsonb[], $2)
                `, [JSON.stringify(testData), 'test_batch_' + Date.now()]);
                
                console.log('✅ Function test result:', testResult.rows[0]);
                
                // Check if test data was inserted
                const verifyResult = await client.query(`
                    SELECT COUNT(*) as count FROM intake.company_raw_intake WHERE batch_id LIKE 'test_batch_%'
                `);
                console.log('✅ Test records inserted:', verifyResult.rows[0].count);
                
            } catch (funcError) {
                console.error('❌ Function test failed:', funcError.message);
            }
        }

        // Check the function definition
        console.log('\\n🔍 Checking function definition...');
        const funcResult = await client.query(`
            SELECT proname, prosrc 
            FROM pg_proc 
            WHERE proname = 'f_ingest_company_csv' 
            AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'intake')
        `);
        
        if (funcResult.rows.length > 0) {
            console.log('✅ Function intake.f_ingest_company_csv exists');
        } else {
            console.log('❌ Function intake.f_ingest_company_csv does not exist');
        }

    } catch (error) {
        console.error('❌ Error checking table data:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

checkIntakeTableData();