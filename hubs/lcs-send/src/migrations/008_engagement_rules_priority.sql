ALTER TABLE lcs_engagement_rules ADD COLUMN signal_priority INTEGER NOT NULL DEFAULT 8;
UPDATE lcs_engagement_rules SET signal_priority = 9 WHERE trigger_event = 'clicked';
UPDATE lcs_engagement_rules SET signal_priority = 8 WHERE trigger_event = 'opened';
UPDATE lcs_engagement_rules SET signal_priority = 5 WHERE trigger_event IN ('no_response_3d', 'no_response_7d');
