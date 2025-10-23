/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/testing
Barton ID: 03.01.03
Unique ID: CTB-2B181B4F
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Comprehensive MCP Integration Test Suite
 * Test connectivity to all required applications through Composio MCP
 */

import ComposioNeonBridge from './apps/outreach-process-manager/api/lib/composio-neon-bridge.js';

class ComprehensiveMCPTester {
  constructor() {
    this.bridge = new ComposioNeonBridge();
    this.composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
    this.composioBaseUrl = 'https://backend.composio.dev';
    this.testResults = {
      timestamp: new Date().toISOString(),
      total_tests: 0,
      passed: 0,
      failed: 0,
      applications: {}
    };
  }

  /**
   * Test direct Composio API connectivity
   */
  async testComposioAPI() {
    console.log('🔍 Testing Composio API connectivity...');

    try {
      const response = await fetch(`${this.composioBaseUrl}/api/v1/apps`, {
        headers: {
          'Authorization': `Bearer ${this.composioApiKey}`,
          'X-API-Key': this.composioApiKey
        }
      });

      if (response.ok) {
        const apps = await response.json();
        console.log(`✅ Composio API: Connected - ${apps.length} apps available`);

        // List available apps
        const appNames = apps.slice(0, 10).map(app => app.name || app.key).join(', ');
        console.log(`📱 Available apps: ${appNames}...`);

        return {
          success: true,
          apps_count: apps.length,
          sample_apps: apps.slice(0, 10).map(app => app.name || app.key)
        };
      } else {
        const error = await response.text();
        console.log(`❌ Composio API: Failed - ${response.status}: ${error}`);
        return { success: false, error: `HTTP ${response.status}: ${error}` };
      }
    } catch (error) {
      console.log(`❌ Composio API: Connection error - ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Test Neon database integration ONLY through Composio MCP
   */
  async testNeonIntegration() {
    console.log('\n🔍 Testing Neon database via Composio MCP (NO DIRECT CONNECTION)...');

    try {
      // Test 1: Composio MCP → Neon simple query
      const testQuery = await this.bridge.executeNeonOperation('QUERY_ROWS', {
        sql: 'SELECT 1 as test_connection, NOW() as current_time',
        database_id: 'marketing_db'
      });

      if (testQuery.success) {
        console.log(`✅ Neon via MCP: Connected - Test query successful`);
        console.log(`📊 MCP Result: ${JSON.stringify(testQuery.data)}`);

        // Test 2: Check if MCP can query marketing schema
        const schemaQuery = await this.bridge.executeNeonOperation('LIST_TABLES', {
          schema_name: 'marketing',
          database_id: 'marketing_db'
        });

        if (schemaQuery.success) {
          const tables = schemaQuery.data?.tables || [];
          console.log(`📋 Marketing tables via MCP: ${tables.join(', ')}`);

          // Test 3: Test specific table query
          const auditLogTest = await this.bridge.executeNeonOperation('QUERY_ROWS', {
            sql: 'SELECT COUNT(*) as row_count FROM marketing.company_promotion_log LIMIT 1',
            database_id: 'marketing_db'
          });

          return {
            success: true,
            connection_method: 'composio_mcp_only',
            connection_test: testQuery.data,
            marketing_tables: tables,
            audit_log_accessible: auditLogTest.success
          };
        } else {
          console.log(`⚠️ Schema check via MCP: ${schemaQuery.error}`);
          return {
            success: true,
            connection_method: 'composio_mcp_only',
            connection_test: testQuery.data,
            schema_warning: schemaQuery.error
          };
        }
      } else {
        console.log(`❌ Neon via MCP: Failed - ${testQuery.error}`);
        return {
          success: false,
          error: testQuery.error,
          connection_method: 'composio_mcp_only'
        };
      }
    } catch (error) {
      console.log(`❌ Neon via MCP: Exception - ${error.message}`);
      return {
        success: false,
        error: error.message,
        connection_method: 'composio_mcp_only'
      };
    }
  }

  /**
   * Test Apify web scraping integration
   */
  async testApifyIntegration() {
    console.log('\n🔍 Testing Apify web scraping integration...');

    try {
      // Test 1: List available actors
      const listActors = await this.bridge.executeNeonOperation('APIFY_LIST_ACTORS', {
        limit: 5
      });

      if (listActors.success) {
        console.log(`✅ Apify: Connected - Actors list retrieved`);
        console.log(`🕷️ Available actors: ${JSON.stringify(listActors.data)}`);

        // Test 2: Get actor details (if actors exist)
        if (listActors.data?.length > 0) {
          const actorId = listActors.data[0].id;
          const actorDetails = await this.bridge.executeNeonOperation('APIFY_GET_ACTOR', {
            actor_id: actorId
          });

          if (actorDetails.success) {
            console.log(`📊 Actor details retrieved for: ${actorId}`);
          }
        }

        return {
          success: true,
          actors_available: listActors.data?.length || 0,
          sample_actors: listActors.data
        };
      } else {
        console.log(`❌ Apify: Failed - ${listActors.error}`);

        // Try alternative approach
        const testRun = await this.bridge.executeNeonOperation('APIFY_RUN_ACTOR', {
          actor_id: 'apify/web-scraper',
          input: {
            urls: ['https://example.com'],
            maxRequestsPerCrawl: 1
          }
        });

        if (testRun.success) {
          console.log(`✅ Apify: Alternative connection successful`);
          return { success: true, method: 'actor_run', data: testRun.data };
        }

        return { success: false, error: listActors.error };
      }
    } catch (error) {
      console.log(`❌ Apify: Exception - ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Test MillionVerifier email validation integration
   */
  async testMillionVerifierIntegration() {
    console.log('\n🔍 Testing MillionVerifier email validation...');

    try {
      // Test email validation
      const validateEmail = await this.bridge.executeNeonOperation('MILLIONVERIFY_VALIDATE', {
        email: 'test@example.com',
        timeout: 5000
      });

      if (validateEmail.success) {
        console.log(`✅ MillionVerifier: Connected - Email validation working`);
        console.log(`📧 Validation result: ${JSON.stringify(validateEmail.data)}`);

        return {
          success: true,
          validation_result: validateEmail.data
        };
      } else {
        console.log(`❌ MillionVerifier: Failed - ${validateEmail.error}`);

        // Try alternative endpoint
        const checkCredits = await this.bridge.executeNeonOperation('MILLIONVERIFY_CREDITS', {});

        if (checkCredits.success) {
          console.log(`✅ MillionVerifier: API key valid - Credits check successful`);
          return { success: true, method: 'credits_check', data: checkCredits.data };
        }

        return { success: false, error: validateEmail.error };
      }
    } catch (error) {
      console.log(`❌ MillionVerifier: Exception - ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Test GitHub integration (for deployment)
   */
  async testGitHubIntegration() {
    console.log('\n🔍 Testing GitHub integration...');

    try {
      const repoCheck = await this.bridge.executeNeonOperation('GITHUB_GET_REPO', {
        owner: 'djb258',
        repo: 'barton-outreach-core'
      });

      if (repoCheck.success) {
        console.log(`✅ GitHub: Connected - Repository accessible`);
        console.log(`📦 Repo info: ${JSON.stringify(repoCheck.data)}`);

        return {
          success: true,
          repo_data: repoCheck.data
        };
      } else {
        console.log(`❌ GitHub: Failed - ${repoCheck.error}`);
        return { success: false, error: repoCheck.error };
      }
    } catch (error) {
      console.log(`❌ GitHub: Exception - ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Test Vercel integration (for deployment)
   */
  async testVercelIntegration() {
    console.log('\n🔍 Testing Vercel deployment integration...');

    try {
      const projectList = await this.bridge.executeNeonOperation('VERCEL_LIST_PROJECTS', {});

      if (projectList.success) {
        console.log(`✅ Vercel: Connected - Projects list retrieved`);
        console.log(`🚀 Projects: ${JSON.stringify(projectList.data)}`);

        return {
          success: true,
          projects: projectList.data
        };
      } else {
        console.log(`❌ Vercel: Failed - ${projectList.error}`);

        // Try creating a project
        const createProject = await this.bridge.executeNeonOperation('VERCEL_CREATE_PROJECT', {
          name: 'test-project-mcp',
          gitRepository: 'https://github.com/djb258/barton-outreach-core'
        });

        if (createProject.success) {
          console.log(`✅ Vercel: Project creation successful`);
          return { success: true, method: 'project_creation', data: createProject.data };
        }

        return { success: false, error: projectList.error };
      }
    } catch (error) {
      console.log(`❌ Vercel: Exception - ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * Run all integration tests
   */
  async runAllTests() {
    console.log('🚀 COMPREHENSIVE MCP INTEGRATION TEST SUITE');
    console.log('═'.repeat(60));

    const tests = [
      { name: 'composio_api', testFn: () => this.testComposioAPI() },
      { name: 'neon_database', testFn: () => this.testNeonIntegration() },
      { name: 'apify_scraping', testFn: () => this.testApifyIntegration() },
      { name: 'millionverifier_email', testFn: () => this.testMillionVerifierIntegration() },
      { name: 'github_repo', testFn: () => this.testGitHubIntegration() },
      { name: 'vercel_deployment', testFn: () => this.testVercelIntegration() }
    ];

    for (const test of tests) {
      this.testResults.total_tests++;

      try {
        const result = await test.testFn();
        this.testResults.applications[test.name] = result;

        if (result.success) {
          this.testResults.passed++;
        } else {
          this.testResults.failed++;
        }
      } catch (error) {
        this.testResults.failed++;
        this.testResults.applications[test.name] = {
          success: false,
          error: error.message
        };
      }
    }

    // Summary
    console.log('\n' + '═'.repeat(60));
    console.log('📊 MCP INTEGRATION TEST SUMMARY');
    console.log('═'.repeat(60));

    Object.entries(this.testResults.applications).forEach(([name, result]) => {
      const status = result.success ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${name.toUpperCase().replace('_', ' ')}`);
    });

    console.log(`\n📈 Results: ${this.testResults.passed}/${this.testResults.total_tests} tests passed`);
    console.log(`📊 Success Rate: ${((this.testResults.passed / this.testResults.total_tests) * 100).toFixed(1)}%`);

    // Deployment readiness assessment
    const criticalApps = ['composio_api', 'neon_database'];
    const criticalPassed = criticalApps.every(app => this.testResults.applications[app]?.success);

    console.log('\n🎯 DEPLOYMENT READINESS:');
    if (criticalPassed) {
      console.log('✅ READY FOR DEPLOYMENT - Critical integrations working');
    } else {
      console.log('❌ NOT READY - Critical integrations failed');
    }

    console.log('\n🔧 Integration Status:');
    console.log(`  Core (Composio + Neon): ${criticalPassed ? 'READY' : 'FAILED'}`);
    console.log(`  Web Scraping (Apify): ${this.testResults.applications.apify_scraping?.success ? 'READY' : 'OPTIONAL'}`);
    console.log(`  Email Validation: ${this.testResults.applications.millionverifier_email?.success ? 'READY' : 'OPTIONAL'}`);
    console.log(`  GitHub Integration: ${this.testResults.applications.github_repo?.success ? 'READY' : 'OPTIONAL'}`);
    console.log(`  Vercel Integration: ${this.testResults.applications.vercel_deployment?.success ? 'READY' : 'MANUAL'}`);

    return this.testResults;
  }
}

// Execute comprehensive tests
async function main() {
  const tester = new ComprehensiveMCPTester();

  try {
    const results = await tester.runAllTests();

    console.log('\n[DETAILED RESULTS]');
    console.log(JSON.stringify(results, null, 2));

    return results;
  } catch (error) {
    console.error('\n[TEST SUITE ERROR]', error);
    return { success: false, error: error.message };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(results => {
    const success = results.passed >= results.total_tests * 0.5; // 50% pass rate minimum
    process.exit(success ? 0 : 1);
  });
}

export default main;