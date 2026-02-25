"""
Tests for Phase 3A — Dispatch Readiness Governor (MID READY Gate)
================================================================
Validates fn_mark_mid_ready gate, mid_ledger FSM whitelist enforcement,
fn_mid_suppression_check stub, error logging, and lcs_worker permissions.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_dispatch_readiness_governor.py -v
"""

import os
import uuid
import json
import pytest
import psycopg2


@pytest.fixture(scope="module")
def conn():
    c = psycopg2.connect(
        host="ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech",
        port=5432,
        dbname="Marketing DB",
        user="Marketing DB_owner",
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )
    c.autocommit = True
    yield c
    c.close()


@pytest.fixture(scope="module")
def cur(conn):
    c = conn.cursor()
    yield c
    c.close()


def _get_test_ids(cur):
    """Get a valid outreach_id/sovereign_id pair for FK satisfaction."""
    cur.execute("""
        SELECT o.outreach_id, o.sovereign_company_id
        FROM outreach.outreach o
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "Need at least one outreach row for FK satisfaction"
    return row[0], row[1]


def _get_movement_type(cur):
    """Get a valid movement_type_code."""
    cur.execute("SELECT movement_type_code FROM lcs.movement_type_registry WHERE is_active = TRUE LIMIT 1")
    row = cur.fetchone()
    assert row is not None, "Need at least one active movement type"
    return row[0]


def _create_test_mid(cur, dispatch_state='MINTED'):
    """Create a test MID chain (CID → SID → MID) and advance to target state."""
    oid, sid_sov = _get_test_ids(cur)
    mtc = _get_movement_type(cur)

    # Create CID
    cur.execute("""
        INSERT INTO lcs.cid_intake (outreach_id, sovereign_id, movement_type_code, source_subhub, detected_at, status)
        VALUES (%s, %s, %s, '04.04.02', NOW(), 'PENDING')
        RETURNING cid
    """, (str(oid), str(sid_sov), mtc))
    cid = cur.fetchone()[0]

    # Create SID
    cur.execute("""
        INSERT INTO lcs.sid_registry (outreach_id, sovereign_id, lifecycle_stage, last_cid, last_movement_at)
        VALUES (%s, %s, 'QUALIFIED', %s, NOW())
        RETURNING sid
    """, (str(oid), str(sid_sov), str(cid)))
    sid = cur.fetchone()[0]

    # Create MID (born MINTED)
    cur.execute("""
        INSERT INTO lcs.mid_ledger (cid, sid, outreach_id, sovereign_id, dispatch_state, movement_type_code)
        VALUES (%s, %s, %s, %s, 'MINTED', %s)
        RETURNING mid
    """, (str(cid), str(sid), str(oid), str(sid_sov), mtc))
    mid = cur.fetchone()[0]

    # Advance through states if needed
    advance_path = ['MINTED', 'COMPILED', 'READY', 'SENT']
    if dispatch_state in advance_path:
        target_idx = advance_path.index(dispatch_state)
        for i in range(1, target_idx + 1):
            cur.execute("""
                UPDATE lcs.mid_ledger SET dispatch_state = %s WHERE mid = %s
            """, (advance_path[i], str(mid)))

    return mid, cid, sid, oid, sid_sov


# ---------------------------------------------------------------------------
# TEST 1: Mid Ledger FSM Enforcement (explicit whitelist)
# ---------------------------------------------------------------------------

class TestDispatchFSM:

    def test_minted_to_compiled_allowed(self, cur):
        """MINTED → COMPILED is an allowed transition."""
        mid, _, _, _, _ = _create_test_mid(cur, 'MINTED')

        cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'COMPILED' WHERE mid = %s", (str(mid),))
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'COMPILED'

    def test_compiled_to_ready_allowed(self, cur):
        """COMPILED → READY is an allowed transition."""
        mid, _, _, _, _ = _create_test_mid(cur, 'COMPILED')

        cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'READY' WHERE mid = %s", (str(mid),))
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'READY'

    def test_ready_to_sent_allowed(self, cur):
        """READY → SENT is an allowed transition."""
        mid, _, _, _, _ = _create_test_mid(cur, 'READY')

        cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'SENT' WHERE mid = %s", (str(mid),))
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'SENT'

    def test_sent_to_terminal_allowed(self, cur):
        """SENT → DELIVERED/FAILED/BOUNCED are allowed terminal transitions."""
        for terminal in ('DELIVERED', 'FAILED', 'BOUNCED'):
            mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

            cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = %s WHERE mid = %s", (terminal, str(mid)))
            cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
            assert cur.fetchone()[0] == terminal

    def test_skip_state_blocked(self, cur):
        """Skipping states (MINTED → READY) is blocked."""
        mid, _, _, _, _ = _create_test_mid(cur, 'MINTED')

        with pytest.raises(psycopg2.errors.RaiseException, match="not allowed"):
            cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'READY' WHERE mid = %s", (str(mid),))

    def test_backward_transition_blocked(self, cur):
        """Backward transition (COMPILED → MINTED) is blocked."""
        mid, _, _, _, _ = _create_test_mid(cur, 'COMPILED')

        with pytest.raises(psycopg2.errors.RaiseException, match="not allowed"):
            cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'MINTED' WHERE mid = %s", (str(mid),))

    def test_terminal_rewind_blocked(self, cur):
        """Terminal state cannot transition further."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')
        cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'DELIVERED' WHERE mid = %s", (str(mid),))

        with pytest.raises(psycopg2.errors.RaiseException, match="terminal"):
            cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'SENT' WHERE mid = %s", (str(mid),))


# ---------------------------------------------------------------------------
# TEST 2: fn_mark_mid_ready — READY gate
# ---------------------------------------------------------------------------

class TestMarkMidReady:

    def test_ready_gate_success(self, cur):
        """fn_mark_mid_ready transitions COMPILED MID to READY when lifecycle permits."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Ensure canonical row exists with dispatch-eligible lifecycle
        cur.execute("""
            SET LOCAL lcs.allow_canonical_write = 'on';
            INSERT INTO lcs.lcs_canonical (sovereign_id, current_lifecycle_stage)
            VALUES (%s, 'QUALIFIED')
            ON CONFLICT (sovereign_id)
            DO UPDATE SET current_lifecycle_stage =
                CASE WHEN lcs.lcs_canonical.current_lifecycle_stage IN ('SUSPECT', 'IDENTIFIED')
                     THEN 'QUALIFIED'
                     ELSE lcs.lcs_canonical.current_lifecycle_stage
                END
        """, (str(sovereign_id),))

        # Call READY gate
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(mid),))

        # Verify state advanced to READY
        cur.execute("SELECT dispatch_state, ready_at FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'READY'
        assert row[1] is not None  # ready_at should be set

    def test_mid_not_found_logs_error(self, cur):
        """fn_mark_mid_ready logs error for non-existent MID and returns cleanly."""
        fake_mid = uuid.uuid4()
        error_count_before = _count_errors(cur, 'mid_minting')

        # Should NOT raise
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(fake_mid),))

        error_count_after = _count_errors(cur, 'mid_minting')
        assert error_count_after == error_count_before + 1

        # Verify error details — mid=NULL for not-found (FK constraint), UUID in payload
        cur.execute("""
            SELECT error_type, error_payload FROM lcs.lcs_errors
            WHERE error_stage = 'mid_minting' AND mid IS NULL
              AND error_payload->>'attempted_mid' = %s
            ORDER BY created_at DESC LIMIT 1
        """, (str(fake_mid),))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'validation'
        payload = row[1] if isinstance(row[1], dict) else json.loads(row[1])
        assert 'not found' in payload['message']

    def test_wrong_state_logs_error(self, cur):
        """fn_mark_mid_ready logs error when MID is not COMPILED."""
        mid, _, _, _, _ = _create_test_mid(cur, 'MINTED')  # Still MINTED, not COMPILED
        error_count_before = _count_errors(cur, 'mid_minting')

        # Should NOT raise
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(mid),))

        error_count_after = _count_errors(cur, 'mid_minting')
        assert error_count_after == error_count_before + 1

        # Verify MID did NOT advance
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'MINTED'

    def test_lifecycle_block_logs_error(self, cur):
        """fn_mark_mid_ready logs error when lifecycle is SUPPRESSED."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Set canonical to SUPPRESSED (highest ordinal, forward-only allows this)
        cur.execute("""
            SET LOCAL lcs.allow_canonical_write = 'on';
            INSERT INTO lcs.lcs_canonical (sovereign_id, current_lifecycle_stage)
            VALUES (%s, 'SUPPRESSED')
            ON CONFLICT (sovereign_id)
            DO UPDATE SET current_lifecycle_stage = 'SUPPRESSED'
        """, (str(sovereign_id),))

        error_count_before = _count_errors(cur, 'mid_minting')

        # Should NOT raise
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(mid),))

        error_count_after = _count_errors(cur, 'mid_minting')
        assert error_count_after == error_count_before + 1

        # Verify MID did NOT advance
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'COMPILED'

    def test_suppression_stub_allows(self, cur):
        """fn_mid_suppression_check stub returns TRUE (allows dispatch)."""
        mid, _, _, _, _ = _create_test_mid(cur, 'MINTED')

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        result = cur.fetchone()[0]
        assert result is True


# ---------------------------------------------------------------------------
# TEST 3: Permissions
# ---------------------------------------------------------------------------

class TestPermissions:

    def test_lcs_worker_has_execute_on_mark_mid_ready(self, cur):
        """lcs_worker has EXECUTE on fn_mark_mid_ready."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_mark_mid_ready(uuid)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_lcs_worker_has_execute_on_suppression_check(self, cur):
        """lcs_worker has EXECUTE on fn_mid_suppression_check."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_mid_suppression_check(uuid)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_errors(cur, stage, mid=None):
    """Count errors from a specific error_stage, optionally filtered by mid."""
    if mid:
        cur.execute("""
            SELECT count(*) FROM lcs.lcs_errors WHERE error_stage = %s AND mid = %s
        """, (stage, str(mid)))
    else:
        cur.execute("""
            SELECT count(*) FROM lcs.lcs_errors WHERE error_stage = %s
        """, (stage,))
    return cur.fetchone()[0]
