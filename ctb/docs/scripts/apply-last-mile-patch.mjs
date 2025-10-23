/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-968062AF
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node
import pg from 'pg';
import fs from 'fs';
import dotenv from 'dotenv';

dotenv.config();
const { Client } = pg;

async function applyLastMilePatch() {
  const client = new Client({
    connectionString: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    console.log('🔧 Applying last-mile patch...');
    await client.connect();
    
    const sql = fs.readFileSync('scripts/last-mile-patch.sql', 'utf8');
    await client.query(sql);
    
    console.log('✅ Last-mile patch applied successfully!');
    
    // Run sanity checks
    console.log('\n📊 Sanity checks:');
    
    const checks = [
      { name: 'ple schema', query: "SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='ple') AS ok" },
      { name: 'trigger slots', query: "SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_after_insert_slots') AS ok" },
      { name: 'trg company', query: "SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_updated_at') AS ok" },
      { name: 'trg slot', query: "SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_slot_updated_at') AS ok" },
      { name: 'trg contact', query: "SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_people_contact_updated_at') AS ok" },
      { name: 'idx verif', query: "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_verif_status_checked') AS ok" },
      { name: 'idx renewal', query: "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_company_renewal_month') AS ok" },
      { name: 'idx brin', query: "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='brin_message_log_created_at') AS ok" }
    ];
    
    for (const check of checks) {
      try {
        const result = await client.query(check.query);
        const status = result.rows[0].ok ? '✅' : '❌';
        console.log(`   ${status} ${check.name}: ${result.rows[0].ok}`);
      } catch (error) {
        console.log(`   ❌ ${check.name}: Error - ${error.message}`);
      }
    }
    
    // Test auto-slot creation
    console.log('\n🧪 Testing auto-slot creation:');
    try {
      const testResult = await client.query(`
        INSERT INTO company.company (company_name) 
        VALUES ('Test Auto-Slots Company') 
        RETURNING company_id
      `);
      
      const testCompanyId = testResult.rows[0].company_id;
      console.log(`   📝 Created test company ID: ${testCompanyId}`);
      
      const slotCheck = await client.query(`
        SELECT role_code, contact_id 
        FROM company.company_slot 
        WHERE company_id = $1 
        ORDER BY role_code
      `, [testCompanyId]);
      
      console.log('   📊 Auto-created slots:');
      slotCheck.rows.forEach(row => {
        console.log(`      • ${row.role_code}: ${row.contact_id || 'unassigned'}`);
      });
      
      if (slotCheck.rows.length === 3) {
        console.log('   ✅ Auto-slot creation working perfectly!');
      } else {
        console.log(`   ⚠️ Expected 3 slots, got ${slotCheck.rows.length}`);
      }
      
      // Clean up test data
      await client.query('DELETE FROM company.company WHERE company_id = $1', [testCompanyId]);
      console.log('   🧹 Test data cleaned up');
      
    } catch (error) {
      console.log(`   ❌ Auto-slot test failed: ${error.message}`);
    }
    
  } catch (error) {
    console.error('❌ Error applying patch:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

applyLastMilePatch().catch(console.error);