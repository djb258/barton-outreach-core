"""
Tests for Phase 2F — Worker Orchestration Contract (DB-First)
==============================================================
Validates fn_worker_tick dispatcher, worker_run_log table, JSON contract,
batch dispatch paths, and lcs_worker least-privilege permissions.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_worker_orchestration_contract.py -v
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


# ---------------------------------------------------------------------------
# TEST 1: worker_run_log table structure
# ---------------------------------------------------------------------------

class TestWorkerRunLog:

    def test_table_exists(self, cur):
        """worker_run_log table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'worker_run_log'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """worker_run_log is registered in CTB as SUPPORTING."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'worker_run_log'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'SUPPORTING'

    def test_identity_columns_immutable(self, cur):
        """Identity columns (run_id, run_type, started_at) are immutable."""
        cur.execute("""
            INSERT INTO lcs.worker_run_log (run_type, status)
            VALUES ('PROMOTE_EMISSIONS', 'STARTED')
            RETURNING run_id
        """)
        run_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match="immutable"):
            cur.execute("""
                UPDATE lcs.worker_run_log SET run_type = 'FINALIZE_DISPATCH'
                WHERE run_id = %s
            """, (str(run_id),))

    def test_delete_blocked(self, cur):
        """DELETE on worker_run_log is blocked."""
        cur.execute("""
            INSERT INTO lcs.worker_run_log (run_type, status)
            VALUES ('PROMOTE_EMISSIONS', 'STARTED')
            RETURNING run_id
        """)
        run_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match="cannot be deleted"):
            cur.execute("DELETE FROM lcs.worker_run_log WHERE run_id = %s", (str(run_id),))

    def test_completion_update_allowed(self, cur):
        """Completion update (finished_at, status, counts) is allowed."""
        cur.execute("""
            INSERT INTO lcs.worker_run_log (run_type, status)
            VALUES ('PROMOTE_EMISSIONS', 'STARTED')
            RETURNING run_id
        """)
        run_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE lcs.worker_run_log
            SET finished_at = NOW(), status = 'SUCCESS',
                attempted_count = 10, success_count = 10, error_count = 0
            WHERE run_id = %s
        """, (str(run_id),))

        cur.execute("SELECT status, success_count FROM lcs.worker_run_log WHERE run_id = %s", (str(run_id),))
        row = cur.fetchone()
        assert row[0] == 'SUCCESS'
        assert row[1] == 10


# ---------------------------------------------------------------------------
# TEST 2: fn_worker_tick — JSON contract and dispatch
# ---------------------------------------------------------------------------

class TestWorkerTick:

    def test_returns_json_with_required_keys(self, cur):
        """fn_worker_tick returns JSON with all required keys."""
        cur.execute("SELECT lcs.fn_worker_tick('PROMOTE_EMISSIONS', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        required_keys = {'run_id', 'run_type', 'attempted', 'success', 'errors', 'status'}
        assert required_keys.issubset(set(result.keys())), f"Missing keys: {required_keys - set(result.keys())}"

    def test_promote_emissions_dispatch(self, cur):
        """PROMOTE_EMISSIONS dispatches to fn_promote_emission_batch."""
        cur.execute("SELECT lcs.fn_worker_tick('PROMOTE_EMISSIONS', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['run_type'] == 'PROMOTE_EMISSIONS'
        assert result['status'] in ('SUCCESS', 'PARTIAL', 'FAIL')
        assert isinstance(result['success'], int)
        assert isinstance(result['errors'], int)

    def test_finalize_dispatch_stub(self, cur):
        """FINALIZE_DISPATCH dispatches to stub (returns 0 success)."""
        cur.execute("SELECT lcs.fn_worker_tick('FINALIZE_DISPATCH', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['run_type'] == 'FINALIZE_DISPATCH'
        assert result['attempted'] == 0
        assert result['success'] == 0
        assert result['status'] == 'SUCCESS'

    def test_invalid_run_type_returns_fail(self, cur):
        """Invalid run_type returns FAIL without inserting run log."""
        cur.execute("SELECT lcs.fn_worker_tick('INVALID_TYPE', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['status'] == 'FAIL'
        assert result['run_id'] is None


# ---------------------------------------------------------------------------
# TEST 3: Run log recording
# ---------------------------------------------------------------------------

class TestRunLogRecording:

    def test_run_log_row_created(self, cur):
        """fn_worker_tick creates a run log row with correct status."""
        cur.execute("SELECT lcs.fn_worker_tick('PROMOTE_EMISSIONS', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        run_id = result['run_id']
        cur.execute("""
            SELECT run_type, status, finished_at, attempted_count, success_count, error_count
            FROM lcs.worker_run_log WHERE run_id = %s
        """, (run_id,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'PROMOTE_EMISSIONS'
        assert row[1] in ('SUCCESS', 'PARTIAL', 'FAIL')
        assert row[2] is not None  # finished_at should be set
        assert row[3] >= 0  # attempted_count
        assert row[4] >= 0  # success_count
        assert row[5] >= 0  # error_count

    def test_run_log_counts_match_json(self, cur):
        """Run log counts match the returned JSON payload."""
        cur.execute("SELECT lcs.fn_worker_tick('PROMOTE_EMISSIONS', 1)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        run_id = result['run_id']
        cur.execute("""
            SELECT attempted_count, success_count, error_count, status
            FROM lcs.worker_run_log WHERE run_id = %s
        """, (run_id,))
        row = cur.fetchone()
        assert row[0] == result['attempted']
        assert row[1] == result['success']
        assert row[2] == result['errors']
        assert row[3] == result['status']


# ---------------------------------------------------------------------------
# TEST 4: lcs_worker permissions
# ---------------------------------------------------------------------------

class TestWorkerPermissions:

    def test_lcs_worker_role_exists(self, cur):
        """lcs_worker role exists."""
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'lcs_worker'")
        assert cur.fetchone() is not None

    def test_lcs_worker_has_execute(self, cur):
        """lcs_worker has EXECUTE on fn_worker_tick."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_worker_tick(text, integer)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True
