-- ============================================================================
-- Migration: 0009_create_client_conversion.sql
-- Description: Create client_conversion table (Final state: CLIENT)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- ENUM: Contract status
-- ============================================================================

CREATE TYPE funnel.contract_status AS ENUM (
    'pending_signature',
    'signed',
    'active',
    'completed',
    'cancelled',
    'churned'
);

-- ============================================================================
-- TABLE: client_conversion
-- Purpose: Track successful conversions to CLIENT (final state)
-- State: CLIENT lifecycle state - terminal state in the funnel system
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.client_conversion (
    -- Primary key
    client_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL UNIQUE,  -- One conversion per company
    person_id               UUID,  -- Primary contact
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- Conversion tracking
    signed_ts               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_date          DATE,
    contract_start_date     DATE,
    contract_end_date       DATE,

    -- Contract status
    contract_status         funnel.contract_status NOT NULL DEFAULT 'signed',

    -- Deal metrics
    lives                   INTEGER,  -- Number of employees/lives covered
    annual_revenue          DECIMAL(12,2),
    monthly_revenue         DECIMAL(12,2),
    deal_value              DECIMAL(12,2),

    -- Revenue tracking
    currency                VARCHAR(3) DEFAULT 'USD',
    revenue_type            VARCHAR(50),  -- 'subscription', 'one_time', 'usage_based'

    -- Source tracking
    source_funnel           funnel.funnel_membership,  -- Last funnel before conversion
    source_appointment_id   UUID REFERENCES funnel.appointment_history(appointment_id),
    acquisition_channel     VARCHAR(100),

    -- Journey metrics
    days_to_conversion      INTEGER,  -- Days from first contact to signed
    touchpoints_count       INTEGER,  -- Number of touchpoints before conversion
    meetings_count          INTEGER,  -- Number of meetings before conversion

    -- Sales attribution
    sales_rep_id            VARCHAR(100),
    sales_rep_name          VARCHAR(255),
    sales_team              VARCHAR(100),

    -- CRM references
    crm_deal_id             VARCHAR(100),
    crm_account_id          VARCHAR(100),
    hubspot_deal_id         VARCHAR(100),
    salesforce_opp_id       VARCHAR(100),

    -- Contract details
    contract_type           VARCHAR(100),
    contract_term_months    INTEGER,
    auto_renewal            BOOLEAN DEFAULT FALSE,

    -- Notes
    notes                   TEXT,
    win_reason              TEXT,  -- Why they chose us

    -- Customer success tracking
    onboarding_status       VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed'
    onboarding_started_at   TIMESTAMPTZ,
    onboarding_completed_at TIMESTAMPTZ,
    csm_assigned            VARCHAR(255),

    -- Churn tracking
    churned_at              TIMESTAMPTZ,
    churn_reason            TEXT,

    -- Metadata
    metadata                JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_lives CHECK (lives IS NULL OR lives >= 0),
    CONSTRAINT chk_revenue CHECK (annual_revenue IS NULL OR annual_revenue >= 0),
    CONSTRAINT chk_contract_dates CHECK (
        contract_end_date IS NULL OR contract_start_date IS NULL OR
        contract_end_date >= contract_start_date
    )
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_client_company_id ON funnel.client_conversion(company_id);
CREATE INDEX idx_client_person_id ON funnel.client_conversion(person_id)
    WHERE person_id IS NOT NULL;
CREATE INDEX idx_client_suspect_id ON funnel.client_conversion(suspect_id);

-- Time-based indexes
CREATE INDEX idx_client_signed_ts ON funnel.client_conversion(signed_ts);
CREATE INDEX idx_client_created_at ON funnel.client_conversion(created_at);
CREATE INDEX idx_client_effective_date ON funnel.client_conversion(effective_date);

-- Status indexes
CREATE INDEX idx_client_contract_status ON funnel.client_conversion(contract_status);

-- Metric indexes
CREATE INDEX idx_client_lives ON funnel.client_conversion(lives);
CREATE INDEX idx_client_revenue ON funnel.client_conversion(annual_revenue);
CREATE INDEX idx_client_deal_value ON funnel.client_conversion(deal_value);

-- Source tracking
CREATE INDEX idx_client_source_funnel ON funnel.client_conversion(source_funnel);
CREATE INDEX idx_client_source_appt ON funnel.client_conversion(source_appointment_id)
    WHERE source_appointment_id IS NOT NULL;
CREATE INDEX idx_client_acquisition ON funnel.client_conversion(acquisition_channel);

-- Sales attribution
CREATE INDEX idx_client_sales_rep ON funnel.client_conversion(sales_rep_id)
    WHERE sales_rep_id IS NOT NULL;
CREATE INDEX idx_client_sales_team ON funnel.client_conversion(sales_team)
    WHERE sales_team IS NOT NULL;

-- CRM references
CREATE INDEX idx_client_crm_deal ON funnel.client_conversion(crm_deal_id)
    WHERE crm_deal_id IS NOT NULL;
CREATE INDEX idx_client_hubspot ON funnel.client_conversion(hubspot_deal_id)
    WHERE hubspot_deal_id IS NOT NULL;
CREATE INDEX idx_client_salesforce ON funnel.client_conversion(salesforce_opp_id)
    WHERE salesforce_opp_id IS NOT NULL;

-- Customer success
CREATE INDEX idx_client_onboarding ON funnel.client_conversion(onboarding_status);
CREATE INDEX idx_client_csm ON funnel.client_conversion(csm_assigned)
    WHERE csm_assigned IS NOT NULL;

-- Churn tracking
CREATE INDEX idx_client_churned ON funnel.client_conversion(churned_at)
    WHERE churned_at IS NOT NULL;
CREATE INDEX idx_client_active ON funnel.client_conversion(contract_status)
    WHERE contract_status IN ('signed', 'active');

-- Contract dates
CREATE INDEX idx_client_contract_end ON funnel.client_conversion(contract_end_date)
    WHERE contract_end_date IS NOT NULL;

-- JSONB index
CREATE INDEX idx_client_metadata ON funnel.client_conversion USING GIN (metadata);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER trg_client_updated_at
    BEFORE UPDATE ON funnel.client_conversion
    FOR EACH ROW
    EXECUTE FUNCTION funnel.update_suspect_timestamp();

-- Calculate days to conversion
CREATE OR REPLACE FUNCTION funnel.calculate_days_to_conversion()
RETURNS TRIGGER AS $$
DECLARE
    first_contact_ts TIMESTAMPTZ;
BEGIN
    -- Get the first contact timestamp from suspect_universe
    IF NEW.suspect_id IS NOT NULL THEN
        SELECT entered_suspect_ts INTO first_contact_ts
        FROM funnel.suspect_universe
        WHERE suspect_id = NEW.suspect_id;

        IF first_contact_ts IS NOT NULL THEN
            NEW.days_to_conversion = EXTRACT(DAY FROM (NEW.signed_ts - first_contact_ts))::INTEGER;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_client_days_to_conversion
    BEFORE INSERT ON funnel.client_conversion
    FOR EACH ROW
    EXECUTE FUNCTION funnel.calculate_days_to_conversion();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active clients summary
CREATE OR REPLACE VIEW funnel.v_active_clients AS
SELECT
    client_id,
    company_id,
    person_id,
    signed_ts,
    lives,
    annual_revenue,
    contract_status,
    onboarding_status,
    days_to_conversion,
    sales_rep_name
FROM funnel.client_conversion
WHERE contract_status IN ('signed', 'active')
ORDER BY signed_ts DESC;

-- Revenue summary by source funnel
CREATE OR REPLACE VIEW funnel.v_revenue_by_funnel AS
SELECT
    source_funnel,
    COUNT(*) as client_count,
    SUM(lives) as total_lives,
    SUM(annual_revenue) as total_annual_revenue,
    AVG(annual_revenue) as avg_annual_revenue,
    AVG(days_to_conversion) as avg_days_to_conversion,
    AVG(meetings_count) as avg_meetings
FROM funnel.client_conversion
WHERE contract_status IN ('signed', 'active')
GROUP BY source_funnel
ORDER BY total_annual_revenue DESC NULLS LAST;

-- Monthly conversion trends
CREATE OR REPLACE VIEW funnel.v_monthly_conversions AS
SELECT
    DATE_TRUNC('month', signed_ts) as month,
    COUNT(*) as conversions,
    SUM(lives) as total_lives,
    SUM(annual_revenue) as total_revenue,
    AVG(days_to_conversion) as avg_days_to_conversion
FROM funnel.client_conversion
WHERE contract_status IN ('signed', 'active')
GROUP BY DATE_TRUNC('month', signed_ts)
ORDER BY month DESC;

-- Upcoming renewals (contracts ending in next 90 days)
CREATE OR REPLACE VIEW funnel.v_upcoming_renewals AS
SELECT
    client_id,
    company_id,
    contract_end_date,
    annual_revenue,
    lives,
    auto_renewal,
    csm_assigned
FROM funnel.client_conversion
WHERE contract_status IN ('signed', 'active')
  AND contract_end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
ORDER BY contract_end_date ASC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.client_conversion IS 'CLIENT lifecycle state - Terminal success state. One record per converted company.';
COMMENT ON COLUMN funnel.client_conversion.client_id IS 'Primary key - unique identifier for each client conversion';
COMMENT ON COLUMN funnel.client_conversion.company_id IS 'FK to company - unique constraint ensures one conversion per company';
COMMENT ON COLUMN funnel.client_conversion.signed_ts IS 'When the contract was signed (conversion timestamp)';
COMMENT ON COLUMN funnel.client_conversion.lives IS 'Number of employees/lives covered (benefits industry metric)';
COMMENT ON COLUMN funnel.client_conversion.annual_revenue IS 'Annual contract value';
COMMENT ON COLUMN funnel.client_conversion.source_funnel IS 'Last funnel the contact was in before converting';
COMMENT ON COLUMN funnel.client_conversion.days_to_conversion IS 'Auto-calculated: days from first contact to signed';
COMMENT ON VIEW funnel.v_active_clients IS 'Currently active clients';
COMMENT ON VIEW funnel.v_revenue_by_funnel IS 'Revenue attribution by source funnel';
COMMENT ON VIEW funnel.v_monthly_conversions IS 'Monthly conversion trends';
COMMENT ON VIEW funnel.v_upcoming_renewals IS 'Contracts expiring in next 90 days';
