"""
Sovereign Mutation Guard
========================

DOCTRINE: Hub status, overrides, and eligibility are PROTECTED tables.
          Only sanctioned IMO middle layers may write to them.

This module enforces:
1. READ-ONLY access from all non-IMO modules
2. Fail-closed behavior if mutation attempted from wrong context
3. Audit logging for all mutation attempts

PROTECTED TABLES (DO NOT WRITE outside IMO middle layer):
- outreach.company_hub_status
- outreach.manual_overrides
- outreach.hub_registry

PROTECTED VIEWS (READ-ONLY, computed from tables):
- outreach.vw_sovereign_completion
- outreach.vw_marketing_eligibility
- outreach.vw_marketing_eligibility_with_overrides

SANCTIONED WRITERS:
- hubs/*/imo/middle/hub_status.py (hub status updates)
- infra/migrations/*.sql (schema + kill switch functions)
- SQL functions: set_marketing_override(), remove_marketing_override()
"""

import os
import sys
import logging
import functools
from pathlib import Path
from typing import Callable, Any, List, Set

logger = logging.getLogger(__name__)

# ============================================================================
# PROTECTED RESOURCES
# ============================================================================

PROTECTED_TABLES: Set[str] = {
    'outreach.company_hub_status',
    'outreach.manual_overrides', 
    'outreach.hub_registry',
    'company_hub_status',  # Without schema prefix
    'manual_overrides',
    'hub_registry',
}

PROTECTED_VIEWS: Set[str] = {
    'outreach.vw_sovereign_completion',
    'outreach.vw_marketing_eligibility',
    'outreach.vw_marketing_eligibility_with_overrides',
    'vw_sovereign_completion',
    'vw_marketing_eligibility', 
    'vw_marketing_eligibility_with_overrides',
}

# ============================================================================
# SANCTIONED PATHS (allowed to write)
# ============================================================================

SANCTIONED_WRITER_PATTERNS: List[str] = [
    'hubs/people-intelligence/imo/middle/hub_status.py',
    'hubs/talent-flow/imo/middle/hub_status.py',
    'hubs/blog-content/imo/middle/hub_status.py',
    'hubs/company-target/imo/middle/hub_status.py',
    'hubs/dol-filings/imo/middle/hub_status.py',
    'infra/migrations/',
    'imo/middle/',  # Any IMO middle layer
]

# Paths that are explicitly READ-ONLY
READ_ONLY_PATHS: List[str] = [
    'spokes/',
    'ctb/ui/',
    'ops/',
    'scripts/',
    'src/',
    'enrichment-hub/',
    'integrations/',
    'tests/',
]


class MutationGuardViolation(Exception):
    """Raised when a mutation is attempted from a non-sanctioned path."""
    pass


def is_sanctioned_writer(caller_path: str) -> bool:
    """
    Check if the caller is a sanctioned writer.
    
    Returns True if the caller is allowed to write to protected tables.
    """
    caller_path = caller_path.replace('\\', '/')
    
    for pattern in SANCTIONED_WRITER_PATTERNS:
        if pattern in caller_path:
            return True
    
    return False


def is_read_only_context(caller_path: str) -> bool:
    """
    Check if the caller is in a read-only context.
    
    These paths should NEVER write to protected tables.
    """
    caller_path = caller_path.replace('\\', '/')
    
    for pattern in READ_ONLY_PATHS:
        if pattern in caller_path:
            return True
    
    return False


def get_caller_path() -> str:
    """Get the path of the calling module."""
    frame = sys._getframe(2)  # Go up 2 frames
    return frame.f_code.co_filename


def check_mutation_allowed(table_name: str, operation: str = 'WRITE') -> bool:
    """
    Check if mutation is allowed for the given table.
    
    FAIL CLOSED: If in doubt, deny the mutation.
    
    Args:
        table_name: The table being accessed
        operation: The operation type (INSERT, UPDATE, DELETE)
        
    Returns:
        True if mutation is allowed
        
    Raises:
        MutationGuardViolation: If mutation is not allowed
    """
    # Normalize table name
    table_lower = table_name.lower()
    
    # Check if it's a protected table
    is_protected = any(t in table_lower for t in PROTECTED_TABLES)
    
    if not is_protected:
        return True  # Not a protected table, allow
    
    # Get caller context
    caller_path = get_caller_path()
    
    # Check if caller is sanctioned
    if is_sanctioned_writer(caller_path):
        logger.debug(f"Sanctioned {operation} to {table_name} from {caller_path}")
        return True
    
    # Check if caller is in read-only context
    if is_read_only_context(caller_path):
        error_msg = (
            f"MUTATION GUARD VIOLATION: {operation} to protected table "
            f"'{table_name}' attempted from read-only path: {caller_path}"
        )
        logger.error(error_msg)
        raise MutationGuardViolation(error_msg)
    
    # FAIL CLOSED: Unknown context, deny mutation
    error_msg = (
        f"MUTATION GUARD VIOLATION: {operation} to protected table "
        f"'{table_name}' from unknown context: {caller_path}. "
        f"Only IMO middle layers may write to sovereign tables."
    )
    logger.error(error_msg)
    raise MutationGuardViolation(error_msg)


def readonly_guard(func: Callable) -> Callable:
    """
    Decorator to mark a function as read-only.
    
    DO NOT WRITE to protected tables from decorated functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Set a flag indicating we're in read-only context
        wrapper._is_readonly = True
        try:
            return func(*args, **kwargs)
        finally:
            wrapper._is_readonly = False
    
    wrapper._is_readonly = False
    return wrapper


def assert_no_mutations_in_sql(sql: str, caller_context: str = None) -> None:
    """
    Assert that a SQL statement doesn't mutate protected tables.
    
    Use this to validate SQL strings before execution in read-only contexts.
    
    Args:
        sql: The SQL statement to check
        caller_context: Optional context for error messages
        
    Raises:
        MutationGuardViolation: If mutation detected
    """
    sql_upper = sql.upper()
    
    # Check for mutation keywords
    mutation_keywords = ['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'DROP', 'ALTER']
    
    has_mutation = any(kw in sql_upper for kw in mutation_keywords)
    
    if not has_mutation:
        return  # No mutations, safe
    
    # Check if any protected tables are targeted
    sql_lower = sql.lower()
    
    for table in PROTECTED_TABLES:
        if table.lower() in sql_lower:
            context_msg = f" from {caller_context}" if caller_context else ""
            error_msg = (
                f"MUTATION GUARD VIOLATION: SQL contains mutation of "
                f"protected table '{table}'{context_msg}: {sql[:200]}..."
            )
            logger.error(error_msg)
            raise MutationGuardViolation(error_msg)


# ============================================================================
# STATIC ANALYSIS HELPERS
# ============================================================================

def scan_file_for_mutations(file_path: str) -> List[str]:
    """
    Scan a Python file for potential mutations to protected tables.
    
    Returns a list of violation descriptions.
    """
    violations = []
    file_path_normalized = file_path.replace('\\', '/')
    
    # Skip sanctioned writers
    if is_sanctioned_writer(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [f"Could not read file: {e}"]
    
    content_lower = content.lower()
    
    # Check for mutation patterns
    mutation_patterns = [
        ('INSERT INTO', 'INSERT'),
        ('UPDATE ', 'UPDATE'),
        ('DELETE FROM', 'DELETE'),
        ('.execute(', 'execute'),
    ]
    
    for table in PROTECTED_TABLES:
        table_lower = table.lower()
        
        if table_lower not in content_lower:
            continue
        
        # Table is mentioned - check for mutations
        for pattern, op in mutation_patterns:
            if pattern.lower() in content_lower and table_lower in content_lower:
                # More precise check - are they near each other?
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if pattern.lower() in line_lower and table_lower in line_lower:
                        violations.append(
                            f"{file_path}:{i+1}: Potential {op} to {table}"
                        )
    
    return violations


def scan_directory_for_mutations(directory: str) -> List[str]:
    """
    Scan a directory for files with potential mutation violations.
    
    Returns a list of all violations found.
    """
    violations = []
    path = Path(directory)
    
    for py_file in path.rglob('*.py'):
        file_violations = scan_file_for_mutations(str(py_file))
        violations.extend(file_violations)
    
    return violations


# ============================================================================
# MAIN - can be run as a script to scan for violations
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan for mutation guard violations')
    parser.add_argument('path', nargs='?', default='.', help='Path to scan')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SOVEREIGN MUTATION GUARD SCANNER")
    print("=" * 60)
    print(f"Scanning: {args.path}")
    print(f"Protected tables: {PROTECTED_TABLES}")
    print("")
    
    violations = scan_directory_for_mutations(args.path)
    
    if violations:
        print(f"❌ Found {len(violations)} potential violations:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("✅ No mutation violations detected")
        sys.exit(0)
