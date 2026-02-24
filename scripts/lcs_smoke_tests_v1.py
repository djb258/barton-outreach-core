"""
LCS Spine v1 CTB Refactor — Operator Smoke Tests (v1)
======================================================
Runs 3 smoke tests against Neon PostgreSQL via psycopg2 + Doppler.

Each test that modifies data runs in its own transaction with explicit
commit/rollback so that error-path tests do not roll back prior work.
"""

import os
import sys
import json
import uuid
import psycopg2
import psycopg2.extras
from datetime import datetime

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def get_conn():
    return psycopg2.connect(
        host="ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech",
        port=5432,
        dbname="Marketing DB",
        user="Marketing DB_owner",
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PASS = "PASS"
FAIL = "FAIL"

results = []   # list of (test_id, description, expected, actual, verdict)

def record(test_id, description, expected, actual, verdict):
    results.append((test_id, description, expected, actual, verdict))
    tag = f"[{verdict}]"
    print(f"  {tag:8s} {test_id}: {description}")
    print(f"           expected: {expected}")
    print(f"           actual:   {actual}")
    print()

def q(conn, sql, params=None):
    """Execute a query and return all rows."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            return []

def q1(conn, sql, params=None):
    """Execute a query and return the first row (or None)."""
    rows = q(conn, sql, params)
    return rows[0] if rows else None

# ---------------------------------------------------------------------------
# STEP 0: Obtain a fresh FK pair not already in lcs.sid_registry
# ---------------------------------------------------------------------------
def get_fresh_fk_pair(conn):
    row = q1(conn, """
        SELECT o.outreach_id, ci.company_unique_id AS sovereign_id
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_company_id = ci.company_unique_id
        WHERE o.outreach_id NOT IN (SELECT outreach_id FROM lcs.sid_registry)
        LIMIT 1;
    """)
    if not row:
        raise RuntimeError("No fresh FK pair available — all outreach_ids already in sid_registry?")
    return str(row["outreach_id"]), str(row["sovereign_id"])

# ---------------------------------------------------------------------------
# SMOKE TEST 1: Full CID→MID flow with canonical verification
# ---------------------------------------------------------------------------
def smoke_test_1(conn, outreach_id, sovereign_id):
    print("=" * 70)
    print("SMOKE TEST 1: Full CID → MID flow with canonical verification")
    print(f"  outreach_id : {outreach_id}")
    print(f"  sovereign_id: {sovereign_id}")
    print("=" * 70)
    print()

    # ---- Step 1a: Insert PENDING CID ----------------------------------------
    print("Step 1a — Insert PENDING CID")
    cid = None
    try:
        row = q1(conn, """
            INSERT INTO lcs.cid_intake
                (outreach_id, sovereign_id, movement_type_code, status,
                 detected_at, source_hub, source_record_id)
            VALUES (%s, %s, 'RENEWAL_APPROACHING', 'PENDING', NOW(),
                    'dol-filings', 'v1-smoke-test')
            RETURNING cid, status;
        """, (outreach_id, sovereign_id))
        conn.commit()
        if row:
            cid = str(row["cid"])
            status = row["status"]
            record("1a", "Insert PENDING CID", "row returned with status=PENDING",
                   f"cid={cid} status={status}",
                   PASS if status == "PENDING" else FAIL)
        else:
            conn.rollback()
            record("1a", "Insert PENDING CID", "row returned", "no row returned", FAIL)
            return None, None, None
    except Exception as e:
        conn.rollback()
        record("1a", "Insert PENDING CID", "success", f"ERROR: {e}", FAIL)
        return None, None, None

    # ---- Step 1b: Process the CID -------------------------------------------
    print("Step 1b — Process CID via fn_process_cid")
    try:
        row = q1(conn, "SELECT lcs.fn_process_cid(%s) AS result;", (cid,))
        conn.commit()
        result_val = row["result"] if row else None
        record("1b", "fn_process_cid returns MID", "non-NULL MID UUID",
               str(result_val),
               PASS if result_val is not None else FAIL)
    except Exception as e:
        conn.rollback()
        record("1b", "fn_process_cid", "success", f"ERROR: {e}", FAIL)
        return cid, None, None

    # ---- Step 1c: Verify MID exists -----------------------------------------
    print("Step 1c — Verify MID in lcs.mid_ledger")
    mid = None
    sid = None
    try:
        row = q1(conn, """
            SELECT mid, cid, sid, outreach_id, dispatch_state
            FROM lcs.mid_ledger WHERE cid = %s;
        """, (cid,))
        if row:
            mid = str(row["mid"])
            sid = str(row["sid"])
            dispatch_state = row["dispatch_state"]
            record("1c", "MID row exists in mid_ledger",
                   "mid + cid + sid + outreach_id + dispatch_state=MINTED",
                   f"mid={mid} sid={sid} dispatch_state={dispatch_state}",
                   PASS if dispatch_state == "MINTED" else FAIL)
        else:
            record("1c", "MID row exists in mid_ledger", "row found", "no row", FAIL)
            return cid, None, None
    except Exception as e:
        record("1c", "MID row exists in mid_ledger", "success", f"ERROR: {e}", FAIL)
        return cid, None, None

    # ---- Step 1d: Verify SID exists -----------------------------------------
    print("Step 1d — Verify SID in lcs.sid_registry")
    try:
        row = q1(conn, """
            SELECT sid, outreach_id, sovereign_id, lifecycle_stage
            FROM lcs.sid_registry WHERE outreach_id = %s;
        """, (outreach_id,))
        if row:
            sid_reg = str(row["sid"])
            lc_stage = row["lifecycle_stage"]
            sid_match = sid_reg == sid
            record("1d", "SID row exists in sid_registry",
                   f"sid matches mid_ledger.sid + lifecycle_stage=ENGAGED",
                   f"sid={sid_reg} lifecycle_stage={lc_stage} sid_match={sid_match}",
                   PASS if sid_match and lc_stage == "ENGAGED" else FAIL)
        else:
            record("1d", "SID row exists in sid_registry", "row found", "no row", FAIL)
    except Exception as e:
        record("1d", "SID row exists in sid_registry", "success", f"ERROR: {e}", FAIL)

    # ---- Step 1e: Verify canonical row --------------------------------------
    print("Step 1e — Verify lcs.lcs_canonical reflects current state")
    try:
        row = q1(conn, """
            SELECT sovereign_id, current_lifecycle_stage, current_sid,
                   current_mid, current_dispatch_state, last_cid
            FROM lcs.lcs_canonical WHERE sovereign_id = %s;
        """, (sovereign_id,))
        if row:
            c_mid = str(row["current_mid"]) if row["current_mid"] else None
            c_sid = str(row["current_sid"]) if row["current_sid"] else None
            c_lc  = row["current_lifecycle_stage"]
            c_ds  = row["current_dispatch_state"]
            c_cid = str(row["last_cid"]) if row["last_cid"] else None

            checks = {
                "current_mid == mid from 1c":       c_mid == mid,
                "current_sid == sid from 1d":       c_sid == sid,
                "last_cid == cid from 1a":          c_cid == cid,
                "current_dispatch_state == MINTED": c_ds  == "MINTED",
                "current_lifecycle_stage == ENGAGED": c_lc == "ENGAGED",
            }
            all_pass = all(checks.values())
            detail = " | ".join(f"{k}={v}" for k, v in checks.items())
            record("1e", "lcs_canonical reflects current state",
                   "all 5 canonical checks pass",
                   detail,
                   PASS if all_pass else FAIL)
        else:
            record("1e", "lcs_canonical reflects current state", "row found", "no row", FAIL)
    except Exception as e:
        record("1e", "lcs_canonical reflects current state", "success", f"ERROR: {e}", FAIL)

    print()
    return cid, mid, sid

# ---------------------------------------------------------------------------
# SMOKE TEST 2: Error path — force errors and verify lcs.lcs_errors rows
# ---------------------------------------------------------------------------
def smoke_test_2(conn, cid_from_test1, mid_from_test1):
    print("=" * 70)
    print("SMOKE TEST 2: Error path — force errors and verify lcs.lcs_errors")
    print(f"  cid_from_test1: {cid_from_test1}")
    print(f"  mid_from_test1: {mid_from_test1}")
    print("=" * 70)
    print()

    # Baseline error count
    baseline_row = q1(conn, "SELECT count(*) AS cnt FROM lcs.lcs_errors;")
    baseline = int(baseline_row["cnt"]) if baseline_row else 0
    print(f"  Baseline lcs.lcs_errors count: {baseline}\n")

    fake_cid = "00000000-0000-0000-0000-000000000000"

    # ---- Step 2a: Non-existent CID ------------------------------------------
    print("Step 2a — fn_process_cid with non-existent CID (should return NULL)")
    try:
        row = q1(conn, "SELECT lcs.fn_process_cid(%s) AS result;", (fake_cid,))
        conn.commit()
        result_val = row["result"] if row else None
        returned_null = result_val is None
        record("2a-call", "fn_process_cid(fake CID) returns NULL",
               "NULL", str(result_val), PASS if returned_null else FAIL)
    except Exception as e:
        conn.rollback()
        record("2a-call", "fn_process_cid(fake CID)", "NULL (no raise)", f"RAISED: {e}", FAIL)

    # Verify error row written
    err_row = q1(conn, """
        SELECT error_stage, error_type, error_payload
        FROM lcs.lcs_errors
        WHERE error_payload->>'cid' = %s
        ORDER BY created_at DESC LIMIT 1;
    """, (fake_cid,))
    if err_row:
        record("2a-error", "Error row written for fake CID",
               "error row exists",
               f"error_stage={err_row['error_stage']} error_type={err_row['error_type']}",
               PASS)
    else:
        record("2a-error", "Error row written for fake CID", "error row exists", "no row found", FAIL)

    # ---- Step 2b: Already-processed CID (ACCEPTED state) --------------------
    print("Step 2b — fn_process_cid on already-ACCEPTED CID (state_violation)")
    try:
        row = q1(conn, "SELECT lcs.fn_process_cid(%s) AS result;", (cid_from_test1,))
        conn.commit()
        result_val = row["result"] if row else None
        record("2b-call", "fn_process_cid(accepted CID) returns NULL",
               "NULL", str(result_val), PASS if result_val is None else FAIL)
    except Exception as e:
        conn.rollback()
        record("2b-call", "fn_process_cid(accepted CID)", "NULL (no raise)", f"RAISED: {e}", FAIL)

    err_row = q1(conn, """
        SELECT error_stage, error_type, error_payload
        FROM lcs.lcs_errors
        WHERE cid = %s AND error_type = 'state_violation'
        ORDER BY created_at DESC LIMIT 1;
    """, (cid_from_test1,))
    if err_row:
        record("2b-error", "state_violation error row written for accepted CID",
               "error_type=state_violation",
               f"error_stage={err_row['error_stage']} error_type={err_row['error_type']}",
               PASS)
    else:
        record("2b-error", "state_violation error row written for accepted CID",
               "error row with error_type=state_violation", "no row found", FAIL)

    # ---- Step 2c: fn_finalize_dispatch — missing outcome key ----------------
    print("Step 2c — fn_finalize_dispatch with missing 'outcome' key")
    try:
        row = q1(conn, "SELECT lcs.fn_finalize_dispatch(%s, %s::jsonb) AS result;",
                 (mid_from_test1, '{"foo": "bar"}'))
        conn.commit()
        result_val = row["result"] if row else None
        record("2c-call", "fn_finalize_dispatch(missing outcome key) returns NULL/false",
               "NULL or false", str(result_val),
               PASS if not result_val else FAIL)
    except Exception as e:
        conn.rollback()
        record("2c-call", "fn_finalize_dispatch(missing outcome key)",
               "NULL (no raise)", f"RAISED: {e}", FAIL)

    err_row = q1(conn, """
        SELECT error_stage, error_type, error_payload
        FROM lcs.lcs_errors
        WHERE mid = %s AND error_payload->>'reason' = 'missing outcome key'
        ORDER BY created_at DESC LIMIT 1;
    """, (mid_from_test1,))
    if err_row:
        record("2c-error", "Error row for missing outcome key",
               "error row with reason='missing outcome key'",
               f"error_stage={err_row['error_stage']} error_type={err_row['error_type']}",
               PASS)
    else:
        record("2c-error", "Error row for missing outcome key",
               "error row exists", "no row found", FAIL)

    # ---- Step 2d: fn_finalize_dispatch — invalid outcome value --------------
    print("Step 2d — fn_finalize_dispatch with invalid outcome value 'EXPLODED'")
    try:
        row = q1(conn, "SELECT lcs.fn_finalize_dispatch(%s, %s::jsonb) AS result;",
                 (mid_from_test1, '{"outcome": "EXPLODED"}'))
        conn.commit()
        result_val = row["result"] if row else None
        record("2d-call", "fn_finalize_dispatch('EXPLODED') returns NULL/false",
               "NULL or false", str(result_val),
               PASS if not result_val else FAIL)
    except Exception as e:
        conn.rollback()
        record("2d-call", "fn_finalize_dispatch('EXPLODED')",
               "NULL (no raise)", f"RAISED: {e}", FAIL)

    err_row = q1(conn, """
        SELECT error_stage, error_type, error_payload
        FROM lcs.lcs_errors
        WHERE mid = %s AND error_payload->>'reason' ILIKE 'invalid outcome%'
        ORDER BY created_at DESC LIMIT 1;
    """, (mid_from_test1,))
    if err_row:
        record("2d-error", "Error row for invalid outcome value",
               "error row with reason LIKE 'invalid outcome%'",
               f"error_stage={err_row['error_stage']} error_type={err_row['error_type']} reason={err_row['error_payload'].get('reason', '')}",
               PASS)
    else:
        record("2d-error", "Error row for invalid outcome value",
               "error row exists", "no row found", FAIL)

    # ---- Final count check ---------------------------------------------------
    final_row = q1(conn, "SELECT count(*) AS cnt FROM lcs.lcs_errors;")
    final = int(final_row["cnt"]) if final_row else 0
    delta = final - baseline
    record("2-total", "Total lcs_errors delta",
           f"baseline+4 = {baseline + 4}",
           f"final={final} delta={delta}",
           PASS if delta == 4 else FAIL)

    print()

# ---------------------------------------------------------------------------
# SMOKE TEST 3: Append-only / immutability constraints
# ---------------------------------------------------------------------------
def smoke_test_3(conn, sovereign_id_for_test1, cid_from_test1):
    print("=" * 70)
    print("SMOKE TEST 3: Append-only constraints still enforced")
    print("=" * 70)
    print()

    # Get a sovereign_id NOT in lcs_canonical for step 3a
    fresh_sov = q1(conn, """
        SELECT ci.company_unique_id AS sovereign_id
        FROM cl.company_identity ci
        WHERE ci.company_unique_id NOT IN (SELECT sovereign_id FROM lcs.lcs_canonical)
        LIMIT 1;
    """)
    fresh_sovereign_id = str(fresh_sov["sovereign_id"]) if fresh_sov else str(uuid.uuid4())
    print(f"  fresh sovereign_id for 3a: {fresh_sovereign_id}")
    print()

    # ---- Step 3a: Direct INSERT into lcs_canonical (guard should block) -----
    print("Step 3a — Direct INSERT into lcs_canonical (trg_lcs_canonical_guard)")
    try:
        conn.autocommit = False
        q(conn, """
            INSERT INTO lcs.lcs_canonical (sovereign_id, current_lifecycle_stage)
            VALUES (%s, 'SUSPECT');
        """, (fresh_sovereign_id,))
        conn.commit()
        record("3a", "Direct INSERT into lcs_canonical raises exception",
               "RAISE from trg_lcs_canonical_guard", "NO exception — INSERT succeeded", FAIL)
    except Exception as e:
        conn.rollback()
        record("3a", "Direct INSERT into lcs_canonical raises exception",
               "RAISE from trg_lcs_canonical_guard",
               f"RAISED: {e}", PASS)

    # ---- Step 3b: UPDATE immutable column on cid_intake ---------------------
    print("Step 3b — UPDATE movement_type_code on ACCEPTED cid_intake row (trg_cid_intake_no_update)")
    try:
        conn.autocommit = False
        q(conn, """
            UPDATE lcs.cid_intake
            SET movement_type_code = 'EXECUTIVE_HIRE'
            WHERE cid = %s;
        """, (cid_from_test1,))
        conn.commit()
        record("3b", "UPDATE immutable cid_intake column raises exception",
               "RAISE from trg_cid_intake_no_update", "NO exception — UPDATE succeeded", FAIL)
    except Exception as e:
        conn.rollback()
        record("3b", "UPDATE immutable cid_intake column raises exception",
               "RAISE from trg_cid_intake_no_update",
               f"RAISED: {e}", PASS)

    # ---- Step 3c: DELETE from lcs_errors ------------------------------------
    print("Step 3c — DELETE from lcs_errors (trg_lcs_errors_no_delete)")
    try:
        conn.autocommit = False
        q(conn, """
            DELETE FROM lcs.lcs_errors
            WHERE error_id = (SELECT error_id FROM lcs.lcs_errors LIMIT 1);
        """)
        conn.commit()
        record("3c", "DELETE from lcs_errors raises exception",
               "RAISE from trg_lcs_errors_no_delete", "NO exception — DELETE succeeded", FAIL)
    except Exception as e:
        conn.rollback()
        record("3c", "DELETE from lcs_errors raises exception",
               "RAISE from trg_lcs_errors_no_delete",
               f"RAISED: {e}", PASS)

    # ---- Step 3d: UPDATE immutable column on lcs_errors ---------------------
    print("Step 3d — UPDATE error_type on lcs_errors (trg_lcs_errors_guard)")
    try:
        conn.autocommit = False
        q(conn, """
            UPDATE lcs.lcs_errors
            SET error_type = 'conflict'
            WHERE error_id = (SELECT error_id FROM lcs.lcs_errors LIMIT 1);
        """)
        conn.commit()
        record("3d", "UPDATE immutable lcs_errors column raises exception",
               "RAISE from trg_lcs_errors_guard", "NO exception — UPDATE succeeded", FAIL)
    except Exception as e:
        conn.rollback()
        record("3d", "UPDATE immutable lcs_errors column raises exception",
               "RAISE from trg_lcs_errors_guard",
               f"RAISED: {e}", PASS)

    # ---- Step 3e: resolved_at CAN be updated (allowed mutation) --------------
    print("Step 3e — UPDATE resolved_at on lcs_errors (the one allowed mutation)")

    # Get a real error_id
    err_row = q1(conn, "SELECT error_id FROM lcs.lcs_errors LIMIT 1;")
    if not err_row:
        record("3e-set", "UPDATE resolved_at on lcs_errors", "success", "no lcs_errors rows to test with", FAIL)
        record("3e-reset", "RESET resolved_at to NULL", "success", "no lcs_errors rows to test with", FAIL)
        return

    error_id = err_row["error_id"]

    try:
        conn.autocommit = False
        q(conn, "UPDATE lcs.lcs_errors SET resolved_at = NOW() WHERE error_id = %s;", (error_id,))
        conn.commit()
        record("3e-set", "UPDATE resolved_at (allowed) succeeds",
               "success", f"resolved_at set on error_id={error_id}", PASS)
    except Exception as e:
        conn.rollback()
        record("3e-set", "UPDATE resolved_at (allowed) succeeds",
               "success", f"RAISED: {e}", FAIL)

    try:
        conn.autocommit = False
        q(conn, "UPDATE lcs.lcs_errors SET resolved_at = NULL WHERE error_id = %s;", (error_id,))
        conn.commit()
        record("3e-reset", "RESET resolved_at to NULL succeeds",
               "success", f"resolved_at reset on error_id={error_id}", PASS)
    except Exception as e:
        conn.rollback()
        record("3e-reset", "RESET resolved_at to NULL succeeds",
               "success", f"RAISED: {e}", FAIL)

    print()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print()
    print("=" * 70)
    print("LCS Spine v1 CTB Refactor — Operator Smoke Tests")
    print(f"Run time: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)
    print()

    conn = get_conn()
    conn.autocommit = False

    # Step 0: fresh FK pair
    print("Step 0 — Fetching fresh FK pair not in lcs.sid_registry...")
    outreach_id, sovereign_id = get_fresh_fk_pair(conn)
    print(f"  outreach_id : {outreach_id}")
    print(f"  sovereign_id: {sovereign_id}")
    print()

    # Test 1
    cid, mid, sid = smoke_test_1(conn, outreach_id, sovereign_id)

    if cid is None or mid is None:
        print("FATAL: Test 1 did not produce a CID/MID — cannot continue Tests 2 & 3.")
        sys.exit(1)

    # Test 2
    smoke_test_2(conn, cid, mid)

    # Test 3
    smoke_test_3(conn, sovereign_id, cid)

    # Final summary table
    conn.close()

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    hdr = f"{'Test':<12} {'Description':<55} {'Expected':<35} {'Actual':<60} {'Result'}"
    print(hdr)
    print("-" * len(hdr))
    passes = 0
    fails  = 0
    for (tid, desc, exp, act, verdict) in results:
        mark = "PASS" if verdict == PASS else "FAIL"
        if verdict == PASS:
            passes += 1
        else:
            fails += 1
        print(f"{tid:<12} {desc:<55} {str(exp):<35} {str(act):<60} {mark}")

    print()
    print(f"Total: {passes + fails} sub-steps | {passes} PASS | {fails} FAIL")
    if fails == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILURES DETECTED: {fails}")
    print()

if __name__ == "__main__":
    main()
