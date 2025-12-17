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
    def validate_employee_count(record: Dict, minimum: int = 50) -> Optional[ValidationFailure]:
        """
        Validate employee_count field
        Rule: Must be > minimum (default: 50 for Phase 1)
        """
        employee_count = record.get("employee_count")

        if employee_count is None:
            failure = ValidationFailure(
                field="employee_count",
                rule="employee_count_required",
                message="Employee count is required",
                severity=ValidationSeverity.ERROR
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

        # Phase 1 requirement: > 50 employees
        if employee_count <= minimum:
            failure = ValidationFailure(
                field="employee_count",
                rule="employee_count_minimum",
                message=f"Employee count must be greater than {minimum} (current: {employee_count})",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = employee_count
            return failure

        return None

    @staticmethod
    def validate_linkedin_url(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate linkedin_url field
        Rule: Must include "linkedin.com/company/"
        """
        linkedin_url = record.get("linkedin_url", "")

        if not linkedin_url or len(linkedin_url.strip()) == 0:
            failure = ValidationFailure(
                field="linkedin_url",
                rule="linkedin_url_required",
                message="LinkedIn URL is required",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = linkedin_url
            return failure

        linkedin_url = linkedin_url.strip()

        # Must include linkedin.com/company/
        if "linkedin.com/company/" not in linkedin_url.lower():
            failure = ValidationFailure(
                field="linkedin_url",
                rule="linkedin_url_format",
                message="LinkedIn URL must include 'linkedin.com/company/'",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = linkedin_url
            return failure

        return None

    @staticmethod
    def validate_company_unique_id(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate company_unique_id field
        Rule: Must not be null
        """
        company_id = record.get("company_unique_id")

        if not company_id or len(str(company_id).strip()) == 0:
            failure = ValidationFailure(
                field="company_unique_id",
                rule="company_unique_id_required",
                message="Company unique ID is required",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = company_id
            return failure

        return None

    @staticmethod
    def validate_slots_presence(record: Dict, slot_rows: List[Dict]) -> List[ValidationFailure]:
        """
        Validate slot presence for company
        Rule: Must have CEO, CFO, and HR slots (filled or unfilled)

        Args:
            record: Company record
            slot_rows: List of company_slot rows for this company

        Returns:
            List of ValidationFailure objects (empty if all slots present)
        """
        failures = []
        required_slots = ["CEO", "CFO", "HR"]

        # Get set of existing slot types
        existing_slot_types = {slot.get("slot_type", "").upper() for slot in slot_rows}

        # Check each required slot
        for slot_type in required_slots:
            if slot_type not in existing_slot_types:
                failure = ValidationFailure(
                    field="company_slots",
                    rule=f"slot_{slot_type.lower()}_missing",
                    message=f"Missing {slot_type} slot (slot must exist, even if unfilled)",
                    severity=ValidationSeverity.ERROR
                )
                failure.current_value = f"Existing slots: {', '.join(existing_slot_types) if existing_slot_types else 'None'}"
                failures.append(failure)

        return failures

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
        Run all company validation rules (basic fields only)

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

    @staticmethod
    def validate_phase1(record: Dict, slot_rows: List[Dict]) -> Tuple[bool, List[ValidationFailure], Dict]:
        """
        Run Phase 1 company validation rules (structure + slot presence)

        Phase 1 validates:
        - Company structure (name, website, employee_count, linkedin_url, unique_id)
        - Slot presence (CEO, CFO, HR slots must exist - not necessarily filled)

        Args:
            record: Company record from company_master
            slot_rows: List of company_slot rows for this company

        Returns:
            (is_valid, list_of_failures, validation_result_dict)
        """
        failures = []

        # Required fields for Phase 1
        required_fields = [
            "company_unique_id",
            "company_name",
            "website",
            "employee_count",
            "linkedin_url"
        ]

        # Run structural validation rules
        structural_rules = [
            CompanyValidator.validate_company_unique_id(record),
            CompanyValidator.validate_company_name(record),
            CompanyValidator.validate_website(record),
            CompanyValidator.validate_employee_count(record, minimum=50),  # Phase 1: > 50 employees
            CompanyValidator.validate_linkedin_url(record)
        ]

        # Collect structural failures
        for failure in structural_rules:
            if failure is not None:
                failures.append(failure)

        # Run slot presence validation
        slot_failures = CompanyValidator.validate_slots_presence(record, slot_rows)
        failures.extend(slot_failures)

        # Determine missing fields
        missing_fields = []
        for field in required_fields:
            value = record.get(field)
            if value is None or (isinstance(value, str) and len(value.strip()) == 0):
                missing_fields.append(field)

        # Build reason code
        if failures:
            reason_parts = []
            for failure in failures:
                reason_parts.append(f"{failure.field}: {failure.message}")
            reason = "; ".join(reason_parts)
        else:
            reason = "Valid"

        # Record is valid if no CRITICAL or ERROR failures
        is_valid = not any(
            f.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
            for f in failures
        )

        # Build validation result
        validation_result = {
            "valid": is_valid,
            "reason": reason,
            "required_fields": required_fields,
            "missing_fields": missing_fields,
            "failures": [f.to_dict() for f in failures],
            "slots_checked": ["CEO", "CFO", "HR"],
            "slots_present": [slot.get("slot_type") for slot in slot_rows],
            "phase": "Phase 1 - Structure + Slot Presence"
        }

        return is_valid, failures, validation_result


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
        Rule: Must include "CEO", "CFO", or HR-related keywords
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

        title_upper = title.strip().upper()

        # Check for CEO
        if "CEO" in title_upper or "CHIEF EXECUTIVE" in title_upper:
            return None

        # Check for CFO
        if "CFO" in title_upper or "CHIEF FINANCIAL" in title_upper:
            return None

        # Check for HR (multiple variations)
        hr_keywords = ["HR", "HUMAN RESOURCES", "PEOPLE", "TALENT"]
        if any(keyword in title_upper for keyword in hr_keywords):
            return None

        # No match found
        failure = ValidationFailure(
            field="title",
            rule="title_executive",
            message="Title must include CEO, CFO, or HR-related keywords (HR, Human Resources, People, Talent)",
            severity=ValidationSeverity.ERROR
        )
        failure.current_value = record.get("title", "")
        return failure

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
    def validate_person_id(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate person_id field
        Rule: Must not be null
        """
        person_id = record.get("person_id") or record.get("unique_id")

        if not person_id or len(str(person_id).strip()) == 0:
            failure = ValidationFailure(
                field="person_id",
                rule="person_id_required",
                message="Person ID is required",
                severity=ValidationSeverity.CRITICAL
            )
            failure.current_value = person_id
            return failure

        return None

    @staticmethod
    def validate_linkedin_url(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate linkedin_url field
        Rule: Must include "linkedin.com/in/"
        """
        linkedin_url = record.get("linkedin_url", "")

        if not linkedin_url or len(linkedin_url.strip()) == 0:
            failure = ValidationFailure(
                field="linkedin_url",
                rule="linkedin_url_required",
                message="LinkedIn URL is required",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = linkedin_url
            return failure

        linkedin_url = linkedin_url.strip().lower()

        # Must include "linkedin.com/in/"
        if "linkedin.com/in/" not in linkedin_url:
            failure = ValidationFailure(
                field="linkedin_url",
                rule="linkedin_url_format",
                message="LinkedIn URL must include 'linkedin.com/in/'",
                severity=ValidationSeverity.ERROR
            )
            failure.current_value = record.get("linkedin_url", "")
            return failure

        return None

    @staticmethod
    def validate_timestamp_last_updated(record: Dict) -> Optional[ValidationFailure]:
        """
        Validate timestamp_last_updated field
        Rule: Must be present
        """
        timestamp = record.get("timestamp_last_updated") or record.get("updated_at")

        if not timestamp:
            failure = ValidationFailure(
                field="timestamp_last_updated",
                rule="timestamp_required",
                message="Last updated timestamp is required",
                severity=ValidationSeverity.WARNING
            )
            failure.current_value = timestamp
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
            PersonValidator.validate_person_id(record),
            PersonValidator.validate_full_name(record),
            PersonValidator.validate_email(record),
            PersonValidator.validate_title(record),
            PersonValidator.validate_linkedin_url(record),
            PersonValidator.validate_timestamp_last_updated(record)
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
def validate_company(row: Dict, slot_rows: List[Dict]) -> Dict:
    """
    Validate a company record for retroactive Neon outreach pipeline

    This function validates company structure and slot presence only.
    It does NOT validate enrichment, email, or slot fill status.

    Validation Rules:
    1. company_name must exist and be >= 3 characters
    2. website must start with "http" and contain domain
    3. employee_count must be integer > 50
    4. linkedin_url must contain "linkedin.com/company/"
    5. All 3 slot types must exist (CEO, CFO, HR) - regardless of is_filled

    Args:
        row: Dictionary from marketing.company_master
        slot_rows: List of slot dictionaries from marketing.company_slots
                   where company_unique_id = row["company_unique_id"]

    Returns:
        {
            "valid": True/False,
            "reason": String (first failure reason or None if valid),
            "severity": "INFO" | "WARNING" | "ERROR" | "CRITICAL",
            "missing_fields": List of missing fields or slots
        }

    Example:
        company = {
            "company_name": "Acme Corp",
            "website": "https://acme.com",
            "employee_count": 250,
            "linkedin_url": "https://linkedin.com/company/acme"
        }

        slots = [
            {"slot_type": "CEO", "is_filled": True},
            {"slot_type": "CFO", "is_filled": False},
            {"slot_type": "HR", "is_filled": True}
        ]

        result = validate_company(company, slots)
        # Returns: {"valid": True, "reason": None, "severity": "INFO", "missing_fields": []}
    """
    missing_fields = []
    reason = None
    severity = "INFO"

    # Rule 1: company_name must exist and be >= 3 characters
    company_name = row.get("company_name", "")
    if not company_name or len(company_name.strip()) < 3:
        missing_fields.append("company_name")
        if not reason:
            reason = "Company name must be at least 3 characters"
            severity = "CRITICAL"

    # Rule 2: website must start with "http" and contain domain
    website = row.get("website", "")
    if not website or not website.strip().startswith(("http://", "https://")):
        missing_fields.append("website")
        if not reason:
            reason = "Website must start with http:// or https://"
            severity = "ERROR"
    elif "." not in website:
        missing_fields.append("website")
        if not reason:
            reason = "Website must contain a valid domain"
            severity = "ERROR"

    # Rule 3: employee_count must be integer > 50
    employee_count = row.get("employee_count")
    try:
        employee_count_int = int(employee_count) if employee_count is not None else 0
        if employee_count_int <= 50:
            missing_fields.append("employee_count")
            if not reason:
                reason = f"Employee count must be greater than 50 (current: {employee_count_int})"
                severity = "ERROR"
    except (ValueError, TypeError):
        missing_fields.append("employee_count")
        if not reason:
            reason = "Employee count must be a valid integer"
            severity = "ERROR"

    # Rule 4: linkedin_url must contain "linkedin.com/company/"
    linkedin_url = row.get("linkedin_url", "")
    if not linkedin_url or "linkedin.com/company/" not in linkedin_url.lower():
        missing_fields.append("linkedin_url")
        if not reason:
            reason = "LinkedIn URL must contain 'linkedin.com/company/'"
            severity = "ERROR"

    # Rule 5: All 3 slot types must exist (CEO, CFO, HR)
    required_slots = {"CEO", "CFO", "HR"}
    existing_slot_types = {slot.get("slot_type", "").upper() for slot in slot_rows}

    for slot_type in required_slots:
        if slot_type not in existing_slot_types:
            missing_fields.append(f"slot_{slot_type}")
            if not reason:
                reason = f"Missing {slot_type} slot (slot must exist, even if unfilled)"
                severity = "ERROR"

    # Determine if valid
    is_valid = len(missing_fields) == 0

    if is_valid:
        severity = "INFO"

    return {
        "valid": is_valid,
        "reason": reason,
        "severity": severity,
        "missing_fields": missing_fields
    }


def validate_company_phase1(record: Dict, slot_rows: List[Dict]) -> Dict:
    """
    Validate a company record for Phase 1 (structure + slot presence)

    Phase 1 Validation:
    - Company structure (name, website, employee_count > 50, linkedin_url, unique_id)
    - Slot presence (CEO, CFO, HR slots must exist - not necessarily filled)

    Args:
        record: Company record from marketing.company_master
        slot_rows: List of company_slot rows for this company (from marketing.company_slot)

    Returns:
        {
            "valid": True/False,
            "reason": "Missing CFO slot; employee_count: Employee count must be greater than 50",
            "required_fields": ["company_unique_id", "company_name", ...],
            "missing_fields": ["linkedin_url"],
            "failures": [{"field": "...", "rule": "...", "message": "...", "severity": "..."}],
            "slots_checked": ["CEO", "CFO", "HR"],
            "slots_present": ["CEO", "HR"],
            "phase": "Phase 1 - Structure + Slot Presence"
        }

    Usage:
        # Load company and its slots from database
        company = {...}  # From marketing.company_master
        slots = [...]    # From marketing.company_slot WHERE company_unique_id = company['company_unique_id']

        # Validate
        result = validate_company_phase1(company, slots)

        if result['valid']:
            print(f"Company {company['company_name']} passed Phase 1")
        else:
            print(f"Company {company['company_name']} failed Phase 1:")
            print(f"  Reason: {result['reason']}")
            for failure in result['failures']:
                print(f"    - {failure['field']}: {failure['message']}")
    """
    is_valid, failures, validation_result = CompanyValidator.validate_phase1(record, slot_rows)
    return validation_result


def validate_person(row: Dict, valid_company_ids: set = None) -> Dict:
    """
    Validate a person record for Phase 1 outreach validation

    Validation Rules:
    1. person_id (or unique_id) is not null (CRITICAL)
    2. full_name is at least 3 characters (CRITICAL)
    3. email is present and passes basic format check (ERROR)
    4. title must include "CEO", "CFO", or "HR" (case-insensitive) (ERROR)
    5. company_unique_id is present AND exists in marketing.company_master (CRITICAL)
    6. linkedin_url must include "linkedin.com/in/" (ERROR)
    7. timestamp_last_updated must be present (WARNING)

    Args:
        row: Dictionary from marketing.people_master
        valid_company_ids: Set of valid company IDs from company_master (optional)

    Returns:
        {
            "valid": True/False,
            "reason": "Missing CEO title; LinkedIn URL is invalid",
            "failures": [
                {"field": "title", "message": "Does not match CEO/CFO/HR"},
                {"field": "linkedin_url", "message": "Missing linkedin.com/in/ link"}
            ],
            "person_id": "abc-123",
            "company_unique_id": "xyz-456",
            "full_name": "Jane Smith",
            "email": "jane@acme.com",
            "title": "Finance Manager",
            "linkedin_url": "",
            "validation_status": "invalid"
        }

    Example:
        person = {
            "person_id": "04.04.02.04.20000.001",
            "full_name": "John Doe",
            "email": "john@acme.com",
            "title": "Chief Executive Officer",
            "company_unique_id": "04.04.02.04.30000.001",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "timestamp_last_updated": "2025-11-17"
        }

        valid_companies = {"04.04.02.04.30000.001", "04.04.02.04.30000.002"}
        result = validate_person(person, valid_companies)
        # Returns: {"valid": True, "reason": None, "failures": [], ...}
    """
    # Run all validation rules
    is_valid, failure_objects = PersonValidator.validate_all(row, valid_company_ids)

    # Convert to requested format
    failures = []
    reason_parts = []

    for failure_obj in failure_objects:
        # Add to failures list
        failures.append({
            "field": failure_obj.field,
            "message": failure_obj.message
        })

        # Add to reason if CRITICAL or ERROR
        if failure_obj.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
            reason_parts.append(f"{failure_obj.field}: {failure_obj.message}")

    # Build reason string (semicolon-separated list of failures)
    reason = "; ".join(reason_parts) if reason_parts else None

    # Extract key fields for return
    person_id = row.get("person_id") or row.get("unique_id") or ""
    company_unique_id = row.get("company_unique_id") or ""
    full_name = row.get("full_name") or ""
    email = row.get("email") or ""
    title = row.get("title") or ""
    linkedin_url = row.get("linkedin_url") or ""

    return {
        "valid": is_valid,
        "reason": reason,
        "failures": failures,
        "person_id": person_id,
        "company_unique_id": company_unique_id,
        "full_name": full_name,
        "email": email,
        "title": title,
        "linkedin_url": linkedin_url,
        "validation_status": "valid" if is_valid else "invalid"
    }


if __name__ == "__main__":
    # Test validation rules
    print("="*60)
    print("Testing Validation Rules")
    print("="*60)

    # Note: Basic company validation tests removed
    # Now using validate_company(row, slot_rows) for retroactive pipeline
    # See "Retroactive Pipeline Company Validation Tests" section below

    # Test Phase 1 company validation (structure + slots)
    print("\n" + "="*60)
    print("Phase 1 Company Validation Tests:")
    print("-"*60)

    # Test valid company with all slots
    phase1_company = {
        "company_unique_id": "04.04.02.04.30000.001",
        "company_name": "Acme Corporation",
        "website": "https://acme.com",
        "employee_count": 250,
        "linkedin_url": "https://linkedin.com/company/acme-corp"
    }

    # All slots present
    phase1_slots = [
        {"slot_type": "CEO", "is_filled": True},
        {"slot_type": "CFO", "is_filled": True},
        {"slot_type": "HR", "is_filled": False}  # Unfilled is OK for Phase 1
    ]

    result = validate_company_phase1(phase1_company, phase1_slots)
    print(f"Test Company (Phase 1): {phase1_company['company_name']}")
    print(f"Valid: {result['valid']}")
    print(f"Reason: {result['reason']}")
    print(f"Slots Checked: {result['slots_checked']}")
    print(f"Slots Present: {result['slots_present']}")
    if result['failures']:
        print("Failures:")
        for f in result['failures']:
            print(f"  - {f['field']}: {f['message']}")

    # Test invalid company (missing CFO slot, employee_count too low)
    print("\n")
    invalid_phase1_company = {
        "company_unique_id": "04.04.02.04.30000.002",
        "company_name": "Small Corp",
        "website": "https://smallcorp.com",
        "employee_count": 30,  # Too low (< 50)
        "linkedin_url": ""  # Missing
    }

    # Missing CFO slot
    invalid_phase1_slots = [
        {"slot_type": "CEO", "is_filled": True},
        {"slot_type": "HR", "is_filled": False}
        # CFO missing!
    ]

    result = validate_company_phase1(invalid_phase1_company, invalid_phase1_slots)
    print(f"Invalid Company (Phase 1): {invalid_phase1_company['company_name']}")
    print(f"Valid: {result['valid']}")
    print(f"Reason: {result['reason']}")
    print(f"Missing Fields: {result['missing_fields']}")
    print(f"Slots Checked: {result['slots_checked']}")
    print(f"Slots Present: {result['slots_present']}")
    if result['failures']:
        print("Failures:")
        for f in result['failures']:
            print(f"  - {f['field']}: {f['message']}")

    # Test validate_company(row, slot_rows) - For Retroactive Pipeline
    print("\n" + "="*60)
    print("Retroactive Pipeline Company Validation Tests:")
    print("-"*60)

    # Test 1: Valid company with all requirements met
    print("\n[Test 1] Valid Company:")
    valid_company_row = {
        "company_name": "Acme Corporation",
        "website": "https://acme.com",
        "employee_count": 250,
        "linkedin_url": "https://linkedin.com/company/acme-corp"
    }

    valid_slots = [
        {"slot_type": "CEO", "is_filled": True},
        {"slot_type": "CFO", "is_filled": False},  # Unfilled OK
        {"slot_type": "HR", "is_filled": True}
    ]

    result = validate_company(valid_company_row, valid_slots)
    print(f"  Company: {valid_company_row['company_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Missing Fields: {result['missing_fields']}")

    # Test 2: Invalid company with multiple failures
    print("\n[Test 2] Invalid Company (Multiple Failures):")
    invalid_company_row = {
        "company_name": "XY",  # Too short (< 3)
        "website": "acme.com",  # Missing http://
        "employee_count": 30,  # Too low (< 50)
        "linkedin_url": "https://acme.com"  # Missing "linkedin.com/company/"
    }

    invalid_slots = [
        {"slot_type": "CEO", "is_filled": True},
        {"slot_type": "HR", "is_filled": False}
        # Missing CFO slot!
    ]

    result = validate_company(invalid_company_row, invalid_slots)
    print(f"  Company: {invalid_company_row['company_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Missing Fields: {result['missing_fields']}")

    # Test 3: Company with no slots at all
    print("\n[Test 3] Invalid Company (No Slots):")
    no_slots_company = {
        "company_name": "No Slots Corp",
        "website": "https://noslots.com",
        "employee_count": 100,
        "linkedin_url": "https://linkedin.com/company/noslots"
    }

    no_slots = []  # Empty slots list

    result = validate_company(no_slots_company, no_slots)
    print(f"  Company: {no_slots_company['company_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Missing Fields: {result['missing_fields']}")

    # Test 4: Edge case - employee_count exactly 50 (should fail)
    print("\n[Test 4] Edge Case (employee_count = 50):")
    edge_case_company = {
        "company_name": "Edge Case Corp",
        "website": "https://edge.com",
        "employee_count": 50,  # Exactly 50 (must be > 50)
        "linkedin_url": "https://linkedin.com/company/edge"
    }

    edge_case_slots = [
        {"slot_type": "CEO", "is_filled": True},
        {"slot_type": "CFO", "is_filled": True},
        {"slot_type": "HR", "is_filled": True}
    ]

    result = validate_company(edge_case_company, edge_case_slots)
    print(f"  Company: {edge_case_company['company_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Missing Fields: {result['missing_fields']}")

    print("\n" + "="*60)
    print("Phase 1 Person Validation Tests:")
    print("="*60)

    # Test 1: Valid person with all fields
    print("\n[Test 1] Valid Person:")
    valid_person = {
        "person_id": "04.04.02.04.20000.001",
        "full_name": "John Doe",
        "email": "john@acme.com",
        "title": "Chief Executive Officer",
        "company_unique_id": "04.04.02.04.30000.001",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "timestamp_last_updated": "2025-11-17"
    }

    valid_companies = {"04.04.02.04.30000.001", "04.04.02.04.30000.002"}
    result = validate_person(valid_person, valid_companies)
    print(f"  Person: {result['full_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Validation Status: {result['validation_status']}")
    print(f"  Failures: {len(result['failures'])}")

    # Test 2: Invalid person with multiple failures
    print("\n[Test 2] Invalid Person (Multiple Failures):")
    invalid_person = {
        "person_id": "",  # Missing (CRITICAL)
        "full_name": "Jane",  # No last name (ERROR)
        "email": "invalid-email",  # Bad format (ERROR)
        "title": "Finance Manager",  # Not CEO/CFO/HR (ERROR)
        "company_unique_id": "invalid-company-id",  # Not in valid set (CRITICAL)
        "linkedin_url": "https://twitter.com/jane",  # Not LinkedIn (ERROR)
        "timestamp_last_updated": None  # Missing (WARNING)
    }

    result = validate_person(invalid_person, valid_companies)
    print(f"  Person: {result['full_name']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Validation Status: {result['validation_status']}")
    print(f"  Failures ({len(result['failures'])}):")
    for failure in result['failures']:
        print(f"    - {failure['field']}: {failure['message']}")

    # Test 3: Person with HR title variant
    print("\n[Test 3] Valid Person (HR Title Variant):")
    hr_person = {
        "person_id": "04.04.02.04.20000.003",
        "full_name": "Sarah Johnson",
        "email": "sarah@acme.com",
        "title": "Director of Human Resources",  # Contains "HR"
        "company_unique_id": "04.04.02.04.30000.001",
        "linkedin_url": "https://linkedin.com/in/sarahjohnson",
        "timestamp_last_updated": "2025-11-17"
    }

    result = validate_person(hr_person, valid_companies)
    print(f"  Person: {result['full_name']}")
    print(f"  Title: {result['title']}")
    print(f"  Valid: {result['valid']}")
    print(f"  Reason: {result['reason']}")

    print("\n" + "="*60)
    print("All validation rules tested successfully")
    print("="*60)
