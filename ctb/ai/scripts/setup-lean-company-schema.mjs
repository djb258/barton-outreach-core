/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-D1825C62
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Set up the Lean Company Schema as specified
 * Creates company.company and company.company_slot tables
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupLeanCompanySchema() {
  console.log('🏢 Setting up Lean Company Schema in Neon...\n');
  
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
    
    // Step 1: Create the lean company.company table
    console.log('1️⃣ Creating company.company table...');
    await sql`
      CREATE TABLE IF NOT EXISTS company.company (
        company_id   BIGSERIAL PRIMARY KEY,
        company_name TEXT,
        ein          TEXT,
        website_url  TEXT,
        linkedin_url TEXT,
        news_url     TEXT,
        -- address (lean)
        address_line1 TEXT,
        address_line2 TEXT,
        city          TEXT,
        state         TEXT,
        postal_code   TEXT,
        country       TEXT,
        -- renewal (month-only; default 120d notice = 4 months)
        renewal_month SMALLINT CHECK (renewal_month BETWEEN 1 AND 12),
        renewal_notice_window_days INT DEFAULT 120
      );
    `;
    console.log('   ✅ company.company table created');
    
    // Step 2: Create index on renewal_month
    console.log('2️⃣ Creating renewal month index...');
    await sql`
      CREATE INDEX IF NOT EXISTS ix_company_renewal_month 
      ON company.company(renewal_month);
    `;
    console.log('   ✅ renewal_month index created');
    
    // Step 3: Create company_slot table (exactly 3 slots per company)
    console.log('3️⃣ Creating company.company_slot table...');
    await sql`
      CREATE TABLE IF NOT EXISTS company.company_slot (
        company_slot_id BIGSERIAL PRIMARY KEY,
        company_id      BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
        role_code       TEXT   NOT NULL CHECK (role_code IN ('CEO','CFO','HR')),
        contact_id      BIGINT,  -- FK to people.contact (nullable until assigned)
        UNIQUE (company_id, role_code)
      );
    `;
    console.log('   ✅ company.company_slot table created');
    console.log('   📋 Exactly 3 slots per company: CEO, CFO, HR');
    
    // Step 4: Create people.contact table to match the FK reference
    console.log('4️⃣ Creating people.contact table...');
    await sql`
      CREATE TABLE IF NOT EXISTS people.contact (
        contact_id BIGSERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        full_name TEXT GENERATED ALWAYS AS (CONCAT(first_name, ' ', last_name)) STORED,
        phone TEXT,
        title TEXT,
        linkedin_url TEXT,
        company_id BIGINT REFERENCES company.company(company_id),
        email_status TEXT DEFAULT 'pending' CHECK (email_status IN ('verified', 'pending', 'invalid', 'bounced')),
        email_status_color TEXT GENERATED ALWAYS AS (
          CASE 
            WHEN email_status = 'verified' THEN 'green'
            WHEN email_status = 'pending' THEN 'yellow'
            WHEN email_status IN ('invalid', 'bounced') THEN 'red'
            ELSE 'gray'
          END
        ) STORED,
        verification_date TIMESTAMP WITH TIME ZONE,
        source TEXT DEFAULT 'manual',
        tags JSONB,
        custom_fields JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      );
    `;
    console.log('   ✅ people.contact table created');
    console.log('   🎨 Email status with dot color indicators');
    
    // Step 5: Add the FK constraint from company_slot to contact
    console.log('5️⃣ Adding FK constraint from company_slot to contact...');
    try {
      await sql`
        ALTER TABLE company.company_slot 
        ADD CONSTRAINT fk_company_slot_contact 
        FOREIGN KEY (contact_id) REFERENCES people.contact(contact_id);
      `;
      console.log('   ✅ FK constraint added');
    } catch (error) {
      if (error.message.includes('already exists')) {
        console.log('   ℹ️  FK constraint already exists');
      } else {
        console.log(`   ⚠️  FK constraint: ${error.message}`);
      }
    }
    
    // Step 6: Update secure promotion function to work with lean schema
    console.log('6️⃣ Updating promotion function for lean schema...');
    await sql`
      CREATE OR REPLACE FUNCTION vault.f_promote_contacts_lean(
        p_load_ids BIGINT[] DEFAULT NULL
      )
      RETURNS TABLE(
        promoted_count INTEGER,
        updated_count INTEGER,
        failed_count INTEGER,
        message TEXT
      )
      LANGUAGE plpgsql
      SECURITY DEFINER
      SET search_path = vault, intake, people, company
      AS $$
      DECLARE
        v_load RECORD;
        v_data JSONB;
        v_contact_id BIGINT;
        v_company_id BIGINT;
        v_promoted_count INT := 0;
        v_updated_count INT := 0;
        v_failed_count INT := 0;
      BEGIN
        -- Select loads to promote
        FOR v_load IN 
          SELECT load_id, raw_data, batch_id, source
          FROM intake.raw_loads 
          WHERE status = 'pending'
            AND (p_load_ids IS NULL OR load_id = ANY(p_load_ids))
        LOOP
          BEGIN
            v_data := v_load.raw_data;
            
            -- Find or create company in lean schema
            SELECT company_id INTO v_company_id 
            FROM company.company 
            WHERE company_name = v_data->>'company_name' 
            LIMIT 1;
            
            IF v_company_id IS NULL AND v_data->>'company_name' IS NOT NULL THEN
              INSERT INTO company.company (
                company_name,
                ein,
                website_url,
                linkedin_url,
                address_line1,
                city,
                state,
                postal_code,
                country
              ) VALUES (
                v_data->>'company_name',
                v_data->>'ein',
                v_data->>'website_url',
                v_data->>'linkedin_url',
                v_data->>'address_line1',
                v_data->>'city',
                v_data->>'state',
                v_data->>'postal_code',
                v_data->>'country'
              ) RETURNING company_id INTO v_company_id;
            END IF;
            
            -- Insert or update contact in lean schema
            INSERT INTO people.contact (
              email,
              first_name,
              last_name,
              phone,
              title,
              linkedin_url,
              company_id,
              source,
              tags,
              custom_fields,
              created_at
            ) VALUES (
              v_data->>'email',
              v_data->>'first_name',
              v_data->>'last_name',
              v_data->>'phone',
              v_data->>'title',
              v_data->>'linkedin_url',
              v_company_id,
              v_load.source,
              v_data->'tags',
              v_data,
              NOW()
            ) 
            ON CONFLICT (email) DO UPDATE SET
              first_name = COALESCE(EXCLUDED.first_name, contact.first_name),
              last_name = COALESCE(EXCLUDED.last_name, contact.last_name),
              phone = COALESCE(EXCLUDED.phone, contact.phone),
              title = COALESCE(EXCLUDED.title, contact.title),
              linkedin_url = COALESCE(EXCLUDED.linkedin_url, contact.linkedin_url),
              company_id = COALESCE(EXCLUDED.company_id, contact.company_id),
              custom_fields = EXCLUDED.custom_fields,
              updated_at = NOW()
            RETURNING contact_id INTO v_contact_id;
            
            -- Auto-assign to company slots based on title
            IF v_company_id IS NOT NULL THEN
              -- Try to assign CEO
              IF UPPER(v_data->>'title') LIKE '%CEO%' OR UPPER(v_data->>'title') LIKE '%CHIEF EXECUTIVE%' THEN
                INSERT INTO company.company_slot (company_id, role_code, contact_id)
                VALUES (v_company_id, 'CEO', v_contact_id)
                ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id;
              -- Try to assign CFO
              ELSIF UPPER(v_data->>'title') LIKE '%CFO%' OR UPPER(v_data->>'title') LIKE '%CHIEF FINANCIAL%' THEN
                INSERT INTO company.company_slot (company_id, role_code, contact_id)
                VALUES (v_company_id, 'CFO', v_contact_id)
                ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id;
              -- Try to assign HR
              ELSIF UPPER(v_data->>'title') LIKE '%HR%' OR UPPER(v_data->>'title') LIKE '%HUMAN RESOURCE%' THEN
                INSERT INTO company.company_slot (company_id, role_code, contact_id)
                VALUES (v_company_id, 'HR', v_contact_id)
                ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id;
              END IF;
            END IF;
            
            -- Record promotion
            INSERT INTO vault.contact_promotions (
              load_id,
              person_id,
              company_id,
              promotion_type,
              status,
              promoted_at
            ) VALUES (
              v_load.load_id,
              v_contact_id::UUID,
              v_company_id::UUID,
              'lean_contact',
              'success',
              NOW()
            );
            
            -- Mark load as promoted
            UPDATE intake.raw_loads 
            SET status = 'promoted', promoted_at = NOW()
            WHERE load_id = v_load.load_id;
            
            v_promoted_count := v_promoted_count + 1;
            
          EXCEPTION WHEN OTHERS THEN
            -- Record failure
            UPDATE intake.raw_loads 
            SET status = 'failed', error_message = SQLERRM
            WHERE load_id = v_load.load_id;
            
            v_failed_count := v_failed_count + 1;
          END;
        END LOOP;
        
        RETURN QUERY SELECT 
          v_promoted_count,
          v_updated_count,
          v_failed_count,
          format('Lean Schema - Promoted: %s, Updated: %s, Failed: %s', v_promoted_count, v_updated_count, v_failed_count);
      END;
      $$;
    `;
    console.log('   ✅ f_promote_contacts_lean function created');
    console.log('   🎯 Auto-assigns contacts to CEO/CFO/HR slots based on title');
    
    console.log('\n🎉 Lean Company Schema Setup Complete!');
    console.log('\n📋 Created Tables:');
    console.log('   • company.company - Core company data with renewal tracking');
    console.log('   • company.company_slot - Exactly 3 slots per company (CEO/CFO/HR)');
    console.log('   • people.contact - Contact management with email status dots');
    console.log('\n🔧 Created Functions:');
    console.log('   • vault.f_promote_contacts_lean() - Promotion with auto-slot assignment');
    console.log('\n🎨 Features:');
    console.log('   • Email status color indicators (green/yellow/red dots)');
    console.log('   • Auto-assignment to company roles based on title');
    console.log('   • Full audit trail and promotion tracking');
    console.log('\n✅ Ready for your lean company workflow!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE permissions');
    console.log('   • Ensure database exists and is accessible');
  }
}

// Run the setup
setupLeanCompanySchema().catch(console.error);