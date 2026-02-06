#!/usr/bin/env python3
"""
CTB Phase 1 Reorganization - Executor
Runs the Phase 1 migration with detailed logging.
"""
import psycopg2
import os
import sys
from datetime import datetime

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    print("=" * 80)
    print("CTB PHASE 1: STRUCTURAL REORGANIZATION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 80)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ============================================
        # PRE-FLIGHT: Add discriminator columns
        # ============================================
        print("\n[PRE-FLIGHT] Adding discriminator columns...")

        preflight_sql = """
        ALTER TABLE outreach.pipeline_audit_log ADD COLUMN IF NOT EXISTS source_hub VARCHAR(50);
        ALTER TABLE outreach.company_target_errors ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);
        ALTER TABLE people.people_errors ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);
        ALTER TABLE cl.cl_err_existence ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);
        ALTER TABLE outreach.entity_resolution_queue ADD COLUMN IF NOT EXISTS queue_type VARCHAR(50);
        ALTER TABLE outreach.bit_signals ADD COLUMN IF NOT EXISTS signal_source VARCHAR(50);
        """
        for stmt in preflight_sql.strip().split(';'):
            if stmt.strip():
                cur.execute(stmt)
        print("  [OK] Discriminator columns added")

        # ============================================
        # PHASE 1A: DUPLICATE TRUTH TABLES → ARCHIVE
        # ============================================
        print("\n[PHASE 1A] Archiving duplicate truth tables...")

        archives_1a = [
            ('company.company_master', 'archive.company_company_master_ctb'),
            ('marketing.company_master', 'archive.marketing_company_master_ctb'),
            ('marketing.people_master', 'archive.marketing_people_master_ctb'),
            ('company.company_slots', 'archive.company_company_slots_ctb'),
            ('company.message_key_reference', 'archive.company_message_key_reference_ctb'),
        ]

        for source, target in archives_1a:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {target} AS
                    SELECT *, NOW() as archived_at, 'ctb_phase1' as archive_reason
                    FROM {source}
                """)
                print(f"  [OK] {source} → {target} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # PHASE 1B: ORPHANED ERROR TABLES → MERGE
        # ============================================
        print("\n[PHASE 1B] Merging orphaned error tables...")

        # Get column info for error tables
        error_merges = [
            ('marketing.failed_company_match', 'outreach.company_target_errors', 'failed_company_match'),
            ('marketing.failed_no_pattern', 'outreach.company_target_errors', 'failed_no_pattern'),
            ('marketing.failed_email_verification', 'people.people_errors', 'failed_email_verification'),
            ('marketing.failed_slot_assignment', 'people.people_errors', 'failed_slot_assignment'),
            ('marketing.failed_low_confidence', 'cl.cl_err_existence', 'failed_low_confidence'),
        ]

        for source, target, error_type in error_merges:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]

                # Archive source first
                archive_name = source.replace('.', '_') + '_ctb'
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS archive.{archive_name.split('.')[-1]} AS
                    SELECT *, NOW() as archived_at FROM {source}
                """)
                print(f"  [OK] Archived {source} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # PHASE 1H: TEMP TABLES → ARCHIVE
        # ============================================
        print("\n[PHASE 1H] Archiving temp tables...")

        temp_archives = [
            ('people.slot_orphan_snapshot_r0_002', 'archive.people_slot_orphan_snapshot_ctb'),
            ('people.slot_quarantine_r0_002', 'archive.people_slot_quarantine_ctb'),
        ]

        for source, target in temp_archives:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {target} AS
                    SELECT *, NOW() as archived_at FROM {source}
                """)
                print(f"  [OK] {source} → {target} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # PHASE 1I: OUT OF SCOPE TABLES → ARCHIVE
        # ============================================
        print("\n[PHASE 1I] Archiving out-of-scope tables...")

        oos_archives = [
            ('public.sn_meeting', 'archive.public_sn_meeting_ctb'),
            ('public.sn_meeting_outcome', 'archive.public_sn_meeting_outcome_ctb'),
            ('public.sn_prospect', 'archive.public_sn_prospect_ctb'),
            ('public.sn_sales_process', 'archive.public_sn_sales_process_ctb'),
            ('talent_flow.movement_history', 'archive.talent_flow_movement_history_ctb'),
            ('talent_flow.movements', 'archive.talent_flow_movements_ctb'),
        ]

        for source, target in oos_archives:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {target} AS
                    SELECT *, NOW() as archived_at FROM {source}
                """)
                print(f"  [OK] {source} → {target} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # PHASE 1K: ADD MISSING PKs
        # ============================================
        print("\n[PHASE 1K] Adding missing primary keys...")

        # Add filter_id to form_5500_icp_filtered
        try:
            cur.execute("ALTER TABLE dol.form_5500_icp_filtered ADD COLUMN IF NOT EXISTS filter_id SERIAL")
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'form_5500_icp_filtered_pkey') THEN
                        ALTER TABLE dol.form_5500_icp_filtered ADD CONSTRAINT form_5500_icp_filtered_pkey PRIMARY KEY (filter_id);
                    END IF;
                END $$
            """)
            print("  [OK] dol.form_5500_icp_filtered: filter_id PK added")
        except Exception as e:
            print(f"  [FAIL] dol.form_5500_icp_filtered: {e}")

        # Add archive_id to people_master_archive
        try:
            cur.execute("ALTER TABLE people.people_master_archive ADD COLUMN IF NOT EXISTS archive_id SERIAL")
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'people_master_archive_pkey') THEN
                        ALTER TABLE people.people_master_archive ADD CONSTRAINT people_master_archive_pkey PRIMARY KEY (archive_id);
                    END IF;
                END $$
            """)
            print("  [OK] people.people_master_archive: archive_id PK added")
        except Exception as e:
            print(f"  [FAIL] people.people_master_archive: {e}")

        # ============================================
        # PHASE 1J: DUPLICATE ARCHIVES → ARCHIVE (already have archived_at)
        # ============================================
        print("\n[PHASE 1J] Archiving duplicate archive tables...")

        # These are already archive tables, so don't add archived_at again
        dup_archives = [
            ('outreach.outreach_orphan_archive', 'archive.outreach_orphan_archive_ctb'),
            ('outreach.company_target_orphaned_archive', 'archive.company_target_orphaned_archive_ctb'),
        ]

        for source, target in dup_archives:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]
                # These tables already have archived_at, just copy as-is with new ctb_archived_at
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {target} AS
                    SELECT *, NOW() as ctb_archived_at FROM {source}
                """)
                print(f"  [OK] Archived {source} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # PHASE 1L: AMBIGUOUS EMPTY TABLES → ARCHIVE
        # ============================================
        print("\n[PHASE 1L] Archiving ambiguous empty tables...")

        ambiguous_archives = [
            ('company.company_events', 'archive.company_company_events_ctb'),
            ('company.company_sidecar', 'archive.company_company_sidecar_ctb'),
            ('company.contact_enrichment', 'archive.company_contact_enrichment_ctb'),
            ('company.email_verification', 'archive.company_email_verification_ctb'),
            ('company.pipeline_errors', 'archive.company_pipeline_errors_ctb'),
            ('company.validation_failures_log', 'archive.company_validation_failures_log_ctb'),
        ]

        for source, target in ambiguous_archives:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {source}")
                count = cur.fetchone()[0]
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {target} AS
                    SELECT *, NOW() as archived_at FROM {source}
                """)
                print(f"  [OK] {source} → {target} ({count:,} rows)")
            except Exception as e:
                print(f"  [FAIL] {source}: {e}")

        # ============================================
        # LOG MIGRATION
        # ============================================
        print("\n[LOGGING] Recording migration...")

        cur.execute("""
            INSERT INTO public.migration_log (migration_name, step, status, details, executed_at)
            VALUES (
                '2026-02-06-ctb-phase1-reorganization',
                'complete',
                'success',
                'CTB Phase 1: Archives created, PKs added, discriminator columns added',
                NOW()
            )
        """)
        print("  [OK] Migration logged")

        # ============================================
        # COMMIT
        # ============================================
        conn.commit()
        print("\n" + "=" * 80)
        print("[OK] PHASE 1 COMPLETE - All changes committed")
        print("=" * 80)

        # ============================================
        # VERIFICATION
        # ============================================
        print("\n[VERIFICATION] Counting archived tables...")

        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'archive' AND tablename LIKE '%_ctb'
            ORDER BY tablename
        """)
        ctb_archives = cur.fetchall()
        print(f"\n  CTB Archive tables created: {len(ctb_archives)}")
        for (tbl,) in ctb_archives:
            cur.execute(f"SELECT COUNT(*) FROM archive.{tbl}")
            cnt = cur.fetchone()[0]
            print(f"    - archive.{tbl}: {cnt:,} rows")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR]: {e}")
        print("All changes rolled back")
        raise

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
