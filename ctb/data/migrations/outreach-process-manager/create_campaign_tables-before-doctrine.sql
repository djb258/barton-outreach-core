-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-62C6000A
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

-- Step 7: Auto-Campaign Builder - Database Schema
-- Barton Doctrine Campaign Tables

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- Campaign master table for doctrine-bound blueprints
CREATE TABLE IF NOT EXISTS marketing.campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT NOT NULL UNIQUE, -- Barton ID format: 04.04.03.XX.XXXXX.XXX
    campaign_type TEXT CHECK (campaign_type IN ('PLE', 'BIT')),
    trigger_event TEXT NOT NULL, -- e.g. promotion, bit_signal_fired
    template JSONB NOT NULL, -- doctrine campaign blueprint

    -- Reference to promoted records (required by doctrine)
    company_unique_id TEXT NOT NULL, -- References company_master
    people_ids TEXT[] NOT NULL, -- Array of people_master Barton IDs

    -- Campaign metadata
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'failed')),
    marketing_score INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    launched_at TIMESTAMPTZ,

    -- Doctrine compliance
    doctrine_version TEXT DEFAULT '04.04.03',
    heir_compliant BOOLEAN DEFAULT true
);

-- Campaign audit log for complete traceability
CREATE TABLE IF NOT EXISTS marketing.campaign_audit_log (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    action TEXT CHECK (action IN ('create', 'launch', 'pause', 'update', 'complete', 'fail')),
    status TEXT CHECK (status IN ('success', 'failed', 'pending')),
    details JSONB, -- Detailed action information

    -- Actor information
    initiated_by TEXT DEFAULT 'system',
    mcp_tool TEXT, -- Which MCP tool executed the action

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Foreign key to campaigns
    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns(campaign_id)
);

-- Campaign execution tracking
CREATE TABLE IF NOT EXISTS marketing.campaign_executions (
    id SERIAL PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    execution_step INTEGER NOT NULL, -- Step number in sequence
    step_type TEXT NOT NULL, -- email, linkedin_connect, phone_call, etc.

    -- Execution details
    scheduled_at TIMESTAMPTZ NOT NULL,
    executed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'executing', 'completed', 'failed', 'skipped')),

    -- Results
    response JSONB,
    error_message TEXT,

    -- Target information
    target_person_id TEXT NOT NULL, -- Barton ID of the person
    target_email TEXT,
    target_linkedin TEXT,

    FOREIGN KEY (campaign_id) REFERENCES marketing.campaigns(campaign_id)
);

-- Campaign templates (doctrine-approved blueprints)
CREATE TABLE IF NOT EXISTS marketing.campaign_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    template_type TEXT CHECK (template_type IN ('PLE', 'BIT')),

    -- Template structure
    blueprint JSONB NOT NULL,
    required_fields TEXT[], -- Fields that must be present in promoted records

    -- Doctrine compliance
    doctrine_approved BOOLEAN DEFAULT false,
    approval_date TIMESTAMPTZ,
    approved_by TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_campaigns_company_id ON marketing.campaigns(company_unique_id);
CREATE INDEX idx_campaigns_status ON marketing.campaigns(status);
CREATE INDEX idx_campaigns_type ON marketing.campaigns(campaign_type);
CREATE INDEX idx_campaign_audit_log_campaign_id ON marketing.campaign_audit_log(campaign_id);
CREATE INDEX idx_campaign_audit_log_created_at ON marketing.campaign_audit_log(created_at DESC);
CREATE INDEX idx_campaign_executions_campaign_id ON marketing.campaign_executions(campaign_id);
CREATE INDEX idx_campaign_executions_scheduled_at ON marketing.campaign_executions(scheduled_at);
CREATE INDEX idx_campaign_executions_status ON marketing.campaign_executions(status);

-- Insert default doctrine-approved templates
INSERT INTO marketing.campaign_templates (template_id, template_name, template_type, blueprint, required_fields, doctrine_approved, approved_by)
VALUES
(
    'PLE_INTRO_001',
    'PLE Introduction Campaign',
    'PLE',
    '{
        "trigger": "record_promoted",
        "conditions": {
            "marketing_score": ">= 80",
            "has_email": true,
            "has_linkedin": true
        },
        "sequence": [
            {
                "type": "email",
                "template": "intro_email",
                "delay": "0d",
                "content": {
                    "subject": "{{company_name}} - Strategic Partnership Opportunity",
                    "body": "doctrine_template_001"
                }
            },
            {
                "type": "linkedin_connect",
                "delay": "2d",
                "message": "doctrine_linkedin_001"
            },
            {
                "type": "phone_call",
                "delay": "7d",
                "script": "doctrine_call_001"
            },
            {
                "type": "email",
                "template": "follow_up",
                "delay": "14d",
                "content": {
                    "subject": "Re: Strategic Partnership Opportunity",
                    "body": "doctrine_template_002"
                }
            }
        ]
    }'::JSONB,
    ARRAY['email', 'linkedin_url', 'company_name', 'marketing_score'],
    true,
    'barton_doctrine'
),
(
    'BIT_SIGNAL_001',
    'BIT Signal Response Campaign',
    'BIT',
    '{
        "trigger": "bit_signal_fired",
        "conditions": {
            "signal_strength": ">= 70",
            "has_contact_info": true
        },
        "sequence": [
            {
                "type": "email",
                "template": "bit_response",
                "delay": "0h",
                "priority": "high",
                "content": {
                    "subject": "Immediate Response: {{signal_type}} Detected",
                    "body": "doctrine_bit_001"
                }
            },
            {
                "type": "sms",
                "delay": "1h",
                "condition": "no_email_open",
                "message": "doctrine_sms_001"
            },
            {
                "type": "phone_call",
                "delay": "4h",
                "priority": "high",
                "script": "doctrine_bit_call_001"
            }
        ]
    }'::JSONB,
    ARRAY['email', 'phone', 'signal_type', 'signal_strength'],
    true,
    'barton_doctrine'
);

-- Function to generate Barton Campaign ID
CREATE OR REPLACE FUNCTION marketing.generate_campaign_id(campaign_type TEXT)
RETURNS TEXT AS $$
DECLARE
    sequence_num INTEGER;
    campaign_id TEXT;
    type_code TEXT;
BEGIN
    -- Determine type code
    type_code := CASE
        WHEN campaign_type = 'PLE' THEN '04'
        WHEN campaign_type = 'BIT' THEN '05'
        ELSE '00'
    END;

    -- Get next sequence number
    SELECT COUNT(*) + 1 INTO sequence_num
    FROM marketing.campaigns
    WHERE campaign_type = campaign_type;

    -- Generate Barton ID: 05.01.02
    campaign_id := '04.04.03.' || type_code || '.' ||
                   LPAD(sequence_num::TEXT, 5, '0') || '.' ||
                   LPAD(FLOOR(RANDOM() * 1000)::TEXT, 3, '0');

    RETURN campaign_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION marketing.update_campaign_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_campaigns_timestamp
    BEFORE UPDATE ON marketing.campaigns
    FOR EACH ROW
    EXECUTE FUNCTION marketing.update_campaign_timestamp();

-- View for campaign analytics
CREATE OR REPLACE VIEW marketing.campaign_analytics AS
SELECT
    c.campaign_id,
    c.campaign_type,
    c.status,
    c.company_unique_id,
    array_length(c.people_ids, 1) as target_count,
    c.marketing_score,
    c.created_at,
    c.launched_at,
    COUNT(DISTINCT ce.id) FILTER (WHERE ce.status = 'completed') as completed_steps,
    COUNT(DISTINCT ce.id) FILTER (WHERE ce.status = 'failed') as failed_steps,
    COUNT(DISTINCT ce.id) FILTER (WHERE ce.status = 'pending') as pending_steps,
    MAX(cal.created_at) as last_action_at
FROM marketing.campaigns c
LEFT JOIN marketing.campaign_executions ce ON c.campaign_id = ce.campaign_id
LEFT JOIN marketing.campaign_audit_log cal ON c.campaign_id = cal.campaign_id
GROUP BY c.campaign_id, c.campaign_type, c.status, c.company_unique_id,
         c.people_ids, c.marketing_score, c.created_at, c.launched_at;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA marketing TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA marketing TO authenticated;
GRANT SELECT ON marketing.campaign_analytics TO authenticated;