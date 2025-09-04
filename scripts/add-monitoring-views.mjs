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

async function addMonitoringViews() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        console.log('📊 Creating monitoring views...');

        // Create next_company_urls_30d view
        await client.query(`
            CREATE OR REPLACE VIEW next_company_urls_30d AS
            SELECT company_id, website_url
            FROM company
            WHERE website_url IS NOT NULL
              AND (last_url_refresh_at IS NULL OR last_url_refresh_at <= now() - interval '30 days')
        `);
        console.log('✅ Created next_company_urls_30d view');

        // Create next_profile_urls_30d view
        await client.query(`
            CREATE OR REPLACE VIEW next_profile_urls_30d AS
            SELECT contact_id, email
            FROM contact
            WHERE (last_profile_fetch_at IS NULL OR last_profile_fetch_at <= now() - interval '30 days')
        `);
        console.log('✅ Created next_profile_urls_30d view');

        // Create due_email_recheck_30d view
        await client.query(`
            CREATE OR REPLACE VIEW due_email_recheck_30d AS
            SELECT contact_id, email
            FROM contact_verification
            WHERE (last_checked_at IS NULL OR last_checked_at <= now() - interval '30 days')
        `);
        console.log('✅ Created due_email_recheck_30d view');

        // Verify views were created
        const viewsResult = await client.query(`
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_name IN ('next_company_urls_30d', 'next_profile_urls_30d', 'due_email_recheck_30d')
            AND table_schema = 'public'
            ORDER BY table_name
        `);

        console.log('\\n📋 Verified views created:');
        viewsResult.rows.forEach(row => {
            console.log(`  📊 ${row.table_name} (${row.table_type})`);
        });

        // Test the views with sample data
        console.log('\\n🧪 Testing views with sample data...');
        
        // Insert test data
        const companyResult = await client.query(`
            INSERT INTO company (name, website_url) 
            VALUES ('Old Company', 'https://old.com') 
            RETURNING company_id
        `);
        const companyId = companyResult.rows[0].company_id;

        const contactResult = await client.query(`
            INSERT INTO contact (company_id, full_name, email) 
            VALUES ($1, 'Old Contact', 'old@example.com') 
            RETURNING contact_id
        `, [companyId]);
        const contactId = contactResult.rows[0].contact_id;

        await client.query(`
            INSERT INTO contact_verification (contact_id, status) 
            VALUES ($1, 'gray')
        `, [contactId]);

        // Test each view
        const companyUrls = await client.query('SELECT * FROM next_company_urls_30d WHERE company_id = $1', [companyId]);
        const profileUrls = await client.query('SELECT * FROM next_profile_urls_30d WHERE contact_id = $1', [contactId]);
        const emailRechecks = await client.query('SELECT * FROM due_email_recheck_30d WHERE contact_id = $1', [contactId]);

        console.log(`  🏢 next_company_urls_30d: Found ${companyUrls.rows.length} companies needing URL refresh`);
        console.log(`  👤 next_profile_urls_30d: Found ${profileUrls.rows.length} contacts needing profile refresh`);
        console.log(`  📧 due_email_recheck_30d: Found ${emailRechecks.rows.length} emails needing verification`);

        // Clean up test data
        await client.query('DELETE FROM company WHERE company_id = $1', [companyId]);
        console.log('\\n🧹 Cleaned up test data');

        console.log('\\n🎉 All monitoring views created and verified successfully!');
        console.log('\\n📝 Views available:');
        console.log('   • next_company_urls_30d - Companies with websites needing refresh (>30 days)');
        console.log('   • next_profile_urls_30d - Contacts needing profile updates (>30 days)');
        console.log('   • due_email_recheck_30d - Email verifications needing recheck (>30 days)');

    } catch (error) {
        console.error('❌ Error creating monitoring views:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

addMonitoringViews();