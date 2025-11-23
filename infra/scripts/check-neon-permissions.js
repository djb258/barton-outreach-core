#!/usr/bin/env node
/**
 * Check Neon PostgreSQL Permissions
 * Determine what permissions the current role has
 */

const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.NEON_CONNECTION_STRING || process.env.DATABASE_URL;

async function checkPermissions() {
  const client = new Client({ connectionString });

  try {
    await client.connect();
    console.log('✅ Connected to Neon PostgreSQL\n');

    // Check current role
    const currentRoleResult = await client.query('SELECT current_user, current_database()');
    console.log('📊 Current Connection:');
    console.table(currentRoleResult.rows);

    // Check role capabilities
    const roleCapabilitiesResult = await client.query(`
      SELECT
        rolname,
        rolsuper,
        rolinherit,
        rolcreaterole,
        rolcreatedb,
        rolcanlogin,
        rolreplication
      FROM pg_roles
      WHERE rolname = current_user
    `);
    console.log('📊 Current Role Capabilities:');
    console.table(roleCapabilitiesResult.rows);

    // Check if we can create roles
    const canCreateRole = roleCapabilitiesResult.rows[0]?.rolcreaterole || false;

    if (canCreateRole) {
      console.log('✅ Current role CAN create new roles\n');
    } else {
      console.log('❌ Current role CANNOT create new roles');
      console.log('💡 You must use Neon Console to create roles\n');
    }

    // Check existing roles
    const existingRolesResult = await client.query(`
      SELECT rolname, rolcanlogin, rolsuper, rolcreaterole
      FROM pg_roles
      WHERE rolname LIKE '%marketing%' OR rolname LIKE '%owner%'
      ORDER BY rolname
    `);
    console.log('📊 Existing Marketing/Owner Roles:');
    console.table(existingRolesResult.rows);

    // Check schemas
    const schemasResult = await client.query(`
      SELECT nspname
      FROM pg_namespace
      WHERE nspname NOT LIKE 'pg_%' AND nspname != 'information_schema'
      ORDER BY nspname
    `);
    console.log('📊 Available Schemas:');
    console.table(schemasResult.rows);

    // Check if invalid tables exist
    const invalidTablesResult = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_name LIKE '%invalid%'
      ORDER BY table_schema, table_name
    `);
    console.log('📊 Invalid Tables:');
    console.table(invalidTablesResult.rows);

    console.log('\n' + '='.repeat(80));
    console.log('RECOMMENDATION:');
    console.log('='.repeat(80));

    if (!canCreateRole) {
      console.log(`
⚠️  Your current role cannot create new roles.

To create a Lovable-friendly role, you have 2 options:

OPTION 1: Use Neon Console (Recommended)
-----------------------------------------
1. Go to https://console.neon.tech
2. Navigate to your project: Marketing DB
3. Go to "Roles" section
4. Click "New Role"
5. Role Name: marketing_db_owner
6. Generate Password (save it!)
7. Grant permissions to schemas: marketing, intake, bit, shq, public

OPTION 2: Use Existing Role
---------------------------
The role "Marketing DB_owner" already exists and has permissions.
However, it has a space in the name which can cause SCRAM auth issues.

You can try using it directly in Lovable with URL encoding:
  Username: Marketing%20DB_owner
  Password: npg_OsE4Z2oPCpiT

Connection String:
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require

If this doesn't work in Lovable, you MUST create a new role in Neon Console.
      `);
    } else {
      console.log('✅ You can create roles! Proceeding with role creation...');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkPermissions().catch(console.error);
