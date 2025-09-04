#!/usr/bin/env node

/**
 * Add Data Refresh Procedures - Update timestamps after data processing
 * Creates stored procedures for marking various data sources as checked
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function addRefreshProcedures() {
  console.log('🔄 Creating Data Refresh Procedures...\n');
  
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
    
    // Step 1: Create company page refresh procedure (improved version)
    console.log('1️⃣ Creating company page refresh procedure...');
    await sql`
      CREATE OR REPLACE FUNCTION company.mark_company_page_checked(
        p_company_id BIGINT,
        p_page_type TEXT
      ) RETURNS TABLE(updated_count INTEGER, message TEXT) AS $$
      DECLARE
        rows_updated INTEGER;
      BEGIN
        UPDATE company.company
        SET last_site_checked_at = CASE WHEN p_page_type = 'website' THEN NOW() ELSE last_site_checked_at END,
            last_linkedin_checked_at = CASE WHEN p_page_type = 'linkedin' THEN NOW() ELSE last_linkedin_checked_at END,
            last_news_checked_at = CASE WHEN p_page_type = 'news' THEN NOW() ELSE last_news_checked_at END
        WHERE company_id = p_company_id;
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        
        IF rows_updated = 0 THEN
          RETURN QUERY SELECT 0, 'Company not found: ' || p_company_id::TEXT;
        ELSE
          RETURN QUERY SELECT rows_updated, 'Updated ' || p_page_type || ' timestamp for company ' || p_company_id::TEXT;
        END IF;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.mark_company_page_checked() created');
    console.log('   🏢 Updates company page timestamps (website/linkedin/news)');
    
    // Step 2: Create person profile refresh procedure (improved version)
    console.log('2️⃣ Creating person profile refresh procedure...');
    await sql`
      CREATE OR REPLACE FUNCTION people.mark_contact_profile_checked(
        p_contact_id BIGINT
      ) RETURNS TABLE(updated_count INTEGER, message TEXT) AS $$
      DECLARE
        rows_updated INTEGER;
      BEGIN
        UPDATE people.contact
        SET last_profile_checked_at = NOW()
        WHERE contact_id = p_contact_id;
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        
        IF rows_updated = 0 THEN
          RETURN QUERY SELECT 0, 'Contact not found: ' || p_contact_id::TEXT;
        ELSE
          RETURN QUERY SELECT rows_updated, 'Updated profile timestamp for contact ' || p_contact_id::TEXT;
        END IF;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ people.mark_contact_profile_checked() created');
    console.log('   👤 Updates contact profile timestamps');
    
    // Step 3: Create email verification refresh procedure (improved version)
    console.log('3️⃣ Creating email verification refresh procedure...');
    await sql`
      CREATE OR REPLACE FUNCTION people.mark_email_verified(
        p_contact_id BIGINT,
        p_source_url TEXT DEFAULT NULL
      ) RETURNS TABLE(updated_count INTEGER, message TEXT) AS $$
      DECLARE
        rows_updated INTEGER;
      BEGIN
        UPDATE people.contact_verification
        SET email_checked_at = NOW(), 
            email_source_url = COALESCE(p_source_url, email_source_url)
        WHERE contact_id = p_contact_id;
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        
        IF rows_updated = 0 THEN
          -- Try to create verification record if it doesn't exist
          INSERT INTO people.contact_verification (contact_id, email_checked_at, email_source_url)
          SELECT p_contact_id, NOW(), p_source_url
          WHERE EXISTS (SELECT 1 FROM people.contact WHERE contact_id = p_contact_id);
          
          GET DIAGNOSTICS rows_updated = ROW_COUNT;
          
          IF rows_updated = 0 THEN
            RETURN QUERY SELECT 0, 'Contact not found: ' || p_contact_id::TEXT;
          ELSE
            RETURN QUERY SELECT rows_updated, 'Created email verification record for contact ' || p_contact_id::TEXT;
          END IF;
        ELSE
          RETURN QUERY SELECT rows_updated, 'Updated email verification timestamp for contact ' || p_contact_id::TEXT;
        END IF;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ people.mark_email_verified() created');
    console.log('   📧 Updates email verification timestamps (creates record if needed)');
    
    // Step 4: Create batch processing procedure
    console.log('4️⃣ Creating batch processing procedures...');
    await sql`
      CREATE OR REPLACE FUNCTION company.process_url_batch(
        p_batch_group INTEGER DEFAULT 1
      ) RETURNS TABLE(
        company_id BIGINT, 
        page_type TEXT, 
        url TEXT, 
        status TEXT
      ) AS $$
      DECLARE
        batch_record RECORD;
      BEGIN
        FOR batch_record IN 
          SELECT b.company_id, b.kind, b.url
          FROM company.vw_next_url_batch b
          WHERE b.batch_group = p_batch_group
          ORDER BY b.company_id, b.kind
        LOOP
          -- Simulate processing (in real implementation, this would call external APIs)
          PERFORM company.mark_company_page_checked(batch_record.company_id, batch_record.kind);
          
          RETURN QUERY SELECT 
            batch_record.company_id,
            batch_record.kind,
            batch_record.url,
            'Processed'::TEXT;
        END LOOP;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.process_url_batch() created');
    console.log('   📦 Processes entire batch of company URLs');
    
    await sql`
      CREATE OR REPLACE FUNCTION people.process_profile_batch(
        p_batch_group INTEGER DEFAULT 1
      ) RETURNS TABLE(
        contact_id BIGINT,
        full_name TEXT,
        url TEXT,
        status TEXT
      ) AS $$
      DECLARE
        batch_record RECORD;
      BEGIN
        FOR batch_record IN 
          SELECT b.contact_id, b.full_name, b.url
          FROM people.vw_next_profile_batch b
          WHERE b.batch_group = p_batch_group
          ORDER BY b.contact_id
        LOOP
          -- Simulate processing
          PERFORM people.mark_contact_profile_checked(batch_record.contact_id);
          
          RETURN QUERY SELECT 
            batch_record.contact_id,
            batch_record.full_name,
            batch_record.url,
            'Processed'::TEXT;
        END LOOP;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ people.process_profile_batch() created');
    console.log('   📦 Processes entire batch of contact profiles');
    
    // Step 5: Test all procedures with sample data
    console.log('5️⃣ Testing data refresh procedures...');
    
    // Test company page refresh
    const companies = await sql`SELECT company_id FROM company.company LIMIT 1`;
    if (companies.length > 0) {
      const companyId = companies[0].company_id;
      
      console.log(`   🧪 Testing company page refresh for company ${companyId}...`);
      
      const websiteResult = await sql`SELECT * FROM company.mark_company_page_checked(${companyId}, 'website')`;
      console.log(`      Website: ${websiteResult[0].message}`);
      
      const linkedinResult = await sql`SELECT * FROM company.mark_company_page_checked(${companyId}, 'linkedin')`;
      console.log(`      LinkedIn: ${linkedinResult[0].message}`);
      
      const newsResult = await sql`SELECT * FROM company.mark_company_page_checked(${companyId}, 'news')`;
      console.log(`      News: ${newsResult[0].message}`);
    }
    
    // Test contact profile refresh
    const contacts = await sql`SELECT contact_id, full_name FROM people.contact LIMIT 1`;
    if (contacts.length > 0) {
      const contactId = contacts[0].contact_id;
      const contactName = contacts[0].full_name;
      
      console.log(`   🧪 Testing profile refresh for ${contactName}...`);
      
      const profileResult = await sql`SELECT * FROM people.mark_contact_profile_checked(${contactId})`;
      console.log(`      Profile: ${profileResult[0].message}`);
      
      const emailResult = await sql`SELECT * FROM people.mark_email_verified(${contactId}, 'test-verification-source')`;
      console.log(`      Email: ${emailResult[0].message}`);
    }
    console.log('');
    
    // Step 6: Create admin schema and monitoring dashboard procedure
    console.log('6️⃣ Creating admin schema and monitoring dashboard procedure...');
    await sql`CREATE SCHEMA IF NOT EXISTS admin`;
    await sql`
      CREATE OR REPLACE FUNCTION admin.get_refresh_status()
      RETURNS TABLE(
        metric TEXT,
        count BIGINT,
        details TEXT
      ) AS $$
      BEGIN
        -- Company URLs needing refresh
        RETURN QUERY 
        SELECT 
          'Company URLs Due'::TEXT,
          COUNT(*),
          STRING_AGG(DISTINCT kind, ', ')
        FROM company.next_company_urls_30d;
        
        -- Contact profiles needing refresh  
        RETURN QUERY
        SELECT 
          'Contact Profiles Due'::TEXT,
          COUNT(*),
          'Profiles needing refresh'::TEXT
        FROM people.next_profile_urls_30d;
        
        -- Email verifications needing refresh
        RETURN QUERY
        SELECT 
          'Email Verifications Due'::TEXT,
          COUNT(*),
          'Emails needing reverification'::TEXT
        FROM people.due_email_recheck_30d;
        
        -- Companies in renewal window
        RETURN QUERY
        SELECT 
          'Companies in Renewal Window'::TEXT,
          COUNT(*),
          'Ready for campaigns'::TEXT
        FROM company.vw_due_renewals_ready;
        
        -- Active BIT signals
        RETURN QUERY
        SELECT 
          'Unprocessed BIT Signals'::TEXT,
          COUNT(*),
          STRING_AGG(DISTINCT reason, ', ')
        FROM bit.signal 
        WHERE processed_at IS NULL;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ admin.get_refresh_status() created');
    console.log('   📊 Provides comprehensive system status dashboard');
    
    // Step 7: Test monitoring dashboard
    console.log('7️⃣ Testing monitoring dashboard...');
    const dashboardStatus = await sql`SELECT * FROM admin.get_refresh_status()`;
    
    console.log('   📊 System Refresh Status Dashboard:');
    dashboardStatus.forEach(status => {
      console.log(`      ${status.metric}: ${status.count} (${status.details})`);
    });
    console.log('');
    
    // Step 8: Create comprehensive batch status view
    console.log('8️⃣ Creating batch status tracking view...');
    await sql`
      CREATE OR REPLACE VIEW admin.vw_batch_status AS
      WITH company_batches AS (
        SELECT 
          'Company URLs' as batch_type,
          batch_group,
          COUNT(*) as items_in_batch,
          STRING_AGG(DISTINCT kind, ', ') as batch_content
        FROM company.vw_next_url_batch
        GROUP BY batch_group
      ),
      profile_batches AS (
        SELECT 
          'Contact Profiles' as batch_type,
          batch_group,
          COUNT(*) as items_in_batch,
          'Profiles' as batch_content
        FROM people.vw_next_profile_batch
        GROUP BY batch_group
      )
      SELECT * FROM company_batches
      UNION ALL
      SELECT * FROM profile_batches
      ORDER BY batch_type, batch_group
    `;
    console.log('   ✅ admin.vw_batch_status view created');
    console.log('   📦 Shows all processing batches across the system');
    
    // Step 9: Test batch status
    console.log('9️⃣ Testing batch status monitoring...');
    const batchStatus = await sql`SELECT * FROM admin.vw_batch_status LIMIT 5`;
    
    if (batchStatus.length > 0) {
      console.log('   📦 Current Processing Batches:');
      batchStatus.forEach(batch => {
        console.log(`      ${batch.batch_type} Batch ${batch.batch_group}: ${batch.items_in_batch} items (${batch.batch_content})`);
      });
    } else {
      console.log('   ✅ No batches currently pending - all data is fresh!');
    }
    console.log('');
    
    console.log('🎉 Data Refresh Procedures Setup Complete!');
    console.log('\n📋 Procedures Created:');
    console.log('✅ company.mark_company_page_checked(company_id, page_type):');
    console.log('   • Updates company page timestamps (website/linkedin/news)');
    console.log('   • Returns success/failure status with message');
    console.log('');
    console.log('✅ people.mark_contact_profile_checked(contact_id):');
    console.log('   • Updates contact profile timestamp');
    console.log('   • Returns success/failure status with message');
    console.log('');
    console.log('✅ people.mark_email_verified(contact_id, source_url):');
    console.log('   • Updates email verification timestamp and source');
    console.log('   • Creates verification record if needed');
    console.log('');
    console.log('✅ Batch Processing Procedures:');
    console.log('✅ company.process_url_batch(batch_group):');
    console.log('   • Processes entire batch of company URLs');
    console.log('   • Returns processing status for each URL');
    console.log('');
    console.log('✅ people.process_profile_batch(batch_group):');
    console.log('   • Processes entire batch of contact profiles');
    console.log('   • Returns processing status for each profile');
    console.log('');
    console.log('✅ Monitoring Procedures:');
    console.log('✅ admin.get_refresh_status():');
    console.log('   • Comprehensive system status dashboard');
    console.log('   • Shows all pending refresh tasks across tables');
    console.log('');
    console.log('✅ admin.vw_batch_status:');
    console.log('   • Shows all processing batches system-wide');
    console.log('');
    console.log('🎯 Usage Examples:');
    console.log('   • Mark company page: SELECT * FROM company.mark_company_page_checked(123, \'website\')');
    console.log('   • Mark profile: SELECT * FROM people.mark_contact_profile_checked(456)');
    console.log('   • Mark email: SELECT * FROM people.mark_email_verified(456, \'mv-source-url\')');
    console.log('   • Process batch: SELECT * FROM company.process_url_batch(1)');
    console.log('   • System status: SELECT * FROM admin.get_refresh_status()');
    console.log('');
    console.log('✅ Ready for automated data refresh orchestration!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify all previous schema scripts have been run');
    console.log('   • Ensure user has CREATE FUNCTION permissions');
  }
}

addRefreshProcedures().catch(console.error);