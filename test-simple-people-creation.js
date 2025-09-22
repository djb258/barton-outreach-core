import pkg from 'pg';

const { Client } = pkg;

async function testSimpleCreation() {
  const connectionString = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';

  const client = new Client({
    connectionString: connectionString
  });

  try {
    await client.connect();
    console.log('🔗 Connected to Neon Marketing DB\n');

    // Step 1: Create schema
    console.log('Step 1: Creating people schema...');
    await client.query('CREATE SCHEMA IF NOT EXISTS people;');
    console.log('✅ Schema created successfully');

    // Step 2: Create simple table
    console.log('Step 2: Creating people.contact table...');
    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS people.contact (
        contact_unique_id        TEXT PRIMARY KEY,
        company_unique_id        TEXT NOT NULL,
        first_name               TEXT NOT NULL,
        last_name                TEXT NOT NULL,
        email                    TEXT,
        created_at               TIMESTAMPTZ DEFAULT now(),
        updated_at               TIMESTAMPTZ DEFAULT now()
      );
    `;

    await client.query(createTableSQL);
    console.log('✅ Table created successfully');

    // Step 3: Verify creation
    console.log('Step 3: Verifying table creation...');
    const verifyResult = await client.query(`
      SELECT table_name, table_schema
      FROM information_schema.tables
      WHERE table_schema = 'people' AND table_name = 'contact';
    `);

    console.log('Tables found:', verifyResult.rows);

    // Step 4: Check columns
    console.log('Step 4: Checking columns...');
    const columnResult = await client.query(`
      SELECT column_name, data_type
      FROM information_schema.columns
      WHERE table_schema = 'people' AND table_name = 'contact'
      ORDER BY ordinal_position;
    `);

    console.log('Columns:', columnResult.rows);

    console.log('✅ Simple creation test successful!');

  } catch (err) {
    console.error('❌ Database error:', err.message);
    console.error('Stack:', err.stack);
  } finally {
    await client.end();
    console.log('\n🔚 Connection closed');
  }
}

console.log('🚀 Starting Simple People Creation Test...\n');
testSimpleCreation();