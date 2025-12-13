"""
Revalidation After Enrichment - Barton Outreach Core
Re-runs validation rules after enrichment to check if company can now be promoted

Usage:
    from revalidate_after_enrichment import revalidate_company

    result = revalidate_company(company_record, enriched_data)

    if result['passes']:
        # INSERT into marketing.company_master
        # DELETE from marketing.company_invalid
        print("Ready to promote!")
    else:
        # Still missing required fields
        print(f"Still invalid: {result['still_missing']}")
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from toolbox-hub.backend.validator.validation_rules import (
        CompanyValidator,
        ValidationSeverity
    )
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent.parent / "toolbox-hub" / "backend"))
    from validator.validation_rules import CompanyValidator, ValidationSeverity


class RevalidationResult:
    """Result from revalidation attempt"""

    def __init__(self, passes: bool, still_missing: List[str] = None,
                 validation_errors: List[Dict] = None, merged_record: Dict = None):
        self.passes = passes
        self.still_missing = still_missing or []
        self.validation_errors = validation_errors or []
        self.merged_record = merged_record or {}

    def to_dict(self) -> Dict:
        return {
            "passes": self.passes,
            "still_missing": self.still_missing,
            "validation_errors": self.validation_errors,
            "merged_record": self.merged_record
        }


def merge_enriched_data(original_record: Dict, enriched_data: Dict) -> Dict:
    """
    Merge enriched data into original company record

    Args:
        original_record: Original failed company record
        enriched_data: New data from enrichment API

    Returns:
        Merged record with enriched data
    """
    # Start with original record
    merged = original_record.copy()

    # Overlay enriched data (enriched data takes precedence)
    for key, value in enriched_data.items():
        if value:  # Only use non-empty enriched values
            merged[key] = value

    return merged


def revalidate_company(company_record: Dict, enriched_data: Dict) -> Dict:
    """
    Re-run validation rules after enrichment

    Args:
        company_record: Original failed company record
        enriched_data: New data from enrichment (e.g., {"website": "https://example.com"})

    Returns:
        Dict with:
            - passes: bool (can be promoted to company_master?)
            - still_missing: List[str] (fields still missing)
            - validation_errors: List[Dict] (detailed validation failures)
            - merged_record: Dict (company_record + enriched_data)
    """
    print(f"\n{'='*80}")
    print(f"REVALIDATION: {company_record.get('company_name', 'Unknown')}")
    print(f"{'='*80}")

    # Step 1: Merge enriched data into original record
    merged_record = merge_enriched_data(company_record, enriched_data)

    print(f"\nOriginal record:")
    print(f"  Company: {company_record.get('company_name')}")
    print(f"  Website: {company_record.get('website', 'N/A')}")
    print(f"  Employee Count: {company_record.get('employee_count', 'N/A')}")

    print(f"\nEnriched data:")
    for key, value in enriched_data.items():
        print(f"  {key}: {value}")

    print(f"\nMerged record:")
    print(f"  Company: {merged_record.get('company_name')}")
    print(f"  Website: {merged_record.get('website', 'N/A')}")
    print(f"  Employee Count: {merged_record.get('employee_count', 'N/A')}")

    # Step 2: Run validation rules on merged record
    validation_failures = []
    still_missing = []

    # Rule 1: Company name (must be present and > 3 chars)
    failure = CompanyValidator.validate_company_name(merged_record)
    if failure:
        validation_failures.append(failure.to_dict())
        still_missing.append("company_name")

    # Rule 2: Website (must be present and valid)
    failure = CompanyValidator.validate_website(merged_record)
    if failure:
        validation_failures.append(failure.to_dict())
        still_missing.append("website")

    # Rule 3: Employee count (must be > 0, optionally > 50 for Phase 1)
    # For enrichment revalidation, we'll be lenient and just check > 0
    failure = CompanyValidator.validate_employee_count(merged_record, minimum=0)
    if failure:
        validation_failures.append(failure.to_dict())
        still_missing.append("employee_count")

    # Step 3: Determine if validation passes
    # Only CRITICAL and ERROR failures block promotion
    blocking_failures = [
        f for f in validation_failures
        if f['severity'] in ['critical', 'error']
    ]

    passes = len(blocking_failures) == 0

    if passes:
        print("\n[REVALIDATION PASSED] Company can be promoted to company_master!")
    else:
        print(f"\n[REVALIDATION FAILED] Still missing: {still_missing}")
        for failure in blocking_failures:
            print(f"  - {failure['field']}: {failure['message']}")

    return RevalidationResult(
        passes=passes,
        still_missing=still_missing,
        validation_errors=validation_failures,
        merged_record=merged_record
    ).to_dict()


# ============================================================================
# CLI TESTING
# ============================================================================

if __name__ == "__main__":
    # Test case 1: Company missing website (should PASS after enrichment)
    print("TEST CASE 1: Company missing website")
    print("="*80)

    failed_company = {
        "company_unique_id": "04.04.01.02.00102.102",
        "company_name": "Mountaineer Casino Resort",
        "domain": None,
        "industry": "Gaming",
        "employee_count": 280,
        "website": None,  # Missing!
        "state": "West Virginia",
        "city": "New Cumberland"
    }

    enriched_data = {
        "website": "https://www.mountaineerparks.com"  # Found by enrichment!
    }

    result = revalidate_company(failed_company, enriched_data)

    print("\n" + "="*80)
    print("RESULT:")
    import json
    print(json.dumps(result, indent=2))
    print("="*80)

    # Test case 2: Company still missing website (should FAIL)
    print("\n\n")
    print("TEST CASE 2: Enrichment failed to find website")
    print("="*80)

    enriched_data_failed = {}  # Enrichment found nothing

    result2 = revalidate_company(failed_company, enriched_data_failed)

    print("\n" + "="*80)
    print("RESULT:")
    print(json.dumps(result2, indent=2))
    print("="*80)
