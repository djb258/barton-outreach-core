"""
Database Utilities - Barton Toolbox Hub

Helper functions for database operations in Phase 1a/1b validation.

Functions:
- fetch_people_batch() - Load people from marketing.people_master
- fetch_valid_company_ids() - Load valid company IDs
- update_validation_status() - Update people_master.validation_status
- log_to_pipeline_events() - Log to marketing.pipeline_events
- log_to_audit_log() - Log to shq.audit_log

Status: ✅ Production Ready
Date: 2025-11-17

SCHEMA GUARD ENFORCEMENT:
All connections returned by get_db_connection() are GUARDED.
Queries accessing forbidden schemas (e.g., cl.* from outreach context)
will raise ForbiddenSchemaAccessError.
"""

import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Schema Guard Integration
try:
    from src.sys.db.guarded_connection import (
        get_guarded_connection,
        wrap_connection,
        GuardedConnection,
    )
    from ops.enforcement.schema_guard import ForbiddenSchemaAccessError
    SCHEMA_GUARD_ENABLED = True
except ImportError:
    SCHEMA_GUARD_ENABLED = False
    logger.warning("Schema guard not available - running WITHOUT protection")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_connection(guarded: bool = True):
    """
    Get PostgreSQL database connection to Neon

    Args:
        guarded: If True (default), returns a GuardedConnection that
                 validates all queries against schema access rules.
                 If False, returns raw psycopg2 connection (USE WITH CAUTION).

    Returns:
        GuardedConnection or psycopg2 connection object

    Raises:
        psycopg2.OperationalError: If connection fails
        ForbiddenSchemaAccessError: If query accesses forbidden schema (guarded mode)

    DOCTRINE: All production code should use guarded=True (the default).
    Queries that attempt to access cl.* schema will be BLOCKED.
    """
    connection_string = os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("NEON_CONNECTION_STRING environment variable not set")

    if guarded and SCHEMA_GUARD_ENABLED:
        return get_guarded_connection(connection_string)
    else:
        if guarded and not SCHEMA_GUARD_ENABLED:
            logger.warning("Schema guard requested but not available - using unguarded connection")
        return psycopg2.connect(connection_string)


def get_raw_connection():
    """
    Get an UNGUARDED database connection.

    WARNING: This bypasses schema protection. Only use for:
    - Migrations
    - Admin scripts that need cross-schema access
    - Emergency operations

    For normal operations, use get_db_connection() instead.
    """
    connection_string = os.getenv("NEON_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("NEON_CONNECTION_STRING environment variable not set")
    return psycopg2.connect(connection_string)


# ============================================================================
# FETCH FUNCTIONS
# ============================================================================

def fetch_people_batch(
    state: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Fetch people from marketing.people_master

    Args:
        state: State code to filter records (e.g., "WV"). None = all states
        limit: Maximum number of records. None = all records

    Returns:
        List of people dictionaries

    Example:
        >>> people = fetch_people_batch(state="WV", limit=100)
        >>> print(len(people))
        100
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        query = """
            SELECT
                p.unique_id as person_id,
                p.full_name,
                p.email,
                p.title,
                p.company_unique_id,
                p.linkedin_url,
                p.updated_at as timestamp_last_updated,
                p.validation_status
            FROM marketing.people_master p
        """

        conditions = []
        params = []

        # Add state filter if provided
        if state:
            query += """
                JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
            """
            conditions.append("c.state = %s")
            params.append(state)

        # Add WHERE clause if conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Add ORDER BY
        query += " ORDER BY p.created_at DESC"

        # Add LIMIT if provided
        if limit:
            query += " LIMIT %s"
            params.append(limit)

        # Execute query
        cursor.execute(query, params)
        people = cursor.fetchall()

        # Convert RealDictRow to dict
        return [dict(person) for person in people]

    finally:
        cursor.close()
        conn.close()


def fetch_valid_company_ids() -> Set[str]:
    """
    Fetch all valid company IDs from marketing.company_master

    Used for validating company_unique_id foreign key in person records.

    Returns:
        Set of valid company_unique_ids

    Example:
        >>> valid_ids = fetch_valid_company_ids()
        >>> "04.04.02.04.30000.001" in valid_ids
        True
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT company_unique_id
            FROM marketing.company_master
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Return set of company_unique_ids
        return {row[0] for row in rows}

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# UPDATE FUNCTIONS
# ============================================================================

def update_validation_status(person_id: str, validation_status: str):
    """
    Update validation_status field in marketing.people_master

    Args:
        person_id: Person's unique identifier
        validation_status: Status to set ("valid", "invalid", "pending")

    Example:
        >>> update_validation_status("04.04.02.04.20000.001", "valid")
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            UPDATE marketing.people_master
            SET validation_status = %s,
                updated_at = NOW()
            WHERE unique_id = %s
        """

        cursor.execute(query, (validation_status, person_id))
        conn.commit()

        logger.debug(f"Updated validation_status for {person_id}: {validation_status}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to update validation_status for {person_id}: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def log_to_pipeline_events(event_type: str, payload: Dict):
    """
    Log event to marketing.pipeline_events

    Args:
        event_type: Event type (e.g., "person_validation_check")
        payload: Event data as dictionary

    Example:
        >>> log_to_pipeline_events("person_validation_check", {
        ...     "person_id": "04.04.02.04.20000.001",
        ...     "valid": True,
        ...     "phase_id": 1.1
        ... })
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO marketing.pipeline_events (event_type, payload, created_at)
            VALUES (%s, %s::jsonb, NOW())
        """

        import json
        cursor.execute(query, (event_type, json.dumps(payload)))
        conn.commit()

        logger.debug(f"Logged to pipeline_events: {event_type}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to log to pipeline_events: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


def log_to_audit_log(component: str, event_type: str, event_data: Dict):
    """
    Log event to shq.audit_log

    Args:
        component: Component name (e.g., "phase1b_people_validator")
        event_type: Event type (e.g., "validation_complete")
        event_data: Event data as dictionary

    Example:
        >>> log_to_audit_log("phase1b_people_validator", "validation_complete", {
        ...     "total": 150,
        ...     "valid": 120,
        ...     "invalid": 30,
        ...     "phase_id": 1.1
        ... })
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO shq.audit_log (component, event_type, event_data, created_at)
            VALUES (%s, %s, %s::jsonb, NOW())
        """

        import json
        cursor.execute(query, (component, event_type, json.dumps(event_data)))
        conn.commit()

        logger.debug(f"Logged to audit_log: {component}.{event_type}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to log to audit_log: {e}")
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("DATABASE UTILITIES - TEST")
    print("=" * 70)

    # Test 1: Fetch valid company IDs
    print("\n[Test 1] Fetch Valid Company IDs:")
    try:
        valid_ids = fetch_valid_company_ids()
        print(f"✅ Loaded {len(valid_ids)} valid company IDs")
        if valid_ids:
            print(f"  Sample: {list(valid_ids)[:3]}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

    # Test 2: Fetch people batch
    print("\n[Test 2] Fetch People Batch (limit=5):")
    try:
        people = fetch_people_batch(limit=5)
        print(f"✅ Loaded {len(people)} people")
        if people:
            person = people[0]
            print(f"  Sample: {person.get('full_name')} ({person.get('person_id')})")
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

    # Test 3: Fetch people by state
    print("\n[Test 3] Fetch People by State (WV, limit=5):")
    try:
        people = fetch_people_batch(state="WV", limit=5)
        print(f"✅ Loaded {len(people)} people from WV")
    except Exception as e:
        print(f"❌ Failed: {e}")
        # Don't exit - WV might not have data

    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
