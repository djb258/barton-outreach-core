"""
DOL EIN Enforcement Gate — IMO Middle Layer
============================================

═══════════════════════════════════════════════════════════════════════════════
DOCTRINE (v1.2 - EIN Enforcement Gate)
═══════════════════════════════════════════════════════════════════════════════

For every outreach_context_id processed by DOL:

    IF EIN count = 0  → FAIL (DOL_EIN_MISSING)
    IF EIN count > 1  → FAIL (DOL_EIN_AMBIGUOUS)
    IF EIN count = 1  → PASS

Failures are DATA DEFICIENCIES.
Failures WRITE ONLY to shq.error_master.

❌ NO AIR
❌ NO RETRIES  
❌ NO FUZZY MATCH
❌ NO COMPANY WRITES
❌ NO NEW TABLES

This is enforcement only. Post-resolution. Facts in, facts out.

═══════════════════════════════════════════════════════════════════════════════
"""

from typing import Any, Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import sys
import os

# Add parent paths for standalone execution
_script_dir = os.path.dirname(os.path.abspath(__file__))
_imo_dir = os.path.dirname(_script_dir)  # imo/
_hub_dir = os.path.dirname(_imo_dir)     # dol-filings/
_hubs_dir = os.path.dirname(_hub_dir)    # hubs/
_root_dir = os.path.dirname(_hubs_dir)   # project root

# Ensure we can import sibling modules
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

# Try relative imports first (when used as module), fallback to direct import
try:
    from ..output.error_writer import (
        write_error_master,
        DOLErrorCode,
        SEVERITY_HARD_FAIL,
        is_in_scope,
        TARGET_STATES,
    )
    from .doctrine_guards import (
        assert_no_cl_writes,
        assert_no_air_logging,
        DoctrineViolation,
    )
except ImportError:
    # Fallback: Direct import for standalone execution
    import importlib.util
    
    # Load error_writer directly
    error_writer_path = os.path.join(_imo_dir, 'output', 'error_writer.py')
    spec = importlib.util.spec_from_file_location("error_writer", error_writer_path)
    error_writer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(error_writer)
    
    write_error_master = error_writer.write_error_master
    DOLErrorCode = error_writer.DOLErrorCode
    SEVERITY_HARD_FAIL = error_writer.SEVERITY_HARD_FAIL
    is_in_scope = error_writer.is_in_scope
    TARGET_STATES = error_writer.TARGET_STATES
    
    # Load doctrine_guards directly
    guards_path = os.path.join(_script_dir, 'doctrine_guards.py')
    spec = importlib.util.spec_from_file_location("doctrine_guards", guards_path)
    doctrine_guards = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctrine_guards)
    
    assert_no_cl_writes = doctrine_guards.assert_no_cl_writes
    assert_no_air_logging = doctrine_guards.assert_no_air_logging
    DoctrineViolation = doctrine_guards.DoctrineViolation

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENFORCEMENT RESULT TYPES
# ═══════════════════════════════════════════════════════════════════════════

class EnforcementOutcome(Enum):
    """Possible outcomes from EIN enforcement gate."""
    PASS = "PASS"
    FAIL_MISSING = "FAIL_MISSING"
    FAIL_AMBIGUOUS = "FAIL_AMBIGUOUS"
    SKIPPED = "SKIPPED"  # Out of geographic scope


@dataclass
class EnforcementResult:
    """Result of enforcing EIN rule on a single context."""
    outreach_context_id: str
    outcome: EnforcementOutcome
    ein_count: int
    eins_found: List[str]
    error_id: Optional[str] = None
    message: Optional[str] = None


@dataclass
class EnforcementSummary:
    """Summary of enforcement gate run."""
    contexts_evaluated: int
    passed: int
    missing_ein: int
    ambiguous_ein: int
    skipped_out_of_scope: int
    errors_written: int


# ═══════════════════════════════════════════════════════════════════════════
# SUPPRESSION KEY (CONTEXT-LEVEL DEDUPLICATION)
# ═══════════════════════════════════════════════════════════════════════════

def generate_enforcement_suppression_key(
    outreach_context_id: str,
    error_code: str,
    filing_year: Optional[int] = None
) -> str:
    """
    Generate deterministic suppression key for EIN enforcement errors.
    
    Same (context, error_code, filing_year) = same key = deduplicated.
    
    Args:
        outreach_context_id: The context being evaluated
        error_code: DOL_EIN_MISSING or DOL_EIN_AMBIGUOUS
        filing_year: Optional filing year for additional granularity
        
    Returns:
        32-char hex hash
    """
    components = [
        str(outreach_context_id).strip(),
        error_code,
        str(filing_year or ''),
    ]
    key_string = '|'.join(components)
    return hashlib.sha256(key_string.encode()).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════════════════════
# EIN COUNT QUERY
# ═══════════════════════════════════════════════════════════════════════════

_EIN_COUNT_SQL = """
SELECT 
    COUNT(DISTINCT ein) AS ein_count,
    ARRAY_AGG(DISTINCT ein) AS eins
FROM dol.ein_linkage
WHERE outreach_context_id = %s
"""

_CONTEXT_STATE_SQL = """
SELECT 
    f.spons_dfe_mail_us_state
FROM dol.ein_linkage el
JOIN dol.form_5500 f 
    ON el.ein = f.sponsor_dfe_ein
WHERE el.outreach_context_id = %s
LIMIT 1
"""


def get_ein_count_for_context(
    cursor,
    outreach_context_id: str
) -> Tuple[int, List[str]]:
    """
    Count distinct EINs linked to an outreach_context_id.
    
    Args:
        cursor: Database cursor
        outreach_context_id: Context to evaluate
        
    Returns:
        Tuple of (count, list of EINs)
    """
    cursor.execute(_EIN_COUNT_SQL, (outreach_context_id,))
    row = cursor.fetchone()
    
    if not row or row[0] is None:
        return (0, [])
    
    return (row[0], row[1] or [])


def get_state_for_context(
    cursor,
    outreach_context_id: str
) -> Optional[str]:
    """
    Get the state associated with a context (for geographic filtering).
    
    Args:
        cursor: Database cursor
        outreach_context_id: Context to look up
        
    Returns:
        Two-letter state code, or None if not found
    """
    cursor.execute(_CONTEXT_STATE_SQL, (outreach_context_id,))
    row = cursor.fetchone()
    
    if row and row[0]:
        return row[0].upper().strip()
    return None


# ═══════════════════════════════════════════════════════════════════════════
# SINGLE CONTEXT ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════

def enforce_ein_rule(
    conn,
    outreach_context_id: str,
    *,
    filing_year: Optional[int] = None,
    skip_geographic_check: bool = False,
) -> EnforcementResult:
    """
    Enforce exactly-one-EIN rule for a single outreach_context_id.
    
    DOCTRINE:
        - 0 EINs → FAIL (DOL_EIN_MISSING)
        - >1 EINs → FAIL (DOL_EIN_AMBIGUOUS)
        - 1 EIN → PASS
    
    Args:
        conn: Database connection
        outreach_context_id: The context to evaluate
        filing_year: Optional filing year for suppression key
        skip_geographic_check: If True, skip state filter (testing only)
        
    Returns:
        EnforcementResult with outcome and details
    """
    cursor = conn.cursor()
    
    # ─────────────────────────────────────────────────────────────────────
    # GEOGRAPHIC GUARD
    # ─────────────────────────────────────────────────────────────────────
    
    if not skip_geographic_check:
        state = get_state_for_context(cursor, outreach_context_id)
        if not is_in_scope(state):
            logger.debug(
                f"SKIPPED (out of scope): context={outreach_context_id[:8]}... "
                f"state={state}"
            )
            return EnforcementResult(
                outreach_context_id=outreach_context_id,
                outcome=EnforcementOutcome.SKIPPED,
                ein_count=0,
                eins_found=[],
                message=f"Out of geographic scope: state={state}"
            )
    
    # ─────────────────────────────────────────────────────────────────────
    # COUNT EINs
    # ─────────────────────────────────────────────────────────────────────
    
    ein_count, eins_found = get_ein_count_for_context(cursor, outreach_context_id)
    
    # ─────────────────────────────────────────────────────────────────────
    # CASE A: ZERO EINs → FAIL (DOL_EIN_MISSING)
    # ─────────────────────────────────────────────────────────────────────
    
    if ein_count == 0:
        suppression_key = generate_enforcement_suppression_key(
            outreach_context_id, 
            DOLErrorCode.DOL_EIN_MISSING, 
            filing_year
        )
        
        error_id = write_error_master(
            conn,
            error_code=DOLErrorCode.DOL_EIN_MISSING,
            message=f"No EIN linked to outreach context: {outreach_context_id}",
            severity=SEVERITY_HARD_FAIL,
            outreach_context_id=outreach_context_id,
            eligible_for_enrichment=False,  # Not an enrichment issue
            context={
                'enforcement_gate': 'DOL_EIN_ENFORCEMENT',
                'suppression_key': suppression_key,
                'ein_count': 0,
                'filing_year': filing_year,
            },
        )
        
        logger.warning(
            f"FAIL (EIN_MISSING): context={outreach_context_id[:8]}... "
            f"error_id={error_id[:8]}..."
        )
        
        return EnforcementResult(
            outreach_context_id=outreach_context_id,
            outcome=EnforcementOutcome.FAIL_MISSING,
            ein_count=0,
            eins_found=[],
            error_id=error_id,
            message="No EIN linked to context"
        )
    
    # ─────────────────────────────────────────────────────────────────────
    # CASE B: MULTIPLE EINs → FAIL (DOL_EIN_AMBIGUOUS)
    # ─────────────────────────────────────────────────────────────────────
    
    if ein_count > 1:
        suppression_key = generate_enforcement_suppression_key(
            outreach_context_id, 
            DOLErrorCode.DOL_EIN_AMBIGUOUS, 
            filing_year
        )
        
        error_id = write_error_master(
            conn,
            error_code=DOLErrorCode.DOL_EIN_AMBIGUOUS,
            message=(
                f"Multiple EINs ({ein_count}) linked to outreach context: "
                f"{outreach_context_id}. EINs: {', '.join(eins_found[:5])}"
            ),
            severity=SEVERITY_HARD_FAIL,
            outreach_context_id=outreach_context_id,
            eligible_for_enrichment=False,  # Not an enrichment issue
            context={
                'enforcement_gate': 'DOL_EIN_ENFORCEMENT',
                'suppression_key': suppression_key,
                'ein_count': ein_count,
                'eins_found': eins_found,
                'filing_year': filing_year,
            },
        )
        
        logger.warning(
            f"FAIL (EIN_AMBIGUOUS): context={outreach_context_id[:8]}... "
            f"ein_count={ein_count} error_id={error_id[:8]}..."
        )
        
        return EnforcementResult(
            outreach_context_id=outreach_context_id,
            outcome=EnforcementOutcome.FAIL_AMBIGUOUS,
            ein_count=ein_count,
            eins_found=eins_found,
            error_id=error_id,
            message=f"Multiple EINs ({ein_count}) linked to context"
        )
    
    # ─────────────────────────────────────────────────────────────────────
    # CASE C: EXACTLY ONE EIN → PASS
    # ─────────────────────────────────────────────────────────────────────
    
    logger.debug(
        f"PASS: context={outreach_context_id[:8]}... ein={eins_found[0]}"
    )
    
    return EnforcementResult(
        outreach_context_id=outreach_context_id,
        outcome=EnforcementOutcome.PASS,
        ein_count=1,
        eins_found=eins_found,
        message=f"EIN attached: {eins_found[0]}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# BATCH ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════

_ACTIVE_CONTEXTS_SQL = """
SELECT DISTINCT outreach_context_id
FROM dol.ein_linkage
WHERE outreach_context_id IS NOT NULL
UNION
SELECT DISTINCT outreach_context_id::text
FROM outreach_ctx.context
WHERE status = 'OPEN'
"""


def enforce_all_contexts(
    conn,
    *,
    filing_year: Optional[int] = None,
    limit: Optional[int] = None,
) -> EnforcementSummary:
    """
    Enforce EIN rule across all active outreach contexts.
    
    Args:
        conn: Database connection
        filing_year: Optional filing year filter
        limit: Max contexts to process (for testing)
        
    Returns:
        EnforcementSummary with counts
    """
    cursor = conn.cursor()
    
    # Get contexts to evaluate
    sql = _ACTIVE_CONTEXTS_SQL
    if limit:
        sql += f" LIMIT {int(limit)}"
    
    cursor.execute(sql)
    contexts = [row[0] for row in cursor.fetchall()]
    
    # Counters
    passed = 0
    missing_ein = 0
    ambiguous_ein = 0
    skipped = 0
    errors_written = 0
    
    for ctx_id in contexts:
        result = enforce_ein_rule(
            conn, 
            ctx_id, 
            filing_year=filing_year
        )
        
        if result.outcome == EnforcementOutcome.PASS:
            passed += 1
        elif result.outcome == EnforcementOutcome.FAIL_MISSING:
            missing_ein += 1
            if result.error_id:
                errors_written += 1
        elif result.outcome == EnforcementOutcome.FAIL_AMBIGUOUS:
            ambiguous_ein += 1
            if result.error_id:
                errors_written += 1
        elif result.outcome == EnforcementOutcome.SKIPPED:
            skipped += 1
    
    summary = EnforcementSummary(
        contexts_evaluated=len(contexts),
        passed=passed,
        missing_ein=missing_ein,
        ambiguous_ein=ambiguous_ein,
        skipped_out_of_scope=skipped,
        errors_written=errors_written,
    )
    
    logger.info(
        f"EIN Enforcement Gate complete: "
        f"evaluated={summary.contexts_evaluated} "
        f"passed={summary.passed} "
        f"missing={summary.missing_ein} "
        f"ambiguous={summary.ambiguous_ein} "
        f"skipped={summary.skipped_out_of_scope}"
    )
    
    return summary


# ═══════════════════════════════════════════════════════════════════════════
# GATE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def run_enforcement_gate(
    conn,
    *,
    filing_year: Optional[int] = None,
    limit: Optional[int] = None,
) -> str:
    """
    Run the DOL EIN Enforcement Gate.
    
    This is the main entry point for CI/scheduled runs.
    
    Args:
        conn: Database connection
        filing_year: Optional filing year filter
        limit: Max contexts to process
        
    Returns:
        Formatted summary string
    """
    summary = enforce_all_contexts(
        conn,
        filing_year=filing_year,
        limit=limit,
    )
    
    return (
        f"EIN Enforcement Gate implemented.\n"
        f"Contexts evaluated: {summary.contexts_evaluated}\n"
        f"Missing EIN: {summary.missing_ein}\n"
        f"Ambiguous EIN: {summary.ambiguous_ein}\n"
        f"AIR writes: 0"
    )


# ═══════════════════════════════════════════════════════════════════════════
# PROHIBITIONS (HARD KILL)
# ═══════════════════════════════════════════════════════════════════════════

def _assert_no_prohibited_operations():
    """
    Static assertions for prohibited operations.
    
    This function exists to document what this module MUST NOT do.
    Import-time check.
    """
    # These imports should NEVER exist in this module
    prohibited_imports = [
        'write_air',
        'write_air_log', 
        'write_air_info_event',
        'BITEngine',
        'emit_bit_signal',
        'fuzzy_match',
        'run_enrichment',
    ]
    
    import sys
    current_module = sys.modules.get(__name__, {})
    for name in prohibited_imports:
        if hasattr(current_module, name):
            raise DoctrineViolation(
                f"PROHIBITED: {name} must not exist in enforcement gate. "
                f"This module does enforcement only — no AIR, no BIT, no fuzzy."
            )


# Run prohibitions check at import time
_assert_no_prohibited_operations()


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    CLI entry point for DOL EIN Enforcement Gate.
    
    Usage:
        python -m hubs.dol-filings.imo.middle.dol_enforcement_gate --mode=batch
        python dol_enforcement_gate.py --mode=batch --limit=100
    """
    import argparse
    import os
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[DOL EIN GATE] %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description='DOL EIN Enforcement Gate (v1.2)',
        epilog='Doctrine: Every outreach_context_id must have exactly ONE EIN.'
    )
    parser.add_argument(
        '--mode',
        choices=['batch', 'single', 'dry-run'],
        default='batch',
        help='Execution mode: batch (all contexts), single (one context), dry-run (no writes)'
    )
    parser.add_argument(
        '--context-id',
        type=str,
        help='Single outreach_context_id to evaluate (required for --mode=single)'
    )
    parser.add_argument(
        '--filing-year',
        type=int,
        help='Filter by filing year'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Max contexts to process (for testing)'
    )
    parser.add_argument(
        '--db-url',
        type=str,
        default=os.environ.get('DATABASE_URL') or os.environ.get('NEON_CONNECTION_STRING'),
        help='Database connection URL (default: $DATABASE_URL or $NEON_CONNECTION_STRING)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'single' and not args.context_id:
        parser.error("--context-id is required for --mode=single")
    
    if not args.db_url:
        logger.error("Database URL not set. Use --db-url or set DATABASE_URL/NEON_CONNECTION_STRING env var.")
        sys.exit(1)
    
    # Print header
    print("═══════════════════════════════════════════════════════════════════════════")
    print("DOL EIN ENFORCEMENT GATE — v1.2")
    print("═══════════════════════════════════════════════════════════════════════════")
    print("")
    print(f"Scope states: {', '.join(sorted(TARGET_STATES))}")
    print(f"Mode: {args.mode}")
    if args.limit:
        print(f"Limit: {args.limit}")
    print("")
    
    # Connect to database
    try:
        import psycopg2
        conn = psycopg2.connect(args.db_url)
        logger.info("Database connected")
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)
    
    try:
        if args.mode == 'dry-run':
            # Dry run - just count, no writes
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT outreach_context_id)
                FROM dol.ein_linkage
                WHERE outreach_context_id IS NOT NULL
            """)
            count = cursor.fetchone()[0]
            print(f"[DRY RUN] Contexts in dol.ein_linkage: {count}")
            print(f"[DRY RUN] No writes performed")
            
        elif args.mode == 'single':
            # Single context evaluation
            result = enforce_ein_rule(
                conn,
                args.context_id,
                filing_year=args.filing_year,
            )
            print(f"Context: {args.context_id}")
            print(f"Outcome: {result.outcome.value}")
            print(f"EIN Count: {result.ein_count}")
            if result.eins_found:
                print(f"EINs: {', '.join(result.eins_found)}")
            if result.error_id:
                print(f"Error ID: {result.error_id}")
            print(f"Message: {result.message}")
            
        else:
            # Batch mode
            logger.info("Starting enforcement pass")
            
            summary = enforce_all_contexts(
                conn,
                filing_year=args.filing_year,
                limit=args.limit,
            )
            
            print("")
            print("─────────────────────────────────────────────────────────────────────────────")
            print(f"Contexts scanned: {summary.contexts_evaluated:,}")
            print(f"Locked (exactly 1 EIN): {summary.passed:,}")
            print(f"Missing EIN: {summary.missing_ein:,}")
            print(f"Ambiguous EIN: {summary.ambiguous_ein:,}")
            print(f"Out of scope (skipped): {summary.skipped_out_of_scope:,}")
            print(f"Errors written: {summary.errors_written:,}")
            print(f"AIR writes: 0")
            print("─────────────────────────────────────────────────────────────────────────────")
            print("")
            logger.info("Enforcement COMPLETE")
            
    except DoctrineViolation as e:
        logger.error(f"DOCTRINE VIOLATION: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Enforcement failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()
    
    print("")
    print("✅ Gate complete. Run CI guards to verify:")
    print("   bash hubs/dol-filings/_audit/dol_imo_guards.sh")
    print("")


if __name__ == '__main__':
    main()
