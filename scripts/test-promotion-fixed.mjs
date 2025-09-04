#!/usr/bin/env node

/**
 * Test Promotion with Fixed Email Constraint
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testPromotionFixed() {
  console.log('🔧 Testing Promotion with Fixed Constraint\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    const sql = neon(connectionString);
    
    console.log('1️⃣ Cleaning up test data...');
    await sql`DELETE FROM intake.raw_loads WHERE source = 'fixed.test'`;
    await sql`DELETE FROM people.marketing_people WHERE source = 'fixed.test'`;
    await sql`DELETE FROM company.marketing_company WHERE source = 'fixed.test'`;
    console.log('   ✅ Test data cleaned');
    
    console.log('2️⃣ Ingesting test data...');
    const testData = [{
      first_name: 'Alice',
      last_name: 'Johnson',
      email: 'alice.johnson@fixedtest.com',
      company_name: 'Fixed Test Industries',
      title: 'CEO',
      phone: '+1-555-0199',
      linkedin_url: 'https://linkedin.com/in/alicejohnson',
      source: 'fixed.test'
    }, {
      first_name: 'Bob',
      last_name: 'Smith',
      email: 'bob.smith@fixedtest.com',
      company_name: 'Fixed Test Industries',
      title: 'CTO',
      phone: '+1-555-0198',
      linkedin_url: 'https://linkedin.com/in/bobsmith',
      source: 'fixed.test'
    }];
    
    const batch_id = `fixed_test_${Date.now()}`;
    const ingestResult = await sql`
      SELECT * FROM intake.f_ingest_json(
        ${testData}::jsonb[], 
        'fixed.test',
        ${batch_id}
      )
    `;
    
    console.log(`   ✅ Ingested ${ingestResult.length} records`);
    ingestResult.forEach((result, i) => {
      console.log(`      ${i + 1}. Load ID: ${result.load_id}, Status: ${result.status}`);
    });
    
    console.log('3️⃣ Promoting data...');
    const promoteResult = await sql`
      SELECT * FROM vault.f_promote_contacts(NULL)
    `;
    
    console.log(`   📤 Promotion completed: ${promoteResult[0].message}`);
    console.log(`      • Promoted: ${promoteResult[0].promoted_count}`);
    console.log(`      • Updated: ${promoteResult[0].updated_count}`);
    console.log(`      • Failed: ${promoteResult[0].failed_count}`);
    
    console.log('4️⃣ Verifying results...');
    const peopleResult = await sql`
      SELECT first_name, last_name, email, title 
      FROM people.marketing_people 
      WHERE source = 'fixed.test'
    `;
    
    const companyResult = await sql`
      SELECT company_name, source
      FROM company.marketing_company 
      WHERE source = 'fixed.test'
    `;
    
    console.log(`   👥 People created: ${peopleResult.length}`);
    peopleResult.forEach(person => {
      console.log(`      • ${person.first_name} ${person.last_name} - ${person.title}`);
    });
    
    console.log(`   🏢 Companies created: ${companyResult.length}`);
    companyResult.forEach(company => {
      console.log(`      • ${company.company_name}`);
    });
    
    if (promoteResult[0].promoted_count > 0) {
      console.log('\n✅ Neon database integration working perfectly!');
      console.log('🎯 Ready for Composio MCP integration!');
      
      // Test the API server health now
      console.log('\n5️⃣ Testing API server health...');
      try {
        const response = await fetch('http://localhost:3000/health');
        const health = await response.json();
        console.log(`   API Status: ${health.status}`);
        console.log(`   Connection: ${health.connection_layer || 'direct'}`);
      } catch (error) {
        console.log('   ⚠️  API server not responding - that\'s OK for now');
      }
      
    } else {
      console.log('\n⚠️  Promotion still having issues');
    }
    
  } catch (error) {
    console.error('Test failed:', error.message);
  }
}

testPromotionFixed().catch(console.error);