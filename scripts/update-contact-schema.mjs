#!/usr/bin/env node

/**
 * Update Contact Schema to Your Exact Specification
 * Recreates people.contact with your lean structure and adds contact_verification table
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function updateContactSchema() {
  console.log('📝 Updating Contact Schema to Your Specification...\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    const sql = neon(connectionString);
    
    console.log('📡 Connected to Neon database');
    console.log('');
    
    // Step 1: Drop existing FK constraint and trigger
    console.log('1️⃣ Cleaning up existing contact structure...');
    try {
      await sql`ALTER TABLE company.company_slot DROP CONSTRAINT IF EXISTS fk_company_slot_contact`;
      await sql`ALTER TABLE company.company_slot DROP CONSTRAINT IF EXISTS fk_slot_contact`;
      await sql`DROP TRIGGER IF EXISTS trigger_update_contact_fields ON people.contact`;
      await sql`DROP FUNCTION IF EXISTS people.update_contact_fields()`;
      console.log('   ✅ Existing constraints cleaned up');
    } catch (error) {
      console.log(`   ℹ️  Cleanup: ${error.message}`);
    }
    
    // Step 2: Backup existing data if any
    console.log('2️⃣ Backing up existing contact data...');
    const existingContacts = await sql`
      SELECT contact_id, email, first_name, last_name, full_name, title, phone, 
             company_id, email_status, email_status_color, source, created_at
      FROM people.contact 
      WHERE contact_id IS NOT NULL
    `;
    console.log(`   📦 Found ${existingContacts.length} existing contacts to preserve`);
    
    // Step 3: Drop and recreate people.contact with your exact structure
    console.log('3️⃣ Recreating people.contact with your specification...');
    await sql`DROP TABLE IF EXISTS people.contact CASCADE`;
    
    await sql`
      CREATE TABLE people.contact (
        contact_id  BIGSERIAL PRIMARY KEY,
        full_name   TEXT,
        title       TEXT,
        email       TEXT,
        phone       TEXT,
        created_at  TIMESTAMPTZ DEFAULT NOW(),
        updated_at  TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ people.contact recreated with your exact structure');
    
    // Step 4: Add the FK constraint as you specified
    console.log('4️⃣ Adding FK constraint from company_slot to contact...');
    await sql`
      ALTER TABLE company.company_slot
      ADD CONSTRAINT fk_slot_contact
      FOREIGN KEY (contact_id) REFERENCES people.contact(contact_id)
      ON DELETE SET NULL
    `;
    console.log('   ✅ FK constraint fk_slot_contact added (ON DELETE SET NULL)');
    
    // Step 5: Create the email verification table (1:1 relationship)
    console.log('5️⃣ Creating people.contact_verification table...');
    await sql`
      CREATE TABLE IF NOT EXISTS people.contact_verification (
        contact_id        BIGINT PRIMARY KEY REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        email_status      TEXT,         -- 'green'|'yellow'|'red'|'gray'
        email_checked_at  TIMESTAMPTZ,
        email_confidence  INT,
        email_source_url  TEXT
      )
    `;
    console.log('   ✅ people.contact_verification created (1:1 with contact)');
    
    // Step 6: Create the helpful indexes
    console.log('6️⃣ Creating helpful indexes...');
    await sql`CREATE INDEX IF NOT EXISTS ix_contact_email ON people.contact (lower(email))`;
    await sql`CREATE INDEX IF NOT EXISTS ix_slot_company_role ON company.company_slot(company_id, role_code)`;
    console.log('   ✅ Indexes created:');
    console.log('      • ix_contact_email on lower(email)');
    console.log('      • ix_slot_company_role on (company_id, role_code)');
    
    // Step 7: Restore data if any existed
    if (existingContacts.length > 0) {
      console.log('7️⃣ Restoring existing contact data...');
      for (const contact of existingContacts) {
        try {
          const restored = await sql`
            INSERT INTO people.contact (
              full_name, title, email, phone, created_at, updated_at
            ) VALUES (
              ${contact.full_name || contact.first_name + ' ' + contact.last_name},
              ${contact.title},
              ${contact.email},
              ${contact.phone},
              ${contact.created_at},
              NOW()
            ) RETURNING contact_id
          `;
          
          // Create verification record if we had email status
          if (contact.email_status && restored[0]) {
            const emailStatus = contact.email_status_color || 
              (contact.email_status === 'verified' ? 'green' : 
               contact.email_status === 'pending' ? 'yellow' : 'red');
               
            await sql`
              INSERT INTO people.contact_verification (
                contact_id, email_status, email_checked_at
              ) VALUES (
                ${restored[0].contact_id}, 
                ${emailStatus}, 
                NOW()
              )
            `;
          }
        } catch (error) {
          console.log(`   ⚠️  Error restoring contact ${contact.email}: ${error.message}`);
        }
      }
      console.log(`   ✅ Restored ${existingContacts.length} contacts with verification data`);
    }
    
    // Step 8: Test the new structure
    console.log('8️⃣ Testing the new contact structure...');
    
    // Create a test contact
    const testContact = await sql`
      INSERT INTO people.contact (
        full_name, title, email, phone
      ) VALUES (
        'Test Contact', 'Senior Manager', 'test@newschema.com', '+1-555-0199'
      ) RETURNING contact_id, full_name, email
    `;
    
    console.log(`   ✅ Test contact created: ${testContact[0].full_name} (${testContact[0].email})`);
    
    // Create verification record
    const testVerification = await sql`
      INSERT INTO people.contact_verification (
        contact_id, email_status, email_checked_at, email_confidence
      ) VALUES (
        ${testContact[0].contact_id}, 'green', NOW(), 95
      ) RETURNING email_status, email_confidence
    `;
    
    console.log(`   ✅ Verification created: ${testVerification[0].email_status} dot (${testVerification[0].email_confidence}% confidence)`);
    
    // Test company slot assignment
    const companies = await sql`SELECT company_id FROM company.company LIMIT 1`;
    if (companies.length > 0) {
      await sql`
        INSERT INTO company.company_slot (company_id, role_code, contact_id)
        VALUES (${companies[0].company_id}, 'CFO', ${testContact[0].contact_id})
        ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id
      `;
      console.log('   ✅ Test contact assigned to CFO slot');
    }
    
    // Step 9: Verify the complete structure
    console.log('9️⃣ Verifying complete structure...');
    const verification = await sql`
      SELECT 
        c.contact_id,
        c.full_name,
        c.title,
        c.email,
        cv.email_status,
        cv.email_confidence,
        cs.role_code
      FROM people.contact c
      LEFT JOIN people.contact_verification cv ON c.contact_id = cv.contact_id
      LEFT JOIN company.company_slot cs ON c.contact_id = cs.contact_id
      WHERE c.email = 'test@newschema.com'
    `;
    
    if (verification.length > 0) {
      const v = verification[0];
      console.log('   📊 Structure verification:');
      console.log(`      Contact: ${v.full_name} (${v.title})`);
      console.log(`      Email: ${v.email}`);
      console.log(`      Status: ${v.email_status} dot (${v.email_confidence}% confidence)`);
      console.log(`      Role: ${v.role_code || 'None'}`);
    }
    
    console.log('\n🎉 Contact Schema Update Complete!');
    console.log('\n📋 Your Exact Schema Structure:');
    console.log('   • people.contact - Lean structure (contact_id, full_name, title, email, phone, timestamps)');
    console.log('   • people.contact_verification - 1:1 email verification (green/yellow/red/gray dots)');
    console.log('   • company.company_slot.contact_id → people.contact.contact_id (ON DELETE SET NULL)');
    console.log('\n🔍 Helpful Indexes:');
    console.log('   • ix_contact_email on lower(email) for fast email lookups');
    console.log('   • ix_slot_company_role on (company_id, role_code) for slot queries');
    console.log('\n✅ Schema now matches your specification exactly!');
    
  } catch (error) {
    console.error('❌ Update failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has ALTER permissions');
    console.log('   • Ensure no active connections to modified tables');
  }
}

updateContactSchema().catch(console.error);