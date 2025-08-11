require('dotenv').config();
const { ApifyClient } = require('apify-client');
const { neon } = require('@neondatabase/serverless');

console.log('======================================');
console.log('  SCRAPING TOOL DIAGNOSTIC TEST');
console.log('======================================\n');

// Test results storage
const testResults = {
  environment: { status: 'pending', issues: [] },
  database: { status: 'pending', issues: [] },
  apify: { status: 'pending', issues: [] },
  modules: { status: 'pending', issues: [] }
};

// 1. TEST ENVIRONMENT VARIABLES
console.log('1. CHECKING ENVIRONMENT VARIABLES');
console.log('----------------------------------');

const requiredEnvVars = ['NEON_DATABASE_URL', 'APIFY_API_KEY', 'APIFY_TASK_ID'];
const envVarStatus = {};

requiredEnvVars.forEach(varName => {
  const value = process.env[varName];
  if (value) {
    envVarStatus[varName] = '✓ SET';
    if (varName === 'APIFY_API_KEY') {
      console.log(`   ${varName}: ✓ SET (${value.substring(0, 20)}...)`);
    } else if (varName === 'NEON_DATABASE_URL') {
      const urlParts = value.match(/postgresql:\/\/([^:]+):[^@]+@([^\/]+)\/(.+)/);
      if (urlParts) {
        console.log(`   ${varName}: ✓ SET (user: ${urlParts[1]}, host: ${urlParts[2]}, db: ${urlParts[3]})`);
      } else {
        console.log(`   ${varName}: ✓ SET`);
      }
    } else {
      console.log(`   ${varName}: ✓ SET (${value})`);
    }
  } else {
    envVarStatus[varName] = '✗ NOT SET';
    console.log(`   ${varName}: ✗ NOT SET`);
    testResults.environment.issues.push(`${varName} is not set`);
  }
});

const optionalEnvVars = ['DRY_RUN'];
optionalEnvVars.forEach(varName => {
  const value = process.env[varName];
  console.log(`   ${varName}: ${value ? `SET (${value})` : 'NOT SET (will default)'}`);
});

testResults.environment.status = testResults.environment.issues.length === 0 ? 'passed' : 'failed';

// 2. TEST MODULE IMPORTS
console.log('\n2. CHECKING MODULE IMPORTS');
console.log('----------------------------------');

const modules = [
  { name: 'getPendingCompanies', path: './modules/getPendingCompanies' },
  { name: 'runApifyScrape', path: './modules/runApifyScrape' },
  { name: 'pollApifyRun', path: './modules/pollApifyRun' },
  { name: 'fetchApifyDataset', path: './modules/fetchApifyDataset' },
  { name: 'filterContactsByTitle', path: './modules/filterContactsByTitle' },
  { name: 'writeResults', path: './modules/writeResults' },
  { name: 'markCompanyStatus', path: './modules/markCompanyStatus' }
];

modules.forEach(mod => {
  try {
    const module = require(mod.path);
    if (module[mod.name]) {
      console.log(`   ✓ ${mod.name} loaded successfully`);
    } else {
      console.log(`   ✗ ${mod.name} export not found`);
      testResults.modules.issues.push(`${mod.name} export not found`);
    }
  } catch (error) {
    console.log(`   ✗ ${mod.name} failed to load: ${error.message}`);
    testResults.modules.issues.push(`${mod.name}: ${error.message}`);
  }
});

testResults.modules.status = testResults.modules.issues.length === 0 ? 'passed' : 'failed';

// 3. TEST DATABASE CONNECTION
console.log('\n3. TESTING DATABASE CONNECTION');
console.log('----------------------------------');

async function testDatabase() {
  if (!process.env.NEON_DATABASE_URL) {
    console.log('   ✗ Skipping: NEON_DATABASE_URL not set');
    testResults.database.status = 'skipped';
    testResults.database.issues.push('NEON_DATABASE_URL not configured');
    return;
  }

  try {
    const sql = neon(process.env.NEON_DATABASE_URL);
    console.log('   Testing connection...');
    
    // Test basic connectivity
    const result = await sql`SELECT version()`;
    console.log(`   ✓ Connected to PostgreSQL: ${result[0].version.split(' ')[0]} ${result[0].version.split(' ')[1]}`);
    
    // Check if required table exists
    const tableCheck = await sql`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'marketing_company_intake'
      ) as table_exists
    `;
    
    if (tableCheck[0].table_exists) {
      console.log('   ✓ Table "marketing_company_intake" exists');
      
      // Check table structure
      const columns = await sql`
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'marketing_company_intake'
        AND column_name IN ('id', 'company_name', 'apollo_url', 'scrape_status', 'apollo_url_validated')
      `;
      
      console.log(`   ✓ Found ${columns.length} required columns`);
      
      // Count pending companies
      const pendingCount = await sql`
        SELECT COUNT(*) as count
        FROM marketing_company_intake
        WHERE scrape_status = 'PENDING'
      `;
      
      console.log(`   ℹ Pending companies to scrape: ${pendingCount[0].count}`);
      testResults.database.status = 'passed';
    } else {
      console.log('   ✗ Table "marketing_company_intake" does not exist');
      testResults.database.issues.push('Required table missing');
      testResults.database.status = 'failed';
    }
  } catch (error) {
    console.log(`   ✗ Database connection failed: ${error.message}`);
    testResults.database.issues.push(error.message);
    testResults.database.status = 'failed';
  }
}

// 4. TEST APIFY CONNECTION
console.log('\n4. TESTING APIFY API CONNECTION');
console.log('----------------------------------');

async function testApify() {
  if (!process.env.APIFY_API_KEY) {
    console.log('   ✗ Skipping: APIFY_API_KEY not set');
    testResults.apify.status = 'skipped';
    testResults.apify.issues.push('APIFY_API_KEY not configured');
    return;
  }

  try {
    const client = new ApifyClient({ token: process.env.APIFY_API_KEY });
    
    // Test authentication by getting user info
    console.log('   Testing authentication...');
    const user = await client.user().get();
    console.log(`   ✓ Authenticated as: ${user.username}`);
    
    // Check if task exists (if APIFY_TASK_ID is set)
    if (process.env.APIFY_TASK_ID) {
      try {
        const task = await client.task(process.env.APIFY_TASK_ID).get();
        console.log(`   ✓ Task found: ${task.name}`);
        console.log(`   ℹ Task actor: ${task.actId}`);
      } catch (error) {
        if (error.statusCode === 404) {
          console.log(`   ✗ Task not found: ${process.env.APIFY_TASK_ID}`);
          testResults.apify.issues.push('Task ID not found');
        } else {
          throw error;
        }
      }
    } else {
      console.log('   ⚠ APIFY_TASK_ID not set - cannot verify task');
      testResults.apify.issues.push('APIFY_TASK_ID not configured');
    }
    
    testResults.apify.status = testResults.apify.issues.length === 0 ? 'passed' : 'partial';
  } catch (error) {
    console.log(`   ✗ Apify API test failed: ${error.message}`);
    if (error.statusCode === 401) {
      console.log('   ℹ The API key appears to be invalid or expired');
    }
    testResults.apify.issues.push(error.message);
    testResults.apify.status = 'failed';
  }
}

// RUN ALL TESTS
async function runAllTests() {
  await testDatabase();
  await testApify();
  
  // SUMMARY
  console.log('\n======================================');
  console.log('  TEST SUMMARY');
  console.log('======================================');
  
  const statusSymbols = {
    passed: '✓',
    failed: '✗',
    partial: '⚠',
    skipped: '○',
    pending: '?'
  };
  
  Object.entries(testResults).forEach(([test, result]) => {
    const symbol = statusSymbols[result.status];
    const testName = test.charAt(0).toUpperCase() + test.slice(1);
    console.log(`${symbol} ${testName}: ${result.status.toUpperCase()}`);
    if (result.issues.length > 0) {
      result.issues.forEach(issue => {
        console.log(`     - ${issue}`);
      });
    }
  });
  
  // RECOMMENDATIONS
  console.log('\n======================================');
  console.log('  RECOMMENDATIONS');
  console.log('======================================');
  
  if (testResults.environment.status === 'failed') {
    console.log('1. Create a .env file with required environment variables:');
    console.log('   - Copy .env.example to .env');
    console.log('   - Fill in your actual credentials');
  }
  
  if (testResults.database.status === 'failed' || testResults.database.status === 'skipped') {
    console.log('2. Set up your Neon database:');
    console.log('   - Create a Neon account at https://neon.tech');
    console.log('   - Create a new database');
    console.log('   - Run the SQL scripts to create required tables');
    console.log('   - Add the connection string to your .env file');
  }
  
  if (testResults.apify.status === 'failed' || testResults.apify.status === 'skipped') {
    console.log('3. Configure Apify:');
    console.log('   - Create an Apify account at https://apify.com');
    console.log('   - Get your API token from account settings');
    console.log('   - Create or identify your Apollo scraper task');
    console.log('   - Add credentials to your .env file');
  }
  
  const allPassed = Object.values(testResults).every(r => r.status === 'passed');
  if (allPassed) {
    console.log('✅ All tests passed! The scraping tool is ready to use.');
    console.log('\nTo run the scraper:');
    console.log('   npm start');
  } else {
    console.log('\n⚠️  Some issues need to be resolved before the tool can run properly.');
  }
}

// Execute tests
runAllTests().catch(error => {
  console.error('\n✗ Test suite failed:', error);
  process.exit(1);
});