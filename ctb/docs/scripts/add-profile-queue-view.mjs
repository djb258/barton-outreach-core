/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-6DF0D9C3
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Add Profile Queue View - Contact profile refresh queue
 * Creates view to identify contact profile URLs needing refresh checks
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function addProfileQueueView() {
  console.log('👤 Creating Profile Queue View for Contact Data Refresh...\n');
  
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
    
    // Step 1: Create the profile queue view
    console.log('1️⃣ Creating next_profile_urls_30d view...');
    await sql`
      CREATE OR REPLACE VIEW people.next_profile_urls_30d AS
      SELECT contact_id, 'profile' AS kind, profile_source_url AS url
      FROM people.contact
      WHERE profile_source_url IS NOT NULL
        AND (last_profile_checked_at IS NULL OR last_profile_checked_at < NOW() - INTERVAL '30 days')
    `;
    console.log('   ✅ people.next_profile_urls_30d view created');
    console.log('   👤 Identifies contact profiles needing refresh (30+ days old or never checked)');
    
    // Step 2: Test the view with current data
    console.log('2️⃣ Testing profile queue view...');
    const profileQueue = await sql`
      SELECT 
        pq.contact_id,
        c.full_name,
        c.email,
        pq.url,
        c.last_profile_checked_at
      FROM people.next_profile_urls_30d pq
      JOIN people.contact c ON c.contact_id = pq.contact_id
      ORDER BY c.full_name
    `;
    
    console.log(`   📋 Found ${profileQueue.length} profiles in refresh queue:`);
    profileQueue.forEach(item => {
      const lastChecked = item.last_profile_checked_at 
        ? new Date(item.last_profile_checked_at).toLocaleDateString()
        : 'Never';
      console.log(`      ${item.full_name} (${item.email})`);
      console.log(`         Profile: ${item.url}`);
      console.log(`         Last checked: ${lastChecked}`);
      console.log('');
    });
    
    // Step 3: Create a summary view for monitoring
    console.log('3️⃣ Creating profile queue summary view...');
    await sql`
      CREATE OR REPLACE VIEW people.vw_profile_queue_summary AS
      SELECT 
        COUNT(*) as profiles_due_for_refresh,
        COUNT(CASE WHEN c.last_profile_checked_at IS NULL THEN 1 END) as never_checked,
        COUNT(CASE WHEN c.last_profile_checked_at < NOW() - INTERVAL '30 days' THEN 1 END) as stale_30d,
        COUNT(CASE WHEN c.last_profile_checked_at < NOW() - INTERVAL '60 days' THEN 1 END) as very_stale_60d
      FROM people.next_profile_urls_30d pq
      JOIN people.contact c ON c.contact_id = pq.contact_id
    `;
    console.log('   ✅ vw_profile_queue_summary view created');
    console.log('   📊 Provides profile refresh queue statistics by staleness');
    
    // Step 4: Test the summary view
    console.log('4️⃣ Testing profile queue summary...');
    const queueSummary = await sql`
      SELECT * FROM people.vw_profile_queue_summary
    `;
    
    if (queueSummary.length > 0) {
      const summary = queueSummary[0];
      console.log('   📊 Profile Refresh Queue Summary:');
      console.log(`      Total profiles due: ${summary.profiles_due_for_refresh}`);
      console.log(`      Never checked: ${summary.never_checked}`);
      console.log(`      Stale (30+ days): ${summary.stale_30d}`);
      console.log(`      Very stale (60+ days): ${summary.very_stale_60d}`);
    }
    console.log('');
    
    // Step 5: Create a function to mark profile as checked
    console.log('5️⃣ Creating profile check update function...');
    await sql`
      CREATE OR REPLACE FUNCTION people.mark_profile_checked(
        p_contact_id BIGINT
      ) RETURNS VOID AS $$
      BEGIN
        UPDATE people.contact 
        SET last_profile_checked_at = NOW() 
        WHERE contact_id = p_contact_id;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ people.mark_profile_checked() function created');
    console.log('   🔄 Updates last-checked timestamp for contact profile');
    
    // Step 6: Test the update function
    console.log('6️⃣ Testing profile check update function...');
    
    if (profileQueue.length > 0) {
      const testProfile = profileQueue[0];
      
      console.log(`   🧪 Simulating profile check for ${testProfile.full_name}...`);
      await sql`SELECT people.mark_profile_checked(${testProfile.contact_id})`;
      
      // Verify the update worked
      const afterUpdate = await sql`
        SELECT COUNT(*) as remaining
        FROM people.next_profile_urls_30d
        WHERE contact_id = ${testProfile.contact_id}
      `;
      
      console.log(`   ✅ Profile marked as checked - ${afterUpdate[0].remaining} profiles remaining in queue for this contact`);
      
      // Reset for demo purposes
      await sql`
        UPDATE people.contact 
        SET last_profile_checked_at = NOW() - INTERVAL '5 days'
        WHERE contact_id = ${testProfile.contact_id}
      `;
      console.log('   🔄 Reset timestamp for demo purposes');
    }
    
    // Step 7: Create batch processing view for profiles
    console.log('7️⃣ Creating profile batch processing view...');
    await sql`
      CREATE OR REPLACE VIEW people.vw_next_profile_batch AS
      WITH numbered AS (
        SELECT 
          pq.contact_id,
          c.full_name,
          c.email,
          pq.url,
          c.last_profile_checked_at,
          ROW_NUMBER() OVER (ORDER BY 
            CASE WHEN c.last_profile_checked_at IS NULL THEN 0 ELSE 1 END,
            c.last_profile_checked_at ASC NULLS FIRST,
            c.contact_id
          ) as batch_number
        FROM people.next_profile_urls_30d pq
        JOIN people.contact c ON c.contact_id = pq.contact_id
      )
      SELECT 
        contact_id,
        full_name,
        email,
        url,
        last_profile_checked_at,
        CEIL(batch_number / 5.0) as batch_group,
        batch_number
      FROM numbered
      ORDER BY batch_group, batch_number
    `;
    console.log('   ✅ vw_next_profile_batch view created');
    console.log('   📦 Organizes profiles into batches of 5 for processing');
    console.log('   🎯 Prioritizes never-checked profiles first');
    
    // Step 8: Test batch processing view
    console.log('8️⃣ Testing profile batch processing view...');
    const batchTest = await sql`
      SELECT 
        batch_group,
        COUNT(*) as profiles_in_batch,
        COUNT(CASE WHEN last_profile_checked_at IS NULL THEN 1 END) as never_checked_in_batch
      FROM people.vw_next_profile_batch
      GROUP BY batch_group
      ORDER BY batch_group
      LIMIT 3
    `;
    
    console.log('   📦 Profile Processing Batches:');
    batchTest.forEach(batch => {
      console.log(`      Batch ${batch.batch_group}: ${batch.profiles_in_batch} profiles (${batch.never_checked_in_batch} never checked)`);
    });
    
    // Show sample batch details
    const sampleBatch = await sql`
      SELECT 
        batch_group,
        full_name,
        email,
        CASE WHEN last_profile_checked_at IS NULL THEN 'Never' 
             ELSE last_profile_checked_at::date::text END as last_checked
      FROM people.vw_next_profile_batch
      WHERE batch_group = 1
      LIMIT 3
    `;
    
    if (sampleBatch.length > 0) {
      console.log(`\n   📋 Sample Batch 1 Details:`);
      sampleBatch.forEach(profile => {
        console.log(`      ${profile.full_name} (${profile.email}) - Last: ${profile.last_checked}`);
      });
    }
    console.log('');
    
    // Step 9: Create comprehensive profile monitoring view
    console.log('9️⃣ Creating comprehensive profile monitoring view...');
    await sql`
      CREATE OR REPLACE VIEW people.vw_profile_monitoring AS
      SELECT 
        c.contact_id,
        c.full_name,
        c.email,
        c.profile_source_url,
        c.last_profile_checked_at,
        cv.email_status,
        cv.email_checked_at,
        CASE 
          WHEN c.profile_source_url IS NULL THEN 'No Profile URL'
          WHEN c.last_profile_checked_at IS NULL THEN 'Never Checked'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '60 days' THEN 'Very Stale (60+ days)'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
          ELSE 'Fresh'
        END as profile_status,
        CASE 
          WHEN cv.email_checked_at IS NULL THEN 'Never Verified'
          WHEN cv.email_checked_at < NOW() - INTERVAL '30 days' THEN 'Email Stale'
          ELSE 'Email Fresh'
        END as email_verification_status,
        CASE 
          WHEN cs.contact_id IS NOT NULL THEN 'In Company Slot'
          ELSE 'Not Assigned'
        END as assignment_status
      FROM people.contact c
      LEFT JOIN people.contact_verification cv ON cv.contact_id = c.contact_id
      LEFT JOIN company.company_slot cs ON cs.contact_id = c.contact_id
      WHERE c.email IS NOT NULL
      ORDER BY 
        CASE WHEN c.profile_source_url IS NULL THEN 2
             WHEN c.last_profile_checked_at IS NULL THEN 0
             ELSE 1 END,
        c.last_profile_checked_at ASC NULLS FIRST
    `;
    console.log('   ✅ vw_profile_monitoring view created');
    console.log('   📊 Comprehensive contact profile and verification monitoring');
    
    // Step 10: Test monitoring view
    console.log('🔟 Testing comprehensive profile monitoring...');
    const monitoring = await sql`
      SELECT 
        full_name,
        email,
        profile_status,
        email_verification_status,
        assignment_status
      FROM people.vw_profile_monitoring
      LIMIT 5
    `;
    
    console.log('   📊 Profile Monitoring Sample:');
    monitoring.forEach(contact => {
      console.log(`      ${contact.full_name} (${contact.email})`);
      console.log(`         Profile: ${contact.profile_status}`);
      console.log(`         Email: ${contact.email_verification_status}`);
      console.log(`         Assignment: ${contact.assignment_status}`);
      console.log('');
    });
    
    console.log('🎉 Profile Queue View Setup Complete!');
    console.log('\n📋 Views Created:');
    console.log('✅ people.next_profile_urls_30d:');
    console.log('   • Lists contact profiles needing refresh (30+ days old)');
    console.log('   • Ready for automated LinkedIn/profile scraping');
    console.log('');
    console.log('✅ people.vw_profile_queue_summary:');
    console.log('   • Statistics on profiles due for refresh');
    console.log('   • Breakdown by staleness categories');
    console.log('');
    console.log('✅ people.vw_next_profile_batch:');
    console.log('   • Organizes profiles into processing batches of 5');
    console.log('   • Prioritizes never-checked profiles first');
    console.log('');
    console.log('✅ people.vw_profile_monitoring:');
    console.log('   • Comprehensive contact data quality monitoring');
    console.log('   • Combines profile, email, and assignment status');
    console.log('');
    console.log('✅ Function Created:');
    console.log('✅ people.mark_profile_checked(contact_id):');
    console.log('   • Updates last-checked timestamp after profile processing');
    console.log('   • Removes profile from refresh queue');
    console.log('');
    console.log('🎯 Usage Examples:');
    console.log('   • Get next batch: SELECT * FROM people.vw_next_profile_batch WHERE batch_group = 1');
    console.log('   • Mark as checked: SELECT people.mark_profile_checked(123)');
    console.log('   • Monitor queue: SELECT * FROM people.vw_profile_queue_summary');
    console.log('   • Full monitoring: SELECT * FROM people.vw_profile_monitoring');
    console.log('');
    console.log('✅ Ready for automated contact profile refresh workflows!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify anchor columns exist (run add-anchor-columns.mjs first)');
    console.log('   • Ensure user has CREATE VIEW permissions');
  }
}

addProfileQueueView().catch(console.error);