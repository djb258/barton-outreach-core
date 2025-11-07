#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup messaging system for marketing automation.
Adds message key tracking to people_master and creates message reference table.

CTB Classification Metadata:
CTB Branch: data/migrations
Barton ID: 04.04.07
Unique ID: CTB-MESSAGING
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

def add_message_key_column(cur):
    """Step 1: Add message_key_scheduled to people_master."""
    
    print("\n" + "="*100)
    print("STEP 1: ADD MESSAGE KEY TRACKING TO people_master")
    print("="*100 + "\n")
    
    print("Adding message_key_scheduled column...")
    
    try:
        cur.execute("""
            ALTER TABLE marketing.people_master
            ADD COLUMN IF NOT EXISTS message_key_scheduled TEXT;
            
            COMMENT ON COLUMN marketing.people_master.message_key_scheduled IS
                'References message_key_reference for next scheduled message. Format: MSG.ROLE.TYPE.VERSION';
        """)
        
        print("[OK] Column added to marketing.people_master")
        print("     Column: message_key_scheduled (TEXT)")
        print("     Purpose: Track which message template is scheduled for each contact")
        print()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    
    return True

def create_message_reference_table(cur):
    """Step 2: Create message_key_reference table."""
    
    print("="*100)
    print("STEP 2: CREATE MESSAGE KEY REFERENCE TABLE")
    print("="*100 + "\n")
    
    print("Creating marketing.message_key_reference...")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS marketing.message_key_reference (
            message_key TEXT PRIMARY KEY,              -- Format: MSG.ROLE.TYPE.VERSION
            role TEXT NOT NULL,                        -- e.g., CEO, CFO, HR
            message_type TEXT NOT NULL,                -- e.g., cold_intro, job_change
            trigger_condition TEXT,                    -- e.g., 'new_contact', 'bit.title_change_detected'
            vibeos_template_id TEXT,                   -- Optional, maps to VibeOS template
            message_channel TEXT,                      -- e.g., email, linkedin, both
            
            -- Content metadata
            subject_line TEXT,
            preview_text TEXT,
            
            -- Timing
            send_delay_hours INTEGER DEFAULT 0,       -- How long to wait before sending
            optimal_send_time TEXT,                    -- e.g., '9:00 AM', 'business_hours'
            
            -- Status
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            -- Constraints
            CONSTRAINT message_key_format
                CHECK (message_key ~ '^MSG\.[A-Z]+\.[0-9]{3}\.[A-Z]$'),
            
            CONSTRAINT message_role_valid
                CHECK (role IN ('CEO', 'CFO', 'HR', 'ALL')),
            
            CONSTRAINT message_channel_valid
                CHECK (message_channel IN ('email', 'linkedin', 'sms', 'both', 'multi'))
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_message_role ON marketing.message_key_reference(role);
        CREATE INDEX IF NOT EXISTS idx_message_type ON marketing.message_key_reference(message_type);
        CREATE INDEX IF NOT EXISTS idx_message_active ON marketing.message_key_reference(active) WHERE active = TRUE;
        
        COMMENT ON TABLE marketing.message_key_reference IS
            'Master reference for all message templates and their routing logic. Links to VibeOS templates and defines triggers.';
    """)
    
    print("[OK] Table created: marketing.message_key_reference")
    print("     Primary Key: message_key (format: MSG.ROLE.TYPE.VERSION)")
    print("     Tracks: Templates, triggers, channels, timing")
    print()
    
    return True

def seed_message_keys(cur):
    """Step 3: Seed with example message keys."""
    
    print("="*100)
    print("STEP 3: SEED MESSAGE KEYS")
    print("="*100 + "\n")
    
    print("Inserting starter message templates...")
    
    message_keys = [
        ('MSG.CEO.001.A', 'CEO', 'cold_intro', 'new_contact', 'vibeos_ceo_intro_a', 'email', 
         'Transforming Benefits Management for Growing Companies', 'Quick question about your benefits strategy...', 0, '9:00 AM'),
        
        ('MSG.CFO.002.A', 'CFO', 'job_change', 'bit.title_change_detected', 'vibeos_cfo_job_a', 'linkedin', 
         'Congrats on the new role!', 'Saw your recent move - exploring cost optimization?', 24, 'business_hours'),
        
        ('MSG.HR.001.B', 'HR', 'cold_intro', 'new_contact', 'vibeos_hr_intro_b', 'email',
         'Simplifying Benefits for Your HR Team', 'Reduce admin time and complexity...', 0, '10:00 AM'),
        
        ('MSG.HR.003.A', 'HR', 'reengage', 'no_reply_30d', 'vibeos_hr_reengage', 'email',
         'Following up: Benefits Management Solutions', 'Circling back on our previous conversation...', 0, '2:00 PM'),
        
        ('MSG.CEO.004.B', 'CEO', 'sniper_followup', 'bit.click_detected', 'vibeos_ceo_clickfollow_b', 'both',
         'I noticed you checked out our site', 'Quick question about what caught your attention...', 2, 'business_hours'),
        
        ('MSG.CFO.005.A', 'CFO', 'cold_intro', 'new_contact', 'vibeos_cfo_intro_a', 'email',
         'Cut Benefits Costs Without Cutting Coverage', 'CFO-focused cost optimization strategy...', 0, '8:00 AM'),
        
        ('MSG.CEO.006.A', 'CEO', 'renewal_window', 'bit.renewal_window_open', 'vibeos_ceo_renewal', 'both',
         'Your Benefits Renewal is Coming Up', 'Lock in savings before your renewal deadline...', 0, 'business_hours'),
        
        ('MSG.HR.007.A', 'HR', 'linkedin_intro', 'new_contact', 'vibeos_hr_linkedin_a', 'linkedin',
         'Connecting: HR Innovation in WV', 'Would love to share some benefits automation insights...', 0, 'business_hours'),
    ]
    
    from psycopg2.extras import execute_values
    
    insert_query = """
        INSERT INTO marketing.message_key_reference 
        (message_key, role, message_type, trigger_condition, vibeos_template_id, message_channel,
         subject_line, preview_text, send_delay_hours, optimal_send_time)
        VALUES %s
        ON CONFLICT (message_key) DO NOTHING
    """
    
    execute_values(cur, insert_query, message_keys)
    
    inserted = cur.rowcount
    
    print(f"[OK] Inserted {inserted} message templates")
    print()
    
    # Show what was inserted
    cur.execute("""
        SELECT message_key, role, message_type, message_channel, subject_line
        FROM marketing.message_key_reference
        ORDER BY role, message_key
    """)
    
    templates = cur.fetchall()
    
    print("Message Templates Created:")
    print("-"*100)
    for t in templates:
        print(f"  {t['message_key']} - {t['role']} - {t['message_type']}")
        print(f"    Channel: {t['message_channel']}")
        print(f"    Subject: {t['subject_line']}")
    
    print()
    
    return True

def show_usage_examples(cur):
    """Show how to use the messaging system."""
    
    print("="*100)
    print("USAGE EXAMPLES")
    print("="*100 + "\n")
    
    print("1. Assign message to a contact:")
    print("-"*100)
    print("""
UPDATE marketing.people_master
SET message_key_scheduled = 'MSG.CEO.001.A'
WHERE unique_id = '04.04.02.XX.XXXXX.XXX';
""")
    
    print("2. Get all CEOs ready for cold intro:")
    print("-"*100)
    print("""
SELECT 
    pm.unique_id,
    pm.full_name,
    pm.email,
    mkr.subject_line,
    mkr.message_channel
FROM marketing.people_master pm
JOIN marketing.company_slots cs ON pm.company_slot_unique_id = cs.company_slot_unique_id
LEFT JOIN marketing.message_key_reference mkr ON pm.message_key_scheduled = mkr.message_key
WHERE cs.slot_type = 'CEO'
  AND pm.message_key_scheduled IS NULL
  AND pm.email_verified = TRUE
LIMIT 100;
""")
    
    print("3. Get contacts ready to send (with template details):")
    print("-"*100)
    print("""
SELECT 
    pm.unique_id,
    pm.full_name,
    pm.email,
    cm.company_name,
    mkr.message_key,
    mkr.subject_line,
    mkr.message_channel,
    mkr.vibeos_template_id
FROM marketing.people_master pm
JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
JOIN marketing.message_key_reference mkr ON pm.message_key_scheduled = mkr.message_key
WHERE mkr.active = TRUE
  AND pm.email IS NOT NULL;
""")
    
    print("4. Add new message template:")
    print("-"*100)
    print("""
INSERT INTO marketing.message_key_reference 
(message_key, role, message_type, trigger_condition, message_channel, subject_line)
VALUES 
('MSG.CFO.010.A', 'CFO', 'budget_season', 'bit.q4_detected', 'email', 
 'Q4 Budget Planning: Benefits Cost Optimization');
""")
    
    print()
    print("="*100 + "\n")

def main():
    """Main execution."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    print("\n" + "="*100)
    print("MESSAGING SYSTEM SETUP")
    print("="*100)
    print("\nThis will:")
    print("  1. Add message_key_scheduled column to people_master")
    print("  2. Create message_key_reference table")
    print("  3. Seed with 8 starter message templates")
    print()
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Step 1
        if not add_message_key_column(cur):
            print("[FAILED] Column addition failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Column added\n")
        
        # Step 2
        if not create_message_reference_table(cur):
            print("[FAILED] Table creation failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Reference table created\n")
        
        # Step 3
        if not seed_message_keys(cur):
            print("[FAILED] Seeding failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Message templates seeded\n")
        
        # Show usage
        show_usage_examples(cur)
        
        # Final verification
        print("="*100)
        print("VERIFICATION")
        print("="*100 + "\n")
        
        cur.execute("SELECT COUNT(*) as count FROM marketing.message_key_reference")
        template_count = cur.fetchone()['count']
        
        print(f"Message templates: {template_count}")
        print(f"People table updated: marketing.people_master.message_key_scheduled added")
        print(f"Status: READY FOR MESSAGE SCHEDULING")
        
        print("\n" + "="*100)
        print("MESSAGING SYSTEM OPERATIONAL!")
        print("="*100)
        print("\nNext steps:")
        print("  1. Assign message keys to contacts based on role and state")
        print("  2. Integrate with VibeOS for template rendering")
        print("  3. Use BIT signals to trigger message key changes")
        print("  4. Create PLE cycles that reference message keys")
        print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == "__main__":
    main()

