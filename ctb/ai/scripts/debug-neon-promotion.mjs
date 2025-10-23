/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-BAA77407
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Debug Neon Promotion Issues
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function debugPromotionIssues() {
  console.log('🔍 Debug Neon Promotion Issues\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    const sql = neon(connectionString);
    
    // Check failed loads
    console.log('1️⃣ Checking failed loads...');
    const failedLoads = await sql`
      SELECT load_id, batch_id, raw_data, status, error_message
      FROM intake.raw_loads 
      WHERE status = 'failed'
      ORDER BY created_at DESC
      LIMIT 5
    `;
    
    failedLoads.forEach(load => {
      console.log(`   Load ID ${load.load_id}: ${load.error_message}`);
    });
    
    // Check pending loads
    console.log('\n2️⃣ Checking pending loads...');
    const pendingLoads = await sql`
      SELECT load_id, batch_id, raw_data->'email' as email, raw_data->'company_name' as company
      FROM intake.raw_loads 
      WHERE status = 'pending'
      ORDER BY created_at DESC
      LIMIT 5
    `;
    
    pendingLoads.forEach(load => {
      console.log(`   Load ID ${load.load_id}: ${load.email} at ${load.company}`);
    });
    
    // Check existing companies
    console.log('\n3️⃣ Checking existing companies...');
    const companies = await sql`
      SELECT id, company_name, source
      FROM company.marketing_company 
      WHERE source = 'direct.test'
      LIMIT 5
    `;
    
    console.log(`   Found ${companies.length} test companies`);
    companies.forEach(company => {
      console.log(`   Company: ${company.company_name} (${company.id})`);
    });
    
    // Check existing people
    console.log('\n4️⃣ Checking existing people...');
    const people = await sql`
      SELECT id, first_name, last_name, email, source
      FROM people.marketing_people 
      WHERE source = 'direct.test'
      LIMIT 5
    `;
    
    console.log(`   Found ${people.length} test people`);
    people.forEach(person => {
      console.log(`   Person: ${person.first_name} ${person.last_name} (${person.email})`);
    });
    
    // Test promotion on a single record
    if (pendingLoads.length > 0) {
      console.log('\n5️⃣ Testing single record promotion...');
      const singleLoad = pendingLoads[0];
      try {
        const result = await sql`
          SELECT * FROM vault.f_promote_contacts(ARRAY[${singleLoad.load_id}])
        `;
        console.log(`   ✅ Single promotion result: ${result[0].message}`);
      } catch (error) {
        console.log(`   ❌ Single promotion failed: ${error.message}`);
      }
    }
    
  } catch (error) {
    console.error('Debug failed:', error.message);
  }
}

debugPromotionIssues().catch(console.error);