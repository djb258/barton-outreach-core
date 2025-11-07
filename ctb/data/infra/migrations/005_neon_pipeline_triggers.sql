-- ════════════════════════════════════════════════════════════════════════════════
-- NEON PIPELINE TRIGGERS - Event-Driven Outreach System
-- ════════════════════════════════════════════════════════════════════════════════
-- Purpose: Convert schedule-based pipeline to event-driven architecture
-- Author: Pipeline Automation Team
-- Date: 2025-10-24
-- ════════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────────
-- 1. CREATE PIPELINE EVENTS TABLE
-- ────────────────────────────────────────────────────────────────────────────────
-- This table acts as the event queue for all pipeline stages

CREATE TABLE IF NOT EXISTS marketing.pipeline_events (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'processed', 'failed')),
  error_message TEXT,
  retry_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_status ON marketing.pipeline_events(status, created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_type ON marketing.pipeline_events(event_type);

COMMENT ON TABLE marketing.pipeline_events IS 'Event queue for pipeline automation - single source of truth';
COMMENT ON COLUMN marketing.pipeline_events.event_type IS 'Type of event: company_created, company_validated, company_promoted, slots_created, contact_enriched';
COMMENT ON COLUMN marketing.pipeline_events.payload IS 'JSONB payload containing record IDs and relevant data';
COMMENT ON COLUMN marketing.pipeline_events.status IS 'Event processing status: pending → processing → processed | failed';

-- ────────────────────────────────────────────────────────────────────────────────
-- 2. TRIGGER FUNCTION: Notify Pipeline Event
-- ────────────────────────────────────────────────────────────────────────────────
-- Generic function to insert events and notify listeners

CREATE OR REPLACE FUNCTION marketing.notify_pipeline_event()
RETURNS TRIGGER AS $$
DECLARE
  event_payload JSONB;
  event_name TEXT;
BEGIN
  -- Determine event type based on triggering table and operation
  CASE TG_TABLE_NAME
    WHEN 'company_raw_intake' THEN
      IF NEW.validated IS NULL AND OLD.validated IS DISTINCT FROM NEW.validated THEN
        event_name := 'company_created';
        event_payload := jsonb_build_object(
          'record_id', NEW.id,
          'company_name', NEW.company,
          'website', NEW.website,
          'batch_id', NEW.import_batch_id,
          'trigger_time', NOW()
        );
      ELSIF NEW.validated = TRUE AND OLD.validated IS DISTINCT FROM NEW.validated THEN
        event_name := 'company_validated';
        event_payload := jsonb_build_object(
          'record_id', NEW.id,
          'company_name', NEW.company,
          'website', NEW.website,
          'batch_id', NEW.import_batch_id,
          'validated_by', NEW.validated_by,
          'trigger_time', NOW()
        );
      ELSE
        RETURN NEW; -- No event needed
      END IF;

    WHEN 'company_master' THEN
      IF TG_OP = 'INSERT' THEN
        event_name := 'company_promoted';
        event_payload := jsonb_build_object(
          'company_unique_id', NEW.company_unique_id,
          'company_name', NEW.company_name,
          'website_url', NEW.website_url,
          'batch_id', NEW.import_batch_id,
          'trigger_time', NOW()
        );
      ELSE
        RETURN NEW; -- Only fire on INSERT
      END IF;

    WHEN 'company_slots' THEN
      IF TG_OP = 'INSERT' THEN
        event_name := 'slots_created';
        event_payload := jsonb_build_object(
          'slot_id', NEW.company_slot_unique_id,
          'company_id', NEW.company_unique_id,
          'slot_type', NEW.slot_type,
          'slot_label', NEW.slot_label,
          'trigger_time', NOW()
        );
      ELSE
        RETURN NEW;
      END IF;

    WHEN 'contact_enrichment' THEN
      IF NEW.enrichment_status = 'completed' AND OLD.enrichment_status IS DISTINCT FROM NEW.enrichment_status THEN
        event_name := 'contact_enriched';
        event_payload := jsonb_build_object(
          'slot_id', NEW.company_slot_unique_id,
          'linkedin_url', NEW.linkedin_url,
          'full_name', NEW.full_name,
          'email', NEW.email,
          'trigger_time', NOW()
        );
      ELSE
        RETURN NEW;
      END IF;

    ELSE
      RETURN NEW; -- Unknown table
  END CASE;

  -- Insert event into pipeline_events table
  INSERT INTO marketing.pipeline_events (event_type, payload, status)
  VALUES (event_name, event_payload, 'pending');

  -- Notify listeners (optional - for debugging/monitoring)
  PERFORM pg_notify('pipeline_event', json_build_object(
    'event_type', event_name,
    'payload', event_payload
  )::text);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.notify_pipeline_event() IS 'Generic trigger function to publish pipeline events to marketing.pipeline_events and pg_notify channel';

-- ────────────────────────────────────────────────────────────────────────────────
-- 3. STAGE 1: Company Raw Intake → Validate Company
-- ────────────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trigger_company_intake_event ON intake.company_raw_intake;

CREATE TRIGGER trigger_company_intake_event
  AFTER INSERT OR UPDATE OF validated
  ON intake.company_raw_intake
  FOR EACH ROW
  EXECUTE FUNCTION marketing.notify_pipeline_event();

COMMENT ON TRIGGER trigger_company_intake_event ON intake.company_raw_intake IS
  'Fires company_created event when new row inserted, company_validated event when validated=TRUE';

-- ────────────────────────────────────────────────────────────────────────────────
-- 4. STAGE 2: Company Validated → Promote Company
-- ────────────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trigger_company_promotion_event ON marketing.company_master;

CREATE TRIGGER trigger_company_promotion_event
  AFTER INSERT
  ON marketing.company_master
  FOR EACH ROW
  EXECUTE FUNCTION marketing.notify_pipeline_event();

COMMENT ON TRIGGER trigger_company_promotion_event ON marketing.company_master IS
  'Fires company_promoted event when company is inserted into master table';

-- ────────────────────────────────────────────────────────────────────────────────
-- 5. STAGE 3: Company Promoted → Create Slots
-- ────────────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS trigger_slot_creation_event ON marketing.company_slots;

CREATE TRIGGER trigger_slot_creation_event
  AFTER INSERT
  ON marketing.company_slots
  FOR EACH ROW
  EXECUTE FUNCTION marketing.notify_pipeline_event();

COMMENT ON TRIGGER trigger_slot_creation_event ON marketing.company_slots IS
  'Fires slots_created event when new slot is created';

-- ────────────────────────────────────────────────────────────────────────────────
-- 6. STAGE 4: Slots Created → Enrich Contacts (Table Creation)
-- ────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.contact_enrichment (
  id SERIAL PRIMARY KEY,
  company_slot_unique_id TEXT NOT NULL REFERENCES marketing.company_slots(company_slot_unique_id),
  linkedin_url TEXT,
  full_name TEXT,
  email TEXT,
  phone TEXT,
  enrichment_status TEXT DEFAULT 'pending' CHECK (enrichment_status IN ('pending', 'processing', 'completed', 'failed')),
  enrichment_source TEXT, -- 'apify', 'apollo', etc.
  enrichment_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  enriched_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_enrichment_status ON marketing.contact_enrichment(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_enrichment_slot ON marketing.contact_enrichment(company_slot_unique_id);

COMMENT ON TABLE marketing.contact_enrichment IS 'Contact enrichment data from LinkedIn/Apify - one record per slot';

DROP TRIGGER IF EXISTS trigger_enrichment_event ON marketing.contact_enrichment;

CREATE TRIGGER trigger_enrichment_event
  AFTER INSERT OR UPDATE OF enrichment_status
  ON marketing.contact_enrichment
  FOR EACH ROW
  EXECUTE FUNCTION marketing.notify_pipeline_event();

COMMENT ON TRIGGER trigger_enrichment_event ON marketing.contact_enrichment IS
  'Fires contact_enriched event when enrichment_status changes to completed';

-- ────────────────────────────────────────────────────────────────────────────────
-- 7. STAGE 5: Contact Enriched → Verify Emails (Table Creation)
-- ────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.email_verification (
  id SERIAL PRIMARY KEY,
  enrichment_id INT NOT NULL REFERENCES marketing.contact_enrichment(id),
  email TEXT NOT NULL,
  verification_status TEXT DEFAULT 'pending' CHECK (verification_status IN ('pending', 'valid', 'invalid', 'risky', 'unknown')),
  verification_service TEXT, -- 'millionverifier', 'zerobounce', etc.
  verification_result JSONB,
  verified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verification_status ON marketing.email_verification(verification_status);
CREATE INDEX IF NOT EXISTS idx_verification_email ON marketing.email_verification(email);

COMMENT ON TABLE marketing.email_verification IS 'Email verification results from MillionVerifier/ZeroBounce';

-- ────────────────────────────────────────────────────────────────────────────────
-- 8. HELPER FUNCTION: Mark Event as Processed
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION marketing.mark_event_processed(event_id INT)
RETURNS VOID AS $$
BEGIN
  UPDATE marketing.pipeline_events
  SET status = 'processed',
      processed_at = NOW()
  WHERE id = event_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.mark_event_processed(INT) IS 'Mark pipeline event as processed - called by n8n webhooks after successful execution';

-- ────────────────────────────────────────────────────────────────────────────────
-- 9. HELPER FUNCTION: Mark Event as Failed
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION marketing.mark_event_failed(event_id INT, error_msg TEXT)
RETURNS VOID AS $$
BEGIN
  UPDATE marketing.pipeline_events
  SET status = 'failed',
      error_message = error_msg,
      retry_count = retry_count + 1,
      processed_at = NOW()
  WHERE id = event_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.mark_event_failed(INT, TEXT) IS 'Mark pipeline event as failed with error message';

-- ────────────────────────────────────────────────────────────────────────────────
-- 10. CLEANUP QUERY: Purge Old Processed Events (Run Periodically)
-- ────────────────────────────────────────────────────────────────────────────────

-- Delete processed events older than 30 days
-- Run this via scheduled n8n workflow or cron job
-- DELETE FROM marketing.pipeline_events
-- WHERE status = 'processed'
--   AND processed_at < NOW() - INTERVAL '30 days';

-- ────────────────────────────────────────────────────────────────────────────────
-- 11. SAMPLE DATA FOR TESTING
-- ────────────────────────────────────────────────────────────────────────────────

-- Test 1: Insert raw company (should trigger company_created event)
-- INSERT INTO intake.company_raw_intake (company, website, import_batch_id)
-- VALUES ('Test Company Inc', 'https://testcompany.com', 'TEST-001')
-- RETURNING id;

-- Test 2: Update to validated (should trigger company_validated event)
-- UPDATE intake.company_raw_intake
-- SET validated = TRUE,
--     validated_at = NOW(),
--     validated_by = 'test-user'
-- WHERE id = [id_from_test_1];

-- Test 3: Check pipeline events
-- SELECT * FROM marketing.pipeline_events ORDER BY created_at DESC LIMIT 10;

-- ────────────────────────────────────────────────────────────────────────────────
-- 12. DEBUGGING: PostgreSQL LISTEN Command
-- ────────────────────────────────────────────────────────────────────────────────

-- Run this in a separate psql session to monitor real-time events:
-- LISTEN pipeline_event;

-- You'll see notifications like:
-- Asynchronous notification "pipeline_event" with payload:
-- {"event_type":"company_created","payload":{"record_id":123,...}}

-- ════════════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION 005 - NEON PIPELINE TRIGGERS
-- ════════════════════════════════════════════════════════════════════════════════
