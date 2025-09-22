-- SCHEMA: people
-- Core contact management schema with comprehensive contact information
-- and social media integration

-- Create the people schema
CREATE SCHEMA IF NOT EXISTS people;

-- Core contact table (personal-only; company data lives elsewhere)
-- Note: Foreign key constraints omitted initially to allow creation without dependent tables
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

-- Performance indexes for people.contact table
CREATE INDEX IF NOT EXISTS idx_contact_company_unique_id ON people.contact (company_unique_id);
CREATE INDEX IF NOT EXISTS idx_contact_slot_unique_id ON people.contact (slot_unique_id);
CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
CREATE INDEX IF NOT EXISTS idx_contact_name ON people.contact (first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_contact_source_system ON people.contact (source_system);
CREATE INDEX IF NOT EXISTS idx_contact_created_at ON people.contact (created_at);
CREATE INDEX IF NOT EXISTS idx_contact_updated_at ON people.contact (updated_at);
CREATE INDEX IF NOT EXISTS idx_contact_email_status ON people.contact (email_status);
CREATE INDEX IF NOT EXISTS idx_contact_do_not_contact ON people.contact (do_not_contact);

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

-- Add table and column comments for documentation
COMMENT ON SCHEMA people IS 'Contact management schema for individual people associated with companies';
COMMENT ON TABLE people.contact IS 'Contact information for individuals associated with companies';

-- Column comments
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

-- Create a view for easier contact querying with computed fields
CREATE OR REPLACE VIEW people.contact_view AS
SELECT
    contact_unique_id,
    company_unique_id,
    slot_unique_id,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name,
    title,
    seniority,
    department,
    email,
    email_status,
    email_last_verified_at,
    mobile_phone_e164,
    work_phone_e164,
    linkedin_url,
    x_url,
    instagram_url,
    facebook_url,
    threads_url,
    tiktok_url,
    youtube_url,
    personal_website_url,
    github_url,
    calendly_url,
    whatsapp_handle,
    telegram_handle,
    do_not_contact,
    contact_owner,
    source_system,
    source_record_id,
    created_at,
    updated_at,
    -- Computed fields
    CASE
        WHEN email IS NOT NULL AND email_status = 'valid' THEN 'available'
        WHEN email IS NOT NULL AND email_status IN ('invalid', 'bounced') THEN 'unavailable'
        WHEN email IS NOT NULL THEN 'pending_verification'
        ELSE 'no_email'
    END AS contact_availability,
    CASE
        WHEN linkedin_url IS NOT NULL OR x_url IS NOT NULL OR instagram_url IS NOT NULL
             OR facebook_url IS NOT NULL OR github_url IS NOT NULL THEN true
        ELSE false
    END AS has_social_media,
    CASE
        WHEN mobile_phone_e164 IS NOT NULL OR work_phone_e164 IS NOT NULL THEN true
        ELSE false
    END AS has_phone
FROM people.contact;

COMMENT ON VIEW people.contact_view IS 'Enhanced contact view with computed fields for easier querying';

-- Grant permissions to the appropriate roles (if they exist)
-- Note: These will only execute if the roles exist
DO $$
BEGIN
    -- Grant schema usage
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_ingest') THEN
        GRANT USAGE ON SCHEMA people TO mcp_ingest;
        GRANT SELECT, INSERT, UPDATE ON people.contact TO mcp_ingest;
        GRANT SELECT ON people.contact_view TO mcp_ingest;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_promote') THEN
        GRANT USAGE ON SCHEMA people TO mcp_promote;
        GRANT SELECT, INSERT, UPDATE ON people.contact TO mcp_promote;
        GRANT SELECT ON people.contact_view TO mcp_promote;
    END IF;

    -- Grant to current user (owner)
    GRANT ALL ON SCHEMA people TO CURRENT_USER;
    GRANT ALL ON people.contact TO CURRENT_USER;
    GRANT ALL ON people.contact_view TO CURRENT_USER;
END
$$;