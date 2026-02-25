"""
Tests for Phase 3D — Retry + Dead-Letter Governor (Deterministic)
=================================================================
Validates retry_queue table, fn_enqueue_retry idempotency,
fn_process_retry_batch routing/escalation/dead-letter, v_dead_letter_queue,
and lcs_worker permissions.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_retry_dead_letter_governor.py -v
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
# TEST 1: retry_queue table structure
# ---------------------------------------------------------------------------

class TestRetryQueue:

    def test_table_exists(self, cur):
        """retry_queue table exists in lcs schema."""
        cur.execute("""
            SELECT count(*) FROM information_schema.tables
            WHERE table_schema = 'lcs' AND table_name = 'retry_queue'
        """)
        assert cur.fetchone()[0] == 1

    def test_ctb_registered(self, cur):
        """retry_queue is registered in CTB as SUPPORTING."""
        cur.execute("""
            SELECT leaf_type FROM ctb.table_registry
            WHERE table_schema = 'lcs' AND table_name = 'retry_queue'
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'SUPPORTING'

    def test_unique_active_constraint(self, cur):
        """Partial unique index enforces one active retry per entity."""
        entity_id = uuid.uuid4()

        # First enqueue succeeds
        cur.execute("""
            INSERT INTO lcs.retry_queue (entity_type, entity_id, retry_strategy, status)
            VALUES ('EMISSION', %s, 'IMMEDIATE', 'PENDING')
        """, (str(entity_id),))

        # Second PENDING for same entity fails
        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute("""
                INSERT INTO lcs.retry_queue (entity_type, entity_id, retry_strategy, status)
                VALUES ('EMISSION', %s, 'IMMEDIATE', 'PENDING')
            """, (str(entity_id),))

    def test_lcs_errors_retry_fields_exist(self, cur):
        """lcs_errors has is_retryable and retry_strategy columns."""
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'lcs' AND table_name = 'lcs_errors'
              AND column_name IN ('is_retryable', 'retry_strategy')
            ORDER BY column_name
        """)
        cols = [r[0] for r in cur.fetchall()]
        assert 'is_retryable' in cols
        assert 'retry_strategy' in cols


# ---------------------------------------------------------------------------
# TEST 2: fn_enqueue_retry — idempotent enqueue
# ---------------------------------------------------------------------------

class TestEnqueueRetry:

    def test_returns_retry_id(self, cur):
        """fn_enqueue_retry returns a valid retry_id."""
        entity_id = uuid.uuid4()
        cur.execute("""
            SELECT lcs.fn_enqueue_retry('EMISSION', %s, NULL, 'IMMEDIATE', 5)
        """, (str(entity_id),))
        retry_id = cur.fetchone()[0]
        assert retry_id is not None

        # Verify row exists
        cur.execute("SELECT status FROM lcs.retry_queue WHERE retry_id = %s", (str(retry_id),))
        assert cur.fetchone()[0] == 'PENDING'

    def test_idempotent_returns_same_id(self, cur):
        """Second enqueue for same active entity returns same retry_id."""
        entity_id = uuid.uuid4()

        cur.execute("SELECT lcs.fn_enqueue_retry('MID', %s, NULL, 'BACKOFF_5M', 3)", (str(entity_id),))
        retry_id_1 = cur.fetchone()[0]

        cur.execute("SELECT lcs.fn_enqueue_retry('MID', %s, NULL, 'BACKOFF_1H', 5)", (str(entity_id),))
        retry_id_2 = cur.fetchone()[0]

        assert retry_id_1 == retry_id_2

    def test_immediate_strategy_next_attempt(self, cur):
        """IMMEDIATE strategy sets next_attempt_at close to now()."""
        entity_id = uuid.uuid4()
        cur.execute("SELECT lcs.fn_enqueue_retry('EMISSION', %s, NULL, 'IMMEDIATE', 5)", (str(entity_id),))
        retry_id = cur.fetchone()[0]

        cur.execute("""
            SELECT next_attempt_at, created_at FROM lcs.retry_queue WHERE retry_id = %s
        """, (str(retry_id),))
        row = cur.fetchone()
        # IMMEDIATE: next_attempt_at should be essentially now (within a few seconds of created_at)
        diff = abs((row[0] - row[1]).total_seconds())
        assert diff < 5

    def test_backoff_5m_strategy_next_attempt(self, cur):
        """BACKOFF_5M strategy sets next_attempt_at ~5 minutes from now."""
        entity_id = uuid.uuid4()
        cur.execute("SELECT lcs.fn_enqueue_retry('EMISSION', %s, NULL, 'BACKOFF_5M', 5)", (str(entity_id),))
        retry_id = cur.fetchone()[0]

        cur.execute("""
            SELECT EXTRACT(EPOCH FROM (next_attempt_at - created_at)) FROM lcs.retry_queue WHERE retry_id = %s
        """, (str(retry_id),))
        diff_seconds = cur.fetchone()[0]
        # Should be approximately 300 seconds (5 minutes)
        assert 295 < diff_seconds < 310


# ---------------------------------------------------------------------------
# TEST 3: fn_process_retry_batch — routing and dead-letter
# ---------------------------------------------------------------------------

class TestProcessRetryBatch:

    def test_returns_json_with_required_keys(self, cur):
        """fn_process_retry_batch returns JSON with required keys."""
        cur.execute("SELECT lcs.fn_process_retry_batch(10)")
        result = cur.fetchone()[0]
        if isinstance(result, str):
            result = json.loads(result)

        required_keys = {'attempted', 'succeeded', 'dead', 'remaining_pending'}
        assert required_keys.issubset(set(result.keys()))

    def test_dead_at_max_attempts(self, cur):
        """Item goes DEAD when attempt_count reaches max_attempts."""
        entity_id = uuid.uuid4()

        # Insert a retry item at attempt 4 of 5, PENDING, next_attempt_at in the past
        cur.execute("""
            INSERT INTO lcs.retry_queue
                (entity_type, entity_id, retry_strategy, attempt_count, max_attempts,
                 next_attempt_at, status)
            VALUES ('EMISSION', %s, 'BACKOFF_1D', 4, 5, NOW() - INTERVAL '1 minute', 'PENDING')
            RETURNING retry_id
        """, (str(entity_id),))
        retry_id = cur.fetchone()[0]

        # Process — this will be attempt 5 of 5. fn_promote_emission will fail
        # (no real emission exists), so it won't succeed → DEAD
        cur.execute("SELECT lcs.fn_process_retry_batch(1)")

        cur.execute("SELECT status, attempt_count FROM lcs.retry_queue WHERE retry_id = %s",
                    (str(retry_id),))
        row = cur.fetchone()
        assert row[0] == 'DEAD'
        assert row[1] == 5

    def test_strategy_escalation_on_failure(self, cur):
        """Failed retry escalates strategy from IMMEDIATE to BACKOFF_5M."""
        entity_id = uuid.uuid4()

        # Insert an IMMEDIATE retry, attempt 0 of 5, eligible now
        cur.execute("""
            INSERT INTO lcs.retry_queue
                (entity_type, entity_id, retry_strategy, attempt_count, max_attempts,
                 next_attempt_at, status)
            VALUES ('EMISSION', %s, 'IMMEDIATE', 0, 5, NOW() - INTERVAL '1 minute', 'PENDING')
            RETURNING retry_id
        """, (str(entity_id),))
        retry_id = cur.fetchone()[0]

        # Process — no real emission, so it fails. Should escalate to BACKOFF_5M
        cur.execute("SELECT lcs.fn_process_retry_batch(1)")

        cur.execute("""
            SELECT status, retry_strategy, attempt_count
            FROM lcs.retry_queue WHERE retry_id = %s
        """, (str(retry_id),))
        row = cur.fetchone()
        assert row[0] == 'PENDING'  # Returned to PENDING
        assert row[1] == 'BACKOFF_5M'  # Escalated
        assert row[2] == 1  # attempt_count incremented


# ---------------------------------------------------------------------------
# TEST 4: v_dead_letter_queue view
# ---------------------------------------------------------------------------

class TestDeadLetterQueue:

    def test_view_exists(self, cur):
        """v_dead_letter_queue view exists."""
        cur.execute("""
            SELECT count(*) FROM information_schema.views
            WHERE table_schema = 'lcs' AND table_name = 'v_dead_letter_queue'
        """)
        assert cur.fetchone()[0] == 1

    def test_shows_dead_items_with_error_context(self, cur):
        """v_dead_letter_queue shows DEAD items joined with error context."""
        # Insert a test error using correct lcs_errors columns
        cur.execute("""
            INSERT INTO lcs.lcs_errors (error_stage, error_type, error_payload, is_retryable)
            VALUES ('test_retry', 'VALIDATION',
                    '{"message": "test error for dead letter"}'::jsonb, TRUE)
            RETURNING error_id
        """)
        error_id = cur.fetchone()[0]

        entity_id = uuid.uuid4()
        # Insert a DEAD retry item linked to the error
        cur.execute("""
            INSERT INTO lcs.retry_queue
                (entity_type, entity_id, error_id, retry_strategy, attempt_count,
                 max_attempts, status)
            VALUES ('EMISSION', %s, %s, 'BACKOFF_1D', 5, 5, 'DEAD')
        """, (str(entity_id), str(error_id)))

        # Query the view — columns are error_stage, error_type, error_context
        cur.execute("""
            SELECT entity_id, error_stage, error_type, error_context
            FROM lcs.v_dead_letter_queue
            WHERE entity_id = %s
        """, (str(entity_id),))
        row = cur.fetchone()
        assert row is not None
        assert str(row[0]) == str(entity_id)
        assert row[1] == 'test_retry'
        assert row[2] == 'VALIDATION'
        # error_context is jsonb (aliased from error_payload)
        context = row[3] if isinstance(row[3], dict) else json.loads(row[3])
        assert 'dead letter' in context['message']


# ---------------------------------------------------------------------------
# TEST 5: Permissions
# ---------------------------------------------------------------------------

class TestRetryPermissions:

    def test_lcs_worker_has_execute_on_enqueue(self, cur):
        """lcs_worker has EXECUTE on fn_enqueue_retry."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_enqueue_retry(text, uuid, uuid, text, integer)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_lcs_worker_has_execute_on_process_batch(self, cur):
        """lcs_worker has EXECUTE on fn_process_retry_batch."""
        cur.execute("""
            SELECT has_function_privilege('lcs_worker',
                'lcs.fn_process_retry_batch(integer)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True
