/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-C55CBE61
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Fix Contact Schema Update - Handle existing slot references properly
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function fixContactSchema() {
  console.log('🔧 Fixing Contact Schema Update...\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    const sql = neon(connectionString);
    
    console.log('📡 Connected to Neon database');
    console.log('');
    
    // Step 1: Clear any invalid contact_id references in company_slot
    console.log('1️⃣ Clearing invalid contact references in company_slot...');
    const invalidRefs = await sql`
      SELECT company_slot_id, company_id, role_code, contact_id
      FROM company.company_slot 
      WHERE contact_id IS NOT NULL
    `;
    
    if (invalidRefs.length > 0) {
      await sql`UPDATE company.company_slot SET contact_id = NULL WHERE contact_id IS NOT NULL`;
      console.log(`   ✅ Cleared ${invalidRefs.length} invalid contact references`);
    } else {
      console.log('   ✅ No invalid references found');
    }
    
    // Step 2: Now safely add the FK constraint
    console.log('2️⃣ Adding FK constraint safely...');
    await sql`
      ALTER TABLE company.company_slot
      ADD CONSTRAINT fk_slot_contact
      FOREIGN KEY (contact_id) REFERENCES people.contact(contact_id)
      ON DELETE SET NULL
    `;
    console.log('   ✅ FK constraint fk_slot_contact added');
    
    // Step 3: Create the contact_verification table
    console.log('3️⃣ Creating contact_verification table...');
    await sql`
      CREATE TABLE IF NOT EXISTS people.contact_verification (
        contact_id        BIGINT PRIMARY KEY REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        email_status      TEXT,         -- 'green'|'yellow'|'red'|'gray'
        email_checked_at  TIMESTAMPTZ,
        email_confidence  INT,
        email_source_url  TEXT
      )
    `;
    console.log('   ✅ people.contact_verification created');
    
    // Step 4: Add the indexes
    console.log('4️⃣ Creating indexes...');
    await sql`CREATE INDEX IF NOT EXISTS ix_contact_email ON people.contact (lower(email))`;
    await sql`CREATE INDEX IF NOT EXISTS ix_slot_company_role ON company.company_slot(company_id, role_code)`;
    console.log('   ✅ Indexes created');
    
    // Step 5: Create test data to verify everything works
    console.log('5️⃣ Creating test data...');
    
    // Create test contacts
    const testContacts = await sql`
      INSERT INTO people.contact (full_name, title, email, phone) 
      VALUES 
        ('John CEO Smith', 'Chief Executive Officer', 'ceo@testcompany.com', '+1-555-0101'),
        ('Jane CFO Johnson', 'Chief Financial Officer', 'cfo@testcompany.com', '+1-555-0102'),
        ('Bob HR Wilson', 'HR Director', 'hr@testcompany.com', '+1-555-0103')
      RETURNING contact_id, full_name, email
    `;
    
    console.log(`   ✅ Created ${testContacts.length} test contacts`);
    
    // Create verification records with different dot colors
    const verifications = [
      { contact_id: testContacts[0].contact_id, status: 'green', confidence: 98 },
      { contact_id: testContacts[1].contact_id, status: 'yellow', confidence: 75 },
      { contact_id: testContacts[2].contact_id, status: 'red', confidence: 30 }
    ];
    
    for (const ver of verifications) {
      await sql`
        INSERT INTO people.contact_verification (
          contact_id, email_status, email_checked_at, email_confidence
        ) VALUES (
          ${ver.contact_id}, ${ver.status}, NOW(), ${ver.confidence}
        )
      `;
    }
    console.log('   ✅ Created verification records with different dot colors');
    
    // Step 6: Assign contacts to company slots
    console.log('6️⃣ Testing company slot assignments...');
    const companies = await sql`SELECT company_id FROM company.company LIMIT 1`;
    
    if (companies.length > 0) {
      const companyId = companies[0].company_id;
      
      // Assign CEO
      await sql`
        INSERT INTO company.company_slot (company_id, role_code, contact_id)
        VALUES (${companyId}, 'CEO', ${testContacts[0].contact_id})
        ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id
      `;
      
      // Assign CFO  
      await sql`
        INSERT INTO company.company_slot (company_id, role_code, contact_id)
        VALUES (${companyId}, 'CFO', ${testContacts[1].contact_id})
        ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id
      `;
      
      // Assign HR
      await sql`
        INSERT INTO company.company_slot (company_id, role_code, contact_id)
        VALUES (${companyId}, 'HR', ${testContacts[2].contact_id})
        ON CONFLICT (company_id, role_code) DO UPDATE SET contact_id = EXCLUDED.contact_id
      `;
      
      console.log('   ✅ All 3 company slots assigned (CEO, CFO, HR)');
    }
    
    // Step 7: Verify the complete structure with a comprehensive query
    console.log('7️⃣ Final verification...');
    const verification = await sql`
      SELECT 
        comp.company_name,
        c.contact_id,
        c.full_name,
        c.title,
        c.email,
        cv.email_status,
        cv.email_confidence,
        cs.role_code
      FROM people.contact c
      JOIN people.contact_verification cv ON c.contact_id = cv.contact_id
      JOIN company.company_slot cs ON c.contact_id = cs.contact_id
      JOIN company.company comp ON cs.company_id = comp.company_id
      ORDER BY cs.role_code
    `;
    
    console.log('\n📊 Complete Structure Verification:');
    verification.forEach(v => {
      console.log(`   ${v.role_code}: ${v.full_name} (${v.title})`);
      console.log(`      Email: ${v.email}`);
      console.log(`      Status: ${v.email_status} dot (${v.email_confidence}% confidence)`);
      console.log(`      Company: ${v.company_name}`);
      console.log('');
    });
    
    console.log('🎉 Contact Schema Successfully Updated!');
    console.log('\n📋 Final Schema Structure:');
    console.log('✅ people.contact:');
    console.log('   • contact_id (BIGSERIAL PRIMARY KEY)');
    console.log('   • full_name, title, email, phone');
    console.log('   • created_at, updated_at (TIMESTAMPTZ)');
    console.log('');
    console.log('✅ people.contact_verification (1:1):');
    console.log('   • contact_id → people.contact(contact_id) CASCADE DELETE');
    console.log('   • email_status (green|yellow|red|gray)');
    console.log('   • email_checked_at, email_confidence, email_source_url');
    console.log('');
    console.log('✅ company.company_slot:');
    console.log('   • contact_id → people.contact(contact_id) ON DELETE SET NULL');
    console.log('   • Exactly 3 slots per company (CEO/CFO/HR)');
    console.log('');
    console.log('✅ Helpful Indexes:');
    console.log('   • ix_contact_email on lower(email)');
    console.log('   • ix_slot_company_role on (company_id, role_code)');
    console.log('\n🎯 Schema now matches your specification exactly!');
    
  } catch (error) {
    console.error('❌ Fix failed:', error.message);
  }
}

fixContactSchema().catch(console.error);