/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-EE825D28
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Add Doctrine Headers Script
 * Adds proper Barton Doctrine headers to all API files missing them
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Generate Barton ID based on file path and purpose
function generateBartonId(filePath) {
  const fileName = path.basename(filePath, path.extname(filePath));

  // Different categories have different ID ranges
  const categories = {
    // Core API files (01.xx.xx.xx.xxxxx.xxx)
    'hello': '01.01.01.07.10000.001',
    'test': '01.01.02.07.10000.002',
    'llm': '01.02.01.07.10000.003',
    'subagents': '01.02.02.07.10000.004',

    // IMO specific (02.xx.xx.xx.xxxxx.xxx)
    'manifest': '02.01.01.07.10000.005',
    'ssot': '02.01.02.07.10000.006',

    // Server/Infrastructure (03.xx.xx.xx.xxxxx.xxx)
    'server': '03.01.01.07.10000.007',
    'mcp-render-endpoint': '03.01.02.07.10000.008',
    'outreach-endpoints': '03.01.03.07.10000.009',

    // Attribution APIs (05.xx.xx.xx.xxxxx.xxx)
    'attribution-analytics': '05.01.01.07.10000.011',
    'attribution-ingest': '05.01.02.07.10000.012',
    'attribution-records': '05.01.03.07.10000.013',

    // Adjustment APIs (06.xx.xx.xx.xxxxx.xxx)
    'adjuster-fetch': '06.01.01.07.10000.014',
    'adjuster-save': '06.01.02.07.10000.015',

    // Data Processing APIs (07.xx.xx.xx.xxxxx.xxx)
    'apify-batch-processor': '07.01.01.07.10000.016',
    'enrich-companies': '07.01.02.07.10000.017',
    'enrich-people': '07.01.03.07.10000.018',

    // Dashboard APIs (09.xx.xx.xx.xxxxx.xxx)
    'dashboard-metrics': '09.01.01.07.10000.019',
    'dashboard-trends': '09.01.02.07.10000.020',

    // Audit APIs (10.xx.xx.xx.xxxxx.xxx)
    'audit-log': '10.01.01.07.10000.021'
  };

  // Try exact match first
  if (categories[fileName]) {
    return categories[fileName];
  }

  // Try partial matches
  for (const [key, id] of Object.entries(categories)) {
    if (fileName.includes(key)) {
      return id;
    }
  }

  // Generate dynamic ID for unknown files
  const hash = fileName.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);

  const sequence = Math.abs(hash % 99999).toString().padStart(5, '0');
  const checksum = Math.abs(hash % 999).toString().padStart(3, '0');

  return `99.99.99.07.${sequence}.${checksum}`;
}

// Generate input/output descriptions based on file analysis
function generateInputOutput(filePath, content) {
  const fileName = path.basename(filePath, path.extname(filePath));

  // Analyze content for clues
  const hasDatabase = content.includes('sql') || content.includes('database') || content.includes('query');
  const hasEmail = content.includes('email') || content.includes('send');
  const hasCampaign = content.includes('campaign');
  const hasAnalytics = content.includes('analytics') || content.includes('metrics');

  const descriptions = {
    'hello': {
      input: 'HTTP request (health check)',
      output: 'service status and version'
    },
    'test': {
      input: 'test parameters and configuration',
      output: 'test results and validation status'
    },
    'llm': {
      input: 'LLM prompt and model configuration',
      output: 'AI-generated response and metadata'
    },
    'subagents': {
      input: 'agent task definition and parameters',
      output: 'agent execution results and status'
    },
    'manifest': {
      input: 'manifest ID and request parameters',
      output: 'IMO manifest configuration data'
    },
    'ssot': {
      input: 'SSOT data and save parameters',
      output: 'save confirmation and data integrity status'
    },
    'server': {
      input: 'server requests and API calls',
      output: 'processed responses and routing data'
    },
    'mcp-render-endpoint': {
      input: 'MCP render request and template data',
      output: 'rendered output and execution status'
    },
    'outreach-endpoints': {
      input: 'outreach API requests and parameters',
      output: 'outreach operation results'
    },
    'attribution-analytics': {
      input: 'attribution query parameters and filters',
      output: 'attribution analytics and performance data'
    },
    'attribution-ingest': {
      input: 'raw attribution data and source information',
      output: 'processed attribution records'
    },
    'attribution-records': {
      input: 'attribution record filter parameters',
      output: 'attribution record list and metadata'
    },
    'adjuster-fetch': {
      input: 'adjustment query parameters and filters',
      output: 'failed records requiring human adjustment'
    },
    'adjuster-save': {
      input: 'adjusted record data and validation',
      output: 'save confirmation and promotion status'
    },
    'apify-batch-processor': {
      input: 'Apify batch job configuration and data',
      output: 'batch processing results and status'
    },
    'enrich-companies': {
      input: 'company IDs and enrichment parameters',
      output: 'enriched company data and validation'
    },
    'enrich-people': {
      input: 'people IDs and enrichment parameters',
      output: 'enriched people data and validation'
    },
    'dashboard-metrics': {
      input: 'metrics query parameters and date range',
      output: 'dashboard metrics and KPI data'
    },
    'dashboard-trends': {
      input: 'trend analysis parameters and filters',
      output: 'trend data and visualization metrics'
    },
    'audit-log': {
      input: 'audit log query and filter parameters',
      output: 'audit trail records and compliance data'
    }
  };

  // Try exact match first
  if (descriptions[fileName]) {
    return descriptions[fileName];
  }

  // Generate based on content analysis
  let input = 'API request parameters';
  let output = 'API response data';

  if (hasDatabase && hasAnalytics) {
    input = 'analytics query parameters and filters';
    output = 'analytics data and metrics';
  } else if (hasDatabase) {
    input = 'data query parameters and filters';
    output = 'database records and metadata';
  } else if (hasCampaign) {
    input = 'campaign configuration and parameters';
    output = 'campaign execution results';
  } else if (hasEmail) {
    input = 'email parameters and recipient data';
    output = 'email sending status and tracking';
  }

  return { input, output };
}

// Generate full Doctrine header
function generateDoctrineHeader(filePath, content) {
  const bartonId = generateBartonId(filePath);
  const { input, output } = generateInputOutput(filePath, content);

  return `/**
 * Doctrine Spec:
 * - Barton ID: 03.01.04
 * - Altitude: 10000 (Execution Layer)
 * - Input: ${input}
 * - Output: ${output}
 * - MCP: Composio (Neon integrated)
 */`;
}

// Check if file already has Doctrine header
function hasDoctrineHeader(content) {
  return content.includes('Doctrine Spec:') && content.includes('Barton ID:03.01.04
}

// Process a single file
function processFile(filePath) {
  console.log(`📄 Processing ${filePath}...`);

  if (!fs.existsSync(filePath)) {
    console.log(`  ⚠️  File not found: ${filePath}`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  // Skip if already has Doctrine header
  if (hasDoctrineHeader(content)) {
    console.log(`  ✓ Already has Doctrine header`);
    return;
  }

  // Generate and add Doctrine header
  const doctrineHeader = generateDoctrineHeader(filePath, content);
  content = doctrineHeader + '\n' + content;

  // Backup original file
  const backupPath = filePath.replace(/\.(ts|js)$/, '-before-doctrine.$1');
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(filePath, backupPath);
  }

  // Write updated content
  fs.writeFileSync(filePath, content);
  console.log(`  ✅ Added Doctrine header`);
}

// Find all API files recursively
function findApiFiles(dir, files = []) {
  if (!fs.existsSync(dir)) return files;

  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Skip node_modules and .git
      if (!['node_modules', '.git', '.github'].includes(item)) {
        findApiFiles(fullPath, files);
      }
    } else if (stat.isFile()) {
      // Include TypeScript and JavaScript files in api directories
      if ((fullPath.includes('/api/') || fullPath.includes('\\api\\')) &&
          (fullPath.endsWith('.ts') || fullPath.endsWith('.js')) &&
          !fullPath.includes('node_modules') &&
          !fullPath.includes('-original') &&
          !fullPath.includes('-before-doctrine')) {
        files.push(fullPath);
      }
    }
  }

  return files;
}

// Main execution
function main() {
  console.log('🚀 Adding Doctrine headers to API files...\n');

  const apiFiles = findApiFiles(process.cwd());
  console.log(`Found ${apiFiles.length} API files to process\n`);

  let processed = 0;
  let skipped = 0;
  let added = 0;

  for (const file of apiFiles) {
    const beforeContent = fs.readFileSync(file, 'utf8');
    const hadHeader = hasDoctrineHeader(beforeContent);

    processFile(file);
    processed++;

    if (hadHeader) {
      skipped++;
    } else {
      added++;
    }
  }

  console.log('\n✅ Doctrine header addition complete!');
  console.log(`📊 Summary:`);
  console.log(`  - Total files processed: ${processed}`);
  console.log(`  - Headers added: ${added}`);
  console.log(`  - Already had headers: ${skipped}`);
  console.log(`\n🔍 Next: Run Barton Doctrine validator to verify compliance`);
}

// Run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}