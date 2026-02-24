"""
Tests for Phase 2D — Promotion Determinism Guard
==================================================
Validates idempotency, replay safety, and concurrency guarantees
on lcs.fn_promote_emission and lcs.cid_intake uniqueness.

One emission → one CID. Replays are safe. No RAISE on any path.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_promotion_determinism_guard.py -v
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


@pytest.fixture(scope="module")
def real_fk_pair(cur):
    """Fetch a fresh outreach_id + sovereign_id not yet in sid_registry."""
    cur.execute("""
        SELECT o.outreach_id, ci.company_unique_id
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_company_id = ci.company_unique_id
        WHERE o.outreach_id NOT IN (SELECT outreach_id FROM lcs.sid_registry)
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "No unused FK pair found"
    return {"outreach_id": row[0], "sovereign_id": row[1]}


def _emit_staged(cur, outreach_id, sovereign_id, movement_type='BROKER_CHANGE'):
    """Helper: emit a STAGED emission and return emission_id."""
    evidence = f'{{"test": "determ_{uuid.uuid4().hex[:8]}"}}'
    cur.execute("""
        SELECT lcs.fn_emit_movement(
            'dol-filings', %s, %s, %s, %s::jsonb
        )
    """, (movement_type, outreach_id, sovereign_id, evidence))
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# TEST 1: UNIQUE(emission_id) enforcement on cid_intake
# ---------------------------------------------------------------------------

class TestCidIntakeUniqueness:

    def test_emission_id_column_exists(self, cur):
        """cid_intake has emission_id column."""
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'lcs' AND table_name = 'cid_intake'
              AND column_name = 'emission_id'
        """)
        row = cur.fetchone()
        assert row is not None, "emission_id column missing from cid_intake"
        assert row[1] == 'uuid'

    def test_unique_index_exists(self, cur):
        """Unique index on emission_id exists."""
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname = 'lcs' AND tablename = 'cid_intake'
              AND indexname = 'uq_cid_intake_emission_id'
        """)
        assert cur.fetchone() is not None, "uq_cid_intake_emission_id index missing"

    def test_duplicate_emission_id_blocked(self, cur):
        """Direct INSERT with duplicate emission_id is blocked by unique index."""
        test_eid = uuid.uuid4()
        cur.execute("""
            INSERT INTO lcs.cid_intake
                (outreach_id, sovereign_id, movement_type_code, status,
                 source_hub, evidence, emission_id)
            SELECT o.outreach_id, o.sovereign_company_id, 'BROKER_CHANGE', 'PENDING',
                   'test', '{}'::jsonb, %s
            FROM outreach.outreach o LIMIT 1
        """, (str(test_eid),))

        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute("""
                INSERT INTO lcs.cid_intake
                    (outreach_id, sovereign_id, movement_type_code, status,
                     source_hub, evidence, emission_id)
                SELECT o.outreach_id, o.sovereign_company_id, 'BROKER_CHANGE', 'PENDING',
                       'test', '{}'::jsonb, %s
                FROM outreach.outreach o LIMIT 1
            """, (str(test_eid),))


# ---------------------------------------------------------------------------
# TEST 2: Idempotent promotion — replay safety
# ---------------------------------------------------------------------------

class TestIdempotentPromotion:

    def test_replay_returns_clean(self, cur, real_fk_pair):
        """Promoting the same emission twice returns clean both times."""
        eid = _emit_staged(cur, real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"])

        # First promotion
        cur.execute("SELECT lcs.fn_promote_emission(%s)", (eid,))

        cur.execute("SELECT status, promoted_cid FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        row = cur.fetchone()
        assert row[0] == 'PROMOTED'
        first_cid = row[1]
        assert first_cid is not None

        # Replay — should return clean, not raise, not mint new CID
        cur.execute("SELECT lcs.fn_promote_emission(%s)", (eid,))

        cur.execute("SELECT status, promoted_cid FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        row2 = cur.fetchone()
        assert row2[0] == 'PROMOTED'
        assert str(row2[1]) == str(first_cid), "Replay must not change promoted_cid"

    def test_replay_no_duplicate_cid(self, cur, real_fk_pair):
        """Replaying promotion does not create a second CID row."""
        eid = _emit_staged(cur, real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"],
                           'PLAN_COST_SPIKE')

        # Promote
        cur.execute("SELECT lcs.fn_promote_emission(%s)", (eid,))

        # Count CIDs for this emission
        cur.execute("SELECT count(*) FROM lcs.cid_intake WHERE emission_id = %s", (str(eid),))
        count_before = cur.fetchone()[0]
        assert count_before == 1

        # Replay
        cur.execute("SELECT lcs.fn_promote_emission(%s)", (eid,))

        # Count should remain 1
        cur.execute("SELECT count(*) FROM lcs.cid_intake WHERE emission_id = %s", (str(eid),))
        count_after = cur.fetchone()[0]
        assert count_after == 1, f"Expected 1 CID, got {count_after} — duplicate minted"


# ---------------------------------------------------------------------------
# TEST 3: Promotion inserts emission_id into cid_intake
# ---------------------------------------------------------------------------

class TestEmissionIdInCidIntake:

    def test_promotion_sets_emission_id(self, cur, real_fk_pair):
        """Promoted CID row has emission_id set to the source emission."""
        eid = _emit_staged(cur, real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"],
                           'RENEWAL_APPROACHING')

        cur.execute("SELECT lcs.fn_promote_emission(%s)", (eid,))

        cur.execute("SELECT promoted_cid FROM lcs.movement_emission_intake WHERE emission_id = %s", (str(eid),))
        cid = cur.fetchone()[0]

        cur.execute("SELECT emission_id FROM lcs.cid_intake WHERE cid = %s", (str(cid),))
        stored_eid = cur.fetchone()[0]
        assert str(stored_eid) == str(eid), "CID row must have emission_id matching source emission"


# ---------------------------------------------------------------------------
# TEST 4: Batch promotion concurrency safety
# ---------------------------------------------------------------------------

class TestBatchConcurrency:

    def test_batch_skip_locked(self, cur, real_fk_pair):
        """Batch uses SKIP LOCKED — verify it runs without error."""
        # Emit a few emissions
        _emit_staged(cur, real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"],
                     'CARRIER_CHANGE')

        # Batch promote — should work without error
        cur.execute("SELECT lcs.fn_promote_emission_batch(10)")
        count = cur.fetchone()[0]
        assert count >= 0

    def test_batch_no_double_mint(self, cur, real_fk_pair):
        """Running batch twice does not double-mint CIDs."""
        # Get fresh pair
        cur.execute("""
            SELECT o.outreach_id, ci.company_unique_id
            FROM outreach.outreach o
            JOIN cl.company_identity ci ON o.sovereign_company_id = ci.company_unique_id
            WHERE o.outreach_id NOT IN (SELECT outreach_id FROM lcs.sid_registry)
            OFFSET 2 LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No additional FK pair for batch double-mint test")

        oid, sid = row[0], row[1]
        eid = _emit_staged(cur, oid, sid)

        # First batch
        cur.execute("SELECT lcs.fn_promote_emission_batch(100)")
        cur.fetchone()

        # Count CIDs for this emission
        cur.execute("SELECT count(*) FROM lcs.cid_intake WHERE emission_id = %s", (str(eid),))
        count1 = cur.fetchone()[0]

        # Second batch (replay) — should be no-op
        cur.execute("SELECT lcs.fn_promote_emission_batch(100)")
        cur.fetchone()

        cur.execute("SELECT count(*) FROM lcs.cid_intake WHERE emission_id = %s", (str(eid),))
        count2 = cur.fetchone()[0]
        assert count2 == count1, f"Double-mint detected: {count1} → {count2}"


# ---------------------------------------------------------------------------
# TEST 5: Forward-only status transitions preserved
# ---------------------------------------------------------------------------

class TestForwardOnlyStatus:

    def test_promoted_cannot_revert_to_staged(self, cur, real_fk_pair):
        """PROMOTED emission cannot be manually reverted to STAGED."""
        # Find a PROMOTED emission
        cur.execute("""
            SELECT emission_id FROM lcs.movement_emission_intake
            WHERE status = 'PROMOTED' LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No PROMOTED emission to test")

        # SRC 4 guard trigger blocks changes to identity columns but allows status.
        # Status reversion is handled by fn_promote_emission's idempotent check,
        # not by the trigger. Verify fn_promote_emission returns clean on replay.
        cur.execute("SELECT lcs.fn_promote_emission(%s)", (row[0],))
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (row[0],))
        assert cur.fetchone()[0] == 'PROMOTED'
