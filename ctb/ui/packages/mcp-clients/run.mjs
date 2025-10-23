#!/usr/bin/env node

/**
 * MCP Clients Demo Runner - Demonstrates Composio-focused capabilities
 */

import { createDevelopmentClients } from './dist/factory/client-factory.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function runComposioDemo() {
  console.log('🎯 Starting Composio MCP Demo...\n');
  
  try {
    // Create development clients
    const { composio, reftools, orchestrator } = createDevelopmentClients();
    
    // Test 1: Get available Composio apps
    console.log('1️⃣ Fetching Composio apps...');
    const appsResponse = await composio.getApps('development');
    if (appsResponse.success && appsResponse.data) {
      console.log(`   ✅ Found ${appsResponse.data.length} development apps`);
      appsResponse.data.slice(0, 3).forEach(app => {
        console.log(`   • ${app.name}: ${app.description}`);
      });
    } else {
      console.log(`   ⚠️  ${appsResponse.error || 'No apps found'}`);
    }
    
    // Test 2: Get AI-optimized tools for Claude
    console.log('\n2️⃣ Getting Claude-optimized Composio tools...');
    const toolsResponse = await orchestrator.getAvailableComposioTools('automation');
    if (toolsResponse.success && toolsResponse.data) {
      console.log(`   ✅ Found ${toolsResponse.data.length} automation tools`);
      toolsResponse.data.slice(0, 3).forEach(tool => {
        console.log(`   • ${tool.name}: ${tool.description}`);
      });
    } else {
      console.log(`   ⚠️  ${toolsResponse.error || 'No tools found'}`);
    }
    
    // Test 3: Execute a complex task using orchestrator
    console.log('\n3️⃣ Orchestrating complex task...');
    const taskResult = await orchestrator.orchestrateComplexTask(
      'Create a REST API client with error handling and documentation',
      {
        language: 'javascript',
        framework: 'express',
        features: ['error-handling', 'logging', 'rate-limiting']
      }
    );
    
    if (taskResult.success && taskResult.data) {
      console.log(`   ✅ Task completed: ${taskResult.data.task}`);
      console.log(`   📊 Steps completed: ${taskResult.data.steps_completed.length}`);
      if (taskResult.data.errors.length > 0) {
        console.log(`   ⚠️  Errors: ${taskResult.data.errors.length}`);
      }
    } else {
      console.log(`   ❌ Task failed: ${taskResult.error}`);
    }
    
    // Test 4: Health check all servers
    console.log('\n4️⃣ Health checking all MCP servers...');
    const healthStatus = await orchestrator.healthCheckAllServers();
    
    Object.values(healthStatus).forEach(server => {
      const statusIcon = server.status === 'healthy' ? '✅' : '❌';
      console.log(`   ${statusIcon} ${server.name}: ${server.status} (${server.response_time_ms}ms)`);
    });
    
    // Test 5: Search for API documentation
    console.log('\n5️⃣ Searching API documentation...');
    const docsResponse = await orchestrator.searchAPIDocumentation(
      'Express.js middleware',
      'javascript'
    );
    
    if (docsResponse.success && docsResponse.data) {
      console.log(`   ✅ Found ${docsResponse.data.length} documentation results`);
      docsResponse.data.slice(0, 2).forEach(doc => {
        console.log(`   • ${doc.title}: ${doc.url}`);
      });
    } else {
      console.log(`   ⚠️  ${docsResponse.error || 'No documentation found'}`);
    }
    
    // Test 6: Create and execute a Composio workflow
    console.log('\n6️⃣ Creating Composio workflow...');
    const workflowResponse = await orchestrator.createComposioWorkflow(
      'Automated Code Review Workflow',
      'Automatically review code, run tests, and generate documentation',
      [
        {
          action: 'github_get_pr',
          params: { pr_number: 123, repo: 'example/repo' }
        },
        {
          action: 'code_analysis',
          params: { language: 'javascript', check_style: true }
        },
        {
          action: 'generate_documentation',
          params: { format: 'markdown', include_examples: true }
        }
      ]
    );
    
    if (workflowResponse.success && workflowResponse.data) {
      console.log(`   ✅ Workflow created: ${workflowResponse.data.name}`);
      console.log(`   🆔 Workflow ID: ${workflowResponse.data.id}`);
    } else {
      console.log(`   ⚠️  ${workflowResponse.error || 'Workflow creation failed'}`);
    }
    
    console.log('\n🎉 Composio MCP Demo completed!\n');
    
  } catch (error) {
    console.error('❌ Demo failed:', error.message);
    process.exit(1);
  }
}

// Run the demo
runComposioDemo().catch(console.error);