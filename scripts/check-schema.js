import pkg from 'pg';
const { Client } = pkg;

async function checkSchema() {
  const connectionString = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';
  
  const client = new Client({
    connectionString: connectionString
  });

  try {
    await client.connect();
    console.log('Connected to Neon Marketing DB\n');

    // List all schemas
    const schemasResult = await client.query(`
      SELECT schema_name 
      FROM information_schema.schemata 
      WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      ORDER BY schema_name;
    `);
    
    console.log('=== Available Schemas ===');
    schemasResult.rows.forEach(row => {
      console.log(`- ${row.schema_name}`);
    });

    // List all tables in marketing schema
    const marketingTablesResult = await client.query(`
      SELECT 
        table_name,
        table_type
      FROM information_schema.tables 
      WHERE table_schema = 'marketing'
      ORDER BY table_name;
    `);
    
    console.log('\n=== Tables in "marketing" schema ===');
    if (marketingTablesResult.rows.length === 0) {
      console.log('No tables found in marketing schema');
    } else {
      for (const table of marketingTablesResult.rows) {
        console.log(`\n📊 ${table.table_name} (${table.table_type})`);
        
        // Get columns for each table
        const columnsResult = await client.query(`
          SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
          FROM information_schema.columns 
          WHERE table_schema = 'marketing' 
            AND table_name = $1
          ORDER BY ordinal_position;
        `, [table.table_name]);
        
        columnsResult.rows.forEach(col => {
          const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
          const maxLength = col.character_maximum_length ? `(${col.character_maximum_length})` : '';
          const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
          console.log(`  - ${col.column_name}: ${col.data_type}${maxLength} ${nullable}${defaultVal}`);
        });
      }
    }

    // Check for company schema
    const companyTablesResult = await client.query(`
      SELECT 
        table_name,
        table_type
      FROM information_schema.tables 
      WHERE table_schema = 'company'
      ORDER BY table_name;
    `);
    
    console.log('\n=== Tables in "company" schema ===');
    if (companyTablesResult.rows.length === 0) {
      console.log('No tables found in company schema');
    } else {
      for (const table of companyTablesResult.rows) {
        console.log(`\n📊 ${table.table_name} (${table.table_type})`);
        
        // Get columns for each table
        const columnsResult = await client.query(`
          SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
          FROM information_schema.columns 
          WHERE table_schema = 'company' 
            AND table_name = $1
          ORDER BY ordinal_position;
        `, [table.table_name]);
        
        columnsResult.rows.forEach(col => {
          const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
          const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
          console.log(`  - ${col.column_name}: ${col.data_type} ${nullable}${defaultVal}`);
        });
      }
    }

    // Check for outreach schema
    const outreachTablesResult = await client.query(`
      SELECT table_name FROM information_schema.tables 
      WHERE table_schema = 'outreach'
      ORDER BY table_name;
    `);
    
    console.log('\n=== Tables in "outreach" schema ===');
    if (outreachTablesResult.rows.length === 0) {
      console.log('No outreach schema or tables found');
    } else {
      outreachTablesResult.rows.forEach(row => {
        console.log(`- ${row.table_name}`);
      });
    }

    // Check for shq schema
    const shqTablesResult = await client.query(`
      SELECT table_name FROM information_schema.tables 
      WHERE table_schema = 'shq'
      ORDER BY table_name;
    `);
    
    console.log('\n=== Tables in "shq" schema ===');
    if (shqTablesResult.rows.length === 0) {
      console.log('No shq schema or tables found');
    } else {
      shqTablesResult.rows.forEach(row => {
        console.log(`- ${row.table_name}`);
      });
    }

  } catch (err) {
    console.error('Database error:', err);
  } finally {
    await client.end();
    console.log('\nConnection closed');
  }
}

checkSchema();