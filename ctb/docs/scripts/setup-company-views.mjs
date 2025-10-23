/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-3A29B540
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Set up Company Views - UI and renewal management views
 * Creates comprehensive views for company slots, renewals, and email verification
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupCompanyViews() {
  console.log('👁️ Setting up Company Views in Neon...\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    if (!connectionString) {
      console.error('❌ No database connection string found.');
      return;
    }
    
    const sql = neon(connectionString);
    
    console.log('📡 Connected to Neon database');
    console.log('');
    
    // Step 1: Create company slots view (for UI)
    console.log('1️⃣ Creating company.vw_company_slots view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_company_slots AS
      SELECT
        cs.company_id,
        cs.role_code,
        cs.company_slot_id,
        c.contact_id,
        c.full_name,
        c.title,
        c.email,
        v.email_status,
        v.email_checked_at,
        v.email_confidence,
        v.email_source_url
      FROM company.company_slot cs
      LEFT JOIN people.contact c ON c.contact_id = cs.contact_id
      LEFT JOIN people.contact_verification v ON v.contact_id = cs.contact_id
    `;
    console.log('   ✅ company.vw_company_slots view created');
    console.log('   📋 Combines company slots with contact details and verification status');
    
    // Step 2: Create due email recheck view
    console.log('2️⃣ Creating people.due_email_recheck_30d view...');
    await sql`
      CREATE OR REPLACE VIEW people.due_email_recheck_30d AS
      SELECT c.contact_id, c.full_name, c.email, v.email_checked_at
      FROM people.contact c
      LEFT JOIN people.contact_verification v USING (contact_id)
      WHERE c.email IS NOT NULL
        AND (v.email_checked_at IS NULL OR v.email_checked_at < NOW() - INTERVAL '30 days')
    `;
    console.log('   ✅ people.due_email_recheck_30d view created');
    console.log('   📧 Identifies contacts needing email verification refresh');
    
    // Step 3: Create next renewal view
    console.log('3️⃣ Creating company.vw_next_renewal view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_next_renewal AS
      WITH base AS (
        SELECT
          c.company_id,
          c.renewal_month,
          COALESCE(c.renewal_notice_window_days, 120) AS notice_days,
          MAKE_DATE(
            EXTRACT(year FROM NOW())::int
              + CASE WHEN c.renewal_month IS NOT NULL
                       AND c.renewal_month < EXTRACT(month FROM NOW())::int
                     THEN 1 ELSE 0 END,
            COALESCE(c.renewal_month, 1),
            1
          )::date AS next_renewal_date
        FROM company.company c
        WHERE c.renewal_month BETWEEN 1 AND 12
      )
      SELECT
        company_id,
        renewal_month,
        notice_days AS renewal_notice_window_days,
        next_renewal_date,
        (next_renewal_date - (notice_days || ' days')::INTERVAL)::date AS window_opens_on
      FROM base
    `;
    console.log('   ✅ company.vw_next_renewal view created');
    console.log('   📅 Calculates next renewal dates and 120-day notice windows');
    
    // Step 4: Create due renewals ready view
    console.log('4️⃣ Creating company.vw_due_renewals_ready view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_due_renewals_ready AS
      SELECT d.company_id, d.renewal_month, d.next_renewal_date, d.window_opens_on
      FROM company.vw_next_renewal d
      WHERE NOW()::date >= d.window_opens_on
        AND EXISTS (
          SELECT 1
          FROM company.company_slot s
          JOIN people.contact c ON c.contact_id = s.contact_id
          JOIN people.contact_verification v ON v.contact_id = c.contact_id
          WHERE s.company_id = d.company_id
            AND v.email_status = 'green'
        )
    `;
    console.log('   ✅ company.vw_due_renewals_ready view created');
    console.log('   🟢 Shows companies in renewal window with verified green contacts');
    
    // Step 5: Test all views with sample data
    console.log('5️⃣ Testing all views with sample data...');
    
    // Test company slots view
    const slotsTest = await sql`
      SELECT company_id, role_code, full_name, email, email_status
      FROM company.vw_company_slots
      WHERE contact_id IS NOT NULL
      LIMIT 3
    `;
    
    console.log(`   📋 Company Slots View: Found ${slotsTest.length} filled slots`);
    slotsTest.forEach(slot => {
      console.log(`      ${slot.role_code}: ${slot.full_name} (${slot.email_status || 'no status'} dot)`);
    });
    
    // Test due email recheck view
    const recheckTest = await sql`
      SELECT contact_id, full_name, email, email_checked_at
      FROM people.due_email_recheck_30d
      LIMIT 3
    `;
    
    console.log(`   📧 Due Email Recheck: Found ${recheckTest.length} contacts needing verification`);
    recheckTest.forEach(contact => {
      const lastCheck = contact.email_checked_at 
        ? new Date(contact.email_checked_at).toLocaleDateString()
        : 'Never';
      console.log(`      ${contact.full_name} (${contact.email}) - Last check: ${lastCheck}`);
    });
    
    // Test renewal views
    const renewalTest = await sql`
      SELECT company_id, renewal_month, next_renewal_date, window_opens_on
      FROM company.vw_next_renewal
      LIMIT 3
    `;
    
    console.log(`   📅 Next Renewals: Found ${renewalTest.length} companies with renewal dates`);
    renewalTest.forEach(renewal => {
      console.log(`      Company ${renewal.company_id}: Month ${renewal.renewal_month} → ${new Date(renewal.next_renewal_date).toLocaleDateString()}`);
      console.log(`         Window opens: ${new Date(renewal.window_opens_on).toLocaleDateString()}`);
    });
    
    const readyTest = await sql`
      SELECT company_id, renewal_month, next_renewal_date
      FROM company.vw_due_renewals_ready
      LIMIT 3
    `;
    
    console.log(`   🟢 Ready for Renewal Campaign: Found ${readyTest.length} companies`);
    readyTest.forEach(ready => {
      console.log(`      Company ${ready.company_id}: Ready for campaign (Month ${ready.renewal_month})`);
    });
    
    // Step 6: Create a comprehensive dashboard query
    console.log('6️⃣ Creating comprehensive dashboard test...');
    const dashboard = await sql`
      SELECT 
        'Company Slots' as metric,
        COUNT(*) as total,
        COUNT(CASE WHEN contact_id IS NOT NULL THEN 1 END) as filled,
        COUNT(CASE WHEN email_status = 'green' THEN 1 END) as green_contacts
      FROM company.vw_company_slots
      
      UNION ALL
      
      SELECT 
        'Due Email Rechecks' as metric,
        COUNT(*) as total,
        NULL as filled,
        NULL as green_contacts
      FROM people.due_email_recheck_30d
      
      UNION ALL
      
      SELECT 
        'Renewal Windows Open' as metric,
        COUNT(*) as total,
        NULL as filled,
        NULL as green_contacts
      FROM company.vw_due_renewals_ready
    `;
    
    console.log('\n📊 Complete Dashboard Summary:');
    dashboard.forEach(metric => {
      console.log(`   ${metric.metric}: ${metric.total} total`);
      if (metric.filled !== null) {
        console.log(`      ${metric.filled} filled, ${metric.green_contacts} green contacts`);
      }
    });
    
    console.log('\n🎉 Company Views Setup Complete!');
    console.log('\n📋 Views Created:');
    console.log('✅ company.vw_company_slots:');
    console.log('   • Complete company slot information with contact details');
    console.log('   • Includes email verification status (dot colors)');
    console.log('   • Primary view for UI display');
    console.log('');
    console.log('✅ people.due_email_recheck_30d:');
    console.log('   • Contacts needing email verification refresh');
    console.log('   • Identifies emails not checked in 30+ days');
    console.log('   • Triggers for MillionVerifier batch jobs');
    console.log('');
    console.log('✅ company.vw_next_renewal:');
    console.log('   • Calculates next renewal dates from renewal_month');
    console.log('   • 120-day notice window calculations');
    console.log('   • Handles year rollover logic');
    console.log('');
    console.log('✅ company.vw_due_renewals_ready:');
    console.log('   • Companies in renewal window with ≥1 green contact');
    console.log('   • Ready for BIT signals and campaign creation');
    console.log('   • Filtered for actionable opportunities');
    console.log('');
    console.log('🎯 Usage Examples:');
    console.log('   • UI: SELECT * FROM company.vw_company_slots WHERE company_id = ?');
    console.log('   • Email verification: SELECT * FROM people.due_email_recheck_30d');
    console.log('   • Renewal campaigns: SELECT * FROM company.vw_due_renewals_ready');
    console.log('\n✅ Views ready for UI integration and automation!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE VIEW permissions');
    console.log('   • Ensure all referenced tables exist');
  }
}

setupCompanyViews().catch(console.error);