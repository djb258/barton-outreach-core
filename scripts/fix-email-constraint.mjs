#!/usr/bin/env node

/**
 * Fix Email Constraint Issue for people.marketing_people
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function fixEmailConstraint() {
  console.log('🔧 Fixing Email Constraint Issue\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    const sql = neon(connectionString);
    
    console.log('1️⃣ Adding unique constraint on email...');
    
    try {
      await sql`
        ALTER TABLE people.marketing_people 
        ADD CONSTRAINT unique_marketing_people_email UNIQUE (email);
      `;
      console.log('   ✅ Unique constraint added on email column');
    } catch (error) {
      if (error.message.includes('already exists')) {
        console.log('   ℹ️  Unique constraint already exists');
      } else {
        console.log(`   ⚠️  Constraint issue: ${error.message}`);
        
        // Check for duplicate emails first
        console.log('2️⃣ Checking for duplicate emails...');
        const duplicates = await sql`
          SELECT email, COUNT(*) as count
          FROM people.marketing_people 
          WHERE email IS NOT NULL
          GROUP BY email
          HAVING COUNT(*) > 1
        `;
        
        if (duplicates.length > 0) {
          console.log(`   ⚠️  Found ${duplicates.length} duplicate emails`);
          duplicates.forEach(dup => {
            console.log(`      ${dup.email}: ${dup.count} occurrences`);
          });
          console.log('   💡 Clean up duplicates before adding constraint');
        } else {
          console.log('   ✅ No duplicate emails found');
          
          // Try creating a partial unique index for non-null emails
          try {
            await sql`
              CREATE UNIQUE INDEX CONCURRENTLY unique_marketing_people_email_idx 
              ON people.marketing_people (email) 
              WHERE email IS NOT NULL;
            `;
            console.log('   ✅ Partial unique index created');
          } catch (indexError) {
            console.log(`   ⚠️  Index creation failed: ${indexError.message}`);
          }
        }
      }
    }
    
    console.log('\n3️⃣ Testing promotion function with fixed constraint...');
    
    // Clear any existing test data
    await sql`
      DELETE FROM intake.raw_loads WHERE source = 'constraint.test';
      DELETE FROM people.marketing_people WHERE source = 'constraint.test';
      DELETE FROM company.marketing_company WHERE source = 'constraint.test';
    `;
    
    // Test data
    const testData = [{
      first_name: 'Test',
      last_name: 'User',
      email: 'test.constraint@example.com',
      company_name: 'Constraint Test Co',
      title: 'Test Manager',
      source: 'constraint.test'
    }];
    
    // Ingest test data
    const batch_id = `constraint_test_${Date.now()}`;
    const ingestResult = await sql`
      SELECT * FROM intake.f_ingest_json(
        ${testData}::jsonb[], 
        'constraint.test',
        ${batch_id}
      )
    `;
    
    console.log(`   📥 Ingested ${ingestResult.length} test records`);
    
    // Try promotion
    const promoteResult = await sql`
      SELECT * FROM vault.f_promote_contacts(NULL)
    `;
    
    console.log(`   📤 Promotion result: ${promoteResult[0].message}`);
    
    if (promoteResult[0].promoted_count > 0) {
      console.log('   ✅ Email constraint issue resolved!');
    } else {
      console.log('   ⚠️  Still having issues, checking logs...');
      
      const failedLoads = await sql`
        SELECT error_message 
        FROM intake.raw_loads 
        WHERE source = 'constraint.test' AND status = 'failed'
      `;
      
      failedLoads.forEach(load => {
        console.log(`      Error: ${load.error_message}`);
      });
    }
    
  } catch (error) {
    console.error('Fix failed:', error.message);
  }
}

fixEmailConstraint().catch(console.error);