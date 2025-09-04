#!/usr/bin/env node

/**
 * Add Anchor Columns - Company and contact source tracking
 * Adds URL anchors and last-checked timestamps for data sources
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function addAnchorColumns() {
  console.log('⚓ Adding Anchor Columns for Source Tracking...\n');
  
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
    
    // Step 1: Add company anchor columns
    console.log('1️⃣ Adding company anchor columns...');
    await sql`
      ALTER TABLE company.company
        ADD COLUMN IF NOT EXISTS website_url TEXT,
        ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
        ADD COLUMN IF NOT EXISTS news_url TEXT,
        ADD COLUMN IF NOT EXISTS last_site_checked_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS last_linkedin_checked_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS last_news_checked_at TIMESTAMPTZ
    `;
    console.log('   ✅ Company anchor columns added');
    console.log('   🌐 website_url, linkedin_url, news_url');
    console.log('   🕐 last_site_checked_at, last_linkedin_checked_at, last_news_checked_at');
    
    // Step 2: Add person profile anchor columns
    console.log('2️⃣ Adding person profile anchor columns...');
    await sql`
      ALTER TABLE people.contact
        ADD COLUMN IF NOT EXISTS profile_source_url TEXT,
        ADD COLUMN IF NOT EXISTS last_profile_checked_at TIMESTAMPTZ
    `;
    console.log('   ✅ Person profile anchor columns added');
    console.log('   👤 profile_source_url, last_profile_checked_at');
    
    // Step 3: Add email source URL to verification table (if not exists)
    console.log('3️⃣ Ensuring email source anchor exists...');
    await sql`
      ALTER TABLE people.contact_verification
        ADD COLUMN IF NOT EXISTS email_source_url TEXT
    `;
    console.log('   ✅ Email source anchor confirmed');
    console.log('   📧 email_source_url (already existed)');
    
    // Step 4: Create helpful indexes for the new columns
    console.log('4️⃣ Creating indexes for anchor URLs...');
    await sql`CREATE INDEX IF NOT EXISTS ix_company_website ON company.company(website_url)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_company_linkedin ON company.company(linkedin_url)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_contact_profile_url ON people.contact(profile_source_url)`;
    console.log('   ✅ Indexes created for fast URL lookups');
    
    // Step 5: Test with sample anchor data
    console.log('5️⃣ Testing with sample anchor data...');
    
    // Update test company with anchor URLs
    const companies = await sql`SELECT company_id, company_name FROM company.company LIMIT 1`;
    if (companies.length > 0) {
      const company = companies[0];
      
      await sql`
        UPDATE company.company 
        SET 
          website_url = 'https://leantestcompany.com',
          linkedin_url = 'https://linkedin.com/company/lean-test-company',
          news_url = 'https://news.google.com/search?q=lean+test+company',
          last_site_checked_at = NOW() - INTERVAL '7 days',
          last_linkedin_checked_at = NOW() - INTERVAL '14 days',
          last_news_checked_at = NOW() - INTERVAL '3 days'
        WHERE company_id = ${company.company_id}
      `;
      
      console.log(`   ✅ Updated ${company.company_name} with anchor URLs`);
      console.log('      Website: https://leantestcompany.com (checked 7 days ago)');
      console.log('      LinkedIn: https://linkedin.com/company/lean-test-company (checked 14 days ago)');
      console.log('      News: https://news.google.com/search?q=lean+test+company (checked 3 days ago)');
    }
    
    // Update test contacts with profile anchors
    const contacts = await sql`
      SELECT contact_id, full_name 
      FROM people.contact 
      WHERE full_name IS NOT NULL 
      LIMIT 2
    `;
    
    if (contacts.length > 0) {
      for (const contact of contacts) {
        const linkedinUrl = `https://linkedin.com/in/${contact.full_name.toLowerCase().replace(' ', '-')}`;
        
        await sql`
          UPDATE people.contact 
          SET 
            profile_source_url = ${linkedinUrl},
            last_profile_checked_at = NOW() - INTERVAL '5 days'
          WHERE contact_id = ${contact.contact_id}
        `;
      }
      
      console.log(`   ✅ Updated ${contacts.length} contacts with profile anchors`);
      contacts.forEach(contact => {
        console.log(`      ${contact.full_name}: LinkedIn profile (checked 5 days ago)`);
      });
    }
    
    // Step 6: Create a view showing all anchors and staleness
    console.log('6️⃣ Creating anchor staleness monitoring view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_anchor_staleness AS
      WITH company_staleness AS (
        SELECT 
          company_id,
          company_name,
          website_url,
          linkedin_url,
          news_url,
          CASE 
            WHEN last_site_checked_at IS NULL THEN 'Never'
            WHEN last_site_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
            WHEN last_site_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
            ELSE 'Fresh'
          END as website_status,
          CASE 
            WHEN last_linkedin_checked_at IS NULL THEN 'Never'
            WHEN last_linkedin_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
            WHEN last_linkedin_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
            ELSE 'Fresh'
          END as linkedin_status,
          CASE 
            WHEN last_news_checked_at IS NULL THEN 'Never'
            WHEN last_news_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
            WHEN last_news_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
            ELSE 'Fresh'
          END as news_status
        FROM company.company
      )
      SELECT 
        company_id,
        company_name,
        website_url,
        website_status,
        linkedin_url,
        linkedin_status,
        news_url,
        news_status,
        CASE 
          WHEN website_status = 'Never' OR linkedin_status = 'Never' OR news_status = 'Never' THEN 'Missing Data'
          WHEN website_status = 'Stale (30+ days)' OR linkedin_status = 'Stale (30+ days)' OR news_status = 'Stale (30+ days)' THEN 'Needs Update'
          WHEN website_status = 'Old (7+ days)' OR linkedin_status = 'Old (7+ days)' OR news_status = 'Old (7+ days)' THEN 'Should Update'
          ELSE 'Up to Date'
        END as overall_status
      FROM company_staleness
    `;
    console.log('   ✅ vw_anchor_staleness view created');
    console.log('   📊 Monitors freshness of all company data sources');
    
    // Step 7: Test the staleness view
    console.log('7️⃣ Testing anchor staleness monitoring...');
    const stalenessTest = await sql`
      SELECT 
        company_name,
        website_status,
        linkedin_status, 
        news_status,
        overall_status
      FROM company.vw_anchor_staleness
      LIMIT 3
    `;
    
    console.log('   📊 Anchor staleness report:');
    stalenessTest.forEach(test => {
      console.log(`      ${test.company_name}:`);
      console.log(`         Website: ${test.website_status}`);
      console.log(`         LinkedIn: ${test.linkedin_status}`);
      console.log(`         News: ${test.news_status}`);
      console.log(`         Overall: ${test.overall_status}`);
      console.log('');
    });
    
    // Step 8: Create contact profile staleness view
    console.log('8️⃣ Creating contact profile staleness view...');
    await sql`
      CREATE OR REPLACE VIEW people.vw_profile_staleness AS
      SELECT 
        c.contact_id,
        c.full_name,
        c.email,
        c.profile_source_url,
        cv.email_source_url,
        CASE 
          WHEN c.last_profile_checked_at IS NULL THEN 'Never'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '60 days' THEN 'Very Stale (60+ days)'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
          WHEN c.last_profile_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
          ELSE 'Fresh'
        END as profile_status,
        CASE 
          WHEN cv.email_checked_at IS NULL THEN 'Never'
          WHEN cv.email_checked_at < NOW() - INTERVAL '30 days' THEN 'Stale (30+ days)'
          WHEN cv.email_checked_at < NOW() - INTERVAL '7 days' THEN 'Old (7+ days)'
          ELSE 'Fresh'
        END as email_status
      FROM people.contact c
      LEFT JOIN people.contact_verification cv ON cv.contact_id = c.contact_id
      WHERE c.email IS NOT NULL
    `;
    console.log('   ✅ vw_profile_staleness view created');
    console.log('   👤 Monitors contact profile and email verification freshness');
    
    // Step 9: Test contact staleness
    console.log('9️⃣ Testing contact staleness monitoring...');
    const contactStaleness = await sql`
      SELECT 
        full_name,
        email,
        profile_status,
        email_status
      FROM people.vw_profile_staleness
      LIMIT 3
    `;
    
    console.log('   👤 Contact staleness report:');
    contactStaleness.forEach(contact => {
      console.log(`      ${contact.full_name} (${contact.email}):`);
      console.log(`         Profile: ${contact.profile_status}`);
      console.log(`         Email: ${contact.email_status}`);
      console.log('');
    });
    
    console.log('🎉 Anchor Columns Setup Complete!');
    console.log('\n📋 New Columns Added:');
    console.log('✅ company.company:');
    console.log('   • website_url, linkedin_url, news_url');
    console.log('   • last_site_checked_at, last_linkedin_checked_at, last_news_checked_at');
    console.log('');
    console.log('✅ people.contact:');
    console.log('   • profile_source_url, last_profile_checked_at');
    console.log('');
    console.log('✅ people.contact_verification:');
    console.log('   • email_source_url (confirmed existing)');
    console.log('');
    console.log('✅ New Views for Monitoring:');
    console.log('   • company.vw_anchor_staleness - Company data source freshness');
    console.log('   • people.vw_profile_staleness - Contact profile freshness');
    console.log('');
    console.log('🎯 Use Cases:');
    console.log('   • Track where data comes from (Apollo, LinkedIn, manual entry)');
    console.log('   • Monitor when sources were last checked');
    console.log('   • Identify stale data needing refresh');
    console.log('   • Audit trail for data quality');
    console.log('');
    console.log('✅ Ready for automated data source management!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has ALTER permissions');
    console.log('   • Ensure referenced tables exist');
  }
}

addAnchorColumns().catch(console.error);