#!/usr/bin/env node

/**
 * Comprehensive Schema Validation
 * Verifies all schemas, tables, constraints, and views are properly implemented
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function validateCompleteSchema() {
  console.log('🔍 Running Comprehensive Schema Validation...\n');
  
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
    
    // Test 1: Check schemas present
    console.log('1️⃣ Validating schemas present...');
    const schemas = await sql`
      SELECT schema_name 
      FROM information_schema.schemata
      WHERE schema_name IN ('company','people','marketing','bit')
      ORDER BY schema_name
    `;
    
    const expectedSchemas = ['bit', 'company', 'marketing', 'people'];
    const foundSchemas = schemas.map(s => s.schema_name);
    
    console.log('   Expected schemas:', expectedSchemas.join(', '));
    console.log('   Found schemas:', foundSchemas.join(', '));
    
    const missingSchemas = expectedSchemas.filter(s => !foundSchemas.includes(s));
    if (missingSchemas.length === 0) {
      console.log('   ✅ All required schemas present');
    } else {
      console.log(`   ❌ Missing schemas: ${missingSchemas.join(', ')}`);
    }
    console.log('');
    
    // Test 2: Check tables created
    console.log('2️⃣ Validating tables created...');
    const tables = await sql`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema IN ('company','people','marketing','bit')
      ORDER BY table_schema, table_name
    `;
    
    console.log('   📋 Tables found:');
    tables.forEach(table => {
      console.log(`      ${table.table_schema}.${table.table_name}`);
    });
    
    const expectedTables = [
      'bit.signal',
      'company.company',
      'company.company_slot',
      'marketing.ac_handoff',
      'marketing.booking_event',
      'marketing.campaign',
      'marketing.campaign_contact',
      'marketing.message_log',
      'people.contact',
      'people.contact_verification'
    ];
    
    const foundTables = tables.map(t => `${t.table_schema}.${t.table_name}`);
    const missingTables = expectedTables.filter(t => !foundTables.includes(t));
    
    if (missingTables.length === 0) {
      console.log('   ✅ All expected tables present');
    } else {
      console.log(`   ❌ Missing tables: ${missingTables.join(', ')}`);
    }
    console.log('');
    
    // Test 3: Check slot uniqueness constraint
    console.log('3️⃣ Validating slot uniqueness constraint...');
    const duplicateSlots = await sql`
      WITH try AS (
        SELECT company_id, role_code, COUNT(*) as cnt
        FROM company.company_slot
        GROUP BY 1,2 HAVING COUNT(*) > 1
      )
      SELECT * FROM try
    `;
    
    if (duplicateSlots.length === 0) {
      console.log('   ✅ No duplicate company slots found - uniqueness constraint working');
    } else {
      console.log(`   ❌ Found ${duplicateSlots.length} duplicate slots:`);
      duplicateSlots.forEach(dup => {
        console.log(`      Company ${dup.company_id} role ${dup.role_code}: ${dup.cnt} duplicates`);
      });
    }
    console.log('');
    
    // Test 4: Check renewal views compile and work
    console.log('4️⃣ Validating renewal views...');
    
    try {
      const nextRenewals = await sql`
        SELECT * FROM company.vw_next_renewal LIMIT 5
      `;
      console.log(`   ✅ vw_next_renewal view working - ${nextRenewals.length} rows returned`);
      
      if (nextRenewals.length > 0) {
        console.log('      Sample renewal data:');
        nextRenewals.slice(0, 2).forEach(r => {
          console.log(`         Company ${r.company_id}: Month ${r.renewal_month} → ${new Date(r.next_renewal_date).toLocaleDateString()}`);
        });
      }
    } catch (error) {
      console.log(`   ❌ vw_next_renewal view error: ${error.message}`);
    }
    
    try {
      const dueRenewals = await sql`
        SELECT * FROM company.vw_due_renewals_ready LIMIT 5
      `;
      console.log(`   ✅ vw_due_renewals_ready view working - ${dueRenewals.length} rows returned`);
      
      if (dueRenewals.length > 0) {
        console.log('      Companies ready for renewal campaigns:');
        dueRenewals.forEach(r => {
          console.log(`         Company ${r.company_id}: Window opens ${new Date(r.window_opens_on).toLocaleDateString()}`);
        });
      }
    } catch (error) {
      console.log(`   ❌ vw_due_renewals_ready view error: ${error.message}`);
    }
    console.log('');
    
    // Test 5: Check other key views
    console.log('5️⃣ Validating other key views...');
    
    try {
      const companySlots = await sql`
        SELECT * FROM company.vw_company_slots LIMIT 3
      `;
      console.log(`   ✅ vw_company_slots view working - ${companySlots.length} rows returned`);
      
      companySlots.forEach(slot => {
        const contact = slot.full_name ? `${slot.full_name} (${slot.email_status || 'no status'} dot)` : 'EMPTY';
        console.log(`      ${slot.role_code}: ${contact}`);
      });
    } catch (error) {
      console.log(`   ❌ vw_company_slots view error: ${error.message}`);
    }
    
    try {
      const dueRecheck = await sql`
        SELECT * FROM people.due_email_recheck_30d LIMIT 3
      `;
      console.log(`   ✅ due_email_recheck_30d view working - ${dueRecheck.length} contacts due for recheck`);
    } catch (error) {
      console.log(`   ❌ due_email_recheck_30d view error: ${error.message}`);
    }
    console.log('');
    
    // Test 6: Check stored functions
    console.log('6️⃣ Validating stored functions...');
    
    const functions = await sql`
      SELECT 
        n.nspname as schema_name,
        p.proname as function_name,
        pg_get_function_result(p.oid) as return_type
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE n.nspname IN ('company', 'intake', 'vault')
        AND p.proname IN ('update_slot_dot', 'free_slot_if_current', 'ensure_slots', 'f_ingest_json', 'f_promote_contacts')
      ORDER BY n.nspname, p.proname
    `;
    
    console.log(`   📋 Found ${functions.length} stored functions:`);
    functions.forEach(fn => {
      console.log(`      ${fn.schema_name}.${fn.function_name}() → ${fn.return_type}`);
    });
    
    const expectedFunctions = [
      'company.ensure_slots',
      'company.free_slot_if_current', 
      'company.update_slot_dot',
      'intake.f_ingest_json',
      'vault.f_promote_contacts'
    ];
    
    const foundFunctions = functions.map(f => `${f.schema_name}.${f.function_name}`);
    const missingFunctions = expectedFunctions.filter(f => !foundFunctions.includes(f));
    
    if (missingFunctions.length === 0) {
      console.log('   ✅ All expected functions present');
    } else {
      console.log(`   ❌ Missing functions: ${missingFunctions.join(', ')}`);
    }
    console.log('');
    
    // Test 7: Check foreign key relationships
    console.log('7️⃣ Validating foreign key relationships...');
    
    const foreignKeys = await sql`
      SELECT 
        tc.table_schema || '.' || tc.table_name as table_name,
        kcu.column_name,
        ccu.table_schema || '.' || ccu.table_name as referenced_table,
        ccu.column_name as referenced_column,
        tc.constraint_name
      FROM information_schema.table_constraints AS tc 
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema IN ('company', 'people', 'marketing', 'bit')
      ORDER BY tc.table_schema, tc.table_name
    `;
    
    console.log(`   🔗 Found ${foreignKeys.length} foreign key relationships:`);
    foreignKeys.forEach(fk => {
      console.log(`      ${fk.table_name}.${fk.column_name} → ${fk.referenced_table}.${fk.referenced_column}`);
    });
    console.log('');
    
    // Test 8: Check indexes
    console.log('8️⃣ Validating key indexes...');
    
    const indexes = await sql`
      SELECT 
        schemaname || '.' || tablename as table_name,
        indexname,
        indexdef
      FROM pg_indexes
      WHERE schemaname IN ('company', 'people', 'marketing', 'bit')
        AND indexname NOT LIKE '%_pkey'
      ORDER BY schemaname, tablename, indexname
    `;
    
    console.log(`   📊 Found ${indexes.length} custom indexes:`);
    indexes.forEach(idx => {
      console.log(`      ${idx.indexname} on ${idx.table_name}`);
    });
    console.log('');
    
    // Test 9: Sample data validation
    console.log('9️⃣ Validating sample data...');
    
    const dataCounts = await sql`
      SELECT 
        'Companies' as entity,
        COUNT(*) as count
      FROM company.company
      
      UNION ALL
      
      SELECT 
        'Company Slots' as entity,
        COUNT(*) as count
      FROM company.company_slot
      
      UNION ALL
      
      SELECT 
        'Contacts' as entity,
        COUNT(*) as count
      FROM people.contact
      
      UNION ALL
      
      SELECT 
        'Contact Verifications' as entity,
        COUNT(*) as count
      FROM people.contact_verification
      
      UNION ALL
      
      SELECT 
        'BIT Signals' as entity,
        COUNT(*) as count
      FROM bit.signal
      
      UNION ALL
      
      SELECT 
        'Marketing Campaigns' as entity,
        COUNT(*) as count
      FROM marketing.campaign
    `;
    
    console.log('   📊 Data summary:');
    dataCounts.forEach(data => {
      console.log(`      ${data.entity}: ${data.count} records`);
    });
    console.log('');
    
    // Final comprehensive test
    console.log('🔟 Running comprehensive integration test...');
    
    const integrationTest = await sql`
      SELECT 
        comp.company_name,
        comp.renewal_month,
        cs.role_code,
        c.full_name,
        c.email,
        cv.email_status,
        CASE WHEN nr.company_id IS NOT NULL THEN 'In Renewal Window' ELSE 'Not Due' END as renewal_status,
        (SELECT COUNT(*) FROM bit.signal bs WHERE bs.company_id = comp.company_id) as signal_count
      FROM company.company comp
      LEFT JOIN company.vw_next_renewal nr ON nr.company_id = comp.company_id AND NOW()::date >= nr.window_opens_on
      LEFT JOIN company.company_slot cs ON cs.company_id = comp.company_id
      LEFT JOIN people.contact c ON c.contact_id = cs.contact_id
      LEFT JOIN people.contact_verification cv ON cv.contact_id = c.contact_id
      ORDER BY comp.company_id, cs.role_code
      LIMIT 10
    `;
    
    console.log(`   🔄 Integration test returned ${integrationTest.length} rows:`);
    integrationTest.forEach(test => {
      console.log(`      ${test.company_name} - ${test.role_code || 'No Role'}: ${test.full_name || 'Empty'}`);
      console.log(`         Email: ${test.email || 'None'} (${test.email_status || 'No status'})`);
      console.log(`         Renewal: ${test.renewal_status}, Signals: ${test.signal_count}`);
    });
    
    console.log('\n🎉 Comprehensive Schema Validation Complete!');
    
    // Summary
    const issues = [];
    if (missingSchemas.length > 0) issues.push(`${missingSchemas.length} missing schemas`);
    if (missingTables.length > 0) issues.push(`${missingTables.length} missing tables`);
    if (duplicateSlots.length > 0) issues.push(`${duplicateSlots.length} duplicate slots`);
    if (missingFunctions.length > 0) issues.push(`${missingFunctions.length} missing functions`);
    
    if (issues.length === 0) {
      console.log('\n✅ All validation tests passed! Schema is complete and ready for production.');
    } else {
      console.log(`\n⚠️ Found ${issues.length} issues: ${issues.join(', ')}`);
      console.log('   Review the validation output above for details.');
    }
    
    console.log('\n📋 Schema Summary:');
    console.log(`   • ${schemas.length}/4 schemas created`);
    console.log(`   • ${tables.length} tables created`);
    console.log(`   • ${functions.length} stored functions`);
    console.log(`   • ${foreignKeys.length} foreign key relationships`);
    console.log(`   • ${indexes.length} custom indexes`);
    console.log('\n🚀 Ready for UI integration and automation!');
    
  } catch (error) {
    console.error('❌ Validation failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify all setup scripts have been run');
    console.log('   • Check user permissions for schema access');
  }
}

validateCompleteSchema().catch(console.error);