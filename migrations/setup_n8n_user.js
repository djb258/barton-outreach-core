const { Client } = require('pg');

(async () => {
  const client = new Client({
    connectionString: 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require&channel_binding=require'
  });

  try {
    await client.connect();
    console.log('✓ Connected to Neon Database\n');
    console.log('═'.repeat(80));
    console.log('🔐 N8N USER SETUP - Security Configuration');
    console.log('═'.repeat(80));

    // 1️⃣ Create n8n_user role with password
    console.log('\n📝 Step 1: Creating n8n_user role...\n');

    const password = 'n8n_secure_' + Math.random().toString(36).substring(2, 15);

    try {
      await client.query('DROP ROLE IF EXISTS n8n_user');
      console.log('  ↳ Dropped existing n8n_user (if any)');
    } catch (err) {
      console.log('  ↳ No existing n8n_user to drop');
    }

    await client.query(`CREATE ROLE n8n_user WITH LOGIN PASSWORD '${password}'`);
    console.log('  ✅ Role n8n_user created with secure password');

    // 2️⃣ Grant database connection
    console.log('\n📝 Step 2: Granting database access...\n');

    await client.query('GRANT CONNECT ON DATABASE "Marketing DB" TO n8n_user');
    console.log('  ✅ GRANT CONNECT ON DATABASE "Marketing DB" TO n8n_user');

    // 3️⃣ Grant schema access
    console.log('\n📝 Step 3: Granting schema access...\n');

    await client.query('GRANT USAGE ON SCHEMA intake TO n8n_user');
    console.log('  ✅ GRANT USAGE ON SCHEMA intake TO n8n_user');

    await client.query('GRANT USAGE ON SCHEMA marketing TO n8n_user');
    console.log('  ✅ GRANT USAGE ON SCHEMA marketing TO n8n_user');

    await client.query('GRANT USAGE ON SCHEMA public TO n8n_user');
    console.log('  ✅ GRANT USAGE ON SCHEMA public TO n8n_user');

    // 4️⃣ Grant table permissions
    console.log('\n📝 Step 4: Granting table permissions...\n');

    await client.query('GRANT SELECT, INSERT, UPDATE ON intake.company_raw_intake TO n8n_user');
    console.log('  ✅ GRANT SELECT, INSERT, UPDATE ON intake.company_raw_intake TO n8n_user');

    await client.query('GRANT SELECT, INSERT, UPDATE ON marketing.company_master TO n8n_user');
    console.log('  ✅ GRANT SELECT, INSERT, UPDATE ON marketing.company_master TO n8n_user');

    await client.query('GRANT SELECT, INSERT ON marketing.company_slots TO n8n_user');
    console.log('  ✅ GRANT SELECT, INSERT ON marketing.company_slots TO n8n_user');

    await client.query('GRANT SELECT, INSERT, UPDATE ON marketing.people_master TO n8n_user');
    console.log('  ✅ GRANT SELECT, INSERT, UPDATE ON marketing.people_master TO n8n_user');

    await client.query('GRANT SELECT, INSERT ON public.shq_validation_log TO n8n_user');
    console.log('  ✅ GRANT SELECT, INSERT ON public.shq_validation_log TO n8n_user');

    // 5️⃣ Grant sequence access
    console.log('\n📝 Step 5: Granting sequence permissions...\n');

    await client.query('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO n8n_user');
    console.log('  ✅ GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO n8n_user');

    await client.query('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO n8n_user');
    console.log('  ✅ GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO n8n_user');

    await client.query('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_user');
    console.log('  ✅ GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_user');

    // 6️⃣ Check and grant function access
    console.log('\n📝 Step 6: Checking for promotion function...\n');

    const funcCheck = await client.query(`
      SELECT
        n.nspname as schema_name,
        p.proname as function_name
      FROM pg_proc p
      JOIN pg_namespace n ON p.pronamespace = n.oid
      WHERE p.proname = 'promote_company_records'
    `);

    if (funcCheck.rows.length > 0) {
      const schema = funcCheck.rows[0].schema_name;
      if (schema !== 'public' && schema !== 'intake' && schema !== 'marketing') {
        await client.query(`GRANT USAGE ON SCHEMA ${schema} TO n8n_user`);
        console.log(`  ✅ GRANT USAGE ON SCHEMA ${schema} TO n8n_user`);
      }
      await client.query(`GRANT EXECUTE ON FUNCTION ${schema}.promote_company_records(TEXT, TEXT) TO n8n_user`);
      console.log(`  ✅ GRANT EXECUTE ON FUNCTION ${schema}.promote_company_records(TEXT, TEXT) TO n8n_user`);
    } else {
      console.log('  ℹ️  promote_company_records function not found');
    }

    // 7️⃣ Verify permissions
    console.log('\n' + '═'.repeat(80));
    console.log('📊 PERMISSION VERIFICATION\n');

    const permissions = await client.query(`
      SELECT
        table_schema,
        table_name,
        STRING_AGG(privilege_type, ', ' ORDER BY privilege_type) as privileges
      FROM information_schema.table_privileges
      WHERE grantee = 'n8n_user'
      GROUP BY table_schema, table_name
      ORDER BY table_schema, table_name
    `);

    permissions.rows.forEach((row) => {
      const fullName = (row.table_schema + '.' + row.table_name).padEnd(40);
      console.log('  ✅ ' + fullName + ' → ' + row.privileges);
    });

    // 8️⃣ Generate connection string
    console.log('\n' + '═'.repeat(80));
    console.log('🔗 CONNECTION STRING\n');

    const host = 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech';
    const database = 'Marketing DB';
    const connectionString = 'postgresql://n8n_user:' + password + '@' + host + '/' + encodeURIComponent(database) + '?sslmode=require';

    console.log('Add this to your n8n .env file:\n');
    console.log('N8N_DB_HOST=' + host);
    console.log('N8N_DB_NAME=' + encodeURIComponent(database));
    console.log('N8N_DB_USER=n8n_user');
    console.log('N8N_DB_PASSWORD=' + password);
    console.log('N8N_DB_SSL=true');
    console.log('');
    console.log('Or as single connection string:');
    console.log('DATABASE_URL=' + connectionString);

    console.log('\n' + '═'.repeat(80));
    console.log('✅ n8n user setup complete!\n');

    // Save credentials
    const fs = require('fs');
    const path = require('path');
    const credPath = path.join(__dirname, 'N8N_CREDENTIALS.txt');

    const credContent = `# N8N Database Credentials
# Generated: ${new Date().toISOString()}
# Role: n8n_user (limited permissions)

# Individual components:
N8N_DB_HOST=${host}
N8N_DB_NAME=${encodeURIComponent(database)}
N8N_DB_USER=n8n_user
N8N_DB_PASSWORD=${password}
N8N_DB_SSL=true

# Connection string:
DATABASE_URL=${connectionString}

# Permissions granted:
# - CONNECT on database
# - USAGE on schemas: intake, marketing, public
# - SELECT, INSERT, UPDATE on core tables
# - USAGE, SELECT on all sequences
# - EXECUTE on promotion function (if exists)
# - NO DROP, ALTER, TRUNCATE, or superuser privileges

# Security notes:
# - Keep this file secure and do not commit to git
# - Add to .gitignore: migrations/N8N_CREDENTIALS.txt
# - Change password if compromised
# - Role has minimum required permissions only
`;

    fs.writeFileSync(credPath, credContent);
    console.log('📄 Credentials saved to: migrations/N8N_CREDENTIALS.txt\n');

  } catch (err) {
    console.error('❌ Error:', err.message);
    console.error(err.stack);
    process.exit(1);
  } finally {
    await client.end();
  }
})();
