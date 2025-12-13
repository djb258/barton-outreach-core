require('dotenv').config();
const { execSync } = require('child_process');

async function testInstantlyMCP() {
  console.log('🔌 Testing Instantly MCP Connection...\n');
  
  try {
    // Test if the MCP server is available
    console.log('📦 Checking instantly-mcp installation...');
    
    const packagePath = require.resolve('instantly-mcp/package.json');
    const packageInfo = require(packagePath);
    
    console.log(`✅ Package found: ${packageInfo.name}@${packageInfo.version}`);
    console.log(`   Description: ${packageInfo.description}`);
    
    // Check if the binary is available
    try {
      const help = execSync('npx instantly-mcp --help', { encoding: 'utf8', timeout: 5000 });
      console.log('\n📋 Available commands:');
      console.log(help);
    } catch (error) {
      console.log('⚠️  Binary help not available, but package is installed');
    }
    
    console.log('\n🔑 Environment check:');
    if (process.env.INSTANTLY_API_KEY) {
      console.log('✅ INSTANTLY_API_KEY found');
      console.log(`   Key format: ${process.env.INSTANTLY_API_KEY.substring(0, 10)}...`);
    } else {
      console.log('❌ INSTANTLY_API_KEY not found in environment');
    }
    
    // Try to start the MCP server (this would normally be done by an MCP client)
    console.log('\n🚀 MCP Server Integration:');
    console.log('The instantly-mcp package provides an MCP server that can be used with:');
    console.log('- Claude Desktop');
    console.log('- Cursor IDE'); 
    console.log('- Other MCP-compatible clients');
    console.log('\nFor direct API usage, we can use the MCP protocol to interact with Instantly.');
    
  } catch (error) {
    console.log('❌ Failed to test instantly-mcp');
    console.log(`   Error: ${error.message}`);
  }
}

async function testDirectConnection() {
  console.log('\n🧪 Testing direct Instantly API access...\n');
  
  try {
    // We can still use axios for direct API calls
    const axios = require('axios');
    
    const apiKey = process.env.INSTANTLY_API_KEY;
    if (!apiKey) {
      console.log('❌ No API key available for testing');
      return;
    }
    
    console.log('🔌 Testing connection to Instantly API...');
    
    // Try different endpoint patterns that might work
    const endpoints = [
      'https://api.instantly.ai/api/v1/account',
      'https://api.instantly.ai/api/v2/account',
      'https://api.instantly.ai/v1/account',
      'https://api.instantly.ai/account'
    ];
    
    for (const endpoint of endpoints) {
      try {
        console.log(`   Trying: ${endpoint}`);
        const response = await axios.get(endpoint, {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
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
  await testInstantlyMCP();
  await testDirectConnection();
  
  console.log('\n📚 Next steps:');
  console.log('1. Configure MCP client to use instantly-mcp server');
  console.log('2. Or integrate MCP protocol into our service');
  console.log('3. Test campaign creation through MCP interface');
}

if (require.main === module) {
  runTests().catch(console.error);
}