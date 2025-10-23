/**
 * Create people schema and contact table in Neon via Composio MCP
 * Comprehensive contact management with social media integration
 */

import ComposioNeonBridge from '../api/lib/composio-neon-bridge.js';

async function createPeopleSchema() {
  const bridge = new ComposioNeonBridge();

  // Step 1: Create the people schema
  const createSchemaSQL = `
    CREATE SCHEMA IF NOT EXISTS people;
  `;

  // Step 2: Create the contact table (without FK constraints first)
  const createContactTableSQL = `
    CREATE TABLE IF NOT EXISTS people.contact (
      contact_unique_id        TEXT PRIMARY KEY,
      company_unique_id        TEXT NOT NULL,
      slot_unique_id           TEXT,
      first_name               TEXT NOT NULL,
      last_name                TEXT NOT NULL,
      title                    TEXT,
      seniority                TEXT,
      department               TEXT,
      email                    CITEXT,
      email_status             TEXT,
      email_last_verified_at   TIMESTAMPTZ,
      mobile_phone_e164        TEXT,
      work_phone_e164          TEXT,
      linkedin_url             TEXT,
      x_url                    TEXT,
      instagram_url            TEXT,
      facebook_url             TEXT,
      threads_url              TEXT,
      tiktok_url               TEXT,
      youtube_url              TEXT,
      personal_website_url     TEXT,
      github_url               TEXT,
      calendly_url             TEXT,
      whatsapp_handle          TEXT,
      telegram_handle          TEXT,
      do_not_contact           BOOLEAN DEFAULT FALSE,
      contact_owner            TEXT,
      source_system            TEXT,
      source_record_id         TEXT,
      created_at               TIMESTAMPTZ DEFAULT now(),
      updated_at               TIMESTAMPTZ DEFAULT now()
    );
  `;

  // Step 3: Create indexes for performance
  const createIndexesSQL = `
    -- Performance indexes for people.contact table
    CREATE INDEX IF NOT EXISTS idx_contact_company_unique_id ON people.contact (company_unique_id);
    CREATE INDEX IF NOT EXISTS idx_contact_slot_unique_id ON people.contact (slot_unique_id);
    CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
    CREATE INDEX IF NOT EXISTS idx_contact_name ON people.contact (first_name, last_name);
    CREATE INDEX IF NOT EXISTS idx_contact_source_system ON people.contact (source_system);
    CREATE INDEX IF NOT EXISTS idx_contact_created_at ON people.contact (created_at);
    CREATE INDEX IF NOT EXISTS idx_contact_updated_at ON people.contact (updated_at);
  `;

  // Step 4: Create timestamp trigger function for updated_at
  const createTriggerFunctionSQL = `
    -- Create or replace the function to update the updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Create the trigger on people.contact table
    DROP TRIGGER IF EXISTS update_people_contact_updated_at ON people.contact;
    CREATE TRIGGER update_people_contact_updated_at
        BEFORE UPDATE ON people.contact
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
  `;

  // Step 5: Add table and column comments for documentation
  const addCommentsSQL = `
    -- Add table comment
    COMMENT ON TABLE people.contact IS 'Contact information for individuals associated with companies';

    -- Add column comments
    COMMENT ON COLUMN people.contact.contact_unique_id IS 'Unique identifier for the contact';
    COMMENT ON COLUMN people.contact.company_unique_id IS 'Reference to company this contact belongs to';
    COMMENT ON COLUMN people.contact.slot_unique_id IS 'Reference to outreach slot if applicable';
    COMMENT ON COLUMN people.contact.first_name IS 'Contact first name';
    COMMENT ON COLUMN people.contact.last_name IS 'Contact last name';
    COMMENT ON COLUMN people.contact.title IS 'Job title or position';
    COMMENT ON COLUMN people.contact.seniority IS 'Seniority level (junior, mid, senior, executive)';
    COMMENT ON COLUMN people.contact.department IS 'Department or functional area';
    COMMENT ON COLUMN people.contact.email IS 'Primary email address (case-insensitive)';
    COMMENT ON COLUMN people.contact.email_status IS 'Email validation status (valid, invalid, bounced, etc.)';
    COMMENT ON COLUMN people.contact.email_last_verified_at IS 'Last time email was verified';
    COMMENT ON COLUMN people.contact.mobile_phone_e164 IS 'Mobile phone in E.164 format';
    COMMENT ON COLUMN people.contact.work_phone_e164 IS 'Work phone in E.164 format';
    COMMENT ON COLUMN people.contact.linkedin_url IS 'LinkedIn profile URL';
    COMMENT ON COLUMN people.contact.x_url IS 'X (Twitter) profile URL';
    COMMENT ON COLUMN people.contact.instagram_url IS 'Instagram profile URL';
    COMMENT ON COLUMN people.contact.facebook_url IS 'Facebook profile URL';
    COMMENT ON COLUMN people.contact.threads_url IS 'Threads profile URL';
    COMMENT ON COLUMN people.contact.tiktok_url IS 'TikTok profile URL';
    COMMENT ON COLUMN people.contact.youtube_url IS 'YouTube channel URL';
    COMMENT ON COLUMN people.contact.personal_website_url IS 'Personal website URL';
    COMMENT ON COLUMN people.contact.github_url IS 'GitHub profile URL';
    COMMENT ON COLUMN people.contact.calendly_url IS 'Calendly booking URL';
    COMMENT ON COLUMN people.contact.whatsapp_handle IS 'WhatsApp handle or phone number';
    COMMENT ON COLUMN people.contact.telegram_handle IS 'Telegram username or handle';
    COMMENT ON COLUMN people.contact.do_not_contact IS 'Flag indicating if contact should not be reached out to';
    COMMENT ON COLUMN people.contact.contact_owner IS 'User responsible for this contact';
    COMMENT ON COLUMN people.contact.source_system IS 'System that created this contact record';
    COMMENT ON COLUMN people.contact.source_record_id IS 'Original record ID in source system';
    COMMENT ON COLUMN people.contact.created_at IS 'Record creation timestamp';
    COMMENT ON COLUMN people.contact.updated_at IS 'Record last update timestamp';
  `;

  const results = {
    schema_created: false,
    table_created: false,
    indexes_created: false,
    triggers_created: false,
    comments_added: false,
    errors: []
  };

  try {
    console.log('[PEOPLE-SCHEMA] Creating people schema...');

    // Step 1: Create schema
    const schemaResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createSchemaSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (schemaResult.success) {
      console.log('[PEOPLE-SCHEMA] ✓ Schema created successfully');
      results.schema_created = true;
    } else {
      console.error('[PEOPLE-SCHEMA] ✗ Failed to create schema:', schemaResult.error);
      results.errors.push(`Schema creation failed: ${schemaResult.error}`);
    }

    // Step 2: Create contact table
    console.log('[PEOPLE-SCHEMA] Creating people.contact table...');
    const tableResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createContactTableSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (tableResult.success) {
      console.log('[PEOPLE-SCHEMA] ✓ Contact table created successfully');
      results.table_created = true;
    } else {
      console.error('[PEOPLE-SCHEMA] ✗ Failed to create table:', tableResult.error);
      results.errors.push(`Table creation failed: ${tableResult.error}`);
    }

    // Step 3: Create indexes
    console.log('[PEOPLE-SCHEMA] Creating performance indexes...');
    const indexResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createIndexesSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (indexResult.success) {
      console.log('[PEOPLE-SCHEMA] ✓ Indexes created successfully');
      results.indexes_created = true;
    } else {
      console.error('[PEOPLE-SCHEMA] ✗ Failed to create indexes:', indexResult.error);
      results.errors.push(`Index creation failed: ${indexResult.error}`);
    }

    // Step 4: Create trigger function
    console.log('[PEOPLE-SCHEMA] Creating timestamp trigger...');
    const triggerResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createTriggerFunctionSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (triggerResult.success) {
      console.log('[PEOPLE-SCHEMA] ✓ Trigger function created successfully');
      results.triggers_created = true;
    } else {
      console.error('[PEOPLE-SCHEMA] ✗ Failed to create trigger:', triggerResult.error);
      results.errors.push(`Trigger creation failed: ${triggerResult.error}`);
    }

    // Step 5: Add comments
    console.log('[PEOPLE-SCHEMA] Adding table and column comments...');
    const commentsResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: addCommentsSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (commentsResult.success) {
      console.log('[PEOPLE-SCHEMA] ✓ Comments added successfully');
      results.comments_added = true;
    } else {
      console.error('[PEOPLE-SCHEMA] ✗ Failed to add comments:', commentsResult.error);
      results.errors.push(`Comments failed: ${commentsResult.error}`);
    }

    // Step 6: Verify schema creation by querying information_schema
    console.log('[PEOPLE-SCHEMA] Verifying schema creation...');
    const verifySchemaSQL = `
      SELECT schema_name
      FROM information_schema.schemata
      WHERE schema_name = 'people';
    `;

    const verifyResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: verifySchemaSQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (verifyResult.success && verifyResult.data?.rows?.length > 0) {
      console.log('[PEOPLE-SCHEMA] ✓ Schema verification successful');
    } else {
      console.log('[PEOPLE-SCHEMA] ⚠️ Schema verification failed or returned no results');
    }

    // Step 7: Verify table creation
    console.log('[PEOPLE-SCHEMA] Verifying table creation...');
    const verifyTableSQL = `
      SELECT table_name, table_schema
      FROM information_schema.tables
      WHERE table_schema = 'people' AND table_name = 'contact';
    `;

    const verifyTableResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: verifyTableSQL,
      mode: 'read',
      return_type: 'rows'
    });

    if (verifyTableResult.success && verifyTableResult.data?.rows?.length > 0) {
      console.log('[PEOPLE-SCHEMA] ✓ Table verification successful');
    } else {
      console.log('[PEOPLE-SCHEMA] ⚠️ Table verification failed or returned no results');
    }

    // Return comprehensive results
    const success = results.schema_created && results.table_created;
    return {
      success,
      message: success ? 'People schema and contact table created successfully' : 'Some operations failed during migration',
      schema_name: 'people',
      table_name: 'people.contact',
      results,
      verification: {
        schema_exists: verifyResult.success && verifyResult.data?.rows?.length > 0,
        table_exists: verifyTableResult.success && verifyTableResult.data?.rows?.length > 0
      }
    };

  } catch (error) {
    console.error('[PEOPLE-SCHEMA] ✗ Exception during migration:', error);
    return {
      success: false,
      error: error.message,
      message: 'Exception occurred during people schema migration',
      results
    };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  createPeopleSchema()
    .then(result => {
      console.log('\n[MIGRATION RESULT]', JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('\n[MIGRATION ERROR]', error);
      process.exit(1);
    });
}

export default createPeopleSchema;