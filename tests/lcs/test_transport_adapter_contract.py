"""
Tests for Phase 3C — Transport Adapter Contract (External Boundary Lock)
========================================================================
Validates fn_record_dispatch_result entry point, dispatch_event_log
append-only table, FSM enforcement, error logging, and lcs_transport
least-privilege permissions.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_transport_adapter_contract.py -v
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
    """Get a valid outreach_id/sovereign_id pair."""
    cur.execute("""
        SELECT o.outreach_id, o.sovereign_company_id
        FROM outreach.outreach o LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None
    return row[0], row[1]


def _get_movement_type(cur):
    """Get a valid movement_type_code."""
    cur.execute("SELECT movement_type_code FROM lcs.movement_type_registry WHERE is_active = TRUE LIMIT 1")
    return cur.fetchone()[0]


def _create_test_mid(cur, dispatch_state='MINTED'):
    """Create a test MID chain and advance to target state."""
    oid, sovereign_id = _get_test_ids(cur)
    mtc = _get_movement_type(cur)

    cur.execute("""
        INSERT INTO lcs.cid_intake (outreach_id, sovereign_id, movement_type_code, source_subhub, status)
        VALUES (%s, %s, %s, '04.04.02', 'PENDING')
        RETURNING cid
    """, (str(oid), str(sovereign_id), mtc))
    cid = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO lcs.sid_registry (outreach_id, sovereign_id, lifecycle_stage, last_cid, last_movement_at)
        VALUES (%s, %s, 'QUALIFIED', %s, NOW())
        RETURNING sid
    """, (str(oid), str(sovereign_id), str(cid)))
    sid = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO lcs.mid_ledger (cid, sid, outreach_id, sovereign_id, dispatch_state, movement_type_code)
        VALUES (%s, %s, %s, %s, 'MINTED', %s)
        RETURNING mid
    """, (str(cid), str(sid), str(oid), str(sovereign_id), mtc))
    mid = cur.fetchone()[0]

    advance_path = ['MINTED', 'COMPILED', 'READY', 'SENT']
    if dispatch_state in advance_path:
        target_idx = advance_path.index(dispatch_state)
        for i in range(1, target_idx + 1):
            cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = %s WHERE mid = %s",
                        (advance_path[i], str(mid)))

    return mid, cid, sid, oid, sovereign_id


def _count_errors(cur, stage):
    cur.execute("SELECT count(*) FROM lcs.lcs_errors WHERE error_stage = %s", (stage,))
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# TEST 1: dispatch_event_log table structure
# ---------------------------------------------------------------------------

class TestDispatchEventLog:

    def test_table_exists(self, cur):
        """dispatch_event_log table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'dispatch_event_log'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """dispatch_event_log is registered in CTB as SUPPORTING."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'dispatch_event_log'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'SUPPORTING'

    def test_update_blocked(self, cur):
        """UPDATE on dispatch_event_log is blocked (append-only)."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        # Insert a test event
        cur.execute("""
            INSERT INTO lcs.dispatch_event_log (mid, provider, result_state)
            VALUES (%s, 'test_provider', 'DELIVERED')
            RETURNING event_id
        """, (str(mid),))
        event_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match="append-only"):
            cur.execute("""
                UPDATE lcs.dispatch_event_log SET provider = 'changed' WHERE event_id = %s
            """, (str(event_id),))

    def test_delete_blocked(self, cur):
        """DELETE on dispatch_event_log is blocked."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        cur.execute("""
            INSERT INTO lcs.dispatch_event_log (mid, provider, result_state)
            VALUES (%s, 'test_provider', 'FAILED')
            RETURNING event_id
        """, (str(mid),))
        event_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match="cannot be deleted"):
            cur.execute("DELETE FROM lcs.dispatch_event_log WHERE event_id = %s", (str(event_id),))


# ---------------------------------------------------------------------------
# TEST 2: fn_record_dispatch_result — behavior
# ---------------------------------------------------------------------------

class TestRecordDispatchResult:

    def test_delivered_updates_mid_ledger(self, cur):
        """DELIVERED result updates mid_ledger state, provider, timestamps."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'mailgun', 'msg-001', 'DELIVERED', '{"status": "ok"}'::jsonb)
        """, (str(mid),))

        cur.execute("""
            SELECT dispatch_state, provider, external_message_id, delivered_at, failed_at, bounced_at, finalized_at
            FROM lcs.mid_ledger WHERE mid = %s
        """, (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'DELIVERED'
        assert row[1] == 'mailgun'
        assert row[2] == 'msg-001'
        assert row[3] is not None   # delivered_at set
        assert row[4] is None       # failed_at null
        assert row[5] is None       # bounced_at null
        assert row[6] is not None   # finalized_at set

    def test_failed_updates_mid_ledger(self, cur):
        """FAILED result sets failed_at timestamp."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'ses', 'msg-002', 'FAILED', NULL)
        """, (str(mid),))

        cur.execute("""
            SELECT dispatch_state, provider, failed_at, delivered_at
            FROM lcs.mid_ledger WHERE mid = %s
        """, (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'FAILED'
        assert row[1] == 'ses'
        assert row[2] is not None   # failed_at set
        assert row[3] is None       # delivered_at null

    def test_bounced_updates_mid_ledger(self, cur):
        """BOUNCED result sets bounced_at timestamp."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'mailgun', 'msg-003', 'BOUNCED', NULL)
        """, (str(mid),))

        cur.execute("""
            SELECT dispatch_state, bounced_at FROM lcs.mid_ledger WHERE mid = %s
        """, (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'BOUNCED'
        assert row[1] is not None   # bounced_at set

    def test_inserts_event_log_row(self, cur):
        """fn_record_dispatch_result inserts a dispatch_event_log row."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'ses', 'msg-004', 'DELIVERED', '{"detail": "test"}'::jsonb)
        """, (str(mid),))

        cur.execute("""
            SELECT provider, external_message_id, result_state, metadata
            FROM lcs.dispatch_event_log WHERE mid = %s
            ORDER BY recorded_at DESC LIMIT 1
        """, (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'ses'
        assert row[1] == 'msg-004'
        assert row[2] == 'DELIVERED'
        assert row[3] is not None

    def test_rejects_non_sent_state(self, cur):
        """fn_record_dispatch_result logs error when MID is not SENT."""
        mid, _, _, _, _ = _create_test_mid(cur, 'COMPILED')  # Not SENT
        error_count_before = _count_errors(cur, 'dispatch_finalization')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'mailgun', 'msg-005', 'DELIVERED', NULL)
        """, (str(mid),))

        error_count_after = _count_errors(cur, 'dispatch_finalization')
        assert error_count_after == error_count_before + 1

        # MID should stay COMPILED
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'COMPILED'

    def test_rejects_invalid_result_state(self, cur):
        """fn_record_dispatch_result logs error for invalid result_state."""
        mid, _, _, _, _ = _create_test_mid(cur, 'SENT')
        error_count_before = _count_errors(cur, 'dispatch_finalization')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'mailgun', 'msg-006', 'INVALID', NULL)
        """, (str(mid),))

        error_count_after = _count_errors(cur, 'dispatch_finalization')
        assert error_count_after == error_count_before + 1

        # MID should stay SENT
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'SENT'

    def test_mid_not_found_logs_error(self, cur):
        """fn_record_dispatch_result logs error for non-existent MID."""
        fake_mid = uuid.uuid4()
        error_count_before = _count_errors(cur, 'dispatch_finalization')

        cur.execute("""
            SELECT lcs.fn_record_dispatch_result(%s, 'mailgun', 'msg-007', 'DELIVERED', NULL)
        """, (str(fake_mid),))

        error_count_after = _count_errors(cur, 'dispatch_finalization')
        assert error_count_after == error_count_before + 1


# ---------------------------------------------------------------------------
# TEST 3: Permissions
# ---------------------------------------------------------------------------

class TestTransportPermissions:

    def test_lcs_transport_role_exists(self, cur):
        """lcs_transport role exists."""
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'lcs_transport'")
        assert cur.fetchone() is not None

    def test_lcs_transport_has_execute(self, cur):
        """lcs_transport has EXECUTE on fn_record_dispatch_result."""
        cur.execute("""
            SELECT has_function_privilege('lcs_transport',
                'lcs.fn_record_dispatch_result(uuid, text, text, text, jsonb)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_lcs_transport_no_table_write(self, cur):
        """lcs_transport lacks INSERT on mid_ledger."""
        cur.execute("""
            SELECT has_table_privilege('lcs_transport', 'lcs.mid_ledger', 'INSERT')
        """)
        assert cur.fetchone()[0] is False

    def test_lcs_transport_no_event_log_write(self, cur):
        """lcs_transport lacks INSERT on dispatch_event_log."""
        cur.execute("""
            SELECT has_table_privilege('lcs_transport', 'lcs.dispatch_event_log', 'INSERT')
        """)
        assert cur.fetchone()[0] is False
