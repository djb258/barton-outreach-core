"""
Test: People Slot Contract Enforcement
Version: 1.0.0
Date: 2026-01-09

DOCTRINE: A slot is FILLED if and only if:
  1. full_name IS NOT NULL AND != ''
  2. title IS NOT NULL AND != ''
  3. linkedin_url IS NOT NULL AND != ''

All other fields (email, phone, socials) are NON-BLOCKING.
Email enrichment may enhance a filled slot, but MUST NEVER
affect slot validity or status.
"""

import pytest
import sys
from pathlib import Path

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ops.validation.validation_rules import PersonValidator, ValidationSeverity


class TestPeopleSlotContract:
    """Test suite for People Slot Contract enforcement."""

    # ==========================================================================
    # SLOT CONTRACT TESTS - Core Doctrine
    # ==========================================================================

    def test_slot_contract_valid_with_all_required_fields(self):
        """Slot contract passes with full_name + title + linkedin_url."""
        record = {
            "full_name": "Jane Doe",
            "title": "Chief Executive Officer",
            "linkedin_url": "https://linkedin.com/in/janedoe"
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is True
        assert len(failures) == 0

    def test_slot_contract_valid_without_email(self):
        """Slot contract passes WITHOUT email (email is optional)."""
        record = {
            "full_name": "John Smith",
            "title": "VP of Operations",
            "linkedin_url": "https://linkedin.com/in/johnsmith",
            # NO EMAIL - this should still pass!
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is True, "Slot fill MUST NOT require email"
        assert len(failures) == 0

    def test_slot_contract_fails_without_full_name(self):
        """Slot contract fails without full_name."""
        record = {
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/someone",
            "email": "ceo@company.com"  # Email doesn't help!
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False
        assert any(f.field == "full_name" for f in failures)

    def test_slot_contract_fails_without_title(self):
        """Slot contract fails without title."""
        record = {
            "full_name": "Jane Doe",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "email": "jane@company.com"  # Email doesn't help!
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False
        assert any(f.field == "title" for f in failures)

    def test_slot_contract_fails_without_linkedin_url(self):
        """Slot contract fails without linkedin_url."""
        record = {
            "full_name": "Jane Doe",
            "title": "CEO",
            "email": "jane@company.com"  # Email doesn't help!
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False
        assert any(f.field == "linkedin_url" for f in failures)

    def test_slot_contract_fails_with_email_only(self):
        """
        CRITICAL: Slot with ONLY email MUST FAIL.
        Email-only is NOT a valid slot fill.
        """
        record = {
            "email": "ceo@company.com"  # Only email, no contract fields
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False, "Email-only MUST NOT fill a slot"
        assert len(failures) == 3  # Missing full_name, title, linkedin_url

    def test_slot_contract_requires_valid_linkedin_format(self):
        """LinkedIn URL must contain 'linkedin.com/in/'."""
        record = {
            "full_name": "Jane Doe",
            "title": "CEO",
            "linkedin_url": "https://twitter.com/janedoe"  # Wrong format!
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False
        assert any("linkedin_url" in f.field for f in failures)

    # ==========================================================================
    # EMAIL VALIDATION TESTS - Must be WARNING only
    # ==========================================================================

    def test_email_missing_is_warning_not_error(self):
        """Missing email returns WARNING, not ERROR."""
        record = {"email": ""}
        failure = PersonValidator.validate_email(record)
        
        assert failure is not None
        assert failure.severity == ValidationSeverity.WARNING, \
            "Email missing MUST be WARNING, not ERROR"

    def test_email_invalid_format_is_warning_not_error(self):
        """Invalid email format returns WARNING, not ERROR."""
        record = {"email": "not-an-email"}
        failure = PersonValidator.validate_email(record)
        
        assert failure is not None
        assert failure.severity == ValidationSeverity.WARNING, \
            "Email format error MUST be WARNING, not ERROR"

    def test_email_valid_returns_none(self):
        """Valid email returns no failure."""
        record = {"email": "valid@company.com"}
        failure = PersonValidator.validate_email(record)
        
        assert failure is None

    # ==========================================================================
    # INTEGRATION TESTS - Full validation flow
    # ==========================================================================

    def test_full_validation_passes_without_email(self):
        """
        validate_all() should pass for records meeting slot contract,
        even without email.
        """
        record = {
            "person_id": "PSN-123",
            "full_name": "Jane Doe",
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "timestamp_last_updated": "2026-01-09T12:00:00Z"
            # NO EMAIL
        }
        is_valid, failures = PersonValidator.validate_all(record)
        
        # Should only have WARNING for missing email, not ERROR
        errors = [f for f in failures if f.severity == ValidationSeverity.ERROR]
        warnings = [f for f in failures if f.severity == ValidationSeverity.WARNING]
        
        # No blocking errors for slot contract compliant records
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"

    def test_full_validation_fails_with_email_only(self):
        """
        validate_all() should fail for email-only records
        (missing slot contract fields).
        """
        record = {
            "person_id": "PSN-456",
            "email": "ceo@company.com",
            "timestamp_last_updated": "2026-01-09T12:00:00Z"
            # Missing: full_name, title, linkedin_url
        }
        is_valid, failures = PersonValidator.validate_all(record)
        
        errors = [f for f in failures if f.severity == ValidationSeverity.ERROR]
        
        # Should have errors for missing contract fields
        assert len(errors) >= 3, "Email-only should fail slot contract"


class TestSlotContractDoctrine:
    """Test doctrine-level behaviors for slot contract."""

    def test_empty_strings_treated_as_missing(self):
        """Empty strings are treated as NULL for contract purposes."""
        record = {
            "full_name": "  ",  # Whitespace only
            "title": "",
            "linkedin_url": ""
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is False
        assert len(failures) == 3

    def test_whitespace_is_trimmed(self):
        """Whitespace is trimmed when validating."""
        record = {
            "full_name": "  Jane Doe  ",
            "title": "  CEO  ",
            "linkedin_url": "  https://linkedin.com/in/janedoe  "
        }
        meets_contract, failures = PersonValidator.validate_slot_contract(record)
        
        assert meets_contract is True

    def test_phone_does_not_affect_slot_contract(self):
        """Phone fields are ignored for slot contract (optional enrichment)."""
        record_with_phone = {
            "full_name": "Jane Doe",
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/janedoe",
            "phone": "555-1234"
        }
        record_without_phone = {
            "full_name": "Jane Doe",
            "title": "CEO",
            "linkedin_url": "https://linkedin.com/in/janedoe"
        }
        
        result_with, _ = PersonValidator.validate_slot_contract(record_with_phone)
        result_without, _ = PersonValidator.validate_slot_contract(record_without_phone)
        
        assert result_with == result_without, "Phone must not affect slot contract"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
