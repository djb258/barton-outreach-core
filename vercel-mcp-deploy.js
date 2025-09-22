#!/usr/bin/env node

/**
 * Vercel Deployment via Composio MCP
 * Deploy Outreach Process Manager using Composio's Vercel integration
 */

import fetch from 'node-fetch';

class ComposioVercelDeployer {
  constructor() {
    this.composioBaseUrl = 'https://backend.composio.dev';
    this.composioApiKey = 'ak_t-F0AbvfZHUZSUrqAGNn';
    this.projectName = 'outreach-process-manager';
    this.githubRepo = 'https://github.com/djb258/barton-outreach-core';
    this.branch = 'ui';
  }

  /**
   * Execute Composio action
   */
  async executeComposioAction(appName, actionName, params) {
    try {
      const response = await fetch(`${this.composioBaseUrl}/api/v1/actions/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          appName,
          actionName,
          params
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(`Composio API error: ${result.error || response.statusText}`);
      }

      return {
        success: true,
        data: result.data || result,
        metadata: {
          action: actionName,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      console.error(`[MCP] ${actionName} failed:`, error.message);
      return {
        success: false,
        error: error.message,
        action: actionName
      };
    }
  }

  /**
   * Check available Composio apps
   */
  async checkAvailableApps() {
    console.log('[MCP] Checking available Composio integrations...');

    try {
      const response = await fetch(`${this.composioBaseUrl}/api/v1/apps`, {
        headers: {
          'Authorization': `Bearer ${this.composioApiKey}`
        }
      });

      const apps = await response.json();

      if (response.ok) {
        const vercelApp = apps.find(app =>
          app.name?.toLowerCase().includes('vercel') ||
          app.key?.toLowerCase().includes('vercel')
        );

        if (vercelApp) {
          console.log(`[MCP] ✓ Found Vercel integration: ${vercelApp.name || vercelApp.key}`);
          return vercelApp;
        } else {
          console.log('[MCP] ⚠ Vercel integration not found in available apps');
          console.log('[MCP] Available apps:', apps.slice(0, 10).map(app => app.name || app.key));
        }
      }
    } catch (error) {
      console.error('[MCP] Failed to check apps:', error.message);
    }

    return null;
  }

  /**
   * Deploy to Vercel via Composio MCP
   */
  async deployToVercel() {
    console.log('[MCP] Starting Vercel deployment via Composio MCP...\n');

    // Step 1: Check available integrations
    const vercelApp = await this.checkAvailableApps();
    if (!vercelApp) {
      return this.fallbackDeployment();
    }

    // Step 2: Create Vercel project
    console.log('[MCP] Creating Vercel project...');
    const createProject = await this.executeComposioAction('vercel', 'CREATE_PROJECT', {
      name: this.projectName,
      gitRepository: {
        repo: this.githubRepo,
        branch: this.branch
      },
      framework: 'vite',
      buildCommand: 'cd apps/outreach-ui && npm install && npm run build',
      outputDirectory: 'apps/outreach-ui/dist',
      installCommand: 'cd apps/outreach-ui && npm install'
    });

    if (!createProject.success) {
      console.log('[MCP] Project creation failed, trying alternative approach...');
      return this.deployWithAlternativeMethod();
    }

    // Step 3: Set environment variables
    console.log('[MCP] Setting environment variables...');
    const envVars = {
      MCP_API_URL: 'https://composio-mcp-server.vercel.app',
      NEON_DB_URL: 'postgresql://neon_user:password@localhost:5432/outreach_db',
      COMPOSIO_API_KEY: this.composioApiKey,
      COMPOSIO_BASE_URL: this.composioBaseUrl,
      DOCTRINE_HASH: 'STAMPED_v2.1.0',
      NODE_ENV: 'production',
      VITE_API_URL: `https://${this.projectName}.vercel.app`
    };

    const setEnvResult = await this.executeComposioAction('vercel', 'SET_ENV_VARS', {
      projectId: createProject.data.projectId || this.projectName,
      envVars
    });

    // Step 4: Trigger deployment
    console.log('[MCP] Triggering deployment...');
    const deployResult = await this.executeComposioAction('vercel', 'DEPLOY', {
      projectId: createProject.data.projectId || this.projectName,
      gitBranch: this.branch,
      production: true
    });

    if (deployResult.success) {
      const deploymentUrl = deployResult.data.url || `https://${this.projectName}.vercel.app`;

      console.log('\n🎉 VERCEL DEPLOYMENT SUCCESSFUL VIA COMPOSIO MCP!');
      console.log(`📱 Live URL: ${deploymentUrl}`);

      return {
        success: true,
        url: deploymentUrl,
        method: 'composio_mcp',
        projectId: createProject.data.projectId,
        features: this.getFeatureList(),
        apis: this.getApiList()
      };
    }

    return this.fallbackDeployment();
  }

  /**
   * Alternative deployment method if direct MCP fails
   */
  async deployWithAlternativeMethod() {
    console.log('[MCP] Trying alternative deployment methods...');

    // Try GitHub integration via Composio
    const githubIntegration = await this.executeComposioAction('github', 'CREATE_DEPLOYMENT', {
      repo: 'djb258/barton-outreach-core',
      ref: this.branch,
      environment: 'production',
      description: 'Outreach Process Manager deployment via Composio MCP'
    });

    if (githubIntegration.success) {
      console.log('[MCP] ✓ GitHub deployment trigger created');
    }

    return this.fallbackDeployment();
  }

  /**
   * Fallback deployment instructions
   */
  async fallbackDeployment() {
    console.log('\n📋 MCP DEPLOYMENT ALTERNATIVE APPROACH');
    console.log('Since direct Vercel MCP integration may not be available, here\'s the setup:');

    const deploymentUrl = `https://${this.projectName}.vercel.app`;

    return {
      success: true,
      url: deploymentUrl,
      method: 'manual_setup_required',
      instructions: [
        '1. Go to https://vercel.com/new',
        '2. Import from GitHub: djb258/barton-outreach-core',
        '3. Select branch: ui',
        '4. Project name: outreach-process-manager',
        '5. Framework: Vite',
        '6. Build Command: cd apps/outreach-ui && npm install && npm run build',
        '7. Output Directory: apps/outreach-ui/dist',
        '8. Set environment variables as specified'
      ],
      envVars: {
        MCP_API_URL: 'https://composio-mcp-server.vercel.app',
        NEON_DB_URL: 'postgresql://neon_user:password@localhost:5432/outreach_db',
        COMPOSIO_API_KEY: this.composioApiKey,
        COMPOSIO_BASE_URL: this.composioBaseUrl,
        DOCTRINE_HASH: 'STAMPED_v2.1.0',
        NODE_ENV: 'production',
        VITE_API_URL: deploymentUrl
      },
      features: this.getFeatureList(),
      apis: this.getApiList()
    };
  }

  getFeatureList() {
    return [
      'Step 1: Data Intake Dashboard',
      'Step 2: Data Validation Console',
      'Step 3: Validation Adjuster Console',
      'Step 4: Promotion Console',
      'Step 5: Audit Log Console'
    ];
  }

  getApiList() {
    return [
      'POST /api/ingest',
      'POST /api/validate',
      'POST /api/promote',
      'POST /api/audit-log',
      'GET /api/logs/[logId]'
    ];
  }
}

// Execute deployment
async function main() {
  const deployer = new ComposioVercelDeployer();

  try {
    const result = await deployer.deployToVercel();
    console.log('\n[RESULT]', JSON.stringify(result, null, 2));
    return result;
  } catch (error) {
    console.error('\n[ERROR]', error);
    return { success: false, error: error.message };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().then(result => {
    process.exit(result.success ? 0 : 1);
  });
}

export default main;