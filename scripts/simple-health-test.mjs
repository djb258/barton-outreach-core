#!/usr/bin/env node
/**
 * Simple health check to verify our Apollo endpoints are working
 */

import axios from 'axios';

const API_BASE = 'http://localhost:3000';

async function testHealth() {
  try {
    console.log('🔍 Testing API health...');
    const response = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
    console.log('✅ Health check passed:', response.data.status);
    console.log('🔌 Connection layer:', response.data.connection_layer);
    return true;
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('❌ API server not running. Please start it with:');
      console.log('   cd apps/api && npm start');
    } else {
      console.log('❌ Health check failed:', error.message);
    }
    return false;
  }
}

async function testEndpoints() {
  console.log('🔍 Testing endpoint availability...');
  
  const endpoints = [
    { method: 'GET', path: '/', name: 'API docs' },
    { method: 'POST', path: '/apollo/csv/validate', name: 'Apollo CSV validation' },
    { method: 'POST', path: '/apollo/csv/ingest', name: 'Apollo CSV ingestion' },
    { method: 'GET', path: '/apollo/batches', name: 'Apollo batch listing' }
  ];
  
  for (const endpoint of endpoints) {
    try {
      if (endpoint.method === 'GET') {
        const response = await axios.get(`${API_BASE}${endpoint.path}`, { timeout: 2000 });
        console.log(`   ✅ ${endpoint.name}: Available`);
      } else {
        // For POST endpoints, just check they're not 404
        try {
          await axios.post(`${API_BASE}${endpoint.path}`, {}, { timeout: 2000 });
        } catch (error) {
          if (error.response?.status === 400) {
            console.log(`   ✅ ${endpoint.name}: Available (400 = validation error as expected)`);
          } else {
            console.log(`   ⚠️ ${endpoint.name}: ${error.response?.status || 'Unknown'}`);
          }
        }
      }
    } catch (error) {
      if (error.response?.status === 404) {
        console.log(`   ❌ ${endpoint.name}: Not found`);
      } else {
        console.log(`   ⚠️ ${endpoint.name}: ${error.message}`);
      }
    }
  }
}

console.log('🧪 Quick API Endpoint Test');
console.log('==========================\n');

testHealth()
  .then((healthy) => {
    if (healthy) {
      return testEndpoints();
    }
  })
  .then(() => {
    console.log('\n🎉 Quick test completed!');
    console.log('\n📝 If all endpoints are available, you can test CSV ingestion with:');
    console.log('   node scripts/test-apollo-ingest.mjs');
  })
  .catch(console.error);