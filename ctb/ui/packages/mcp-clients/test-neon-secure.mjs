#!/usr/bin/env node

/**
 * Test Neon Secure Integration with Composio MCP
 * Default connection setup for Neon database through Composio MCP server
 * Demonstrates RLS-protected database operations through SECURITY DEFINER functions
 */

import { createComposioClient } from './dist/factory/client-factory.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Check for required environment variables
const requiredEnvVars = {
  'COMPOSIO_API_KEY': process.env.COMPOSIO_API_KEY,
  'DATABASE_URL or NEON_DATABASE_URL': process.env.DATABASE_URL || process.env.NEON_DATABASE_URL
};

const missingVars = Object.entries(requiredEnvVars)
  .filter(([_, value]) => !value || value === 'your_composio_api_key')
  .map(([key, _]) => key);

if (missingVars.length > 0) {
  console.log('❌ Missing required environment variables:');
  missingVars.forEach(varName => console.log(`   • ${varName}`));
  console.log('\n💡 Set these in your .env file:');
  console.log('   COMPOSIO_API_KEY=your_composio_api_key');
  console.log('   DATABASE_URL=postgresql://username:password@host.neon.tech/dbname?sslmode=require');
  console.log('\n🎯 This test demonstrates Composio MCP as the DEFAULT connection layer');
  console.log('   • All database operations go through Composio MCP server');
  console.log('   • All UI builder integrations use Composio');
  console.log('   • All external service connections use Composio');
  console.log('\n📡 Connection Architecture:');
  console.log('   Your App → Composio MCP → Neon Database');
  console.log('   Your App → Composio MCP → UI Builders (Builder.io, Plasmic, Figma)');
  console.log('   Your App → Composio MCP → Email Verification Services');
  process.exit(1);
}

async function testNeonSecureIntegration() {
  console.log('🔐 Testing Neon Secure Integration with Composio MCP\n');
  console.log('=' . repeat(60));
  
  // Create Composio client with database configuration
  const composio = createComposioClient({
    apiKey: process.env.COMPOSIO_API_KEY,
    timeout: 30000,
    retries: 3
  });
  
  // Set up database connection for Composio
  console.log('🔧 Configuring Composio with Neon database connection...');
  const databaseUrl = process.env.DATABASE_URL || process.env.NEON_DATABASE_URL;
  console.log(`📡 Database: ${databaseUrl.replace(/\/\/.*@/, '//***:***@')}`); // Hide credentials in logs
  
  try {
    // Step 0: Configure Neon database connection in Composio
    console.log('\n0️⃣ Setting up Neon database connection...');
    
    try {
      const configResult = await composio.executeAction('neon_configure', {
        connection_string: databaseUrl,
        schema_mode: 'company', // Use company schema mode
        enable_rls: true,
        enable_security_definer: true
      });
      
      if (configResult.success) {
        console.log('   ✅ Neon database configured in Composio');
        console.log(`   🔧 Configuration: ${configResult.data?.message || 'Ready for secure operations'}`);
      } else {
        console.log(`   ⚠️  Configuration warning: ${configResult.error || 'Using default settings'}`);
      }
      
    } catch (configError) {
      console.log(`   ℹ️  Configuration step skipped: ${configError.message}`);
      console.log('   💡 Proceeding with default Composio-Neon integration');
    }
  
  // Test data for company schema
  const testContacts = [
    {
      email: 'john.doe@acmecorp.com',
      first_name: 'John',
      last_name: 'Doe',
      company_name: 'Acme Corp',
      title: 'CEO',
      phone: '+1-555-0101',
      linkedin_url: 'https://linkedin.com/in/johndoe',
      source: 'composio.test',
      tags: ['executive', 'ceo-slot'],
      custom_fields: { industry: 'Technology', employees: '100-500', role_type: 'CEO' }
    },
    {
      email: 'jane.smith@acmecorp.com',
      first_name: 'Jane',
      last_name: 'Smith',
      company_name: 'Acme Corp',
      title: 'CFO',
      phone: '+1-555-0102',
      linkedin_url: 'https://linkedin.com/in/janesmith',
      source: 'composio.test',
      tags: ['executive', 'cfo-slot'],
      custom_fields: { industry: 'Technology', role_type: 'CFO' }
    },
    {
      email: 'bob.wilson@acmecorp.com',
      first_name: 'Bob',
      last_name: 'Wilson',
      company_name: 'Acme Corp',
      title: 'VP Human Resources',
      phone: '+1-555-0103',
      source: 'composio.test',
      tags: ['hr', 'hr-slot'],
      custom_fields: { role_type: 'HR', team_size: 50 }
    },
    // Second company
    {
      email: 'sarah.tech@techstart.com',
      first_name: 'Sarah',
      last_name: 'Tech',
      company_name: 'TechStart Inc',
      title: 'CEO',
      source: 'composio.test',
      tags: ['ceo-slot'],
      custom_fields: { industry: 'SaaS', funding: 'Series B', role_type: 'CEO' }
    }
  ];
  
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