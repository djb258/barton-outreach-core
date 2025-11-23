#!/usr/bin/env node
/**
 * Create Lovable.dev Role in Neon PostgreSQL - Version 2
 * Executes commands in proper order with error handling
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;
const NEW_ROLE = 'marketing_db_owner';
const NEW_PASSWORD = 'G1wkzJLlpYdIb3Hq0YOZX2Z4m67uveb';

async function createLovableRole() {
  const client = new Client({ connectionString });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL\n');

    // Step 1: Check if role already exists
    console.log('🔍 Checking if role exists...');
    const checkRoleResult = await client.query(
      `SELECT 1 FROM pg_roles WHERE rolname = $1`,
      [NEW_ROLE]
    );

    if (checkRoleResult.rows.length > 0) {
      console.log(`⚠️  Role "${NEW_ROLE}" already exists`);
      console.log('🔄 Dropping existing role and recreating...\n');

      // Revoke permissions first
      await client.query(`REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA marketing FROM ${NEW_ROLE}`);
      await client.query(`REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA marketing FROM ${NEW_ROLE}`);
      await client.query(`REVOKE USAGE ON SCHEMA marketing FROM ${NEW_ROLE}`);

      // Drop role
      await client.query(`DROP ROLE IF EXISTS ${NEW_ROLE}`);
      console.log('✅ Existing role dropped\n');
    }

    // Step 2: Create role
    console.log('📝 Creating new role...');
    await client.query(`CREATE ROLE ${NEW_ROLE} WITH LOGIN PASSWORD '${NEW_PASSWORD}'`);
    console.log(`✅ Role "${NEW_ROLE}" created with LOGIN\n`);

    // Step 3: Grant schema usage
    console.log('📝 Granting schema USAGE...');
    const schemas = ['public', 'marketing', 'intake', 'bit', 'shq', 'ple', 'PLE', 'BIT'];

    for (const schema of schemas) {
      try {
        await client.query(`GRANT USAGE ON SCHEMA ${schema} TO ${NEW_ROLE}`);
        console.log(`  ✅ Granted USAGE on schema: ${schema}`);
      } catch (err) {
        if (err.message.includes('does not exist')) {
          console.log(`  ⚠️  Schema ${schema} does not exist, skipping`);
        } else {
          throw err;
        }
      }
    }

    // Step 4: Grant table permissions
    console.log('\n📝 Granting table permissions...');
    for (const schema of schemas) {
      try {
        await client.query(`GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ${schema} TO ${NEW_ROLE}`);
        console.log(`  ✅ Granted table permissions on schema: ${schema}`);
      } catch (err) {
        if (err.message.includes('does not exist')) {
          console.log(`  ⚠️  Schema ${schema} does not exist, skipping`);
        } else {
          console.error(`  ❌ Failed to grant table permissions on ${schema}:`, err.message);
        }
      }
    }

    // Step 5: Grant sequence permissions
    console.log('\n📝 Granting sequence permissions...');
    for (const schema of schemas) {
      try {
        await client.query(`GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ${schema} TO ${NEW_ROLE}`);
        console.log(`  ✅ Granted sequence permissions on schema: ${schema}`);
      } catch (err) {
        if (err.message.includes('does not exist')) {
          console.log(`  ⚠️  Schema ${schema} does not exist, skipping`);
        } else {
          console.error(`  ❌ Failed to grant sequence permissions on ${schema}:`, err.message);
        }
      }
    }

    // Step 6: Grant function execution
    console.log('\n📝 Granting function EXECUTE...');
    for (const schema of schemas) {
      try {
        await client.query(`GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ${schema} TO ${NEW_ROLE}`);
        console.log(`  ✅ Granted EXECUTE on functions in schema: ${schema}`);
      } catch (err) {
        if (err.message.includes('does not exist')) {
          console.log(`  ⚠️  Schema ${schema} does not exist, skipping`);
        } else {
          console.error(`  ❌ Failed to grant function permissions on ${schema}:`, err.message);
        }
      }
    }

    // Step 7: Set default privileges for future objects
    console.log('\n📝 Setting default privileges for future objects...');
    for (const schema of schemas) {
      try {
        await client.query(`ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${NEW_ROLE}`);
        await client.query(`ALTER DEFAULT PRIVILEGES IN SCHEMA ${schema} GRANT USAGE, SELECT ON SEQUENCES TO ${NEW_ROLE}`);
        console.log(`  ✅ Set default privileges on schema: ${schema}`);
      } catch (err) {
        if (err.message.includes('does not exist')) {
          console.log(`  ⚠️  Schema ${schema} does not exist, skipping`);
        } else {
          console.error(`  ❌ Failed to set default privileges on ${schema}:`, err.message);
        }
      }
    }

    // Step 8: Grant database-level permissions
    console.log('\n📝 Granting database-level permissions...');
    await client.query(`GRANT TEMP ON DATABASE "Marketing DB" TO ${NEW_ROLE}`);
    console.log('  ✅ Granted TEMP on database\n');

    // Step 9: Verify role and permissions
    console.log('🧪 Verifying role...');
    const verifyRoleResult = await client.query(`
      SELECT rolname, rolcanlogin, rolcreaterole, rolcreatedb
      FROM pg_roles
      WHERE rolname = $1
    `, [NEW_ROLE]);
    console.log('✅ Role verification:');
    console.table(verifyRoleResult.rows);

    // Step 10: Test table access
    console.log('🧪 Testing table access...');
    const tableAccessResult = await client.query(`
      SELECT schemaname, tablename
      FROM pg_tables
      WHERE schemaname IN ('marketing', 'intake', 'bit', 'shq')
        AND tablename LIKE '%invalid%'
      ORDER BY schemaname, tablename
    `);
    console.log('✅ Accessible invalid tables:');
    console.table(tableAccessResult.rows);

    // Generate connection strings
    console.log('\n' + '='.repeat(80));
    console.log('🎉 SUCCESS! Role created and permissions granted');
    console.log('='.repeat(80));

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error('\nStack:', error.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
}

createLovableRole().catch(console.error);
