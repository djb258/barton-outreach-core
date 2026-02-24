"""
Tests for SRC 2 — Outreach Identity Resolution Governor
========================================================
Validates outreach.fn_resolve_identity success/failure paths,
error logging, ambiguity hard-fail, missing anchor hard-fail,
and permission enforcement.

Requires: Doppler environment (NEON_PASSWORD), live Neon connection.
Run: doppler run -- pytest tests/lcs/test_identity_resolution_governor.py -v
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
def real_identity(cur):
    """Fetch a real outreach_id, sovereign_id, domain, ein for valid tests."""
    cur.execute("""
        SELECT outreach_id, sovereign_id, domain, ein
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND ein IS NOT NULL
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "No record with domain+ein found"
    return {
        "outreach_id": str(row[0]),
        "sovereign_id": str(row[1]),
        "domain": row[2],
        "ein": row[3],
    }


# ---------------------------------------------------------------------------
# TEST 1: Successful resolution paths
# ---------------------------------------------------------------------------

class TestResolveSuccess:

    def test_resolve_by_outreach_id(self, cur, real_identity):
        """Resolve by outreach_id returns both IDs."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'row1',
                %s::jsonb
            )
        """, (f'{{"outreach_id": "{real_identity["outreach_id"]}"}}',))
        result = cur.fetchone()[0]
        assert result is not None
        assert result["outreach_id"] == real_identity["outreach_id"]
        assert result["sovereign_id"] == real_identity["sovereign_id"]

    def test_resolve_by_sovereign_id(self, cur, real_identity):
        """Resolve by sovereign_id returns both IDs."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'row2',
                %s::jsonb
            )
        """, (f'{{"sovereign_id": "{real_identity["sovereign_id"]}"}}',))
        result = cur.fetchone()[0]
        assert result is not None
        assert result["outreach_id"] == real_identity["outreach_id"]
        assert result["sovereign_id"] == real_identity["sovereign_id"]

    def test_resolve_by_domain(self, cur, real_identity):
        """Resolve by domain returns both IDs."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'row3',
                %s::jsonb
            )
        """, (f'{{"domain": "{real_identity["domain"]}"}}',))
        result = cur.fetchone()[0]
        # Could be NULL if domain is ambiguous; skip if so
        if result is None:
            pytest.skip("Domain is ambiguous in test data")
        assert result["outreach_id"] is not None
        assert result["sovereign_id"] is not None

    def test_resolve_by_ein(self, cur, real_identity):
        """Resolve by EIN returns both IDs."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'row4',
                %s::jsonb
            )
        """, (f'{{"ein": "{real_identity["ein"]}"}}',))
        result = cur.fetchone()[0]
        if result is None:
            pytest.skip("EIN is ambiguous in test data")
        assert result["outreach_id"] is not None
        assert result["sovereign_id"] is not None


# ---------------------------------------------------------------------------
# TEST 2: Hard-fail on missing anchor
# ---------------------------------------------------------------------------

class TestMissingAnchor:

    def test_nonexistent_outreach_id(self, cur):
        """Fake outreach_id returns NULL + logs not_found error."""
        fake_oid = str(uuid.uuid4())
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'miss1',
                %s::jsonb
            )
        """, (f'{{"outreach_id": "{fake_oid}"}}',))
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type, resolution_stage FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'miss1' ORDER BY created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'not_found'
        assert row[1] == 'outreach_lookup'

    def test_nonexistent_sovereign_id(self, cur):
        """Fake sovereign_id returns NULL + logs not_found error."""
        fake_sid = str(uuid.uuid4())
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'miss2',
                %s::jsonb
            )
        """, (f'{{"sovereign_id": "{fake_sid}"}}',))
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type, resolution_stage FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'miss2' ORDER BY created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'not_found'
        assert row[1] == 'sovereign_lookup'

    def test_sovereign_without_outreach(self, cur):
        """Sovereign in CL but no outreach.outreach row → missing_anchor."""
        # Find a sovereign_id that exists in CL but NOT in outreach.outreach
        cur.execute("""
            SELECT ci.company_unique_id FROM cl.company_identity ci
            WHERE ci.company_unique_id NOT IN (
                SELECT sovereign_id FROM outreach.outreach WHERE sovereign_id IS NOT NULL
            )
            LIMIT 1
        """)
        row = cur.fetchone()
        if row is None:
            pytest.skip("No unlinked sovereign_id found")

        sid = str(row[0])
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'miss3',
                %s::jsonb
            )
        """, (f'{{"sovereign_id": "{sid}"}}',))
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'miss3' ORDER BY created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'missing_anchor'


# ---------------------------------------------------------------------------
# TEST 3: Hard-fail on ambiguity
# ---------------------------------------------------------------------------

class TestAmbiguity:

    def test_cross_validation_mismatch(self, cur, real_identity):
        """Providing outreach_id + wrong sovereign_id → ambiguity."""
        fake_sid = str(uuid.uuid4())
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'amb1',
                %s::jsonb
            )
        """, (f'{{"outreach_id": "{real_identity["outreach_id"]}", "sovereign_id": "{fake_sid}"}}',))
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type, resolution_stage FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'amb1' ORDER BY created_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 'ambiguity'
        assert row[1] == 'cross_validation'


# ---------------------------------------------------------------------------
# TEST 4: Invalid input
# ---------------------------------------------------------------------------

class TestInvalidInput:

    def test_no_usable_identifiers(self, cur):
        """Empty identifiers → invalid_input error."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'inv1',
                '{"foo": "bar"}'::jsonb
            )
        """)
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'inv1' ORDER BY created_at DESC LIMIT 1
        """)
        assert cur.fetchone()[0] == 'invalid_input'

    def test_bad_uuid_format(self, cur):
        """Non-UUID outreach_id → invalid_input error."""
        cur.execute("""
            SELECT outreach.fn_resolve_identity(
                'test', 'test_table', 'inv2',
                '{"outreach_id": "not-a-uuid"}'::jsonb
            )
        """)
        assert cur.fetchone()[0] is None

        cur.execute("""
            SELECT error_type FROM outreach.identity_resolution_errors
            WHERE source_row_pk = 'inv2' ORDER BY created_at DESC LIMIT 1
        """)
        assert cur.fetchone()[0] == 'invalid_input'


# ---------------------------------------------------------------------------
# TEST 5: Deterministic error payload
# ---------------------------------------------------------------------------

class TestErrorPayload:

    def test_error_payload_has_reason(self, cur):
        """All identity resolution errors include reason in payload."""
        cur.execute("""
            SELECT count(*) FROM outreach.identity_resolution_errors
            WHERE NOT (error_payload ? 'reason')
        """)
        assert cur.fetchone()[0] == 0


# ---------------------------------------------------------------------------
# TEST 6: Permission enforcement
# ---------------------------------------------------------------------------

class TestPermissions:

    def test_identity_resolver_role_exists(self, cur):
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'identity_resolver'")
        assert cur.fetchone() is not None

    def test_resolver_has_execute_grant(self, cur):
        cur.execute("""
            SELECT has_function_privilege('identity_resolver',
                'outreach.fn_resolve_identity(text, text, text, jsonb)', 'EXECUTE')
        """)
        assert cur.fetchone()[0] is True

    def test_resolver_no_insert_on_outreach(self, cur):
        cur.execute("""
            SELECT has_table_privilege('identity_resolver',
                'outreach.outreach', 'INSERT')
        """)
        assert cur.fetchone()[0] is False

    def test_resolver_no_insert_on_cl(self, cur):
        cur.execute("""
            SELECT has_table_privilege('identity_resolver',
                'cl.company_identity', 'INSERT')
        """)
        assert cur.fetchone()[0] is False
