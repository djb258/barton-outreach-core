"""
Tests for SRC 4 — LCS Emission Status Guard Trigger
=====================================================
Validates column-level immutability guard on lcs.movement_emission_intake.
Blocks UPDATE on identity/evidence columns.
Allows: status, reject_reason, promoted_cid, error_id, processed_at.
DELETE remains fully blocked.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_emission_status_guard_trigger.py -v
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


def _insert_emission(cur):
    """Helper: insert a raw STAGED emission and return emission_id."""
    eid = uuid.uuid4()
    dedupe = f'guard_test_{uuid.uuid4().hex[:8]}'
    evidence = f'{{"test": "guard_{uuid.uuid4().hex[:8]}"}}'
    cur.execute("""
        INSERT INTO lcs.movement_emission_intake
            (emission_id, source_hub, movement_type_code, outreach_id, sovereign_id,
             evidence, dedupe_key, status)
        VALUES (%s, 'dol-filings', 'BROKER_CHANGE', NULL, NULL, %s::jsonb, %s, 'STAGED')
    """, (str(eid), evidence, dedupe))
    return eid


# ---------------------------------------------------------------------------
# TEST 1: Allowed mutable column updates
# ---------------------------------------------------------------------------

class TestAllowedUpdates:

    def test_update_status_allowed(self, cur):
        """UPDATE status column succeeds."""
        eid = _insert_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'PROMOTED'
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] == 'PROMOTED'

    def test_update_reject_reason_allowed(self, cur):
        """UPDATE reject_reason column succeeds."""
        eid = _insert_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET reject_reason = 'outreach_id not found'
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT reject_reason FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] == 'outreach_id not found'

    def test_update_promoted_cid_allowed(self, cur):
        """UPDATE promoted_cid column succeeds."""
        eid = _insert_emission(cur)
        fake_cid = uuid.uuid4()
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET promoted_cid = %s
            WHERE emission_id = %s
        """, (str(fake_cid), str(eid)))
        cur.execute("SELECT promoted_cid FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert str(cur.fetchone()[0]) == str(fake_cid)

    def test_update_error_id_allowed(self, cur):
        """UPDATE error_id column succeeds."""
        eid = _insert_emission(cur)
        fake_err = uuid.uuid4()
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET error_id = %s
            WHERE emission_id = %s
        """, (str(fake_err), str(eid)))
        cur.execute("SELECT error_id FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert str(cur.fetchone()[0]) == str(fake_err)

    def test_update_processed_at_allowed(self, cur):
        """UPDATE processed_at column succeeds."""
        eid = _insert_emission(cur)
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET processed_at = NOW()
            WHERE emission_id = %s
        """, (str(eid),))
        cur.execute("SELECT processed_at FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        assert cur.fetchone()[0] is not None


# ---------------------------------------------------------------------------
# TEST 2: Blocked immutable column updates
# ---------------------------------------------------------------------------

class TestBlockedUpdates:

    def test_update_source_hub_blocked(self, cur):
        """UPDATE source_hub is blocked by guard trigger."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake
                SET source_hub = 'blog-scraper'
                WHERE emission_id = %s
            """, (str(eid),))

    def test_update_movement_type_code_blocked(self, cur):
        """UPDATE movement_type_code is blocked by guard trigger."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake
                SET movement_type_code = 'PLAN_COST_SPIKE'
                WHERE emission_id = %s
            """, (str(eid),))

    def test_update_evidence_blocked(self, cur):
        """UPDATE evidence is blocked by guard trigger."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake
                SET evidence = '{"tampered": true}'::jsonb
                WHERE emission_id = %s
            """, (str(eid),))

    def test_update_dedupe_key_blocked(self, cur):
        """UPDATE dedupe_key is blocked by guard trigger."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake
                SET dedupe_key = 'tampered_key'
                WHERE emission_id = %s
            """, (str(eid),))

    def test_update_created_at_blocked(self, cur):
        """UPDATE created_at is blocked by guard trigger."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake
                SET created_at = '2020-01-01'::timestamptz
                WHERE emission_id = %s
            """, (str(eid),))


# ---------------------------------------------------------------------------
# TEST 3: DELETE fully blocked
# ---------------------------------------------------------------------------

class TestDeleteBlocked:

    def test_delete_blocked(self, cur):
        """DELETE on movement_emission_intake is fully blocked."""
        eid = _insert_emission(cur)
        with pytest.raises(psycopg2.errors.RaiseException):
            cur.execute("""
                DELETE FROM lcs.movement_emission_intake
                WHERE emission_id = %s
            """, (str(eid),))


# ---------------------------------------------------------------------------
# TEST 4: Combined legal status transitions
# ---------------------------------------------------------------------------

class TestStatusTransitions:

    def test_staged_to_promoted_with_cid(self, cur):
        """Full legal transition: STAGED → PROMOTED with promoted_cid + processed_at."""
        eid = _insert_emission(cur)
        fake_cid = uuid.uuid4()
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'PROMOTED', promoted_cid = %s, processed_at = NOW()
            WHERE emission_id = %s
        """, (str(fake_cid), str(eid)))
        cur.execute("""
            SELECT status, promoted_cid, processed_at
            FROM lcs.movement_emission_intake WHERE emission_id = %s
        """, (str(eid),))
        row = cur.fetchone()
        assert row[0] == 'PROMOTED'
        assert str(row[1]) == str(fake_cid)
        assert row[2] is not None

    def test_staged_to_rejected_with_reason(self, cur):
        """Full legal transition: STAGED → REJECTED with reject_reason + error_id."""
        eid = _insert_emission(cur)
        fake_err = uuid.uuid4()
        cur.execute("""
            UPDATE lcs.movement_emission_intake
            SET status = 'REJECTED', reject_reason = 'bad FK', error_id = %s, processed_at = NOW()
            WHERE emission_id = %s
        """, (str(fake_err), str(eid)))
        cur.execute("""
            SELECT status, reject_reason, error_id
            FROM lcs.movement_emission_intake WHERE emission_id = %s
        """, (str(eid),))
        row = cur.fetchone()
        assert row[0] == 'REJECTED'
        assert row[1] == 'bad FK'
        assert str(row[2]) == str(fake_err)
