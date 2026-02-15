-- ═══════════════════════════════════════════════════════════════════════════════
-- ██████╗  ██████╗     ███╗   ██╗ ██████╗ ████████╗    ███╗   ███╗ ██████╗ ██████╗ ██╗███████╗██╗   ██╗
-- ██╔══██╗██╔═══██╗    ████╗  ██║██╔═══██╗╚══██╔══╝    ████╗ ████║██╔═══██╗██╔══██╗██║██╔════╝╚██╗ ██╔╝
-- ██║  ██║██║   ██║    ██╔██╗ ██║██║   ██║   ██║       ██╔████╔██║██║   ██║██║  ██║██║█████╗   ╚████╔╝
-- ██║  ██║██║   ██║    ██║╚██╗██║██║   ██║   ██║       ██║╚██╔╝██║██║   ██║██║  ██║██║██╔══╝    ╚██╔╝
-- ██████╔╝╚██████╔╝    ██║ ╚████║╚██████╔╝   ██║       ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║██║        ██║
-- ╚═════╝  ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝    ╚═╝       ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝        ╚═╝
-- ═══════════════════════════════════════════════════════════════════════════════
--
-- BIT Authorization System v2.0 - Phase 1: Distributed Signal Architecture
--
-- Authority: ADR-017
-- Date: 2026-01-26
-- Status: FROZEN (structure)
--
-- ARCHITECTURE PRINCIPLE:
--   Each sub-hub OWNS its own signal table.
--   Company Target OWNS a read-only view that unions all signal tables.
--   BIT is a COMPUTATION inside Company Target that reads the view.
--
-- SIGNAL TABLE CONTRACT (all hubs implement same structure):
--   company_id        TEXT NOT NULL       -- FK to company record
--   signal_type       VARCHAR(50)         -- e.g., 'renewal_proximity', 'slot_vacancy'
--   pressure_class    VARCHAR(30)         -- 'STRUCTURAL_PRESSURE', 'DECISION_SURFACE', 'NARRATIVE_VOLATILITY'
--   signal_value      JSONB               -- domain-specific payload
--   detected_at       TIMESTAMPTZ         -- when signal was detected
--   expires_at        TIMESTAMPTZ         -- validity window end
--   correlation_id    UUID                -- trace ID
--
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 0: SCHEMA CREATION
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS dol;
CREATE SCHEMA IF NOT EXISTS people;
CREATE SCHEMA IF NOT EXISTS blog;
CREATE SCHEMA IF NOT EXISTS company_target;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 1: ENUM TYPES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Pressure class domains (frozen logic)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pressure_domain') THEN
        CREATE TYPE pressure_domain AS ENUM (
            'STRUCTURAL_PRESSURE',      -- DOL: gravity, required for Band 3+
            'DECISION_SURFACE',         -- People: direction
            'NARRATIVE_VOLATILITY'      -- Blog: amplifier only
        );
    END IF;
END $$;

-- Pressure class types (frozen logic)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pressure_class_type') THEN
        CREATE TYPE pressure_class_type AS ENUM (
            'COST_PRESSURE',
            'VENDOR_DISSATISFACTION',
            'DEADLINE_PROXIMITY',
            'ORGANIZATIONAL_RECONFIGURATION',
            'OPERATIONAL_CHAOS'
        );
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 2: DOL PRESSURE SIGNALS TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- DOL Hub owns this table. Emits STRUCTURAL_PRESSURE signals.
-- Trust: HIGHEST - required for Band 3+

CREATE TABLE IF NOT EXISTS dol.pressure_signals (
    signal_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company reference
    company_unique_id   TEXT NOT NULL,

    -- Signal classification
    signal_type         VARCHAR(50) NOT NULL,
    pressure_domain     pressure_domain NOT NULL DEFAULT 'STRUCTURAL_PRESSURE',
    pressure_class      pressure_class_type,

    -- Signal payload (domain-specific evidence)
    signal_value        JSONB NOT NULL DEFAULT '{}',

    -- Magnitude (0-100 scale for BIT computation)
    magnitude           INTEGER NOT NULL DEFAULT 0 CHECK (magnitude >= 0 AND magnitude <= 100),

    -- Temporal validity
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,

    -- Traceability
    correlation_id      UUID,
    source_record_id    TEXT,  -- e.g., ack_id from form_5500

    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_dol_pressure_domain CHECK (pressure_domain = 'STRUCTURAL_PRESSURE')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_dol_signals_company ON dol.pressure_signals(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_dol_signals_type ON dol.pressure_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_dol_signals_expires ON dol.pressure_signals(expires_at);
CREATE INDEX IF NOT EXISTS idx_dol_signals_magnitude ON dol.pressure_signals(magnitude DESC);
CREATE INDEX IF NOT EXISTS idx_dol_signals_correlation ON dol.pressure_signals(correlation_id);

COMMENT ON TABLE dol.pressure_signals IS
'DOL Hub signal table. STRUCTURAL_PRESSURE domain.
Trust: HIGHEST - required for Band 3+ authorization.
Signals: renewal_proximity, cost_increase, broker_change, filing_anomaly.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 3: PEOPLE PRESSURE SIGNALS TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- People Hub owns this table. Emits DECISION_SURFACE signals.
-- Trust: MEDIUM - provides direction

CREATE TABLE IF NOT EXISTS people.pressure_signals (
    signal_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company reference
    company_unique_id   TEXT NOT NULL,

    -- Signal classification
    signal_type         VARCHAR(50) NOT NULL,
    pressure_domain     pressure_domain NOT NULL DEFAULT 'DECISION_SURFACE',
    pressure_class      pressure_class_type,

    -- Signal payload (domain-specific evidence)
    signal_value        JSONB NOT NULL DEFAULT '{}',

    -- Magnitude (0-100 scale for BIT computation)
    magnitude           INTEGER NOT NULL DEFAULT 0 CHECK (magnitude >= 0 AND magnitude <= 100),

    -- Temporal validity
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,

    -- Traceability
    correlation_id      UUID,
    source_record_id    TEXT,  -- e.g., person_id, slot_id

    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_people_pressure_domain CHECK (pressure_domain = 'DECISION_SURFACE')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_people_signals_company ON people.pressure_signals(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_signals_type ON people.pressure_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_people_signals_expires ON people.pressure_signals(expires_at);
CREATE INDEX IF NOT EXISTS idx_people_signals_magnitude ON people.pressure_signals(magnitude DESC);
CREATE INDEX IF NOT EXISTS idx_people_signals_correlation ON people.pressure_signals(correlation_id);

COMMENT ON TABLE people.pressure_signals IS
'People Hub signal table. DECISION_SURFACE domain.
Trust: MEDIUM - provides direction.
Signals: slot_vacancy, executive_movement, authority_gap, new_hire.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 4: BLOG PRESSURE SIGNALS TABLE
-- ═══════════════════════════════════════════════════════════════════════════════
-- Blog Hub owns this table. Emits NARRATIVE_VOLATILITY signals.
-- Trust: LOWEST - amplifier only, Blog alone = max Band 1

CREATE TABLE IF NOT EXISTS blog.pressure_signals (
    signal_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company reference
    company_unique_id   TEXT NOT NULL,

    -- Signal classification
    signal_type         VARCHAR(50) NOT NULL,
    pressure_domain     pressure_domain NOT NULL DEFAULT 'NARRATIVE_VOLATILITY',
    pressure_class      pressure_class_type,

    -- Signal payload (domain-specific evidence)
    signal_value        JSONB NOT NULL DEFAULT '{}',

    -- Magnitude (0-100 scale for BIT computation)
    magnitude           INTEGER NOT NULL DEFAULT 0 CHECK (magnitude >= 0 AND magnitude <= 100),

    -- Temporal validity
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,

    -- Traceability
    correlation_id      UUID,
    source_record_id    TEXT,  -- e.g., news_id, blog_post_id

    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_blog_pressure_domain CHECK (pressure_domain = 'NARRATIVE_VOLATILITY')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blog_signals_company ON blog.pressure_signals(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_blog_signals_type ON blog.pressure_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_blog_signals_expires ON blog.pressure_signals(expires_at);
CREATE INDEX IF NOT EXISTS idx_blog_signals_magnitude ON blog.pressure_signals(magnitude DESC);
CREATE INDEX IF NOT EXISTS idx_blog_signals_correlation ON blog.pressure_signals(correlation_id);

COMMENT ON TABLE blog.pressure_signals IS
'Blog Hub signal table. NARRATIVE_VOLATILITY domain.
Trust: LOWEST - amplifier only, Blog alone = max Band 1.
Signals: funding_announcement, news_mention, content_signal, growth_indicator.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 5: COMPANY TARGET UNION VIEW (READ-ONLY)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Company Target owns this view. Unions all signal tables.
-- BIT computation reads from this view.

CREATE OR REPLACE VIEW company_target.vw_all_pressure_signals AS
SELECT
    signal_id,
    company_unique_id,
    signal_type,
    pressure_domain,
    pressure_class,
    signal_value,
    magnitude,
    detected_at,
    expires_at,
    correlation_id,
    source_record_id,
    created_at,
    'dol' AS source_hub
FROM dol.pressure_signals
WHERE expires_at > NOW()

UNION ALL

SELECT
    signal_id,
    company_unique_id,
    signal_type,
    pressure_domain,
    pressure_class,
    signal_value,
    magnitude,
    detected_at,
    expires_at,
    correlation_id,
    source_record_id,
    created_at,
    'people' AS source_hub
FROM people.pressure_signals
WHERE expires_at > NOW()

UNION ALL

SELECT
    signal_id,
    company_unique_id,
    signal_type,
    pressure_domain,
    pressure_class,
    signal_value,
    magnitude,
    detected_at,
    expires_at,
    correlation_id,
    source_record_id,
    created_at,
    'blog' AS source_hub
FROM blog.pressure_signals
WHERE expires_at > NOW();

COMMENT ON VIEW company_target.vw_all_pressure_signals IS
'Union view of all active pressure signals from all hubs.
Company Target owns this view. BIT computation reads from here.
Filters: Only non-expired signals (expires_at > NOW()).
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 6: BIT COMPUTATION FUNCTION
-- ═══════════════════════════════════════════════════════════════════════════════
-- Company Target owns this function. Computes authorization band.
-- SIGNATURE FROZEN - Logic can evolve, signature cannot change.

CREATE OR REPLACE FUNCTION company_target.compute_authorization_band(
    p_company_id TEXT
)
RETURNS TABLE (
    company_unique_id TEXT,
    authorization_band INTEGER,
    band_name TEXT,
    dol_active BOOLEAN,
    people_active BOOLEAN,
    blog_active BOOLEAN,
    aligned_domains INTEGER,
    primary_pressure TEXT,
    total_magnitude INTEGER,
    band_capped_by TEXT
) AS $$
DECLARE
    v_dol_magnitude INTEGER := 0;
    v_people_magnitude INTEGER := 0;
    v_blog_magnitude INTEGER := 0;
    v_total_magnitude INTEGER := 0;
    v_dol_active BOOLEAN := FALSE;
    v_people_active BOOLEAN := FALSE;
    v_blog_active BOOLEAN := FALSE;
    v_aligned_domains INTEGER := 0;
    v_raw_band INTEGER := 0;
    v_final_band INTEGER := 0;
    v_band_name TEXT := 'SILENT';
    v_primary_pressure TEXT := NULL;
    v_band_capped_by TEXT := NULL;
BEGIN
    -- Calculate domain magnitudes from active signals
    SELECT COALESCE(SUM(magnitude), 0) INTO v_dol_magnitude
    FROM company_target.vw_all_pressure_signals
    WHERE company_unique_id = p_company_id
      AND pressure_domain = 'STRUCTURAL_PRESSURE';

    SELECT COALESCE(SUM(magnitude), 0) INTO v_people_magnitude
    FROM company_target.vw_all_pressure_signals
    WHERE company_unique_id = p_company_id
      AND pressure_domain = 'DECISION_SURFACE';

    SELECT COALESCE(SUM(magnitude), 0) INTO v_blog_magnitude
    FROM company_target.vw_all_pressure_signals
    WHERE company_unique_id = p_company_id
      AND pressure_domain = 'NARRATIVE_VOLATILITY';

    -- Determine domain activation (threshold: 10)
    v_dol_active := v_dol_magnitude >= 10;
    v_people_active := v_people_magnitude >= 10;
    v_blog_active := v_blog_magnitude >= 10;

    -- Count aligned domains
    v_aligned_domains :=
        CASE WHEN v_dol_active THEN 1 ELSE 0 END +
        CASE WHEN v_people_active THEN 1 ELSE 0 END +
        CASE WHEN v_blog_active THEN 1 ELSE 0 END;

    -- Calculate total magnitude (Blog amplifies, doesn't drive)
    -- DOL weight: 1.0, People weight: 0.8, Blog weight: 0.5 (amplifier only)
    v_total_magnitude :=
        v_dol_magnitude +
        (v_people_magnitude * 0.8)::INTEGER +
        (v_blog_magnitude * 0.5)::INTEGER;

    -- Get primary pressure class
    SELECT pressure_class::TEXT INTO v_primary_pressure
    FROM company_target.vw_all_pressure_signals
    WHERE company_unique_id = p_company_id
    ORDER BY magnitude DESC
    LIMIT 1;

    -- Calculate raw band from magnitude
    -- Band thresholds: 0=0-9, 1=10-24, 2=25-39, 3=40-59, 4=60-79, 5=80+
    v_raw_band := CASE
        WHEN v_total_magnitude >= 80 THEN 5
        WHEN v_total_magnitude >= 60 THEN 4
        WHEN v_total_magnitude >= 40 THEN 3
        WHEN v_total_magnitude >= 25 THEN 2
        WHEN v_total_magnitude >= 10 THEN 1
        ELSE 0
    END;

    -- Apply domain trust caps (FROZEN LOGIC)
    v_final_band := v_raw_band;

    -- Rule 1: Blog alone = max Band 1
    IF v_blog_active AND NOT v_dol_active AND NOT v_people_active THEN
        IF v_final_band > 1 THEN
            v_final_band := 1;
            v_band_capped_by := 'BLOG_ALONE_CAP';
        END IF;
    END IF;

    -- Rule 2: No DOL = max Band 2
    IF NOT v_dol_active THEN
        IF v_final_band > 2 THEN
            v_final_band := 2;
            v_band_capped_by := 'NO_DOL_CAP';
        END IF;
    END IF;

    -- Determine band name
    v_band_name := CASE v_final_band
        WHEN 0 THEN 'SILENT'
        WHEN 1 THEN 'WATCH'
        WHEN 2 THEN 'EXPLORATORY'
        WHEN 3 THEN 'TARGETED'
        WHEN 4 THEN 'ENGAGED'
        WHEN 5 THEN 'DIRECT'
        ELSE 'SILENT'
    END;

    RETURN QUERY SELECT
        p_company_id,
        v_final_band,
        v_band_name,
        v_dol_active,
        v_people_active,
        v_blog_active,
        v_aligned_domains,
        v_primary_pressure,
        v_total_magnitude,
        v_band_capped_by;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION company_target.compute_authorization_band(TEXT) IS
'Computes BIT authorization band for a company.
SIGNATURE FROZEN - Logic can evolve, signature cannot change.

Domain Trust Rules (FROZEN):
- Blog alone = max Band 1 (WATCH)
- No DOL = max Band 2 (EXPLORATORY)

Band Definitions (FROZEN):
- 0: SILENT (0-9) - No action permitted
- 1: WATCH (10-24) - Internal only
- 2: EXPLORATORY (25-39) - 1 educational / 60d
- 3: TARGETED (40-59) - Persona email, proof required
- 4: ENGAGED (60-79) - Phone allowed, multi-source proof
- 5: DIRECT (80+) - Full contact, full-chain proof

Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 7: CONVENIENCE VIEW FOR COMPANY AUTHORIZATION STATUS
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW company_target.vw_company_authorization AS
SELECT
    cm.company_unique_id,
    cm.company_name,
    auth.authorization_band,
    auth.band_name,
    auth.dol_active,
    auth.people_active,
    auth.blog_active,
    auth.aligned_domains,
    auth.primary_pressure,
    auth.total_magnitude,
    auth.band_capped_by
FROM marketing.company_master cm
CROSS JOIN LATERAL company_target.compute_authorization_band(cm.company_unique_id) auth;

COMMENT ON VIEW company_target.vw_company_authorization IS
'Convenience view showing authorization status for all companies.
Calls compute_authorization_band() for each company.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 8: TALENT FLOW BRIDGE ADAPTER
-- ═══════════════════════════════════════════════════════════════════════════════
-- Bridges existing talent_flow.movements to people.pressure_signals
-- Allows gradual migration without breaking existing Talent Flow integration

CREATE OR REPLACE FUNCTION people.bridge_talent_flow_movement()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process high-confidence executive movements
    IF NEW.confidence_score >= 70 AND NEW.movement_type IN ('hire', 'departure') THEN
        -- Check if title is executive-level
        IF NEW.new_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of'
           OR NEW.old_title ~* 'chief|ceo|cfo|coo|chro|cto|vp|vice president|director|head of' THEN

            -- Insert pressure signal for the affected company
            -- For hires: new company gets signal
            -- For departures: old company gets signal
            INSERT INTO people.pressure_signals (
                company_unique_id,
                signal_type,
                pressure_domain,
                pressure_class,
                signal_value,
                magnitude,
                detected_at,
                expires_at,
                source_record_id
            )
            SELECT
                CASE
                    WHEN NEW.movement_type = 'hire' THEN NEW.new_company_id
                    ELSE NEW.old_company_id
                END,
                'executive_movement',
                'DECISION_SURFACE',
                'ORGANIZATIONAL_RECONFIGURATION',
                jsonb_build_object(
                    'movement_id', NEW.movement_id,
                    'contact_id', NEW.contact_id,
                    'movement_type', NEW.movement_type,
                    'old_title', NEW.old_title,
                    'new_title', NEW.new_title,
                    'confidence_score', NEW.confidence_score,
                    'detected_source', NEW.detected_source
                ),
                LEAST(NEW.confidence_score::INTEGER, 40),  -- Cap at 40 per movement
                NEW.detected_at,
                NEW.detected_at + INTERVAL '365 days',
                NEW.movement_id::TEXT
            WHERE CASE
                    WHEN NEW.movement_type = 'hire' THEN NEW.new_company_id
                    ELSE NEW.old_company_id
                  END IS NOT NULL
              AND NOT EXISTS (
                  -- Prevent duplicates
                  SELECT 1 FROM people.pressure_signals
                  WHERE source_record_id = NEW.movement_id::TEXT
              );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to talent_flow.movements (if table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'talent_flow' AND table_name = 'movements'
    ) THEN
        DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON talent_flow.movements;
        CREATE TRIGGER trg_bridge_to_pressure_signals
            AFTER INSERT ON talent_flow.movements
            FOR EACH ROW
            EXECUTE FUNCTION people.bridge_talent_flow_movement();

        RAISE NOTICE 'Talent Flow bridge trigger created on talent_flow.movements';
    ELSE
        RAISE NOTICE 'talent_flow.movements does not exist - bridge trigger skipped';
    END IF;
END $$;

COMMENT ON FUNCTION people.bridge_talent_flow_movement() IS
'Bridge adapter: Converts talent_flow.movements to people.pressure_signals.
Allows gradual migration without breaking existing Talent Flow integration.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 9: DOL RENEWAL SIGNAL BRIDGE
-- ═══════════════════════════════════════════════════════════════════════════════
-- Bridges dol.renewal_calendar to dol.pressure_signals

CREATE OR REPLACE FUNCTION dol.bridge_renewal_calendar()
RETURNS TRIGGER AS $$
DECLARE
    v_magnitude INTEGER;
    v_pressure_class pressure_class_type;
BEGIN
    -- Calculate magnitude based on days until renewal
    -- 30d = 70, 60d = 55, 90d = 45, 120d = 35
    v_magnitude := CASE
        WHEN NEW.days_until_renewal <= 30 THEN 70
        WHEN NEW.days_until_renewal <= 60 THEN 55
        WHEN NEW.days_until_renewal <= 90 THEN 45
        WHEN NEW.days_until_renewal <= 120 THEN 35
        ELSE 25
    END;

    -- Determine pressure class
    v_pressure_class := 'DEADLINE_PROXIMITY';

    -- Insert or update pressure signal
    INSERT INTO dol.pressure_signals (
        company_unique_id,
        signal_type,
        pressure_domain,
        pressure_class,
        signal_value,
        magnitude,
        detected_at,
        expires_at,
        source_record_id
    ) VALUES (
        NEW.company_unique_id,
        'renewal_proximity',
        'STRUCTURAL_PRESSURE',
        v_pressure_class,
        jsonb_build_object(
            'renewal_id', NEW.renewal_id,
            'renewal_date', NEW.renewal_date,
            'days_until_renewal', NEW.days_until_renewal,
            'plan_name', NEW.plan_name,
            'carrier_name', NEW.carrier_name
        ),
        v_magnitude,
        NOW(),
        COALESCE(NEW.renewal_date, NOW()) + INTERVAL '30 days',  -- Signal expires 30d after renewal
        NEW.renewal_id::TEXT
    )
    ON CONFLICT DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to dol.renewal_calendar (if table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'dol' AND table_name = 'renewal_calendar'
    ) THEN
        DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON dol.renewal_calendar;
        CREATE TRIGGER trg_bridge_to_pressure_signals
            AFTER INSERT OR UPDATE ON dol.renewal_calendar
            FOR EACH ROW
            EXECUTE FUNCTION dol.bridge_renewal_calendar();

        RAISE NOTICE 'DOL renewal bridge trigger created on dol.renewal_calendar';
    ELSE
        RAISE NOTICE 'dol.renewal_calendar does not exist - bridge trigger skipped';
    END IF;
END $$;

COMMENT ON FUNCTION dol.bridge_renewal_calendar() IS
'Bridge adapter: Converts dol.renewal_calendar to dol.pressure_signals.
Magnitude based on days_until_renewal: 30d=70, 60d=55, 90d=45, 120d=35.
Authority: ADR-017';

-- ═══════════════════════════════════════════════════════════════════════════════
-- PHASE 10: VERIFICATION
-- ═══════════════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    v_dol_signals BOOLEAN;
    v_people_signals BOOLEAN;
    v_blog_signals BOOLEAN;
    v_union_view BOOLEAN;
    v_compute_func BOOLEAN;
BEGIN
    -- Check tables
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'dol' AND table_name = 'pressure_signals'
    ) INTO v_dol_signals;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'people' AND table_name = 'pressure_signals'
    ) INTO v_people_signals;

    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'blog' AND table_name = 'pressure_signals'
    ) INTO v_blog_signals;

    -- Check view
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views
        WHERE table_schema = 'company_target' AND table_name = 'vw_all_pressure_signals'
    ) INTO v_union_view;

    -- Check function
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'company_target' AND p.proname = 'compute_authorization_band'
    ) INTO v_compute_func;

    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE 'BIT v2 Phase 1 Distributed Signals Migration Complete';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Signal Tables:';
    RAISE NOTICE '  dol.pressure_signals:       %', CASE WHEN v_dol_signals THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '  people.pressure_signals:    %', CASE WHEN v_people_signals THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '  blog.pressure_signals:      %', CASE WHEN v_blog_signals THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '';
    RAISE NOTICE 'Company Target Components:';
    RAISE NOTICE '  vw_all_pressure_signals:    %', CASE WHEN v_union_view THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '  compute_authorization_band: %', CASE WHEN v_compute_func THEN 'OK' ELSE 'MISSING' END;
    RAISE NOTICE '';
    RAISE NOTICE 'Architecture:';
    RAISE NOTICE '  Each hub owns its signal table';
    RAISE NOTICE '  Company Target owns union view + BIT computation';
    RAISE NOTICE '  Talent Flow bridge: people.bridge_talent_flow_movement()';
    RAISE NOTICE '  DOL renewal bridge: dol.bridge_renewal_calendar()';
    RAISE NOTICE '';
    RAISE NOTICE 'Authority: ADR-017';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- END MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROLLBACK SCRIPT (DO NOT EXECUTE UNLESS REQUIRED)
-- ═══════════════════════════════════════════════════════════════════════════════
/*
-- To rollback this migration, execute the following:

-- 1. Drop bridge triggers
DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON talent_flow.movements;
DROP TRIGGER IF EXISTS trg_bridge_to_pressure_signals ON dol.renewal_calendar;

-- 2. Drop bridge functions
DROP FUNCTION IF EXISTS people.bridge_talent_flow_movement();
DROP FUNCTION IF EXISTS dol.bridge_renewal_calendar();

-- 3. Drop convenience view
DROP VIEW IF EXISTS company_target.vw_company_authorization;

-- 4. Drop BIT computation function
DROP FUNCTION IF EXISTS company_target.compute_authorization_band(TEXT);

-- 5. Drop union view
DROP VIEW IF EXISTS company_target.vw_all_pressure_signals;

-- 6. Drop signal tables (CAUTION: Data loss)
DROP TABLE IF EXISTS blog.pressure_signals;
DROP TABLE IF EXISTS people.pressure_signals;
DROP TABLE IF EXISTS dol.pressure_signals;

-- 7. Drop enum types (optional - may be used elsewhere)
-- DROP TYPE IF EXISTS pressure_class_type;
-- DROP TYPE IF EXISTS pressure_domain;

-- Note: Schemas are NOT dropped as they may contain other objects.
*/
-- ═══════════════════════════════════════════════════════════════════════════════
