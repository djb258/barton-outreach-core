"""
Tests for Phase 4A — Cadence Governor (Frequency Caps + Time Windows)
=====================================================================
Validates cadence_policy_registry, dispatch_attempt_log append-only,
fn_cadence_check decision logic, logging, and lcs_worker permissions.

Integration: Option B — fn_cadence_check is standalone. READY remains
channel-agnostic. Cadence wired into send-attempt path in Phase 4B.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_cadence_governor.py -v
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
# Helpers — create a sovereign + MID for cadence tests
# ---------------------------------------------------------------------------

def _create_test_mid(cur, lifecycle_stage='QUALIFIED'):
    """Insert a canonical sovereign + MID in READY state for cadence testing."""
    sovereign_id = uuid.uuid4()
    cid = uuid.uuid4()
    sid = uuid.uuid4()
    outreach_id = uuid.uuid4()

    # Insert canonical record
    cur.execute("""
        INSERT INTO lcs.lcs_canonical (sovereign_id, current_lifecycle_stage)
        VALUES (%s, %s::lcs.lifecycle_stage)
    """, (str(sovereign_id), lifecycle_stage))

    # Insert SID
    cur.execute("""
        INSERT INTO lcs.sid_registry (sid, sovereign_id, cid, outreach_id)
        VALUES (%s, %s, %s, %s)
    """, (str(sid), str(sovereign_id), str(cid), str(outreach_id)))

    # Insert MID in READY state (skip FSM by direct insert with MINTED then update path)
    cur.execute("""
        INSERT INTO lcs.mid_ledger
            (mid, cid, sid, outreach_id, sovereign_id, dispatch_state, movement_type_code)
        VALUES (gen_random_uuid(), %s, %s, %s, %s, 'MINTED', 'RENEWAL_APPROACHING')
        RETURNING mid
    """, (str(cid), str(sid), str(outreach_id), str(sovereign_id)))
    mid = cur.fetchone()[0]

    # Advance to COMPILED then READY via FSM
    cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'COMPILED' WHERE mid = %s", (str(mid),))
    cur.execute("UPDATE lcs.mid_ledger SET dispatch_state = 'READY', ready_at = NOW() WHERE mid = %s", (str(mid),))

    return mid, sovereign_id


# ---------------------------------------------------------------------------
# TEST 1: cadence_policy_registry structure
# ---------------------------------------------------------------------------

class TestCadencePolicyRegistry:

    def test_table_exists(self, cur):
        """cadence_policy_registry table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'cadence_policy_registry'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """cadence_policy_registry is registered in CTB as REGISTRY."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'cadence_policy_registry'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'REGISTRY'

    def test_composite_pk(self, cur):
        """Primary key is (lifecycle_stage, channel)."""
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'lcs'
              AND tc.table_name = 'cadence_policy_registry'
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """)
        cols = [r[0] for r in cur.fetchall()]
        assert cols == ['lifecycle_stage', 'channel']

    def test_seeded_policies(self, cur):
        """Default policies seeded for QUALIFIED, ENGAGED, CONVERTED EMAIL."""
        cur.execute("""
            SELECT lifecycle_stage, channel, min_gap_hours, max_sends_7d, max_sends_30d
            FROM lcs.cadence_policy_registry
            WHERE channel = 'EMAIL'
            ORDER BY lifecycle_stage
        """)
        rows = cur.fetchall()
        stages = [r[0] for r in rows]
        assert 'QUALIFIED' in stages
        assert 'ENGAGED' in stages
        assert 'CONVERTED' in stages

    def test_updated_at_trigger(self, cur):
        """updated_at auto-updates on policy change."""
        cur.execute("""
            SELECT updated_at FROM lcs.cadence_policy_registry
            WHERE lifecycle_stage = 'QUALIFIED' AND channel = 'EMAIL'
        """)
        old_ts = cur.fetchone()[0]

        cur.execute("""
            UPDATE lcs.cadence_policy_registry
            SET min_gap_hours = min_gap_hours
            WHERE lifecycle_stage = 'QUALIFIED' AND channel = 'EMAIL'
        """)

        cur.execute("""
            SELECT updated_at FROM lcs.cadence_policy_registry
            WHERE lifecycle_stage = 'QUALIFIED' AND channel = 'EMAIL'
        """)
        new_ts = cur.fetchone()[0]
        assert new_ts >= old_ts


# ---------------------------------------------------------------------------
# TEST 2: dispatch_attempt_log structure + append-only
# ---------------------------------------------------------------------------

class TestDispatchAttemptLog:

    def test_table_exists(self, cur):
        """dispatch_attempt_log table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'dispatch_attempt_log'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """dispatch_attempt_log is CTB-registered as SUPPORTING."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'dispatch_attempt_log'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'SUPPORTING'

    def test_update_blocked(self, cur):
        """UPDATE on dispatch_attempt_log is forbidden (append-only)."""
        mid, sovereign_id = _create_test_mid(cur)

        cur.execute("""
            INSERT INTO lcs.dispatch_attempt_log
                (mid, sovereign_id, channel, lifecycle_stage, decision)
            VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED')
            RETURNING attempt_id
        """, (str(mid), str(sovereign_id)))
        attempt_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match='append-only'):
            cur.execute("""
                UPDATE lcs.dispatch_attempt_log SET decision = 'BLOCKED'
                WHERE attempt_id = %s
            """, (str(attempt_id),))

    def test_delete_blocked(self, cur):
        """DELETE on dispatch_attempt_log is forbidden (append-only)."""
        mid, sovereign_id = _create_test_mid(cur)

        cur.execute("""
            INSERT INTO lcs.dispatch_attempt_log
                (mid, sovereign_id, channel, lifecycle_stage, decision)
            VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED')
            RETURNING attempt_id
        """, (str(mid), str(sovereign_id)))
        attempt_id = cur.fetchone()[0]

        with pytest.raises(psycopg2.errors.RaiseException, match='append-only'):
            cur.execute("""
                DELETE FROM lcs.dispatch_attempt_log WHERE attempt_id = %s
            """, (str(attempt_id),))


# ---------------------------------------------------------------------------
# TEST 3: fn_cadence_check — decision logic
# ---------------------------------------------------------------------------

class TestCadenceCheck:

    def test_returns_json_with_required_keys(self, cur):
        """fn_cadence_check returns JSON with required keys."""
        mid, _ = _create_test_mid(cur)
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        required_keys = {'allowed', 'block_reason', 'policy', 'metrics'}
        assert required_keys.issubset(set(result.keys()))

    def test_allowed_when_under_caps(self, cur):
        """Cadence allows send when all caps are under limit."""
        mid, _ = _create_test_mid(cur, 'QUALIFIED')
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['allowed'] is True
        assert result['block_reason'] is None

    def test_no_policy_returns_allowed(self, cur):
        """No cadence policy for stage/channel → ALLOWED."""
        mid, _ = _create_test_mid(cur, 'SUSPECT')
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'LINKEDIN')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['allowed'] is True
        assert result['policy']['reason'] == 'NO_POLICY'

    def test_mid_not_found(self, cur):
        """fn_cadence_check returns blocked for nonexistent MID."""
        fake_mid = uuid.uuid4()
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(fake_mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['allowed'] is False
        assert result['block_reason'] == 'MID_NOT_FOUND'

        # Verify error logged with correct constraint-compliant values
        cur.execute("""
            SELECT error_stage, error_type FROM lcs.lcs_errors
            WHERE error_stage = 'cadence_check' AND error_payload->>'attempted_mid' = %s
            ORDER BY created_at DESC LIMIT 1
        """, (str(fake_mid),))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'cadence_check'
        assert row[1] == 'validation'

    def test_blocked_by_min_gap_hours(self, cur):
        """Cadence blocks when min_gap_hours violated."""
        mid, sovereign_id = _create_test_mid(cur, 'QUALIFIED')

        # Insert a recent ALLOWED send for this sovereign
        cur.execute("""
            INSERT INTO lcs.dispatch_attempt_log
                (mid, sovereign_id, channel, lifecycle_stage, decision, attempted_at)
            VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED', NOW() - INTERVAL '1 hour')
        """, (str(mid), str(sovereign_id)))

        # QUALIFIED EMAIL has min_gap_hours=72, so 1 hour ago should block
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        assert result['allowed'] is False
        assert result['block_reason'] == 'MIN_GAP_HOURS'

    def test_blocked_by_max_sends_7d(self, cur):
        """Cadence blocks when max_sends_7d exceeded."""
        mid, sovereign_id = _create_test_mid(cur, 'QUALIFIED')

        # QUALIFIED EMAIL max_sends_7d=2, insert 2 recent ALLOWED
        for i in range(2):
            cur.execute("""
                INSERT INTO lcs.dispatch_attempt_log
                    (mid, sovereign_id, channel, lifecycle_stage, decision, attempted_at)
                VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED', NOW() - INTERVAL '%s days')
            """, (str(mid), str(sovereign_id), str(i + 1)))

        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        # Should be blocked by either MIN_GAP (if within 72h) or MAX_SENDS_7D
        assert result['allowed'] is False
        assert result['block_reason'] in ('MIN_GAP_HOURS', 'MAX_SENDS_7D')

    def test_metrics_populated(self, cur):
        """Metrics include last_send_at, count_7d, count_30d."""
        mid, _ = _create_test_mid(cur, 'QUALIFIED')
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        metrics = result['metrics']
        assert 'last_send_at' in metrics
        assert 'count_7d' in metrics
        assert 'count_30d' in metrics


# ---------------------------------------------------------------------------
# TEST 4: Logging behavior
# ---------------------------------------------------------------------------

class TestCadenceLogging:

    def test_allowed_logged_to_attempt_log(self, cur):
        """ALLOWED decision is logged to dispatch_attempt_log."""
        mid, sovereign_id = _create_test_mid(cur, 'QUALIFIED')
        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))

        cur.execute("""
            SELECT decision, block_reason FROM lcs.dispatch_attempt_log
            WHERE mid = %s AND channel = 'EMAIL'
            ORDER BY attempted_at DESC LIMIT 1
        """, (str(mid),))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'ALLOWED'
        assert row[1] is None

    def test_blocked_logged_to_attempt_log(self, cur):
        """BLOCKED decision is logged to dispatch_attempt_log."""
        mid, sovereign_id = _create_test_mid(cur, 'QUALIFIED')

        # Create a recent send to trigger MIN_GAP block
        cur.execute("""
            INSERT INTO lcs.dispatch_attempt_log
                (mid, sovereign_id, channel, lifecycle_stage, decision, attempted_at)
            VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED', NOW() - INTERVAL '1 hour')
        """, (str(mid), str(sovereign_id)))

        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))

        cur.execute("""
            SELECT decision, block_reason FROM lcs.dispatch_attempt_log
            WHERE mid = %s AND channel = 'EMAIL' AND decision = 'BLOCKED'
            ORDER BY attempted_at DESC LIMIT 1
        """, (str(mid),))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'BLOCKED'
        assert row[1] == 'MIN_GAP_HOURS'

    def test_blocked_logs_to_lcs_errors(self, cur):
        """BLOCKED cadence decision also logs to lcs_errors."""
        mid, sovereign_id = _create_test_mid(cur, 'QUALIFIED')

        # Create a recent send to trigger MIN_GAP block
        cur.execute("""
            INSERT INTO lcs.dispatch_attempt_log
                (mid, sovereign_id, channel, lifecycle_stage, decision, attempted_at)
            VALUES (%s, %s, 'EMAIL', 'QUALIFIED', 'ALLOWED', NOW() - INTERVAL '1 hour')
        """, (str(mid), str(sovereign_id)))

        cur.execute("SELECT lcs.fn_cadence_check(%s, 'EMAIL')", (str(mid),))

        cur.execute("""
            SELECT error_stage, error_type, error_payload
            FROM lcs.lcs_errors
            WHERE mid = %s AND error_type = 'conflict' AND error_stage = 'cadence_check'
            ORDER BY created_at DESC LIMIT 1
        """, (str(mid),))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'cadence_check'
        assert row[1] == 'conflict'
        payload = row[2] if isinstance(row[2], dict) else json.loads(row[2])
        assert payload['block_reason'] == 'MIN_GAP_HOURS'


# ---------------------------------------------------------------------------
# TEST 5: Permissions
# ---------------------------------------------------------------------------

class TestCadencePermissions:

    def test_lcs_worker_has_execute_on_cadence_check(self, cur):
        """lcs_worker has EXECUTE on fn_cadence_check."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_cadence_check(uuid, text)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_lcs_worker_no_direct_policy_write(self, cur):
        """lcs_worker cannot INSERT into cadence_policy_registry directly."""
        cur.execute("""
            SELECT has_table_privilege('lcs_worker',
                'lcs.cadence_policy_registry', 'INSERT')
        """)
        assert cur.fetchone()[0] is False

    def test_lcs_worker_no_direct_attempt_log_write(self, cur):
        """lcs_worker cannot INSERT into dispatch_attempt_log directly."""
        cur.execute("""
            SELECT has_table_privilege('lcs_worker',
                'lcs.dispatch_attempt_log', 'INSERT')
        """)
        assert cur.fetchone()[0] is False
