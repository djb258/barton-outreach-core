-- BAR-304: Add unique constraint on (contact_email, sequence_id) to prevent
-- race condition where two concurrent requests both INSERT for the same contact.
-- Enables INSERT ... ON CONFLICT(contact_email, sequence_id) DO UPDATE.
CREATE UNIQUE INDEX IF NOT EXISTS idx_contact_seq_email_seqid
  ON lcs_contact_sequence_state(contact_email, sequence_id);
