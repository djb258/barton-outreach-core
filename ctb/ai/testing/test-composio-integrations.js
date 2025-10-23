/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/testing
Barton ID: 03.01.03
Unique ID: CTB-24B62C3C
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Test Composio MCP Integrations
 * Check available integrations: Vercel, Apify, Neon, etc.
 */

import ComposioNeonBridge from './apps/outreach-process-manager/api/lib/composio-neon-bridge.js';

class ComposioIntegrationTester {
  constructor() {
    this.bridge = new ComposioNeonBridge();
    this.composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
    this.composioBaseUrl = 'https://backend.composio.dev';
  }

  /**
   * Test direct Composio API call
   */
  async testComposioAPI(endpoint, method = 'GET', body = null) {
    try {
      const options = {
        method,
        headers: {
          'Authorization': `Bearer ${this.composioApiKey}`,
          'Content-Type': 'application/json'
        }
      };

      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(`${this.composioBaseUrl}${endpoint}`, options);
      const data = await response.json();

      return {
        success: response.ok,
        status: response.status,
        data,
        endpoint
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        endpoint
      };
    }
  }

  /**
   * Test Apify integration
   */
  async testApifyIntegration() {
    console.log('[COMPOSIO] Testing Apify integration...');

    // Test 1: Check if Apify app exists
    const apifyAppTest = await this.testComposioAPI('/api/v1/apps');
    if (apifyAppTest.success) {
      const apifyApp = apifyAppTest.data.find(app =>
        app.name?.toLowerCase().includes('apify') ||
        app.key?.toLowerCase().includes('apify')
      );

      if (apifyApp) {
        console.log(`[COMPOSIO] ✓ Found Apify app: ${apifyApp.name || apifyApp.key}`);

        // Test 2: Try Apify action
        const apifyActionTest = await this.bridge.executeNeonOperation('APIFY_RUN_ACTOR', {
          actor_id: 'apify/web-scraper',
          input: {
            urls: ['https://example.com'],
            maxRequestsPerCrawl: 1
          }
        });

        if (apifyActionTest.success) {
          console.log('[COMPOSIO] ✓ Apify integration working');
          return { integration: 'apify', status: 'working', details: apifyActionTest };
        } else {
          console.log('[COMPOSIO] ⚠ Apify app found but action failed:', apifyActionTest.error);
          return { integration: 'apify', status: 'found_but_failed', error: apifyActionTest.error };
        }
      } else {
        console.log('[COMPOSIO] ✗ Apify app not found');
        return { integration: 'apify', status: 'not_found' };
      }
    } else {
      console.log('[COMPOSIO] ✗ Could not check apps:', apifyAppTest.error);
      return { integration: 'apify', status: 'api_error', error: apifyAppTest.error };
    }
  }

  /**
   * Test Vercel integration
   */
  async testVercelIntegration() {
    console.log('[COMPOSIO] Testing Vercel integration...');

    const vercelAppTest = await this.testComposioAPI('/api/v1/apps');
    if (vercelAppTest.success) {
      const vercelApp = vercelAppTest.data.find(app =>
        app.name?.toLowerCase().includes('vercel') ||
        app.key?.toLowerCase().includes('vercel')
      );

      if (vercelApp) {
        console.log(`[COMPOSIO] ✓ Found Vercel app: ${vercelApp.name || vercelApp.key}`);

        // Test Vercel actions
        const vercelActionTest = await this.bridge.executeNeonOperation('VERCEL_LIST_PROJECTS', {});

        if (vercelActionTest.success) {
          console.log('[COMPOSIO] ✓ Vercel integration working');
          return { integration: 'vercel', status: 'working', details: vercelActionTest };
        } else {
          console.log('[COMPOSIO] ⚠ Vercel app found but action failed:', vercelActionTest.error);
          return { integration: 'vercel', status: 'found_but_failed', error: vercelActionTest.error };
        }
      } else {
        console.log('[COMPOSIO] ✗ Vercel app not found');
        return { integration: 'vercel', status: 'not_found' };
      }
    } else {
      console.log('[COMPOSIO] ✗ Could not check apps:', vercelAppTest.error);
      return { integration: 'vercel', status: 'api_error', error: vercelAppTest.error };
    }
  }

  /**
   * Test Neon integration
   */
  async testNeonIntegration() {
    console.log('[COMPOSIO] Testing Neon integration...');

    const neonTest = await this.bridge.executeNeonOperation('QUERY_ROWS', {
      sql: 'SELECT 1 as test_connection',
      mode: 'read'
    });

    if (neonTest.success) {
      console.log('[COMPOSIO] ✓ Neon integration working');
      return { integration: 'neon', status: 'working', details: neonTest };
    } else {
      console.log('[COMPOSIO] ⚠ Neon integration failed:', neonTest.error);
      return { integration: 'neon', status: 'failed', error: neonTest.error };
    }
  }

  /**
   * Test GitHub integration
   */
  async testGitHubIntegration() {
    console.log('[COMPOSIO] Testing GitHub integration...');

    const githubTest = await this.bridge.executeNeonOperation('GITHUB_GET_REPO', {
      owner: 'djb258',
      repo: 'barton-outreach-core'
    });

    if (githubTest.success) {
      console.log('[COMPOSIO] ✓ GitHub integration working');
      return { integration: 'github', status: 'working', details: githubTest };
    } else {
      console.log('[COMPOSIO] ⚠ GitHub integration failed:', githubTest.error);
      return { integration: 'github', status: 'failed', error: githubTest.error };
    }
  }

  /**
   * Test all integrations
   */
  async testAllIntegrations() {
    console.log('🔍 TESTING COMPOSIO MCP INTEGRATIONS\n');

    const results = {
      timestamp: new Date().toISOString(),
      composio_api_key: this.composioApiKey.substring(0, 8) + '...',
      integration_tests: {}
    };

    // Test each integration
    const integrations = [
      { name: 'neon', testFn: () => this.testNeonIntegration() },
      { name: 'apify', testFn: () => this.testApifyIntegration() },
      { name: 'vercel', testFn: () => this.testVercelIntegration() },
      { name: 'github', testFn: () => this.testGitHubIntegration() }
    ];

    for (const integration of integrations) {
      try {
        console.log(`\n--- Testing ${integration.name.toUpperCase()} ---`);
        const result = await integration.testFn();
        results.integration_tests[integration.name] = result;
        console.log(`Result: ${result.status}`);
      } catch (error) {
        console.log(`Error testing ${integration.name}:`, error.message);
        results.integration_tests[integration.name] = {
          integration: integration.name,
          status: 'error',
          error: error.message
        };
      }
    }

    // Summary
    console.log('\n═══════════════════════════════════════');
    console.log('📊 INTEGRATION TEST SUMMARY');
    console.log('═══════════════════════════════════════');

    Object.entries(results.integration_tests).forEach(([name, result]) => {
      const status = result.status === 'working' ? '✅' :
                    result.status === 'found_but_failed' ? '⚠️' :
                    result.status === 'not_found' ? '❌' : '🔴';
      console.log(`${status} ${name.toUpperCase()}: ${result.status}`);
    });

    // Deployment recommendations
    console.log('\n🚀 DEPLOYMENT RECOMMENDATIONS:');

    const workingIntegrations = Object.values(results.integration_tests)
      .filter(r => r.status === 'working')
      .map(r => r.integration);

    if (workingIntegrations.includes('vercel')) {
      console.log('✅ Deploy directly via Composio → Vercel MCP');
    } else if (workingIntegrations.includes('github')) {
      console.log('✅ Deploy via Composio → GitHub → Vercel webhook');
    } else {
      console.log('⚠️ Manual deployment required (MCP integrations limited)');
    }

    return results;
  }
}

// Execute tests
async function main() {
  const tester = new ComposioIntegrationTester();

  try {
    const results = await tester.testAllIntegrations();
    console.log('\n[DETAILED RESULTS]');
    console.log(JSON.stringify(results, null, 2));
    return results;
  } catch (error) {
    console.error('\n[TEST ERROR]', error);
    return { success: false, error: error.message };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(results => {
    const hasWorkingIntegrations = Object.values(results.integration_tests || {})
      .some(r => r.status === 'working');
    process.exit(hasWorkingIntegrations ? 0 : 1);
  });
}

export default main;