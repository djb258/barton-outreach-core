-- EXTEND PEOPLE SCHEMA MIGRATION
-- This migration extends the existing people.contact table with additional fields
-- from the comprehensive contact management specification

-- Add missing columns to existing people.contact table
-- Note: We're working with the existing table structure and adding to it

-- Add company and slot references
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS company_unique_id TEXT,
ADD COLUMN IF NOT EXISTS slot_unique_id TEXT;

-- Add name fields (supplement existing full_name)
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT;

-- Add additional contact fields
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS seniority TEXT,
ADD COLUMN IF NOT EXISTS department TEXT,
ADD COLUMN IF NOT EXISTS email_status TEXT,
ADD COLUMN IF NOT EXISTS email_last_verified_at TIMESTAMPTZ;

-- Add phone fields (supplement existing phone)
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS mobile_phone_e164 TEXT,
ADD COLUMN IF NOT EXISTS work_phone_e164 TEXT;

-- Add social media URLs
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
ADD COLUMN IF NOT EXISTS x_url TEXT,
ADD COLUMN IF NOT EXISTS instagram_url TEXT,
ADD COLUMN IF NOT EXISTS facebook_url TEXT,
ADD COLUMN IF NOT EXISTS threads_url TEXT,
ADD COLUMN IF NOT EXISTS tiktok_url TEXT,
ADD COLUMN IF NOT EXISTS youtube_url TEXT,
ADD COLUMN IF NOT EXISTS personal_website_url TEXT,
ADD COLUMN IF NOT EXISTS github_url TEXT,
ADD COLUMN IF NOT EXISTS calendly_url TEXT;

-- Add messaging platform handles
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS whatsapp_handle TEXT,
ADD COLUMN IF NOT EXISTS telegram_handle TEXT;

-- Add management fields
ALTER TABLE people.contact
ADD COLUMN IF NOT EXISTS do_not_contact BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS contact_owner TEXT,
ADD COLUMN IF NOT EXISTS source_system TEXT,
ADD COLUMN IF NOT EXISTS source_record_id TEXT;

-- Add performance indexes for new columns
CREATE INDEX IF NOT EXISTS idx_contact_company_unique_id_new ON people.contact (company_unique_id);
CREATE INDEX IF NOT EXISTS idx_contact_slot_unique_id_new ON people.contact (slot_unique_id);
CREATE INDEX IF NOT EXISTS idx_contact_source_system_new ON people.contact (source_system);
CREATE INDEX IF NOT EXISTS idx_contact_email_status_new ON people.contact (email_status);
CREATE INDEX IF NOT EXISTS idx_contact_do_not_contact_new ON people.contact (do_not_contact);
CREATE INDEX IF NOT EXISTS idx_contact_first_last_name ON people.contact (first_name, last_name);

-- Add column comments for new fields
COMMENT ON COLUMN people.contact.company_unique_id IS 'Reference to company this contact belongs to';
COMMENT ON COLUMN people.contact.slot_unique_id IS 'Reference to outreach slot if applicable';
COMMENT ON COLUMN people.contact.first_name IS 'Contact first name (supplements full_name)';
COMMENT ON COLUMN people.contact.last_name IS 'Contact last name (supplements full_name)';
COMMENT ON COLUMN people.contact.seniority IS 'Seniority level (junior, mid, senior, executive)';
COMMENT ON COLUMN people.contact.department IS 'Department or functional area';
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

-- Create or update the enhanced contact view with computed fields
CREATE OR REPLACE VIEW people.contact_enhanced_view AS
SELECT
    contact_id,
    full_name,
    first_name,
    last_name,
    -- Create computed full name if individual names exist
    COALESCE(
        CASE
            WHEN first_name IS NOT NULL AND last_name IS NOT NULL
            THEN CONCAT(first_name, ' ', last_name)
            ELSE full_name
        END,
        full_name
    ) AS computed_full_name,
    company_unique_id,
    slot_unique_id,
    title,
    seniority,
    department,
    email,
    email_status,
    email_last_verified_at,
    phone,
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
    profile_source_url,
    last_profile_checked_at,
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
        WHEN mobile_phone_e164 IS NOT NULL OR work_phone_e164 IS NOT NULL OR phone IS NOT NULL THEN true
        ELSE false
    END AS has_phone,
    -- Profile monitoring from existing system
    CASE
        WHEN profile_source_url IS NOT NULL THEN true
        ELSE false
    END AS has_profile_source
FROM people.contact;

COMMENT ON VIEW people.contact_enhanced_view IS 'Enhanced contact view combining existing and new schema fields with computed fields';

-- Create a function to populate first_name and last_name from full_name where they are missing
CREATE OR REPLACE FUNCTION people.split_full_name_if_missing()
RETURNS void AS $$
BEGIN
    -- Update first_name and last_name from full_name where they are null and full_name exists
    UPDATE people.contact
    SET
        first_name = CASE
            WHEN position(' ' in full_name) > 0
            THEN substring(full_name from 1 for position(' ' in full_name) - 1)
            ELSE full_name
        END,
        last_name = CASE
            WHEN position(' ' in full_name) > 0
            THEN substring(full_name from position(' ' in full_name) + 1)
            ELSE NULL
        END
    WHERE full_name IS NOT NULL
      AND (first_name IS NULL OR last_name IS NULL);

    -- Also update the full_name if it's null but first_name and last_name exist
    UPDATE people.contact
    SET full_name = CONCAT(first_name, ' ', last_name)
    WHERE full_name IS NULL
      AND first_name IS NOT NULL
      AND last_name IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION people.split_full_name_if_missing() IS 'Utility function to split full_name into first_name/last_name or combine them as needed';

-- Grant permissions to the appropriate roles (if they exist)
DO $$
BEGIN
    -- Grant permissions to MCP roles if they exist
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_ingest') THEN
        GRANT SELECT, INSERT, UPDATE ON people.contact TO mcp_ingest;
        GRANT SELECT ON people.contact_enhanced_view TO mcp_ingest;
        GRANT EXECUTE ON FUNCTION people.split_full_name_if_missing() TO mcp_ingest;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_promote') THEN
        GRANT SELECT, INSERT, UPDATE ON people.contact TO mcp_promote;
        GRANT SELECT ON people.contact_enhanced_view TO mcp_promote;
        GRANT EXECUTE ON FUNCTION people.split_full_name_if_missing() TO mcp_promote;
    END IF;
END
$$;