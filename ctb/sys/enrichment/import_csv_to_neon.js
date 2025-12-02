#!/usr/bin/env node
/**
 * DOL Form 5500 CSV Import to Neon PostgreSQL
 *
 * Imports the prepared staging CSV files to Neon using streaming.
 * Handles large files (230K, 759K, 336K records) efficiently.
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');
const readline = require('readline');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

const BATCH_SIZE = 1000;

// CSV file paths
const CSV_FILES = {
  form_5500: path.join(__dirname, 'output', 'form_5500_2023_staging.csv'),
  form_5500_sf: path.join(__dirname, '..', '..', '..', 'output', 'form_5500_sf_2023_staging.csv'),
  schedule_a: path.join(__dirname, '..', '..', '..', 'output', 'schedule_a_2023_staging.csv')
};

async function getTableColumns(client, tableName) {
  const result = await client.query(`
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'marketing' AND table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);
  return result.rows.map(r => r.column_name);
}

function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (char === '"' && !inQuotes) {
      inQuotes = true;
    } else if (char === '"' && inQuotes) {
      if (nextChar === '"') {
        current += '"';
        i++; // Skip next quote
      } else {
        inQuotes = false;
      }
    } else if (char === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current);

  return values;
}

async function importCSV(client, csvPath, tableName, expectedColumns) {
  console.log(`\nImporting ${tableName}...`);
  console.log(`  File: ${csvPath}`);

  if (!fs.existsSync(csvPath)) {
    console.log(`  ERROR: File not found!`);
    return 0;
  }

  const fileStream = fs.createReadStream(csvPath, { encoding: 'utf8' });
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity
  });

  let lineNum = 0;
  let header = null;
  let batch = [];
  let totalInserted = 0;

  // Get table columns
  const tableColumns = await getTableColumns(client, tableName);
  console.log(`  Table columns: ${tableColumns.length}`);

  for await (const line of rl) {
    lineNum++;

    if (lineNum === 1) {
      header = parseCSVLine(line);
      console.log(`  CSV columns: ${header.length}`);
      console.log(`  First CSV col: "${header[0]}", First table col: "${tableColumns[0]}"`);

      // Find matching columns (case-insensitive comparison)
      const matchingColumns = header.filter(h => tableColumns.some(tc => tc.toLowerCase() === h.toLowerCase()));
      console.log(`  Matching columns: ${matchingColumns.length}`);
      continue;
    }

    const values = parseCSVLine(line);

    // Build insert object matching table columns (case-insensitive)
    const row = {};
    for (let i = 0; i < header.length && i < values.length; i++) {
      const csvCol = header[i].toLowerCase();
      const tableCol = tableColumns.find(tc => tc.toLowerCase() === csvCol);
      if (tableCol) {
        row[tableCol] = values[i] || null;
      }
    }

    // Only add row if it has columns
    if (Object.keys(row).length > 0) {
      batch.push(row);
    }

    // Insert in batches
    if (batch.length >= BATCH_SIZE) {
      await insertBatch(client, tableName, tableColumns, batch);
      totalInserted += batch.length;

      if (totalInserted % 10000 === 0) {
        console.log(`    Inserted ${totalInserted.toLocaleString()} records...`);
      }

      batch = [];
    }
  }

  // Insert remaining
  if (batch.length > 0) {
    await insertBatch(client, tableName, tableColumns, batch);
    totalInserted += batch.length;
  }

  console.log(`  COMPLETE: ${totalInserted.toLocaleString()} records inserted`);
  return totalInserted;
}

async function insertBatch(client, tableName, tableColumns, batch) {
  if (batch.length === 0) return;

  // Get columns that exist in the batch
  const batchColumns = Object.keys(batch[0]);
  const columns = batchColumns.filter(c => tableColumns.includes(c));

  // Build parameterized insert
  const valueRows = [];
  const allValues = [];
  let paramIndex = 1;

  for (const row of batch) {
    const rowParams = [];
    for (const col of columns) {
      rowParams.push(`$${paramIndex++}`);
      allValues.push(row[col] || null);
    }
    valueRows.push(`(${rowParams.join(', ')})`);
  }

  const sql = `
    INSERT INTO marketing.${tableName} (${columns.join(', ')})
    VALUES ${valueRows.join(', ')}
    ON CONFLICT DO NOTHING
  `;

  await client.query(sql, allValues);
}

async function main() {
  console.log('='.repeat(80));
  console.log('DOL FORM 5500 CSV IMPORT TO NEON POSTGRESQL');
  console.log('='.repeat(80));

  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('\nConnected to Neon PostgreSQL');

    // Clear staging tables
    console.log('\nClearing staging tables...');
    await client.query('TRUNCATE marketing.form_5500_staging');
    await client.query('TRUNCATE marketing.form_5500_sf_staging');
    await client.query('TRUNCATE marketing.schedule_a_staging');
    console.log('Staging tables cleared');

    // Import each CSV
    const results = {};

    // Form 5500 (Large Plans)
    results.form_5500 = await importCSV(
      client,
      CSV_FILES.form_5500,
      'form_5500_staging',
      64
    );

    // Form 5500-SF (Small Plans)
    results.form_5500_sf = await importCSV(
      client,
      CSV_FILES.form_5500_sf,
      'form_5500_sf_staging',
      47
    );

    // Schedule A (Insurance)
    results.schedule_a = await importCSV(
      client,
      CSV_FILES.schedule_a,
      'schedule_a_staging',
      13
    );

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('IMPORT SUMMARY');
    console.log('='.repeat(80));
    console.log(`Form 5500 (Large Plans):   ${results.form_5500.toLocaleString()} records`);
    console.log(`Form 5500-SF (Small Plans): ${results.form_5500_sf.toLocaleString()} records`);
    console.log(`Schedule A (Insurance):     ${results.schedule_a.toLocaleString()} records`);
    console.log(`TOTAL:                      ${(results.form_5500 + results.form_5500_sf + results.schedule_a).toLocaleString()} records`);

    // Verify counts
    console.log('\n' + '='.repeat(80));
    console.log('VERIFICATION');
    console.log('='.repeat(80));

    const verify1 = await client.query('SELECT COUNT(*) as cnt FROM marketing.form_5500_staging');
    const verify2 = await client.query('SELECT COUNT(*) as cnt FROM marketing.form_5500_sf_staging');
    const verify3 = await client.query('SELECT COUNT(*) as cnt FROM marketing.schedule_a_staging');

    console.log(`form_5500_staging:    ${parseInt(verify1.rows[0].cnt).toLocaleString()} rows`);
    console.log(`form_5500_sf_staging: ${parseInt(verify2.rows[0].cnt).toLocaleString()} rows`);
    console.log(`schedule_a_staging:   ${parseInt(verify3.rows[0].cnt).toLocaleString()} rows`);

    console.log('\n' + '='.repeat(80));
    console.log('NEXT STEPS');
    console.log('='.repeat(80));
    console.log(`
1. Process staging tables (creates company matches, populates main tables):
   CALL marketing.process_5500_staging();
   CALL marketing.process_5500_sf_staging();
   CALL marketing.process_schedule_a_staging();

2. Verify main tables:
   SELECT COUNT(*) FROM marketing.form_5500;
   SELECT COUNT(*) FROM marketing.form_5500_sf;
   SELECT COUNT(*) FROM marketing.schedule_a;

3. Check hub-and-spoke joins:
   SELECT f.sponsor_dfe_name, COUNT(a.ack_id) as insurance_contracts
   FROM marketing.form_5500 f
   JOIN marketing.schedule_a a ON f.ack_id = a.ack_id
   GROUP BY f.sponsor_dfe_name
   ORDER BY insurance_contracts DESC
   LIMIT 10;
`);

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
