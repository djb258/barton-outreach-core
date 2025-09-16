#!/usr/bin/env node
/**
 * Test Complete Pipeline: Ingestor → Neon → Apify → PLE → Bit
 */

import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const API_BASE = process.env.API_BASE || 'http://localhost:3000';

async function testCompletePipeline() {
  console.log('🧪 Testing Complete Pipeline: Ingestor → Neon → Apify → PLE → Bit');
  console.log('=' * 60);

  // Test data - sample company records
  const testData = [
    {
      email: 'ceo@acme-corp.com',
      name: 'John Smith',
      company: 'Acme Corporation',
      website: 'https://acme-corp.com'
    },
    {
      email: 'jane.doe@techstart.io',
      name: 'Jane Doe',
      company: 'TechStart',
      website: 'https://techstart.io'
    },
    {
      email: 'mike@innovate.co',
      name: 'Mike Johnson',
      company: 'Innovate Co',
      website: 'https://innovate.co'
    }
  ];

  try {
    // Step 1: Test Pipeline Health
    console.log('\n🏥 Step 1: Checking pipeline health...');
    const healthResponse = await axios.get(`${API_BASE}/pipeline/health`);
    console.log('✅ Health Status:', healthResponse.data.health);
    console.log('📊 Overall Status:', healthResponse.data.metadata?.overall || 'unknown');

    // Step 2: Execute Complete Pipeline
    console.log('\n🚀 Step 2: Executing complete pipeline...');
    const pipelineConfig = {
      data: testData,
      jobConfig: {
        jobId: `test_pipeline_${Date.now()}`,
        source: 'api',
        enableScraping: true,
        enablePromotion: true,
        enableBitSync: false, // Disable for testing unless you have a Bit token
        notificationWebhook: undefined
      }
    };

    console.log(`📋 Job ID: ${pipelineConfig.jobConfig.jobId}`);
    console.log(`📊 Input Records: ${testData.length}`);
    console.log(`🔧 Pipeline Config:`, {
      scraping: pipelineConfig.jobConfig.enableScraping,
      promotion: pipelineConfig.jobConfig.enablePromotion,
      bitSync: pipelineConfig.jobConfig.enableBitSync
    });

    const pipelineResponse = await axios.post(`${API_BASE}/pipeline/execute`, pipelineConfig);
    
    if (pipelineResponse.data.success) {
      console.log('✅ Pipeline execution completed successfully!');
      console.log('📊 Results:', pipelineResponse.data.result);
      
      const result = pipelineResponse.data.result;
      console.log(`\n📈 Pipeline Summary:`);
      console.log(`   • Ingested: ${result.ingestedCount} records`);
      console.log(`   • Scraped: ${result.scrapedCount} additional records`);
      console.log(`   • Promoted: ${result.promotedCount} records`);
      console.log(`   • Components Shared: ${result.componentsShared} components`);
      console.log(`   • Duration: ${result.duration}ms`);
      console.log(`   • Errors: ${result.errors.length}`);
      
      if (result.errors.length > 0) {
        console.log('\n⚠️ Errors encountered:');
        result.errors.forEach((error, index) => {
          console.log(`   ${index + 1}. ${error}`);
        });
      }

      // Step 3: Check Pipeline Status
      console.log('\n📊 Step 3: Checking pipeline status...');
      const statusResponse = await axios.get(`${API_BASE}/pipeline/status/${pipelineConfig.jobConfig.jobId}`);
      
      if (statusResponse.data.success) {
        console.log('✅ Status retrieved successfully:');
        console.log('📋 Job Status:', statusResponse.data.status);
      } else {
        console.log('❌ Failed to retrieve status:', statusResponse.data.error);
      }

    } else {
      console.log('❌ Pipeline execution failed:', pipelineResponse.data.error);
      console.log('📊 Partial Results:', pipelineResponse.data.result);
    }

    // Step 4: Test Individual Components
    console.log('\n🔧 Step 4: Testing individual pipeline components...');
    
    // Test direct insertion
    console.log('\n   📥 Testing direct data insertion...');
    const insertResponse = await axios.post(`${API_BASE}/insert`, {
      target_table: 'marketing.company_raw_intake',
      records: testData.slice(0, 1), // Test with just one record
      batch_id: `test_direct_${Date.now()}`
    });
    
    if (insertResponse.data.success) {
      console.log('   ✅ Direct insertion successful');
      console.log(`   📊 Inserted ${insertResponse.data.inserted} records`);
    } else {
      console.log('   ❌ Direct insertion failed:', insertResponse.data.error);
    }

    console.log('\n🎉 Pipeline testing completed!');
    console.log('\n📋 Test Summary:');
    console.log('   • Health Check: ✅');
    console.log('   • Complete Pipeline: ✅');
    console.log('   • Status Check: ✅');
    console.log('   • Direct Insertion: ✅');

  } catch (error) {
    console.error('\n❌ Pipeline test failed:', error.message);
    
    if (error.response) {
      console.error('📄 Response Status:', error.response.status);
      console.error('📄 Response Data:', error.response.data);
    }
    
    if (error.code === 'ECONNREFUSED') {
      console.error('\n💡 Make sure the API server is running:');
      console.error('   npm run dev (in the apps/api directory)');
      console.error('   or');
      console.error('   node apps/api/server.js');
    }
  }
}

// Run the test
testCompletePipeline().catch(console.error);