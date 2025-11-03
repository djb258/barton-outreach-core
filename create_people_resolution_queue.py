#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create marketing.people_resolution_queue table and populate with missing/invalid contacts.
This is the doctrine-compliant working queue for AI/human triage & repair.

CTB Classification Metadata:
CTB Branch: data/migrations
Barton ID: 04.04.06
Unique ID: CTB-PEOPLEQUEUE
Enforcement: ORBT
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def create_resolution_queue_table(cur):
    """Create the people_resolution_queue table."""
    
    print("\n" + "="*100)
    print("CREATING marketing.people_resolution_queue TABLE")
    print("="*100 + "\n")
    
    print("Creating table structure...")
    
    cur.execute("""
        -- ============================================================================
        -- CTB Classification Metadata
        -- ============================================================================
        -- CTB Branch: data/migrations/outreach-process-manager
        -- Barton ID: 04.04.06
        -- Unique ID: CTB-PEOPLEQUEUE
        -- Last Updated: 2025-11-03
        -- Enforcement: ORBT
        -- ============================================================================
        
        CREATE TABLE IF NOT EXISTS marketing.people_resolution_queue (
            queue_id SERIAL PRIMARY KEY,
            
            -- Company & Slot Links
            company_unique_id TEXT NOT NULL
                CONSTRAINT fk_queue_company 
                REFERENCES marketing.company_master(company_unique_id)
                ON DELETE CASCADE,
            
            company_slot_unique_id TEXT NOT NULL
                CONSTRAINT fk_queue_slot
                REFERENCES marketing.company_slots(company_slot_unique_id)
                ON DELETE CASCADE,
            
            slot_type TEXT,
            
            -- Issue Details
            existing_email TEXT,
            issue_type TEXT NOT NULL,  -- 'missing_contact', 'bad_email', 'duplicate', 'invalid_data'
            priority INTEGER DEFAULT 5,  -- 1=urgent, 10=low
            
            -- Status & Resolution
            status TEXT DEFAULT 'pending' 
                CHECK (status IN ('pending', 'in_progress', 'resolved', 'escalated', 'failed')),
            resolved_contact_id TEXT,  -- Link to people_master.unique_id if fixed
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT now(),
            last_touched_at TIMESTAMP,
            resolved_at TIMESTAMP,
            
            -- Agent Tracking
            touched_by TEXT,  -- Agent or tool that last handled this
            assigned_to TEXT,  -- Which agent should handle this (Amplify, Abacus, Human)
            
            -- Metadata
            notes TEXT,
            error_details JSONB,
            attempt_count INTEGER DEFAULT 0,
            
            -- Barton Doctrine Compliance
            CONSTRAINT queue_issue_type_valid
                CHECK (issue_type IN ('missing_contact', 'bad_email', 'duplicate', 'invalid_data', 'unverified_email', 'incomplete_profile'))
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_queue_status 
            ON marketing.people_resolution_queue(status) 
            WHERE status IN ('pending', 'in_progress');
        
        CREATE INDEX IF NOT EXISTS idx_queue_company 
            ON marketing.people_resolution_queue(company_unique_id);
        
        CREATE INDEX IF NOT EXISTS idx_queue_slot 
            ON marketing.people_resolution_queue(company_slot_unique_id);
        
        CREATE INDEX IF NOT EXISTS idx_queue_priority 
            ON marketing.people_resolution_queue(priority, created_at);
        
        CREATE INDEX IF NOT EXISTS idx_queue_assigned 
            ON marketing.people_resolution_queue(assigned_to) 
            WHERE status = 'in_progress';
        
        -- Add comments for documentation
        COMMENT ON TABLE marketing.people_resolution_queue IS 
            'Doctrine-compliant working queue for missing, invalid, or incomplete contact data. Acts as firebreak and control plane for AI agents (Amplify, Abacus) and human triage.';
        
        COMMENT ON COLUMN marketing.people_resolution_queue.issue_type IS 
            'Type of issue: missing_contact (empty slot), bad_email (bounced/invalid), duplicate (already exists), invalid_data (failed validation), unverified_email (needs verification), incomplete_profile (missing LinkedIn/phone)';
        
        COMMENT ON COLUMN marketing.people_resolution_queue.assigned_to IS 
            'Which agent/tool should handle: Amplify (LinkedIn enrichment), Abacus (email verification), Human (manual review)';
    """)
    
    print("[OK] Table created successfully")
    print("     - Primary key: queue_id (auto-increment)")
    print("     - Foreign keys: company_unique_id, company_slot_unique_id")
    print("     - Status tracking: pending → in_progress → resolved")
    print("     - Agent assignment: Amplify, Abacus, Human")
    print()
    
    return True

def populate_missing_contacts(cur):
    """Detect and queue all empty slots (missing contacts)."""
    
    print("="*100)
    print("DETECTING MISSING CONTACTS")
    print("="*100 + "\n")
    
    print("Finding empty slots (slots without people)...")
    
    # Find all empty slots
    cur.execute("""
        SELECT
            cm.company_unique_id,
            cm.company_name,
            cs.company_slot_unique_id,
            cs.slot_type
        FROM marketing.company_master cm
        JOIN marketing.company_slots cs ON cm.company_unique_id = cs.company_unique_id
        LEFT JOIN marketing.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
        WHERE pm.unique_id IS NULL
        ORDER BY cm.company_name, cs.slot_type
    """)
    
    missing_slots = cur.fetchall()
    
    print(f"Found {len(missing_slots):,} empty slots\n")
    
    if len(missing_slots) == 0:
        print("[INFO] All slots are filled!")
        return True
    
    # Count by slot type
    slot_breakdown = {}
    for slot in missing_slots:
        slot_type = slot['slot_type']
        slot_breakdown[slot_type] = slot_breakdown.get(slot_type, 0) + 1
    
    print("Breakdown by role:")
    for role, count in sorted(slot_breakdown.items()):
        print(f"  {role}: {count:,} empty slots")
    print()
    
    print(f"Inserting {len(missing_slots):,} issues into resolution queue...")
    
    # Determine priority and assignment based on slot type
    def get_priority_and_assignment(slot_type):
        if slot_type == 'CEO':
            return 1, 'Amplify'  # High priority, LinkedIn enrichment
        elif slot_type == 'CFO':
            return 2, 'Amplify'  # High priority, LinkedIn enrichment
        elif slot_type == 'HR':
            return 3, 'Amplify'  # Medium priority, LinkedIn enrichment
        else:
            return 5, 'Human'  # Low priority, manual review
    
    # Insert into queue
    queue_records = []
    for slot in missing_slots:
        priority, assigned_to = get_priority_and_assignment(slot['slot_type'])
        
        queue_records.append((
            slot['company_unique_id'],
            slot['company_slot_unique_id'],
            slot['slot_type'],
            None,  # existing_email
            'missing_contact',  # issue_type
            priority,
            'pending',  # status
            assigned_to,  # assigned_to
            f"Empty {slot['slot_type']} slot for {slot['company_name']}"  # notes
        ))
    
    # Bulk insert
    from psycopg2.extras import execute_values
    
    insert_query = """
        INSERT INTO marketing.people_resolution_queue 
        (company_unique_id, company_slot_unique_id, slot_type, 
         existing_email, issue_type, priority, status, assigned_to, notes)
        VALUES %s
    """
    
    execute_values(cur, insert_query, queue_records, page_size=500)
    
    print(f"[OK] Inserted {len(queue_records):,} missing contact issues")
    print()
    
    return True

def populate_unverified_emails(cur):
    """Queue contacts with unverified emails."""
    
    print("="*100)
    print("DETECTING UNVERIFIED EMAILS")
    print("="*100 + "\n")
    
    print("Finding contacts with unverified emails...")
    
    # Find contacts with email but not verified
    cur.execute("""
        SELECT
            pm.unique_id,
            pm.company_unique_id,
            pm.company_slot_unique_id,
            pm.email,
            pm.email_verified,
            cm.company_name
        FROM marketing.people_master pm
        JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
        WHERE pm.email IS NOT NULL
          AND pm.email_verified = FALSE
    """)
    
    unverified = cur.fetchall()
    
    print(f"Found {len(unverified):,} unverified emails\n")
    
    if len(unverified) == 0:
        print("[INFO] All emails are verified!")
        return True
    
    print(f"Inserting {len(unverified):,} email verification tasks...")
    
    # Insert into queue
    queue_records = []
    for contact in unverified:
        queue_records.append((
            contact['company_unique_id'],
            contact['company_slot_unique_id'],
            None,  # slot_type (already filled)
            contact['email'],
            'unverified_email',
            4,  # priority
            'pending',
            'Abacus',  # assigned to email verification agent
            f"Verify email for {contact['company_name']}"
        ))
    
    from psycopg2.extras import execute_values
    
    insert_query = """
        INSERT INTO marketing.people_resolution_queue 
        (company_unique_id, company_slot_unique_id, slot_type, 
         existing_email, issue_type, priority, status, assigned_to, notes)
        VALUES %s
    """
    
    execute_values(cur, insert_query, queue_records, page_size=500)
    
    print(f"[OK] Inserted {len(queue_records):,} email verification tasks")
    print()
    
    return True

def show_queue_summary(cur):
    """Display queue summary and statistics."""
    
    print("="*100)
    print("RESOLUTION QUEUE SUMMARY")
    print("="*100 + "\n")
    
    # Total count
    cur.execute("SELECT COUNT(*) as count FROM marketing.people_resolution_queue")
    total = cur.fetchone()['count']
    
    print(f"Total queue items: {total:,}\n")
    
    # By issue type
    cur.execute("""
        SELECT 
            issue_type,
            COUNT(*) as count,
            MIN(priority) as min_priority
        FROM marketing.people_resolution_queue
        GROUP BY issue_type
        ORDER BY MIN(priority), COUNT(*) DESC
    """)
    
    issues = cur.fetchall()
    
    print("By Issue Type:")
    for issue in issues:
        print(f"  {issue['issue_type']}: {issue['count']:,} (priority: {issue['min_priority']})")
    print()
    
    # By assigned agent
    cur.execute("""
        SELECT 
            assigned_to,
            COUNT(*) as count
        FROM marketing.people_resolution_queue
        WHERE status = 'pending'
        GROUP BY assigned_to
        ORDER BY COUNT(*) DESC
    """)
    
    agents = cur.fetchall()
    
    print("Assigned to Agents (pending tasks):")
    for agent in agents:
        print(f"  {agent['assigned_to']}: {agent['count']:,} tasks")
    print()
    
    # By slot type for missing contacts
    cur.execute("""
        SELECT 
            slot_type,
            COUNT(*) as count
        FROM marketing.people_resolution_queue
        WHERE issue_type = 'missing_contact'
        GROUP BY slot_type
        ORDER BY COUNT(*) DESC
    """)
    
    slots = cur.fetchall()
    
    print("Missing Contacts by Role:")
    for slot in slots:
        print(f"  {slot['slot_type']}: {slot['count']:,} empty slots")
    print()
    
    # Sample tasks
    cur.execute("""
        SELECT 
            queue_id,
            issue_type,
            status,
            assigned_to,
            notes
        FROM marketing.people_resolution_queue
        ORDER BY priority, created_at
        LIMIT 5
    """)
    
    samples = cur.fetchall()
    
    print("Next 5 Tasks (highest priority):")
    for i, task in enumerate(samples, 1):
        print(f"  {i}. [#{task['queue_id']}] {task['issue_type']}")
        print(f"     Status: {task['status']} | Assigned: {task['assigned_to']}")
        print(f"     {task['notes']}")
    
    print("\n" + "="*100)
    print("QUEUE READY FOR AGENT PROCESSING")
    print("="*100)
    print(f"  Total tasks: {total:,}")
    print(f"  Pending: {sum(a['count'] for a in agents):,}")
    print(f"  Agents ready: Amplify (LinkedIn), Abacus (Email), Human (Manual)")
    print("="*100 + "\n")

def main():
    """Main execution."""
    
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    print("\n" + "="*100)
    print("PEOPLE RESOLUTION QUEUE - SETUP & POPULATION")
    print("="*100)
    print("\nThis will:")
    print("  1. Create marketing.people_resolution_queue table")
    print("  2. Detect all empty slots (missing contacts)")
    print("  3. Detect unverified emails")
    print("  4. Populate queue with tasks for AI agents")
    print()
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Step 1: Create table
        if not create_resolution_queue_table(cur):
            print("[FAILED] Table creation failed")
            return
        
        conn.commit()
        print("[COMMITTED] Table created\n")
        
        # Step 2: Populate with missing contacts
        if not populate_missing_contacts(cur):
            print("[FAILED] Missing contact detection failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Missing contacts queued\n")
        
        # Step 3: Populate with unverified emails
        if not populate_unverified_emails(cur):
            print("[FAILED] Unverified email detection failed")
            conn.rollback()
            return
        
        conn.commit()
        print("[COMMITTED] Unverified emails queued\n")
        
        # Step 4: Show summary
        show_queue_summary(cur)
        
        cur.close()
        conn.close()
        
        print("\n[SUCCESS] Resolution queue created and populated!")
        print("\n[NEXT STEPS]")
        print("  1. Amplify Agent: Pull tasks with assigned_to='Amplify' for LinkedIn enrichment")
        print("  2. Abacus Agent: Pull tasks with assigned_to='Abacus' for email verification")
        print("  3. Human Review: Check tasks with status='escalated'")
        print()
        print("[SQL EXAMPLES]")
        print()
        print("-- Get next task for Amplify:")
        print("SELECT * FROM marketing.people_resolution_queue")
        print("WHERE assigned_to = 'Amplify' AND status = 'pending'")
        print("ORDER BY priority, created_at LIMIT 1;")
        print()
        print("-- Mark task in progress:")
        print("UPDATE marketing.people_resolution_queue")
        print("SET status = 'in_progress', last_touched_at = NOW(), touched_by = 'amplify_v1'")
        print("WHERE queue_id = 123;")
        print()
        print("-- Mark task resolved:")
        print("UPDATE marketing.people_resolution_queue")
        print("SET status = 'resolved', resolved_at = NOW(), resolved_contact_id = '04.04.02.XX.XXXXX.XXX'")
        print("WHERE queue_id = 123;")
        print()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()

if __name__ == "__main__":
    main()

