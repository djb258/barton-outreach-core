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

async function verifySchema() {
    try {
        console.log('🔌 Connecting to verify schema...');
        await client.connect();

        // Test insert and select operations
        console.log('🧪 Testing your original schema...');

        // Insert a test company
        const companyResult = await client.query(`
            INSERT INTO company (name, website_url, last_url_refresh_at) 
            VALUES ('Test Company', 'https://example.com', NOW()) 
            RETURNING company_id, name
        `);
        
        const companyId = companyResult.rows[0].company_id;
        console.log(`✅ Inserted test company: ${companyResult.rows[0].name} (ID: ${companyId})`);

        // Insert a test contact
        const contactResult = await client.query(`
            INSERT INTO contact (company_id, full_name, title, email, last_profile_fetch_at) 
            VALUES ($1, 'John Doe', 'CEO', 'john@example.com', NOW()) 
            RETURNING contact_id, full_name
        `, [companyId]);
        
        const contactId = contactResult.rows[0].contact_id;
        console.log(`✅ Inserted test contact: ${contactResult.rows[0].full_name} (ID: ${contactId})`);

        // Insert contact verification
        await client.query(`
            INSERT INTO contact_verification (contact_id, status, last_checked_at) 
            VALUES ($1, 'green', NOW())
        `, [contactId]);
        
        console.log(`✅ Inserted contact verification: green status`);

        // Test the complete relationship
        const joinResult = await client.query(`
            SELECT 
                c.name as company_name,
                co.full_name,
                co.email,
                cv.status as verification_status
            FROM company c
            JOIN contact co ON c.company_id = co.company_id  
            JOIN contact_verification cv ON co.contact_id = cv.contact_id
            WHERE c.company_id = $1
        `, [companyId]);

        console.log('\\n📊 Complete relationship test:');
        joinResult.rows.forEach(row => {
            console.log(`  🏢 ${row.company_name}`);
            console.log(`  👤 ${row.full_name} (${row.email})`);
            console.log(`  🔍 Status: ${row.verification_status}`);
        });

        // Clean up test data
        await client.query('DELETE FROM company WHERE company_id = $1', [companyId]);
        console.log('\\n🧹 Cleaned up test data');

        console.log('\\n🎉 Schema verification complete! Your tables are working perfectly in Neon.');

    } catch (error) {
        console.error('❌ Error during verification:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

verifySchema();