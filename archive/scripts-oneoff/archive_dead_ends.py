"""
Archive dead-end companies (guessed patterns, no Hunter data, no DOL data)
Cleanup operation for Outreach v1.0
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def archive_dead_ends():
    """Archive companies with guessed email patterns but no validation data"""

    # Build connection string from Doppler env vars
    conn_str = f"postgresql://{os.getenv('NEON_USER')}:{os.getenv('NEON_PASSWORD')}@{os.getenv('NEON_HOST')}/{os.getenv('NEON_DATABASE')}?sslmode=require"

    conn = psycopg2.connect(conn_str)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        print("=" * 80)
        print("DEAD-END COMPANY ARCHIVE OPERATION")
        print("=" * 80)

        # Step 1: Create archive table
        print("\n[1/5] Creating archive table...")
        cur.execute("DROP TABLE IF EXISTS outreach.company_target_dead_ends;")
        cur.execute("""
            CREATE TABLE outreach.company_target_dead_ends (
                archive_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                outreach_id UUID NOT NULL,
                domain TEXT,
                email_method TEXT,
                method_type TEXT,
                confidence_score NUMERIC,
                archived_at TIMESTAMPTZ DEFAULT NOW(),
                archive_reason TEXT DEFAULT 'DEAD_END_NO_DATA'
            );
        """)
        conn.commit()
        print("✓ Archive table ready")

        # Step 2: Count dead-end companies
        print("\n[2/5] Identifying dead-end companies...")
        cur.execute("""
            SELECT COUNT(*) as dead_end_count
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            WHERE ct.email_method IS NOT NULL
              AND hc.domain IS NULL
              AND (d.ein IS NULL OR d.outreach_id IS NULL);
        """)
        result = cur.fetchone()
        dead_end_count = result['dead_end_count']
        print(f"✓ Found {dead_end_count:,} dead-end companies")

        if dead_end_count == 0:
            print("\n✓ No dead-end companies to archive. Exiting.")
            return

        # Step 3: Get breakdown by email method
        print("\n[3/5] Breakdown by email method:")
        cur.execute("""
            SELECT
                ct.email_method,
                COUNT(*) as count
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            WHERE ct.email_method IS NOT NULL
              AND hc.domain IS NULL
              AND (d.ein IS NULL OR d.outreach_id IS NULL)
            GROUP BY ct.email_method
            ORDER BY count DESC;
        """)

        methods = cur.fetchall()
        for method in methods:
            print(f"  {method['email_method']}: {method['count']:,}")

        # Step 4: Archive the dead ends
        print("\n[4/5] Archiving dead-end companies...")
        cur.execute("""
            INSERT INTO outreach.company_target_dead_ends (
                outreach_id, domain, email_method, method_type, confidence_score, archive_reason
            )
            SELECT
                o.outreach_id,
                o.domain,
                ct.email_method,
                ct.method_type,
                ct.confidence_score,
                'DEAD_END_NO_HUNTER_NO_DOL'
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            WHERE ct.email_method IS NOT NULL
              AND hc.domain IS NULL
              AND (d.ein IS NULL OR d.outreach_id IS NULL);
        """)
        archived_count = cur.rowcount
        conn.commit()
        print(f"✓ Archived {archived_count:,} companies to outreach.company_target_dead_ends")

        # Step 5: Mark as blocked in company_target
        print("\n[5/5] Updating execution_status to 'blocked' (archived in dead_ends table)...")
        cur.execute("""
            UPDATE outreach.company_target ct
            SET execution_status = 'blocked',
                updated_at = NOW()
            FROM outreach.outreach o
            LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            WHERE ct.outreach_id = o.outreach_id
              AND ct.email_method IS NOT NULL
              AND hc.domain IS NULL
              AND (d.ein IS NULL OR d.outreach_id IS NULL);
        """)
        updated_count = cur.rowcount
        conn.commit()
        print(f"✓ Updated {updated_count:,} company_target records to blocked status")

        # Final report
        print("\n" + "=" * 80)
        print("ARCHIVE COMPLETE")
        print("=" * 80)
        print(f"Companies archived: {archived_count:,}")
        print(f"Records updated: {updated_count:,}")
        print(f"Archive table: outreach.company_target_dead_ends")
        print(f"Archive reason: DEAD_END_NO_HUNTER_NO_DOL")
        print(f"Execution status: blocked (prevents marketing)")
        print("\nThese companies had guessed email patterns but no validation data")
        print("from Hunter or DOL. They are now blocked from marketing campaigns.")
        print("=" * 80)

        # Verify archive
        print("\n[VERIFICATION] Archive table sample (first 5 records):")
        cur.execute("""
            SELECT
                archive_id,
                domain,
                email_method,
                method_type,
                confidence_score,
                archived_at,
                archive_reason
            FROM outreach.company_target_dead_ends
            ORDER BY archived_at DESC
            LIMIT 5;
        """)

        samples = cur.fetchall()
        for i, sample in enumerate(samples, 1):
            print(f"\n  {i}. {sample['domain']}")
            print(f"     Method: {sample['email_method']}")
            print(f"     Type: {sample['method_type']}")
            print(f"     Confidence: {sample['confidence_score']}")
            print(f"     Reason: {sample['archive_reason']}")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ ERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    archive_dead_ends()
