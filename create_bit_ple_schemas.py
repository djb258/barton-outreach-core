#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create BIT (Buyer Intent Tool) and PLE (Perpetual Lead Engine) schemas and tables.
These connect to the marketing core for signal detection and automated nurture loops.

CTB Classification Metadata:
CTB Branch: data/migrations
Barton ID: 04.05.01 (BIT), 04.06.01 (PLE)
Unique ID: CTB-BITPLE
Enforcement: ORBT
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_existing_tables(cur):
    """Check if BIT and PLE tables already exist."""
    
    print("\n" + "="*100)
    print("CHECKING EXISTING TABLES")
    print("="*100 + "\n")
    
    # Check BIT schema tables
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'BIT'
        ORDER BY table_name
    """)
    
    bit_tables = [row['table_name'] for row in cur.fetchall()]
    
    # Check PLE schema tables
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'PLE'
        ORDER BY table_name
    """)
    
    ple_tables = [row['table_name'] for row in cur.fetchall()]
    
    print(f"BIT Schema: {len(bit_tables)} existing tables")
    if bit_tables:
        for table in bit_tables:
            print(f"  - {table}")
    else:
        print("  (empty - ready for creation)")
    
    print(f"\nPLE Schema: {len(ple_tables)} existing tables")
    if ple_tables:
        for table in ple_tables:
            print(f"  - {table}")
    else:
        print("  (empty - ready for creation)")
    
    print()
    
    return bit_tables, ple_tables

def create_bit_tables(cur):
    """Create BIT (Buyer Intent Tool) tables."""
    
    print("="*100)
    print("CREATING BIT (BUYER INTENT TOOL) TABLES")
    print("="*100 + "\n")
    
    # First ensure schema exists
    print("[0/3] Creating BIT schema...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS BIT")
    print("     [OK] BIT schema ready\n")
    
    print("[1/3] Creating bit.bit_signal...")
    
    cur.execute("""
        -- ============================================================================
        -- BIT (Buyer Intent Tool) - Signal Tracking
        -- ============================================================================
        -- CTB Branch: data/migrations/bit
        -- Barton ID: 04.05.01
        -- Purpose: Track buying intent signals from multiple sources
        -- ============================================================================
        
        CREATE TABLE IF NOT EXISTS BIT.bit_signal (
            signal_id SERIAL PRIMARY KEY,
            
            -- Links to Marketing Core
            company_unique_id TEXT NOT NULL
                CONSTRAINT fk_signal_company 
                REFERENCES marketing.company_master(company_unique_id)
                ON DELETE CASCADE,
            
            contact_unique_id TEXT
                CONSTRAINT fk_signal_contact
                REFERENCES marketing.people_master(unique_id)
                ON DELETE SET NULL,
            
            -- Signal Details
            signal_type TEXT NOT NULL,  -- 'email_open', 'linkedin_click', 'site_visit', 'form_fill', 'content_download'
            signal_strength INTEGER DEFAULT 5 CHECK (signal_strength BETWEEN 1 AND 10),
            
            -- Source & Context
            source TEXT NOT NULL,  -- 'instantly', 'linkedin', 'hubspot', 'website', 'apollo'
            source_campaign_id TEXT,
            source_url TEXT,
            metadata JSONB,
            
            -- Timestamps
            captured_at TIMESTAMP DEFAULT now(),
            processed_at TIMESTAMP,
            
            -- Barton Doctrine
            CONSTRAINT bit_signal_type_valid
                CHECK (signal_type IN ('email_open', 'email_click', 'linkedin_view', 'linkedin_click', 
                                       'site_visit', 'form_fill', 'content_download', 'reply', 
                                       'meeting_booked', 'phone_answered'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_signal_company ON BIT.bit_signal(company_unique_id);
        CREATE INDEX IF NOT EXISTS idx_signal_contact ON BIT.bit_signal(contact_unique_id);
        CREATE INDEX IF NOT EXISTS idx_signal_type ON BIT.bit_signal(signal_type);
        CREATE INDEX IF NOT EXISTS idx_signal_strength ON BIT.bit_signal(signal_strength DESC);
        CREATE INDEX IF NOT EXISTS idx_signal_captured ON BIT.bit_signal(captured_at DESC);
        
        COMMENT ON TABLE BIT.bit_signal IS 
            'Tracks buying intent signals from email, LinkedIn, website, and other sources. Each signal indicates prospect engagement level.';
    """)
    
    print("     [OK] bit.bit_signal created")
    
    print("[2/3] Creating bit.bit_company_score...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS BIT.bit_company_score (
            company_unique_id TEXT PRIMARY KEY
                CONSTRAINT fk_company_score
                REFERENCES marketing.company_master(company_unique_id)
                ON DELETE CASCADE,
            
            -- Scoring
            score INTEGER DEFAULT 0 CHECK (score >= 0),
            signal_count INTEGER DEFAULT 0,
            last_signal_at TIMESTAMP,
            
            -- Score Breakdown
            email_score INTEGER DEFAULT 0,
            linkedin_score INTEGER DEFAULT 0,
            website_score INTEGER DEFAULT 0,
            
            -- Metadata
            score_tier TEXT,  -- 'hot', 'warm', 'cold', 'frozen'
            last_updated TIMESTAMP DEFAULT now(),
            
            -- Auto-update tier based on score
            CONSTRAINT score_tier_valid
                CHECK (score_tier IN ('hot', 'warm', 'cold', 'frozen'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_company_score_tier ON BIT.bit_company_score(score_tier);
        CREATE INDEX IF NOT EXISTS idx_company_score_value ON BIT.bit_company_score(score DESC);
        CREATE INDEX IF NOT EXISTS idx_company_last_signal ON BIT.bit_company_score(last_signal_at DESC);
        
        COMMENT ON TABLE BIT.bit_company_score IS 
            'Aggregated buying intent score per company. Updated by triggers when new signals arrive.';
    """)
    
    print("     [OK] bit.bit_company_score created")
    
    print("[3/3] Creating bit.bit_contact_score...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS BIT.bit_contact_score (
            contact_unique_id TEXT PRIMARY KEY
                CONSTRAINT fk_contact_score
                REFERENCES marketing.people_master(unique_id)
                ON DELETE CASCADE,
            
            -- Scoring
            score INTEGER DEFAULT 0 CHECK (score >= 0),
            signal_count INTEGER DEFAULT 0,
            last_signal_at TIMESTAMP,
            
            -- Engagement Metrics
            email_opens INTEGER DEFAULT 0,
            email_clicks INTEGER DEFAULT 0,
            linkedin_views INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            
            -- Status
            engagement_tier TEXT,  -- 'engaged', 'interested', 'passive', 'cold'
            last_updated TIMESTAMP DEFAULT now(),
            
            CONSTRAINT engagement_tier_valid
                CHECK (engagement_tier IN ('engaged', 'interested', 'passive', 'cold'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_contact_score_tier ON BIT.bit_contact_score(engagement_tier);
        CREATE INDEX IF NOT EXISTS idx_contact_score_value ON BIT.bit_contact_score(score DESC);
        CREATE INDEX IF NOT EXISTS idx_contact_last_signal ON BIT.bit_contact_score(last_signal_at DESC);
        
        COMMENT ON TABLE BIT.bit_contact_score IS 
            'Individual contact engagement scores. Tracks how actively each person is engaging with outreach.';
    """)
    
    print("     [OK] bit.bit_contact_score created")
    print()
    
    return True

def create_ple_tables(cur):
    """Create PLE (Perpetual Lead Engine) tables."""
    
    print("="*100)
    print("CREATING PLE (PERPETUAL LEAD ENGINE) TABLES")
    print("="*100 + "\n")
    
    # First ensure schema exists
    print("[0/3] Creating PLE schema...")
    cur.execute("CREATE SCHEMA IF NOT EXISTS PLE")
    print("     [OK] PLE schema ready\n")
    
    print("[1/3] Creating ple.ple_cycle...")
    
    cur.execute("""
        -- ============================================================================
        -- PLE (Perpetual Lead Engine) - Automated Nurture Cycles
        -- ============================================================================
        -- CTB Branch: data/migrations/ple
        -- Barton ID: 04.06.01
        -- Purpose: Automated follow-ups, re-engagement, and lead recycling
        -- ============================================================================
        
        CREATE TABLE IF NOT EXISTS PLE.ple_cycle (
            cycle_id SERIAL PRIMARY KEY,
            
            -- Links to Marketing Core
            company_unique_id TEXT NOT NULL
                CONSTRAINT fk_cycle_company
                REFERENCES marketing.company_master(company_unique_id)
                ON DELETE CASCADE,
            
            contact_unique_id TEXT
                CONSTRAINT fk_cycle_contact
                REFERENCES marketing.people_master(unique_id)
                ON DELETE CASCADE,
            
            -- Cycle Configuration
            cycle_type TEXT NOT NULL,  -- 'initial_outreach', 'nurture', 'recycle', 'reactivation'
            stage TEXT NOT NULL,  -- 'initial', 'follow_up_1', 'follow_up_2', 'nurture', 'recycle', 'won', 'lost'
            
            -- Status & Timing
            status TEXT DEFAULT 'active' 
                CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
            started_at TIMESTAMP DEFAULT now(),
            last_step_at TIMESTAMP,
            next_step_at TIMESTAMP,
            completed_at TIMESTAMP,
            
            -- Metrics
            steps_completed INTEGER DEFAULT 0,
            total_touchpoints INTEGER DEFAULT 0,
            response_received BOOLEAN DEFAULT FALSE,
            meeting_booked BOOLEAN DEFAULT FALSE,
            
            -- Metadata
            campaign_id TEXT,
            notes TEXT,
            
            CONSTRAINT ple_cycle_type_valid
                CHECK (cycle_type IN ('initial_outreach', 'nurture', 'recycle', 'reactivation', 'renewal')),
            
            CONSTRAINT ple_stage_valid
                CHECK (stage IN ('initial', 'follow_up_1', 'follow_up_2', 'follow_up_3', 
                                'nurture', 'recycle', 'won', 'lost', 'unresponsive'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_cycle_company ON PLE.ple_cycle(company_unique_id);
        CREATE INDEX IF NOT EXISTS idx_cycle_contact ON PLE.ple_cycle(contact_unique_id);
        CREATE INDEX IF NOT EXISTS idx_cycle_status ON PLE.ple_cycle(status) WHERE status = 'active';
        CREATE INDEX IF NOT EXISTS idx_cycle_next_step ON PLE.ple_cycle(next_step_at) WHERE status = 'active';
        CREATE INDEX IF NOT EXISTS idx_cycle_stage ON PLE.ple_cycle(stage);
        
        COMMENT ON TABLE PLE.ple_cycle IS 
            'Tracks automated nurture cycles for each contact/company. Manages multi-touch sequences and re-engagement loops.';
    """)
    
    print("     [OK] ple.ple_cycle created")
    
    print("[2/3] Creating ple.ple_step...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS PLE.ple_step (
            step_id SERIAL PRIMARY KEY,
            
            -- Link to Cycle
            cycle_id INTEGER NOT NULL
                CONSTRAINT fk_step_cycle
                REFERENCES PLE.ple_cycle(cycle_id)
                ON DELETE CASCADE,
            
            -- Step Details
            step_number INTEGER NOT NULL,
            step_type TEXT NOT NULL,  -- 'email', 'linkedin_message', 'phone_call', 'sms', 'wait'
            step_name TEXT,
            
            -- Scheduling
            scheduled_for TIMESTAMP,
            executed_at TIMESTAMP,
            
            -- Execution
            status TEXT DEFAULT 'pending'
                CHECK (status IN ('pending', 'scheduled', 'sent', 'delivered', 'opened', 
                                 'clicked', 'replied', 'failed', 'skipped')),
            
            result TEXT,
            error_message TEXT,
            
            -- Content
            template_used TEXT,
            message_content TEXT,
            subject_line TEXT,
            
            -- Response Tracking
            response_received_at TIMESTAMP,
            response_type TEXT,  -- 'positive', 'negative', 'neutral', 'auto_reply'
            
            -- Metadata
            metadata JSONB,
            
            CONSTRAINT ple_step_type_valid
                CHECK (step_type IN ('email', 'linkedin_message', 'linkedin_connect', 
                                    'phone_call', 'sms', 'wait', 'webhook', 'internal_note'))
        );
        
        CREATE INDEX IF NOT EXISTS idx_step_cycle ON PLE.ple_step(cycle_id);
        CREATE INDEX IF NOT EXISTS idx_step_scheduled ON PLE.ple_step(scheduled_for) WHERE status IN ('pending', 'scheduled');
        CREATE INDEX IF NOT EXISTS idx_step_status ON PLE.ple_step(status);
        CREATE INDEX IF NOT EXISTS idx_step_type ON PLE.ple_step(step_type);
        
        COMMENT ON TABLE PLE.ple_step IS 
            'Individual steps within a nurture cycle. Each step is a touchpoint (email, LinkedIn, call) with scheduling and response tracking.';
    """)
    
    print("     [OK] ple.ple_step created")
    
    print("[3/3] Creating ple.ple_log...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS PLE.ple_log (
            log_id SERIAL PRIMARY KEY,
            
            -- Links
            cycle_id INTEGER
                CONSTRAINT fk_log_cycle
                REFERENCES PLE.ple_cycle(cycle_id)
                ON DELETE SET NULL,
            
            contact_unique_id TEXT
                CONSTRAINT fk_log_contact
                REFERENCES marketing.people_master(unique_id)
                ON DELETE SET NULL,
            
            -- Log Details
            action TEXT NOT NULL,  -- 'cycle_started', 'step_executed', 'response_received', 'cycle_completed'
            result TEXT,
            
            -- Metadata
            details JSONB,
            logged_at TIMESTAMP DEFAULT now(),
            logged_by TEXT  -- Agent or system that created this log
        );
        
        CREATE INDEX IF NOT EXISTS idx_log_cycle ON PLE.ple_log(cycle_id);
        CREATE INDEX IF NOT EXISTS idx_log_contact ON PLE.ple_log(contact_unique_id);
        CREATE INDEX IF NOT EXISTS idx_log_action ON PLE.ple_log(action);
        CREATE INDEX IF NOT EXISTS idx_log_timestamp ON PLE.ple_log(logged_at DESC);
        
        COMMENT ON TABLE PLE.ple_log IS 
            'Audit trail for all PLE cycle activities. Tracks every action, result, and state change.';
    """)
    
    print("     [OK] ple.ple_log created")
    print()
    
    return True

def create_helper_views(cur):
    """Create helpful views for BIT and PLE monitoring."""
    
    print("="*100)
    print("CREATING MONITORING VIEWS")
    print("="*100 + "\n")
    
    print("[1/2] Creating BIT monitoring views...")
    
    # Hot companies view
    cur.execute("""
        CREATE OR REPLACE VIEW BIT.vw_hot_companies AS
        SELECT 
            cm.company_unique_id,
            cm.company_name,
            COALESCE(bcs.score, 0) as company_score,
            COALESCE(bcs.signal_count, 0) as signal_count,
            bcs.score_tier,
            bcs.last_signal_at,
            COUNT(DISTINCT pm.unique_id) as contact_count
        FROM marketing.company_master cm
        LEFT JOIN BIT.bit_company_score bcs ON cm.company_unique_id = bcs.company_unique_id
        LEFT JOIN marketing.people_master pm ON cm.company_unique_id = pm.company_unique_id
        WHERE bcs.score_tier IN ('hot', 'warm')
           OR bcs.last_signal_at > NOW() - INTERVAL '7 days'
        GROUP BY cm.company_unique_id, cm.company_name, bcs.score, bcs.signal_count, 
                 bcs.score_tier, bcs.last_signal_at
        ORDER BY bcs.score DESC NULLS LAST;
        
        COMMENT ON VIEW BIT.vw_hot_companies IS 
            'Companies with recent or high-value buying intent signals. Prime targets for immediate outreach.';
    """)
    
    # Engaged contacts view
    cur.execute("""
        CREATE OR REPLACE VIEW BIT.vw_engaged_contacts AS
        SELECT 
            pm.unique_id,
            pm.full_name,
            pm.email,
            pm.title,
            cm.company_name,
            COALESCE(bct.score, 0) as engagement_score,
            bct.engagement_tier,
            bct.email_opens,
            bct.email_clicks,
            bct.linkedin_views,
            bct.replies,
            bct.last_signal_at
        FROM marketing.people_master pm
        JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
        LEFT JOIN BIT.bit_contact_score bct ON pm.unique_id = bct.contact_unique_id
        WHERE bct.engagement_tier IN ('engaged', 'interested')
           OR bct.last_signal_at > NOW() - INTERVAL '7 days'
        ORDER BY bct.score DESC NULLS LAST;
        
        COMMENT ON VIEW BIT.vw_engaged_contacts IS 
            'Contacts showing active engagement. Ready for next-step actions.';
    """)
    
    print("     [OK] BIT views created")
    
    print("[2/2] Creating PLE monitoring views...")
    
    # Active cycles view
    cur.execute("""
        CREATE OR REPLACE VIEW PLE.vw_active_cycles AS
        SELECT 
            pc.cycle_id,
            pc.cycle_type,
            pc.stage,
            pc.status,
            cm.company_name,
            pm.full_name,
            pm.email,
            pc.steps_completed,
            pc.next_step_at,
            pc.response_received,
            pc.meeting_booked,
            (pc.next_step_at < NOW()) as overdue
        FROM PLE.ple_cycle pc
        JOIN marketing.company_master cm ON pc.company_unique_id = cm.company_unique_id
        LEFT JOIN marketing.people_master pm ON pc.contact_unique_id = pm.unique_id
        WHERE pc.status = 'active'
        ORDER BY pc.next_step_at NULLS LAST;
        
        COMMENT ON VIEW PLE.vw_active_cycles IS 
            'All active nurture cycles with next action dates. Shows what needs attention now.';
    """)
    
    # Pending steps view
    cur.execute("""
        CREATE OR REPLACE VIEW PLE.vw_pending_steps AS
        SELECT 
            ps.step_id,
            ps.cycle_id,
            ps.step_number,
            ps.step_type,
            ps.scheduled_for,
            cm.company_name,
            pm.full_name,
            pm.email,
            pc.stage,
            (ps.scheduled_for < NOW()) as overdue
        FROM PLE.ple_step ps
        JOIN PLE.ple_cycle pc ON ps.cycle_id = pc.cycle_id
        JOIN marketing.company_master cm ON pc.company_unique_id = cm.company_unique_id
        LEFT JOIN marketing.people_master pm ON pc.contact_unique_id = pm.unique_id
        WHERE ps.status IN ('pending', 'scheduled')
          AND pc.status = 'active'
        ORDER BY ps.scheduled_for NULLS LAST;
        
        COMMENT ON VIEW PLE.vw_pending_steps IS 
            'Upcoming touchpoints that need execution. Queue for automation engines.';
    """)
    
    print("     [OK] PLE views created")
    print()
    
    return True

def show_summary(cur):
    """Show summary of created tables."""
    
    print("="*100)
    print("SCHEMA CREATION SUMMARY")
    print("="*100 + "\n")
    
    # Count BIT tables
    cur.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = 'BIT' AND table_type = 'BASE TABLE'
    """)
    bit_count = cur.fetchone()['count']
    
    # Count BIT views
    cur.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.views
        WHERE table_schema = 'BIT'
    """)
    bit_views = cur.fetchone()['count']
    
    # Count PLE tables
    cur.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.tables
        WHERE table_schema = 'PLE' AND table_type = 'BASE TABLE'
    """)
    ple_count = cur.fetchone()['count']
    
    # Count PLE views
    cur.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.views
        WHERE table_schema = 'PLE'
    """)
    ple_views = cur.fetchone()['count']
    
    print("BIT (Buyer Intent Tool):")
    print(f"  Tables: {bit_count}")
    print(f"  Views: {bit_views}")
    print("  Purpose: Signal detection & engagement scoring")
    print()
    
    print("PLE (Perpetual Lead Engine):")
    print(f"  Tables: {ple_count}")
    print(f"  Views: {ple_views}")
    print("  Purpose: Automated nurture cycles & re-engagement")
    print()
    
    print("="*100)
    print("INTEGRATION POINTS")
    print("="*100 + "\n")
    
    print("BIT connects to:")
    print("  - marketing.company_master (company signals)")
    print("  - marketing.people_master (contact engagement)")
    print()
    
    print("PLE connects to:")
    print("  - marketing.company_master (cycle targets)")
    print("  - marketing.people_master (contact sequences)")
    print("  - marketing.people_resolution_queue (triggers when contacts resolved)")
    print()
    
    print("="*100)
    print("READY FOR AGENT DEPLOYMENT")
    print("="*100)
    print()
    print("[BIT] Signal Ingestion Examples:")
    print()
    print("-- Record email open signal")
    print("INSERT INTO BIT.bit_signal (company_unique_id, contact_unique_id, signal_type, signal_strength, source)")
    print("VALUES ('04.04.01.XX.XXXXX.XXX', '04.04.02.XX.XXXXX.XXX', 'email_open', 3, 'instantly');")
    print()
    print("-- Record LinkedIn profile view")
    print("INSERT INTO BIT.bit_signal (company_unique_id, contact_unique_id, signal_type, signal_strength, source)")
    print("VALUES ('04.04.01.XX.XXXXX.XXX', '04.04.02.XX.XXXXX.XXX', 'linkedin_view', 5, 'linkedin');")
    print()
    print("[PLE] Cycle Creation Examples:")
    print()
    print("-- Start nurture cycle for new contact")
    print("INSERT INTO PLE.ple_cycle (company_unique_id, contact_unique_id, cycle_type, stage)")
    print("VALUES ('04.04.01.XX.XXXXX.XXX', '04.04.02.XX.XXXXX.XXX', 'initial_outreach', 'initial');")
    print()
    print("-- Add follow-up step")
    print("INSERT INTO PLE.ple_step (cycle_id, step_number, step_type, scheduled_for, step_name)")
    print("VALUES (1, 1, 'email', NOW() + INTERVAL '3 days', 'Initial email');")
    print()
    print("="*100 + "\n")

def main():
    """Main execution."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    print("\n" + "="*100)
    print("BIT & PLE SCHEMA INITIALIZATION")
    print("="*100)
    print("\nPurpose:")
    print("  BIT (Buyer Intent Tool): Track engagement signals and score leads")
    print("  PLE (Perpetual Lead Engine): Automate nurture cycles and re-engagement")
    print()
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check existing tables
        bit_tables, ple_tables = check_existing_tables(cur)
        
        # Create BIT tables if needed
        if len(bit_tables) < 3:
            if not create_bit_tables(cur):
                print("[FAILED] BIT table creation failed")
                conn.rollback()
                return
            conn.commit()
            print("[COMMITTED] BIT tables created\n")
        else:
            print("[INFO] BIT tables already exist, skipping creation\n")
        
        # Create PLE tables if needed
        if len(ple_tables) < 3:
            if not create_ple_tables(cur):
                print("[FAILED] PLE table creation failed")
                conn.rollback()
                return
            conn.commit()
            print("[COMMITTED] PLE tables created\n")
        else:
            print("[INFO] PLE tables already exist, skipping creation\n")
        
        # Create helper views
        if not create_helper_views(cur):
            print("[FAILED] View creation failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Monitoring views created\n")
        
        # Show summary
        show_summary(cur)
        
        cur.close()
        conn.close()
        
        print("\n[SUCCESS] BIT and PLE schemas are now operational!")
        print("\n[READY FOR]")
        print("  1. Signal ingestion from email/LinkedIn/website")
        print("  2. Automated scoring and tier assignment")
        print("  3. Nurture cycle automation")
        print("  4. Re-engagement workflows")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == "__main__":
    main()

