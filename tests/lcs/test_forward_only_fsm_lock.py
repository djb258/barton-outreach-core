"""
Tests for Phase 2E — Forward-Only FSM Lock
============================================
Validates emission status FSM, CID immutability, and canonical
monotonic progression guards.

No rewind. No regression. All violations fail loudly.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_forward_only_fsm_lock.py -v
"""

import os
import uuid
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


def _insert_staged_emission(cur):
    """Helper: insert a raw STAGED emission for FSM testing."""
    eid = uuid.uuid4()
    dedupe = f'fsm_test_{uuid.uuid4().hex[:8]}'
    evidence = f'{{"test": "fsm_{uuid.uuid4().hex[:8]}"}}'
    cur.execute("""
        INSERT INTO lcs.movement_emission_intake
            (emission_id, source_hub, movement_type_code, outreach_id, sovereign_id,
             evidence, dedupe_key, status)
        VALUES (%s, 'dol-filings', 'BROKER_CHANGE', NULL, NULL, %s::jsonb, %s, 'STAGED')
    """, (str(eid), evidence, dedupe))
    return eid


# ---------------------------------------------------------------------------
# PART 1: Emission Status FSM
# ---------------------------------------------------------------------------

class TestEmissionFSM:

    def test_staged_to_promoted_allowed(self, cur):
        """STAGED → PROMOTED is a legal transition."""
        eid = _insert_staged_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'PROMOTED', processed_at = NOW()
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] == 'PROMOTED'

    def test_staged_to_rejected_allowed(self, cur):
        """STAGED → REJECTED is a legal transition."""
        eid = _insert_staged_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'REJECTED', processed_at = NOW()
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] == 'REJECTED'

    def test_staged_to_error_allowed(self, cur):
        """STAGED → ERROR is a legal transition."""
        eid = _insert_staged_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'ERROR', processed_at = NOW()
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] == 'ERROR'

    def test_promoted_to_staged_blocked(self, cur):
        """PROMOTED → STAGED is blocked (terminal state)."""
        eid = _insert_staged_emission(cur)
        cur.execute("UPDATE lcs.movement_emission_intake SET status = 'PROMOTED' WHERE emission_id = %s", (str(eid),))
        with pytest.raises(psycopg2.errors.RaiseException, match="illegal status transition"):
            cur.execute("UPDATE lcs.movement_emission_intake SET status = 'STAGED' WHERE emission_id = %s", (str(eid),))

    def test_rejected_to_staged_blocked(self, cur):
        """REJECTED → STAGED is blocked (terminal state)."""
        eid = _insert_staged_emission(cur)
        cur.execute("UPDATE lcs.movement_emission_intake SET status = 'REJECTED' WHERE emission_id = %s", (str(eid),))
        with pytest.raises(psycopg2.errors.RaiseException, match="illegal status transition"):
            cur.execute("UPDATE lcs.movement_emission_intake SET status = 'STAGED' WHERE emission_id = %s", (str(eid),))

    def test_promoted_to_rejected_blocked(self, cur):
        """PROMOTED → REJECTED is blocked (terminal crossover)."""
        eid = _insert_staged_emission(cur)
        cur.execute("UPDATE lcs.movement_emission_intake SET status = 'PROMOTED' WHERE emission_id = %s", (str(eid),))
        with pytest.raises(psycopg2.errors.RaiseException, match="illegal status transition"):
            cur.execute("UPDATE lcs.movement_emission_intake SET status = 'REJECTED' WHERE emission_id = %s", (str(eid),))

    def test_rejected_to_promoted_blocked(self, cur):
        """REJECTED → PROMOTED is blocked (terminal crossover)."""
        eid = _insert_staged_emission(cur)
        cur.execute("UPDATE lcs.movement_emission_intake SET status = 'REJECTED' WHERE emission_id = %s", (str(eid),))
        with pytest.raises(psycopg2.errors.RaiseException, match="illegal status transition"):
            cur.execute("UPDATE lcs.movement_emission_intake SET status = 'PROMOTED' WHERE emission_id = %s", (str(eid),))


# ---------------------------------------------------------------------------
# PART 2: CID Intake Immutability (v0 enforcement verification)
# ---------------------------------------------------------------------------

class TestCidImmutability:

    def test_cid_update_after_accepted_blocked(self, cur):
        """UPDATE on ACCEPTED CID row is blocked."""
        cur.execute("SELECT cid FROM lcs.cid_intake WHERE status = 'ACCEPTED' LIMIT 1")
        row = cur.fetchone()
        if row is None:
            pytest.skip("No ACCEPTED CID to test")

        with pytest.raises(psycopg2.errors.RaiseException, match="append-only"):
            cur.execute("""
                UPDATE lcs.cid_intake SET evidence = '{"tampered": true}'::jsonb
                WHERE cid = %s
            """, (row[0],))

    def test_cid_delete_blocked(self, cur):
        """DELETE on cid_intake is blocked."""
        cur.execute("SELECT cid FROM lcs.cid_intake LIMIT 1")
        row = cur.fetchone()
        if row is None:
            pytest.skip("No CID to test")

        with pytest.raises(psycopg2.errors.RaiseException, match="append-only"):
            cur.execute("DELETE FROM lcs.cid_intake WHERE cid = %s", (row[0],))


# ---------------------------------------------------------------------------
# PART 3: Canonical Monotonic Guard
# ---------------------------------------------------------------------------

class TestCanonicalMonotonic:

    def _get_canonical_row(self, cur):
        """Get a canonical row for testing."""
        cur.execute("""
            SELECT sovereign_id, current_lifecycle_stage, current_sid,
                   current_mid, current_dispatch_state, last_cid
            FROM lcs.lcs_canonical LIMIT 1
        """)
        return cur.fetchone()

    def test_lifecycle_regression_blocked(self, cur):
        """Lifecycle stage regression (ENGAGED → SUSPECT) is blocked."""
        row = self._get_canonical_row(cur)
        if row is None:
            pytest.skip("No canonical row to test")

        sid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="lifecycle regression"):
            cur.execute("""
                SET LOCAL lcs.allow_canonical_write = 'on';
                UPDATE lcs.lcs_canonical
                SET current_lifecycle_stage = 'SUSPECT'
                WHERE sovereign_id = %s
            """, (str(sid),))

    def test_sid_rewind_blocked(self, cur):
        """SID change (once set) is blocked."""
        row = self._get_canonical_row(cur)
        if row is None or row[2] is None:
            pytest.skip("No canonical row with SID to test")

        sid = row[0]
        fake_sid = uuid.uuid4()
        with pytest.raises(psycopg2.errors.RaiseException, match="SID rewind"):
            cur.execute("""
                SET LOCAL lcs.allow_canonical_write = 'on';
                UPDATE lcs.lcs_canonical
                SET current_sid = %s
                WHERE sovereign_id = %s
            """, (str(fake_sid), str(sid)))

    def test_mid_null_regression_blocked(self, cur):
        """MID null regression (non-NULL → NULL) is blocked."""
        row = self._get_canonical_row(cur)
        if row is None or row[3] is None:
            pytest.skip("No canonical row with MID to test")

        sid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="MID null regression"):
            cur.execute("""
                SET LOCAL lcs.allow_canonical_write = 'on';
                UPDATE lcs.lcs_canonical
                SET current_mid = NULL
                WHERE sovereign_id = %s
            """, (str(sid),))

    def test_last_cid_null_regression_blocked(self, cur):
        """last_cid null regression (non-NULL → NULL) is blocked."""
        row = self._get_canonical_row(cur)
        if row is None or row[5] is None:
            pytest.skip("No canonical row with last_cid to test")

        sid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="last_cid null regression"):
            cur.execute("""
                SET LOCAL lcs.allow_canonical_write = 'on';
                UPDATE lcs.lcs_canonical
                SET last_cid = NULL
                WHERE sovereign_id = %s
            """, (str(sid),))

    def test_dispatch_regression_same_mid_blocked(self, cur):
        """Dispatch state regression within same MID is blocked."""
        cur.execute("""
            SELECT sovereign_id, current_mid, current_dispatch_state
            FROM lcs.lcs_canonical
            WHERE current_dispatch_state != 'MINTED'
              AND current_mid IS NOT NULL
            LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No canonical row with advanced dispatch to test")

        sid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="dispatch state regression"):
            cur.execute("""
                SET LOCAL lcs.allow_canonical_write = 'on';
                UPDATE lcs.lcs_canonical
                SET current_dispatch_state = 'MINTED'
                WHERE sovereign_id = %s
            """, (str(sid),))

    def test_lifecycle_forward_allowed(self, cur):
        """Lifecycle forward progression (same or higher ordinal) is allowed."""
        row = self._get_canonical_row(cur)
        if row is None:
            pytest.skip("No canonical row to test")

        sid = row[0]
        current_stage = row[1]
        # Same stage should be allowed (no-op update)
        cur.execute("""
            SET LOCAL lcs.allow_canonical_write = 'on';
            UPDATE lcs.lcs_canonical
            SET current_lifecycle_stage = %s
            WHERE sovereign_id = %s
        """, (current_stage, str(sid)))
        # Should not raise
        cur.execute("SELECT current_lifecycle_stage FROM lcs.lcs_canonical WHERE sovereign_id = %s", (str(sid),))
        assert cur.fetchone()[0] == current_stage
