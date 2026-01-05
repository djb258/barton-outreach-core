"""
CL Gate Enforcement Test
========================

DOCTRINE: run_full_pipeline() MUST FAIL HARD if company does not exist
in Company Lifecycle (CL).

Outreach is a CONSUMER of CL truth, not a creator.
If CL did not mint the sovereign ID, Outreach MUST NOT proceed.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import using direct file loading (avoiding hyphenated directory issues)
import importlib.util

# Load cl_gate module
cl_gate_spec = importlib.util.spec_from_file_location(
    "cl_gate",
    PROJECT_ROOT / "hubs" / "company-target" / "imo" / "middle" / "utils" / "cl_gate.py"
)
cl_gate_module = importlib.util.module_from_spec(cl_gate_spec)
cl_gate_spec.loader.exec_module(cl_gate_module)

CLGate = cl_gate_module.CLGate
CLNotVerifiedError = cl_gate_module.CLNotVerifiedError
UpstreamCLError = cl_gate_module.UpstreamCLError


class TestCLGateEnforcement:
    """
    Tests that Company Target enforces CL upstream contract.

    DOCTRINE: Outreach assumes Company Life Cycle existence verification
    has already passed. Outreach will not execute without an EXISTENCE_PASS
    signal.
    """

    def setup_method(self):
        """Reset CLGate state before each test."""
        CLGate.reset()
        # Enable mock mode with known verified IDs
        CLGate.set_mock_mode(verified_ids={
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        })

    def teardown_method(self):
        """Reset CLGate state after each test."""
        CLGate.reset()

    def test_missing_sov_id_returns_false(self):
        """
        DOCTRINE: Empty/None sovereign ID returns False (EXISTENCE_FAIL).
        """
        assert CLGate.check_existence(None) is False
        assert CLGate.check_existence("") is False
        assert CLGate.check_existence("   ") is False

    def test_unverified_company_returns_false(self):
        """
        DOCTRINE: Company not in CL returns False (EXISTENCE_FAIL).
        """
        assert CLGate.check_existence("99999999-9999-9999-9999-999999999999") is False

    def test_verified_company_returns_true(self):
        """
        DOCTRINE: Company in CL returns True (EXISTENCE_PASS).
        """
        assert CLGate.check_existence("11111111-1111-1111-1111-111111111111") is True
        assert CLGate.check_existence("22222222-2222-2222-2222-222222222222") is True

    def test_enforce_or_fail_raises_on_missing(self):
        """
        DOCTRINE: Missing CL company MUST raise CLNotVerifiedError.
        """
        with pytest.raises(CLNotVerifiedError) as exc_info:
            CLGate.enforce_or_fail(
                company_sov_id="99999999-9999-9999-9999-999999999999",
                outreach_context_id="test-context-123"
            )

        assert exc_info.value.error_code == "CT_UPSTREAM_CL_NOT_VERIFIED"
        assert "not found in CL" in exc_info.value.message

    def test_enforce_or_fail_passes_on_verified(self):
        """
        DOCTRINE: Verified CL company proceeds without exception.
        """
        # Should not raise
        CLGate.enforce_or_fail(
            company_sov_id="11111111-1111-1111-1111-111111111111",
            outreach_context_id="test-context-123"
        )

    def test_exception_contains_company_id(self):
        """
        Error should contain the company_sov_id for debugging.
        """
        try:
            CLGate.enforce_or_fail(
                company_sov_id="bad-company-id",
                outreach_context_id="test-context"
            )
            pytest.fail("Should have raised CLNotVerifiedError")
        except CLNotVerifiedError as e:
            assert e.company_sov_id == "bad-company-id"
            assert "bad-company-id" in str(e)

    def test_error_inherits_from_base(self):
        """
        CLNotVerifiedError should inherit from UpstreamCLError.
        """
        try:
            CLGate.enforce_or_fail(
                company_sov_id="missing",
                outreach_context_id="ctx"
            )
        except UpstreamCLError as e:
            assert e.error_code == "CT_UPSTREAM_CL_NOT_VERIFIED"
        except Exception:
            pytest.fail("Exception should be UpstreamCLError subclass")


# =============================================================================
# DIRECT EXECUTION
# =============================================================================

if __name__ == '__main__':
    """
    Run CL gate enforcement tests directly.

    Usage:
        python -m tests.hub.company.test_cl_gate

    Or with pytest:
        pytest tests/hub/company/test_cl_gate.py -v
    """
    test = TestCLGateEnforcement()

    print("=" * 70)
    print("CL GATE ENFORCEMENT TEST")
    print("=" * 70)
    print()

    # Test 1: Missing sov_id
    test.setup_method()
    try:
        test.test_missing_sov_id_returns_false()
        print("[PASS] test_missing_sov_id_returns_false")
    except AssertionError as e:
        print(f"[FAIL] test_missing_sov_id_returns_false: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 2: Unverified company
    test.setup_method()
    try:
        test.test_unverified_company_returns_false()
        print("[PASS] test_unverified_company_returns_false")
    except AssertionError as e:
        print(f"[FAIL] test_unverified_company_returns_false: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 3: Verified company
    test.setup_method()
    try:
        test.test_verified_company_returns_true()
        print("[PASS] test_verified_company_returns_true")
    except AssertionError as e:
        print(f"[FAIL] test_verified_company_returns_true: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 4: Enforce raises on missing
    test.setup_method()
    try:
        test.test_enforce_or_fail_raises_on_missing()
        print("[PASS] test_enforce_or_fail_raises_on_missing")
    except AssertionError as e:
        print(f"[FAIL] test_enforce_or_fail_raises_on_missing: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 5: Enforce passes on verified
    test.setup_method()
    try:
        test.test_enforce_or_fail_passes_on_verified()
        print("[PASS] test_enforce_or_fail_passes_on_verified")
    except AssertionError as e:
        print(f"[FAIL] test_enforce_or_fail_passes_on_verified: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 6: Exception contains company ID
    test.setup_method()
    try:
        test.test_exception_contains_company_id()
        print("[PASS] test_exception_contains_company_id")
    except AssertionError as e:
        print(f"[FAIL] test_exception_contains_company_id: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    # Test 7: Error inherits from base
    test.setup_method()
    try:
        test.test_error_inherits_from_base()
        print("[PASS] test_error_inherits_from_base")
    except AssertionError as e:
        print(f"[FAIL] test_error_inherits_from_base: {e}")
        sys.exit(1)
    finally:
        test.teardown_method()

    print()
    print("=" * 70)
    print("ALL CL GATE TESTS PASSED")
    print("=" * 70)
