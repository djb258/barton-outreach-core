#!/usr/bin/env node

const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

class Step2CDeploymentVerifier {
  constructor() {
    this.functions = ['scrapeCompany', 'scrapePerson'];
    this.deploymentSession = `deploy-step2c-${Date.now()}`;

    console.log('🚀 Step 2C Deployment Verifier');
    console.log(`🔍 Session: ${this.deploymentSession}\n`);
  }

  async verifyAndDeploy() {
    try {
      console.log('📋 Step 1: Checking Firebase CLI setup...');
      await this.checkFirebaseSetup();

      console.log('📋 Step 2: Validating function code...');
      await this.validateFunctionCode();

      console.log('📋 Step 3: Deploying Step 2C functions...');
      await this.deployFunctions();

      console.log('📋 Step 4: Verifying deployment...');
      await this.verifyDeployment();

      console.log('\n🎉 Step 2C deployment completed successfully!');

    } catch (error) {
      console.error('\n❌ Deployment failed:', error.message);
      process.exit(1);
    }
  }

  async checkFirebaseSetup() {
    try {
      const { stdout } = await execAsync('firebase --version');
      console.log(`✅ Firebase CLI: ${stdout.trim()}`);

      const { stdout: project } = await execAsync('firebase use');
      console.log(`✅ Project: ${project.trim()}`);

    } catch (error) {
      throw new Error(`Firebase CLI not setup: ${error.message}`);
    }
  }

  async validateFunctionCode() {
    const fs = require('fs');
    const path = require('path');

    const scrapingOpsPath = path.join(__dirname, 'functions', 'scrapingOperations.js');
    const mcpEndpointsPath = path.join(__dirname, 'scraping-mcp-endpoints.js');

    try {
      if (!fs.existsSync(scrapingOpsPath)) {
        throw new Error('scrapingOperations.js not found');
      }

      if (!fs.existsSync(mcpEndpointsPath)) {
        throw new Error('scraping-mcp-endpoints.js not found');
      }

      console.log('✅ Function files exist');

      // Basic syntax check
      const scrapingCode = fs.readFileSync(scrapingOpsPath, 'utf8');
      if (!scrapingCode.includes('export const scrapeCompany') ||
          !scrapingCode.includes('export const scrapePerson')) {
        throw new Error('Required exports not found in scrapingOperations.js');
      }

      console.log('✅ Function exports validated');

    } catch (error) {
      throw new Error(`Code validation failed: ${error.message}`);
    }
  }

  async deployFunctions() {
    try {
      console.log('🚀 Deploying scrapeCompany function...');
      const { stdout: deploy1 } = await execAsync('firebase deploy --only functions:scrapeCompany', {
        cwd: __dirname,
        timeout: 300000 // 5 minutes
      });

      console.log('🚀 Deploying scrapePerson function...');
      const { stdout: deploy2 } = await execAsync('firebase deploy --only functions:scrapePerson', {
        cwd: __dirname,
        timeout: 300000 // 5 minutes
      });

      console.log('✅ Functions deployed successfully');

    } catch (error) {
      // Try deploying all functions if individual deployment fails
      try {
        console.log('🔄 Attempting bulk deployment...');
        await execAsync('firebase deploy --only functions', {
          cwd: __dirname,
          timeout: 600000 // 10 minutes
        });
        console.log('✅ Bulk deployment successful');
      } catch (bulkError) {
        throw new Error(`Deployment failed: ${error.message}`);
      }
    }
  }

  async verifyDeployment() {
    try {
      const { stdout } = await execAsync('firebase functions:list');
      const deployedFunctions = stdout;

      for (const func of this.functions) {
        if (deployedFunctions.includes(func)) {
          console.log(`✅ ${func} deployed`);
        } else {
          throw new Error(`${func} not found in deployed functions`);
        }
      }

      console.log('✅ All Step 2C functions verified');

    } catch (error) {
      throw new Error(`Verification failed: ${error.message}`);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const verifier = new Step2CDeploymentVerifier();
  verifier.verifyAndDeploy().catch(console.error);
}

module.exports = Step2CDeploymentVerifier;