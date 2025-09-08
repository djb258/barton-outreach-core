#!/usr/bin/env node

import { Client } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

// Check if there's a separate marketing_db connection string
const MARKETING_DB_URL = process.env.MARKETING_DATABASE_URL || process.env.NEON_MARKETING_DATABASE_URL;
const DATABASE_URL = process.env.NEON_DATABASE_URL || process.env.DATABASE_URL;

console.log('🔍 Checking database connections...');
console.log('   Main DB URL:', DATABASE_URL ? 'Found' : 'Not found');
console.log('   Marketing DB URL:', MARKETING_DB_URL ? 'Found' : 'Not found');

if (!DATABASE_URL && !MARKETING_DB_URL) {
    console.error('❌ No database URL found. Please set NEON_DATABASE_URL or MARKETING_DATABASE_URL');
    process.exit(1);
}

// Use marketing DB URL if available, otherwise fall back to main DB
const connectionString = MARKETING_DB_URL || DATABASE_URL;
console.log('📡 Using connection for marketing_db');

const client = new Client({
    connectionString: connectionString,
    ssl: { rejectUnauthorized: false }
});

async function checkMarketingDb() {
    try {
        console.log('🔌 Connecting to marketing_db...');
        await client.connect();

        // Check current database name
        const dbResult = await client.query('SELECT current_database()');
        console.log('📊 Connected to database:', dbResult.rows[0].current_database);

        // Check if intake schema exists
        const schemaResult = await client.query(`
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'intake'
        `);
        
        console.log('📋 intake schema exists:', schemaResult.rows.length > 0);

        // Check if company_raw_intake table exists in intake schema
        const tableResult = await client.query(`
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'intake' 
                AND table_name = 'company_raw_intake'
            ) as exists
        `);
        
        console.log('📊 intake.company_raw_intake table exists:', tableResult.rows[0].exists);

        if (tableResult.rows[0].exists) {
            // Check columns in intake.company_raw_intake
            const columnsResult = await client.query(`
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'intake' 
                AND table_name = 'company_raw_intake'
                ORDER BY ordinal_position
            `);
            
            console.log('\\n📋 Columns in intake.company_raw_intake (' + columnsResult.rows.length + '):');
            columnsResult.rows.forEach(col => {
                console.log('  -', col.column_name, '(' + col.data_type + ')');
            });
        } else {
            console.log('⚠️  intake.company_raw_intake table does not exist');
            
            // Check what tables exist in intake schema
            const tablesResult = await client.query(`
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'intake'
                ORDER BY table_name
            `);
            
            console.log('\\n📋 Tables in intake schema:');
            tablesResult.rows.forEach(table => {
                console.log('  -', table.table_name);
            });
        }

        // Also check if marketing schema exists
        const marketingSchema = await client.query(`
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'marketing'
        `);
        
        if (marketingSchema.rows.length > 0) {
            const marketingTables = await client.query(`
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'marketing'
                ORDER BY table_name
            `);
            
            console.log('\\n📋 Tables in marketing schema:');
            marketingTables.rows.forEach(table => {
                console.log('  -', table.table_name);
            });
        }

    } catch (error) {
        console.error('❌ Error checking marketing_db:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

checkMarketingDb();