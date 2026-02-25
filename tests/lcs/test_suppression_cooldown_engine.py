"""
Tests for Phase 3B — Suppression + Cooldown Engine (Foundational Layer)
=======================================================================
Validates suppression_registry table, fn_mid_suppression_check real
implementation, readiness integration with fn_mark_mid_ready, and
deterministic error logging.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_suppression_cooldown_engine.py -v
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
    """Create a test MID chain (CID -> SID -> MID) and advance to target state."""
    oid, sovereign_id = _get_test_ids(cur)
    mtc = _get_movement_type(cur)

    cur.execute("""
        INSERT INTO lcs.cid_intake (outreach_id, sovereign_id, movement_type_code, source_subhub, detected_at, status)
        VALUES (%s, %s, %s, '04.04.02', NOW(), 'PENDING')
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
            cur.execute("""
                UPDATE lcs.mid_ledger SET dispatch_state = %s WHERE mid = %s
            """, (advance_path[i], str(mid)))

    return mid, cid, sid, oid, sovereign_id


def _count_errors(cur, stage):
    """Count errors from a specific error_stage."""
    cur.execute("SELECT count(*) FROM lcs.lcs_errors WHERE error_stage = %s", (stage,))
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# TEST 1: suppression_registry table structure
# ---------------------------------------------------------------------------

class TestSuppressionRegistry:

    def test_table_exists(self, cur):
        """suppression_registry table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'suppression_registry'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """suppression_registry is registered in CTB as CANONICAL."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'suppression_registry'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'CANONICAL'

    def test_delete_blocked(self, cur):
        """DELETE on suppression_registry is blocked."""
        _, sovereign_id = _get_test_ids(cur)

        # Ensure a row exists
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed)
            VALUES (%s, FALSE)
            ON CONFLICT (sovereign_id) DO NOTHING
        """, (str(sovereign_id),))

        with pytest.raises(psycopg2.errors.RaiseException, match="cannot be deleted"):
            cur.execute("DELETE FROM lcs.suppression_registry WHERE sovereign_id = %s", (str(sovereign_id),))

    def test_update_allowed(self, cur):
        """UPDATE on suppression_registry is allowed (governance surface)."""
        _, sovereign_id = _get_test_ids(cur)

        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed)
            VALUES (%s, FALSE)
            ON CONFLICT (sovereign_id) DO NOTHING
        """, (str(sovereign_id),))

        cur.execute("""
            UPDATE lcs.suppression_registry
            SET suppression_reason = 'test', updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))

        cur.execute("""
            SELECT suppression_reason FROM lcs.suppression_registry WHERE sovereign_id = %s
        """, (str(sovereign_id),))
        assert cur.fetchone()[0] == 'test'

        # Clean up test value
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET suppression_reason = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))


# ---------------------------------------------------------------------------
# TEST 2: fn_mid_suppression_check — real implementation
# ---------------------------------------------------------------------------

class TestSuppressionCheck:

    def test_suppressed_returns_false(self, cur):
        """fn_mid_suppression_check returns FALSE when global_suppressed = TRUE."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Set suppression
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, suppressed_at)
            VALUES (%s, TRUE, NOW())
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = TRUE, suppressed_at = NOW(), updated_at = NOW()
        """, (str(sovereign_id),))

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        assert cur.fetchone()[0] is False

        # Clean up
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET global_suppressed = FALSE, suppressed_at = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))

    def test_cooldown_active_returns_false(self, cur):
        """fn_mid_suppression_check returns FALSE when cooldown_until > NOW()."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Set cooldown 1 hour in the future
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, cooldown_until)
            VALUES (%s, FALSE, NOW() + INTERVAL '1 hour')
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = FALSE, cooldown_until = NOW() + INTERVAL '1 hour', updated_at = NOW()
        """, (str(sovereign_id),))

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        assert cur.fetchone()[0] is False

        # Clean up
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET cooldown_until = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))

    def test_not_suppressed_returns_true(self, cur):
        """fn_mid_suppression_check returns TRUE when not suppressed and no cooldown."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Ensure clean state
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, cooldown_until)
            VALUES (%s, FALSE, NULL)
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = FALSE, cooldown_until = NULL, updated_at = NOW()
        """, (str(sovereign_id),))

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        assert cur.fetchone()[0] is True

    def test_no_registry_row_returns_true(self, cur):
        """fn_mid_suppression_check returns TRUE when no suppression_registry row exists."""
        # Use a different sovereign_id that won't have a suppression row
        cur.execute("""
            SELECT o.outreach_id, o.sovereign_company_id
            FROM outreach.outreach o
            WHERE o.sovereign_company_id NOT IN (
                SELECT sovereign_id FROM lcs.suppression_registry
            )
            LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("All test sovereigns have suppression rows")

        oid, sovereign_id = row[0], row[1]
        mtc = _get_movement_type(cur)

        # Create MID for this sovereign
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

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        assert cur.fetchone()[0] is True

    def test_cooldown_expired_returns_true(self, cur):
        """fn_mid_suppression_check returns TRUE when cooldown_until is in the past."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Set cooldown 1 hour in the PAST (expired)
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, cooldown_until)
            VALUES (%s, FALSE, NOW() - INTERVAL '1 hour')
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = FALSE, cooldown_until = NOW() - INTERVAL '1 hour', updated_at = NOW()
        """, (str(sovereign_id),))

        cur.execute("SELECT lcs.fn_mid_suppression_check(%s)", (str(mid),))
        assert cur.fetchone()[0] is True

        # Clean up
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET cooldown_until = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))


# ---------------------------------------------------------------------------
# TEST 3: Readiness integration — fn_mark_mid_ready with real suppression
# ---------------------------------------------------------------------------

class TestReadinessIntegration:

    def test_mark_mid_ready_denied_when_suppressed(self, cur):
        """fn_mark_mid_ready denies READY and logs error when sovereign is suppressed."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Ensure canonical row with eligible lifecycle
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

        # Set global suppression
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, suppressed_at)
            VALUES (%s, TRUE, NOW())
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = TRUE, suppressed_at = NOW(), updated_at = NOW()
        """, (str(sovereign_id),))

        error_count_before = _count_errors(cur, 'mid_minting')

        # Should NOT raise — returns cleanly
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(mid),))

        # Verify MID did NOT advance
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'COMPILED'

        # Verify error logged
        error_count_after = _count_errors(cur, 'mid_minting')
        assert error_count_after == error_count_before + 1

        # Verify error details
        cur.execute("""
            SELECT error_type, error_payload FROM lcs.lcs_errors
            WHERE error_stage = 'mid_minting' AND mid = %s
            ORDER BY created_at DESC LIMIT 1
        """, (str(mid),))
        row = cur.fetchone()
        assert row[0] == 'conflict'
        payload = row[1] if isinstance(row[1], dict) else json.loads(row[1])
        assert 'suppressed' in payload['message'].lower()

        # Clean up suppression
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET global_suppressed = FALSE, suppressed_at = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))

    def test_mark_mid_ready_denied_when_cooldown_active(self, cur):
        """fn_mark_mid_ready denies READY when sovereign has active cooldown."""
        mid, _, _, _, sovereign_id = _create_test_mid(cur, 'COMPILED')

        # Ensure canonical row
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

        # Set active cooldown
        cur.execute("""
            INSERT INTO lcs.suppression_registry (sovereign_id, global_suppressed, cooldown_until)
            VALUES (%s, FALSE, NOW() + INTERVAL '1 hour')
            ON CONFLICT (sovereign_id)
            DO UPDATE SET global_suppressed = FALSE, cooldown_until = NOW() + INTERVAL '1 hour', updated_at = NOW()
        """, (str(sovereign_id),))

        # Should NOT raise
        cur.execute("SELECT lcs.fn_mark_mid_ready(%s)", (str(mid),))

        # Verify MID did NOT advance
        cur.execute("SELECT dispatch_state FROM lcs.mid_ledger WHERE mid = %s", (str(mid),))
        assert cur.fetchone()[0] == 'COMPILED'

        # Clean up
        cur.execute("""
            UPDATE lcs.suppression_registry
            SET cooldown_until = NULL, updated_at = NOW()
            WHERE sovereign_id = %s
        """, (str(sovereign_id),))
