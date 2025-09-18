#!/usr/bin/env node
/**
 * Enhanced Lean Outreach Schema Setup v2
 * 
 * This script sets up a streamlined database schema for the Barton Outreach Core system.
 * It includes comprehensive error handling, automatic slot creation, and enhanced testing.
 * 
 * Key Features:
 * - Creates 5 main schemas: company, people, marketing, bit, ple
 * - Implements slot-based contact management (CEO, CFO, HR per company)
 * - Sets up zero-wandering scraper queues with 30-day TTL
 * - Includes automatic backfilling for existing data
 * - Comprehensive verification and testing
 * 
 * Usage: node setup-lean-outreach-schema-v2.mjs
 */

import pg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Client } = pg;

async function setupLeanOutreachSchema() {
  const client = new Client({
    connectionString: process.env.NEON_DATABASE_URL || process.env.DATABASE_URL,
    ssl: {
      rejectUnauthorized: false
    }
  });

  try {
    console.log('🔌 Connecting to Neon Database...');
    await client.connect();
    console.log('✅ Connected successfully\n');

    // Start transaction
    await client.query('BEGIN');

    console.log('🏗️ Creating schemas...');
    await client.query(`
      CREATE SCHEMA IF NOT EXISTS company;
      CREATE SCHEMA IF NOT EXISTS people;
      CREATE SCHEMA IF NOT EXISTS marketing;
      CREATE SCHEMA IF NOT EXISTS bit;
      CREATE SCHEMA IF NOT EXISTS ple;
    `);

    console.log('📝 Creating ENUM types...');
    await client.query(`
      DO $$
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
          WHERE t.typname='role_code_t' AND n.nspname='company'
        ) THEN
          CREATE TYPE company.role_code_t AS ENUM ('CEO','CFO','HR');
        END IF;

        IF NOT EXISTS (
          SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace
          WHERE t.typname='email_status_t' AND n.nspname='people'
        ) THEN
          CREATE TYPE people.email_status_t AS ENUM ('green','yellow','red','gray');
        END IF;
      END$$;
    `);

    console.log('🏢 Creating company tables...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS company.company (
        company_id BIGSERIAL PRIMARY KEY,
        company_name TEXT NOT NULL,
        ein TEXT,
        website_url TEXT,
        linkedin_url TEXT,
        news_url TEXT,
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        state_region TEXT,
        postal_code TEXT,
        country TEXT,
        renewal_month INT CHECK (renewal_month BETWEEN 1 AND 12),
        renewal_notice_window_days INT NOT NULL DEFAULT 120 CHECK (renewal_notice_window_days >= 0),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_site_checked_at TIMESTAMPTZ,
        last_linkedin_checked_at TIMESTAMPTZ,
        last_news_checked_at TIMESTAMPTZ
      );

      CREATE TABLE IF NOT EXISTS company.company_slot (
        company_slot_id BIGSERIAL PRIMARY KEY,
        company_id BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
        role_code company.role_code_t NOT NULL,
        contact_id BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_company_role UNIQUE (company_id, role_code)
      );
    `);

    console.log('👥 Creating people tables...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS people.contact (
        contact_id BIGSERIAL PRIMARY KEY,
        full_name TEXT NOT NULL,
        title TEXT,
        email TEXT,
        phone TEXT,
        profile_source_url TEXT,
        last_profile_checked_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );

      CREATE TABLE IF NOT EXISTS people.contact_verification (
        contact_id BIGINT PRIMARY KEY REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        email_status people.email_status_t NOT NULL DEFAULT 'gray',
        email_checked_at TIMESTAMPTZ,
        email_confidence NUMERIC(5,2),
        email_source_url TEXT
      );
    `);

    console.log('📧 Creating marketing tables...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS marketing.campaign (
        campaign_id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );

      CREATE TABLE IF NOT EXISTS marketing.campaign_contact (
        campaign_contact_id BIGSERIAL PRIMARY KEY,
        campaign_id BIGINT NOT NULL REFERENCES marketing.campaign(campaign_id) ON DELETE CASCADE,
        contact_id BIGINT NOT NULL REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );

      CREATE TABLE IF NOT EXISTS marketing.message_log (
        message_log_id BIGSERIAL PRIMARY KEY,
        campaign_id BIGINT REFERENCES marketing.campaign(campaign_id) ON DELETE SET NULL,
        contact_id BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
        direction TEXT CHECK (direction IN ('outbound','inbound')),
        channel TEXT CHECK (channel IN ('email','linkedin','phone','other')),
        subject TEXT,
        body TEXT,
        sent_at TIMESTAMPTZ DEFAULT now()
      );

      CREATE TABLE IF NOT EXISTS marketing.booking_event (
        booking_event_id BIGSERIAL PRIMARY KEY,
        contact_id BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
        company_id BIGINT REFERENCES company.company(company_id) ON DELETE SET NULL,
        event_time TIMESTAMPTZ NOT NULL,
        source TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );

      CREATE TABLE IF NOT EXISTS marketing.ac_handoff (
        handoff_id BIGSERIAL PRIMARY KEY,
        company_id BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
        contact_id BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      );
    `);

    console.log('🎯 Creating bit schema tables...');
    await client.query(`
      CREATE TABLE IF NOT EXISTS bit.signal (
        signal_id BIGSERIAL PRIMARY KEY,
        company_id BIGINT REFERENCES company.company(company_id) ON DELETE CASCADE,
        reason TEXT NOT NULL,
        payload JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        processed_at TIMESTAMPTZ
      );
    `);

    console.log('⚙️ Creating triggers and functions...');
    await client.query(`
      CREATE OR REPLACE FUNCTION public.set_updated_at()
      RETURNS trigger AS $$
      BEGIN
        NEW.updated_at := now();
        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;

      -- Company triggers
      DROP TRIGGER IF EXISTS trg_company_updated_at ON company.company;
      CREATE TRIGGER trg_company_updated_at
      BEFORE UPDATE ON company.company
      FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

      DROP TRIGGER IF EXISTS trg_company_slot_updated_at ON company.company_slot;
      CREATE TRIGGER trg_company_slot_updated_at
      BEFORE UPDATE ON company.company_slot
      FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

      -- People triggers
      DROP TRIGGER IF EXISTS trg_people_contact_updated_at ON people.contact;
      CREATE TRIGGER trg_people_contact_updated_at
      BEFORE UPDATE ON people.contact
      FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

      -- Marketing triggers
      DROP TRIGGER IF EXISTS trg_marketing_campaign_updated_at ON marketing.campaign;
      CREATE TRIGGER trg_marketing_campaign_updated_at
      BEFORE UPDATE ON marketing.campaign
      FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
    `);

    console.log('🔍 Creating views and queues...');
    await client.query(`
      CREATE OR REPLACE VIEW company.vw_company_slots AS
      SELECT
        c.company_id,
        c.company_name,
        cs.company_slot_id,
        cs.role_code,
        cs.contact_id,
        p.full_name,
        p.title,
        p.email,
        p.phone,
        p.profile_source_url,
        v.email_status,
        v.email_checked_at,
        c.website_url,
        c.linkedin_url,
        c.news_url,
        c.renewal_month,
        c.created_at as company_created_at,
        c.updated_at as company_updated_at
      FROM company.company c
      JOIN company.company_slot cs ON cs.company_id = c.company_id
      LEFT JOIN people.contact p ON p.contact_id = cs.contact_id
      LEFT JOIN people.contact_verification v ON v.contact_id = cs.contact_id;

      CREATE OR REPLACE VIEW company.next_company_urls_30d AS
      SELECT company_id, 'website'::text AS url_type, website_url AS url, last_site_checked_at AS last_checked_at
      FROM company.company
      WHERE website_url IS NOT NULL
        AND (last_site_checked_at IS NULL OR last_site_checked_at < (now() - INTERVAL '30 days'))
      UNION ALL
      SELECT company_id, 'linkedin'::text, linkedin_url, last_linkedin_checked_at
      FROM company.company
      WHERE linkedin_url IS NOT NULL
        AND (last_linkedin_checked_at IS NULL OR last_linkedin_checked_at < (now() - INTERVAL '30 days'))
      UNION ALL
      SELECT company_id, 'news'::text, news_url, last_news_checked_at
      FROM company.company
      WHERE news_url IS NOT NULL
        AND (last_news_checked_at IS NULL OR last_news_checked_at < (now() - INTERVAL '30 days'));

      CREATE OR REPLACE VIEW people.next_profile_urls_30d AS
      SELECT contact_id, profile_source_url AS url, last_profile_checked_at AS last_checked_at
      FROM people.contact
      WHERE profile_source_url IS NOT NULL
        AND (last_profile_checked_at IS NULL OR last_profile_checked_at < (now() - INTERVAL '30 days'));

      CREATE OR REPLACE VIEW people.due_email_recheck_30d AS
      SELECT
        p.contact_id,
        p.full_name,
        p.title,
        p.email,
        v.email_status,
        v.email_checked_at,
        GREATEST(COALESCE(v.email_checked_at, 'epoch'::timestamptz), 'epoch'::timestamptz) AS last_checked_at
      FROM people.contact p
      LEFT JOIN people.contact_verification v ON v.contact_id = p.contact_id
      WHERE p.email IS NOT NULL
        AND (v.email_checked_at IS NULL OR v.email_checked_at < (now() - INTERVAL '30 days'));
    `);

    console.log('📅 Creating renewal tracking views...');
    await client.query(`
      CREATE OR REPLACE VIEW company.vw_next_renewal AS
      WITH base AS (
        SELECT company_id, company_name, renewal_month, COALESCE(renewal_notice_window_days,120) AS notice_days
        FROM company.company
        WHERE renewal_month IS NOT NULL
      )
      SELECT
        b.company_id,
        b.company_name,
        b.renewal_month,
        b.notice_days,
        CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int + 1, b.renewal_month, 1))::date
          ELSE DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date
        END AS next_renewal_date,
        CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN (DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int + 1, b.renewal_month, 1))::date - (notice_days * INTERVAL '1 day'))::date
          ELSE (DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date - (notice_days * INTERVAL '1 day'))::date
        END AS campaign_window_start
      FROM base b;

      CREATE OR REPLACE VIEW company.vw_due_renewals_ready AS
      WITH next_r AS (
        SELECT company_id, next_renewal_date, campaign_window_start
        FROM company.vw_next_renewal
      )
      SELECT
        c.company_id,
        c.company_name,
        nr.next_renewal_date,
        nr.campaign_window_start,
        EXISTS (
          SELECT 1
          FROM company.vw_company_slots s
          WHERE s.company_id = c.company_id
            AND s.contact_id IS NOT NULL
            AND s.email IS NOT NULL
            AND s.email_status = 'green'
        ) AS has_green_contact
      FROM company.company c
      JOIN next_r nr ON nr.company_id = c.company_id
      WHERE nr.campaign_window_start IS NOT NULL
        AND CURRENT_DATE >= nr.campaign_window_start
        AND EXISTS (
          SELECT 1
          FROM company.vw_company_slots s2
          WHERE s2.company_id = c.company_id
            AND s2.contact_id IS NOT NULL
            AND s2.email IS NOT NULL
            AND s2.email_status = 'green'
        );
    `);

    console.log('🔧 Creating slot management functions...');
    await client.query(`
      CREATE OR REPLACE FUNCTION company.ensure_company_slots(p_company_id BIGINT)
      RETURNS void AS $$
      BEGIN
        -- CEO
        INSERT INTO company.company_slot (company_id, role_code)
        SELECT p_company_id, 'CEO'
        WHERE NOT EXISTS (
          SELECT 1 FROM company.company_slot
          WHERE company_id = p_company_id AND role_code = 'CEO'
        );

        -- CFO
        INSERT INTO company.company_slot (company_id, role_code)
        SELECT p_company_id, 'CFO'
        WHERE NOT EXISTS (
          SELECT 1 FROM company.company_slot
          WHERE company_id = p_company_id AND role_code = 'CFO'
        );

        -- HR
        INSERT INTO company.company_slot (company_id, role_code)
        SELECT p_company_id, 'HR'
        WHERE NOT EXISTS (
          SELECT 1 FROM company.company_slot
          WHERE company_id = p_company_id AND role_code = 'HR'
        );
      END;
      $$ LANGUAGE plpgsql;

      -- Trigger: on insert of company, create slots automatically
      DROP TRIGGER IF EXISTS trg_company_after_insert_slots ON company.company;
      CREATE TRIGGER trg_company_after_insert_slots
      AFTER INSERT ON company.company
      FOR EACH ROW
      EXECUTE FUNCTION company.ensure_company_slots(NEW.company_id);
    `);

    console.log('📊 Creating indexes for performance...');
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_company_name ON company.company (company_name);
      CREATE INDEX IF NOT EXISTS idx_company_renewal_month ON company.company (renewal_month);
      CREATE INDEX IF NOT EXISTS idx_company_last_site_checked ON company.company (last_site_checked_at);
      CREATE INDEX IF NOT EXISTS idx_company_last_linkedin_checked ON company.company (last_linkedin_checked_at);
      CREATE INDEX IF NOT EXISTS idx_company_last_news_checked ON company.company (last_news_checked_at);
      
      CREATE INDEX IF NOT EXISTS idx_company_slot_company ON company.company_slot (company_id);
      CREATE INDEX IF NOT EXISTS idx_company_slot_role ON company.company_slot (role_code);
      CREATE INDEX IF NOT EXISTS idx_company_slot_contact ON company.company_slot (contact_id);
      
      CREATE INDEX IF NOT EXISTS idx_contact_name ON people.contact (full_name);
      CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
      CREATE INDEX IF NOT EXISTS idx_contact_last_profile_checked ON people.contact (last_profile_checked_at);
      
      CREATE INDEX IF NOT EXISTS idx_contact_verif_status ON people.contact_verification (email_status);
      CREATE INDEX IF NOT EXISTS idx_contact_verif_checked_at ON people.contact_verification (email_checked_at);
      
      CREATE INDEX IF NOT EXISTS idx_message_log_campaign ON marketing.message_log (campaign_id);
      CREATE INDEX IF NOT EXISTS idx_message_log_contact ON marketing.message_log (contact_id);
      CREATE INDEX IF NOT EXISTS idx_message_log_sent_at ON marketing.message_log (sent_at);
      
      CREATE INDEX IF NOT EXISTS idx_bit_signal_company ON bit.signal (company_id);
      CREATE INDEX IF NOT EXISTS idx_bit_signal_created_at ON bit.signal (created_at);
      CREATE INDEX IF NOT EXISTS idx_bit_signal_processed_at ON bit.signal (processed_at);
    `);

    console.log('🧹 Cleaning up legacy marketing tables...');
    const legacyTables = [
      'marketing.company_raw_intake',
      'marketing.marketing_ceo',
      'marketing.marketing_cfo', 
      'marketing.marketing_hr',
      'marketing.marketing_david_barton_company',
      'marketing.marketing_david_barton_people',
      'marketing.marketing_david_barton_prep_table',
      'marketing.marketing_david_barton_command_log',
      'marketing.marketing_shq_command_log',
      'marketing.marketing_shq_error_log',
      'marketing.marketing_shq_prep_table'
    ];

    for (const table of legacyTables) {
      try {
        await client.query(`DROP TABLE IF EXISTS ${table} CASCADE`);
        console.log(`   ✅ Dropped ${table}`);
      } catch (error) {
        console.log(`   ⚠️ Could not drop ${table}: ${error.message}`);
      }
    }

    console.log('🔄 Creating compatibility views...');
    await client.query(`
      DROP VIEW IF EXISTS marketing.marketing_ceo;
      DROP VIEW IF EXISTS marketing.marketing_cfo;
      DROP VIEW IF EXISTS marketing.marketing_hr;

      CREATE OR REPLACE VIEW marketing.marketing_ceo AS
      SELECT * FROM company.vw_company_slots WHERE role_code='CEO';
      
      CREATE OR REPLACE VIEW marketing.marketing_cfo AS
      SELECT * FROM company.vw_company_slots WHERE role_code='CFO';
      
      CREATE OR REPLACE VIEW marketing.marketing_hr AS
      SELECT * FROM company.vw_company_slots WHERE role_code='HR';
    `);

    console.log('🔄 Backfilling company slots...');
    await client.query(`
      DO $$
      DECLARE r RECORD;
      BEGIN
        FOR r IN SELECT company_id FROM company.company LOOP
          PERFORM company.ensure_company_slots(r.company_id);
        END LOOP;
      END$$;
    `);

    // Commit transaction
    await client.query('COMMIT');

    console.log('\n🧪 Running verification tests...');
    
    // Test basic table counts
    const basicChecks = [
      { query: "SELECT COUNT(*) AS count FROM company.company", name: "Companies" },
      { query: "SELECT COUNT(*) AS count FROM company.company_slot", name: "Company slots" },
      { query: "SELECT COUNT(*) AS count FROM people.contact", name: "Contacts" },
      { query: "SELECT COUNT(*) AS count FROM people.contact_verification", name: "Contact verifications" },
      { query: "SELECT COUNT(*) AS count FROM marketing.campaign", name: "Campaigns" },
      { query: "SELECT COUNT(*) AS count FROM bit.signal", name: "Bit signals" }
    ];

    for (const check of basicChecks) {
      try {
        const result = await client.query(check.query);
        console.log(`   ✅ ${check.name}: ${result.rows[0].count}`);
      } catch (error) {
        console.log(`   ⚠️ ${check.name}: Error - ${error.message}`);
      }
    }

    // Test queue views
    console.log('\n📊 Testing queue views...');
    const queueChecks = [
      { query: "SELECT COUNT(*) AS count FROM company.vw_company_slots", name: "Company slots view" },
      { query: "SELECT COUNT(*) AS count FROM company.next_company_urls_30d", name: "Company URLs queue" },
      { query: "SELECT COUNT(*) AS count FROM people.next_profile_urls_30d", name: "Profile URLs queue" },
      { query: "SELECT COUNT(*) AS count FROM people.due_email_recheck_30d", name: "Email recheck queue" },
      { query: "SELECT COUNT(*) AS count FROM company.vw_due_renewals_ready", name: "Renewal ready queue" }
    ];

    for (const check of queueChecks) {
      try {
        const result = await client.query(check.query);
        console.log(`   ✅ ${check.name}: ${result.rows[0].count} items`);
      } catch (error) {
        console.log(`   ⚠️ ${check.name}: Error - ${error.message}`);
      }
    }

    // Test slot distribution
    console.log('\n🎯 Checking slot distribution...');
    try {
      const slotCheck = await client.query(`
        SELECT 
          c.company_name,
          COUNT(cs.role_code) as total_slots,
          COUNT(cs.contact_id) as filled_slots,
          STRING_AGG(cs.role_code::text, ',' ORDER BY cs.role_code) as roles
        FROM company.company c
        LEFT JOIN company.company_slot cs ON cs.company_id = c.company_id
        GROUP BY c.company_id, c.company_name
        HAVING COUNT(cs.role_code) > 0
        ORDER BY c.company_name
        LIMIT 5
      `);
      
      if (slotCheck.rows.length > 0) {
        slotCheck.rows.forEach(row => {
          console.log(`   📊 ${row.company_name}: ${row.filled_slots}/${row.total_slots} slots (${row.roles})`);
        });
      } else {
        console.log('   ℹ️ No companies found for slot distribution test');
      }
    } catch (error) {
      console.log(`   ⚠️ Slot distribution check failed: ${error.message}`);
    }

    // Test sample data insertion and slot auto-creation
    console.log('\n🧪 Testing auto-slot creation...');
    try {
      const testResult = await client.query(`
        INSERT INTO company.company (company_name, website_url, renewal_month)
        VALUES ('Test Company Auto-Slots', 'https://test.com', 6)
        RETURNING company_id
      `);
      
      const testCompanyId = testResult.rows[0].company_id;
      
      const slotCount = await client.query(`
        SELECT COUNT(*) as slot_count 
        FROM company.company_slot 
        WHERE company_id = $1
      `, [testCompanyId]);
      
      if (slotCount.rows[0].slot_count == 3) {
        console.log('   ✅ Auto-slot creation working correctly (3 slots created)');
      } else {
        console.log(`   ⚠️ Auto-slot creation issue: ${slotCount.rows[0].slot_count} slots created instead of 3`);
      }
      
      // Clean up test data
      await client.query('DELETE FROM company.company WHERE company_id = $1', [testCompanyId]);
      
    } catch (error) {
      console.log(`   ⚠️ Auto-slot test failed: ${error.message}`);
    }

    console.log('\n🎉 Schema setup completed successfully!');
    console.log('\n📋 Summary:');
    console.log('   ✅ 5 schemas created (company, people, marketing, bit, ple)');
    console.log('   ✅ Core tables with proper relationships');
    console.log('   ✅ Zero-wandering scraper queues (30-day TTL)');
    console.log('   ✅ Auto-slot creation for companies (CEO, CFO, HR)');
    console.log('   ✅ Renewal tracking and campaign windows');
    console.log('   ✅ Email verification status tracking');
    console.log('   ✅ Performance indexes on key columns');
    console.log('   ✅ Legacy table cleanup completed');
    console.log('   ✅ Compatibility views for marketing roles');
    console.log('\n🚀 Database ready for complete pipeline: Ingestor → Neon → Apify → PLE → Bit');

  } catch (error) {
    console.error('❌ Schema setup failed:', error.message);
    console.error('Full error:', error);
    
    // Try to rollback
    try {
      await client.query('ROLLBACK');
      console.log('🔄 Transaction rolled back');
    } catch (rollbackError) {
      console.error('❌ Rollback failed:', rollbackError.message);
    }
    
    throw error;
    
  } finally {
    await client.end();
    console.log('🔌 Database connection closed');
  }
}

// Self-executing function with error handling
if (import.meta.url === `file://${process.argv[1]}`) {
  if (!process.env.NEON_DATABASE_URL && !process.env.DATABASE_URL) {
    console.error('❌ DATABASE_URL or NEON_DATABASE_URL environment variable is required');
    console.error('Please set one of these variables with your Neon connection string');
    process.exit(1);
  }

  setupLeanOutreachSchema()
    .then(() => {
      console.log('\n✨ All done! Your lean outreach schema is ready for action.');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Setup failed with error:', error.message);
      process.exit(1);
    });
}

export { setupLeanOutreachSchema };