#!/usr/bin/env node
/**
 * Schema Status Verification
 * Comprehensive check of database schema deployment status
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Client } = pg;

async function verifySchemaStatus() {
  console.log('🔍 Starting Barton Outreach Core Schema Verification...');
  
  const client = new Client({
    connectionString: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });

  try {
    console.log('🔌 Connecting to database...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // 1. Check Schemas
    console.log('📁 Schema Verification:');
    const expectedSchemas = ['company', 'people', 'marketing', 'bit', 'ple'];
    const schemaResult = await client.query(`
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name = ANY($1)
      ORDER BY schema_name
    `, [expectedSchemas]);

    const existingSchemas = schemaResult.rows.map(row => row.schema_name);
    expectedSchemas.forEach(schema => {
      if (existingSchemas.includes(schema)) {
        console.log(`   ✅ ${schema} schema exists`);
      } else {
        console.log(`   ❌ ${schema} schema missing`);
      }
    });

    // 2. Check ENUM Types
    console.log('\n📝 ENUM Type Verification:');
    const enumTypes = [
      { schema: 'company', type: 'role_code_t', expected: ['CEO', 'CFO', 'HR'] },
      { schema: 'people', type: 'email_status_t', expected: ['green', 'yellow', 'red', 'gray'] }
    ];

    for (const enumDef of enumTypes) {
      try {
        const enumResult = await client.query(`
          SELECT e.enumlabel as value
          FROM pg_type t 
          JOIN pg_enum e ON t.oid = e.enumtypid  
          JOIN pg_namespace n ON n.oid = t.typnamespace
          WHERE n.nspname = $1 AND t.typname = $2
          ORDER BY e.enumsortorder
        `, [enumDef.schema, enumDef.type]);

        const actualValues = enumResult.rows.map(row => row.value);
        const isCorrect = JSON.stringify(actualValues) === JSON.stringify(enumDef.expected);
        
        if (isCorrect) {
          console.log(`   ✅ ${enumDef.schema}.${enumDef.type} (${actualValues.join(', ')})`);
        } else {
          console.log(`   ⚠️ ${enumDef.schema}.${enumDef.type} - Expected: ${enumDef.expected.join(', ')}, Actual: ${actualValues.join(', ')}`);
        }
      } catch (error) {
        console.log(`   ❌ ${enumDef.schema}.${enumDef.type} - Not found`);
      }
    }

    // 3. Check Core Tables
    console.log('\n📊 Core Table Verification:');
    const coreStables = [
      'company.company',
      'company.company_slot',
      'people.contact',
      'people.contact_verification',
      'marketing.campaign',
      'marketing.campaign_contact',
      'marketing.message_log',
      'marketing.booking_event',
      'marketing.ac_handoff',
      'bit.signal'
    ];

    for (const table of coreStables) {
      try {
        const countResult = await client.query(`SELECT COUNT(*) as count FROM ${table}`);
        console.log(`   ✅ ${table} (${countResult.rows[0].count} records)`);
      } catch (error) {
        console.log(`   ❌ ${table} - ${error.message}`);
      }
    }

    // 4. Check Views
    console.log('\n🔍 View Verification:');
    const expectedViews = [
      'company.vw_company_slots',
      'company.vw_next_renewal',
      'company.vw_due_renewals_ready',
      'company.next_company_urls_30d',
      'people.next_profile_urls_30d',
      'people.due_email_recheck_30d',
      'marketing.marketing_ceo',
      'marketing.marketing_cfo',
      'marketing.marketing_hr'
    ];

    for (const view of expectedViews) {
      try {
        const countResult = await client.query(`SELECT COUNT(*) as count FROM ${view} LIMIT 1`);
        console.log(`   ✅ ${view} (${countResult.rows[0].count} items)`);
      } catch (error) {
        console.log(`   ❌ ${view} - ${error.message}`);
      }
    }

    // 5. Check Functions
    console.log('\n⚙️ Function Verification:');
    const expectedFunctions = [
      'public.set_updated_at',
      'company.ensure_company_slots'
    ];

    for (const func of expectedFunctions) {
      try {
        const funcResult = await client.query(`
          SELECT p.proname, n.nspname
          FROM pg_proc p
          JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE n.nspname = $1 AND p.proname = $2
        `, func.split('.'));

        if (funcResult.rows.length > 0) {
          console.log(`   ✅ ${func} function exists`);
        } else {
          console.log(`   ❌ ${func} function missing`);
        }
      } catch (error) {
        console.log(`   ❌ ${func} - Error checking: ${error.message}`);
      }
    }

    // 6. Check Triggers
    console.log('\n🔄 Trigger Verification:');
    const expectedTriggers = [
      { table: 'company.company', trigger: 'trg_company_updated_at' },
      { table: 'company.company_slot', trigger: 'trg_company_slot_updated_at' },
      { table: 'people.contact', trigger: 'trg_people_contact_updated_at' },
      { table: 'company.company', trigger: 'trg_company_after_insert_slots' },
      { table: 'marketing.campaign', trigger: 'trg_marketing_campaign_updated_at' }
    ];

    for (const triggerDef of expectedTriggers) {
      try {
        const triggerResult = await client.query(`
          SELECT trigger_name
          FROM information_schema.triggers
          WHERE event_object_schema = $1 
          AND event_object_table = $2 
          AND trigger_name = $3
        `, [
          triggerDef.table.split('.')[0],
          triggerDef.table.split('.')[1],
          triggerDef.trigger
        ]);

        if (triggerResult.rows.length > 0) {
          console.log(`   ✅ ${triggerDef.trigger} on ${triggerDef.table}`);
        } else {
          console.log(`   ❌ ${triggerDef.trigger} on ${triggerDef.table} - Missing`);
        }
      } catch (error) {
        console.log(`   ❌ ${triggerDef.trigger} on ${triggerDef.table} - Error: ${error.message}`);
      }
    }

    // 7. Check Indexes
    console.log('\n📊 Index Verification:');
    const keyIndexes = [
      'idx_company_name',
      'idx_company_renewal_month',
      'idx_contact_email',
      'idx_contact_verif_status',
      'idx_company_slot_company',
      'idx_bit_signal_company'
    ];

    for (const indexName of keyIndexes) {
      try {
        const indexResult = await client.query(`
          SELECT indexname, tablename, schemaname
          FROM pg_indexes
          WHERE indexname = $1
        `, [indexName]);

        if (indexResult.rows.length > 0) {
          const idx = indexResult.rows[0];
          console.log(`   ✅ ${indexName} on ${idx.schemaname}.${idx.tablename}`);
        } else {
          console.log(`   ❌ ${indexName} - Missing`);
        }
      } catch (error) {
        console.log(`   ❌ ${indexName} - Error: ${error.message}`);
      }
    }

    // 8. Test Slot Management
    console.log('\n🎯 Slot Management Test:');
    try {
      const slotDistribution = await client.query(`
        SELECT 
          COUNT(DISTINCT c.company_id) as total_companies,
          COUNT(cs.company_slot_id) as total_slots,
          COUNT(cs.contact_id) as filled_slots,
          COUNT(CASE WHEN cs.role_code = 'CEO' THEN 1 END) as ceo_slots,
          COUNT(CASE WHEN cs.role_code = 'CFO' THEN 1 END) as cfo_slots,
          COUNT(CASE WHEN cs.role_code = 'HR' THEN 1 END) as hr_slots
        FROM company.company c
        LEFT JOIN company.company_slot cs ON cs.company_id = c.company_id
      `);

      const stats = slotDistribution.rows[0];
      console.log(`   📊 Companies: ${stats.total_companies}`);
      console.log(`   📊 Total slots: ${stats.total_slots} (${stats.filled_slots} filled)`);
      console.log(`   📊 CEO slots: ${stats.ceo_slots}`);
      console.log(`   📊 CFO slots: ${stats.cfo_slots}`);
      console.log(`   📊 HR slots: ${stats.hr_slots}`);

      // Check if every company has exactly 3 slots
      const incompleteCompanies = await client.query(`
        SELECT c.company_name, COUNT(cs.role_code) as slot_count
        FROM company.company c
        LEFT JOIN company.company_slot cs ON cs.company_id = c.company_id
        GROUP BY c.company_id, c.company_name
        HAVING COUNT(cs.role_code) != 3
        LIMIT 5
      `);

      if (incompleteCompanies.rows.length === 0) {
        console.log(`   ✅ All companies have exactly 3 slots (CEO, CFO, HR)`);
      } else {
        console.log(`   ⚠️ Found ${incompleteCompanies.rows.length} companies with incomplete slots:`);
        incompleteCompanies.rows.forEach(row => {
          console.log(`      • ${row.company_name}: ${row.slot_count} slots`);
        });
      }
    } catch (error) {
      console.log(`   ❌ Slot management test failed: ${error.message}`);
    }

    // 9. Test Queue Functionality
    console.log('\n🔄 Queue Functionality Test:');
    const queueViews = [
      'company.next_company_urls_30d',
      'people.next_profile_urls_30d',
      'people.due_email_recheck_30d',
      'company.vw_due_renewals_ready'
    ];

    for (const queue of queueViews) {
      try {
        const queueSize = await client.query(`SELECT COUNT(*) as size FROM ${queue}`);
        console.log(`   📋 ${queue}: ${queueSize.rows[0].size} items in queue`);
      } catch (error) {
        console.log(`   ❌ ${queue}: Error - ${error.message}`);
      }
    }

    console.log('\n✨ Schema verification completed!');

    // Summary assessment
    const schemaScore = existingSchemas.length / expectedSchemas.length * 100;
    console.log('\n📋 Summary Assessment:');
    console.log(`   🎯 Schema Completeness: ${schemaScore.toFixed(1)}%`);
    
    if (schemaScore === 100) {
      console.log('   🎉 Schema is fully deployed and ready for production!');
    } else if (schemaScore >= 80) {
      console.log('   ⚠️ Schema is mostly deployed but may need some adjustments');
    } else {
      console.log('   ❌ Schema deployment appears incomplete - consider running setup script');
    }

  } catch (error) {
    console.error('❌ Schema verification failed:', error.message);
    throw error;
  } finally {
    await client.end();
    console.log('\n🔌 Database connection closed');
  }
}

// Run verification
if (import.meta.url === `file://${process.argv[1]}`) {
  if (!process.env.NEON_DATABASE_URL && !process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL or NEON_DATABASE_URL environment variable is required');
    process.exit(1);
  }

  verifySchemaStatus()
    .then(() => {
      console.log('\n✅ Verification completed successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Verification failed:', error.message);
      process.exit(1);
    });
}

export { verifySchemaStatus };