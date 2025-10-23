/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-09E2918A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Add URL Queue View - Company data refresh queue
 * Creates view to identify company URLs needing refresh checks
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function addUrlQueueView() {
  console.log('🔄 Creating URL Queue View for Data Refresh...\n');
  
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
    
    // Step 1: Create the URL queue view
    console.log('1️⃣ Creating next_company_urls_30d view...');
    await sql`
      CREATE OR REPLACE VIEW company.next_company_urls_30d AS
      SELECT company_id, 'website' AS kind, website_url AS url
      FROM company.company
      WHERE website_url IS NOT NULL
        AND (last_site_checked_at IS NULL OR last_site_checked_at < NOW() - INTERVAL '30 days')
      UNION ALL
      SELECT company_id, 'linkedin' AS kind, linkedin_url AS url
      FROM company.company
      WHERE linkedin_url IS NOT NULL
        AND (last_linkedin_checked_at IS NULL OR last_linkedin_checked_at < NOW() - INTERVAL '30 days')
      UNION ALL
      SELECT company_id, 'news' AS kind, news_url AS url
      FROM company.company
      WHERE news_url IS NOT NULL
        AND (last_news_checked_at IS NULL OR last_news_checked_at < NOW() - INTERVAL '30 days')
    `;
    console.log('   ✅ company.next_company_urls_30d view created');
    console.log('   📊 Identifies URLs needing refresh (30+ days old or never checked)');
    
    // Step 2: Test the view with current data
    console.log('2️⃣ Testing URL queue view...');
    const urlQueue = await sql`
      SELECT 
        company_id,
        kind,
        url,
        CASE kind
          WHEN 'website' THEN (SELECT last_site_checked_at FROM company.company c WHERE c.company_id = q.company_id)
          WHEN 'linkedin' THEN (SELECT last_linkedin_checked_at FROM company.company c WHERE c.company_id = q.company_id)
          WHEN 'news' THEN (SELECT last_news_checked_at FROM company.company c WHERE c.company_id = q.company_id)
        END as last_checked
      FROM company.next_company_urls_30d q
      ORDER BY company_id, kind
    `;
    
    console.log(`   📋 Found ${urlQueue.length} URLs in refresh queue:`);
    urlQueue.forEach(item => {
      const lastChecked = item.last_checked 
        ? new Date(item.last_checked).toLocaleDateString()
        : 'Never';
      console.log(`      Company ${item.company_id} ${item.kind}: ${item.url}`);
      console.log(`         Last checked: ${lastChecked}`);
    });
    console.log('');
    
    // Step 3: Create a summary view for monitoring
    console.log('3️⃣ Creating URL queue summary view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_url_queue_summary AS
      SELECT 
        kind,
        COUNT(*) as urls_due_for_refresh,
        COUNT(DISTINCT company_id) as companies_affected
      FROM company.next_company_urls_30d
      GROUP BY kind
      ORDER BY kind
    `;
    console.log('   ✅ vw_url_queue_summary view created');
    console.log('   📊 Provides refresh queue statistics by URL type');
    
    // Step 4: Test the summary view
    console.log('4️⃣ Testing URL queue summary...');
    const queueSummary = await sql`
      SELECT * FROM company.vw_url_queue_summary
    `;
    
    console.log('   📊 URL Refresh Queue Summary:');
    queueSummary.forEach(summary => {
      console.log(`      ${summary.kind}: ${summary.urls_due_for_refresh} URLs from ${summary.companies_affected} companies`);
    });
    console.log('');
    
    // Step 5: Create a function to mark URL as checked
    console.log('5️⃣ Creating URL check update function...');
    await sql`
      CREATE OR REPLACE FUNCTION company.mark_url_checked(
        p_company_id BIGINT,
        p_kind TEXT
      ) RETURNS VOID AS $$
      BEGIN
        CASE p_kind
          WHEN 'website' THEN
            UPDATE company.company 
            SET last_site_checked_at = NOW() 
            WHERE company_id = p_company_id;
          WHEN 'linkedin' THEN
            UPDATE company.company 
            SET last_linkedin_checked_at = NOW() 
            WHERE company_id = p_company_id;
          WHEN 'news' THEN
            UPDATE company.company 
            SET last_news_checked_at = NOW() 
            WHERE company_id = p_company_id;
        END CASE;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.mark_url_checked() function created');
    console.log('   🔄 Updates last-checked timestamp for specified URL type');
    
    // Step 6: Test the update function
    console.log('6️⃣ Testing URL check update function...');
    
    if (urlQueue.length > 0) {
      const testUrl = urlQueue[0];
      
      console.log(`   🧪 Simulating ${testUrl.kind} check for company ${testUrl.company_id}...`);
      await sql`SELECT company.mark_url_checked(${testUrl.company_id}, ${testUrl.kind})`;
      
      // Verify the update worked
      const afterUpdate = await sql`
        SELECT COUNT(*) as remaining
        FROM company.next_company_urls_30d
        WHERE company_id = ${testUrl.company_id} AND kind = ${testUrl.kind}
      `;
      
      console.log(`   ✅ URL marked as checked - ${afterUpdate[0].remaining} URLs remaining in queue for this company/type`);
      
      // Reset for demo purposes
      await sql`
        UPDATE company.company 
        SET last_site_checked_at = NOW() - INTERVAL '7 days',
            last_linkedin_checked_at = NOW() - INTERVAL '14 days',
            last_news_checked_at = NOW() - INTERVAL '3 days'
        WHERE company_id = ${testUrl.company_id}
      `;
      console.log('   🔄 Reset timestamps for demo purposes');
    }
    
    // Step 7: Create batch processing view
    console.log('7️⃣ Creating batch processing view...');
    await sql`
      CREATE OR REPLACE VIEW company.vw_next_url_batch AS
      WITH numbered AS (
        SELECT 
          company_id,
          kind,
          url,
          ROW_NUMBER() OVER (ORDER BY company_id, kind) as batch_number
        FROM company.next_company_urls_30d
      )
      SELECT 
        company_id,
        kind,
        url,
        CEIL(batch_number / 10.0) as batch_group
      FROM numbered
      ORDER BY batch_group, company_id, kind
    `;
    console.log('   ✅ vw_next_url_batch view created');
    console.log('   📦 Organizes URLs into batches of 10 for processing');
    
    // Step 8: Test batch processing view
    console.log('8️⃣ Testing batch processing view...');
    const batchTest = await sql`
      SELECT 
        batch_group,
        COUNT(*) as urls_in_batch,
        STRING_AGG(DISTINCT kind, ', ') as url_types
      FROM company.vw_next_url_batch
      GROUP BY batch_group
      ORDER BY batch_group
      LIMIT 3
    `;
    
    console.log('   📦 URL Processing Batches:');
    batchTest.forEach(batch => {
      console.log(`      Batch ${batch.batch_group}: ${batch.urls_in_batch} URLs (${batch.url_types})`);
    });
    console.log('');
    
    console.log('🎉 URL Queue View Setup Complete!');
    console.log('\n📋 Views Created:');
    console.log('✅ company.next_company_urls_30d:');
    console.log('   • Lists all company URLs needing refresh (30+ days old)');
    console.log('   • Combines website, LinkedIn, and news URLs');
    console.log('   • Ready for automated crawling/checking');
    console.log('');
    console.log('✅ company.vw_url_queue_summary:');
    console.log('   • Statistics on URLs due for refresh by type');
    console.log('   • Monitoring dashboard data');
    console.log('');
    console.log('✅ company.vw_next_url_batch:');
    console.log('   • Organizes URLs into processing batches of 10');
    console.log('   • Prevents overwhelming external APIs');
    console.log('');
    console.log('✅ Function Created:');
    console.log('✅ company.mark_url_checked(company_id, kind):');
    console.log('   • Updates last-checked timestamp after processing URL');
    console.log('   • Removes URL from refresh queue');
    console.log('');
    console.log('🎯 Usage Examples:');
    console.log('   • Get next batch: SELECT * FROM company.vw_next_url_batch WHERE batch_group = 1');
    console.log('   • Mark as checked: SELECT company.mark_url_checked(123, \'website\')');
    console.log('   • Monitor queue: SELECT * FROM company.vw_url_queue_summary');
    console.log('');
    console.log('✅ Ready for automated company data refresh workflows!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify anchor columns exist (run add-anchor-columns.mjs first)');
    console.log('   • Ensure user has CREATE VIEW permissions');
  }
}

addUrlQueueView().catch(console.error);