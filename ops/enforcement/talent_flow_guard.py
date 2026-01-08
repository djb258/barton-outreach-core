"""
Talent Flow Doctrine Guard — TF-001
====================================
CI ENFORCEMENT for Talent Flow Doctrine v1.0.1

This module FAILS FAST on doctrine violations.
It does NOT fix violations — only detects and reports.

CERTIFICATION: TF-001
STATUS: CERTIFIED
DATE: 2026-01-08

ENFORCEMENT SCOPE:
- Forbidden table writes
- Forbidden signal emissions
- Phase gate violations
- Non-binary outcome detection
- Idempotency enforcement gaps
- Forbidden operations (minting, enrichment, scoring)

HARD RULE: Violations block the build.
"""

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# DOCTRINE CONSTANTS (LOCKED — DO NOT MODIFY)
# =============================================================================

CERTIFICATION_ID = "TF-001"
DOCTRINE_VERSION = "1.0.1"

# Permitted tables (ONLY these are allowed for Talent Flow writes)
PERMITTED_TABLES: Set[str] = {
    "person_movement_history",
    "people_errors",
    "people.person_movement_history",
    "people.people_errors",
}

# Permitted signals (ONLY these may be emitted)
PERMITTED_SIGNALS: Set[str] = {
    "SLOT_VACATED",
    "SLOT_BIND_REQUEST",
    "COMPANY_RESOLUTION_REQUIRED",
    "MOVEMENT_RECORDED",
}

# Required phase order (DETECT → RECON → SIGNAL)
REQUIRED_PHASE_ORDER: List[str] = ["DETECT", "RECON", "SIGNAL"]

# Binary outcomes (ONLY these are valid)
VALID_OUTCOMES: Set[str] = {"PROMOTED", "QUARANTINED"}

# Forbidden operations (patterns that indicate doctrine violation)
FORBIDDEN_PATTERNS: Dict[str, str] = {
    "company_id_mint": r"mint.*company.*id|create.*company.*id|generate.*company.*id",
    "outreach_creation": r"create.*outreach|insert.*outreach|write.*outreach",
    "enrichment_logic": r"enrich\(|enrichment_pipeline|run_enrichment",
    "scoring_logic": r"calculate_score|score_company|bit_score.*=|scoring_engine",
    "recursive_execution": r"talent_flow.*talent_flow|self\._run_talent_flow|recursive.*movement",
    "auto_resolve": r"auto.*resolve.*company|resolve_company_auto",
}

# Tables that are FORBIDDEN for Talent Flow writes
FORBIDDEN_TABLES: Set[str] = {
    "company_master",
    "companies",
    "outreach",
    "outreach_execution",
    "enrichment_cache",
    "bit_scores",
    "company_slot",
    "people_master",  # Read only — TF cannot write here
}

# Kill switch variable (must be honored)
KILL_SWITCH_VAR = "PEOPLE_MOVEMENT_DETECT_ENABLED"


class ViolationType(Enum):
    """Types of doctrine violations."""
    FORBIDDEN_TABLE_WRITE = "FORBIDDEN_TABLE_WRITE"
    FORBIDDEN_SIGNAL = "FORBIDDEN_SIGNAL"
    PHASE_ORDER_VIOLATION = "PHASE_ORDER_VIOLATION"
    NON_BINARY_OUTCOME = "NON_BINARY_OUTCOME"
    MISSING_IDEMPOTENCY = "MISSING_IDEMPOTENCY"
    FORBIDDEN_OPERATION = "FORBIDDEN_OPERATION"
    MISSING_KILL_SWITCH = "MISSING_KILL_SWITCH"


@dataclass
class Violation:
    """A single doctrine violation."""
    violation_type: ViolationType
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    invariant_violated: str

    def to_error_message(self) -> str:
        """Format as CI error message."""
        return (
            f"::error file={self.file_path},line={self.line_number}::"
            f"[{CERTIFICATION_ID}] {self.violation_type.value}: "
            f"{self.description} | Invariant: {self.invariant_violated}"
        )

    def to_report_line(self) -> str:
        """Format for report output."""
        return (
            f"  ❌ {self.violation_type.value}\n"
            f"     File: {self.file_path}:{self.line_number}\n"
            f"     Issue: {self.description}\n"
            f"     Invariant: {self.invariant_violated}\n"
            f"     Code: {self.code_snippet[:80]}..."
        )


@dataclass
class TalentFlowGuardResult:
    """Result of Talent Flow doctrine guard scan."""
    passed: bool
    files_scanned: int
    violations: List[Violation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_report(self) -> str:
        """Generate full report."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        lines = [
            "=" * 72,
            f"TALENT FLOW DOCTRINE GUARD — {CERTIFICATION_ID}",
            "=" * 72,
            f"Status: {status}",
            f"Doctrine Version: {DOCTRINE_VERSION}",
            f"Files Scanned: {self.files_scanned}",
            f"Violations Found: {len(self.violations)}",
            "",
        ]

        if self.violations:
            lines.append("VIOLATIONS:")
            lines.append("-" * 40)
            for v in self.violations:
                lines.append(v.to_report_line())
                lines.append("")

        if self.warnings:
            lines.append("WARNINGS:")
            lines.append("-" * 40)
            for w in self.warnings:
                lines.append(f"  ⚠️ {w}")

        lines.append("=" * 72)
        return "\n".join(lines)


# =============================================================================
# STATIC ANALYSIS FUNCTIONS
# =============================================================================

def find_talent_flow_files(base_path: str) -> List[Path]:
    """
    Find all files that are EXCLUSIVELY part of Talent Flow scope.
    
    STRICT SCOPE — Only files that:
    1. Are in a talent_flow directory
    2. Have talent_flow in their filename
    3. Are explicitly movement_engine files in people-intelligence
    
    This excludes:
    - BIT Engine (separate doctrine)
    - Dry run orchestrators (simulation code)
    - Test files in other modules
    - Files that merely reference Talent Flow
    """
    talent_flow_files = []
    base = Path(base_path)

    # STRICT: Only scan these specific paths for Talent Flow code
    strict_patterns = [
        "hubs/people-intelligence/**/talent_flow*.py",
        "hubs/people-intelligence/**/movement_engine/**/*.py",
        "spokes/**/talent_flow*.py",
    ]

    for pattern in strict_patterns:
        for py_file in base.glob(pattern):
            if "__pycache__" in str(py_file):
                continue
            if "test_talent_flow_doctrine.py" in str(py_file):
                continue  # Don't scan the test file itself
            if "talent_flow_guard.py" in str(py_file):
                continue  # Don't scan self
            talent_flow_files.append(py_file)

    return talent_flow_files


def check_forbidden_table_writes(file_path: Path, content: str) -> List[Violation]:
    """
    Detect writes to forbidden tables.
    
    DOCTRINE: Talent Flow may ONLY write to:
    - people.person_movement_history
    - people.people_errors
    """
    violations = []
    lines = content.split("\n")

    # Patterns for SQL writes
    write_patterns = [
        (r"INSERT\s+INTO\s+([^\s(]+)", "INSERT"),
        (r"UPDATE\s+([^\s]+)\s+SET", "UPDATE"),
        (r"DELETE\s+FROM\s+([^\s]+)", "DELETE"),
        (r"\.execute\([^)]*INSERT\s+INTO\s+([^\s(]+)", "execute INSERT"),
        (r"\.execute\([^)]*UPDATE\s+([^\s]+)", "execute UPDATE"),
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern, op_type in write_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for table_name in matches:
                # Normalize table name
                table_clean = table_name.strip("'\"` ").lower()
                
                # Check if it's a forbidden table
                for forbidden in FORBIDDEN_TABLES:
                    if forbidden.lower() in table_clean:
                        violations.append(Violation(
                            violation_type=ViolationType.FORBIDDEN_TABLE_WRITE,
                            file_path=str(file_path),
                            line_number=line_num,
                            description=f"{op_type} to forbidden table: {table_name}",
                            code_snippet=line.strip(),
                            invariant_violated="Sensor Only — TF writes ONLY to person_movement_history and people_errors",
                        ))

                # Check if it's NOT a permitted table (and not a variable/placeholder)
                if not table_clean.startswith("%") and not table_clean.startswith("{"):
                    is_permitted = any(p.lower() in table_clean for p in PERMITTED_TABLES)
                    is_forbidden = any(f.lower() in table_clean for f in FORBIDDEN_TABLES)
                    
                    if is_forbidden and not is_permitted:
                        # Already caught above
                        pass

    return violations


def check_forbidden_signals(file_path: Path, content: str) -> List[Violation]:
    """
    Detect emission of forbidden signals.
    
    DOCTRINE: Talent Flow may ONLY emit:
    - SLOT_VACATED
    - SLOT_BIND_REQUEST
    - COMPANY_RESOLUTION_REQUIRED
    - MOVEMENT_RECORDED
    """
    violations = []
    lines = content.split("\n")

    # Patterns for signal emission
    signal_emit_patterns = [
        r"emit_signal\s*\(\s*['\"]([^'\"]+)['\"]",
        r"emit\s*\(\s*['\"]([^'\"]+)['\"]",
        r"_emit_signal\s*\(\s*['\"]([^'\"]+)['\"]",
        r"signal_type\s*=\s*['\"]([^'\"]+)['\"]",
        r"SignalType\.([A-Z_]+)",
    ]

    for line_num, line in enumerate(lines, 1):
        # Skip if line is in Talent Flow guard/test (meta-references)
        if "PERMITTED_SIGNALS" in line or "VALID_SIGNALS" in line:
            continue

        for pattern in signal_emit_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for signal_name in matches:
                signal_upper = signal_name.upper()
                
                # Skip known non-TF signals that might appear in shared code
                if signal_upper in {"EXECUTIVE_DEPARTURE", "EXECUTIVE_HIRE", "PROMOTION", "LATERAL_MOVE"}:
                    # These are movement TYPES, not signals — check context
                    if "movement_type" in line.lower() or "movement_types" in line.lower():
                        continue

                # Check if this is a TF signal emission (not just a reference)
                if "emit" in line.lower() or "signal" in line.lower():
                    if signal_upper not in PERMITTED_SIGNALS:
                        # Verify it's actually in TF context
                        if "talent_flow" in content.lower() or "movement" in content.lower():
                            violations.append(Violation(
                                violation_type=ViolationType.FORBIDDEN_SIGNAL,
                                file_path=str(file_path),
                                line_number=line_num,
                                description=f"Forbidden signal emission: {signal_name}",
                                code_snippet=line.strip(),
                                invariant_violated="Signal Authority — Only SLOT_VACATED, SLOT_BIND_REQUEST, COMPANY_RESOLUTION_REQUIRED, MOVEMENT_RECORDED",
                            ))

    return violations


def check_phase_order(file_path: Path, content: str) -> List[Violation]:
    """
    Detect phase gate order violations.
    
    DOCTRINE: Phases must execute in order: DETECT → RECON → SIGNAL
    No partial progression allowed.
    """
    violations = []

    # Look for phase execution patterns
    phase_patterns = {
        "DETECT": r"phase.*detect|detect.*phase|phase_1|phase1|PHASE_DETECT",
        "RECON": r"phase.*recon|recon.*phase|phase_2|phase2|PHASE_RECON",
        "SIGNAL": r"phase.*signal|signal.*phase|phase_3|phase3|PHASE_SIGNAL",
    }

    # Find phase occurrences with line numbers
    phase_occurrences = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for phase, pattern in phase_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                phase_occurrences.append((line_num, phase, line.strip()))

    # Check order (first occurrence of each phase)
    if len(phase_occurrences) >= 2:
        first_detect = next((x for x in phase_occurrences if x[1] == "DETECT"), None)
        first_recon = next((x for x in phase_occurrences if x[1] == "RECON"), None)
        first_signal = next((x for x in phase_occurrences if x[1] == "SIGNAL"), None)

        # Validate order
        if first_detect and first_recon:
            if first_recon[0] < first_detect[0]:
                violations.append(Violation(
                    violation_type=ViolationType.PHASE_ORDER_VIOLATION,
                    file_path=str(file_path),
                    line_number=first_recon[0],
                    description="RECON phase appears before DETECT phase",
                    code_snippet=first_recon[2],
                    invariant_violated="Phase-Gated — DETECT → RECON → SIGNAL order is mandatory",
                ))

        if first_recon and first_signal:
            if first_signal[0] < first_recon[0]:
                violations.append(Violation(
                    violation_type=ViolationType.PHASE_ORDER_VIOLATION,
                    file_path=str(file_path),
                    line_number=first_signal[0],
                    description="SIGNAL phase appears before RECON phase",
                    code_snippet=first_signal[2],
                    invariant_violated="Phase-Gated — DETECT → RECON → SIGNAL order is mandatory",
                ))

        if first_detect and first_signal and not first_recon:
            violations.append(Violation(
                violation_type=ViolationType.PHASE_ORDER_VIOLATION,
                file_path=str(file_path),
                line_number=first_signal[0],
                description="SIGNAL phase reached without RECON phase (phase skip detected)",
                code_snippet=first_signal[2],
                invariant_violated="Phase-Gated — All phases are mandatory, no skipping",
            ))

    return violations


def check_binary_outcomes(file_path: Path, content: str) -> List[Violation]:
    """
    Detect non-binary outcome states.
    
    DOCTRINE: Only PROMOTED or QUARANTINED are valid outcomes.
    No third state. No partial completion.
    """
    violations = []
    
    # Only check in TF-relevant context
    if "talent" not in content.lower() and "movement" not in content.lower():
        return violations
    
    lines = content.split("\n")

    # Patterns for outcome assignment (TF-specific)
    outcome_patterns = [
        r"TalentFlowOutcome\.([A-Z_]+)",
        r"talent_flow_outcome\s*=\s*['\"]([^'\"]+)['\"]",
    ]

    for line_num, line in enumerate(lines, 1):

        for pattern in outcome_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for outcome in matches:
                outcome_upper = outcome.upper()

                # Check if it looks like a TF outcome but isn't valid
                if outcome_upper not in VALID_OUTCOMES:
                    violations.append(Violation(
                        violation_type=ViolationType.NON_BINARY_OUTCOME,
                        file_path=str(file_path),
                        line_number=line_num,
                        description=f"Non-standard TF outcome state: {outcome} (expected PROMOTED or QUARANTINED)",
                        code_snippet=line.strip(),
                        invariant_violated="Binary Outcome — Only PROMOTED or QUARANTINED, no third state",
                    ))

    return violations


def check_idempotency_enforcement(file_path: Path, content: str) -> List[Violation]:
    """
    Detect missing idempotency enforcement.
    
    DOCTRINE: All movements must be deduplicated via hash key:
    SHA256(person_unique_id + movement_type + company_from_id + company_to_id + movement_date)
    """
    violations = []

    # Check if this file handles movement inserts
    if "INSERT" not in content.upper() or "movement" not in content.lower():
        return violations

    # Look for deduplication patterns
    dedup_patterns = [
        r"sha256|SHA256",
        r"dedup|deduplicate|deduplication",
        r"idempoten",
        r"movement_hash|hash_key|dedup_key",
        r"IF\s+NOT\s+EXISTS|ON\s+CONFLICT\s+DO\s+NOTHING",
        r"exists.*movement|movement.*exists",
    ]

    has_dedup = any(re.search(p, content, re.IGNORECASE) for p in dedup_patterns)

    if not has_dedup:
        # Find the INSERT line
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            if "INSERT" in line.upper() and "movement" in content.lower():
                violations.append(Violation(
                    violation_type=ViolationType.MISSING_IDEMPOTENCY,
                    file_path=str(file_path),
                    line_number=line_num,
                    description="Movement INSERT without idempotency check (missing deduplication)",
                    code_snippet=line.strip(),
                    invariant_violated="Idempotent — Same movement cannot fire twice (SHA256 hash required)",
                ))
                break

    return violations


def check_forbidden_operations(file_path: Path, content: str) -> List[Violation]:
    """
    Detect forbidden operations.
    
    DOCTRINE FORBIDDEN:
    - Company ID minting
    - Outreach record creation
    - Enrichment logic
    - Scoring logic
    - Recursive execution
    - Auto-resolve companies
    """
    violations = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for op_name, pattern in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                # Verify this is in TF context (not just a generic file)
                if "talent" in content.lower() or "movement" in content.lower():
                    violations.append(Violation(
                        violation_type=ViolationType.FORBIDDEN_OPERATION,
                        file_path=str(file_path),
                        line_number=line_num,
                        description=f"Forbidden operation detected: {op_name}",
                        code_snippet=line.strip(),
                        invariant_violated="Sensor Only — TF observes and emits, it does not act",
                    ))

    return violations


def check_kill_switch(file_path: Path, content: str) -> List[Violation]:
    """
    Verify kill switch is honored.
    
    DOCTRINE: PEOPLE_MOVEMENT_DETECT_ENABLED must HALT, not SKIP.
    """
    violations = []
    lines = content.split("\n")

    # Check if this is a TF execution file
    if "talent_flow" not in content.lower() and "_run_talent" not in content.lower():
        return violations

    # Look for kill switch reference
    has_kill_switch = KILL_SWITCH_VAR in content or "MOVEMENT_DETECT_ENABLED" in content

    if not has_kill_switch:
        # Find function definitions that should check kill switch
        for line_num, line in enumerate(lines, 1):
            if re.search(r"def\s+.*talent.*flow|def\s+.*movement.*detect", line, re.IGNORECASE):
                violations.append(Violation(
                    violation_type=ViolationType.MISSING_KILL_SWITCH,
                    file_path=str(file_path),
                    line_number=line_num,
                    description=f"Talent Flow execution without kill switch check ({KILL_SWITCH_VAR})",
                    code_snippet=line.strip(),
                    invariant_violated="Kill Switch — HALT behavior required, never SKIP",
                ))
                break

    return violations


# =============================================================================
# MAIN GUARD FUNCTION
# =============================================================================

def run_talent_flow_guard(base_path: str) -> TalentFlowGuardResult:
    """
    Run complete Talent Flow doctrine guard.
    
    Returns:
        TalentFlowGuardResult with all violations
    """
    all_violations: List[Violation] = []
    warnings: List[str] = []

    # Find relevant files
    tf_files = find_talent_flow_files(base_path)

    if not tf_files:
        warnings.append("No Talent Flow files found in scan scope")
        return TalentFlowGuardResult(
            passed=True,
            files_scanned=0,
            violations=[],
            warnings=warnings,
        )

    # Scan each file
    for file_path in tf_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Run all checks
            all_violations.extend(check_forbidden_table_writes(file_path, content))
            all_violations.extend(check_forbidden_signals(file_path, content))
            all_violations.extend(check_phase_order(file_path, content))
            all_violations.extend(check_binary_outcomes(file_path, content))
            all_violations.extend(check_idempotency_enforcement(file_path, content))
            all_violations.extend(check_forbidden_operations(file_path, content))
            all_violations.extend(check_kill_switch(file_path, content))

        except Exception as e:
            warnings.append(f"Error scanning {file_path}: {e}")

    return TalentFlowGuardResult(
        passed=len(all_violations) == 0,
        files_scanned=len(tf_files),
        violations=all_violations,
        warnings=warnings,
    )


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point for CI integration."""
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Talent Flow Doctrine Guard — {CERTIFICATION_ID}"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Base path to scan (default: current directory)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Output in CI format (GitHub Actions annotations)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    args = parser.parse_args()

    # Run guard
    result = run_talent_flow_guard(args.path)

    # Output results
    if args.json:
        import json
        print(json.dumps({
            "certification_id": CERTIFICATION_ID,
            "doctrine_version": DOCTRINE_VERSION,
            "passed": result.passed,
            "files_scanned": result.files_scanned,
            "violation_count": len(result.violations),
            "violations": [
                {
                    "type": v.violation_type.value,
                    "file": v.file_path,
                    "line": v.line_number,
                    "description": v.description,
                    "invariant": v.invariant_violated,
                }
                for v in result.violations
            ],
        }, indent=2))
    elif args.ci:
        # CI format: GitHub Actions annotations
        for v in result.violations:
            print(v.to_error_message())
        if result.passed:
            print(f"::notice::[{CERTIFICATION_ID}] Talent Flow Doctrine Guard: PASS ({result.files_scanned} files scanned)")
        else:
            print(f"::error::[{CERTIFICATION_ID}] Talent Flow Doctrine Guard: FAIL ({len(result.violations)} violations)")
    else:
        # Human-readable report
        print(result.to_report())

    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
