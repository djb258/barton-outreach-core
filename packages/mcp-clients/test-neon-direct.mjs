#!/usr/bin/env node

/**
 * Direct Neon Database Test via MCP Client
 * Tests Neon integration through our own MCP client (not Composio)
 */

import { NeonMCPClient } from './dist/clients/neon-mcp-client.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testNeonDirect() {
  console.log('🔐 Testing Direct Neon MCP Integration\n');
  console.log('=' . repeat(60));
  
  try {
    // Create direct Neon client
    const neonClient = new NeonMCPClient({
      connectionString: process.env.NEON_DATABASE_URL || 
                       process.env.DATABASE_URL || 
                       process.env.NEON_MARKETING_DB_URL ||
                       'postgresql://test:test@localhost:5432/test'
    });
    
    // Step 1: Test Connection
    console.log('\n1️⃣ Testing Neon Connection...');
    const healthCheck = await neonClient.healthCheck();
    
    if (healthCheck.success) {
      console.log('   ✅ Connected to Neon successfully');
      console.log(`   📊 Database: ${healthCheck.data?.database || 'Connected'}`);
    } else {
      console.log(`   ❌ Connection failed: ${healthCheck.error}`);
      console.log('   💡 Make sure NEON_DATABASE_URL is set in your environment');
    }
    
    // Step 2: Test Schema Check
    console.log('\n2️⃣ Checking Database Schema...');
    const schemaCheck = await neonClient.checkSchema();
    
    if (schemaCheck.success) {
      console.log('   ✅ Schema verification successful');
      console.log(`   📋 Schemas found: ${schemaCheck.data?.schemas?.join(', ') || 'checking...'}`);
      console.log(`   🔧 Functions: ${schemaCheck.data?.functions?.length || 0} secure functions found`);
    } else {
      console.log(`   ⚠️  Schema check: ${schemaCheck.error}`);
      console.log('   💡 Run: npm run db:setup-company to install schema');
    }
    
    // Step 3: Test Secure Ingestion
    console.log('\n3️⃣ Testing Secure Data Ingestion...');
    
    const testData = [
      {
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        company_name: 'Test Corp',
        title: 'CEO',
        source: 'mcp.test'
      },
      {
        email: 'demo@sample.com', 
        first_name: 'Demo',
        last_name: 'Contact',
        company_name: 'Sample Inc',
        title: 'CTO',
        source: 'mcp.test'
      }
    ];
    
    const ingestResult = await neonClient.secureIngest(testData, 'mcp.test');
    
    if (ingestResult.success) {
      console.log('   ✅ Secure ingestion successful');
      console.log(`   📦 Ingested: ${ingestResult.data?.length || testData.length} records`);
      console.log(`   🆔 Batch ID: ${ingestResult.metadata?.batch_id || 'generated'}`);
    } else {
      console.log(`   ❌ Ingestion failed: ${ingestResult.error}`);
    }
    
    // Step 4: Test Secure Promotion
    console.log('\n4️⃣ Testing Secure Data Promotion...');
    
    const promoteResult = await neonClient.securePromote();
    
    if (promoteResult.success) {
      console.log('   ✅ Secure promotion successful');
      console.log(`   📊 Promoted: ${promoteResult.data?.promoted_count || 0} contacts`);
      console.log(`   🏢 Companies: ${promoteResult.data?.companies_created || 0} created`);
    } else {
      console.log(`   ❌ Promotion failed: ${promoteResult.error}`);
    }
    
    // Step 5: Test Query Operations
    console.log('\n5️⃣ Testing Contact Queries...');
    
    const queryResult = await neonClient.getContacts({ limit: 5 });
    
    if (queryResult.success) {
      console.log('   ✅ Contact query successful');
      console.log(`   👥 Contacts found: ${queryResult.data?.length || 0}`);
      
      if (queryResult.data?.length > 0) {
        console.log('   📋 Sample contacts:');
        queryResult.data.slice(0, 3).forEach((contact, i) => {
          console.log(`      ${i + 1}. ${contact.full_name || contact.email} (${contact.email_status_color} dot)`);
        });
      }
    } else {
      console.log(`   ❌ Query failed: ${queryResult.error}`);
    }
    
    // Step 6: Test Company Operations
    console.log('\n6️⃣ Testing Company Operations...');
    
    const companyResult = await neonClient.getCompanies({ limit: 3 });
    
    if (companyResult.success) {
      console.log('   ✅ Company query successful');
      console.log(`   🏢 Companies found: ${companyResult.data?.length || 0}`);
      
      if (companyResult.data?.length > 0) {
        console.log('   📋 Sample companies:');
        companyResult.data.forEach((company, i) => {
          console.log(`      ${i + 1}. ${company.company_name} (${company.contact_count || 0} contacts)`);
        });
      }
    } else {
      console.log(`   ❌ Company query failed: ${companyResult.error}`);
    }
    
    console.log('\n' + '=' . repeat(60));
    console.log('📊 Direct Neon Test Summary:');
    console.log(`   • Connection: ${healthCheck.success ? '✅ Connected' : '❌ Failed'}`);
    console.log(`   • Schema: ${schemaCheck.success ? '✅ Ready' : '⚠️ Needs setup'}`);
    console.log(`   • Ingestion: ${ingestResult.success ? '✅ Working' : '❌ Failed'}`);
    console.log(`   • Promotion: ${promoteResult.success ? '✅ Working' : '❌ Failed'}`);
    console.log(`   • Queries: ${queryResult.success ? '✅ Working' : '❌ Failed'}`);
    
    // Configuration info
    if (!healthCheck.success) {
      console.log('\n🔧 Setup Instructions:');
      console.log('   1. Set NEON_DATABASE_URL environment variable');
      console.log('   2. Run: npm run db:setup-company');  
      console.log('   3. Ensure user has mcp_ingest, mcp_promote roles');
      console.log('\n💡 Connection String Format:');
      console.log('   postgresql://username:password@host.neon.tech/dbname?sslmode=require');
    }
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check NEON_DATABASE_URL environment variable');
    console.log('   • Verify network connectivity to Neon');
    console.log('   • Ensure database exists and user has permissions');
  }
  
  console.log('\n✅ Direct Neon MCP Test Complete!\n');
}

// Helper function for string repeat
String.prototype.repeat = String.prototype.repeat || function(count) {
  return new Array(count + 1).join(this);
};

// Run the test
testNeonDirect().catch(console.error);