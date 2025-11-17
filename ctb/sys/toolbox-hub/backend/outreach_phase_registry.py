"""
Outreach Phase Registry - Barton Toolbox Hub

Maps each phase of the outreach pipeline to a callable Claude reference.
Used for error handling, retries, and phase-based execution tracking.

Phase Flow:
0. Intake Load → 1. Company Validation → 2. Person Validation →
3. Outreach Readiness → 4. BIT Trigger Check → 5. BIT Score Calculation →
6. Promotion to Outreach Log

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
        "phase_id": 2,
        "phase_name": "Person Validation",
        "description": "Checks LinkedIn, email, title, and company link",
        "file": "backend/validator/validation_rules.py",
        "function": "validate_person",
        "status": "implemented",
        "input_table": "marketing.people_master",
        "output_table": "marketing.people_master (validation_status)",
        "error_routing": "n8n webhook → Google Sheets (Invalid_People)",
        "dependencies": [1],  # Requires Phase 1 (Company Validation)
        "estimated_duration_seconds": 2,
        "validation_rules": 7,
        "severity_levels": ["CRITICAL", "ERROR", "WARNING"]
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
        "status": "planned",
        "input_table": "marketing.company_master (outreach_ready = true)",
        "output_table": "bit.events",
        "error_routing": "shq.error_master",
        "dependencies": [3],  # Requires Phase 3 (Outreach Readiness)
        "estimated_duration_seconds": 3,
        "signal_types": ["Movement", "Funding", "Hiring", "Tech Stack Change", "Leadership Change"]
    },
    {
        "phase_id": 5,
        "phase_name": "BIT Score Calculation",
        "description": "Assigns score based on context, timing, and movement patterns",
        "file": "backend/bit_engine/bit_score.py",
        "function": "calculate_bit_score",
        "status": "planned",
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
        }
    },
    {
        "phase_id": 6,
        "phase_name": "Promotion to Outreach Log",
        "description": "Moves ready contacts into outreach queue with campaign metadata",
        "file": "backend/outreach/promote_to_log.py",
        "function": "promote_contact_to_outreach",
        "status": "planned",
        "input_table": "bit.company_scores (score >= 50)",
        "output_table": "marketing.outreach_log",
        "error_routing": "shq.error_master",
        "dependencies": [5],  # Requires Phase 5 (BIT Score Calculation)
        "estimated_duration_seconds": 2,
        "campaign_metadata": ["campaign_id", "sequence_id", "personalization_template", "send_date"]
    }
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_phase_entry(phase_id: int) -> Dict:
    """
    Get phase entry by phase_id

    Args:
        phase_id: Phase identifier (0-6)

    Returns:
        Phase entry dictionary

    Raises:
        ValueError: If phase_id not found

    Example:
        >>> phase = get_phase_entry(2)
        >>> print(phase['phase_name'])
        'Person Validation'
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


# ============================================================================
# DOCTRINE INTEGRATION
# ============================================================================

DOCTRINE_ENTRY = {
    "doctrine_id": "04.04.02.04.ple.validation_pipeline",
    "description": "Outreach validation and enrichment lifecycle. Each phase represents a callable unit tracked via phase_id for Claude execution and error handling.",
    "phases": [0, 1, 2, 3, 4, 5, 6],
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
    "version": "04"
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

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("OUTREACH PHASE REGISTRY - TEST")
    print("=" * 70)

    # Test 1: Get all phases
    print("\n[Test 1] All Phases:")
    for phase in get_all_phases():
        status_icon = "✅" if phase["status"] == "implemented" else "📋"
        print(f"  {status_icon} Phase {phase['phase_id']}: {phase['phase_name']} ({phase['status']})")

    # Test 2: Get phase by ID
    print("\n[Test 2] Get Phase by ID (phase_id=2):")
    phase = get_phase_entry(2)
    print(f"  Phase ID: {phase['phase_id']}")
    print(f"  Phase Name: {phase['phase_name']}")
    print(f"  Description: {phase['description']}")
    print(f"  File: {phase['file']}")
    print(f"  Function: {phase['function']}")
    print(f"  Status: {phase['status']}")

    # Test 3: Get phase by name
    print("\n[Test 3] Get Phase by Name ('Person Validation'):")
    phase = get_phase_by_name("Person Validation")
    print(f"  Phase ID: {phase['phase_id']}")
    print(f"  File: {phase['file']}")
    print(f"  Function: {phase['function']}")

    # Test 4: Get implemented phases
    print("\n[Test 4] Implemented Phases:")
    for phase in get_implemented_phases():
        print(f"  ✅ Phase {phase['phase_id']}: {phase['phase_name']}")

    # Test 5: Get planned phases
    print("\n[Test 5] Planned Phases:")
    for phase in get_planned_phases():
        print(f"  📋 Phase {phase['phase_id']}: {phase['phase_name']}")

    # Test 6: Get phase dependencies
    print("\n[Test 6] Dependencies for Phase 3 (Outreach Readiness):")
    deps = get_phase_dependencies(3)
    for dep in deps:
        print(f"  → Phase {dep['phase_id']}: {dep['phase_name']}")

    # Test 7: Get next phase
    print("\n[Test 7] Next Phase after Phase 2:")
    next_phase = get_next_phase(2)
    print(f"  → Phase {next_phase['phase_id']}: {next_phase['phase_name']}")

    # Test 8: Validate phase sequence
    print("\n[Test 8] Validate Phase Sequences:")
    valid_seq = [1, 2, 3]
    invalid_seq = [3, 1, 2]
    print(f"  [1, 2, 3] is valid: {validate_phase_sequence(valid_seq)}")
    print(f"  [3, 1, 2] is valid: {validate_phase_sequence(invalid_seq)}")

    # Test 9: Get phase status summary
    print("\n[Test 9] Phase Status Summary:")
    summary = get_phase_status_summary()
    print(f"  Total Phases: {summary['total']}")
    print(f"  Implemented: {summary['implemented']}")
    print(f"  Planned: {summary['planned']}")
    print(f"  Completion: {summary['completion_pct']}%")

    # Test 10: Get doctrine entry
    print("\n[Test 10] Doctrine Entry:")
    doctrine = get_doctrine_entry()
    print(f"  Doctrine ID: {doctrine['doctrine_id']}")
    print(f"  Description: {doctrine['description']}")
    print(f"  Phases: {doctrine['phases']}")

    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
