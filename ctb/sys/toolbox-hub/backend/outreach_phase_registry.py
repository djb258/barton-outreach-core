"""
Outreach Phase Registry - Barton Toolbox Hub

Maps each phase of the outreach pipeline to a callable Claude reference.
Used for error handling, retries, and phase-based execution tracking.

Phase Flow (Updated 2025-11-25):
0. Intake Load → 1. Company Validation → 1.1 People Validation →
1.5 Three-Tier Enrichment Waterfall → 2 Person Validation →
2.5 3/3 Slot Completion Gate → 3 Outreach Readiness →
4. BIT Trigger Check → 5. BIT Score Calculation → 6. Promotion to Outreach Log

NEW PHASES ADDED:
- Phase 1.5: Three-Tier Enrichment Waterfall (Tier 1: $0.20, Tier 2: $1.50, Tier 3: $3.00)
- Phase 2.5: 3/3 Slot Completion Gate (blocks outreach until CEO+CFO+HR filled)

Usage:
    from backend.outreach_phase_registry import get_phase_entry, OUTREACH_PHASES

    # Get phase details
    phase = get_phase_entry(2)
    print(f"Phase 2: {phase['phase_name']}")  # "Person Validation"

    # Import and execute phase function
    module = __import__(phase['file'].replace('/', '.').replace('.py', ''), fromlist=[phase['function']])
    func = getattr(module, phase['function'])
    result = func(company_id)

Integration Points:
- shq.error_master.phase_id - Error tracking by phase
- marketing.pipeline_events.phase_id - Event logging by phase
- Claude Code - Manual override trigger
- marketing.company_manual_override - Manual entry table

Status: ✅ Production Ready
Date: 2025-11-17
"""

from typing import Dict, List, Optional

# ============================================================================
# OUTREACH PHASE REGISTRY
# ============================================================================

OUTREACH_PHASES = [
    {
        "phase_id": 0,
        "phase_name": "Intake Load",
        "description": "Initial data insert from Apollo/CSV",
        "file": "backend/intake/load_intake_data.py",
        "function": "load_raw_records",
        "status": "planned",
        "input_table": "intake.company_raw_intake",
        "output_table": "marketing.company_master",
        "error_routing": "shq.error_master",
        "dependencies": [],
        "estimated_duration_seconds": 30
    },
    {
        "phase_id": 1,
        "phase_name": "Company Validation",
        "description": "Checks structure, size, LinkedIn, and slot presence",
        "file": "backend/validator/validation_rules.py",
        "function": "validate_company",
        "status": "implemented",
        "input_table": "marketing.company_master",
        "output_table": "marketing.company_master (validation_status)",
        "error_routing": "n8n webhook → Google Sheets (Invalid_Companies)",
        "dependencies": [],
        "estimated_duration_seconds": 2,
        "validation_rules": 5,
        "severity_levels": ["CRITICAL", "ERROR", "WARNING"]
    },
    {
        "phase_id": 1.1,
        "phase_name": "Phase 1b: People Validation Trigger",
        "description": "Claude-callable orchestrator for people validation. Validates people data for outreach readiness.",
        "file": "backend/validator/phase1b_people_trigger.py",
        "function": "run_phase1b_people_validation",
        "status": "implemented",
        "input_table": "marketing.people_master",
        "output_table": "marketing.people_master (validation_status)",
        "error_routing": "n8n webhook → Google Sheets (Invalid_People)",
        "dependencies": [1],  # Requires Phase 1 (Company Validation)
        "estimated_duration_seconds": 2,
        "validation_rules": 7,
        "severity_levels": ["CRITICAL", "ERROR", "WARNING"],
        "doctrine_id": "4.svg.marketing.ple.phase1b_people_validator",
        "webhook_url": "https://n8n.barton.com/webhook/route-person-failure",
        "google_sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
        "google_sheet_tab": "Invalid_People",
        "failure_schema": ["title mismatch", "missing email", "no LinkedIn URL", "bad format or missing timestamp", "not linked to company"]
    },
    {
        "phase_id": 1.5,
        "phase_name": "Three-Tier Enrichment Waterfall",
        "description": "Cost-optimized enrichment through three tiers: Tier 1 ($0.20), Tier 2 ($1.50), Tier 3 ($3.00)",
        "file": "backend/enrichment/three_tier_waterfall.py",
        "function": "enrich_entity",
        "status": "implemented",
        "input_table": "marketing.company_master / marketing.people_master",
        "output_table": "marketing.data_enrichment_log",
        "error_routing": "shq.error_master",
        "dependencies": [1],  # Requires Phase 1 (Company Validation)
        "estimated_duration_seconds": 10,
        "doctrine_id": "04.04.02.04.15000.001",
        "tiers": {
            "tier_1": {
                "name": "Cheap & Wide",
                "cost": 0.20,
                "success_rate": 0.80,
                "providers": ["Firecrawl", "SerpAPI", "Clearbit Lite"]
            },
            "tier_2": {
                "name": "Mid-Cost Selective",
                "cost": 1.50,
                "success_rate": 0.15,
                "providers": ["Abacus.ai", "Clay", "People Data APIs"]
            },
            "tier_3": {
                "name": "Expensive Precision",
                "cost": 3.00,
                "success_rate": 0.05,
                "providers": ["RocketReach", "PDL", "Apify"]
            }
        }
    },
    {
        "phase_id": 2,
        "phase_name": "Person Validation (Low-Level)",
        "description": "Low-level function: Checks LinkedIn, email, title, and company link (single person record)",
        "file": "backend/validator/validation_rules.py",
        "function": "validate_person",
        "status": "implemented",
        "input_table": "marketing.people_master (single record)",
        "output_table": "Dict result (not database)",
        "error_routing": "Returns validation result",
        "dependencies": [1],  # Requires Phase 1 (Company Validation)
        "estimated_duration_seconds": 0.01,
        "validation_rules": 7,
        "severity_levels": ["CRITICAL", "ERROR", "WARNING"],
        "note": "This is the low-level validation function. Use Phase 1.1 for batch processing."
    },
    {
        "phase_id": 2.5,
        "phase_name": "3/3 Slot Completion Gate",
        "description": "BLOCKING GATE: Requires all 3 executive slots (CEO, CFO, HR) filled before outreach",
        "file": "backend/gates/slot_completion_gate.py",
        "function": "check_slot_completion",
        "status": "implemented",
        "input_table": "marketing.company_slot",
        "output_table": "Gate decision (pass/wait)",
        "error_routing": "n8n webhook → Google Sheets (Enrichment_Queue)",
        "dependencies": [1.5, 2],  # Requires Enrichment and Person Validation
        "estimated_duration_seconds": 1,
        "doctrine_id": "04.04.02.04.25000.001",
        "gate_type": "blocking",
        "required_slots": ["CEO", "CFO", "HR"],
        "slot_messaging": {
            "CEO": "Cost/ROI messaging for executive buy-in",
            "CFO": "Budget/financial justification messaging",
            "HR": "Service/efficiency messaging for operational support"
        },
        "on_fail": "Return to enrichment waterfall for missing slots"
    },
    {
        "phase_id": 3,
        "phase_name": "Outreach Readiness Evaluation",
        "description": "Checks slot fills, enrichment, verified emails, and title matches",
        "file": "backend/enrichment/evaluate_outreach_readiness.py",
        "function": "evaluate_company_readiness",
        "status": "implemented",
        "input_table": "marketing.company_master (validation_status = 'valid')",
        "output_table": "marketing.company_master (outreach_ready)",
        "error_routing": "marketing.pipeline_events",
        "dependencies": [1, 2],  # Requires Phase 1 + Phase 2
        "estimated_duration_seconds": 5,
        "checks_per_company": 15,  # 5 checks × 3 slots (CEO, CFO, HR)
        "failure_categories": ["Slot Not Filled", "Enrichment Missing", "Email Not Verified", "Title Mismatch"]
    },
    {
        "phase_id": 4,
        "phase_name": "BIT Trigger Check",
        "description": "Evaluates if outreach-ready contacts meet BIT signal thresholds",
        "file": "backend/bit_engine/bit_trigger.py",
        "function": "check_bit_trigger_conditions",
        "status": "implemented",
        "input_table": "marketing.company_master (outreach_ready = true)",
        "output_table": "bit.events",
        "error_routing": "shq.error_master",
        "dependencies": [3],  # Requires Phase 3 (Outreach Readiness)
        "estimated_duration_seconds": 3,
        "signal_types": ["Executive Movement", "Funding Round", "Hiring Spree", "Tech Stack Change", "Leadership Change"],
        "doctrine_id": "4.svg.marketing.ple.bit_trigger_check"
    },
    {
        "phase_id": 5,
        "phase_name": "BIT Score Calculation",
        "description": "Assigns score based on context, timing, and movement patterns",
        "file": "backend/bit_engine/bit_score.py",
        "function": "calculate_bit_score",
        "status": "implemented",
        "input_table": "bit.events",
        "output_table": "bit.company_scores",
        "error_routing": "shq.error_master",
        "dependencies": [4],  # Requires Phase 4 (BIT Trigger Check)
        "estimated_duration_seconds": 2,
        "score_range": [0, 100],
        "thresholds": {
            "hot": 75,
            "warm": 50,
            "cold": 25
        },
        "doctrine_id": "4.svg.marketing.ple.bit_score_calc"
    },
    {
        "phase_id": 6,
        "phase_name": "Promotion to Outreach Log",
        "description": "Moves ready contacts into outreach queue with campaign metadata",
        "file": "backend/outreach/promote_to_log.py",
        "function": "promote_contact_to_outreach",
        "status": "implemented",
        "input_table": "bit.company_scores (score >= 50)",
        "output_table": "marketing.outreach_log",
        "error_routing": "shq.error_master",
        "dependencies": [5],  # Requires Phase 5 (BIT Score Calculation)
        "estimated_duration_seconds": 2,
        "campaign_metadata": ["campaign_id", "sequence_id", "personalization_template", "send_date"],
        "doctrine_id": "4.svg.marketing.ple.outreach_promotion"
    }
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_phase_entry(phase_id) -> Dict:
    """
    Get phase entry by phase_id

    Args:
        phase_id: Phase identifier (int or float, e.g., 0, 1, 1.1, 2, 3, etc.)

    Returns:
        Phase entry dictionary

    Raises:
        ValueError: If phase_id not found

    Example:
        >>> phase = get_phase_entry(2)
        >>> print(phase['phase_name'])
        'Person Validation (Low-Level)'

        >>> phase = get_phase_entry(1.1)
        >>> print(phase['phase_name'])
        'Phase 1b: People Validation Trigger'
    """
    for phase in OUTREACH_PHASES:
        if phase["phase_id"] == phase_id:
            return phase
    raise ValueError(f"Phase ID {phase_id} not found in registry.")


def get_phase_by_name(phase_name: str) -> Dict:
    """
    Get phase entry by phase_name (case-insensitive)

    Args:
        phase_name: Phase name (e.g., "Person Validation")

    Returns:
        Phase entry dictionary

    Raises:
        ValueError: If phase_name not found

    Example:
        >>> phase = get_phase_by_name("Person Validation")
        >>> print(phase['phase_id'])
        2
    """
    phase_name_upper = phase_name.upper()
    for phase in OUTREACH_PHASES:
        if phase["phase_name"].upper() == phase_name_upper:
            return phase
    raise ValueError(f"Phase name '{phase_name}' not found in registry.")


def get_all_phases() -> List[Dict]:
    """
    Get all phases in order

    Returns:
        List of all phase dictionaries

    Example:
        >>> phases = get_all_phases()
        >>> for phase in phases:
        ...     print(f"{phase['phase_id']}: {phase['phase_name']}")
        0: Intake Load
        1: Company Validation
        2: Person Validation
        ...
    """
    return OUTREACH_PHASES.copy()


def get_implemented_phases() -> List[Dict]:
    """
    Get only implemented phases

    Returns:
        List of implemented phase dictionaries

    Example:
        >>> phases = get_implemented_phases()
        >>> print([p['phase_name'] for p in phases])
        ['Company Validation', 'Person Validation', 'Outreach Readiness Evaluation']
    """
    return [phase for phase in OUTREACH_PHASES if phase.get("status") == "implemented"]


def get_planned_phases() -> List[Dict]:
    """
    Get only planned (not yet implemented) phases

    Returns:
        List of planned phase dictionaries

    Example:
        >>> phases = get_planned_phases()
        >>> print([p['phase_name'] for p in phases])
        ['Intake Load', 'BIT Trigger Check', 'BIT Score Calculation', 'Promotion to Outreach Log']
    """
    return [phase for phase in OUTREACH_PHASES if phase.get("status") == "planned"]


def get_phase_dependencies(phase_id: int) -> List[Dict]:
    """
    Get all dependency phases for a given phase_id

    Args:
        phase_id: Phase identifier (0-6)

    Returns:
        List of dependency phase dictionaries

    Example:
        >>> deps = get_phase_dependencies(3)  # Outreach Readiness
        >>> print([d['phase_name'] for d in deps])
        ['Company Validation', 'Person Validation']
    """
    phase = get_phase_entry(phase_id)
    dependency_ids = phase.get("dependencies", [])
    return [get_phase_entry(dep_id) for dep_id in dependency_ids]


def get_next_phase(phase_id: int) -> Optional[Dict]:
    """
    Get the next phase in the pipeline

    Args:
        phase_id: Current phase identifier (0-6)

    Returns:
        Next phase dictionary or None if last phase

    Example:
        >>> next_phase = get_next_phase(2)
        >>> print(next_phase['phase_name'])
        'Outreach Readiness Evaluation'
    """
    if phase_id >= len(OUTREACH_PHASES) - 1:
        return None
    return get_phase_entry(phase_id + 1)


def validate_phase_sequence(phase_ids: List[int]) -> bool:
    """
    Validate that a sequence of phase_ids is in correct order

    Args:
        phase_ids: List of phase identifiers

    Returns:
        True if sequence is valid, False otherwise

    Example:
        >>> validate_phase_sequence([1, 2, 3])
        True
        >>> validate_phase_sequence([3, 1, 2])
        False
    """
    if not phase_ids:
        return True

    for i in range(len(phase_ids) - 1):
        if phase_ids[i] >= phase_ids[i + 1]:
            return False

    return True


def get_phase_status_summary() -> Dict:
    """
    Get summary of phase implementation status

    Returns:
        Dictionary with counts of implemented vs planned phases

    Example:
        >>> summary = get_phase_status_summary()
        >>> print(summary)
        {'total': 7, 'implemented': 3, 'planned': 4, 'completion_pct': 42.86}
    """
    total = len(OUTREACH_PHASES)
    implemented = len(get_implemented_phases())
    planned = len(get_planned_phases())

    return {
        "total": total,
        "implemented": implemented,
        "planned": planned,
        "completion_pct": round((implemented / total) * 100, 2)
    }


# ============================================================================
# PHASE EXECUTION HELPERS (For Claude Code)
# ============================================================================

def get_phase_function(phase_id: int):
    """
    Dynamically import and return the phase function

    Args:
        phase_id: Phase identifier (0-6)

    Returns:
        Function object for the phase

    Raises:
        ImportError: If module cannot be imported
        AttributeError: If function not found in module
        ValueError: If phase_id not found

    Example:
        >>> validate_company = get_phase_function(1)
        >>> result = validate_company(company_record)
    """
    phase = get_phase_entry(phase_id)

    # Convert file path to module path
    # "backend/validator/validation_rules.py" → "backend.validator.validation_rules"
    module_path = phase["file"].replace("/", ".").replace(".py", "")

    # Import module
    try:
        module = __import__(module_path, fromlist=[phase["function"]])
    except ImportError as e:
        raise ImportError(f"Failed to import module '{module_path}': {e}")

    # Get function
    try:
        func = getattr(module, phase["function"])
    except AttributeError as e:
        raise AttributeError(f"Function '{phase['function']}' not found in module '{module_path}': {e}")

    return func


def execute_phase(phase_id: int, *args, **kwargs):
    """
    Execute a phase function with given arguments

    Args:
        phase_id: Phase identifier (0-6)
        *args: Positional arguments for phase function
        **kwargs: Keyword arguments for phase function

    Returns:
        Result of phase function execution

    Example:
        >>> # Execute Phase 2 (Person Validation)
        >>> result = execute_phase(2, person_record, valid_company_ids)
        >>> print(result['valid'])
        True
    """
    func = get_phase_function(phase_id)
    return func(*args, **kwargs)


def execute_all_phases(state: str, dry_run: bool = False) -> Dict:
    """
    Execute all implemented phases sequentially for a given state

    This function:
    - Retrieves all implemented phases from the registry
    - Executes them in order (sorted by phase_id)
    - Collects results and errors for each phase
    - Returns summary of all phase executions

    Args:
        state: State code (e.g., "WV", "CA")
        dry_run: If True, execute in dry-run mode (no database writes)

    Returns:
        {
            "state": "WV",
            "dry_run": True,
            "total_phases": 7,
            "successful": 6,
            "failed": 1,
            "phases": [
                {
                    "phase_id": 0,
                    "phase_name": "Company Structure Validation",
                    "statistics": {...}
                },
                {
                    "phase_id": 1,
                    "phase_name": "Phase 1: Outreach Readiness Evaluator",
                    "error": "Database connection failed"
                },
                ...
            ]
        }

    Example:
        >>> # Execute all phases for West Virginia
        >>> result = execute_all_phases(state="WV", dry_run=True)
        >>> print(f"Executed {result['total_phases']} phases")
        >>> print(f"Success: {result['successful']}, Failed: {result['failed']}")

        >>> # Production run
        >>> result = execute_all_phases(state="CA", dry_run=False)
    """
    print("=" * 70)
    print(f"EXECUTING ALL PHASES FOR STATE: {state}")
    print(f"Dry-run: {dry_run}")
    print("=" * 70)
    print()

    results = []
    successful = 0
    failed = 0

    # Get all implemented phases, sorted by phase_id
    implemented_phases = sorted(get_implemented_phases(), key=lambda p: p["phase_id"])

    for phase in implemented_phases:
        phase_id = phase["phase_id"]
        phase_name = phase["phase_name"]

        try:
            print(f"🔁 Executing Phase {phase_id}: {phase_name}")

            # Get the phase function
            func = get_phase_function(phase_id)

            # Prepare arguments (all phases accept state and dry_run)
            args = {"state": state, "dry_run": dry_run}

            # Execute the phase
            result = func(**args)

            # Extract statistics from result
            statistics = result.get("statistics", {})

            results.append({
                "phase_id": phase_id,
                "phase_name": phase_name,
                "status": "success",
                "statistics": statistics
            })

            successful += 1
            print(f"✅ Phase {phase_id} completed successfully")

            # Print key statistics if available
            if statistics:
                for key, value in list(statistics.items())[:3]:  # Show first 3 stats
                    print(f"   {key}: {value}")

            print()

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error in Phase {phase_id}: {error_msg}")
            print()

            results.append({
                "phase_id": phase_id,
                "phase_name": phase_name,
                "status": "failed",
                "error": error_msg
            })

            failed += 1

    # Summary
    print("=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    print(f"State:           {state}")
    print(f"Dry-run:         {dry_run}")
    print(f"Total Phases:    {len(results)}")
    print(f"Successful:      {successful}")
    print(f"Failed:          {failed}")
    print("=" * 70)

    return {
        "state": state,
        "dry_run": dry_run,
        "total_phases": len(results),
        "successful": successful,
        "failed": failed,
        "phases": results
    }


# ============================================================================
# DOCTRINE INTEGRATION
# ============================================================================

DOCTRINE_ENTRY = {
    "doctrine_id": "04.04.02.04.ple.validation_pipeline",
    "description": "Outreach validation and enrichment lifecycle. Each phase represents a callable unit tracked via phase_id for Claude execution and error handling.",
    "phases": [0, 1, 1.1, 2, 3, 4, 5, 6],
    "integration_points": {
        "error_log": "shq.error_master.phase_id",
        "event_log": "marketing.pipeline_events.phase_id",
        "override_trigger": "Claude Code",
        "manual_entry_table": "marketing.company_manual_override"
    },
    "barton_id_format": "04.04.02.04.XXXXX.###",
    "subhive": "04",
    "app": "outreach",
    "layer": "04",
    "schema": "02",
    "version": "04",
    "phase1b_doctrine": {
        "doctrine_id": "4.svg.marketing.ple.phase1b_people_validator",
        "description": "Validates people data for outreach readiness. Checks full_name, title, email, LinkedIn, company link, and timestamp. Logs to audit + routes to Invalid_People tab.",
        "trigger_phase": 1.1,
        "output": {
            "validation_status": ["valid", "invalid", "warning"],
            "webhook": "https://n8n.barton.com/webhook/route-person-failure",
            "sheet": {
                "id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
                "tab": "Invalid_People"
            }
        },
        "failure_schema": [
            "title mismatch",
            "missing email",
            "no LinkedIn URL",
            "bad format or missing timestamp",
            "not linked to company"
        ]
    }
}


def get_doctrine_entry() -> Dict:
    """
    Get the doctrine entry for this phase registry

    Returns:
        Doctrine entry dictionary

    Example:
        >>> doctrine = get_doctrine_entry()
        >>> print(doctrine['doctrine_id'])
        '04.04.02.04.ple.validation_pipeline'
    """
    return DOCTRINE_ENTRY.copy()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    import io
    import argparse
    import json

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # CLI argument parser
    parser = argparse.ArgumentParser(
        description="Outreach Phase Registry - Execute phases or run tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all implemented phases for West Virginia (dry-run)
  python outreach_phase_registry.py --state WV --dry-run

  # Run all implemented phases for California (production)
  python outreach_phase_registry.py --state CA

  # Run test suite
  python outreach_phase_registry.py --test

  # Get JSON output
  python outreach_phase_registry.py --state WV --dry-run --json
        """
    )

    parser.add_argument(
        "--state",
        type=str,
        help="State code to process (e.g., WV, CA)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no database writes)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test suite instead of executing phases"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Run test suite if --test flag is provided
    if args.test:
        print("=" * 70)
        print("OUTREACH PHASE REGISTRY - TEST SUITE")
        print("=" * 70)

        # Test 1: Get all phases
        print("\n[Test 1] All Phases:")
        for phase in get_all_phases():
            status_icon = "✅" if phase["status"] == "implemented" else "📋"
            print(f"  {status_icon} Phase {phase['phase_id']}: {phase['phase_name']} ({phase['status']})")

        # Test 2: Get implemented phases
        print("\n[Test 2] Implemented Phases:")
        for phase in get_implemented_phases():
            print(f"  ✅ Phase {phase['phase_id']}: {phase['phase_name']}")
            if phase.get('doctrine_id'):
                print(f"     Doctrine ID: {phase['doctrine_id']}")

        # Test 3: Get phase status summary
        print("\n[Test 3] Phase Status Summary:")
        summary = get_phase_status_summary()
        print(f"  Total Phases: {summary['total']}")
        print(f"  Implemented: {summary['implemented']}")
        print(f"  Planned: {summary['planned']}")
        print(f"  Completion: {summary['completion_pct']}%")

        # Test 4: Get doctrine entry
        print("\n[Test 4] Doctrine Entry:")
        doctrine = get_doctrine_entry()
        print(f"  Doctrine ID: {doctrine['doctrine_id']}")
        print(f"  Description: {doctrine['description']}")
        print(f"  Phases: {doctrine['phases']}")

        print("\n" + "=" * 70)
        print("✅ All tests complete!")
        print("=" * 70)

    # Execute all phases if state is provided
    elif args.state:
        result = execute_all_phases(state=args.state, dry_run=args.dry_run)

        # Output as JSON if --json flag is provided
        if args.json:
            print(json.dumps(result, indent=2))

    # Show help if no arguments provided
    else:
        parser.print_help()
