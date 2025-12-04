"""
Stage 5B: Promote High-Confidence Matches to Company Vessels
============================================================
Promotes records from Stage 5 cleanup to company_vessels table:
- Firecrawl Upgraded (3 records) - score >= 0.78
- Splink High Confidence (959 records) - strong DOL match

Updates company_vessels with:
- confidence_tier = 'high'
- dol_match_status = 'matched'
- DOL enrichment data (EIN, participants, etc.)
"""

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import pandas as pd
import json
from datetime import datetime
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

FIRECRAWL_UPGRADED = os.path.join(OUTPUT_DIR, 'firecrawl_upgraded.csv')
SPLINK_HIGH = os.path.join(OUTPUT_DIR, 'splink_high_confidence.csv')
LOG_FILE = os.path.join(OUTPUT_DIR, 'logs', 'promotion_log.json')

# Database connection
DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

def load_promotion_candidates():
    """Load records to promote from CSV files."""
    candidates = []

    # Load Firecrawl upgraded
    if os.path.exists(FIRECRAWL_UPGRADED):
        df = pd.read_csv(FIRECRAWL_UPGRADED)
        for _, row in df.iterrows():
            # Handle both column naming conventions
            company_id = row.get('company_unique_id') or row.get('company_id')
            candidates.append({
                'company_unique_id': company_id,
                'source': 'firecrawl_upgrade',
                'match_score': row.get('enriched_score', 0.78),
                'dol_ein': row.get('best_ein_match'),
                'dol_name': row.get('sponsor_name') or row.get('scraped_title'),
                'dol_participants': None
            })
        print(f"  Loaded {len(df)} Firecrawl upgraded records")

    # Load Splink high confidence
    if os.path.exists(SPLINK_HIGH):
        df = pd.read_csv(SPLINK_HIGH)
        for _, row in df.iterrows():
            # Handle both column naming conventions
            company_id = row.get('company_unique_id') or row.get('company_id')
            candidates.append({
                'company_unique_id': company_id,
                'source': 'splink_high',
                'match_score': row.get('splink_confidence') or row.get('match_score', 0.85),
                'dol_ein': row.get('best_ein_match') or row.get('dol_ein'),
                'dol_name': row.get('sponsor_name') or row.get('dol_name'),
                'dol_participants': row.get('dol_participants')
            })
        print(f"  Loaded {len(df)} Splink high-confidence records")

    return candidates

def promote_to_company_master(conn, candidates):
    """Update company_master with EIN from DOL matches."""
    cur = conn.cursor()

    promoted = 0
    already_has_ein = 0
    not_found = 0
    errors = []

    for c in candidates:
        try:
            company_id = c['company_unique_id']
            if not company_id:
                continue

            # Check if company exists and current EIN status
            cur.execute("""
                SELECT ein FROM company.company_master
                WHERE company_unique_id = %s
            """, (company_id,))

            row = cur.fetchone()
            if not row:
                not_found += 1
                continue

            current_ein = row[0]
            if current_ein and len(str(current_ein)) >= 9:
                already_has_ein += 1
                continue

            # Update with EIN if we have one
            if c['dol_ein']:
                cur.execute("""
                    UPDATE company.company_master
                    SET ein = %s,
                        data_quality_score = COALESCE(data_quality_score, 0) + 0.1,
                        updated_at = NOW()
                    WHERE company_unique_id = %s
                """, (str(c['dol_ein']), company_id))
                promoted += 1

        except Exception as e:
            errors.append({'company_id': company_id, 'error': str(e)})

    conn.commit()
    cur.close()

    return {
        'promoted': promoted,
        'already_has_ein': already_has_ein,
        'not_found': not_found,
        'errors': errors
    }

def log_promotion_event(conn, candidates, results):
    """Log promotion event to company_events table."""
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO company.company_events
            (event_type, event_data, created_at)
            VALUES ('stage5_promotion', %s, NOW())
        """, (json.dumps({
            'total_candidates': len(candidates),
            'promoted': results.get('promoted', 0),
            'already_has_ein': results.get('already_has_ein', 0),
            'not_found': results.get('not_found', 0),
            'errors': len(results.get('errors', []))
        }),))
        conn.commit()
    except Exception as e:
        print(f"  Warning: Could not log event: {e}")

    cur.close()

def main():
    print("=" * 70)
    print("STAGE 5B: PROMOTE HIGH-CONFIDENCE MATCHES")
    print("=" * 70)
    print()

    start_time = datetime.now()

    # Load candidates
    print("[1] Loading promotion candidates...")
    candidates = load_promotion_candidates()
    print(f"  Total candidates: {len(candidates)}")
    print()

    if not candidates:
        print("No candidates to promote. Exiting.")
        return

    # Connect to database
    print("[2] Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("  Connected.")
    print()

    # Promote to company_master (update EIN)
    print("[3] Promoting EINs to company_master...")
    results = promote_to_company_master(conn, candidates)
    print(f"  EINs Updated: {results['promoted']}")
    print(f"  Already has EIN: {results['already_has_ein']}")
    print(f"  Not found: {results['not_found']}")
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
    print()

    # Log event
    print("[4] Logging promotion event...")
    log_promotion_event(conn, candidates, results)
    print("  Event logged.")
    print()

    # Get final counts
    print("[5] Verifying promotion...")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(ein) as with_ein,
            COUNT(*) - COUNT(ein) as without_ein
        FROM company.company_master
    """)
    row = cur.fetchone()
    print(f"  Total companies: {row['total']:,}")
    print(f"  With EIN: {row['with_ein']:,}")
    print(f"  Without EIN: {row['without_ein']:,}")

    cur.close()
    conn.close()

    # Save log
    end_time = datetime.now()
    log = {
        'started_at': start_time.isoformat(),
        'completed_at': end_time.isoformat(),
        'total_candidates': len(candidates),
        'eins_updated': results['promoted'],
        'already_has_ein': results['already_has_ein'],
        'not_found': results['not_found'],
        'errors': results['errors'][:10] if results['errors'] else []
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

    print()
    print("=" * 70)
    print("PROMOTION COMPLETE")
    print("=" * 70)
    print(f"  EINs promoted: {results['promoted']}")
    print(f"  Run time: {(end_time - start_time).total_seconds():.1f} seconds")
    print(f"  Log saved: {LOG_FILE}")

if __name__ == '__main__':
    main()
