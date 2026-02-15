#!/usr/bin/env python3
"""
PROMOTE PEOPLE TO OUTREACH
==========================
Uses cl.company_identity_bridge to link people_master to outreach.

Path: people_master -> bridge -> outreach.outreach -> outreach.people
"""

import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
import uuid

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def promote_people(cur, dry_run: bool) -> int:
    """
    Promote people from people_master to outreach.people using the bridge.
    """
    print("\n" + "=" * 60)
    print("PROMOTE PEOPLE TO OUTREACH")
    print("=" * 60)
    
    # Count promotable
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE pm.email_verified = true) as verified
        FROM people.people_master pm
        JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
        JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        LEFT JOIN outreach.people op ON o.outreach_id = op.outreach_id AND pm.email = op.email
        WHERE pm.email IS NOT NULL
        AND op.person_id IS NULL  -- Not already promoted
    """)
    r = cur.fetchone()
    print(f"  Promotable people: {r['total']}")
    print(f"  With verified email: {r['verified']}")
    
    if dry_run:
        print(f"\n  [DRY RUN] Would promote {r['total']} people")
        # Show samples
        cur.execute("""
            SELECT pm.first_name, pm.last_name, pm.email, o.domain
            FROM people.people_master pm
            JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
            JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
            JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN outreach.people op ON o.outreach_id = op.outreach_id AND pm.email = op.email
            WHERE pm.email IS NOT NULL
            AND op.person_id IS NULL
            LIMIT 10
        """)
        print("\n  Sample:")
        for row in cur.fetchall():
            print(f"    {row['first_name']} {row['last_name']} <{row['email']}> @ {row['domain']}")
        return r['total']
    
    # Perform the promotion
    cur.execute("""
        INSERT INTO outreach.people (
            person_id,
            target_id,
            company_unique_id,
            slot_type,
            email,
            email_verified,
            email_verified_at,
            contact_status,
            lifecycle_state,
            source,
            created_at,
            updated_at,
            outreach_id
        )
        SELECT 
            gen_random_uuid() as person_id,
            ct.target_id,
            COALESCE(ct.company_unique_id, b.company_sov_id::text) as company_unique_id,
            'OTHER' as slot_type,
            pm.email,
            pm.email_verified,
            pm.email_verified_at,
            'active' as contact_status,
            'SUSPECT'::outreach.lifecycle_state as lifecycle_state,
            'bridge_promotion' as source,
            NOW() as created_at,
            NOW() as updated_at,
            o.outreach_id
        FROM people.people_master pm
        JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
        JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
        JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        LEFT JOIN outreach.people op ON o.outreach_id = op.outreach_id AND pm.email = op.email
        WHERE pm.email IS NOT NULL
        AND op.person_id IS NULL
        ON CONFLICT DO NOTHING
    """)
    promoted = cur.rowcount
    print(f"\n  ✅ Promoted {promoted} people to outreach.people")
    
    return promoted


def main():
    parser = argparse.ArgumentParser(description='Promote people to outreach via bridge')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Preview changes without applying')
    args = parser.parse_args()
    
    print("=" * 60)
    print("PEOPLE PROMOTION VIA BRIDGE")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        promoted = promote_people(cur, args.dry_run)
        
        # Verify new state
        if not args.dry_run and promoted > 0:
            cur.execute("SELECT COUNT(*) as cnt FROM outreach.people")
            total = cur.fetchone()['cnt']
            print(f"\n  Total people in outreach.people: {total}")
            
            cur.execute("""
                SELECT COUNT(*) as cnt FROM outreach.people WHERE email_verified = true
            """)
            verified = cur.fetchone()['cnt']
            print(f"  Verified emails: {verified}")
        
        if args.dry_run:
            print("\n  [DRY RUN] No changes made. Run without --dry-run to apply.")
            conn.rollback()
        else:
            conn.commit()
            print("\n  ✅ All changes committed!")
            
    except Exception as e:
        conn.rollback()
        print(f"\n  ❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
