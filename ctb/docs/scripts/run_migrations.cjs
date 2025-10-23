/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/scripts
Barton ID: 06.01.04
Unique ID: CTB-24AD239A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

const migrations = [
  '../apps/outreach-process-manager/migrations/2025-10-23_fix_marketing_company_slot_duplicates.sql',
  '../apps/outreach-process-manager/migrations/2025-10-23_fix_company_slot_fk.sql',
  '../apps/outreach-process-manager/migrations/2025-10-23_fix_people_master_column_naming.sql',
  '../apps/outreach-process-manager/migrations/2025-10-23_verify_shq_views.sql'
];

async function run() {
  const connectionString = process.env.DATABASE_URL || process.env.NEON_DATABASE_URL;

  if (!connectionString) {
    console.error('❌ No DATABASE_URL or NEON_DATABASE_URL found');
    process.exit(1);
  }

  const client = new Client({ connectionString });

  try {
    await client.connect();
    console.log('✅ Connected to Neon database\n');

    for (const file of migrations) {
      const filePath = path.join(__dirname, file);
      const fileName = path.basename(file);

      console.log(`📄 Executing: ${fileName}`);
      const sql = fs.readFileSync(filePath, 'utf8');

      try {
        await client.query(sql);
        console.log(`✅ Success\n`);
      } catch (error) {
        console.error(`❌ Error: ${error.message}\n`);
      }
    }

    console.log('✅ All migrations complete!');
  } catch (error) {
    console.error('❌ Connection error:', error.message);
    process.exit(1);
  } finally {
    await client.end();
  }
}

run();
