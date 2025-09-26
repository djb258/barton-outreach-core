#!/usr/bin/env node

/**
 * Barton Doctrine MCP Compliance Fix Script
 * Automatically fixes direct Neon imports and adds Doctrine headers
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Files with direct Neon violations that need fixing
const VIOLATION_FILES = [
  'apps/outreach-process-manager/api/bit-signals-list.ts',
  'apps/outreach-process-manager/api/campaign-auto-create.ts',
  'apps/outreach-process-manager/api/campaign-launch.ts',
  'apps/outreach-process-manager/api/campaign-list.ts',
  'apps/outreach-process-manager/api/campaign-stats.ts',
  'apps/outreach-process-manager/api/optimization-history.ts',
  'apps/outreach-process-manager/api/top-leads.ts'
];

// Generate appropriate Barton IDs for different API types
function generateBartonId(fileName) {
  const baseIds = {
    'campaign-auto-create': '08.05.01.07.10000.004',
    'campaign-launch': '08.05.02.07.10000.005',
    'campaign-list': '08.05.03.07.10000.006',
    'campaign-stats': '08.05.04.07.10000.007',
    'bit-signals-list': '08.04.03.07.10000.008',
    'optimization-history': '08.04.04.07.10000.009',
    'top-leads': '08.04.05.07.10000.010'
  };

  const baseName = path.basename(fileName, '.ts');
  return baseIds[baseName] || '08.09.99.07.10000.999';
}

// Generate Doctrine header for API file
function generateDoctrineHeader(fileName) {
  const bartonId = generateBartonId(fileName);
  const baseName = path.basename(fileName, '.ts');

  const descriptions = {
    'campaign-auto-create': {
      input: 'campaign trigger event and target data',
      output: 'automated campaign configuration and launch status'
    },
    'campaign-launch': {
      input: 'campaign configuration and recipient list',
      output: 'campaign execution status and tracking data'
    },
    'campaign-list': {
      input: 'campaign filter and pagination parameters',
      output: 'campaign list with status and metrics'
    },
    'campaign-stats': {
      input: 'campaign ID and date range parameters',
      output: 'campaign performance analytics and metrics'
    },
    'bit-signals-list': {
      input: 'signal filter and pagination parameters',
      output: 'BIT signal list with weights and status'
    },
    'optimization-history': {
      input: 'optimization filter and date range',
      output: 'optimization history with performance data'
    },
    'top-leads': {
      input: 'lead filtering and ranking parameters',
      output: 'ranked lead list with scoring data'
    }
  };

  const desc = descriptions[baseName] || {
    input: 'API request parameters',
    output: 'API response data'
  };

  return `/**
 * Doctrine Spec:
 * - Barton ID: ${bartonId}
 * - Altitude: 10000 (Execution Layer)
 * - Input: ${desc.input}
 * - Output: ${desc.output}
 * - MCP: Composio (Neon integrated)
 */`;
}

// Fix direct Neon import to use MCP
function fixNeonImport(content) {
  // Replace direct Neon import with MCP bridge
  const neonImportRegex = /import\s*{\s*neon\s*}\s*from\s*['"]@neondatabase\/serverless['"];?\s*/g;
  const sqlInitRegex = /const\s+sql\s*=\s*neon\([^)]+\);?\s*/g;

  let fixed = content.replace(neonImportRegex, '');
  fixed = fixed.replace(sqlInitRegex, '');

  // Add MCP import at the top
  const importRegex = /(import\s+type.*?from.*?['"];?\s*)/;
  fixed = fixed.replace(importRegex, `$1import ComposioNeonBridge from './lib/composio-neon-bridge.js';\n`);

  return fixed;
}

// Add MCP initialization to handler function
function addMcpInitialization(content) {
  // Find the try block and add MCP initialization
  const tryBlockRegex = /(try\s*{)/;
  const mcpInit = `$1
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();
`;

  return content.replace(tryBlockRegex, mcpInit);
}

// Replace direct SQL queries with MCP calls
function replaceSqlQueries(content) {
  // Replace sql`` template literals with MCP calls
  let fixed = content;

  // Pattern for sql`` queries
  const sqlQueryRegex = /await\s+sql`([^`]+)`/g;

  fixed = fixed.replace(sqlQueryRegex, (match, query) => {
    // Clean up the query
    const cleanQuery = query.trim();

    // Determine if it's a read or write operation
    const isWrite = /^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)/i.test(cleanQuery);
    const mode = isWrite ? 'write' : 'read';

    return `await mcpBridge.executeNeonOperation('${isWrite ? 'EXECUTE_SQL' : 'QUERY_ROWS'}', {
      sql: \`${cleanQuery}\`,
      mode: '${mode}'
    })`;
  });

  // Replace direct sql() calls
  const sqlCallRegex = /await\s+sql\(([^)]+)\)/g;
  fixed = fixed.replace(sqlCallRegex, (match, query) => {
    return `await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: ${query},
      mode: 'write'
    })`;
  });

  return fixed;
}

// Update result handling for MCP responses
function updateResultHandling(content) {
  // Need to update how results are accessed since MCP returns { success, data }
  let fixed = content;

  // Common patterns that need updating
  const patterns = [
    // result[0] becomes result.data.rows[0]
    {
      search: /(\w+)\[0\]/g,
      replace: (match, varName) => {
        // Only replace if it looks like a DB result variable
        if (['result', 'results', 'rows', 'data', 'queryResult', 'insertResult', 'updateResult'].includes(varName)) {
          return `${varName}.data.rows[0]`;
        }
        return match;
      }
    },
    // result.length becomes result.data.rows.length
    {
      search: /(\w+)\.length/g,
      replace: (match, varName) => {
        if (['result', 'results', 'rows', 'data', 'queryResult'].includes(varName)) {
          return `${varName}.data.rows.length`;
        }
        return match;
      }
    }
  ];

  patterns.forEach(pattern => {
    if (typeof pattern.replace === 'function') {
      fixed = fixed.replace(pattern.search, pattern.replace);
    } else {
      fixed = fixed.replace(pattern.search, pattern.replace);
    }
  });

  return fixed;
}

// Add error handling for MCP calls
function addMcpErrorHandling(content) {
  // Add checks for MCP success
  let fixed = content;

  // Add success checks after MCP calls
  const mcpCallRegex = /(const\s+\w+\s*=\s*await\s+mcpBridge\.executeNeonOperation[^;]+;)/g;

  fixed = fixed.replace(mcpCallRegex, (match) => {
    const varName = match.match(/const\s+(\w+)\s*=/)?.[1] || 'result';
    return `${match}

    if (!${varName}.success) {
      throw new Error(\`MCP operation failed: \${${varName}.error}\`);
    }`;
  });

  return fixed;
}

// Main fix function for a single file
function fixFile(filePath) {
  console.log(`🔧 Fixing ${filePath}...`);

  if (!fs.existsSync(filePath)) {
    console.log(`  ⚠️  File not found: ${filePath}`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  // Step 1: Add Doctrine header if missing
  if (!content.includes('Doctrine Spec:')) {
    const doctrineHeader = generateDoctrineHeader(filePath);
    content = doctrineHeader + '\n' + content;
  }

  // Step 2: Fix Neon import
  content = fixNeonImport(content);

  // Step 3: Add MCP initialization
  content = addMcpInitialization(content);

  // Step 4: Replace SQL queries with MCP calls
  content = replaceSqlQueries(content);

  // Step 5: Update result handling
  content = updateResultHandling(content);

  // Step 6: Add MCP error handling
  content = addMcpErrorHandling(content);

  // Step 7: Update error messages to mention MCP
  content = content.replace(/console\.error\('\[([^\]]+)\] Error:/g, "console.error('[MCP $1] Error:");

  // Backup original file
  const backupPath = filePath.replace('.ts', '-original.ts');
  if (!fs.existsSync(backupPath)) {
    fs.copyFileSync(filePath, backupPath);
  }

  // Write fixed content
  fs.writeFileSync(filePath, content);
  console.log(`  ✅ Fixed ${filePath}`);
}

// Main execution
function main() {
  console.log('🚀 Starting Barton Doctrine MCP Compliance Fix...\n');

  VIOLATION_FILES.forEach(file => {
    const fullPath = path.join(process.cwd(), file);
    fixFile(fullPath);
  });

  console.log('\n✅ All MCP violations fixed!');
  console.log('\n📋 Next steps:');
  console.log('1. Review the fixed files');
  console.log('2. Test the APIs');
  console.log('3. Run the Barton Doctrine validator');
}

// Run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}