"""
Pipeline Context Enforcement Test
==================================

DOCTRINE: run_full_pipeline() MUST FAIL HARD if outreach_context_id
or company_sov_id is missing.

This test verifies the orchestrator enforces cost discipline by testing
the validation functions that run_full_pipeline() calls at entry.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import using direct file loading (avoiding hyphenated directory issues)
import importlib.util

# Load context_manager for exception types and validation functions
context_spec = importlib.util.spec_from_file_location(
    "context_manager",
    PROJECT_ROOT / "hubs" / "company-target" / "imo" / "middle" / "utils" / "context_manager.py"
)
context_manager_module = importlib.util.module_from_spec(context_spec)
context_spec.loader.exec_module(context_manager_module)

OutreachContextManager = context_manager_module.OutreachContextManager
MissingContextError = context_manager_module.MissingContextError
MissingSovIdError = context_manager_module.MissingSovIdError


class TestPipelineContextEnforcement:
    """
    Tests that run_full_pipeline() enforces context discipline.

    These tests verify the validation functions that run_full_pipeline()
    calls at entry point. The pipeline uses:
        outreach_context_id = OutreachContextManager.validate_context_id(outreach_context_id)
        company_sov_id = OutreachContextManager.validate_sov_id(company_sov_id)
    """

    def test_missing_outreach_context_id_raises(self):
        """
        DOCTRINE: Missing outreach_context_id MUST raise MissingContextError.
        """
        with pytest.raises(MissingContextError):
            OutreachContextManager.validate_context_id(None)

    def test_empty_outreach_context_id_raises(self):
        """
        DOCTRINE: Empty outreach_context_id MUST raise MissingContextError.
        """
        with pytest.raises(MissingContextError):
            OutreachContextManager.validate_context_id("")

    def test_missing_company_sov_id_raises(self):
        """
        DOCTRINE: Missing company_sov_id MUST raise MissingSovIdError.
        """
        with pytest.raises(MissingSovIdError):
            OutreachContextManager.validate_sov_id(None)

    def test_empty_company_sov_id_raises(self):
        """
        DOCTRINE: Empty company_sov_id MUST raise MissingSovIdError.
        """
        with pytest.raises(MissingSovIdError):
            OutreachContextManager.validate_sov_id("")

    def test_valid_context_id_passes(self):
        """Valid context ID should pass validation."""
        result = OutreachContextManager.validate_context_id("test-context-123")
        assert result == "test-context-123"

    def test_valid_sov_id_passes(self):
        """Valid sovereign ID should pass validation."""
        result = OutreachContextManager.validate_sov_id("test-sov-456")
        assert result == "test-sov-456"


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == '__main__':
    """
    Run pipeline context enforcement tests directly.

    Usage:
        python -m tests.hub.company.test_pipeline_context_enforcement

    Or with pytest:
        pytest tests/hub/company/test_pipeline_context_enforcement.py -v
    """
    test = TestPipelineContextEnforcement()

    print("=" * 70)
    print("PIPELINE CONTEXT ENFORCEMENT TEST")
    print("=" * 70)
    print()

    # Test 1: Missing outreach_context_id
    try:
        test.test_missing_outreach_context_id_raises()
        print("[PASS] test_missing_outreach_context_id_raises")
    except AssertionError as e:
        print(f"[FAIL] test_missing_outreach_context_id_raises: {e}")
        sys.exit(1)

    # Test 2: Empty outreach_context_id
    try:
        test.test_empty_outreach_context_id_raises()
        print("[PASS] test_empty_outreach_context_id_raises")
    except AssertionError as e:
        print(f"[FAIL] test_empty_outreach_context_id_raises: {e}")
        sys.exit(1)

    # Test 3: Missing company_sov_id
    try:
        test.test_missing_company_sov_id_raises()
        print("[PASS] test_missing_company_sov_id_raises")
    except AssertionError as e:
        print(f"[FAIL] test_missing_company_sov_id_raises: {e}")
        sys.exit(1)

    # Test 4: Empty company_sov_id
    try:
        test.test_empty_company_sov_id_raises()
        print("[PASS] test_empty_company_sov_id_raises")
    except AssertionError as e:
        print(f"[FAIL] test_empty_company_sov_id_raises: {e}")
        sys.exit(1)

    # Test 5: Valid IDs pass
    try:
        test.test_valid_context_id_passes()
        print("[PASS] test_valid_context_id_passes")
    except AssertionError as e:
        print(f"[FAIL] test_valid_context_id_passes: {e}")
        sys.exit(1)

    try:
        test.test_valid_sov_id_passes()
        print("[PASS] test_valid_sov_id_passes")
    except AssertionError as e:
        print(f"[FAIL] test_valid_sov_id_passes: {e}")
        sys.exit(1)

    print()
    print("=" * 70)
    print("ALL PIPELINE CONTEXT TESTS PASSED")
    print("=" * 70)
