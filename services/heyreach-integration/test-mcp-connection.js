require('dotenv').config();
const { execSync } = require('child_process');

async function testHeyReachMCP() {
  console.log('🔌 Testing HeyReach MCP Connection...\n');
  
  try {
    // Test if the MCP server is available
    console.log('📦 Checking heyreach-mcp-server installation...');
    
    const packagePath = require.resolve('heyreach-mcp-server/package.json');
    const packageInfo = require(packagePath);
    
    console.log(`✅ Package found: ${packageInfo.name}@${packageInfo.version}`);
    console.log(`   Description: ${packageInfo.description}`);
    
    // Check if the binary is available
    try {
      const help = execSync('npx heyreach-mcp-server --help', { encoding: 'utf8', timeout: 5000 });
      console.log('\n📋 Available commands:');
      console.log(help);
    } catch (error) {
      console.log('⚠️  Binary help not available, but package is installed');
      console.log('   Trying HTTP server version...');
      
      try {
        const httpHelp = execSync('npx heyreach-mcp-http --help', { encoding: 'utf8', timeout: 5000 });
        console.log('\n📋 HTTP Server commands:');
        console.log(httpHelp);
      } catch (httpError) {
        console.log('⚠️  HTTP server help also not available');
      }
    }
    
    console.log('\n🔑 Environment check:');
    if (process.env.HEYREACH_API_KEY) {
      console.log('✅ HEYREACH_API_KEY found');
      console.log(`   Key format: ${process.env.HEYREACH_API_KEY.substring(0, 10)}...`);
    } else {
      console.log('❌ HEYREACH_API_KEY not found in environment');
    }
    
    // Try to start the MCP server (this would normally be done by an MCP client)
    console.log('\n🚀 MCP Server Integration:');
    console.log('The heyreach-mcp-server package provides dual transport support:');
    console.log('- stdio transport for Claude Desktop');
    console.log('- HTTP streaming for web applications');
    console.log('- Header authentication for API access');
    console.log('\nFor direct API usage, we can use the MCP protocol to interact with HeyReach.');
    
  } catch (error) {
    console.log('❌ Failed to test heyreach-mcp-server');
    console.log(`   Error: ${error.message}`);
  }
}

async function testDirectConnection() {
  console.log('\n🧪 Testing direct HeyReach API access...\n');
  
  try {
    const axios = require('axios');
    
    const apiKey = process.env.HEYREACH_API_KEY;
    if (!apiKey) {
      console.log('❌ No API key available for testing');
      return;
    }
    
    console.log('🔌 Testing connection to HeyReach API...');
    
    // Try different endpoint patterns that might work
    const endpoints = [
      'https://api.heyreach.io/api/v1/account',
      'https://api.heyreach.io/api/v2/account', 
      'https://api.heyreach.io/v1/account',
      'https://api.heyreach.io/account',
      'https://api.heyreach.io/api/v1/profile',
      'https://api.heyreach.io/api/v1/campaigns',
      'https://api.heyreach.io/api/campaigns'
    ];
    
    for (const endpoint of endpoints) {
      try {
        console.log(`   Trying: ${endpoint}`);
        const response = await axios.get(endpoint, {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'X-API-Key': apiKey, // Some APIs prefer this header
            'Content-Type': 'application/json'
          },
          timeout: 5000
        });
        
        console.log(`✅ Success! Endpoint works: ${endpoint}`);
        console.log(`   Status: ${response.status}`);
        console.log(`   Data preview: ${JSON.stringify(response.data).substring(0, 100)}...`);
        break;
        
      } catch (error) {
        if (error.response) {
          console.log(`   ${error.response.status}: ${error.response.statusText}`);
        } else {
          console.log(`   Error: ${error.message}`);
        }
      }
    }
    
  } catch (error) {
    console.log('❌ Direct connection test failed');
    console.log(`   Error: ${error.message}`);
  }
}

async function runTests() {
  await testHeyReachMCP();
  await testDirectConnection();
  
  console.log('\n📚 Next steps:');
  console.log('1. Configure MCP client to use heyreach-mcp-server');
  console.log('2. Or integrate MCP protocol into our service');
  console.log('3. Test LinkedIn campaign creation through MCP interface');
  console.log('4. Set up HTTP streaming server for web integration');
}

if (require.main === module) {
  runTests().catch(console.error);
}