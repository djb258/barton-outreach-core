"""
Unit tests for Outreach Readiness Evaluator - Phase 2
Tests slot evaluation, title matching, and overall readiness logic

Run tests:
    python backend/enrichment/tests/test_readiness.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from enrichment.evaluate_outreach_readiness import OutreachReadinessEvaluator


def test_title_match():
    """Test title matching logic for CEO, CFO, HR"""
    evaluator = OutreachReadinessEvaluator("dummy_connection", dry_run=True)

    print("="*60)
    print("Test 1: Title Matching")
    print("="*60)

    # CEO tests
    assert evaluator.check_title_match("CEO", "Chief Executive Officer") == True
    assert evaluator.check_title_match("CEO", "CEO") == True
    assert evaluator.check_title_match("CEO", "President and CEO") == True
    assert evaluator.check_title_match("CEO", "CFO") == False
    print("[PASS] CEO title matching works")

    # CFO tests
    assert evaluator.check_title_match("CFO", "Chief Financial Officer") == True
    assert evaluator.check_title_match("CFO", "CFO") == True
    assert evaluator.check_title_match("CFO", "VP of Finance and CFO") == True
    assert evaluator.check_title_match("CFO", "CEO") == False
    print("[PASS] CFO title matching works")

    # HR tests
    assert evaluator.check_title_match("HR", "Director of Human Resources") == True
    assert evaluator.check_title_match("HR", "Chief People Officer") == True
    assert evaluator.check_title_match("HR", "VP of Talent Acquisition") == True
    assert evaluator.check_title_match("HR", "HR Manager") == True
    assert evaluator.check_title_match("HR", "CEO") == False
    print("[PASS] HR title matching works")

    print()


def test_slot_evaluation_logic():
    """Test slot evaluation with various scenarios"""
    evaluator = OutreachReadinessEvaluator("dummy_connection", dry_run=True)

    print("="*60)
    print("Test 2: Slot Evaluation Logic")
    print("="*60)

    # Scenario 1: Unfilled slot
    unfilled_slot = {
        "slot_type": "CEO",
        "is_filled": False,
        "person_unique_id": None
    }
    result = evaluator.evaluate_slot(unfilled_slot)
    assert result["passed"] == False
    assert "not filled" in result["failures"][0].lower()
    print("[PASS] Unfilled slot correctly fails")

    # Scenario 2: Filled slot with person_unique_id
    filled_slot = {
        "slot_type": "CFO",
        "is_filled": True,
        "person_unique_id": "04.04.02.04.20000.001"
    }
    result = evaluator.evaluate_slot(filled_slot)
    # In dry-run mode, person won't be found (database not accessed)
    assert result["passed"] == False
    assert result["checks"]["is_filled"] == True
    print("[PASS] Filled slot evaluation logic works")

    print()


def test_readiness_result_structure():
    """Test the structure of readiness evaluation result"""
    evaluator = OutreachReadinessEvaluator("dummy_connection", dry_run=True)

    print("="*60)
    print("Test 3: Result Structure Validation")
    print("="*60)

    # Evaluate a dummy company (will fail in dry-run, but we check structure)
    result = evaluator.evaluate_outreach_readiness("04.04.02.04.30000.001")

    # Check required keys
    assert "company_unique_id" in result
    assert "outreach_ready" in result
    assert "reason" in result
    assert "slot_results" in result
    assert "missing_slots" in result
    assert "total_checks" in result
    assert "passed_checks" in result

    print("[PASS] Result contains all required keys")
    print(f"   Keys: {list(result.keys())}")
    print()


def test_stats_tracking():
    """Test statistics tracking"""
    evaluator = OutreachReadinessEvaluator("dummy_connection", dry_run=True)

    print("="*60)
    print("Test 4: Statistics Tracking")
    print("="*60)

    # Increment various stats
    evaluator.stats.total_evaluated = 10
    evaluator.stats.ready = 7
    evaluator.stats.not_ready = 3
    evaluator.stats.slot_not_filled = 2
    evaluator.stats.enrichment_missing = 1

    stats_dict = evaluator.stats.to_dict()

    assert stats_dict["total_evaluated"] == 10
    assert stats_dict["outreach_ready"] == 7
    assert stats_dict["not_ready"] == 3
    assert stats_dict["failures"]["slot_not_filled"] == 2
    assert stats_dict["failures"]["enrichment_missing"] == 1

    print("[PASS] Statistics tracking works correctly")
    print(f"   Stats: {stats_dict}")
    print()


def test_missing_slots_detection():
    """Test detection of missing slot records"""
    evaluator = OutreachReadinessEvaluator("dummy_connection", dry_run=True)

    print("="*60)
    print("Test 5: Missing Slots Detection")
    print("="*60)

    # In dry-run mode, company won't be found, but we can test the logic
    result = evaluator.evaluate_outreach_readiness("04.04.02.04.30000.999")

    # Company not found should report missing all slots
    assert result["outreach_ready"] == False
    assert "not found" in result["reason"].lower()

    print("[PASS] Missing company detection works")
    print(f"   Reason: {result['reason']}")
    print()


def run_all_tests():
    """Run all test functions"""
    print("\n" + "="*60)
    print("OUTREACH READINESS EVALUATOR - UNIT TESTS")
    print("="*60)
    print()

    try:
        test_title_match()
        test_slot_evaluation_logic()
        test_readiness_result_structure()
        test_stats_tracking()
        test_missing_slots_detection()

        print("="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
