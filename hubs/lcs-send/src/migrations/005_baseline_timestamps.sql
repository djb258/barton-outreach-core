-- Baseline + Change timestamps for Grid Reader
-- Two timestamps per data point:
--   *_baseline_at = when we FIRST captured this value (the baseline)
--   *_changed_at  = when the value actually CHANGED (the signal)
-- Process 300 and 200 write these when they detect changes.

-- SP timestamps (social platform presence)
ALTER TABLE slot_workbench ADD COLUMN sp_baseline_at TEXT;
ALTER TABLE slot_workbench ADD COLUMN sp_changed_at TEXT;

-- People timestamps (per slot — already have person_found_at, add baseline + changed)
ALTER TABLE slot_workbench ADD COLUMN people_baseline_at TEXT;
ALTER TABLE slot_workbench ADD COLUMN people_changed_at TEXT;

-- DOL timestamp (when filing data changed)
ALTER TABLE slot_workbench ADD COLUMN dol_baseline_at TEXT;
ALTER TABLE slot_workbench ADD COLUMN dol_changed_at TEXT;

-- CT timestamp (company target data rarely changes but track it)
ALTER TABLE slot_workbench ADD COLUMN ct_baseline_at TEXT;
ALTER TABLE slot_workbench ADD COLUMN ct_changed_at TEXT;
