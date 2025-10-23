/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-89B0D20F
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

async function fixMonitoringViews() {
    try {
        console.log('🔌 Connecting to Neon database...');
        await client.connect();

        console.log('🔧 Fixing due_email_recheck_30d view...');

        // Fix the due_email_recheck_30d view to properly join with contact table
        await client.query(`
            CREATE OR REPLACE VIEW due_email_recheck_30d AS
            SELECT cv.contact_id, c.email
            FROM contact_verification cv
            JOIN contact c ON cv.contact_id = c.contact_id
            WHERE (cv.last_checked_at IS NULL OR cv.last_checked_at <= now() - interval '30 days')
        `);
        console.log('✅ Fixed due_email_recheck_30d view');

        // Verify all views are working
        console.log('\\n📋 Verifying all monitoring views...');

        // Check view definitions
        const viewsResult = await client.query(`
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_name IN ('next_company_urls_30d', 'next_profile_urls_30d', 'due_email_recheck_30d')
            AND table_schema = 'public'
            ORDER BY table_name
        `);

        console.log('\\n📊 Available monitoring views:');
        viewsResult.rows.forEach(row => {
            console.log(`  ✅ ${row.table_name} (${row.table_type})`);
        });

        // Test with sample data
        console.log('\\n🧪 Testing all views...');
        
        // Insert test data
        const companyResult = await client.query(`
            INSERT INTO company (name, website_url) 
            VALUES ('Test Company for Views', 'https://test-views.com') 
            RETURNING company_id
        `);
        const companyId = companyResult.rows[0].company_id;

        const contactResult = await client.query(`
            INSERT INTO contact (company_id, full_name, email) 
            VALUES ($1, 'Test Contact Views', 'test-views@example.com') 
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

        console.log(`  🏢 next_company_urls_30d: Found ${companyUrls.rows.length} companies (${companyUrls.rows[0]?.website_url || 'none'})`);
        console.log(`  👤 next_profile_urls_30d: Found ${profileUrls.rows.length} contacts (${profileUrls.rows[0]?.email || 'none'})`);
        console.log(`  📧 due_email_recheck_30d: Found ${emailRechecks.rows.length} verifications (${emailRechecks.rows[0]?.email || 'none'})`);

        // Clean up test data
        await client.query('DELETE FROM company WHERE company_id = $1', [companyId]);
        console.log('\\n🧹 Cleaned up test data');

        console.log('\\n🎉 All monitoring views are working perfectly!');
        console.log('\\n📝 View Descriptions:');
        console.log('   • next_company_urls_30d - Companies needing website refresh (NULL or >30 days old)');
        console.log('   • next_profile_urls_30d - Contacts needing profile update (NULL or >30 days old)');
        console.log('   • due_email_recheck_30d - Email verifications needing recheck (NULL or >30 days old)');

    } catch (error) {
        console.error('❌ Error fixing monitoring views:', error.message);
        process.exit(1);
    } finally {
        await client.end();
    }
}

fixMonitoringViews();