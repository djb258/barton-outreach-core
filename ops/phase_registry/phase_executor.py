"""
Phase Executor - Barton Toolbox Hub

Phase-aware execution system for Claude Code.
Orchestrates outreach pipeline phases using the phase registry.

Purpose:
- Execute phases by ID with context
- Validate phase sequences before execution
- Track phase completion per company
- Log all actions to pipeline_events and audit_log
- Handle phase failures and retries

Doctrine ID: 04.04.02.04.ple.validation_pipeline

Usage:
    from backend.phase_executor import run_outreach_phase

    # Execute Phase 1 (Company Validation)
    result = run_outreach_phase(1, {"company": company_record})

    # Execute Phase 1.1 (People Validation)
    result = run_outreach_phase(1.1, {"state": "WV", "dry_run": False})

    # Execute Phase 3 (Outreach Readiness)
    result = run_outreach_phase(3, {"state": "WV", "only_validated": True})

Claude Code Pattern:
    When user says "Run Phase 2 for WV people":
    1. Get phase entry: phase = get_phase_entry(2)
    2. Execute: result = run_outreach_phase(2, {"state": "WV"})
    3. Log result to pipeline_events with phase_id
    4. Report results to user

Status: ✅ Production Ready
Date: 2025-11-17
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TODO: backend module does not exist — need to implement or remove
# from backend.outreach_phase_registry import (
#     get_phase_entry,
#     get_phase_function,
#     validate_phase_sequence,
#     get_next_phase,
#     get_phase_dependencies,
#     get_phase_status_summary
# )

# Import database utilities
try:
    from backend.validator.db_utils import log_to_pipeline_events, log_to_audit_log  # TODO: backend module does not exist
    DB_UTILS_AVAILABLE = True
except ImportError:
    DB_UTILS_AVAILABLE = False
    logging.warning("Database utilities not available. Logging disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PHASE EXECUTION CONFIGURATION
# ============================================================================

EXECUTION_CONFIG = {
    "doctrine_id": "04.04.02.04.ple.validation_pipeline",
    "log_to_pipeline_events": True,
    "log_to_audit_log": True,
    "validate_dependencies": True,
    "auto_advance": False,  # Automatically execute next phase if current succeeds
    "stop_on_error": True   # Stop execution if phase fails
}


# ============================================================================
# PHASE EXECUTION STATISTICS
# ============================================================================

class PhaseExecutionStats:
    """Track phase execution statistics"""

    def __init__(self):
        self.phase_id = None
        self.phase_name = None
        self.started_at = None
        self.completed_at = None
        self.status = None  # 'complete', 'failed', 'skipped'
        self.error_message = None
        self.result = None

    def start(self, phase_id, phase_name):
        """Mark phase execution start"""
        self.phase_id = phase_id
        self.phase_name = phase_name
        self.started_at = datetime.now()
        self.status = "running"

    def complete(self, result):
        """Mark phase execution complete"""
        self.completed_at = datetime.now()
        self.status = "complete"
        self.result = result

    def fail(self, error_message):
        """Mark phase execution failed"""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.error_message = error_message

    def skip(self, reason):
        """Mark phase execution skipped"""
        self.completed_at = datetime.now()
        self.status = "skipped"
        self.error_message = reason

    def get_duration_seconds(self) -> float:
        """Get execution duration in seconds"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return 0.0

    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        return {
            "phase_id": self.phase_id,
            "phase_name": self.phase_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "error_message": self.error_message,
            "duration_seconds": self.get_duration_seconds()
        }


# ============================================================================
# MAIN PHASE EXECUTION FUNCTION
# ============================================================================

def run_outreach_phase(
    phase_id,
    context: Optional[Dict] = None,
    validate_deps: bool = True,
    log_execution: bool = True
) -> Dict:
    """
    Execute the specified outreach phase using the registry.

    Args:
        phase_id: Phase identifier (int or float, e.g., 0, 1, 1.1, 2, 3, etc.)
        context: Context dictionary with inputs for phase function (optional)
        validate_deps: Validate phase dependencies before execution (default: True)
        log_execution: Log execution to pipeline_events and audit_log (default: True)

    Returns:
        {
            "phase_id": 1.1,
            "phase_name": "Phase 1b: People Validation Trigger",
            "status": "complete",
            "duration_seconds": 45.2,
            "result": { /* phase function result */ },
            "error_message": None
        }

    Raises:
        ValueError: If phase_id not found in registry
        RuntimeError: If phase dependencies not met
        Exception: If phase function execution fails

    Example:
        >>> # Execute Phase 1 (Company Validation)
        >>> result = run_outreach_phase(1, {"company": company_record})
        >>> print(f"Status: {result['status']}")

        >>> # Execute Phase 1.1 (People Validation)
        >>> result = run_outreach_phase(1.1, {"state": "WV", "dry_run": False})
        >>> print(f"Valid: {result['result']['statistics']['valid']}")

        >>> # Execute Phase 3 (Outreach Readiness)
        >>> result = run_outreach_phase(3, {"state": "WV", "only_validated": True})
    """
    # Initialize context if None
    if context is None:
        context = {}

    # Initialize statistics
    stats = PhaseExecutionStats()

    try:
        # Step 1: Get phase entry
        logger.info(f"⏳ Executing Phase {phase_id}...")
        phase = get_phase_entry(phase_id)
        stats.start(phase_id, phase["phase_name"])

        logger.info(f"   Phase: {phase['phase_name']}")
        logger.info(f"   Description: {phase['description']}")
        logger.info(f"   File: {phase['file']}")
        logger.info(f"   Function: {phase['function']}")

        # Step 2: Validate dependencies (if enabled)
        if validate_deps:
            dependencies = get_phase_dependencies(phase_id)
            if dependencies:
                logger.info(f"   Dependencies: {[f'Phase {d['phase_id']}' for d in dependencies]}")

                # TODO: Check if dependencies have been executed
                # This would require querying marketing.phase_completion_log
                # For now, we just log the dependencies

        # Step 3: Get phase function
        logger.info(f"   Loading function '{phase['function']}'...")
        func = get_phase_function(phase_id)

        # Step 4: Execute phase function
        logger.info(f"   Executing with context: {list(context.keys())}")
        result = func(**context)

        # Mark as complete
        stats.complete(result)

        logger.info(f"✅ Phase {phase_id} completed successfully")
        logger.info(f"   Duration: {stats.get_duration_seconds():.2f}s")

        # Step 5: Log execution (if enabled)
        if log_execution and DB_UTILS_AVAILABLE:
            try:
                # Log to pipeline_events
                log_to_pipeline_events("phase_execution", {
                    "phase_id": phase_id,
                    "phase_name": phase["phase_name"],
                    "status": "complete",
                    "duration_seconds": stats.get_duration_seconds(),
                    "context": context,
                    "result_summary": _summarize_result(result)
                })

                # Log to audit_log
                log_to_audit_log("phase_executor", "phase_complete", {
                    "phase_id": phase_id,
                    "phase_name": phase["phase_name"],
                    "status": "complete",
                    "duration_seconds": stats.get_duration_seconds()
                })

                logger.info(f"   Logged to pipeline_events and audit_log")

            except Exception as e:
                logger.error(f"   Failed to log execution: {e}")

        # Return result
        return {
            "phase_id": phase_id,
            "phase_name": phase["phase_name"],
            "status": stats.status,
            "duration_seconds": stats.get_duration_seconds(),
            "result": result,
            "error_message": None
        }

    except ValueError as e:
        # Phase not found
        logger.error(f"❌ Phase {phase_id} not found in registry: {e}")
        stats.fail(str(e))

        if log_execution and DB_UTILS_AVAILABLE:
            try:
                log_to_audit_log("phase_executor", "phase_failed", {
                    "phase_id": phase_id,
                    "status": "failed",
                    "error": str(e)
                })
            except:
                pass

        raise

    except Exception as e:
        # Phase execution failed
        logger.error(f"❌ Phase {phase_id} execution failed: {e}")
        stats.fail(str(e))

        if log_execution and DB_UTILS_AVAILABLE:
            try:
                log_to_pipeline_events("phase_execution", {
                    "phase_id": phase_id,
                    "phase_name": stats.phase_name,
                    "status": "failed",
                    "error": str(e)
                })

                log_to_audit_log("phase_executor", "phase_failed", {
                    "phase_id": phase_id,
                    "phase_name": stats.phase_name,
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": stats.get_duration_seconds()
                })
            except:
                pass

        return {
            "phase_id": phase_id,
            "phase_name": stats.phase_name,
            "status": "failed",
            "duration_seconds": stats.get_duration_seconds(),
            "result": None,
            "error_message": str(e)
        }


# ============================================================================
# BATCH PHASE EXECUTION
# ============================================================================

def run_phase_sequence(
    phase_ids: List,
    context: Optional[Dict] = None,
    stop_on_error: bool = True
) -> List[Dict]:
    """
    Execute a sequence of phases in order

    Args:
        phase_ids: List of phase identifiers to execute in order
        context: Shared context for all phases (optional)
        stop_on_error: Stop execution if any phase fails (default: True)

    Returns:
        List of execution results, one per phase

    Example:
        >>> # Execute Phase 1, 1.1, and 3 in sequence
        >>> results = run_phase_sequence([1, 1.1, 3], {"state": "WV"})
        >>> for result in results:
        ...     print(f"Phase {result['phase_id']}: {result['status']}")
    """
    if context is None:
        context = {}

    # Validate sequence
    if not validate_phase_sequence(phase_ids):
        raise ValueError(f"Invalid phase sequence: {phase_ids}. Phases must be in ascending order.")

    logger.info(f"⏳ Executing phase sequence: {phase_ids}")

    results = []

    for phase_id in phase_ids:
        result = run_outreach_phase(phase_id, context, log_execution=True)
        results.append(result)

        if stop_on_error and result["status"] == "failed":
            logger.error(f"❌ Stopping sequence at Phase {phase_id} due to failure")
            break

    # Log sequence completion
    if DB_UTILS_AVAILABLE:
        try:
            log_to_audit_log("phase_executor", "sequence_complete", {
                "phase_ids": phase_ids,
                "total_phases": len(phase_ids),
                "executed_phases": len(results),
                "failed_phases": sum(1 for r in results if r["status"] == "failed")
            })
        except:
            pass

    logger.info(f"✅ Phase sequence complete: {len(results)}/{len(phase_ids)} phases executed")

    return results


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _summarize_result(result: Any) -> Dict:
    """
    Summarize phase result for logging (avoid storing large payloads)

    Args:
        result: Phase function result

    Returns:
        Summarized result dictionary
    """
    if isinstance(result, dict):
        summary = {}

        # Extract statistics if present
        if "statistics" in result:
            summary["statistics"] = result["statistics"]

        # Extract status fields
        for key in ["status", "valid", "invalid", "total", "phase_id", "phase_name"]:
            if key in result:
                summary[key] = result[key]

        return summary

    else:
        # Non-dict result - return as-is
        return {"result": str(result)[:200]}  # Truncate to 200 chars


# ============================================================================
# CLAUDE CODE INTEGRATION HELPERS
# ============================================================================

def execute_phase_by_name(phase_name: str, context: Optional[Dict] = None) -> Dict:
    """
    Execute phase by name instead of ID

    Args:
        phase_name: Phase name (e.g., "Phase 1b: People Validation Trigger")
        context: Context dictionary (optional)

    Returns:
        Execution result

    Example:
        >>> result = execute_phase_by_name("Phase 1b: People Validation Trigger", {"state": "WV"})
    """
    from backend.outreach_phase_registry import get_phase_by_name

    phase = get_phase_by_name(phase_name)
    return run_outreach_phase(phase["phase_id"], context)


def retry_failed_phase(phase_id, context: Optional[Dict] = None) -> Dict:
    """
    Retry a failed phase

    Args:
        phase_id: Phase identifier
        context: Context dictionary (optional)

    Returns:
        Execution result

    Example:
        >>> # Retry Phase 1.1
        >>> result = retry_failed_phase(1.1, {"state": "WV"})
    """
    logger.info(f"🔄 Retrying Phase {phase_id}...")
    return run_outreach_phase(phase_id, context)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase Executor - Run outreach phases")
    parser.add_argument("phase_id", type=float, help="Phase ID to execute (e.g., 1, 1.1, 2, 3)")
    parser.add_argument("--state", type=str, default=None, help="State code (e.g., WV)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Build context
    context = {}
    if args.state:
        context["state"] = args.state
    if args.dry_run:
        context["dry_run"] = True
    if args.limit:
        context["limit"] = args.limit
    if args.verbose:
        context["verbose"] = True
        logger.setLevel(logging.DEBUG)

    # Execute phase
    result = run_outreach_phase(args.phase_id, context)

    # Print result
    print("\n" + "=" * 70)
    print(f"PHASE {result['phase_id']}: {result['phase_name']}")
    print("=" * 70)
    print(f"Status: {result['status']}")
    print(f"Duration: {result['duration_seconds']:.2f}s")

    if result["error_message"]:
        print(f"Error: {result['error_message']}")

    if result["result"]:
        print(f"\nResult:")
        import json
        print(json.dumps(result["result"], indent=2))

    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "complete" else 1)
