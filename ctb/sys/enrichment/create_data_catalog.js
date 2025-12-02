#!/usr/bin/env node
/**
 * PLE Data Catalog: AI & Human Searchable Metadata Layer
 *
 * Creates a comprehensive, searchable data catalog that enables:
 * 1. AI searchability - Claude/LLMs can query metadata to understand schema
 * 2. Human searchability - Analysts can find fields by business meaning
 * 3. Unique IDs - Every column has a traceable identifier
 * 4. Format documentation - Data types, patterns, constraints documented
 */

const { Client } = require('pg');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '..', '..', '.env') });

async function createDataCatalog() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL || process.env.NEON_CONNECTION_STRING
  });

  try {
    await client.connect();
    console.log('='.repeat(80));
    console.log('PLE DATA CATALOG: Creating Searchable Metadata Layer');
    console.log('='.repeat(80));
    console.log();

    // =========================================================================
    // TASK 1: CREATE CATALOG SCHEMA
    // =========================================================================
    console.log('TASK 1: Creating catalog schema...');

    await client.query(`CREATE SCHEMA IF NOT EXISTS catalog`);
    await client.query(`COMMENT ON SCHEMA catalog IS 'Data catalog: searchable metadata for all PLE tables and columns'`);
    console.log('  Created: catalog schema');

    // =========================================================================
    // TASK 2: CREATE CATALOG TABLES
    // =========================================================================
    console.log('\nTASK 2: Creating catalog tables...');

    // 2A: Schema Registry
    await client.query(`
      CREATE TABLE IF NOT EXISTS catalog.schemas (
        schema_id VARCHAR(50) PRIMARY KEY,
        schema_name VARCHAR(50) NOT NULL,
        schema_type VARCHAR(20) NOT NULL,
        description TEXT NOT NULL,
        parent_schema VARCHAR(50),
        owner VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);
    console.log('  Created: catalog.schemas');

    // 2B: Table Registry
    await client.query(`
      CREATE TABLE IF NOT EXISTS catalog.tables (
        table_id VARCHAR(100) PRIMARY KEY,
        schema_id VARCHAR(50) NOT NULL REFERENCES catalog.schemas(schema_id),
        table_name VARCHAR(100) NOT NULL,
        table_type VARCHAR(20) NOT NULL,
        description TEXT NOT NULL,
        business_purpose TEXT,
        primary_key VARCHAR(100),
        foreign_keys JSONB,
        row_count_approx INT,
        data_source VARCHAR(100),
        refresh_frequency VARCHAR(50),
        owner VARCHAR(100),
        tags TEXT[],
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_tables_schema ON catalog.tables(schema_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_tables_tags ON catalog.tables USING GIN(tags)`);
    console.log('  Created: catalog.tables');

    // 2C: Column Registry
    await client.query(`
      CREATE TABLE IF NOT EXISTS catalog.columns (
        column_id VARCHAR(200) PRIMARY KEY,
        table_id VARCHAR(100) NOT NULL REFERENCES catalog.tables(table_id),
        column_name VARCHAR(100) NOT NULL,
        ordinal_position INT,
        data_type VARCHAR(50) NOT NULL,
        max_length INT,
        is_nullable BOOLEAN DEFAULT TRUE,
        default_value TEXT,
        description TEXT NOT NULL,
        business_name VARCHAR(100),
        business_definition TEXT,
        format_pattern VARCHAR(100),
        format_example VARCHAR(200),
        valid_values TEXT[],
        validation_rule TEXT,
        is_primary_key BOOLEAN DEFAULT FALSE,
        is_foreign_key BOOLEAN DEFAULT FALSE,
        references_column VARCHAR(200),
        pii_classification VARCHAR(20),
        data_sensitivity VARCHAR(20),
        source_system VARCHAR(100),
        source_field VARCHAR(200),
        transformation_logic TEXT,
        tags TEXT[],
        synonyms TEXT[],
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_columns_table ON catalog.columns(table_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_columns_tags ON catalog.columns USING GIN(tags)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_columns_synonyms ON catalog.columns USING GIN(synonyms)`);
    console.log('  Created: catalog.columns');

    // 2D: Relationship Registry
    await client.query(`
      CREATE TABLE IF NOT EXISTS catalog.relationships (
        relationship_id SERIAL PRIMARY KEY,
        from_table_id VARCHAR(100) NOT NULL,
        from_column_id VARCHAR(200) NOT NULL,
        to_table_id VARCHAR(100) NOT NULL,
        to_column_id VARCHAR(200) NOT NULL,
        relationship_type VARCHAR(20) NOT NULL,
        relationship_name VARCHAR(100),
        description TEXT,
        is_enforced BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    await client.query(`CREATE INDEX IF NOT EXISTS idx_rel_from ON catalog.relationships(from_table_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_rel_to ON catalog.relationships(to_table_id)`);
    console.log('  Created: catalog.relationships');

    // =========================================================================
    // TASK 3: POPULATE SCHEMA REGISTRY
    // =========================================================================
    console.log('\nTASK 3: Populating schema registry...');

    await client.query(`DELETE FROM catalog.schemas`);

    await client.query(`
      INSERT INTO catalog.schemas (schema_id, schema_name, schema_type, description, parent_schema, owner) VALUES
      ('company', 'company', 'hub', 'Hub: The company record. All enrichment lands here. The product we build.', NULL, 'PLE System'),
      ('dol', 'dol', 'spoke', 'Spoke: DOL federal data - Form 5500, Schedule A, violations. Enriches company via EIN.', 'company', 'PLE System'),
      ('people', 'people', 'spoke', 'Spoke: People as sensors - slots, occupants, movement tracking. Contains Talent Flow engine.', 'company', 'PLE System'),
      ('clay', 'clay', 'spoke', 'Spoke: Clay.com enrichment engine - raw data intake from external enrichment.', 'company', 'PLE System'),
      ('intake', 'intake', 'staging', 'Quarantine: Invalid records pending human review before promotion to core tables.', NULL, 'PLE System'),
      ('catalog', 'catalog', 'catalog', 'Metadata layer: Searchable documentation of all schemas, tables, and columns.', NULL, 'PLE System')
      ON CONFLICT (schema_id) DO UPDATE SET
        description = EXCLUDED.description,
        updated_at = NOW()
    `);
    console.log('  Populated: 6 schemas');

    // =========================================================================
    // TASK 4: POPULATE TABLE REGISTRY
    // =========================================================================
    console.log('\nTASK 4: Populating table registry...');

    // First, get actual tables from database
    const actualTables = await client.query(`
      SELECT table_schema, table_name
      FROM information_schema.tables
      WHERE table_schema IN ('company', 'dol', 'people', 'clay', 'intake')
      AND table_type = 'BASE TABLE'
      ORDER BY table_schema, table_name
    `);

    // Clear existing
    await client.query(`DELETE FROM catalog.columns`);
    await client.query(`DELETE FROM catalog.tables`);

    // Insert table metadata
    const tableMetadata = {
      'company.company_master': {
        type: 'core',
        desc: 'Hub table: The company record. All enrichment lands here.',
        purpose: 'Central company record containing firmographics, federal IDs, and enrichment data. This is the PRODUCT we build - everything else feeds this table.',
        pk: 'id',
        source: 'Clay, DOL, Manual',
        refresh: 'real-time',
        tags: ['hub', 'company', 'master', 'firmographics', 'ein', 'enrichment']
      },
      'company.company_events': {
        type: 'sidecar',
        desc: 'Company-level signals and events',
        purpose: 'Tracks significant company events: funding, acquisitions, layoffs, leadership changes. Used for BIT scoring.',
        pk: 'id',
        source: 'Clay, News, Manual',
        refresh: 'daily',
        tags: ['events', 'signals', 'funding', 'acquisitions', 'bit']
      },
      'company.company_sidecar': {
        type: 'sidecar',
        desc: 'Extended company attributes',
        purpose: 'Additional company fields that dont fit in company_master. Overflow for enrichment data.',
        pk: 'id',
        source: 'Various',
        refresh: 'real-time',
        tags: ['sidecar', 'extended', 'attributes']
      },
      'company.company_slots': {
        type: 'core',
        desc: 'Executive position slots per company',
        purpose: 'Tracks CEO, CFO, HR slots per company. Alternative to people.company_slot.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['slots', 'positions', 'executives']
      },
      'company.pipeline_events': {
        type: 'audit',
        desc: 'Pipeline activity audit log',
        purpose: 'Tracks all pipeline operations: intake, validation, enrichment, promotion.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['audit', 'pipeline', 'events', 'log']
      },
      'company.pipeline_errors': {
        type: 'audit',
        desc: 'Pipeline error tracking',
        purpose: 'Records errors that occur during pipeline processing for debugging.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['errors', 'pipeline', 'debugging']
      },
      'dol.form_5500': {
        type: 'core',
        desc: 'DOL Form 5500 filings for large plans (100+ participants)',
        purpose: 'Federal retirement plan filings. Contains EIN, participant counts, plan assets. Joins to company via EIN. Source of renewal date intelligence.',
        pk: 'ack_id',
        source: 'DOL EBSA',
        refresh: 'annual',
        tags: ['dol', 'federal', '5500', 'retirement', 'ein', 'erisa', 'pension']
      },
      'dol.form_5500_sf': {
        type: 'core',
        desc: 'DOL Form 5500-SF filings for small plans (<100 participants)',
        purpose: 'Short form federal retirement plan filings. Same purpose as form_5500 but for smaller plans.',
        pk: 'ack_id',
        source: 'DOL EBSA',
        refresh: 'annual',
        tags: ['dol', 'federal', '5500', 'retirement', 'ein', 'small-plan']
      },
      'dol.schedule_a': {
        type: 'core',
        desc: 'DOL Schedule A: Insurance contract information',
        purpose: 'Insurance policy details including carrier, policy dates, premiums. CRITICAL: Contains policy end dates used for renewal timing and BIT scoring.',
        pk: 'ack_id',
        source: 'DOL EBSA',
        refresh: 'annual',
        tags: ['dol', 'insurance', 'renewal', 'carrier', 'premium', 'schedule-a', 'bit']
      },
      'dol.violations': {
        type: 'core',
        desc: 'DOL ERISA violations and penalties',
        purpose: 'ERISA compliance violations. Companies with violations may need benefits advisory help - this is an opportunity signal.',
        pk: 'id',
        source: 'DOL EBSA',
        refresh: 'quarterly',
        tags: ['dol', 'violations', 'erisa', 'compliance', 'penalties', 'risk']
      },
      'dol.form_5500_staging': {
        type: 'staging',
        desc: 'Staging table for Form 5500 CSV imports',
        purpose: 'Temporary holding table for raw CSV data before processing into main tables.',
        pk: null,
        source: 'DOL CSV Import',
        refresh: 'on-demand',
        tags: ['staging', 'import', 'csv']
      },
      'dol.form_5500_sf_staging': {
        type: 'staging',
        desc: 'Staging table for Form 5500-SF CSV imports',
        purpose: 'Temporary holding table for raw Form 5500-SF data.',
        pk: null,
        source: 'DOL CSV Import',
        refresh: 'on-demand',
        tags: ['staging', 'import', 'csv']
      },
      'dol.schedule_a_staging': {
        type: 'staging',
        desc: 'Staging table for Schedule A CSV imports',
        purpose: 'Temporary holding table for raw Schedule A data.',
        pk: null,
        source: 'DOL CSV Import',
        refresh: 'on-demand',
        tags: ['staging', 'import', 'csv']
      },
      'people.company_slot': {
        type: 'core',
        desc: 'CEO/CFO/HR slots - the chairs, not the occupants',
        purpose: 'Three slots per company for key decision makers. Phone belongs to slot, not person. When occupant leaves, slot remains.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['slots', 'ceo', 'cfo', 'hr', 'chairs', 'phone']
      },
      'people.people_master': {
        type: 'core',
        desc: 'People records - minimal, transient occupants',
        purpose: 'Sensor data only: name, title, LinkedIn. People fill slots. They come and go. We do NOT enrich people - we enrich companies.',
        pk: 'id',
        source: 'Clay',
        refresh: 'real-time',
        tags: ['people', 'contacts', 'linkedin', 'occupants', 'sensors']
      },
      'people.people_invalid': {
        type: 'staging',
        desc: 'Invalid person records',
        purpose: 'Person records that failed validation. Pending review or permanent rejection.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['invalid', 'validation', 'quarantine']
      },
      'people.people_resolution_queue': {
        type: 'staging',
        desc: 'Duplicate person resolution queue',
        purpose: 'Suspected duplicate person records pending human review and merge decision.',
        pk: 'id',
        source: 'Internal',
        refresh: 'real-time',
        tags: ['duplicates', 'resolution', 'merge']
      },
      'people.people_sidecar': {
        type: 'sidecar',
        desc: 'Extended person attributes',
        purpose: 'Additional person fields. Minimal - we dont invest in person enrichment.',
        pk: 'id',
        source: 'Various',
        refresh: 'real-time',
        tags: ['sidecar', 'extended']
      },
      'people.person_movement_history': {
        type: 'audit',
        desc: 'Talent Flow audit trail - movement detection log',
        purpose: 'Records every detected job change, title change, or contact loss. Core of Talent Flow engine. Used for company discovery.',
        pk: 'id',
        source: 'Talent Flow',
        refresh: 'real-time',
        tags: ['movement', 'talent-flow', 'job-change', 'audit', 'discovery']
      },
      'people.person_scores': {
        type: 'sidecar',
        desc: 'BIT (Buyer Intent Threshold) scores per person',
        purpose: 'Calculated scores indicating likelihood of engagement. Higher score = hotter lead.',
        pk: 'id',
        source: 'Calculated',
        refresh: 'daily',
        tags: ['bit', 'scores', 'intent', 'priority']
      },
      'clay.company_raw': {
        type: 'staging',
        desc: 'Raw company data from Clay.com enrichment',
        purpose: 'Inbound company data from Clay before validation and promotion to company_master.',
        pk: 'id',
        source: 'Clay.com',
        refresh: 'on-demand',
        tags: ['clay', 'enrichment', 'raw', 'staging', 'companies']
      },
      'clay.people_raw': {
        type: 'staging',
        desc: 'Raw people data from Clay.com enrichment',
        purpose: 'Inbound contact data from Clay before validation and promotion to people_master.',
        pk: 'id',
        source: 'Clay.com',
        refresh: 'on-demand',
        tags: ['clay', 'enrichment', 'raw', 'staging', 'contacts']
      },
      'intake.quarantine': {
        type: 'staging',
        desc: 'Invalid records pending human review',
        purpose: 'Records that failed validation. Stored with rejection reason. Human reviews and either fixes/promotes or permanently rejects.',
        pk: 'id',
        source: 'Various',
        refresh: 'real-time',
        tags: ['quarantine', 'validation', 'errors', 'review', 'staging']
      },
      'intake.company_raw_intake': {
        type: 'staging',
        desc: 'Raw company intake staging',
        purpose: 'First landing zone for external company data. Validated before moving to company_master.',
        pk: 'id',
        source: 'CSV Upload',
        refresh: 'on-demand',
        tags: ['intake', 'staging', 'companies', 'raw']
      },
      'intake.company_raw_wv': {
        type: 'staging',
        desc: 'West Virginia company raw data',
        purpose: 'WV-specific company intake data.',
        pk: 'id',
        source: 'WV State Data',
        refresh: 'on-demand',
        tags: ['intake', 'staging', 'wv', 'west-virginia']
      },
      'intake.people_raw_intake': {
        type: 'staging',
        desc: 'Raw people intake staging',
        purpose: 'First landing zone for external contact data.',
        pk: 'id',
        source: 'CSV Upload',
        refresh: 'on-demand',
        tags: ['intake', 'staging', 'people', 'raw']
      },
      'intake.people_raw_wv': {
        type: 'staging',
        desc: 'West Virginia people raw data',
        purpose: 'WV-specific people intake data.',
        pk: 'id',
        source: 'WV State Data',
        refresh: 'on-demand',
        tags: ['intake', 'staging', 'wv', 'west-virginia']
      }
    };

    let tableCount = 0;
    for (const row of actualTables.rows) {
      const tableId = `${row.table_schema}.${row.table_name}`;
      const meta = tableMetadata[tableId] || {
        type: 'core',
        desc: `Table ${row.table_name} in ${row.table_schema} schema`,
        purpose: null,
        pk: 'id',
        source: 'Unknown',
        refresh: 'unknown',
        tags: [row.table_schema]
      };

      // Get row count
      let rowCount = null;
      try {
        const countResult = await client.query(`SELECT COUNT(*) FROM "${row.table_schema}"."${row.table_name}"`);
        rowCount = parseInt(countResult.rows[0].count);
      } catch (e) {
        // Ignore count errors
      }

      await client.query(`
        INSERT INTO catalog.tables (table_id, schema_id, table_name, table_type, description, business_purpose, primary_key, row_count_approx, data_source, refresh_frequency, owner, tags)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'PLE System', $11)
        ON CONFLICT (table_id) DO UPDATE SET
          description = EXCLUDED.description,
          business_purpose = EXCLUDED.business_purpose,
          row_count_approx = EXCLUDED.row_count_approx,
          tags = EXCLUDED.tags,
          updated_at = NOW()
      `, [
        tableId,
        row.table_schema,
        row.table_name,
        meta.type,
        meta.desc,
        meta.purpose,
        meta.pk,
        rowCount,
        meta.source,
        meta.refresh,
        meta.tags
      ]);
      tableCount++;
    }
    console.log(`  Populated: ${tableCount} tables`);

    // =========================================================================
    // TASK 5: POPULATE COLUMN REGISTRY (Auto-discover from information_schema)
    // =========================================================================
    console.log('\nTASK 5: Populating column registry...');

    // Get all columns from database
    const actualColumns = await client.query(`
      SELECT
        c.table_schema,
        c.table_name,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.character_maximum_length,
        c.is_nullable,
        c.column_default,
        (
          SELECT COUNT(*) > 0
          FROM information_schema.table_constraints tc
          JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
          WHERE tc.table_schema = c.table_schema
            AND tc.table_name = c.table_name
            AND kcu.column_name = c.column_name
            AND tc.constraint_type = 'PRIMARY KEY'
        ) as is_primary_key
      FROM information_schema.columns c
      WHERE c.table_schema IN ('company', 'dol', 'people', 'clay', 'intake')
      ORDER BY c.table_schema, c.table_name, c.ordinal_position
    `);

    // Key column metadata (business descriptions)
    const columnMetadata = {
      // company.company_master
      'company.company_master.company_unique_id': {
        businessName: 'Company UID',
        businessDef: 'Internal business key. Used for all cross-table joins within PLE system.',
        formatPattern: 'CMP-XXXXXX',
        formatExample: 'CMP-000001',
        tags: ['uid', 'business-key', 'unique'],
        synonyms: ['company_id', 'company_key']
      },
      'company.company_master.ein': {
        businessName: 'EIN',
        businessDef: 'Federal passport. 9-digit IRS tax ID. Joins to DOL data. Format: XXXXXXXXX (no dashes).',
        formatPattern: 'XXXXXXXXX',
        formatExample: '123456789',
        tags: ['ein', 'federal', 'tax-id', 'irs', 'dol'],
        synonyms: ['employer_id', 'tax_id', 'fein'],
        pii: 'medium',
        sensitivity: 'confidential',
        source: 'DOL Form 5500'
      },
      'company.company_master.company_name': {
        businessName: 'Company Name',
        businessDef: 'Official business name as registered or commonly known.',
        tags: ['name', 'company', 'business-name'],
        synonyms: ['business_name', 'org_name', 'organization']
      },
      'company.company_master.linkedin_url': {
        businessName: 'LinkedIn URL',
        businessDef: 'Link to company LinkedIn page. Used for verification and enrichment.',
        formatExample: 'https://linkedin.com/company/acme-corp',
        tags: ['linkedin', 'social', 'url'],
        synonyms: ['li_url', 'linkedin_profile']
      },
      'company.company_master.website_url': {
        businessName: 'Website',
        businessDef: 'Primary company website. Used for email domain extraction.',
        formatExample: 'https://acme.com',
        tags: ['website', 'url', 'domain'],
        synonyms: ['homepage', 'web_address']
      },
      'company.company_master.email_pattern': {
        businessName: 'Email Pattern',
        businessDef: 'Template for generating employee emails. e.g., {first}.{last}@ means john.smith@domain.com',
        formatExample: '{f}{last}@',
        tags: ['email', 'pattern', 'template'],
        synonyms: ['email_format', 'email_template']
      },
      'company.company_master.address_state': {
        businessName: 'State',
        businessDef: 'US state code. Must be in ICP: PA, VA, MD, OH, WV, KY.',
        formatPattern: 'XX',
        formatExample: 'PA',
        tags: ['state', 'address', 'icp', 'territory'],
        synonyms: ['us_state', 'state_code']
      },
      // dol.form_5500
      'dol.form_5500.ack_id': {
        businessName: 'ACK ID',
        businessDef: 'Primary key from DOL. Unique identifier for each Form 5500 filing.',
        formatPattern: 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        tags: ['ack_id', 'filing-id', 'dol'],
        synonyms: ['acknowledgement_id', 'filing_id']
      },
      'dol.form_5500.sponsor_dfe_ein': {
        businessName: 'Sponsor EIN',
        businessDef: 'Federal tax ID of plan sponsor. Key join field to company_master.ein.',
        formatPattern: 'XXXXXXXXX',
        tags: ['ein', 'sponsor', 'federal', 'tax-id'],
        synonyms: ['employer_ein', 'company_ein'],
        pii: 'medium'
      },
      'dol.form_5500.sponsor_dfe_name': {
        businessName: 'Sponsor Name',
        businessDef: 'Official name of plan sponsor. Used for fuzzy matching to company_master.',
        tags: ['sponsor', 'name', 'company'],
        synonyms: ['company_name', 'employer_name']
      },
      'dol.form_5500.tot_partcp_boy_cnt': {
        businessName: 'Participants BOY',
        businessDef: 'Number of plan participants at beginning of year. Indicator of company size.',
        tags: ['participants', 'employees', 'headcount'],
        synonyms: ['employee_count', 'member_count']
      },
      // dol.schedule_a (THE GOLD)
      'dol.schedule_a.insurance_company_name': {
        businessName: 'Carrier Name',
        businessDef: 'Insurance company providing coverage. Used for competitive intelligence.',
        tags: ['carrier', 'insurance', 'provider'],
        synonyms: ['insurer', 'insurance_company']
      },
      'dol.schedule_a.covered_lives': {
        businessName: 'Covered Lives',
        businessDef: 'Number of people covered under the policy. Key sizing metric.',
        tags: ['coverage', 'lives', 'headcount'],
        synonyms: ['employees_covered', 'members']
      },
      // people.company_slot
      'people.company_slot.slot_type': {
        businessName: 'Slot Type',
        businessDef: 'The chair type: CEO, CFO, or HR. Three per company. Phone stays with slot.',
        formatExample: 'CEO',
        tags: ['slot', 'role', 'position'],
        synonyms: ['chair_type', 'role_type']
      },
      'people.company_slot.person_unique_id': {
        businessName: 'Person UID',
        businessDef: 'Current occupant. NULL if vacant. Changes when person moves.',
        tags: ['person', 'occupant'],
        synonyms: ['occupant_id', 'contact_id']
      },
      // people.people_master
      'people.people_master.linkedin_url': {
        businessName: 'LinkedIn URL',
        businessDef: 'CRITICAL: This is the key we check in Talent Flow sweeps. Must have for movement detection.',
        formatExample: 'https://linkedin.com/in/johnsmith',
        tags: ['linkedin', 'social', 'profile', 'talent-flow'],
        synonyms: ['li_url', 'linkedin_profile']
      },
      'people.people_master.title': {
        businessName: 'Title',
        businessDef: 'Job title. Used in Talent Flow to detect title changes. Maps to slot type.',
        tags: ['title', 'job', 'position'],
        synonyms: ['job_title', 'role', 'position']
      }
    };

    let columnCount = 0;
    for (const col of actualColumns.rows) {
      const tableId = `${col.table_schema}.${col.table_name}`;
      const columnId = `${tableId}.${col.column_name}`;

      // Check if table exists in catalog
      const tableExists = await client.query(`SELECT 1 FROM catalog.tables WHERE table_id = $1`, [tableId]);
      if (tableExists.rows.length === 0) continue;

      const meta = columnMetadata[columnId] || {};

      // Generate basic description from column name
      const basicDesc = col.column_name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());

      await client.query(`
        INSERT INTO catalog.columns (
          column_id, table_id, column_name, ordinal_position,
          data_type, max_length, is_nullable, default_value,
          description, business_name, business_definition,
          format_pattern, format_example,
          is_primary_key, is_foreign_key,
          pii_classification, data_sensitivity,
          source_system, tags, synonyms
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
        ON CONFLICT (column_id) DO UPDATE SET
          data_type = EXCLUDED.data_type,
          max_length = EXCLUDED.max_length,
          is_nullable = EXCLUDED.is_nullable,
          business_name = EXCLUDED.business_name,
          business_definition = EXCLUDED.business_definition,
          tags = EXCLUDED.tags,
          synonyms = EXCLUDED.synonyms,
          updated_at = NOW()
      `, [
        columnId,
        tableId,
        col.column_name,
        col.ordinal_position,
        col.data_type,
        col.character_maximum_length,
        col.is_nullable === 'YES',
        col.column_default,
        meta.businessDef || basicDesc,
        meta.businessName || null,
        meta.businessDef || null,
        meta.formatPattern || null,
        meta.formatExample || null,
        col.is_primary_key,
        false, // FK detection would require additional query
        meta.pii || 'none',
        meta.sensitivity || 'internal',
        meta.source || col.table_schema,
        meta.tags || [col.table_schema],
        meta.synonyms || null
      ]);
      columnCount++;
    }
    console.log(`  Populated: ${columnCount} columns`);

    // =========================================================================
    // TASK 6: CREATE SEARCH FUNCTIONS
    // =========================================================================
    console.log('\nTASK 6: Creating search functions...');

    // Full-text search function
    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.search_columns(
        p_query TEXT,
        p_limit INT DEFAULT 20
      ) RETURNS TABLE (
        column_id VARCHAR(200),
        table_id VARCHAR(100),
        column_name VARCHAR(100),
        description TEXT,
        business_name VARCHAR(100),
        data_type VARCHAR(50),
        relevance FLOAT
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id,
          c.table_id,
          c.column_name,
          c.description,
          c.business_name,
          c.data_type,
          ts_rank(
            to_tsvector('english',
              c.column_name || ' ' ||
              COALESCE(c.description, '') || ' ' ||
              COALESCE(c.business_name, '') || ' ' ||
              COALESCE(c.business_definition, '') || ' ' ||
              COALESCE(array_to_string(c.synonyms, ' '), '') || ' ' ||
              COALESCE(array_to_string(c.tags, ' '), '')
            ),
            plainto_tsquery('english', p_query)
          ) as relevance
        FROM catalog.columns c
        WHERE to_tsvector('english',
              c.column_name || ' ' ||
              COALESCE(c.description, '') || ' ' ||
              COALESCE(c.business_name, '') || ' ' ||
              COALESCE(c.business_definition, '') || ' ' ||
              COALESCE(array_to_string(c.synonyms, ' '), '') || ' ' ||
              COALESCE(array_to_string(c.tags, ' '), '')
          ) @@ plainto_tsquery('english', p_query)
        ORDER BY relevance DESC
        LIMIT p_limit;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Created: catalog.search_columns()');

    // Search by tag
    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.search_by_tag(
        p_tag TEXT
      ) RETURNS TABLE (
        column_id VARCHAR(200),
        table_id VARCHAR(100),
        column_name VARCHAR(100),
        description TEXT,
        tags TEXT[]
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id,
          c.table_id,
          c.column_name,
          c.description,
          c.tags
        FROM catalog.columns c
        WHERE p_tag = ANY(c.tags)
        ORDER BY c.table_id, c.ordinal_position;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Created: catalog.search_by_tag()');

    // Get table details
    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.get_table_details(p_table_id VARCHAR)
      RETURNS TABLE (
        column_id VARCHAR(200),
        column_name VARCHAR(100),
        business_name VARCHAR(100),
        data_type VARCHAR(50),
        description TEXT,
        format_example VARCHAR(200),
        is_nullable BOOLEAN,
        is_primary_key BOOLEAN,
        is_foreign_key BOOLEAN
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          c.column_id,
          c.column_name,
          c.business_name,
          c.data_type,
          c.description,
          c.format_example,
          c.is_nullable,
          c.is_primary_key,
          c.is_foreign_key
        FROM catalog.columns c
        WHERE c.table_id = p_table_id
        ORDER BY c.ordinal_position;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Created: catalog.get_table_details()');

    // AI context dump
    await client.query(`
      CREATE OR REPLACE FUNCTION catalog.get_ai_context(p_schema VARCHAR DEFAULT NULL)
      RETURNS TEXT AS $$
      DECLARE
        v_context TEXT := '';
        v_schema RECORD;
        v_table RECORD;
        v_column RECORD;
      BEGIN
        v_context := '# PLE Database Schema Reference' || E'\n\n';

        FOR v_schema IN
          SELECT * FROM catalog.schemas
          WHERE p_schema IS NULL OR schema_id = p_schema
          ORDER BY schema_type, schema_id
        LOOP
          v_context := v_context || '## Schema: ' || v_schema.schema_name ||
                       ' (' || v_schema.schema_type || ')' || E'\n';
          v_context := v_context || v_schema.description || E'\n\n';

          FOR v_table IN
            SELECT * FROM catalog.tables
            WHERE schema_id = v_schema.schema_id
            ORDER BY table_name
          LOOP
            v_context := v_context || '### Table: ' || v_table.table_name || E'\n';
            v_context := v_context || v_table.description || E'\n';
            v_context := v_context || 'Business Purpose: ' || COALESCE(v_table.business_purpose, 'N/A') || E'\n';
            v_context := v_context || 'Tags: ' || array_to_string(v_table.tags, ', ') || E'\n\n';
            v_context := v_context || '| Column | Type | Description |' || E'\n';
            v_context := v_context || '|--------|------|-------------|' || E'\n';

            FOR v_column IN
              SELECT * FROM catalog.columns
              WHERE table_id = v_table.table_id
              ORDER BY ordinal_position
            LOOP
              v_context := v_context || '| ' || v_column.column_name ||
                           ' | ' || v_column.data_type ||
                           ' | ' || LEFT(v_column.description, 80) || ' |' || E'\n';
            END LOOP;

            v_context := v_context || E'\n';
          END LOOP;
        END LOOP;

        RETURN v_context;
      END;
      $$ LANGUAGE plpgsql;
    `);
    console.log('  Created: catalog.get_ai_context()');

    // =========================================================================
    // TASK 7: CREATE SEARCH VIEWS
    // =========================================================================
    console.log('\nTASK 7: Creating search views...');

    await client.query(`
      CREATE OR REPLACE VIEW catalog.v_searchable_columns AS
      SELECT
        c.column_id,
        c.table_id,
        s.schema_name,
        s.schema_type,
        t.table_name,
        t.table_type,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.max_length,
        c.is_nullable,
        c.description,
        c.business_name,
        c.business_definition,
        c.format_pattern,
        c.format_example,
        c.is_primary_key,
        c.is_foreign_key,
        c.references_column,
        c.source_system,
        c.tags,
        c.synonyms
      FROM catalog.columns c
      JOIN catalog.tables t ON t.table_id = c.table_id
      JOIN catalog.schemas s ON s.schema_id = t.schema_id
    `);
    console.log('  Created: catalog.v_searchable_columns');

    await client.query(`
      CREATE OR REPLACE VIEW catalog.v_ai_reference AS
      SELECT
        column_id,
        column_name,
        business_name,
        data_type || CASE WHEN max_length IS NOT NULL THEN '(' || max_length || ')' ELSE '' END as full_type,
        description,
        format_example,
        CASE WHEN is_primary_key THEN 'PK'
             WHEN is_foreign_key THEN 'FK -> ' || references_column
             ELSE '' END as key_info,
        array_to_string(tags, ', ') as tags
      FROM catalog.columns
      ORDER BY table_id, ordinal_position
    `);
    console.log('  Created: catalog.v_ai_reference');

    await client.query(`
      CREATE OR REPLACE VIEW catalog.v_schema_summary AS
      SELECT
        s.schema_id,
        s.schema_name,
        s.schema_type,
        s.description,
        COUNT(DISTINCT t.table_id) as table_count,
        SUM(t.row_count_approx) as total_rows,
        (SELECT COUNT(*) FROM catalog.columns c WHERE c.table_id IN (SELECT table_id FROM catalog.tables WHERE schema_id = s.schema_id)) as column_count
      FROM catalog.schemas s
      LEFT JOIN catalog.tables t ON t.schema_id = s.schema_id
      GROUP BY s.schema_id, s.schema_name, s.schema_type, s.description
      ORDER BY s.schema_type, s.schema_name
    `);
    console.log('  Created: catalog.v_schema_summary');

    // Log to migration_log
    await client.query(`
      INSERT INTO public.migration_log (migration_name, step, status, details)
      VALUES ('data_catalog', 'CREATE_CATALOG', 'SUCCESS', 'Data catalog schema created with ' || $1 || ' tables and ' || $2 || ' columns')
    `, [tableCount, columnCount]);

    // =========================================================================
    // FINAL SUMMARY
    // =========================================================================
    console.log('\n' + '='.repeat(80));
    console.log('DATA CATALOG CREATED SUCCESSFULLY');
    console.log('='.repeat(80));

    const summary = await client.query(`SELECT * FROM catalog.v_schema_summary`);
    console.log('\nCatalog Summary:');
    console.log('| Schema | Type | Tables | Columns | Rows |');
    console.log('|--------|------|--------|---------|------|');
    for (const row of summary.rows) {
      console.log(`| ${row.schema_name} | ${row.schema_type} | ${row.table_count} | ${row.column_count} | ${(row.total_rows || 0).toLocaleString()} |`);
    }

    console.log('\nSearch Functions:');
    console.log('  - catalog.search_columns(query)   -- Full-text search');
    console.log('  - catalog.search_by_tag(tag)      -- Tag-based search');
    console.log('  - catalog.get_table_details(id)   -- Table column list');
    console.log('  - catalog.get_ai_context(schema)  -- AI-friendly dump');

    console.log('\nExample Queries:');
    console.log("  SELECT * FROM catalog.search_columns('renewal date');");
    console.log("  SELECT * FROM catalog.search_by_tag('dol');");
    console.log("  SELECT * FROM catalog.get_table_details('company.company_master');");
    console.log("  SELECT catalog.get_ai_context('company');");

  } catch (error) {
    console.error('\nError:', error.message);
    throw error;
  } finally {
    await client.end();
  }
}

createDataCatalog().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
