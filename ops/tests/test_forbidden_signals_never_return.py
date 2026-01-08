"""
Forbidden Signals Regression Test — TF-001
==========================================
CERTIFICATION: TF-001
DOCTRINE VERSION: 1.0.1
STATUS: CERTIFIED
DATE: 2026-01-08

This test is a REGRESSION LOCK to prevent forbidden signals from
re-entering the codebase after quarantine.

PURPOSE:
- Ensure forbidden signals never appear in production code
- Block PRs that introduce forbidden signal patterns
- Maintain TF-001 doctrine integrity

FORBIDDEN SIGNALS:
- JOB_CHANGE
- STARTUP
- PROMOTION
- LATERAL
- COMPANY_CHANGE

These signals were quarantined on 2026-01-08 because they violate
TF-001 Signal Authority invariant.
"""

import os
import re
import pytest
from pathlib import Path
from typing import List, Set, Tuple


# =============================================================================
# CONSTANTS
# =============================================================================

CERTIFICATION_ID = "TF-001"

# Signals that are FORBIDDEN and must never appear in production code
# These are specifically TalentFlowSignalType values, not ErrorStage or other enums
FORBIDDEN_SIGNALS: Set[str] = {
    "JOB_CHANGE",
    "STARTUP",
    # Note: PROMOTION and LATERAL are excluded because they appear in other contexts
    # (e.g., ErrorStage.PROMOTION is a funnel stage, not a TalentFlow signal)
    # The regression lock focuses on the unique TalentFlow signals
    "COMPANY_CHANGE",
}

# TalentFlow-specific forbidden signals (appear in TalentFlowSignalType enum)
TALENTFLOW_FORBIDDEN_SIGNALS: Set[str] = {
    "JOB_CHANGE",
    "STARTUP", 
    "PROMOTION",  # Only forbidden in TalentFlowSignalType context
    "LATERAL",    # Only forbidden in TalentFlowSignalType context
    "COMPANY_CHANGE",
}

# Permitted signals per TF-001
PERMITTED_SIGNALS: Set[str] = {
    "SLOT_VACATED",
    "SLOT_BIND_REQUEST",
    "COMPANY_RESOLUTION_REQUIRED",
    "MOVEMENT_RECORDED",
}

# Paths to scan for forbidden signals
SCAN_PATHS: List[str] = [
    "hubs/people-intelligence",
    "spokes",
    "ops/enforcement",
]

# Paths to EXCLUDE from scanning (quarantined code)
EXCLUDE_PATHS: List[str] = [
    "meta/legacy_quarantine",
    "__pycache__",
    ".git",
    "test_forbidden_signals",  # Don't scan self
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_workspace_root() -> Path:
    """Get the workspace root directory."""
    # Navigate up from test file to find repo root
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "CLAUDE.md").exists() or (current / ".git").exists():
            return current
        current = current.parent
    # Fallback
    return Path(__file__).resolve().parent.parent.parent.parent


def should_exclude(file_path: Path, workspace_root: Path) -> bool:
    """Check if a file should be excluded from scanning."""
    # Convert to string and normalize path separators for cross-platform
    relative_path = str(file_path.relative_to(workspace_root)).replace("\\", "/")
    for exclude in EXCLUDE_PATHS:
        if exclude in relative_path:
            return True
    return False


def find_python_files(workspace_root: Path) -> List[Path]:
    """Find all Python files in scan paths."""
    python_files = []
    
    for scan_path in SCAN_PATHS:
        full_path = workspace_root / scan_path
        if not full_path.exists():
            continue
            
        for py_file in full_path.rglob("*.py"):
            if not should_exclude(py_file, workspace_root):
                python_files.append(py_file)
    
    return python_files


def scan_file_for_forbidden_signals(
    file_path: Path
) -> List[Tuple[int, str, str]]:
    """
    Scan a file for forbidden TalentFlow signal patterns.
    
    Only flags signals that are clearly TalentFlow-related, not
    other uses like ErrorStage.PROMOTION.
    
    Returns:
        List of (line_number, signal_found, line_content) tuples
    """
    violations = []
    
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            for signal in FORBIDDEN_SIGNALS:
                # Only match TalentFlow-specific patterns, not generic uses
                patterns = [
                    rf"TalentFlowSignalType\.{signal}",  # Enum reference
                    rf"TalentFlowSignal\.{signal}",  # Alternate enum
                    rf"signal_type\s*=\s*['\"]{signal.lower()}['\"]",  # TF signal assignment
                    rf"talent_flow.*{signal}",  # TalentFlow context
                    rf"{signal}.*talent_flow",  # TalentFlow context
                ]
                
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append((line_num, signal, line.strip()))
                        break  # Only report once per line per signal
    
    except Exception:
        pass  # Skip unreadable files
    
    return violations


# =============================================================================
# TEST CLASS
# =============================================================================

class TestForbiddenSignalsNeverReturn:
    """
    Regression tests to ensure forbidden signals never return.
    
    These tests will FAIL if any forbidden signal patterns are found
    in production code paths.
    """

    @pytest.fixture
    def workspace_root(self) -> Path:
        return get_workspace_root()

    def test_no_job_change_signal_in_codebase(self, workspace_root):
        """
        TF-001: JOB_CHANGE signal must not appear in production code.
        
        This signal was quarantined because it is not a permitted
        Talent Flow signal per doctrine.
        """
        violations = []
        
        for py_file in find_python_files(workspace_root):
            file_violations = scan_file_for_forbidden_signals(py_file)
            job_change = [v for v in file_violations if v[1] == "JOB_CHANGE"]
            violations.extend([(py_file, *v) for v in job_change])
        
        if violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNAL DETECTED: JOB_CHANGE\n\n"
            for file_path, line_num, signal, line in violations:
                rel_path = file_path.relative_to(workspace_root)
                msg += f"  {rel_path}:{line_num}: {line}\n"
            msg += "\nThis signal is FORBIDDEN by TF-001 doctrine.\n"
            msg += "Remove it or move to legacy_quarantine/.\n"
            pytest.fail(msg)

    def test_no_startup_signal_in_codebase(self, workspace_root):
        """
        TF-001: STARTUP signal must not appear in production code.
        """
        violations = []
        
        for py_file in find_python_files(workspace_root):
            file_violations = scan_file_for_forbidden_signals(py_file)
            startup = [v for v in file_violations if v[1] == "STARTUP"]
            violations.extend([(py_file, *v) for v in startup])
        
        if violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNAL DETECTED: STARTUP\n\n"
            for file_path, line_num, signal, line in violations:
                rel_path = file_path.relative_to(workspace_root)
                msg += f"  {rel_path}:{line_num}: {line}\n"
            pytest.fail(msg)

    def test_no_promotion_signal_in_codebase(self, workspace_root):
        """
        TF-001: PROMOTION signal must not appear as TalentFlowSignalType.
        
        Note: ErrorStage.PROMOTION (funnel stage) is allowed.
        Only TalentFlowSignalType.PROMOTION is forbidden.
        """
        violations = []
        
        for py_file in find_python_files(workspace_root):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            for line_num, line in enumerate(lines, 1):
                # Only check TalentFlow-specific patterns
                if re.search(r"TalentFlowSignalType\.PROMOTION", line, re.IGNORECASE):
                    violations.append((py_file, line_num, "PROMOTION", line.strip()))
        
        if violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNAL DETECTED: TalentFlowSignalType.PROMOTION\n\n"
            for file_path, line_num, signal, line in violations:
                rel_path = file_path.relative_to(workspace_root)
                msg += f"  {rel_path}:{line_num}: {line}\n"
            pytest.fail(msg)

    def test_no_lateral_signal_in_codebase(self, workspace_root):
        """
        TF-001: LATERAL signal must not appear as TalentFlowSignalType.
        """
        violations = []
        
        for py_file in find_python_files(workspace_root):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            for line_num, line in enumerate(lines, 1):
                # Only check TalentFlow-specific patterns
                if re.search(r"TalentFlowSignalType\.LATERAL", line, re.IGNORECASE):
                    violations.append((py_file, line_num, "LATERAL", line.strip()))
        
        if violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNAL DETECTED: TalentFlowSignalType.LATERAL\n\n"
            for file_path, line_num, signal, line in violations:
                rel_path = file_path.relative_to(workspace_root)
                msg += f"  {rel_path}:{line_num}: {line}\n"
            pytest.fail(msg)

    def test_no_company_change_signal_in_codebase(self, workspace_root):
        """
        TF-001: COMPANY_CHANGE signal must not appear in production code.
        """
        violations = []
        
        for py_file in find_python_files(workspace_root):
            file_violations = scan_file_for_forbidden_signals(py_file)
            company = [v for v in file_violations if v[1] == "COMPANY_CHANGE"]
            violations.extend([(py_file, *v) for v in company])
        
        if violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNAL DETECTED: COMPANY_CHANGE\n\n"
            for file_path, line_num, signal, line in violations:
                rel_path = file_path.relative_to(workspace_root)
                msg += f"  {rel_path}:{line_num}: {line}\n"
            pytest.fail(msg)

    def test_all_forbidden_signals_quarantined(self, workspace_root):
        """
        TF-001: All forbidden signals must be in quarantine, not production.
        
        This is a comprehensive check that scans all production paths.
        """
        all_violations = []
        
        for py_file in find_python_files(workspace_root):
            file_violations = scan_file_for_forbidden_signals(py_file)
            all_violations.extend([(py_file, *v) for v in file_violations])
        
        if all_violations:
            msg = f"\n[{CERTIFICATION_ID}] FORBIDDEN SIGNALS DETECTED IN PRODUCTION CODE\n"
            msg += "=" * 60 + "\n\n"
            
            # Group by signal
            by_signal = {}
            for file_path, line_num, signal, line in all_violations:
                if signal not in by_signal:
                    by_signal[signal] = []
                by_signal[signal].append((file_path, line_num, line))
            
            for signal, locations in sorted(by_signal.items()):
                msg += f"❌ {signal} ({len(locations)} occurrences):\n"
                for file_path, line_num, line in locations[:3]:  # Show first 3
                    rel_path = file_path.relative_to(workspace_root)
                    msg += f"   {rel_path}:{line_num}\n"
                if len(locations) > 3:
                    msg += f"   ... and {len(locations) - 3} more\n"
                msg += "\n"
            
            msg += "DOCTRINE VIOLATION: These signals are forbidden by TF-001.\n"
            msg += "Permitted signals: " + ", ".join(PERMITTED_SIGNALS) + "\n"
            msg += "\nTo fix: Move violating code to meta/legacy_quarantine/\n"
            
            pytest.fail(msg)

    def test_permitted_signals_are_correct(self):
        """
        TF-001: Verify permitted signals match doctrine.
        """
        expected = {
            "SLOT_VACATED",
            "SLOT_BIND_REQUEST",
            "COMPANY_RESOLUTION_REQUIRED",
            "MOVEMENT_RECORDED",
        }
        assert PERMITTED_SIGNALS == expected

    def test_forbidden_signals_are_correct(self):
        """
        TF-001: Verify forbidden signals match quarantine list.
        
        Note: FORBIDDEN_SIGNALS contains only signals unique to TalentFlow.
        TALENTFLOW_FORBIDDEN_SIGNALS contains the full list including PROMOTION/LATERAL
        which also appear in other contexts (e.g., ErrorStage).
        """
        # Core forbidden signals (unique to TalentFlow)
        expected_core = {
            "JOB_CHANGE",
            "STARTUP",
            "COMPANY_CHANGE",
        }
        assert FORBIDDEN_SIGNALS == expected_core
        
        # Full TalentFlow forbidden signals (including shared names)
        expected_full = {
            "JOB_CHANGE",
            "STARTUP",
            "PROMOTION",
            "LATERAL",
            "COMPANY_CHANGE",
        }
        assert TALENTFLOW_FORBIDDEN_SIGNALS == expected_full

    def test_quarantine_path_excluded_from_scan(self, workspace_root):
        """
        TF-001: Verify quarantine path is properly excluded.
        
        Files in legacy_quarantine should not trigger violations.
        """
        quarantine_file = workspace_root / "meta" / "legacy_quarantine" / "test.py"
        
        # Verify exclusion logic works
        assert should_exclude(quarantine_file, workspace_root)
        
        # Verify production paths are NOT excluded
        prod_file = workspace_root / "hubs" / "people-intelligence" / "test.py"
        assert not should_exclude(prod_file, workspace_root)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    """Run regression check without pytest."""
    print("=" * 60)
    print(f"FORBIDDEN SIGNALS REGRESSION CHECK — {CERTIFICATION_ID}")
    print("=" * 60)
    print()
    
    workspace_root = get_workspace_root()
    print(f"Workspace: {workspace_root}")
    print()
    
    all_violations = []
    files_scanned = 0
    
    for py_file in find_python_files(workspace_root):
        files_scanned += 1
        file_violations = scan_file_for_forbidden_signals(py_file)
        all_violations.extend([(py_file, *v) for v in file_violations])
    
    print(f"Files scanned: {files_scanned}")
    print(f"Violations found: {len(all_violations)}")
    print()
    
    if all_violations:
        print("❌ FORBIDDEN SIGNALS DETECTED:")
        print("-" * 40)
        for file_path, line_num, signal, line in all_violations:
            rel_path = file_path.relative_to(workspace_root)
            print(f"  {signal}: {rel_path}:{line_num}")
        print()
        print("FAIL: Forbidden signals found in production code.")
        exit(1)
    else:
        print("✅ PASS: No forbidden signals in production code.")
        exit(0)
