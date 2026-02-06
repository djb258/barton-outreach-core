#!/usr/bin/env python3
"""
Guarded Database Connection — Schema Enforcement at Query Level

DOCTRINE: Each repo can ONLY touch its own schemas.
This module wraps psycopg2 connections to enforce schema access rules
on EVERY query before execution.

Usage:
    from src.sys.db.guarded_connection import get_guarded_connection, guarded_execute

    # Option 1: Get a guarded connection (validates all queries)
    conn = get_guarded_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM outreach.outreach")  # OK
        cur.execute("SELECT * FROM cl.company_identity")  # RAISES ForbiddenSchemaAccessError

    # Option 2: Use guarded_execute directly
    guarded_execute(cursor, "SELECT * FROM outreach.outreach", params)

    # Option 3: Wrap existing cursor
    guarded_cursor = GuardedCursor(cursor)
    guarded_cursor.execute("SELECT * FROM outreach.outreach")

FAIL HARD on all violations. No exceptions.
"""

import os
import logging
import functools
from typing import Any, Optional, Tuple, List, Union

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from ops.enforcement.schema_guard import (
    SchemaGuard,
    SchemaGuardError,
    ForbiddenSchemaAccessError,
    RepoContext,
    validate_query,
    get_guard,
)

logger = logging.getLogger(__name__)


# =============================================================================
# GUARDED CURSOR
# =============================================================================

class GuardedCursor:
    """
    Cursor wrapper that validates queries before execution.

    Wraps a psycopg2 cursor and intercepts execute/executemany calls
    to validate queries against schema access rules.
    """

    def __init__(self, cursor: psycopg2.extensions.cursor, guard: SchemaGuard = None):
        """
        Initialize guarded cursor.

        Args:
            cursor: The underlying psycopg2 cursor
            guard: SchemaGuard instance (uses global if None)
        """
        self._cursor = cursor
        self._guard = guard or get_guard()

    def execute(self, query: str, vars: Any = None) -> None:
        """
        Execute a query after schema validation.

        Args:
            query: SQL query string
            vars: Query parameters

        Raises:
            ForbiddenSchemaAccessError: If query accesses forbidden schema
        """
        # Validate query before execution
        self._guard.validate_query(query)

        # Log for audit trail
        logger.debug(f"[SCHEMA_GUARD] Query validated: {query[:100]}...")

        # Execute the query
        return self._cursor.execute(query, vars)

    def executemany(self, query: str, vars_list: List[Any]) -> None:
        """
        Execute a query with multiple parameter sets after validation.

        Args:
            query: SQL query string
            vars_list: List of parameter tuples

        Raises:
            ForbiddenSchemaAccessError: If query accesses forbidden schema
        """
        # Validate query before execution
        self._guard.validate_query(query)

        logger.debug(f"[SCHEMA_GUARD] Query validated (executemany): {query[:100]}...")

        return self._cursor.executemany(query, vars_list)

    def callproc(self, procname: str, parameters: Any = None) -> Any:
        """
        Call a stored procedure.

        Note: Stored procedures are allowed if they're in allowed schemas.
        We validate the schema prefix of the procedure name.
        """
        # Extract schema from procname (e.g., "outreach_ctx.log_tool_attempt")
        if '.' in procname:
            schema = procname.split('.')[0]
            # Create a dummy query to validate schema access
            dummy_query = f"SELECT * FROM {schema}.dummy"
            self._guard.validate_query(dummy_query)

        return self._cursor.callproc(procname, parameters)

    # Delegate all other methods to the underlying cursor
    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)

    def __iter__(self):
        return iter(self._cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()
        return False


# =============================================================================
# GUARDED CONNECTION
# =============================================================================

class GuardedConnection:
    """
    Connection wrapper that returns guarded cursors.

    All cursors created from this connection will validate queries
    against schema access rules before execution.
    """

    def __init__(self, connection: psycopg2.extensions.connection, guard: SchemaGuard = None):
        """
        Initialize guarded connection.

        Args:
            connection: The underlying psycopg2 connection
            guard: SchemaGuard instance (uses global if None)
        """
        self._connection = connection
        self._guard = guard or get_guard()

    def cursor(self, *args, **kwargs) -> GuardedCursor:
        """
        Create a guarded cursor.

        All arguments are passed to the underlying cursor() method.

        Returns:
            GuardedCursor that validates queries before execution
        """
        underlying_cursor = self._connection.cursor(*args, **kwargs)
        return GuardedCursor(underlying_cursor, self._guard)

    # Delegate all other methods to the underlying connection
    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._connection.rollback()
        self._connection.close()
        return False


# =============================================================================
# CONNECTION FACTORY
# =============================================================================

def get_guarded_connection(
    connection_string: str = None,
    repo_context: RepoContext = None
) -> GuardedConnection:
    """
    Get a guarded database connection.

    Args:
        connection_string: Neon connection string (reads from env if None)
        repo_context: Repository context for schema rules (defaults to OUTREACH)

    Returns:
        GuardedConnection that validates all queries

    Raises:
        ValueError: If connection string not available
        psycopg2.OperationalError: If connection fails
    """
    if connection_string is None:
        connection_string = os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("NEON_CONNECTION_STRING environment variable not set")

    # Create the guard
    guard = SchemaGuard(repo_context) if repo_context else get_guard()

    # Create the connection
    connection = psycopg2.connect(connection_string)

    # Wrap in guarded connection
    return GuardedConnection(connection, guard)


def get_guarded_dict_connection(
    connection_string: str = None,
    repo_context: RepoContext = None
) -> GuardedConnection:
    """
    Get a guarded connection that returns dict cursors by default.

    Convenience function for common use case.
    """
    conn = get_guarded_connection(connection_string, repo_context)
    # Override cursor to use RealDictCursor by default
    original_cursor = conn.cursor

    def dict_cursor(*args, **kwargs):
        if 'cursor_factory' not in kwargs:
            kwargs['cursor_factory'] = psycopg2.extras.RealDictCursor
        return original_cursor(*args, **kwargs)

    conn.cursor = dict_cursor
    return conn


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def guarded_execute(
    cursor: psycopg2.extensions.cursor,
    query: str,
    vars: Any = None,
    guard: SchemaGuard = None
) -> None:
    """
    Execute a query with schema validation.

    Use this to add validation to an existing cursor without wrapping it.

    Args:
        cursor: psycopg2 cursor
        query: SQL query string
        vars: Query parameters
        guard: SchemaGuard instance (uses global if None)

    Raises:
        ForbiddenSchemaAccessError: If query accesses forbidden schema
    """
    guard = guard or get_guard()
    guard.validate_query(query)
    return cursor.execute(query, vars)


def wrap_cursor(cursor: psycopg2.extensions.cursor, guard: SchemaGuard = None) -> GuardedCursor:
    """
    Wrap an existing cursor with schema validation.

    Args:
        cursor: psycopg2 cursor to wrap
        guard: SchemaGuard instance (uses global if None)

    Returns:
        GuardedCursor that validates queries
    """
    return GuardedCursor(cursor, guard or get_guard())


def wrap_connection(connection: psycopg2.extensions.connection, guard: SchemaGuard = None) -> GuardedConnection:
    """
    Wrap an existing connection with schema validation.

    Args:
        connection: psycopg2 connection to wrap
        guard: SchemaGuard instance (uses global if None)

    Returns:
        GuardedConnection that returns validated cursors
    """
    return GuardedConnection(connection, guard or get_guard())


# =============================================================================
# DECORATOR FOR EXISTING FUNCTIONS
# =============================================================================

def with_schema_guard(func):
    """
    Decorator to add schema validation to functions that execute SQL.

    The decorated function should have a 'query' or 'sql' parameter,
    or the first string argument will be treated as the query.

    Usage:
        @with_schema_guard
        def my_query_function(query, params=None):
            cursor.execute(query, params)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find the query parameter
        query = None

        if 'query' in kwargs:
            query = kwargs['query']
        elif 'sql' in kwargs:
            query = kwargs['sql']
        elif args:
            for arg in args:
                if isinstance(arg, str) and len(arg) > 10:
                    query = arg
                    break

        # Validate if found
        if query:
            validate_query(query)

        return func(*args, **kwargs)

    return wrapper


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "GuardedCursor",
    "GuardedConnection",
    # Factory functions
    "get_guarded_connection",
    "get_guarded_dict_connection",
    # Utility functions
    "guarded_execute",
    "wrap_cursor",
    "wrap_connection",
    # Decorator
    "with_schema_guard",
]
