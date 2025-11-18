-- Add Backblaze B2 export tracking columns to validation_failures_log
--
-- This migration adds columns to track which validation failures have been
-- exported to Backblaze B2 object storage.
--
-- Date: 2025-11-18
-- Status: Production Ready

-- Add B2 export tracking columns
ALTER TABLE marketing.validation_failures_log
ADD COLUMN IF NOT EXISTS exported_to_b2 BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS exported_to_b2_at TIMESTAMP;

-- Create index for efficient queries of unexported records
CREATE INDEX IF NOT EXISTS idx_validation_failures_b2_export
ON marketing.validation_failures_log (exported_to_b2, failure_type)
WHERE exported_to_b2 = FALSE;

-- Add comment
COMMENT ON COLUMN marketing.validation_failures_log.exported_to_b2 IS 'TRUE if this failure has been exported to Backblaze B2';
COMMENT ON COLUMN marketing.validation_failures_log.exported_to_b2_at IS 'Timestamp when this failure was exported to Backblaze B2';

-- Verify
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'marketing'
  AND table_name = 'validation_failures_log'
  AND column_name IN ('exported_to_b2', 'exported_to_b2_at')
ORDER BY ordinal_position;
