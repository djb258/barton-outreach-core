#!/usr/bin/env node

import { Client } from 'pg';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __dirname = dirname(fileURLToPath(import.meta.url));

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

async function setupOriginalSchema() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        // Read and execute your original schema
        console.log('📄 Executing your original schema...');
        
        const originalSchemaSql = `
-- Your original schema as specified
CREATE TABLE IF NOT EXISTS company (
  company_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  website_url TEXT,
  last_url_refresh_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS contact (
  contact_id BIGSERIAL PRIMARY KEY,
  company_id BIGINT REFERENCES company(company_id) ON DELETE CASCADE,
  full_name TEXT,
  title TEXT,
  email TEXT,
  last_profile_fetch_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS contact_verification (
  contact_id BIGINT PRIMARY KEY REFERENCES contact(contact_id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('green','yellow','red','gray')) DEFAULT 'gray',
  last_checked_at TIMESTAMPTZ
);
`;

        await client.query(originalSchemaSql);
        console.log('✅ Your original schema tables created successfully!');

        // Verify tables exist
        const result = await client.query(`
            SELECT table_name, table_schema 
            FROM information_schema.tables 
            WHERE table_name IN ('company', 'contact', 'contact_verification')
            AND table_schema = 'public'
            ORDER BY table_name
        `);

        console.log('\\n📊 Verified your original tables:');
        result.rows.forEach(row => {
            console.log(`  ✅ ${row.table_schema}.${row.table_name}`);
        });

        // Check constraints
        const constraints = await client.query(`
            SELECT table_name, constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name IN ('company', 'contact', 'contact_verification')
            AND table_schema = 'public'
            ORDER BY table_name, constraint_type
        `);

        console.log('\\n🔗 Constraints verified:');
        constraints.rows.forEach(row => {
            console.log(`  📋 ${row.table_name}: ${row.constraint_name} (${row.constraint_type})`);
        });

        console.log('\\n🎉 Your original schema is now set up in Neon!');
        console.log('\\n📝 Summary:');
        console.log('   • company table - stores company info');
        console.log('   • contact table - linked to companies');
        console.log('   • contact_verification table - verification status with color dots');

    } catch (error) {
        console.error('❌ Error setting up schema:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

setupOriginalSchema();