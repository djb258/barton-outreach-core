/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-23049768
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

#!/usr/bin/env node
/**
 * Test Apollo CSV Ingestion
 * Simple test to verify the new Apollo ingestion functionality
 */

import axios from 'axios';

const API_BASE = 'http://localhost:3000';

const testCsvData = `email,first_name,last_name,company_name,title,phone
john.doe@example.com,John,Doe,Example Corp,CEO,555-0123
jane.smith@test.com,Jane,Smith,Test Inc,CTO,555-0124
bob.wilson@acme.com,Bob,Wilson,Acme Corp,CFO,555-0125`;

async function testApolloIngestion() {
  console.log('🧪 Testing Apollo CSV Ingestion...\n');

  try {
    // Test 1: Health check
    console.log('1️⃣ Testing API health...');
    const healthResponse = await axios.get(`${API_BASE}/health`);
    console.log(`   ✅ Health Status: ${healthResponse.data.status}`);
    console.log(`   🔌 Connection: ${healthResponse.data.connection_layer}\n`);

    // Test 2: Validate CSV format
    console.log('2️⃣ Testing CSV validation...');
    const validateResponse = await axios.post(`${API_BASE}/apollo/csv/validate`, {
      csv: testCsvData
    });
    
    if (validateResponse.data.success) {
      console.log('   ✅ CSV validation passed');
      console.log(`   📊 Total records: ${validateResponse.data.validation.total_records}`);
      console.log(`   📈 Success rate: ${validateResponse.data.validation.estimated_success_rate.toFixed(1)}%`);
      console.log(`   ⭐ Avg quality: ${validateResponse.data.validation.average_quality_score.toFixed(1)}%\n`);
    } else {
      console.log('   ❌ CSV validation failed:', validateResponse.data.error);
      return;
    }

    // Test 3: Ingest CSV data
    console.log('3️⃣ Testing CSV ingestion to marketing_apollo_raw...');
    const ingestResponse = await axios.post(`${API_BASE}/apollo/csv/ingest`, {
      csv: testCsvData,
      config: {
        source: 'test_script',
        blueprintId: 'test_apollo_import',
        createdBy: 'test_user'
      }
    });
    
    if (ingestResponse.data.success) {
      console.log('   ✅ CSV ingestion successful');
      console.log(`   📥 Inserted: ${ingestResponse.data.result.inserted_count} records`);
      console.log(`   🏷️ Batch ID: ${ingestResponse.data.result.batch_id}`);
      console.log(`   🎯 Target: ${ingestResponse.data.target_table}`);
      console.log(`   ❌ Failed: ${ingestResponse.data.result.failed_records} records\n`);
      
      const batchId = ingestResponse.data.result.batch_id;
      
      // Test 4: Check batch status
      console.log('4️⃣ Testing batch status retrieval...');
      const statusResponse = await axios.get(`${API_BASE}/apollo/batch/${batchId}/status`);
      
      if (statusResponse.data.success) {
        console.log('   ✅ Batch status retrieved');
        console.log(`   📊 Status:`, statusResponse.data.status);
      } else {
        console.log('   ❌ Batch status failed:', statusResponse.data.error);
      }
      
      // Test 5: List recent batches
      console.log('\n5️⃣ Testing batch listing...');
      const batchesResponse = await axios.get(`${API_BASE}/apollo/batches?limit=5`);
      
      if (batchesResponse.data.success) {
        console.log('   ✅ Batch listing successful');
        console.log(`   📋 Found ${batchesResponse.data.batches.length} recent batches`);
      } else {
        console.log('   ❌ Batch listing failed');
      }
      
    } else {
      console.log('   ❌ CSV ingestion failed:', ingestResponse.data.error);
      console.log('   📄 Details:', ingestResponse.data.details);
    }

  } catch (error) {
    console.error('❌ Test failed:', error.response?.data || error.message);
    
    if (error.code === 'ECONNREFUSED') {
      console.log('\n💡 Make sure the API server is running:');
      console.log('   cd apps/api && npm start');
    }
  }
}

// Test different CSV scenarios
async function testCsvScenarios() {
  console.log('\n🔬 Testing different CSV scenarios...\n');
  
  const scenarios = [
    {
      name: 'Invalid Email Format',
      csv: `email,first_name,last_name,company_name
invalid-email,John,Doe,Example Corp
jane@test.com,Jane,Smith,Test Inc`,
      expectValidation: 'partial'
    },
    {
      name: 'Missing Required Fields',
      csv: `first_name,last_name
John,Doe
Jane,Smith`,
      expectValidation: 'fail'
    },
    {
      name: 'High Quality Data',
      csv: `email,first_name,last_name,company_name,title,phone,city,state
john.doe@example.com,John,Doe,Example Corp,CEO,555-0123,San Francisco,CA
jane.smith@test.com,Jane,Smith,Test Inc,CTO,555-0124,New York,NY`,
      expectValidation: 'pass'
    }
  ];
  
  for (const scenario of scenarios) {
    console.log(`📋 Scenario: ${scenario.name}`);
    
    try {
      const response = await axios.post(`${API_BASE}/apollo/csv/validate`, {
        csv: scenario.csv
      });
      
      if (response.data.success) {
        const rate = response.data.validation.estimated_success_rate;
        const quality = response.data.validation.average_quality_score;
        console.log(`   📊 Success rate: ${rate.toFixed(1)}%, Quality: ${quality.toFixed(1)}%`);
        
        if (rate > 80) {
          console.log('   ✅ High success rate');
        } else if (rate > 50) {
          console.log('   ⚠️ Moderate success rate');
        } else {
          console.log('   ❌ Low success rate');
        }
      } else {
        console.log('   ❌ Validation failed:', response.data.error);
      }
    } catch (error) {
      console.log('   ❌ Test error:', error.response?.data?.error || error.message);
    }
    
    console.log('');
  }
}

// Run tests
console.log('🚀 Apollo CSV Ingestion Test Suite');
console.log('=====================================\n');

testApolloIngestion()
  .then(() => testCsvScenarios())
  .then(() => {
    console.log('🎉 All tests completed!');
    console.log('\n📝 Next steps:');
    console.log('   • Check marketing_apollo_raw table for ingested data');
    console.log('   • Verify data quality scores are being calculated');
    console.log('   • Test with larger CSV files');
    console.log('   • Integrate with your existing pipeline');
  })
  .catch((error) => {
    console.error('💥 Test suite failed:', error.message);
    process.exit(1);
  });