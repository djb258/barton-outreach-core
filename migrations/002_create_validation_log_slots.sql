-- =============================================================
-- MIGRATION 2: Create Validation Log + Company Slot Table
-- =============================================================
-- Created: 2025-10-24
-- Database: Marketing DB (white-union-26418370)
-- Purpose: Add validation logging and company slots infrastructure

-- 1️⃣ shq_validation_log — doctrine enforcement log
CREATE TABLE IF NOT EXISTS shq_validation_log (
    validation_run_id TEXT PRIMARY KEY,
    source_table TEXT NOT NULL,
    target_table TEXT NOT NULL,
    total_records INTEGER,
    passed_records INTEGER,
    failed_records INTEGER,
    executed_by TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

COMMENT ON TABLE shq_validation_log IS
'Tracks each validation run (input table → target table) per Barton Doctrine.';


-- 2️⃣ marketing.company_slots — supports company_slot_unique_id constraint
CREATE TABLE IF NOT EXISTS marketing.company_slots (
    company_slot_unique_id TEXT PRIMARY KEY,
    company_unique_id TEXT NOT NULL REFERENCES marketing.company_master(company_unique_id),
    slot_type TEXT DEFAULT 'default',
    slot_label TEXT DEFAULT 'Primary Slot',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE marketing.company_slots IS
'Defines logical "slots" for a company (e.g., Primary, Division A, etc.). Each person references one slot.';

-- 3️⃣ Create default slot for each company
INSERT INTO marketing.company_slots (company_slot_unique_id, company_unique_id)
SELECT
    '04.04.05.' ||
    LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0') || '.' ||
    LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') || '.' ||
    LPAD((ROW_NUMBER() OVER ())::TEXT, 3, '0'),
    cm.company_unique_id
FROM marketing.company_master cm
WHERE NOT EXISTS (
    SELECT 1 FROM marketing.company_slots cs WHERE cs.company_unique_id = cm.company_unique_id
);
