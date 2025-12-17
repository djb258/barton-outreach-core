#!/usr/bin/env python3
"""
Test Apollo ID Validation with Source Type Doctrine
====================================================

Tests the new source_type-based apollo_id validation logic:
- Apollo-sourced records MUST have apollo_id
- Non-Apollo sources can skip apollo_id (warning only)

Author: Claude Code
Created: 2025-11-18
Barton ID: 04.04.02.04.50000.###
"""

from company_validator import validate_company
from people_validator import validate_person

# ============================================================================
# TEST CASES: COMPANY VALIDATION
# ============================================================================

def test_company_apollo_source_missing_apollo_id():
    """Test 1: Apollo-sourced company missing apollo_id → should FAIL"""
    company = {
        'company_name': 'Acme Corporation',
        'domain': 'acmecorp.com',
        'linkedin_url': 'https://linkedin.com/company/testcorp',
        'employee_count': '50',
        'industry': 'Technology',
        'location': 'San Francisco, CA',
        'source_type': 'apollo',  # Apollo source
        'apollo_id': None,  # Missing apollo_id
        'enrichment_attempt': 0,
    }

    result = validate_company(company, check_live_dns=False)

    print("Test 1: Company from Apollo missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: FAILED, bay_a, ['apollo_id_missing']")

    assert result['validation_status'] == 'failed', "Should fail validation"
    assert result['garage_bay'] == 'bay_a', "Should be Bay A (missing field)"
    assert 'apollo_id_missing' in result['reasons'], "Should have apollo_id_missing error"
    print("  [OK] PASSED\n")

def test_company_enrichment_source_missing_apollo_id():
    """Test 2: Enrichment-sourced company missing apollo_id → should PASS with warning"""
    company = {
        'company_name': 'Enriched Corp',
        'domain': 'enrichedcorp.com',
        'linkedin_url': 'https://linkedin.com/company/enrichedcorp',
        'employee_count': '100',
        'industry': 'Software',
        'location': 'Boston, MA',
        'source_type': 'enrichment',  # Enrichment source
        'apollo_id': None,  # Missing apollo_id (OK for enrichment)
        'enrichment_attempt': 0,
    }

    result = validate_company(company, check_live_dns=False)

    print("Test 2: Company from enrichment missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: PASSED, None, []")

    assert result['validation_status'] == 'passed', "Should pass validation"
    assert result['garage_bay'] is None, "Should not be routed to garage"
    assert 'apollo_id_missing' not in result['reasons'], "Should not have apollo_id_missing error"
    print("  [OK] PASSED\n")

def test_company_csv_source_missing_apollo_id():
    """Test 3: CSV-sourced company missing apollo_id → should PASS with warning"""
    company = {
        'company_name': 'CSV Import Corp',
        'domain': 'csvimport.com',
        'linkedin_url': 'https://linkedin.com/company/csvimport',
        'employee_count': '25',
        'industry': 'Manufacturing',
        'location': 'Detroit, MI',
        'source_type': 'csv',  # CSV source
        'apollo_id': None,  # Missing apollo_id (OK for CSV)
        'enrichment_attempt': 0,
    }

    result = validate_company(company, check_live_dns=False)

    print("Test 3: Company from CSV import missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: PASSED, None, []")

    assert result['validation_status'] == 'passed', "Should pass validation"
    assert result['garage_bay'] is None, "Should not be routed to garage"
    print("  [OK] PASSED\n")

def test_company_default_source_missing_apollo_id():
    """Test 4: Company without source_type (defaults to 'apollo') missing apollo_id → should FAIL"""
    company = {
        'company_name': 'Default Source Corp',
        'domain': 'defaultsource.com',
        'linkedin_url': 'https://linkedin.com/company/defaultsource',
        'employee_count': '75',
        'industry': 'Consulting',
        'location': 'New York, NY',
        # source_type not specified (defaults to 'apollo')
        'apollo_id': None,  # Missing apollo_id
        'enrichment_attempt': 0,
    }

    result = validate_company(company, check_live_dns=False)

    print("Test 4: Company without source_type (defaults to apollo) missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: FAILED, bay_a, ['apollo_id_missing']")

    assert result['validation_status'] == 'failed', "Should fail validation (default is apollo)"
    assert result['garage_bay'] == 'bay_a', "Should be Bay A (missing field)"
    assert 'apollo_id_missing' in result['reasons'], "Should have apollo_id_missing error"
    print("  [OK] PASSED\n")

# ============================================================================
# TEST CASES: PEOPLE VALIDATION
# ============================================================================

def test_person_apollo_source_missing_apollo_id():
    """Test 5: Apollo-sourced person missing apollo_id → should FAIL"""
    person = {
        'full_name': 'John Doe',
        'email': 'john.doe@testcorp.com',
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'title': 'VP of Engineering',
        'company_unique_id': '04.04.01.24.00024.024',
        'source_type': 'apollo',  # Apollo source
        'apollo_id': None,  # Missing apollo_id
        'enrichment_attempt': 0,
    }

    result = validate_person(person)

    print("Test 5: Person from Apollo missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: FAILED, bay_a, ['apollo_id_missing']")

    assert result['validation_status'] == 'failed', "Should fail validation"
    assert result['garage_bay'] == 'bay_a', "Should be Bay A (missing field)"
    assert 'apollo_id_missing' in result['reasons'], "Should have apollo_id_missing error"
    print("  [OK] PASSED\n")

def test_person_enrichment_source_missing_apollo_id():
    """Test 6: Enrichment-sourced person missing apollo_id → should PASS with warning"""
    person = {
        'full_name': 'Jane Smith',
        'email': 'jane.smith@enrichedcorp.com',
        'linkedin_url': 'https://linkedin.com/in/janesmith',
        'title': 'Director of Sales',
        'company_unique_id': '04.04.01.50.00050.050',
        'source_type': 'enrichment',  # Enrichment source
        'apollo_id': None,  # Missing apollo_id (OK for enrichment)
        'enrichment_attempt': 0,
    }

    result = validate_person(person)

    print("Test 6: Person from enrichment missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: PASSED, None, []")

    assert result['validation_status'] == 'passed', "Should pass validation"
    assert result['garage_bay'] is None, "Should not be routed to garage"
    assert 'apollo_id_missing' not in result['reasons'], "Should not have apollo_id_missing error"
    print("  [OK] PASSED\n")

def test_person_linkedin_scraper_source_missing_apollo_id():
    """Test 7: LinkedIn scraper-sourced person missing apollo_id → should PASS with warning"""
    person = {
        'full_name': 'Bob Johnson',
        'email': 'bob.johnson@linkedin.com',
        'linkedin_url': 'https://linkedin.com/in/bobjohnson',
        'title': 'Software Engineer',
        'company_unique_id': '04.04.01.75.00075.075',
        'source_type': 'linkedin_scraper',  # LinkedIn scraper source
        'apollo_id': None,  # Missing apollo_id (OK for scraper)
        'enrichment_attempt': 0,
    }

    result = validate_person(person)

    print("Test 7: Person from LinkedIn scraper missing apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: PASSED, None, []")

    assert result['validation_status'] == 'passed', "Should pass validation"
    assert result['garage_bay'] is None, "Should not be routed to garage"
    print("  [OK] PASSED\n")

def test_person_with_valid_apollo_id():
    """Test 8: Person with valid apollo_id → should PASS"""
    person = {
        'full_name': 'Alice Williams',
        'email': 'alice.williams@apollo.com',
        'linkedin_url': 'https://linkedin.com/in/alicewilliams',
        'title': 'CEO',
        'company_unique_id': '04.04.01.99.00099.099',
        'source_type': 'apollo',
        'apollo_id': 'apollo_12345678',  # Valid apollo_id
        'enrichment_attempt': 0,
    }

    result = validate_person(person)

    print("Test 8: Person with valid apollo_id")
    print(f"  Status: {result['validation_status']}")
    print(f"  Bay: {result['garage_bay']}")
    print(f"  Reasons: {result['reasons']}")
    print(f"  Expected: PASSED, None, []")

    assert result['validation_status'] == 'passed', "Should pass validation"
    assert result['garage_bay'] is None, "Should not be routed to garage"
    assert 'last_hash' in result and result['last_hash'], "Should have hash generated"
    print("  [OK] PASSED\n")

# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("APOLLO ID VALIDATION TESTS - NEW SOURCE TYPE DOCTRINE")
    print("=" * 80)
    print()

    print("COMPANY VALIDATION TESTS")
    print("-" * 80)
    test_company_apollo_source_missing_apollo_id()
    test_company_enrichment_source_missing_apollo_id()
    test_company_csv_source_missing_apollo_id()
    test_company_default_source_missing_apollo_id()

    print("PEOPLE VALIDATION TESTS")
    print("-" * 80)
    test_person_apollo_source_missing_apollo_id()
    test_person_enrichment_source_missing_apollo_id()
    test_person_linkedin_scraper_source_missing_apollo_id()
    test_person_with_valid_apollo_id()

    print("=" * 80)
    print("ALL TESTS PASSED [OK]")
    print("=" * 80)
    print()
    print("Summary:")
    print("  - Apollo-sourced records without apollo_id: FAIL validation")
    print("  - Non-Apollo records without apollo_id: PASS with warning")
    print("  - Default (no source_type): Treated as Apollo -> FAIL if missing")
    print("  - Records with valid apollo_id: Always PASS")
