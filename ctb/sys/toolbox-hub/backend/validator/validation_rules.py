"""
Validation Rules - Barton Toolbox Hub
Barton Doctrine-compliant validation rules for company and people records

Doctrine ID: 04.04.02.04.10000.002
Blueprint: 04.svg.marketing.outreach.v1
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum


class ValidationSeverity(Enum):
    """Validation failure severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationFailure:
    """Represents a validation failure"""

    def __init__(self, field: str, rule: str, message: str, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.field = field
        self.rule = rule
        self.message = message
        self.severity = severity
        self.current_value = None

    def to_dict(self) -> Dict:
        return {
            "field": self.field,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity.value,
            "current_value": str(self.current_value) if self.current_value else None
        }


class CompanyValidator:
    """Validation rules for company records"""

    @staticmethod
    def validate_company_name(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate company_name field
        Rule: Must be present and length > 3
        """
        company_name = record.get("company_name", "")

        if not company_name or len(company_name.strip()) == 0:
            failure = ValidationFailure(
                field="company_name",
                rule="company_name_required",
                message="Company name is required",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = company_name
            return failure

        if len(company_name.strip()) <= 3:
            failure = ValidationFailure(
                field="company_name",
                rule="company_name_min_length",
                message="Company name must be longer than 3 characters",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = company_name
            return failure

        return None

    @staticmethod
    def validate_website(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate website field
        Rule: Must start with "http" and contain a domain
        """
        website = record.get("website", "")

        if not website or len(website.strip()) == 0:
            failure = ValidationFailure(
                field="website",
                rule="website_required",
                message="Website is required",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = website
            return failure

        website = website.strip()

        # Must start with http or https
        if not website.startswith("http://") and not website.startswith("https://"):
            failure = ValidationFailure(
                field="website",
                rule="website_protocol",
                message="Website must start with http:// or https://",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = website
            return failure

        # Must contain a domain (at least one dot)
        if "." not in website:
            failure = ValidationFailure(
                field="website",
                rule="website_domain",
                message="Website must contain a valid domain",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = website
            return failure

        return None

    @staticmethod
    def validate_employee_count(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate employee_count field
        Rule: Must be > 0
        """
        employee_count = record.get("employee_count")

        if employee_count is None:
            failure = ValidationFailure(
                field="employee_count",
                rule="employee_count_required",
                message="Employee count is required",
                severity=ValidationSeverity.WARNING
            )
            failure.current_value = employee_count
            return failure

        # Convert to int if string
        try:
            employee_count = int(employee_count)
        except (ValueError, TypeError):
            failure = ValidationFailure(
                field="employee_count",
                rule="employee_count_numeric",
                message="Employee count must be a number",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = employee_count
            return failure

        if employee_count <= 0:
            failure = ValidationFailure(
                field="employee_count",
                rule="employee_count_positive",
                message="Employee count must be greater than 0",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = employee_count
            return failure

        return None

    @staticmethod
    def validate_postal_code(record: Dict, state: str = "WV") -> Optional[ValidationFailure]:
        """
        Validate postal_code field for specific state
        Rule (WV): Must begin with 24 or 25
        """
        postal_code = record.get("postal_code", "")

        if not postal_code or len(str(postal_code).strip()) == 0:
            failure = ValidationFailure(
                field="postal_code",
                rule="postal_code_required",
                message=f"Postal code is required for {state}",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = postal_code
            return failure

        postal_code = str(postal_code).strip()

        # WV-specific validation
        if state == "WV":
            if not (postal_code.startswith("24") or postal_code.startswith("25")):
                failure = ValidationFailure(
                    field="postal_code",
                    rule="postal_code_wv_format",
                    message="West Virginia postal codes must start with 24 or 25",
                    severity=ValidationSeverity.ERROR
                )
                failure.current_value = postal_code
                return failure

        # General zip code format (5 or 9 digits)
        if not re.match(r'^\d{5}(-\d{4})?$', postal_code):
            failure = ValidationFailure(
                field="postal_code",
                rule="postal_code_format",
                message="Postal code must be in format 12345 or 12345-6789",
                severity=ValidationSeverity.WARNING
            )
            failure.current_value = postal_code
            return failure

        return None

    @staticmethod
    def validate_all(record: Dict, state: str = "WV") -> Tuple[bool, List[ValidationFailure]]:
        """
        Run all company validation rules

        Returns: (is_valid, list_of_failures)
        """
        failures = []

        # Run all validation rules
        rules = [
            CompanyValidator.validate_company_name(record),
            CompanyValidator.validate_website(record),
            CompanyValidator.validate_employee_count(record),
            CompanyValidator.validate_postal_code(record, state)
        ]

        # Collect failures
        for failure in rules:
            if failure is not None:
                failures.append(failure)

        # Record is valid if no CRITICAL or ERROR failures
        is_valid = not any(
            f.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
            for f in failures
        )

        return is_valid, failures


class PersonValidator:
    """Validation rules for people records"""

    @staticmethod
    def validate_full_name(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate full_name field
        Rule: Must contain a space (first + last name)
        """
        full_name = record.get("full_name", "")

        if not full_name or len(full_name.strip()) == 0:
            failure = ValidationFailure(
                field="full_name",
                rule="full_name_required",
                message="Full name is required",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = full_name
            return failure

        # Must contain at least one space (first + last name)
        if " " not in full_name.strip():
            failure = ValidationFailure(
                field="full_name",
                rule="full_name_format",
                message="Full name must include both first and last name",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = full_name
            return failure

        return None

    @staticmethod
    def validate_email(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate email field
        Rule: Must be valid email format
        """
        email = record.get("email", "")

        if not email or len(email.strip()) == 0:
            failure = ValidationFailure(
                field="email",
                rule="email_required",
                message="Email is required",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = email
            return failure

        email = email.strip()

        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            failure = ValidationFailure(
                field="email",
                rule="email_format",
                message="Email must be in valid format (e.g., user@domain.com)",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = email
            return failure

        return None

    @staticmethod
    def validate_title(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate title field
        Rule: Must include "HR", "CFO", or "CEO"
        """
        title = record.get("title", "")

        if not title or len(title.strip()) == 0:
            failure = ValidationFailure(
                field="title",
                rule="title_required",
                message="Title is required",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = title
            return failure

        title = title.strip().upper()

        # Must include one of the target titles
        valid_titles = ["HR", "CFO", "CEO"]
        if not any(target in title for target in valid_titles):
            failure = ValidationFailure(
                field="title",
                rule="title_executive",
                message="Title must include HR, CFO, or CEO",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = record.get("title", "")
            return failure

        return None

    @staticmethod
    def validate_company_link(record: Dict, valid_company_ids: set) -> Optional[ValidationFailure]:
        """
        Validate company_unique_id field
        Rule: Must exist in company_master table
        """
        company_id = record.get("company_unique_id", "")

        if not company_id or len(str(company_id).strip()) == 0:
            failure = ValidationFailure(
                field="company_unique_id",
                rule="company_link_required",
                message="Company unique ID is required",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = company_id
            return failure

        # Check if company exists
        if company_id not in valid_company_ids:
            failure = ValidationFailure(
                field="company_unique_id",
                rule="company_link_exists",
                message="Company unique ID does not exist in company_master",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = company_id
            return failure

        return None

    @staticmethod
    def validate_all(record: Dict, valid_company_ids: set = None) -> Tuple[bool, List[ValidationFailure]]:
        """
        Run all person validation rules

        Returns: (is_valid, list_of_failures)
        """
        failures = []

        # Run all validation rules
        rules = [
            PersonValidator.validate_full_name(record),
            PersonValidator.validate_email(record),
            PersonValidator.validate_title(record)
        ]

        # Add company link validation if valid_company_ids provided
        if valid_company_ids is not None:
            rules.append(PersonValidator.validate_company_link(record, valid_company_ids))

        # Collect failures
        for failure in rules:
            if failure is not None:
                failures.append(failure)

        # Record is valid if no CRITICAL or ERROR failures
        is_valid = not any(
            f.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
            for f in failures
        )

        return is_valid, failures


# Convenience functions
def validate_company(record: Dict, state: str = "WV") -> Tuple[bool, List[Dict]]:
    """
    Validate a company record

    Returns: (is_valid, list_of_failure_dicts)
    """
    is_valid, failures = CompanyValidator.validate_all(record, state)
    return is_valid, [f.to_dict() for f in failures]


def validate_person(record: Dict, valid_company_ids: set = None) -> Tuple[bool, List[Dict]]:
    """
    Validate a person record

    Returns: (is_valid, list_of_failure_dicts)
    """
    is_valid, failures = PersonValidator.validate_all(record, valid_company_ids)
    return is_valid, [f.to_dict() for f in failures]


if __name__ == "__main__":
    # Test validation rules
    print("="*60)
    print("Testing Validation Rules")
    print("="*60)

    # Test company validation
    print("\nCompany Validation Tests:")
    print("-"*60)

    test_company = {
        "company_name": "Acme Corp",
        "website": "https://acme.com",
        "employee_count": 250,
        "postal_code": "25301"
    }

    is_valid, failures = validate_company(test_company, state="WV")
    print(f"Test Company: {test_company['company_name']}")
    print(f"Valid: {is_valid}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f['field']}: {f['message']}")
    else:
        print("No failures")

    # Test invalid company
    print("\n")
    invalid_company = {
        "company_name": "XY",  # Too short
        "website": "acme.com",  # Missing http
        "employee_count": 0,  # Must be > 0
        "postal_code": "12345"  # Wrong state
    }

    is_valid, failures = validate_company(invalid_company, state="WV")
    print(f"Invalid Company: {invalid_company['company_name']}")
    print(f"Valid: {is_valid}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f['field']}: {f['message']}")

    # Test person validation
    print("\n" + "="*60)
    print("Person Validation Tests:")
    print("-"*60)

    test_person = {
        "full_name": "John Doe",
        "email": "john.doe@acme.com",
        "title": "Chief Financial Officer (CFO)",
        "company_unique_id": "04.04.02.04.30000.001"
    }

    valid_companies = {"04.04.02.04.30000.001"}
    is_valid, failures = validate_person(test_person, valid_companies)
    print(f"Test Person: {test_person['full_name']}")
    print(f"Valid: {is_valid}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f['field']}: {f['message']}")
    else:
        print("No failures")

    # Test invalid person
    print("\n")
    invalid_person = {
        "full_name": "John",  # No last name
        "email": "invalid-email",  # Bad format
        "title": "Manager",  # Not HR/CFO/CEO
        "company_unique_id": "invalid-id"  # Doesn't exist
    }

    is_valid, failures = validate_person(invalid_person, valid_companies)
    print(f"Invalid Person: {invalid_person['full_name']}")
    print(f"Valid: {is_valid}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f['field']}: {f['message']}")

    print("\n" + "="*60)
    print("✅ Validation rules tested successfully")
    print("="*60)
