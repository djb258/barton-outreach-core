"""
Tests for LCS Movement Emission Governance (Phase 2A)
=====================================================
Validates fn_emit_movement, fn_process_emissions, idempotency,
error promotion, permission enforcement, and status transitions.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_movement_emission_governance.py -v
"""

import os
import uuid
import pytest
import psycopg2

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def conn():
    """Live Neon connection for the test module."""
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
    """Cursor reused across module."""
    c = conn.cursor()
    yield c
    c.close()


@pytest.fixture(scope="module")
def real_fk_pair(cur):
    """Fetch a real outreach_id + sovereign_id for FK-valid tests."""
    cur.execute("""
        SELECT o.outreach_id, ci.company_unique_id
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_company_id = ci.company_unique_id
        WHERE o.outreach_id NOT IN (SELECT outreach_id FROM lcs.sid_registry)
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "No unused outreach_id/sovereign_id pair found"
    return {"outreach_id": row[0], "sovereign_id": row[1]}


@pytest.fixture(scope="module")
def error_count_before(cur):
    """Snapshot lcs_errors count before tests."""
    cur.execute("SELECT count(*) FROM lcs.lcs_errors")
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# TEST 1: fn_emit_movement — callability and validation paths
# ---------------------------------------------------------------------------

class TestEmitMovement:

    def test_valid_emission(self, cur, real_fk_pair):
        """Valid emission returns a non-NULL emission_id."""
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'BROKER_CHANGE',
                %s, %s,
                '{"broker_name": "Acme Insurance"}'::jsonb
            )
        """, (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"]))
        result = cur.fetchone()[0]
        assert result is not None, "fn_emit_movement should return emission_id"

    def test_invalid_movement_type(self, cur, real_fk_pair):
        """Unknown movement_type_code returns NULL + logs error."""
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'NONEXISTENT_TYPE',
                %s, %s, '{}'::jsonb
            )
        """, (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"]))
        result = cur.fetchone()[0]
        assert result is None, "Invalid movement type should return NULL"

        cur.execute("""
            SELECT error_type FROM lcs.lcs_errors
            WHERE error_stage = 'emission_validation'
              AND error_payload->>'reason' LIKE 'unknown movement_type_code%'
            ORDER BY created_at DESC LIMIT 1
        """)
        assert cur.fetchone() is not None, "Error row should exist for invalid type"

    def test_unauthorized_source(self, cur, real_fk_pair):
        """Source not in allowed_sources returns NULL + logs error."""
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'blog-content', 'BROKER_CHANGE',
                %s, %s, '{}'::jsonb
            )
        """, (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"]))
        result = cur.fetchone()[0]
        assert result is None, "Unauthorized source should return NULL"

        cur.execute("""
            SELECT error_payload->>'reason' FROM lcs.lcs_errors
            WHERE error_stage = 'emission_validation'
              AND error_payload->>'reason' LIKE 'source%not in allowed_sources%'
            ORDER BY created_at DESC LIMIT 1
        """)
        assert cur.fetchone() is not None, "Error row should exist for unauthorized source"

    def test_missing_sovereign_id(self, cur, real_fk_pair):
        """Missing required sovereign_id returns NULL + logs error."""
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'BROKER_CHANGE',
                %s, NULL, '{}'::jsonb
            )
        """, (real_fk_pair["outreach_id"],))
        result = cur.fetchone()[0]
        assert result is None, "Missing sovereign_id should return NULL"

    def test_missing_outreach_id(self, cur, real_fk_pair):
        """Missing required outreach_id returns NULL + logs error."""
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'BROKER_CHANGE',
                NULL, %s, '{}'::jsonb
            )
        """, (real_fk_pair["sovereign_id"],))
        result = cur.fetchone()[0]
        assert result is None, "Missing outreach_id should return NULL"


# ---------------------------------------------------------------------------
# TEST 2: Idempotent insert / dedupe_key behavior
# ---------------------------------------------------------------------------

class TestDeduplication:

    def test_duplicate_emission_returns_same_id(self, cur, real_fk_pair):
        """Same emission twice returns the same emission_id (dedupe)."""
        evidence = '{"test_key": "dedupe_test_' + str(uuid.uuid4())[:8] + '"}'
        args = (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"])

        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'RENEWAL_APPROACHING', %s, %s, %s::jsonb
            )
        """, (*args, evidence))
        first_id = cur.fetchone()[0]

        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'RENEWAL_APPROACHING', %s, %s, %s::jsonb
            )
        """, (*args, evidence))
        second_id = cur.fetchone()[0]

        assert first_id == second_id, "Duplicate emission should return same emission_id"

    def test_different_evidence_creates_new_emission(self, cur, real_fk_pair):
        """Different evidence produces different dedupe_key → new row."""
        args = (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"])

        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'PLAN_COST_SPIKE', %s, %s,
                '{"delta": 0.18}'::jsonb
            )
        """, args)
        id1 = cur.fetchone()[0]

        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'PLAN_COST_SPIKE', %s, %s,
                '{"delta": 0.25}'::jsonb
            )
        """, args)
        id2 = cur.fetchone()[0]

        assert id1 != id2, "Different evidence should create different emissions"


# ---------------------------------------------------------------------------
# TEST 3: fn_process_emissions — promotion path
# ---------------------------------------------------------------------------

class TestProcessEmissions:

    def test_promotion_to_cid(self, cur, real_fk_pair):
        """STAGED emission with valid FKs gets promoted to cid_intake."""
        # Emit a fresh movement
        evidence = '{"test": "promotion_' + str(uuid.uuid4())[:8] + '"}'
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'dol-filings', 'CARRIER_CHANGE', %s, %s, %s::jsonb
            )
        """, (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"], evidence))
        eid = cur.fetchone()[0]
        assert eid is not None

        # Process it
        cur.execute("SELECT * FROM lcs.fn_process_emissions(10)")
        rows = cur.fetchall()
        promoted = [r for r in rows if str(r[0]) == str(eid)]
        assert len(promoted) == 1, "Emission should appear in process results"
        assert promoted[0][1] == 'PROMOTED', f"Status should be PROMOTED, got {promoted[0][1]}"
        assert promoted[0][2] is not None, "promoted_cid should be non-NULL"

        # Verify CID exists in cid_intake
        cid = promoted[0][2]
        cur.execute("SELECT status, source_hub FROM lcs.cid_intake WHERE cid = %s", (cid,))
        cid_row = cur.fetchone()
        assert cid_row is not None, "CID should exist in cid_intake"
        assert cid_row[0] == 'PENDING', "New CID should be PENDING"
        assert cid_row[1] == 'dol-filings'

    def test_rejection_invalid_outreach_id(self, cur, real_fk_pair):
        """Emission with bad outreach_id gets REJECTED + error logged."""
        fake_oid = str(uuid.uuid4())
        evidence = '{"test": "reject_' + str(uuid.uuid4())[:8] + '"}'
        # Emit with valid source but fake outreach_id
        # Need to bypass requires_outreach validation — emit manually
        cur.execute("""
            INSERT INTO lcs.movement_emission_intake
                (source_hub, movement_type_code, outreach_id, sovereign_id, evidence, dedupe_key, status)
            VALUES
                ('dol-filings', 'BROKER_CHANGE', %s, %s, %s::jsonb, %s, 'STAGED')
            RETURNING emission_id
        """, (fake_oid, real_fk_pair["sovereign_id"], evidence, 'reject_test_' + str(uuid.uuid4())[:8]))
        eid = cur.fetchone()[0]

        # Process
        cur.execute("SELECT * FROM lcs.fn_process_emissions(10)")
        rows = cur.fetchall()
        rejected = [r for r in rows if str(r[0]) == str(eid)]
        assert len(rejected) == 1
        assert rejected[0][1] == 'REJECTED'
        assert rejected[0][3] is not None, "error_id should be set"


# ---------------------------------------------------------------------------
# TEST 4: Deterministic error writes
# ---------------------------------------------------------------------------

class TestErrorWrites:

    def test_errors_have_correct_stage(self, cur):
        """All emission errors use emission_validation or emission_processing stage."""
        cur.execute("""
            SELECT DISTINCT error_stage FROM lcs.lcs_errors
            WHERE error_stage LIKE 'emission_%'
        """)
        stages = {r[0] for r in cur.fetchall()}
        valid_stages = {'emission_validation', 'emission_processing'}
        assert stages.issubset(valid_stages), f"Unexpected stages: {stages - valid_stages}"

    def test_error_payload_has_reason(self, cur):
        """All emission errors include a reason key in payload."""
        cur.execute("""
            SELECT count(*) FROM lcs.lcs_errors
            WHERE error_stage LIKE 'emission_%'
              AND NOT (error_payload ? 'reason')
        """)
        missing = cur.fetchone()[0]
        assert missing == 0, f"{missing} emission errors missing 'reason' in payload"


# ---------------------------------------------------------------------------
# TEST 5: Permission enforcement (lcs_emitter role)
# ---------------------------------------------------------------------------

class TestPermissions:

    def test_lcs_emitter_role_exists(self, cur):
        """lcs_emitter role exists in the database."""
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'lcs_emitter'")
        assert cur.fetchone() is not None, "lcs_emitter role should exist"

    def test_lcs_emitter_has_execute_grant(self, cur):
        """lcs_emitter has EXECUTE on fn_emit_movement."""
        cur.execute("""
            SELECT has_function_privilege('lcs_emitter',
                'lcs.fn_emit_movement(text, text, uuid, uuid, jsonb)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_lcs_emitter_no_insert_on_intake(self, cur):
        """lcs_emitter does NOT have INSERT on movement_emission_intake."""
        cur.execute("""
            SELECT has_table_privilege('lcs_emitter',
                'lcs.movement_emission_intake', 'INSERT')
        """)
        assert cur.fetchone()[0] is False

    def test_lcs_emitter_no_insert_on_cid_intake(self, cur):
        """lcs_emitter does NOT have INSERT on cid_intake."""
        cur.execute("""
            SELECT has_table_privilege('lcs_emitter',
                'lcs.cid_intake', 'INSERT')
        """)
        assert cur.fetchone()[0] is False


# ---------------------------------------------------------------------------
# TEST 6: Status transition enforcement
# ---------------------------------------------------------------------------

class TestStatusTransitions:

    def test_promoted_emission_is_immutable(self, cur):
        """Once PROMOTED, emission row cannot be updated."""
        cur.execute("""
            SELECT emission_id FROM lcs.movement_emission_intake
            WHERE status = 'PROMOTED' LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No PROMOTED emissions to test against")

        eid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="append-only"):
            cur.execute("""
                UPDATE lcs.movement_emission_intake SET status = 'STAGED'
                WHERE emission_id = %s
            """, (eid,))

    def test_delete_blocked(self, cur):
        """DELETE on movement_emission_intake is blocked."""
        cur.execute("""
            SELECT emission_id FROM lcs.movement_emission_intake LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No emissions to test against")

        eid = row[0]
        with pytest.raises(psycopg2.errors.RaiseException, match="append-only"):
            cur.execute("""
                DELETE FROM lcs.movement_emission_intake WHERE emission_id = %s
            """, (eid,))

    def test_staged_emission_can_be_updated(self, cur, real_fk_pair):
        """STAGED emission status can still transition (via process function)."""
        evidence = '{"test": "staged_update_' + str(uuid.uuid4())[:8] + '"}'
        cur.execute("""
            SELECT lcs.fn_emit_movement(
                'blog-content', 'FUNDING_EVENT', %s, %s, %s::jsonb
            )
        """, (real_fk_pair["outreach_id"], real_fk_pair["sovereign_id"], evidence))
        eid = cur.fetchone()[0]

        # Verify it's STAGED
        cur.execute("SELECT status FROM lcs.movement_emission_intake WHERE emission_id = %s", (eid,))
        assert cur.fetchone()[0] == 'STAGED'

        # Process it — should transition to PROMOTED
        cur.execute("SELECT * FROM lcs.fn_process_emissions(10)")
        rows = cur.fetchall()
        promoted = [r for r in rows if str(r[0]) == str(eid)]
        assert len(promoted) == 1
        assert promoted[0][1] == 'PROMOTED'
