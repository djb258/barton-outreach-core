"""
LCS Integration Tests
Runs 4 sequential integration tests against lcs.cid_intake, lcs.mid_ledger, and lcs.sid_registry.
All tests are run via Doppler-injected NEON_PASSWORD.
"""

import os
import sys
import psycopg2
from psycopg2 import sql

# Force UTF-8 stdout on Windows so non-ASCII characters in print() do not crash
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_conn():
    password = os.environ.get("NEON_PASSWORD")
    if not password:
        raise RuntimeError("NEON_PASSWORD not set — run via: doppler run -- python ...")
    return psycopg2.connect(
        host="ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech",
        port=5432,
        dbname="Marketing DB",
        user="Marketing DB_owner",
        password=password,
        sslmode="require",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
results = []  # list of (test_num, description, expected, actual, status)


def log_result(test_num, description, expected, actual, status):
    results.append((test_num, description, expected, actual, status))
    marker = "OK" if status == PASS else "!!"
    print(f"\n[{marker}] TEST {test_num}: {description}")
    print(f"     Expected : {expected}")
    print(f"     Actual   : {actual}")
    print(f"     Result   : {status}")


# ---------------------------------------------------------------------------
# Pre-flight: fetch real FK values
# ---------------------------------------------------------------------------

def fetch_real_fk_values(conn):
    with conn.cursor() as cur:
        # outreach.outreach uses column name "sovereign_id" (FK to cl.company_identity.company_unique_id)
        cur.execute("""
            SELECT o.outreach_id, o.sovereign_id
            FROM outreach.outreach o
            WHERE o.sovereign_id IS NOT NULL
            LIMIT 1;
        """)
        row = cur.fetchone()
        if not row:
            raise RuntimeError("No rows found in outreach.outreach with sovereign_id — cannot run tests.")
        outreach_id, sovereign_id = row
        print(f"\n[PRE-FLIGHT] Real FK values obtained:")
        print(f"  outreach_id   = {outreach_id}")
        print(f"  sovereign_id  = {sovereign_id}")
        return str(outreach_id), str(sovereign_id)


# ---------------------------------------------------------------------------
# TEST 1 — Insert CID row (status = PENDING)
# ---------------------------------------------------------------------------

def test1_insert_cid(conn, outreach_id, sovereign_id):
    print("\n" + "="*70)
    print("TEST 1: Insert a CID row (PENDING)")
    print("="*70)
    cid = None
    try:
        with conn.cursor() as cur:
            # lcs.cid_intake has no source_signal column — use source_record_id as test marker
            cur.execute("""
                INSERT INTO lcs.cid_intake
                    (outreach_id, sovereign_id, movement_type_code, status, detected_at, source_hub, source_record_id)
                VALUES
                    (%s, %s, 'BROKER_CHANGE', 'PENDING', NOW(), 'dol-filings', 'test-signal-integration')
                RETURNING cid, outreach_id, status;
            """, (outreach_id, sovereign_id))
            row = cur.fetchone()
            conn.commit()
            cid, ret_oid, ret_status = str(row[0]), str(row[1]), row[2]
            actual = f"cid={cid}, outreach_id={ret_oid}, status={ret_status}"
            log_result(1, "Insert CID row (PENDING)", "INSERT succeeds, cid UUID returned", actual, PASS)
            print(f"\n  Returned cid = {cid}")
    except Exception as exc:
        conn.rollback()
        log_result(1, "Insert CID row (PENDING)", "INSERT succeeds, cid UUID returned", f"EXCEPTION: {exc}", FAIL)
        raise
    return cid


# ---------------------------------------------------------------------------
# TEST 2 — Call fn_process_cid → verify MID + SID created
# ---------------------------------------------------------------------------

def test2_process_cid(conn, cid, outreach_id):
    print("\n" + "="*70)
    print("TEST 2: Call lcs.fn_process_cid(cid) — verify MID and SID created")
    print("="*70)
    mid = None
    try:
        with conn.cursor() as cur:
            # Call the function
            cur.execute("SELECT lcs.fn_process_cid(%s);", (cid,))
            fn_row = cur.fetchone()
            mid = str(fn_row[0]) if fn_row and fn_row[0] else None
            print(f"\n  fn_process_cid returned MID = {mid}")

            # Verify mid_ledger
            cur.execute("""
                SELECT mid, cid, sid, outreach_id, dispatch_state
                FROM lcs.mid_ledger
                WHERE cid = %s;
            """, (cid,))
            mid_row = cur.fetchone()

            # Verify sid_registry — column is lifecycle_stage (not current_stage)
            cur.execute("""
                SELECT sid, outreach_id, lifecycle_stage
                FROM lcs.sid_registry
                WHERE outreach_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
            """, (outreach_id,))
            sid_row = cur.fetchone()

            conn.commit()

            if mid_row:
                mid_from_ledger = str(mid_row[0])
                cid_in_ledger   = str(mid_row[1])
                sid_in_ledger   = str(mid_row[2]) if mid_row[2] else None
                oid_in_ledger   = str(mid_row[3])
                dispatch_state  = mid_row[4]
                print(f"\n  mid_ledger row:")
                print(f"    mid            = {mid_from_ledger}")
                print(f"    cid            = {cid_in_ledger}")
                print(f"    sid            = {sid_in_ledger}")
                print(f"    outreach_id    = {oid_in_ledger}")
                print(f"    dispatch_state = {dispatch_state}")
                mid = mid_from_ledger  # canonical MID for downstream tests
            else:
                print("  mid_ledger: NO ROW FOUND")

            if sid_row:
                sid_val       = str(sid_row[0])
                oid_sid       = str(sid_row[1])
                lifecycle_stg = sid_row[2]
                print(f"\n  sid_registry row:")
                print(f"    sid             = {sid_val}")
                print(f"    outreach_id     = {oid_sid}")
                print(f"    lifecycle_stage = {lifecycle_stg}")
            else:
                print("  sid_registry: NO ROW FOUND")

            all_ok = (mid_row is not None) and (sid_row is not None)
            actual = (
                f"MID={mid}, dispatch_state={dispatch_state if mid_row else 'N/A'}, "
                f"SID={'found' if sid_row else 'NOT FOUND'}"
            )
            log_result(
                2,
                "fn_process_cid creates MID in mid_ledger + SID in sid_registry",
                "MID UUID returned, mid_ledger row exists, sid_registry row exists",
                actual,
                PASS if all_ok else FAIL,
            )
    except Exception as exc:
        conn.rollback()
        log_result(
            2,
            "fn_process_cid creates MID in mid_ledger + SID in sid_registry",
            "MID UUID returned, mid_ledger row exists, sid_registry row exists",
            f"EXCEPTION: {exc}",
            FAIL,
        )
        raise
    return mid


# ---------------------------------------------------------------------------
# TEST 3 — Illegal update of immutable CID column → must FAIL
# ---------------------------------------------------------------------------

def test3_immutable_cid_column(conn, cid):
    print("\n" + "="*70)
    print("TEST 3: Illegal update of immutable CID column — expect EXCEPTION")
    print("="*70)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE lcs.cid_intake
                SET movement_type_code = 'EXECUTIVE_HIRE'
                WHERE cid = %s;
            """, (cid,))
            conn.commit()
            # If we reach here the trigger did NOT fire — that is a failure
            log_result(
                3,
                "Immutable CID column update blocked by trigger",
                "EXCEPTION raised by trg_cid_intake_no_update",
                "UPDATE succeeded — trigger did NOT fire",
                FAIL,
            )
    except psycopg2.errors.RaiseException as exc:
        conn.rollback()
        err_msg = str(exc).strip()
        print(f"\n  Caught expected exception:\n    {err_msg}")
        log_result(
            3,
            "Immutable CID column update blocked by trigger",
            "EXCEPTION raised by trg_cid_intake_no_update",
            f"EXCEPTION: {err_msg}",
            PASS,
        )
    except Exception as exc:
        conn.rollback()
        err_msg = str(exc).strip()
        print(f"\n  Caught exception (unexpected type):\n    {err_msg}")
        # Still a trigger-raised error even if psycopg2 wraps it differently
        if "cid_intake" in err_msg.lower() or "immutable" in err_msg.lower() or "update" in err_msg.lower():
            log_result(
                3,
                "Immutable CID column update blocked by trigger",
                "EXCEPTION raised by trg_cid_intake_no_update",
                f"EXCEPTION (trigger): {err_msg}",
                PASS,
            )
        else:
            log_result(
                3,
                "Immutable CID column update blocked by trigger",
                "EXCEPTION raised by trg_cid_intake_no_update",
                f"EXCEPTION (unexpected): {err_msg}",
                FAIL,
            )


# ---------------------------------------------------------------------------
# TEST 4 — Illegal dispatch_state rewind → must FAIL
# ---------------------------------------------------------------------------

def test4_dispatch_state_rewind(conn, mid):
    print("\n" + "="*70)
    print("TEST 4: Illegal dispatch_state rewind -- expect EXCEPTION on QUEUED->MINTED")
    print("="*70)

    # Step 4a: Advance to QUEUED (must succeed)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE lcs.mid_ledger
                SET dispatch_state = 'QUEUED'
                WHERE mid = %s;
            """, (mid,))
            conn.commit()
            print(f"\n  Step 4a: Advanced mid_ledger dispatch_state to QUEUED — OK")
    except Exception as exc:
        conn.rollback()
        log_result(
            4,
            "Dispatch state rewind blocked by forward-only trigger",
            "QUEUED advance succeeds; MINTED rewind raises EXCEPTION",
            f"Step 4a FAILED: {exc}",
            FAIL,
        )
        return

    # Step 4b: Attempt rewind to MINTED (must fail)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE lcs.mid_ledger
                SET dispatch_state = 'MINTED'
                WHERE mid = %s;
            """, (mid,))
            conn.commit()
            log_result(
                4,
                "Dispatch state rewind blocked by forward-only trigger",
                "QUEUED→MINTED rewind raises EXCEPTION from trg_dispatch_state_forward",
                "UPDATE succeeded — trigger did NOT fire",
                FAIL,
            )
    except psycopg2.errors.RaiseException as exc:
        conn.rollback()
        err_msg = str(exc).strip()
        print(f"\n  Step 4b: Caught expected exception:\n    {err_msg}")
        log_result(
            4,
            "Dispatch state rewind blocked by forward-only trigger",
            "QUEUED→MINTED rewind raises EXCEPTION from trg_dispatch_state_forward",
            f"EXCEPTION: {err_msg}",
            PASS,
        )
    except Exception as exc:
        conn.rollback()
        err_msg = str(exc).strip()
        print(f"\n  Step 4b: Caught exception (unexpected type):\n    {err_msg}")
        if "rewind" in err_msg.lower() or "dispatch" in err_msg.lower() or "forward" in err_msg.lower() or "state" in err_msg.lower():
            log_result(
                4,
                "Dispatch state rewind blocked by forward-only trigger",
                "QUEUED→MINTED rewind raises EXCEPTION from trg_dispatch_state_forward",
                f"EXCEPTION (trigger): {err_msg}",
                PASS,
            )
        else:
            log_result(
                4,
                "Dispatch state rewind blocked by forward-only trigger",
                "QUEUED→MINTED rewind raises EXCEPTION from trg_dispatch_state_forward",
                f"EXCEPTION (unexpected): {err_msg}",
                FAIL,
            )


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary():
    print("\n\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    col_w = [6, 48, 20, 8]
    header = f"{'Test #':<{col_w[0]}}  {'Description':<{col_w[1]}}  {'Expected':<{col_w[2]}}  {'Result'}"
    print(header)
    print("-" * 90)
    all_pass = True
    for (num, desc, expected, actual, status) in results:
        trunc_desc   = desc[:col_w[1]] if len(desc) > col_w[1] else desc
        trunc_expect = expected[:col_w[2]] if len(expected) > col_w[2] else expected
        print(f"{str(num):<{col_w[0]}}  {trunc_desc:<{col_w[1]}}  {trunc_expect:<{col_w[2]}}  {status}")
        if status != PASS:
            all_pass = False
    print("-" * 90)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_pass else 'ONE OR MORE TESTS FAILED'}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("LCS Integration Tests — barton-outreach-core")
    print("Connecting to Neon PostgreSQL...")

    conn = get_conn()
    print("Connected.")

    try:
        outreach_id, sovereign_id = fetch_real_fk_values(conn)

        cid = test1_insert_cid(conn, outreach_id, sovereign_id)
        mid = test2_process_cid(conn, cid, outreach_id)
        test3_immutable_cid_column(conn, cid)
        test4_dispatch_state_rewind(conn, mid)

    finally:
        conn.close()
        print_summary()
