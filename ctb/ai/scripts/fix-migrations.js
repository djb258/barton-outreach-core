/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-B685626E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

#!/usr/bin/env node

/**
 * Fix Migration Files Script
 * Adds Barton ID columns and audit compliance to SQL migration files
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Check if SQL file creates tables
function createsTables(content) {
  return /CREATE\s+TABLE/i.test(content);
}

// Check if table already has Barton ID column
function hasBartonIdColumn(content) {
  return /unique_id|barton_id/i.test(content);
}

// Check if table has audit columns
function hasAuditColumns(content) {
  return /created_at.*updated_at|updated_at.*created_at/i.test(content);
}

// Add Barton ID column to CREATE TABLE statements
function addBartonIdColumn(content) {
  // Find CREATE TABLE statements and add unique_id column
  const createTableRegex = /CREATE\s+TABLE\s+[^(]+\s*\(([^;]+)\);/gi;

  return content.replace(createTableRegex, (match) => {
    // Check if already has unique_id
    if (/unique_id|barton_id/i.test(match)) {
      return match;
    }

    // Add unique_id as first column
    const tableMatch = match.match(/CREATE\s+TABLE\s+([^(]+)\s*\(([^;]+)\);/i);
    if (tableMatch) {
      const tableName = tableMatch[1].trim();
      const columns = tableMatch[2].trim();

      const newColumns = `
    unique_id VARCHAR(23) PRIMARY KEY DEFAULT generate_barton_id(),
    ${columns}`;

      return `CREATE TABLE ${tableName} (${newColumns});`;
    }

    return match;
  });
}

// Add audit columns to CREATE TABLE statements
function addAuditColumns(content) {
  const createTableRegex = /CREATE\s+TABLE\s+[^(]+\s*\(([^;]+)\);/gi;

  return content.replace(createTableRegex, (match) => {
    // Check if already has audit columns
    if (/created_at.*updated_at|updated_at.*created_at/i.test(match)) {
      return match;
    }

    // Add audit columns before the closing parenthesis
    const tableMatch = match.match(/CREATE\s+TABLE\s+([^(]+)\s*\(([^;]+)\);/i);
    if (tableMatch) {
      const tableName = tableMatch[1].trim();
      const columns = tableMatch[2].trim();

      // Add audit columns
      const auditColumns = `,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()`;

      const newColumns = columns + auditColumns;
      return `CREATE TABLE ${tableName} (${newColumns});`;
    }

    return match;
  });
}

// Add Barton ID generator function if not present
function addBartonIdGenerator(content) {
  if (content.includes('generate_barton_id')) {
    return content;
  }

  const generatorFunction = `
-- Barton ID Generator Function
-- Generates format: NN.NN.NN.NN.NNNNN.NNN
CREATE OR REPLACE FUNCTION generate_barton_id()
RETURNS VARCHAR(23) AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
BEGIN
    -- Use timestamp and random for uniqueness
    segment1 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment2 := LPAD((EXTRACT(MICROSECONDS FROM NOW()) % 100)::TEXT, 2, '0');
    segment3 := LPAD((RANDOM() * 100)::INT::TEXT, 2, '0');
    segment4 := '07'; -- Fixed segment for database records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

`;

  return generatorFunction + content;
}

// Add trigger for updated_at if tables have audit columns
function addUpdatedAtTrigger(content) {
  if (content.includes('trigger_updated_at')) {
    return content;
  }

  const triggerFunction = `
-- Updated At Trigger Function
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

`;

  // Add triggers for any tables that have updated_at column
  const tableRegex = /CREATE\s+TABLE\s+([^\s(]+)/gi;
  let triggers = '';
  let match;

  while ((match = tableRegex.exec(content)) !== null) {
    const tableName = match[1];
    if (content.includes('updated_at')) {
      triggers += `
-- Trigger for ${tableName}
CREATE TRIGGER trigger_${tableName.replace(/[^a-zA-Z0-9_]/g, '_')}_updated_at
    BEFORE UPDATE ON ${tableName}
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();
`;
    }
  }

  return triggerFunction + content + triggers;
}

// Add doctrine comment header to SQL file
function addSqlDoctrineHeader(content, filePath) {
  if (content.includes('-- Barton Doctrine')) {
    return content;
  }

  const fileName = path.basename(filePath, '.sql');
  const header = `-- Barton Doctrine Migration
-- File: ${fileName}
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

`;

  return header + content;
}

// Process a single migration file
function processMigrationFile(filePath) {
  console.log(`🔧 Processing ${filePath}...`);

  if (!fs.existsSync(filePath)) {
    console.log(`  ⚠️  File not found`);
    return;
  }

  let content = fs.readFileSync(filePath, 'utf8');

  // Skip if it doesn't create tables
  if (!createsTables(content)) {
    console.log(`  ↪️  No tables created, skipping`);
    return;
  }

  let modified = false;

  // Add doctrine header
  const originalContent = content;
  content = addSqlDoctrineHeader(content, filePath);
  if (content !== originalContent) modified = true;

  // Add Barton ID generator function
  const beforeGenerator = content;
  content = addBartonIdGenerator(content);
  if (content !== beforeGenerator) modified = true;

  // Add Barton ID columns if missing
  if (!hasBartonIdColumn(content)) {
    content = addBartonIdColumn(content);
    modified = true;
    console.log(`  ✅ Added Barton ID columns`);
  } else {
    console.log(`  ✓ Already has Barton ID columns`);
  }

  // Add audit columns if missing
  if (!hasAuditColumns(content)) {
    content = addAuditColumns(content);
    modified = true;
    console.log(`  ✅ Added audit columns`);
  } else {
    console.log(`  ✓ Already has audit columns`);
  }

  // Add updated_at trigger
  const beforeTrigger = content;
  content = addUpdatedAtTrigger(content);
  if (content !== beforeTrigger) modified = true;

  if (modified) {
    // Backup original
    const backupPath = filePath.replace('.sql', '-before-doctrine.sql');
    if (!fs.existsSync(backupPath)) {
      fs.copyFileSync(filePath, backupPath);
    }

    // Write fixed content
    fs.writeFileSync(filePath, content);
    console.log(`  ✅ Migration file updated`);
  } else {
    console.log(`  ✓ No changes needed`);
  }
}

// Find all SQL migration files
function findMigrationFiles() {
  const files = [];
  const searchPaths = [
    'migrations',
    'apps/outreach-process-manager/migrations',
    'apps/factory-imo/garage-mcp/packages/sql,
    infra,
    scripts',
    'garage-mcp/packages/sql,
    infra,
    scripts'
  ];

  for (const searchPath of searchPaths) {
    if (fs.existsSync(searchPath)) {
      const items = fs.readdirSync(searchPath);
      for (const item of items) {
        const fullPath = path.join(searchPath, item);
        if (item.endsWith('.sql') && !item.includes('-before-doctrine')) {
          files.push(fullPath);
        }
      }
    }
  }

  return files;
}

// Main execution
function main() {
  console.log('🚀 Fixing migration files for Barton Doctrine compliance...\n');

  const migrationFiles = findMigrationFiles();
  console.log(`Found ${migrationFiles.length} migration files\n`);

  let processed = 0;
  let modified = 0;
  let skipped = 0;

  for (const file of migrationFiles) {
    const beforeContent = fs.readFileSync(file, 'utf8');
    processMigrationFile(file);

    const afterContent = fs.readFileSync(file, 'utf8');
    processed++;

    if (beforeContent !== afterContent) {
      modified++;
    } else {
      skipped++;
    }
  }

  console.log('\n✅ Migration fix complete!');
  console.log(`📊 Summary:`);
  console.log(`  - Files processed: ${processed}`);
  console.log(`  - Files modified: ${modified}`);
  console.log(`  - Files skipped: ${skipped}`);
  console.log(`\n🔍 Next: Fix infrastructure SQL files`);
}

// Run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}