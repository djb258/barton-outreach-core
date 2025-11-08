-- ========================================
-- Company Slot Table for Executive Positions
-- ========================================
-- Purpose: Track CEO, CFO, HR positions for each company
-- Links people to companies via executive slots

CREATE TABLE IF NOT EXISTS marketing.company_slot (
    -- Primary Key
    company_slot_unique_id TEXT PRIMARY KEY,

    -- Foreign Keys
    company_unique_id TEXT NOT NULL,
    person_unique_id TEXT,

    -- Slot Information
    slot_type TEXT NOT NULL CHECK (slot_type IN ('CEO', 'CFO', 'HR')),
    is_filled BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    filled_at TIMESTAMP WITH TIME ZONE,
    last_refreshed_at TIMESTAMP WITH TIME ZONE,

    -- Audit Trail
    filled_by TEXT,
    source_system TEXT DEFAULT 'manual',

    -- Foreign Key Constraints
    CONSTRAINT fk_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_person
        FOREIGN KEY (person_unique_id)
        REFERENCES marketing.people_master(unique_id)
        ON DELETE SET NULL,

    -- Unique Constraint: One slot type per company
    CONSTRAINT unique_company_slot
        UNIQUE (company_unique_id, slot_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_company_slot_company
    ON marketing.company_slot(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_person
    ON marketing.company_slot(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_type
    ON marketing.company_slot(slot_type);

CREATE INDEX IF NOT EXISTS idx_company_slot_filled
    ON marketing.company_slot(is_filled);

CREATE INDEX IF NOT EXISTS idx_company_slot_unfilled
    ON marketing.company_slot(company_unique_id, slot_type)
    WHERE is_filled = FALSE;

-- Comments
COMMENT ON TABLE marketing.company_slot IS 'Executive position slots (CEO, CFO, HR) for each company';
COMMENT ON COLUMN marketing.company_slot.company_slot_unique_id IS 'Barton ID format: 04.04.02.04.10000.XXX';
COMMENT ON COLUMN marketing.company_slot.slot_type IS 'Position type: CEO, CFO, or HR';
COMMENT ON COLUMN marketing.company_slot.is_filled IS 'Whether this slot has a person assigned';
COMMENT ON COLUMN marketing.company_slot.confidence_score IS 'Confidence in the title match (0.00-1.00)';
COMMENT ON COLUMN marketing.company_slot.last_refreshed_at IS 'Last time this slot was checked/updated';
