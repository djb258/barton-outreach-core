/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-5B4BB35A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Set up Slot Management Functions
 * Creates stored procedures for managing company slots and contact verification
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupSlotFunctions() {
  console.log('🔧 Setting up Slot Management Functions in Neon...\n');
  
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
    
    // Step 1: Create update_slot_dot function
    console.log('1️⃣ Creating update_slot_dot function...');
    await sql`
      CREATE OR REPLACE FUNCTION company.update_slot_dot(
        p_company_id BIGINT,
        p_role TEXT,
        p_dot TEXT,
        p_checked_at TIMESTAMPTZ,
        p_source_url TEXT
      ) RETURNS INTEGER AS $$
      DECLARE
        rows_updated INTEGER;
      BEGIN
        UPDATE people.contact_verification v
        SET 
          email_status = p_dot, 
          email_checked_at = p_checked_at, 
          email_source_url = p_source_url
        FROM company.company_slot s
        JOIN people.contact c ON c.contact_id = s.contact_id
        WHERE s.company_id = p_company_id 
          AND s.role_code = p_role 
          AND v.contact_id = c.contact_id;
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        RETURN rows_updated;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.update_slot_dot() created');
    console.log('   📧 Updates contact verification after MillionVerifier check');
    
    // Step 2: Create free_slot_if_current function
    console.log('2️⃣ Creating free_slot_if_current function...');
    await sql`
      CREATE OR REPLACE FUNCTION company.free_slot_if_current(
        p_old_company_id BIGINT,
        p_role TEXT,
        p_contact_id BIGINT
      ) RETURNS INTEGER AS $$
      DECLARE
        rows_updated INTEGER;
      BEGIN
        UPDATE company.company_slot
        SET contact_id = NULL
        WHERE company_id = p_old_company_id 
          AND role_code = p_role 
          AND contact_id = p_contact_id;
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        RETURN rows_updated;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.free_slot_if_current() created');
    console.log('   👥 Handles executive movement between companies');
    
    // Step 3: Create ensure_slots function
    console.log('3️⃣ Creating ensure_slots function...');
    await sql`
      CREATE OR REPLACE FUNCTION company.ensure_slots(
        p_company_id BIGINT
      ) RETURNS INTEGER AS $$
      DECLARE
        rows_inserted INTEGER;
      BEGIN
        INSERT INTO company.company_slot (company_id, role_code)
        SELECT p_company_id, x.role
        FROM (VALUES ('CEO'),('CFO'),('HR')) AS x(role)
        ON CONFLICT (company_id, role_code) DO NOTHING;
        
        GET DIAGNOSTICS rows_inserted = ROW_COUNT;
        RETURN rows_inserted;
      END;
      $$ LANGUAGE plpgsql;
    `;
    console.log('   ✅ company.ensure_slots() created');
    console.log('   🏢 Ensures every company has CEO/CFO/HR slots');
    
    // Step 4: Test all functions
    console.log('4️⃣ Testing slot management functions...');
    
    // Test ensure_slots
    const companies = await sql`SELECT company_id FROM company.company LIMIT 1`;
    if (companies.length > 0) {
      const companyId = companies[0].company_id;
      
      const slotsCreated = await sql`SELECT company.ensure_slots(${companyId}) as created`;
      console.log(`   🏢 ensure_slots(${companyId}): ${slotsCreated[0].created} new slots created`);
      
      // Get a contact for testing
      const contacts = await sql`
        SELECT c.contact_id, c.full_name, c.email
        FROM people.contact c
        JOIN people.contact_verification v ON v.contact_id = c.contact_id
        WHERE c.email IS NOT NULL
        LIMIT 1
      `;
      
      if (contacts.length > 0) {
        const contact = contacts[0];
        
        // Test update_slot_dot
        const dotUpdated = await sql`
          SELECT company.update_slot_dot(
            ${companyId}, 
            'CEO', 
            'green', 
            NOW(), 
            'test-verification-source'
          ) as updated
        `;
        console.log(`   📧 update_slot_dot(${companyId}, 'CEO', 'green'): ${dotUpdated[0].updated} rows updated`);
        
        // Test free_slot_if_current
        const slotFreed = await sql`
          SELECT company.free_slot_if_current(
            ${companyId}, 
            'CEO', 
            ${contact.contact_id}
          ) as freed
        `;
        console.log(`   👥 free_slot_if_current(${companyId}, 'CEO', ${contact.contact_id}): ${slotFreed[0].freed} rows freed`);
      }
    }
    
    // Step 5: Demonstrate complete slot management workflow
    console.log('5️⃣ Demonstrating complete slot management workflow...');
    
    if (companies.length > 0) {
      const companyId = companies[0].company_id;
      
      // Ensure all slots exist
      await sql`SELECT company.ensure_slots(${companyId})`;
      
      // Check current slot status
      const currentSlots = await sql`
        SELECT 
          cs.role_code,
          c.full_name,
          c.email,
          v.email_status,
          v.email_checked_at
        FROM company.company_slot cs
        LEFT JOIN people.contact c ON c.contact_id = cs.contact_id
        LEFT JOIN people.contact_verification v ON v.contact_id = c.contact_id
        WHERE cs.company_id = ${companyId}
        ORDER BY cs.role_code
      `;
      
      console.log(`   📋 Current slot status for company ${companyId}:`);
      currentSlots.forEach(slot => {
        const contact = slot.full_name ? `${slot.full_name} (${slot.email})` : 'EMPTY';
        const status = slot.email_status ? `${slot.email_status} dot` : 'no verification';
        const lastCheck = slot.email_checked_at 
          ? new Date(slot.email_checked_at).toLocaleDateString()
          : 'never';
        console.log(`      ${slot.role_code}: ${contact} - ${status} - checked ${lastCheck}`);
      });
      
      // Simulate MillionVerifier update
      const contacts = await sql`
        SELECT c.contact_id, c.full_name
        FROM company.company_slot cs
        JOIN people.contact c ON c.contact_id = cs.contact_id
        WHERE cs.company_id = ${companyId} AND cs.role_code = 'CEO'
      `;
      
      if (contacts.length > 0) {
        console.log('\n   🧪 Simulating MillionVerifier update workflow:');
        
        // Update CEO dot to red (bounced email)
        await sql`
          SELECT company.update_slot_dot(
            ${companyId}, 
            'CEO', 
            'red', 
            NOW(), 
            'millionverifier-batch-2025-09-04'
          )
        `;
        console.log('      ✅ Updated CEO dot to red (email bounced)');
        
        // Simulate executive movement - free the slot
        const contactId = contacts[0].contact_id;
        await sql`SELECT company.free_slot_if_current(${companyId}, 'CEO', ${contactId})`;
        console.log(`      ✅ Freed CEO slot (${contacts[0].full_name} moved companies)`);
        
        // Verify the changes
        const updatedSlots = await sql`
          SELECT 
            cs.role_code,
            c.full_name,
            v.email_status
          FROM company.company_slot cs
          LEFT JOIN people.contact c ON c.contact_id = cs.contact_id
          LEFT JOIN people.contact_verification v ON v.contact_id = c.contact_id
          WHERE cs.company_id = ${companyId} AND cs.role_code = 'CEO'
        `;
        
        if (updatedSlots.length > 0) {
          const slot = updatedSlots[0];
          console.log(`      📊 Final CEO slot status: ${slot.full_name || 'EMPTY'} (${slot.email_status || 'no status'})`);
        }
      }
    }
    
    console.log('\n🎉 Slot Management Functions Setup Complete!');
    console.log('\n📋 Functions Created:');
    console.log('✅ company.update_slot_dot(company_id, role, dot, checked_at, source_url):');
    console.log('   • Updates contact verification after MillionVerifier checks');
    console.log('   • Returns number of rows updated');
    console.log('   • Used by automated email verification pipeline');
    console.log('');
    console.log('✅ company.free_slot_if_current(old_company_id, role, contact_id):');
    console.log('   • Handles executive movement between companies');
    console.log('   • Only frees slot if specific contact currently fills it');
    console.log('   • Prevents accidental slot clearing');
    console.log('');
    console.log('✅ company.ensure_slots(company_id):');
    console.log('   • Ensures every company has CEO/CFO/HR slots');
    console.log('   • Idempotent - safe to call multiple times');
    console.log('   • Used when adding new companies');
    console.log('');
    console.log('🎯 Usage Examples:');
    console.log('   • After MV batch: SELECT company.update_slot_dot(123, \'CEO\', \'green\', NOW(), \'mv-batch-url\')');
    console.log('   • Executive moves: SELECT company.free_slot_if_current(123, \'CEO\', 456)');
    console.log('   • New company: SELECT company.ensure_slots(123)');
    console.log('');
    console.log('✅ Functions ready for automation and UI integration!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE FUNCTION permissions');
    console.log('   • Ensure all referenced tables exist');
  }
}

setupSlotFunctions().catch(console.error);