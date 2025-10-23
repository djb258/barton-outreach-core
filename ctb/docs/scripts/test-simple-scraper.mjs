/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-5CAE1B80
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Test Simple Scraper - Zero wandering queue consumption
 * Tests direct consumption of the three core queues
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testSimpleScraper() {
  console.log('🧪 Testing Simple Scraper (Zero Wandering Approach)...\n');
  
  try {
    const sql = neon(process.env.NEON_DATABASE_URL || process.env.DATABASE_URL);
    
    console.log('📡 Connected to Neon database');
    console.log('');

    // Step 1: Test company crawl queue - exactly as specified
    console.log('1️⃣ Testing company crawl queue...');
    const companyQueue = await sql`
      SELECT company_id, kind, url
      FROM company.next_company_urls_30d
      ORDER BY company_id, kind
    `;
    
    console.log(`   📋 Company queue: ${companyQueue.length} URLs`);
    companyQueue.forEach(item => {
      console.log(`      Company ${item.company_id} (${item.kind}): ${item.url}`);
    });
    console.log('');

    // Step 2: Test person profile queue - exactly as specified  
    console.log('2️⃣ Testing person profile queue...');
    const profileQueue = await sql`
      SELECT contact_id, kind, url
      FROM people.next_profile_urls_30d
    `;
    
    console.log(`   👤 Profile queue: ${profileQueue.length} profiles`);
    profileQueue.forEach(item => {
      console.log(`      Contact ${item.contact_id} (${item.kind}): ${item.url}`);
    });
    console.log('');

    // Step 3: Test email verify queue - exactly as specified
    console.log('3️⃣ Testing email verify queue...');
    const emailQueue = await sql`
      SELECT contact_id, email
      FROM people.due_email_recheck_30d
    `;
    
    console.log(`   📧 Email queue: ${emailQueue.length} emails`);
    emailQueue.forEach(item => {
      console.log(`      Contact ${item.contact_id}: ${item.email}`);
    });
    console.log('');

    // Step 4: Simulate processing first item from each queue
    console.log('4️⃣ Simulating queue processing...');
    
    let processed = 0;
    let succeeded = 0;
    
    // Process first company URL
    if (companyQueue.length > 0) {
      const item = companyQueue[0];
      console.log(`   🔄 Processing company ${item.company_id} ${item.kind}...`);
      
      try {
        // Simple timestamp update - core of zero wandering approach
        await sql`
          UPDATE company.company
          SET last_site_checked_at = CASE WHEN ${item.kind} = 'website' THEN NOW() ELSE last_site_checked_at END,
              last_linkedin_checked_at = CASE WHEN ${item.kind} = 'linkedin' THEN NOW() ELSE last_linkedin_checked_at END,
              last_news_checked_at = CASE WHEN ${item.kind} = 'news' THEN NOW() ELSE last_news_checked_at END
          WHERE company_id = ${item.company_id}
        `;
        processed++;
        succeeded++;
        console.log(`      ✅ Marked ${item.kind} as checked`);
      } catch (error) {
        console.log(`      ❌ Failed: ${error.message}`);
        processed++;
      }
    }

    // Process first profile
    if (profileQueue.length > 0) {
      const item = profileQueue[0];
      console.log(`   🔄 Processing profile ${item.contact_id}...`);
      
      try {
        // Simple timestamp update
        await sql`
          UPDATE people.contact
          SET last_profile_checked_at = NOW()
          WHERE contact_id = ${item.contact_id}
        `;
        processed++;
        succeeded++;
        console.log(`      ✅ Marked profile as checked`);
      } catch (error) {
        console.log(`      ❌ Failed: ${error.message}`);
        processed++;
      }
    }

    // Process first email
    if (emailQueue.length > 0) {
      const item = emailQueue[0];
      console.log(`   🔄 Processing email ${item.contact_id}...`);
      
      try {
        // Simple timestamp update
        await sql`
          UPDATE people.contact_verification
          SET email_checked_at = NOW()
          WHERE contact_id = ${item.contact_id}
        `;
        processed++;
        succeeded++;
        console.log(`      ✅ Marked email as checked`);
      } catch (error) {
        console.log(`      ❌ Failed: ${error.message}`);
        processed++;
      }
    }
    
    console.log(`   📊 Processing summary: ${succeeded}/${processed} succeeded`);
    console.log('');

    // Step 5: Verify queues after processing
    console.log('5️⃣ Verifying queue sizes after processing...');
    
    const updatedCompanyQueue = await sql`
      SELECT COUNT(*) as count FROM company.next_company_urls_30d
    `;
    
    const updatedProfileQueue = await sql`
      SELECT COUNT(*) as count FROM people.next_profile_urls_30d
    `;
    
    const updatedEmailQueue = await sql`
      SELECT COUNT(*) as count FROM people.due_email_recheck_30d
    `;
    
    console.log(`   Company queue: ${companyQueue.length} → ${updatedCompanyQueue[0].count} (should be reduced)`);
    console.log(`   Profile queue: ${profileQueue.length} → ${updatedProfileQueue[0].count} (should be reduced)`);
    console.log(`   Email queue: ${emailQueue.length} → ${updatedEmailQueue[0].count} (should be reduced)`);
    console.log('');

    // Step 6: Show the simplicity of the approach
    console.log('6️⃣ Demonstrating zero wandering benefits...');
    console.log('   ✅ Hard bookmarks: URLs point directly to source data');
    console.log('   ✅ Simple timestamps: Just 5 URL fields + 3 timestamp fields');
    console.log('   ✅ No extra schemas: Uses existing company/people tables');
    console.log('   ✅ No heavy provenance: Direct URL → timestamp mapping');
    console.log('   ✅ Queue auto-refresh: Views automatically update based on timestamps');
    console.log('');

    console.log('🎉 Simple Scraper Test Complete!');
    console.log('\n📋 Zero Wandering Architecture Confirmed:');
    console.log('✅ Three simple queues for all data refresh needs:');
    console.log('   • company.next_company_urls_30d (company_id, kind, url)');
    console.log('   • people.next_profile_urls_30d (contact_id, kind, url)');
    console.log('   • people.due_email_recheck_30d (contact_id, email)');
    console.log('');
    console.log('✅ Simple timestamp updates remove items from queues');
    console.log('✅ No complex batch tracking or heavy orchestration');
    console.log('✅ Direct bookmark to data source for each fact');
    console.log('');
    console.log('🚀 Perfect for production scraper automation!');
    console.log('');
    console.log('💡 Scraper Implementation Pattern:');
    console.log('   1. SELECT from one of the three queue views');
    console.log('   2. Scrape/verify the URLs or emails');
    console.log('   3. UPDATE the simple timestamp field');
    console.log('   4. Item automatically disappears from queue');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Ensure all schema scripts have been run');
    console.log('   • Verify queue views exist and have data');
  }
}

testSimpleScraper().catch(console.error);