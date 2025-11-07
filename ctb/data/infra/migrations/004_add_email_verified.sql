-- =============================================================
-- MIGRATION 4: Add email_verified Column to people_master
-- =============================================================
-- Created: 2025-10-24
-- Database: Marketing DB (white-union-26418370)
-- Purpose: Add email verification tracking per Barton Doctrine

-- 1️⃣ Add email_verified column
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false;

COMMENT ON COLUMN marketing.people_master.email_verified IS
'Tracks whether the email address has been verified (e.g., via bounce check, MX record, API validation). Default: false';

-- 2️⃣ Create index for filtering verified contacts
CREATE INDEX IF NOT EXISTS idx_people_email_verified
ON marketing.people_master(email_verified) WHERE email_verified = true;

COMMENT ON INDEX marketing.idx_people_email_verified IS
'Partial index for quickly finding verified email contacts. Only indexes TRUE values for efficiency.';
