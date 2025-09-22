import pkg from 'pg';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const { Client } = pkg;
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function executePeopleExtension() {
  const connectionString = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';

  const client = new Client({
    connectionString: connectionString
  });

  try {
    await client.connect();
    console.log('🔗 Connected to Neon Marketing DB\n');

    // Read the extension DDL file
    const ddlPath = join(__dirname, 'extend-people-schema.sql');
    const ddlContent = readFileSync(ddlPath, 'utf8');

    console.log('📄 Executing People Schema Extension...\n');

    // Execute the DDL
    await client.query(ddlContent);

    console.log('✅ People schema extension executed successfully!\n');

    // Verify the new columns were added
    const columnsResult = await client.query(`
      SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
      FROM information_schema.columns
      WHERE table_schema = 'people' AND table_name = 'contact'
      ORDER BY ordinal_position;
    `);

    console.log('📊 Updated columns in people.contact:');
    columnsResult.rows.forEach(col => {
      const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
      const defaultVal = col.column_default ? ` DEFAULT ${col.column_default}` : '';
      console.log(`   ${col.column_name} (${col.data_type}) ${nullable}${defaultVal}`);
    });

    // Check new indexes
    const indexesResult = await client.query(`
      SELECT
        indexname,
        tablename
      FROM pg_indexes
      WHERE schemaname = 'people' AND tablename = 'contact'
        AND indexname LIKE '%_new'
      ORDER BY indexname;
    `);

    console.log('\n🔍 New indexes created:');
    if (indexesResult.rows.length === 0) {
      console.log('   No new indexes found (may have already existed)');
    } else {
      indexesResult.rows.forEach(index => {
        console.log(`   ${index.indexname}`);
      });
    }

    // Check if the enhanced view was created
    const viewResult = await client.query(`
      SELECT table_name
      FROM information_schema.views
      WHERE table_schema = 'people' AND table_name = 'contact_enhanced_view';
    `);

    console.log('\n👁️ Enhanced view:');
    if (viewResult.rows.length > 0) {
      console.log('   ✅ people.contact_enhanced_view created successfully');

      // Test the view
      const sampleViewResult = await client.query(`
        SELECT
          contact_id,
          computed_full_name,
          email,
          contact_availability,
          has_social_media,
          has_phone
        FROM people.contact_enhanced_view
        LIMIT 3;
      `);

      console.log('\n📄 Sample data from enhanced view:');
      sampleViewResult.rows.forEach((row, i) => {
        console.log(`   Contact ${i + 1}: ${row.computed_full_name} (${row.email}) - ${row.contact_availability}`);
      });
    } else {
      console.log('   ❌ Enhanced view was not created');
    }

    // Run the name splitting function for existing data
    console.log('\n🔄 Running name splitting function for existing data...');
    await client.query('SELECT people.split_full_name_if_missing();');
    console.log('   ✅ Name splitting completed');

    // Show summary of extension
    const totalContactsResult = await client.query(`
      SELECT COUNT(*) as total_contacts
      FROM people.contact;
    `);

    const contactsWithNewFieldsResult = await client.query(`
      SELECT
        COUNT(*) as with_company_id,
        COUNT(first_name) as with_first_name,
        COUNT(last_name) as with_last_name,
        COUNT(email_status) as with_email_status
      FROM people.contact;
    `);

    console.log('\n📈 Extension Summary:');
    console.log(`   Total contacts: ${totalContactsResult.rows[0].total_contacts}`);
    console.log(`   With first_name: ${contactsWithNewFieldsResult.rows[0].with_first_name}`);
    console.log(`   With last_name: ${contactsWithNewFieldsResult.rows[0].with_last_name}`);
    console.log(`   Ready for company linking: ${contactsWithNewFieldsResult.rows[0].with_company_id}`);

  } catch (err) {
    console.error('❌ Database error:', err.message);
    console.error('Stack:', err.stack);
  } finally {
    await client.end();
    console.log('\n🔚 Connection closed');
  }
}

console.log('🚀 Starting People Schema Extension...\n');
executePeopleExtension();