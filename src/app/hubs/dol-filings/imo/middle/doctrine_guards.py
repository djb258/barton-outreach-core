"""
DOL Doctrine Guards — IMO Middle Layer Enforcement
===================================================

═══════════════════════════════════════════════════════════════════════════════
DOCTRINE (v1.1 - Error-Only Enforcement)
═══════════════════════════════════════════════════════════════════════════════

The DOL Sub-Hub emits facts only.
All failures are DATA DEFICIENCIES, not system failures.
Therefore, the DOL Sub-Hub NEVER writes to AIR.

Enforced Boundaries:
- NO writes to Company Lifecycle (marketing.company_master)
- NO BIT signal emission
- NO identity minting
- NO AIR logging (dol.air_log is FORBIDDEN)
- ALL failures route to shq.error_master ONLY

These guards enforce IMO boundaries at runtime.
═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Any, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)


class DoctrineViolation(Exception):
    """
    Raised when code attempts to violate DOL Sub-Hub doctrine boundaries.
    
    This is a HARD FAIL. No recovery. No retry.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"DOCTRINE VIOLATION: {self.message}"


# ═══════════════════════════════════════════════════════════════════════════
# GUARD 1: NO CL WRITES
# ═══════════════════════════════════════════════════════════════════════════

# Patterns that indicate CL write attempts (case-insensitive)
_CL_WRITE_PATTERNS = [
    r'\bUPDATE\s+.*company_master\b',
    r'\bUPDATE\s+.*marketing\.company_master\b',
    r'\bINSERT\s+INTO\s+.*company_master\b',
    r'\bINSERT\s+INTO\s+.*marketing\.company_master\b',
    r'\bDELETE\s+FROM\s+.*company_master\b',
    r'\bDELETE\s+FROM\s+.*marketing\.company_master\b',
]

_CL_WRITE_RE = re.compile('|'.join(_CL_WRITE_PATTERNS), re.IGNORECASE)


def assert_no_cl_writes(sql: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    DOCTRINE GUARD: DOL Sub-Hub may NOT write to Company Lifecycle.
    
    Raises DoctrineViolation if SQL contains UPDATE/INSERT/DELETE 
    targeting company_master.
    
    Args:
        sql: SQL statement to validate
        context: Additional context for error reporting
        
    Raises:
        DoctrineViolation: If CL write detected
    """
    if _CL_WRITE_RE.search(sql):
        logger.error(
            f"DOCTRINE VIOLATION: Attempted CL write in DOL Sub-Hub. "
            f"SQL: {sql[:200]}..."
        )
        raise DoctrineViolation(
            "DOL Sub-Hub may NOT write to Company Lifecycle (company_master). "
            "EIN data must be written to dol.ein_linkage only. "
            "Company Hub consumes EIN from linkage table.",
            context=context or {'sql_preview': sql[:500]}
        )


# ═══════════════════════════════════════════════════════════════════════════
# GUARD 2: ALLOWED DOL WRITES (WHITELIST)
# ═══════════════════════════════════════════════════════════════════════════

# NOTE: dol.air_log is INTENTIONALLY EXCLUDED - AIR is FORBIDDEN in DOL
_ALLOWED_DOL_TABLES = frozenset([
    'dol.ein_linkage',
    'dol.violations',
    'dol.form_5500',
    'dol.form_5500_sf',
    'dol.form_5500_schedule_a',
    'dol.form_5500_ez',
    'dol.form_5500_staging',
    'shq.error_master',
])

_WRITE_TO_TABLE_RE = re.compile(
    r'\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+["\']?(\w+\.\w+)["\']?',
    re.IGNORECASE
)


def assert_allowed_write_target(sql: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    DOCTRINE GUARD: DOL may only write to approved DOL tables.
    
    Whitelist:
    - dol.ein_linkage
    - dol.violations
    - dol.air_log
    - dol.form_5500*
    - shq.error_master
    
    Args:
        sql: SQL statement to validate
        context: Additional context for error reporting
        
    Raises:
        DoctrineViolation: If write targets non-DOL table
    """
    matches = _WRITE_TO_TABLE_RE.findall(sql)
    
    for operation, table in matches:
        table_lower = table.lower()
        if table_lower not in _ALLOWED_DOL_TABLES:
            logger.error(
                f"DOCTRINE VIOLATION: DOL attempted write to {table}. "
                f"Only DOL tables are permitted."
            )
            raise DoctrineViolation(
                f"DOL Sub-Hub may only write to DOL-owned tables. "
                f"Attempted: {operation} {table}. "
                f"Allowed: {', '.join(sorted(_ALLOWED_DOL_TABLES))}",
                context=context or {'sql_preview': sql[:500], 'target_table': table}
            )


# ═══════════════════════════════════════════════════════════════════════════
# GUARD 3: NO BIT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

def assert_no_bit_integration() -> None:
    """
    DOCTRINE GUARD: DOL Sub-Hub has NO CONNECTION to BIT Axle.
    
    This guard should be called at module load to prevent BIT imports.
    DOL emits FACTS ONLY — BIT consumes facts via views.
    
    Raises:
        DoctrineViolation: Always (this function exists to document the rule)
    """
    raise DoctrineViolation(
        "DOL Sub-Hub has NO CONNECTION to BIT Axle. "
        "DOL emits FACTS ONLY. BIT must consume DOL data via views: "
        "dol.ein_linkage, analytics.v_5500_*. "
        "Remove all BITEngine imports and signal emissions from DOL code."
    )


# ═══════════════════════════════════════════════════════════════════════════
# GUARD 4: NO AIR LOGGING (HARD KILL)
# ═══════════════════════════════════════════════════════════════════════════

# Patterns that indicate AIR write attempts (case-insensitive)
_AIR_PATTERNS = [
    r'\bINSERT\s+INTO\s+.*air_log\b',
    r'\bINSERT\s+INTO\s+.*dol\.air_log\b',
    r'\bwrite_air\b',
    r'\bAIR_EVENT\b',
    r'\bwrite_air_log\b',
    r'\bwrite_air_info_event\b',
]

import re as _air_re_module
_AIR_RE = _air_re_module.compile('|'.join(_AIR_PATTERNS), _air_re_module.IGNORECASE)


def assert_no_air_logging(sql_or_code: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    DOCTRINE GUARD: DOL Sub-Hub may NOT write to AIR.
    
    The DOL Sub-Hub emits facts only.
    All failures are DATA DEFICIENCIES, not system failures.
    Therefore, the DOL Sub-Hub NEVER writes to AIR.
    
    All failures must route to shq.error_master ONLY.
    
    Args:
        sql_or_code: SQL statement or code to validate
        context: Additional context for error reporting
        
    Raises:
        DoctrineViolation: If AIR write detected
    """
    if _AIR_RE.search(sql_or_code):
        logger.error(
            f"DOCTRINE VIOLATION: Attempted AIR write in DOL Sub-Hub. "
            f"Content: {sql_or_code[:200]}..."
        )
        raise DoctrineViolation(
            "AIR logging is FORBIDDEN in the DOL Sub-Hub. "
            "All failures must write to shq.error_master. "
            "Remove all references to: dol.air_log, write_air, AIR_EVENT, "
            "write_air_log, write_air_info_event",
            context=context or {'preview': sql_or_code[:500]}
        )


# ═══════════════════════════════════════════════════════════════════════════
# SQL EXECUTION WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

def execute_with_guards(cursor, sql: str, params=None, context: Optional[Dict] = None):
    """
    Execute SQL with doctrine guards applied.
    
    Validates SQL against DOL boundaries before execution.
    
    Args:
        cursor: Database cursor
        sql: SQL to execute
        params: Query parameters
        context: Additional context for error reporting
        
    Returns:
        Cursor result
        
    Raises:
        DoctrineViolation: If SQL violates DOL boundaries
    """
    # Apply guards
    assert_no_cl_writes(sql, context)
    assert_allowed_write_target(sql, context)
    assert_no_air_logging(sql, context)  # AIR is FORBIDDEN
    
    # Execute if guards pass
    if params:
        return cursor.execute(sql, params)
    return cursor.execute(sql)


# ═══════════════════════════════════════════════════════════════════════════
# GUARD 5: ENFORCEMENT GATE ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════

def assert_enforcement_gate_clean(module_source: str) -> None:
    """
    DOCTRINE GUARD: Enforcement Gate may NOT contain prohibited patterns.
    
    The enforcement gate is post-resolution. It does:
    - Read dol.ein_linkage
    - Count EINs per context
    - Write errors to shq.error_master
    
    It does NOT do:
    - AIR logging
    - Fuzzy matching
    - Enrichment
    - BIT signals
    - CL writes
    
    Args:
        module_source: Source code to validate
        
    Raises:
        DoctrineViolation: If prohibited pattern found
    """
    prohibited_patterns = [
        (r'\bfuzzy_match\b', "Enforcement gate cannot run fuzzy matching"),
        (r'\benrichment\b', "Enforcement gate cannot trigger enrichment"),
        (r'\bBITEngine\b', "Enforcement gate cannot emit BIT signals"),
        (r'\bemit_bit_signal\b', "Enforcement gate cannot emit BIT signals"),
        (r'\bwrite_air\b', "Enforcement gate cannot write to AIR"),
        (r'\bair_log\b', "Enforcement gate cannot reference AIR tables"),
        (r'\bINSERT\s+INTO\s+.*company_master\b', "Enforcement gate cannot write to CL"),
        (r'\bUPDATE\s+.*company_master\b', "Enforcement gate cannot write to CL"),
    ]
    
    for pattern, message in prohibited_patterns:
        if re.search(pattern, module_source, re.IGNORECASE):
            raise DoctrineViolation(
                f"Enforcement gate violation: {message}. "
                f"Remove prohibited pattern: {pattern}"
            )


def assert_ein_count_logic_only(sql: str) -> None:
    """
    DOCTRINE GUARD: Enforcement SQL should only count EINs, not modify data.
    
    Enforcement gate reads are:
    - SELECT COUNT(DISTINCT ein) FROM dol.ein_linkage
    - SELECT ... FROM outreach_ctx.context
    - SELECT ... FROM marketing.company_master (READ ONLY)
    
    Args:
        sql: SQL to validate
        
    Raises:
        DoctrineViolation: If SQL is not a read operation (except error writes)
    """
    sql_upper = sql.upper().strip()
    
    # Allow SELECT statements
    if sql_upper.startswith('SELECT'):
        return
    
    # Allow INSERT to shq.error_master ONLY
    if 'INSERT' in sql_upper and 'SHQ.ERROR_MASTER' in sql_upper:
        return
    
    # Everything else is prohibited
    if any(kw in sql_upper for kw in ['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'DROP']):
        raise DoctrineViolation(
            f"Enforcement gate may only READ data (except error writes). "
            f"Prohibited SQL: {sql[:200]}..."
        )
