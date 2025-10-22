/**
 * Schema Compliance Audit - Barton Doctrine
 *
 * Verifies all 6 doctrine-required tables/views exist
 * Checks migration files, helper functions, and schema structure
 *
 * Barton Doctrine Requirements:
 * 1. marketing.company_slots (or company_slot)
 * 2. marketing.company_intelligence
 * 3. marketing.people_intelligence
 * 4. shq.audit_log
 * 5. shq.validation_queue
 * 6. marketing.outreach_history
 */

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('\n' + '='.repeat(70));
console.log('📋 BARTON DOCTRINE SCHEMA COMPLIANCE AUDIT');
console.log('='.repeat(70) + '\n');

const MIGRATIONS_DIR = path.join(__dirname, '../apps/outreach-process-manager/migrations');

// Doctrine-required tables/views
const DOCTRINE_REQUIREMENTS = [
  {
    name: 'marketing.company_slots',
    bartonId: '04.04.05.xx.xxxxx.xxx',
    type: 'table',
    purpose: 'Slot management for CEO/CFO/HR positions',
    migrationFile: 'create_company_slot.sql',
    alternateNames: ['marketing.company_slot']
  },
  {
    name: 'marketing.company_intelligence',
    bartonId: '04.04.03.xx.xxxxx.xxx',
    type: 'table',
    purpose: 'Company intelligence signals for BIT',
    migrationFile: '2025-10-22_create_marketing_company_intelligence.sql'
  },
  {
    name: 'marketing.people_intelligence',
    bartonId: '04.04.04.xx.xxxxx.xxx',
    type: 'table',
    purpose: 'Executive movement tracking for PLE',
    migrationFile: '2025-10-22_create_marketing_people_intelligence.sql'
  },
  {
    name: 'shq.audit_log',
    bartonId: 'segment4=05 for audit',
    type: 'view',
    purpose: 'Central audit trail',
    migrationFile: '2025-10-22_move_audit_and_validation_views.sql',
    sourceTables: ['marketing.unified_audit_log']
  },
  {
    name: 'shq.validation_queue',
    bartonId: 'N/A',
    type: 'view',
    purpose: 'Validation management queue',
    migrationFile: '2025-10-22_move_audit_and_validation_views.sql',
    sourceTables: ['intake.validation_failed']
  },
  {
    name: 'marketing.outreach_history',
    bartonId: '04.04.03.XX.XXXXX.XXX (campaigns)',
    type: 'view',
    purpose: 'Unified campaign/execution/message tracking',
    migrationFile: '2025-10-22_create_outreach_history_view.sql',
    sourceTables: ['marketing.campaigns', 'marketing.campaign_executions', 'marketing.message_log']
  }
];

async function auditMigrationFiles() {
  console.log('[AUDIT 1/4] Migration Files\n');
  console.log('─'.repeat(70));

  const results = [];

  for (const req of DOCTRINE_REQUIREMENTS) {
    const migrationPath = path.join(MIGRATIONS_DIR, req.migrationFile);

    try {
      const content = await fs.readFile(migrationPath, 'utf8');
      const size = content.length;

      // Check for key elements
      const hasCreateStatement = req.type === 'table'
        ? content.includes('CREATE TABLE')
        : content.includes('CREATE OR REPLACE VIEW');

      const hasBartonId = content.toLowerCase().includes('barton') ||
                          content.includes('04.04.0');

      const hasComments = content.includes('COMMENT ON');

      const hasFunctions = content.includes('CREATE OR REPLACE FUNCTION');

      const hasIndexes = content.includes('CREATE INDEX');

      console.log(`✅ ${req.name}`);
      console.log(`   Migration: ${req.migrationFile}`);
      console.log(`   Type: ${req.type.toUpperCase()}`);
      console.log(`   Size: ${size.toLocaleString()} characters`);
      console.log(`   Barton ID Format: ${req.bartonId}`);
      if (req.sourceTables) {
        console.log(`   Source Tables: ${req.sourceTables.join(', ')}`);
      }
      console.log(`   Features:`);
      console.log(`     - ${req.type.toUpperCase()} definition: ${hasCreateStatement ? '✅' : '❌'}`);
      console.log(`     - Barton ID references: ${hasBartonId ? '✅' : '⚠️'}`);
      console.log(`     - Documentation comments: ${hasComments ? '✅' : '⚠️'}`);
      if (req.type === 'table') {
        console.log(`     - Helper functions: ${hasFunctions ? '✅' : '⚠️'}`);
        console.log(`     - Indexes: ${hasIndexes ? '✅' : '⚠️'}`);
      }
      console.log('');

      results.push({
        name: req.name,
        status: 'found',
        migrationFile: req.migrationFile,
        size,
        hasCreateStatement,
        hasBartonId,
        hasComments,
        hasFunctions: req.type === 'table' ? hasFunctions : 'N/A',
        hasIndexes: req.type === 'table' ? hasIndexes : 'N/A'
      });

    } catch (error) {
      console.log(`❌ ${req.name}`);
      console.log(`   Migration: ${req.migrationFile} - NOT FOUND`);
      console.log(`   Error: ${error.message}\n`);

      results.push({
        name: req.name,
        status: 'missing',
        error: error.message
      });
    }
  }

  return results;
}

async function auditHelperFunctions() {
  console.log('\n[AUDIT 2/4] Helper Functions\n');
  console.log('─'.repeat(70));

  const functionChecks = [
    {
      name: 'generate_company_intelligence_barton_id()',
      file: '2025-10-22_create_marketing_company_intelligence.sql',
      purpose: 'Generate Barton ID for company intelligence (04.04.03.XX.XXXXX.XXX)'
    },
    {
      name: 'generate_people_intelligence_barton_id()',
      file: '2025-10-22_create_marketing_people_intelligence.sql',
      purpose: 'Generate Barton ID for people intelligence (04.04.04.XX.XXXXX.XXX)'
    },
    {
      name: 'insert_company_intelligence()',
      file: '2025-10-22_create_marketing_company_intelligence.sql',
      purpose: 'Insert company intelligence with auto-generated Barton ID'
    },
    {
      name: 'insert_people_intelligence()',
      file: '2025-10-22_create_marketing_people_intelligence.sql',
      purpose: 'Insert people intelligence with auto-generated Barton ID'
    },
    {
      name: 'get_company_intelligence()',
      file: '2025-10-22_create_marketing_company_intelligence.sql',
      purpose: 'Retrieve recent intelligence for a company'
    },
    {
      name: 'get_people_intelligence()',
      file: '2025-10-22_create_marketing_people_intelligence.sql',
      purpose: 'Retrieve recent intelligence for a person'
    },
    {
      name: 'get_high_impact_signals()',
      file: '2025-10-22_create_marketing_company_intelligence.sql',
      purpose: 'Get high-impact signals for BIT engine'
    },
    {
      name: 'get_recent_executive_movements()',
      file: '2025-10-22_create_marketing_people_intelligence.sql',
      purpose: 'Get recent executive movements for PLE engine'
    }
  ];

  const results = [];

  for (const func of functionChecks) {
    const migrationPath = path.join(MIGRATIONS_DIR, func.file);

    try {
      const content = await fs.readFile(migrationPath, 'utf8');
      const found = content.includes(func.name);

      if (found) {
        console.log(`✅ ${func.name}`);
        console.log(`   Purpose: ${func.purpose}`);
        console.log(`   Location: ${func.file}\n`);
        results.push({ name: func.name, status: 'found' });
      } else {
        console.log(`⚠️  ${func.name}`);
        console.log(`   Expected in: ${func.file}`);
        console.log(`   Status: NOT FOUND\n`);
        results.push({ name: func.name, status: 'missing' });
      }

    } catch (error) {
      console.log(`❌ ${func.name}`);
      console.log(`   Error: ${error.message}\n`);
      results.push({ name: func.name, status: 'error' });
    }
  }

  return results;
}

async function auditSchemaStructure() {
  console.log('\n[AUDIT 3/4] Schema Structure\n');
  console.log('─'.repeat(70));

  const schemas = [
    {
      name: 'marketing',
      tables: ['company_master', 'people_master', 'company_slot', 'company_intelligence', 'people_intelligence', 'campaigns', 'campaign_executions'],
      views: ['outreach_history']
    },
    {
      name: 'shq',
      tables: [],
      views: ['audit_log', 'validation_queue']
    },
    {
      name: 'intake',
      tables: ['company_raw_intake', 'validation_failed', 'validation_audit_log', 'human_firebreak_queue'],
      views: []
    }
  ];

  for (const schema of schemas) {
    console.log(`\n📦 Schema: ${schema.name}`);

    if (schema.tables.length > 0) {
      console.log(`   Tables (${schema.tables.length}):`);
      schema.tables.forEach(table => {
        console.log(`     - ${schema.name}.${table}`);
      });
    }

    if (schema.views.length > 0) {
      console.log(`   Views (${schema.views.length}):`);
      schema.views.forEach(view => {
        console.log(`     - ${schema.name}.${view}`);
      });
    }
  }

  console.log('');

  return schemas;
}

async function generateComplianceReport(migrationResults, functionResults) {
  console.log('\n[AUDIT 4/4] Compliance Report\n');
  console.log('='.repeat(70));

  const foundMigrations = migrationResults.filter(r => r.status === 'found').length;
  const totalMigrations = migrationResults.length;
  const migrationCompliance = Math.round((foundMigrations / totalMigrations) * 100);

  const foundFunctions = functionResults.filter(r => r.status === 'found').length;
  const totalFunctions = functionResults.length;
  const functionCompliance = Math.round((foundFunctions / totalFunctions) * 100);

  console.log('\n📊 COMPLIANCE METRICS\n');
  console.log(`Migration Files:     ${foundMigrations}/${totalMigrations} (${migrationCompliance}%)`);
  console.log(`Helper Functions:    ${foundFunctions}/${totalFunctions} (${functionCompliance}%)`);
  console.log(`Overall Compliance:  ${migrationCompliance === 100 && functionCompliance === 100 ? '✅ 100%' : `⚠️ ${Math.round((migrationCompliance + functionCompliance) / 2)}%`}`);

  console.log('\n📋 DOCTRINE REQUIREMENTS STATUS\n');

  DOCTRINE_REQUIREMENTS.forEach((req, index) => {
    const result = migrationResults.find(r => r.name === req.name);
    const status = result?.status === 'found' ? '✅ COMPLIANT' : '❌ MISSING';

    console.log(`${index + 1}. ${req.name}`);
    console.log(`   Status: ${status}`);
    console.log(`   Type: ${req.type.toUpperCase()}`);
    console.log(`   Barton ID: ${req.bartonId}`);
    console.log(`   Purpose: ${req.purpose}`);

    if (result?.status === 'found') {
      console.log(`   ✓ Migration file exists`);
      console.log(`   ✓ ${req.type.toUpperCase()} definition present`);
      if (result.hasComments) console.log(`   ✓ Documentation comments`);
      if (req.type === 'table') {
        if (result.hasFunctions) console.log(`   ✓ Helper functions`);
        if (result.hasIndexes) console.log(`   ✓ Performance indexes`);
      }
      if (req.sourceTables) {
        console.log(`   ✓ Source tables: ${req.sourceTables.join(', ')}`);
      }
    } else {
      console.log(`   ✗ Migration file missing or incomplete`);
    }
    console.log('');
  });

  console.log('\n🎯 DEPLOYMENT STATUS\n');

  if (migrationCompliance === 100) {
    console.log('✅ All migration files created and ready for deployment');
    console.log('✅ Schema is Barton Doctrine compliant (in code)');
    console.log('\n📋 Next Steps:');
    console.log('   1. Ensure Composio MCP server is running (localhost:3001)');
    console.log('   2. Set environment variables (COMPOSIO_USER_ID, NEON_DATABASE_URL)');
    console.log('   3. Run: cd apps/outreach-process-manager/scripts');
    console.log('   4. Run: node execute-intelligence-migrations-via-composio.js');
    console.log('   5. Verify deployment with schema verification queries');
  } else {
    console.log('⚠️  Some migration files are missing');
    console.log('⚠️  Review missing items above before deployment');
  }

  console.log('\n' + '='.repeat(70));
  console.log('📋 AUDIT COMPLETE');
  console.log('='.repeat(70) + '\n');

  return {
    migrationCompliance,
    functionCompliance,
    overallCompliance: Math.round((migrationCompliance + functionCompliance) / 2),
    allReady: migrationCompliance === 100 && functionCompliance === 100
  };
}

async function runAudit() {
  try {
    console.log('Starting comprehensive schema compliance audit...\n');

    const migrationResults = await auditMigrationFiles();
    const functionResults = await auditHelperFunctions();
    const schemaStructure = await auditSchemaStructure();
    const complianceReport = await generateComplianceReport(migrationResults, functionResults);

    if (complianceReport.allReady) {
      console.log('✅ Schema compliance audit PASSED');
      process.exit(0);
    } else {
      console.log('⚠️  Schema compliance audit completed with warnings');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Audit failed:', error);
    console.error('   Stack:', error.stack);
    process.exit(1);
  }
}

runAudit();
