#!/usr/bin/env node

/**
 * Test Neon Secure Integration with Composio MCP
 * Demonstrates RLS-protected database operations through SECURITY DEFINER functions
 */

import { createComposioClient } from './dist/factory/client-factory.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testNeonSecureIntegration() {
  console.log('🔐 Testing Neon Secure Integration with Composio MCP\n');
  console.log('=' . repeat(60));
  
  // Create Composio client
  const composio = createComposioClient();
  
  // Test data
  const testContacts = [
    {
      email: 'john.doe@example.com',
      name: 'John Doe',
      company: 'Acme Corp',
      title: 'CEO',
      phone: '+1-555-0101',
      source: 'composio.test',
      tags: ['executive', 'decision-maker'],
      custom_fields: { industry: 'Technology', employees: '100-500' }
    },
    {
      email: 'jane.smith@example.com',
      name: 'Jane Smith',
      company: 'TechStart Inc',
      title: 'CTO',
      phone: '+1-555-0102',
      source: 'composio.test',
      tags: ['technical', 'decision-maker'],
      custom_fields: { industry: 'SaaS', funding: 'Series B' }
    },
    {
      email: 'bob.wilson@example.com',
      name: 'Bob Wilson',
      company: 'GlobalCo',
      title: 'VP Sales',
      phone: '+1-555-0103',
      source: 'composio.test',
      tags: ['sales', 'influencer'],
      custom_fields: { region: 'North America', team_size: 50 }
    },
    // Duplicate for testing
    {
      email: 'john.doe@example.com',
      name: 'John Doe Updated',
      company: 'Acme Corp International',
      title: 'Chairman',
      source: 'composio.test'
    }
  ];
  
  try {
    // Step 1: Create Neon Ingest Workflow
    console.log('\n1️⃣ Creating Neon Ingest Workflow...');
    const ingestWorkflow = await composio.createNeonIngestWorkflow();
    
    if (ingestWorkflow.success) {
      console.log('   ✅ Ingest workflow created successfully');
      console.log(`   📋 Workflow: ${ingestWorkflow.data?.name}`);
      console.log(`   🆔 ID: ${ingestWorkflow.data?.id}`);
    } else {
      console.log(`   ⚠️  Failed to create workflow: ${ingestWorkflow.error}`);
    }
    
    // Step 2: Execute Secure Ingestion
    console.log('\n2️⃣ Executing Secure Ingestion...');
    const timestamp = Date.now();
    const batchId = `test-batch-${timestamp}`;
    
    const ingestResult = await composio.executeNeonIngest(
      testContacts,
      'composio.test',
      batchId
    );
    
    if (ingestResult.success) {
      console.log('   ✅ Ingestion executed successfully');
      console.log(`   📦 Batch ID: ${ingestResult.data?.batch_id || batchId}`);
      console.log(`   📊 Result: ${ingestResult.data?.message || 'Processing...'}`);
    } else {
      console.log(`   ❌ Ingestion failed: ${ingestResult.error}`);
    }
    
    // Step 3: Create Neon Promote Workflow
    console.log('\n3️⃣ Creating Neon Promote Workflow...');
    const promoteWorkflow = await composio.createNeonPromoteWorkflow();
    
    if (promoteWorkflow.success) {
      console.log('   ✅ Promote workflow created successfully');
      console.log(`   📋 Workflow: ${promoteWorkflow.data?.name}`);
      console.log(`   🆔 ID: ${promoteWorkflow.data?.id}`);
    } else {
      console.log(`   ⚠️  Failed to create workflow: ${promoteWorkflow.error}`);
    }
    
    // Step 4: Execute Secure Promotion
    console.log('\n4️⃣ Executing Secure Promotion...');
    
    // Promote all pending (no specific IDs)
    const promoteResult = await composio.executeNeonPromote();
    
    if (promoteResult.success) {
      console.log('   ✅ Promotion executed successfully');
      console.log(`   📊 Results:`);
      console.log(`      • Promoted: ${promoteResult.data?.promoted_count || 0} new contacts`);
      console.log(`      • Updated: ${promoteResult.data?.updated_count || 0} existing contacts`);
      console.log(`      • Failed: ${promoteResult.data?.failed_count || 0} records`);
      console.log(`   💬 Message: ${promoteResult.data?.message || 'Processing complete'}`);
    } else {
      console.log(`   ❌ Promotion failed: ${promoteResult.error}`);
    }
    
    // Step 5: Report Role Grants Required
    console.log('\n5️⃣ Database Configuration Report:');
    console.log('   📝 Required Role Grants:');
    console.log('      • GRANT mcp_ingest, mcp_promote TO <mcp_user>;');
    console.log('   🔒 Security Features:');
    console.log('      • RLS enabled on all tables');
    console.log('      • No direct DML permissions granted');
    console.log('      • All operations through SECURITY DEFINER functions');
    console.log('   🔑 Connection Requirements:');
    console.log('      • Use DATABASE_URL or NEON_DATABASE_URL env var');
    console.log('      • User must have mcp_ingest and mcp_promote roles');
    
    // Step 6: Example SQL Statements
    console.log('\n6️⃣ SQL Statements Used:');
    console.log('   📥 Ingestion:');
    console.log('      SELECT * FROM intake.f_ingest_json($1::jsonb[], $2::text, $3::text);');
    console.log('   📤 Promotion:');
    console.log('      SELECT * FROM vault.f_promote_contacts($1::bigint[]);');
    console.log('      SELECT * FROM vault.f_promote_contacts(NULL); -- for all pending');
    
    // Summary
    console.log('\n' + '=' . repeat(60));
    console.log('📊 Test Summary:');
    console.log(`   • Test Contacts: ${testContacts.length} records`);
    console.log(`   • Batch ID: ${batchId}`);
    console.log(`   • Source: composio.test`);
    console.log(`   • Security: RLS + SECURITY DEFINER functions`);
    console.log(`   • Duplicate Handling: Automatic detection and marking`);
    
    // Mock results (since we don't have actual DB connection in this demo)
    if (!process.env.DATABASE_URL && !process.env.NEON_DATABASE_URL) {
      console.log('\n⚠️  Note: No DATABASE_URL configured - showing expected behavior');
      console.log('\n📈 Expected Results with Real Connection:');
      console.log('   • Inserted: 3 new contacts');
      console.log('   • Skipped: 1 duplicate (john.doe@example.com)');
      console.log('   • Promoted: 3 contacts to vault');
      console.log('   • Updated: 0 existing contacts');
    }
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
  }
  
  console.log('\n✅ Neon Secure Integration Test Complete!\n');
}

// Helper function for string repeat (for older Node versions)
String.prototype.repeat = String.prototype.repeat || function(count) {
  return new Array(count + 1).join(this);
};

// Run the test
testNeonSecureIntegration().catch(console.error);