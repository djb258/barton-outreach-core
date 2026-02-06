#!/usr/bin/env python3
"""
Schema Guard — Cross-Repo Table Access Prevention

DOCTRINE: Each repo can ONLY touch its own schemas.
- Outreach repo: outreach.*, people.*, shq.* (NOT cl.*)
- CL repo: cl.* (NOT outreach.*, people.*)
- Sales repo: sales.* (NOT outreach.*, cl.*)
- Client repo: client.* (NOT outreach.*, cl.*, sales.*)

This prevents cleanup/migration logic in one repo from making
decisions based on another repo's tables.

FAIL HARD on all violations. No exceptions.
"""

import re
import os
import functools
from enum import Enum
from typing import Set, List, Optional, Callable, Any
from dataclasses import dataclass


# =============================================================================
# CONFIGURATION
# =============================================================================

class RepoContext(Enum):
    """Repository context identifiers."""
    OUTREACH = "outreach"
    CL = "cl"
    SALES = "sales"
    CLIENT = "client"
    UNKNOWN = "unknown"


# Schema access rules: repo -> allowed schemas
SCHEMA_ACCESS_RULES = {
    RepoContext.OUTREACH: {
        "allowed": {"outreach", "people", "shq", "intake", "bit", "marketing", "public"},
        "forbidden": {"cl", "sales", "client"},
        "read_only": set(),  # Schemas that can be read but not written
    },
    RepoContext.CL: {
        "allowed": {"cl", "shq", "public"},
        "forbidden": {"outreach", "people", "sales", "client", "intake", "bit", "marketing"},
        "read_only": set(),
    },
    RepoContext.SALES: {
        "allowed": {"sales", "shq", "public"},
        "forbidden": {"outreach", "people", "cl", "client", "intake", "bit", "marketing"},
        "read_only": set(),
    },
    RepoContext.CLIENT: {
        "allowed": {"client", "shq", "public"},
        "forbidden": {"outreach", "people", "cl", "sales", "intake", "bit", "marketing"},
        "read_only": set(),
    },
}

# Environment variable to set repo context
REPO_CONTEXT_ENV_VAR = "BARTON_REPO_CONTEXT"

# Default context if not set (for this repo)
DEFAULT_REPO_CONTEXT = RepoContext.OUTREACH


# =============================================================================
# EXCEPTIONS
# =============================================================================

class SchemaGuardError(Exception):
    """Base exception for schema guard violations."""

    def __init__(self, message: str, repo_context: str, forbidden_schema: str, query_snippet: str = ""):
        self.repo_context = repo_context
        self.forbidden_schema = forbidden_schema
        self.query_snippet = query_snippet[:200] if query_snippet else ""
        super().__init__(message)


class ForbiddenSchemaAccessError(SchemaGuardError):
    """Raised when a query attempts to access a forbidden schema."""
    pass


class ReadOnlySchemaWriteError(SchemaGuardError):
    """Raised when a query attempts to write to a read-only schema."""
    pass


# =============================================================================
# QUERY PARSER
# =============================================================================

@dataclass
class QueryAnalysis:
    """Result of analyzing a SQL query."""
    schemas_referenced: Set[str]
    tables_referenced: Set[str]
    is_write_operation: bool
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP


class QueryParser:
    """
    Parses SQL queries to extract schema and table references.

    NOTE: This is a best-effort parser for common SQL patterns.
    It may not catch all edge cases but covers the vast majority
    of queries used in this codebase.
    """

    # Patterns for detecting schema.table references
    SCHEMA_TABLE_PATTERN = re.compile(
        r'\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b',
        re.IGNORECASE
    )

    # Patterns for detecting operation type
    WRITE_OPERATIONS = {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE'}
    READ_OPERATIONS = {'SELECT', 'WITH'}

    # Keywords that are NOT schema names (to filter false positives)
    SQL_KEYWORDS = {
        'information_schema', 'pg_catalog', 'pg_temp', 'pg_toast',
        'public',  # public is always allowed
    }

    @classmethod
    def analyze(cls, query: str) -> QueryAnalysis:
        """
        Analyze a SQL query and extract schema/table references.

        Args:
            query: The SQL query string

        Returns:
            QueryAnalysis with extracted information
        """
        # Normalize query
        query_upper = query.upper().strip()
        query_clean = cls._remove_comments(query)

        # Detect operation type
        operation_type = cls._detect_operation_type(query_upper)
        is_write = operation_type in cls.WRITE_OPERATIONS

        # Extract schema.table references
        schemas = set()
        tables = set()

        for match in cls.SCHEMA_TABLE_PATTERN.finditer(query_clean):
            schema = match.group(1).lower()
            table = match.group(2).lower()

            # Filter out system schemas and keywords
            if schema not in cls.SQL_KEYWORDS:
                schemas.add(schema)
                tables.add(f"{schema}.{table}")

        return QueryAnalysis(
            schemas_referenced=schemas,
            tables_referenced=tables,
            is_write_operation=is_write,
            operation_type=operation_type,
        )

    @classmethod
    def _detect_operation_type(cls, query_upper: str) -> str:
        """Detect the primary operation type of a query."""
        # Check for CTEs first
        if query_upper.startswith('WITH'):
            # Look for the main operation after the CTE
            cte_end = query_upper.rfind(')')
            if cte_end > 0:
                remainder = query_upper[cte_end:].strip()
                for op in list(cls.WRITE_OPERATIONS) + list(cls.READ_OPERATIONS):
                    if op in remainder:
                        return op
            return 'SELECT'  # Default for CTEs

        # Check for each operation type
        for op in list(cls.WRITE_OPERATIONS) + list(cls.READ_OPERATIONS):
            if query_upper.startswith(op) or f' {op} ' in query_upper:
                return op

        return 'UNKNOWN'

    @classmethod
    def _remove_comments(cls, query: str) -> str:
        """Remove SQL comments from query."""
        # Remove single-line comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        # Remove multi-line comments
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        return query


# =============================================================================
# SCHEMA GUARD
# =============================================================================

class SchemaGuard:
    """
    Validates SQL queries against schema access rules.

    Usage:
        guard = SchemaGuard(RepoContext.OUTREACH)
        guard.validate_query("SELECT * FROM cl.company_identity")  # Raises!
        guard.validate_query("SELECT * FROM outreach.outreach")  # OK
    """

    def __init__(self, repo_context: Optional[RepoContext] = None):
        """
        Initialize schema guard.

        Args:
            repo_context: The repository context. If None, reads from
                         BARTON_REPO_CONTEXT env var or uses default.
        """
        if repo_context is None:
            repo_context = self._get_context_from_env()

        self.repo_context = repo_context
        self.rules = SCHEMA_ACCESS_RULES.get(repo_context, SCHEMA_ACCESS_RULES[DEFAULT_REPO_CONTEXT])
        self._violation_log: List[dict] = []

    def _get_context_from_env(self) -> RepoContext:
        """Get repo context from environment variable."""
        env_value = os.environ.get(REPO_CONTEXT_ENV_VAR, "").lower()

        for context in RepoContext:
            if context.value == env_value:
                return context

        return DEFAULT_REPO_CONTEXT

    def validate_query(self, query: str, raise_on_violation: bool = True) -> bool:
        """
        Validate a SQL query against schema access rules.

        Args:
            query: The SQL query to validate
            raise_on_violation: If True, raise exception on violation.
                               If False, return False and log violation.

        Returns:
            True if query is allowed, False if not (when raise_on_violation=False)

        Raises:
            ForbiddenSchemaAccessError: If query accesses a forbidden schema
            ReadOnlySchemaWriteError: If query writes to a read-only schema
        """
        analysis = QueryParser.analyze(query)

        # Check for forbidden schema access
        forbidden_accessed = analysis.schemas_referenced & self.rules["forbidden"]
        if forbidden_accessed:
            violation = {
                "type": "FORBIDDEN_SCHEMA_ACCESS",
                "repo_context": self.repo_context.value,
                "forbidden_schemas": list(forbidden_accessed),
                "query_snippet": query[:200],
                "operation": analysis.operation_type,
            }
            self._violation_log.append(violation)

            if raise_on_violation:
                raise ForbiddenSchemaAccessError(
                    f"SCHEMA GUARD VIOLATION: Repo '{self.repo_context.value}' cannot access "
                    f"schema(s) {forbidden_accessed}. Query: {query[:100]}...",
                    repo_context=self.repo_context.value,
                    forbidden_schema=", ".join(forbidden_accessed),
                    query_snippet=query,
                )
            return False

        # Check for write to read-only schema
        if analysis.is_write_operation:
            readonly_written = analysis.schemas_referenced & self.rules["read_only"]
            if readonly_written:
                violation = {
                    "type": "READONLY_SCHEMA_WRITE",
                    "repo_context": self.repo_context.value,
                    "readonly_schemas": list(readonly_written),
                    "query_snippet": query[:200],
                    "operation": analysis.operation_type,
                }
                self._violation_log.append(violation)

                if raise_on_violation:
                    raise ReadOnlySchemaWriteError(
                        f"SCHEMA GUARD VIOLATION: Repo '{self.repo_context.value}' cannot write to "
                        f"read-only schema(s) {readonly_written}. Query: {query[:100]}...",
                        repo_context=self.repo_context.value,
                        forbidden_schema=", ".join(readonly_written),
                        query_snippet=query,
                    )
                return False

        return True

    def get_violations(self) -> List[dict]:
        """Get all logged violations."""
        return self._violation_log.copy()

    def clear_violations(self) -> None:
        """Clear the violation log."""
        self._violation_log.clear()


# =============================================================================
# GLOBAL INSTANCE & DECORATORS
# =============================================================================

# Global guard instance (initialized on first use)
_global_guard: Optional[SchemaGuard] = None


def get_guard() -> SchemaGuard:
    """Get or create the global schema guard instance."""
    global _global_guard
    if _global_guard is None:
        _global_guard = SchemaGuard()
    return _global_guard


def validate_query(query: str) -> bool:
    """
    Validate a query using the global schema guard.

    Args:
        query: SQL query to validate

    Returns:
        True if valid

    Raises:
        SchemaGuardError: If query violates schema access rules
    """
    return get_guard().validate_query(query)


def guarded_query(func: Callable) -> Callable:
    """
    Decorator to validate SQL queries before execution.

    The decorated function must have a 'query' parameter (positional or keyword)
    that contains the SQL query string.

    Usage:
        @guarded_query
        def execute_sql(query: str, params: dict = None):
            # query is validated before this runs
            return cursor.execute(query, params)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Try to find the query parameter
        query = None

        # Check kwargs first
        if 'query' in kwargs:
            query = kwargs['query']
        elif 'sql' in kwargs:
            query = kwargs['sql']
        elif args:
            # Assume first string argument is the query
            for arg in args:
                if isinstance(arg, str) and len(arg) > 10:
                    query = arg
                    break

        # Validate if we found a query
        if query:
            validate_query(query)

        return func(*args, **kwargs)

    return wrapper


def schema_guard_context(repo_context: RepoContext):
    """
    Context manager to temporarily set a specific repo context.

    Usage:
        with schema_guard_context(RepoContext.OUTREACH):
            execute_sql("SELECT * FROM outreach.outreach")
    """
    class SchemaGuardContext:
        def __init__(self, context: RepoContext):
            self.context = context
            self.previous_guard = None

        def __enter__(self):
            global _global_guard
            self.previous_guard = _global_guard
            _global_guard = SchemaGuard(self.context)
            return _global_guard

        def __exit__(self, exc_type, exc_val, exc_tb):
            global _global_guard
            _global_guard = self.previous_guard
            return False

    return SchemaGuardContext(repo_context)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point for testing schema guard."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Schema Guard — Validate SQL queries against repo access rules"
    )
    parser.add_argument(
        "--context",
        choices=["outreach", "cl", "sales", "client"],
        default="outreach",
        help="Repository context (default: outreach)",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="SQL query to validate",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="File containing SQL queries (one per line)",
    )
    parser.add_argument(
        "--show-rules",
        action="store_true",
        help="Show schema access rules for context",
    )

    args = parser.parse_args()

    # Set context
    context_map = {
        "outreach": RepoContext.OUTREACH,
        "cl": RepoContext.CL,
        "sales": RepoContext.SALES,
        "client": RepoContext.CLIENT,
    }
    context = context_map[args.context]
    guard = SchemaGuard(context)

    # Show rules
    if args.show_rules:
        print(f"\n{'='*60}")
        print(f"SCHEMA ACCESS RULES — {context.value.upper()}")
        print(f"{'='*60}")
        rules = SCHEMA_ACCESS_RULES[context]
        print(f"\nALLOWED schemas:   {', '.join(sorted(rules['allowed']))}")
        print(f"FORBIDDEN schemas: {', '.join(sorted(rules['forbidden']))}")
        if rules['read_only']:
            print(f"READ-ONLY schemas: {', '.join(sorted(rules['read_only']))}")
        print(f"{'='*60}\n")
        return

    # Validate query
    queries = []
    if args.query:
        queries.append(args.query)
    if args.file:
        with open(args.file, 'r') as f:
            queries.extend([line.strip() for line in f if line.strip()])

    if not queries:
        parser.print_help()
        sys.exit(1)

    # Process queries
    violations = 0
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Query: {query[:80]}{'...' if len(query) > 80 else ''}")

        try:
            guard.validate_query(query)
            print("Result: ALLOWED")
        except SchemaGuardError as e:
            print(f"Result: BLOCKED")
            print(f"Reason: {e}")
            violations += 1

    print(f"\n{'='*60}")
    print(f"Total: {len(queries)} queries, {violations} violations")
    print(f"{'='*60}")

    sys.exit(1 if violations > 0 else 0)


if __name__ == "__main__":
    main()
