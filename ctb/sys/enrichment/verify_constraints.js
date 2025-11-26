#!/usr/bin/env node

/**
 * Verify Constraints on company_master
 * Quick check to confirm no 2000 ceiling exists
 */

const { Client } = require('pg');

const connectionString = process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING;
const client = new Client({ connectionString });

async function main() {
  try {
    await client.connect();
    console.log('✓ Connected\n');

    const result = await client.query(`
      SELECT
        conname as constraint_name,
        pg_get_constraintdef(oid) as definition
      FROM pg_constraint
      WHERE conrelid = (
        SELECT oid
        FROM pg_class
        WHERE relname = 'company_master'
        AND relnamespace = (
          SELECT oid
          FROM pg_namespace
          WHERE nspname = 'marketing'
        )
      )
      AND contype = 'c'
    `);

    console.log('=== CHECK CONSTRAINTS ON marketing.company_master ===\n');

    if (result.rows.length === 0) {
      console.log('No check constraints found');
    } else {
      result.rows.forEach(row => {
        console.log(`Constraint: ${row.constraint_name}`);
        console.log(`Definition: ${row.definition}`);

        if (row.definition.includes('2000')) {
          console.log('❌ WARNING: Contains 2000 ceiling!');
        } else if (row.definition.includes('employee_count')) {
          console.log('✅ Employee constraint (no ceiling)');
        }
        console.log('');
      });
    }

    await client.end();
  } catch (error) {
    console.error('ERROR:', error.message);
    process.exit(1);
  }
}

main();
