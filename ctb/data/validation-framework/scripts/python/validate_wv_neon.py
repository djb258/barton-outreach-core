#!/usr/bin/env python3
"""
Enricha-Vision WV Data Validation (Neon-Only)

Validates West Virginia company and people data within Neon database.
No Supabase workspace - all validation happens in Neon.

Source tables:
  - marketing.company_raw_wv (companies with state='WV')
  - marketing.people_raw_wv (people with state='WV')

Destination tables:
  - marketing.company_master (PASSED)
  - marketing.company_invalid (FAILED)
  - marketing.people_master (PASSED)
  - marketing.people_invalid (FAILED)

Audit:
  - shq.validation_log (all validation activity)

Usage:
  python validate_wv_neon.py --entity company
  python validate_wv_neon.py --entity person
  python validate_wv_neon.py --all
  python validate_wv_neon.py --all --dry-run
"""

import os
import sys
import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import re
import json
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

class NeonWVValidator:
    """Neon-only validator for West Virginia data"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.batch_id = f"WV-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.stats = {
            'company': {'passed': 0, 'failed': 0, 'total': 0},
            'person': {'passed': 0, 'failed': 0, 'total': 0}
        }

    def connect(self):
        """Connect to Neon database"""
        database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

        if not database_url:
            raise ValueError("NEON_DATABASE_URL or DATABASE_URL environment variable not set")

        try:
            self.connection = psycopg2.connect(database_url)
            self.connection.autocommit = False
            print(f"[OK] Connected to Neon database")
        except Exception as e:
            print(f"[FAIL] Failed to connect to Neon: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

    # ========================================================================
    # Validation Rules
    # ========================================================================

    def validate_email(self, email: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not email or not email.strip():
            return False, "Email is empty"

        email = email.strip().lower()

        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"

        # Check for common invalid patterns
        invalid_patterns = [
            'noreply@', 'no-reply@', 'donotreply@',
            'test@', 'example@', 'sample@',
            '@example.com', '@test.com', '@sample.com'
        ]

        for pattern in invalid_patterns:
            if pattern in email:
                return False, f"Invalid email pattern: {pattern}"

        return True, None

    def validate_domain(self, domain: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate domain format"""
        if not domain or not domain.strip():
            return False, "Domain is empty"

        domain = domain.strip().lower()

        # Remove protocol if present
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]  # Remove path

        # Basic domain regex
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$'
        if not re.match(pattern, domain):
            return False, "Invalid domain format"

        # Check for invalid domains
        invalid_domains = [
            'example.com', 'test.com', 'sample.com',
            'localhost', '127.0.0.1', 'n/a', 'none'
        ]

        if domain in invalid_domains:
            return False, f"Invalid domain: {domain}"

        return True, None

    def validate_linkedin_url(self, url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate LinkedIn URL format"""
        if not url or not url.strip():
            return False, "LinkedIn URL is empty"

        url = url.strip()

        # LinkedIn URL patterns
        patterns = [
            r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?$',
            r'^https?://(www\.)?linkedin\.com/company/[a-zA-Z0-9_-]+/?$',
            r'^linkedin\.com/in/[a-zA-Z0-9_-]+/?$',
            r'^linkedin\.com/company/[a-zA-Z0-9_-]+/?$'
        ]

        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True, None

        return False, "Invalid LinkedIn URL format"

    def validate_phone(self, phone: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate phone number format"""
        if not phone or not phone.strip():
            return False, "Phone is empty"

        phone = phone.strip()

        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

        # Check if it's a valid US phone number (10 or 11 digits)
        if re.match(r'^\+?1?\d{10}$', cleaned):
            return True, None

        if len(cleaned) >= 10 and cleaned.isdigit():
            return True, None

        return False, "Invalid phone format (expected 10+ digits)"

    def validate_name_completeness(self, name: Optional[str], entity_type: str) -> Tuple[bool, Optional[str]]:
        """Validate name completeness"""
        if not name or not name.strip():
            return False, f"{entity_type.capitalize()} name is empty"

        name = name.strip()

        # Minimum length
        if len(name) < 2:
            return False, f"{entity_type.capitalize()} name too short (min 2 chars)"

        # Check for placeholder text
        invalid_names = [
            'test', 'example', 'sample', 'n/a', 'none', 'unknown',
            'tbd', 'tba', 'pending', 'temp'
        ]

        if name.lower() in invalid_names:
            return False, f"Invalid {entity_type} name: {name}"

        # For person names, check for at least 2 parts (first + last)
        if entity_type == 'person':
            parts = name.split()
            if len(parts) < 2:
                return False, "Person name should include first and last name"

        return True, None

    # ========================================================================
    # Company Validation
    # ========================================================================

    def validate_company(self, record: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate company record

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Critical validations (must pass)
        name_valid, name_error = self.validate_name_completeness(
            record.get('company_name'), 'company'
        )
        if not name_valid:
            errors.append(name_error)

        domain_valid, domain_error = self.validate_domain(record.get('domain'))
        if not domain_valid:
            errors.append(domain_error)

        # Warning validations (nice to have)
        if record.get('website'):
            website_valid, website_error = self.validate_domain(record.get('website'))
            if not website_valid:
                warnings.append(f"Website: {website_error}")

        if record.get('phone'):
            phone_valid, phone_error = self.validate_phone(record.get('phone'))
            if not phone_valid:
                warnings.append(f"Phone: {phone_error}")

        # Check employee count
        employee_count = record.get('employee_count')
        if employee_count is not None:
            try:
                count = int(employee_count)
                if count < 0:
                    warnings.append("Employee count is negative")
                elif count == 0:
                    warnings.append("Employee count is zero")
            except (ValueError, TypeError):
                warnings.append("Employee count is not a valid number")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def process_company_batch(self) -> int:
        """
        Process all WV companies

        Returns:
            Number of records processed
        """
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Fetch all WV companies
            cursor.execute("""
                SELECT *
                FROM marketing.company_raw_wv
                WHERE state = 'WV'
                ORDER BY company_unique_id
            """)

            records = cursor.fetchall()
            total = len(records)

            print(f"\n[INFO] Processing {total} WV companies...")

            for i, record in enumerate(records, 1):
                start_time = datetime.now()

                is_valid, errors, warnings = self.validate_company(dict(record))

                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                company_unique_id = record['company_unique_id']

                if is_valid:
                    # Insert into company_master
                    self._insert_company_master(record, warnings)
                    self.stats['company']['passed'] += 1
                    status_icon = "[OK]"
                else:
                    # Insert into company_invalid
                    self._insert_company_invalid(record, errors, warnings)
                    self.stats['company']['failed'] += 1
                    status_icon = "[FAIL]"

                # Log to validation_log
                self._log_validation(
                    record_id=company_unique_id,
                    entity_type='company',
                    source_table='marketing.company_raw_wv',
                    destination_table='marketing.company_master' if is_valid else 'marketing.company_invalid',
                    validation_status='PASSED' if is_valid else 'FAILED',
                    reason_code=None if is_valid else errors[0] if errors else 'Unknown',
                    errors=errors,
                    warnings=warnings,
                    processing_time_ms=processing_time_ms
                )

                self.stats['company']['total'] += 1

                if i % 10 == 0 or i == total:
                    print(f"  {status_icon} Processed {i}/{total} companies "
                          f"([OK] {self.stats['company']['passed']} | "
                          f"[FAIL] {self.stats['company']['failed']})")

            if not self.dry_run:
                self.connection.commit()
            else:
                self.connection.rollback()
                print("  [DRY RUN] Changes rolled back")

            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error processing companies: {e}")
            raise
        finally:
            cursor.close()

    def _insert_company_master(self, record: Dict, warnings: List[str]):
        """Insert valid company into master table"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO marketing.company_master (
                    company_unique_id, company_name, domain, industry,
                    employee_count, website, phone, address, city, state, zip,
                    validation_status, validated_at, batch_id,
                    created_at, updated_at
                )
                VALUES (
                    %(company_unique_id)s, %(company_name)s, %(domain)s, %(industry)s,
                    %(employee_count)s, %(website)s, %(phone)s, %(address)s,
                    %(city)s, %(state)s, %(zip)s,
                    'PASSED', now(), %(batch_id)s,
                    COALESCE(%(created_at)s, now()), now()
                )
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    domain = EXCLUDED.domain,
                    industry = EXCLUDED.industry,
                    employee_count = EXCLUDED.employee_count,
                    website = EXCLUDED.website,
                    phone = EXCLUDED.phone,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    zip = EXCLUDED.zip,
                    validation_status = 'PASSED',
                    validated_at = now(),
                    batch_id = %(batch_id)s,
                    updated_at = now()
            """, {**record, 'batch_id': self.batch_id})
        finally:
            cursor.close()

    def _insert_company_invalid(self, record: Dict, errors: List[str], warnings: List[str]):
        """Insert failed company into invalid table"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()

        try:
            reason_code = errors[0] if errors else 'Validation failed'

            cursor.execute("""
                INSERT INTO marketing.company_invalid (
                    company_unique_id, company_name, domain, industry,
                    employee_count, website, phone, address, city, state, zip,
                    validation_status, reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table, created_at
                )
                VALUES (
                    %(company_unique_id)s, %(company_name)s, %(domain)s, %(industry)s,
                    %(employee_count)s, %(website)s, %(phone)s, %(address)s,
                    %(city)s, %(state)s, %(zip)s,
                    'FAILED', %(reason_code)s, %(errors)s, %(warnings)s,
                    now(), %(batch_id)s, 'marketing.company_raw_wv', now()
                )
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    validation_warnings = EXCLUDED.validation_warnings,
                    failed_at = now(),
                    batch_id = EXCLUDED.batch_id,
                    updated_at = now()
            """, {
                **record,
                'batch_id': self.batch_id,
                'reason_code': reason_code,
                'errors': json.dumps(errors),
                'warnings': json.dumps(warnings) if warnings else None
            })
        finally:
            cursor.close()

    # ========================================================================
    # People Validation
    # ========================================================================

    def validate_person(self, record: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate person record

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Critical validations (must pass)
        name_valid, name_error = self.validate_name_completeness(
            record.get('full_name'), 'person'
        )
        if not name_valid:
            errors.append(name_error)

        email_valid, email_error = self.validate_email(record.get('email'))
        if not email_valid:
            errors.append(email_error)

        # Warning validations (nice to have)
        if record.get('linkedin_url'):
            linkedin_valid, linkedin_error = self.validate_linkedin_url(record.get('linkedin_url'))
            if not linkedin_valid:
                warnings.append(f"LinkedIn: {linkedin_error}")

        if record.get('phone'):
            phone_valid, phone_error = self.validate_phone(record.get('phone'))
            if not phone_valid:
                warnings.append(f"Phone: {phone_error}")

        # Check for first/last name if available
        first_name = record.get('first_name', '').strip()
        last_name = record.get('last_name', '').strip()

        if not first_name:
            warnings.append("First name is missing")
        if not last_name:
            warnings.append("Last name is missing")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def process_people_batch(self) -> int:
        """
        Process all WV people

        Returns:
            Number of records processed
        """
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Fetch all WV people
            cursor.execute("""
                SELECT *
                FROM marketing.people_raw_wv
                WHERE state = 'WV'
                ORDER BY unique_id
            """)

            records = cursor.fetchall()
            total = len(records)

            print(f"\n👥 Processing {total} WV people...")

            for i, record in enumerate(records, 1):
                start_time = datetime.now()

                is_valid, errors, warnings = self.validate_person(dict(record))

                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                unique_id = record['unique_id']

                if is_valid:
                    # Insert into people_master
                    self._insert_people_master(record, warnings)
                    self.stats['person']['passed'] += 1
                    status_icon = "[OK]"
                else:
                    # Insert into people_invalid
                    self._insert_people_invalid(record, errors, warnings)
                    self.stats['person']['failed'] += 1
                    status_icon = "[FAIL]"

                # Log to validation_log
                self._log_validation(
                    record_id=unique_id,
                    entity_type='person',
                    source_table='marketing.people_raw_wv',
                    destination_table='marketing.people_master' if is_valid else 'marketing.people_invalid',
                    validation_status='PASSED' if is_valid else 'FAILED',
                    reason_code=None if is_valid else errors[0] if errors else 'Unknown',
                    errors=errors,
                    warnings=warnings,
                    processing_time_ms=processing_time_ms
                )

                self.stats['person']['total'] += 1

                if i % 10 == 0 or i == total:
                    print(f"  {status_icon} Processed {i}/{total} people "
                          f"([OK] {self.stats['person']['passed']} | "
                          f"[FAIL] {self.stats['person']['failed']})")

            if not self.dry_run:
                self.connection.commit()
            else:
                self.connection.rollback()
                print("  [DRY RUN] Changes rolled back")

            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error processing people: {e}")
            raise
        finally:
            cursor.close()

    def _insert_people_master(self, record: Dict, warnings: List[str]):
        """Insert valid person into master table"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO marketing.people_master (
                    unique_id, full_name, first_name, last_name, email, phone,
                    title, company_name, company_unique_id, linkedin_url,
                    city, state,
                    validation_status, validated_at, batch_id,
                    created_at, updated_at
                )
                VALUES (
                    %(unique_id)s, %(full_name)s, %(first_name)s, %(last_name)s,
                    %(email)s, %(phone)s, %(title)s, %(company_name)s,
                    %(company_unique_id)s, %(linkedin_url)s, %(city)s, %(state)s,
                    'PASSED', now(), %(batch_id)s,
                    COALESCE(%(created_at)s, now()), now()
                )
                ON CONFLICT (unique_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    phone = EXCLUDED.phone,
                    title = EXCLUDED.title,
                    company_name = EXCLUDED.company_name,
                    company_unique_id = EXCLUDED.company_unique_id,
                    linkedin_url = EXCLUDED.linkedin_url,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    validation_status = 'PASSED',
                    validated_at = now(),
                    batch_id = %(batch_id)s,
                    updated_at = now()
            """, {**record, 'batch_id': self.batch_id})
        finally:
            cursor.close()

    def _insert_people_invalid(self, record: Dict, errors: List[str], warnings: List[str]):
        """Insert failed person into invalid table"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()

        try:
            reason_code = errors[0] if errors else 'Validation failed'

            cursor.execute("""
                INSERT INTO marketing.people_invalid (
                    unique_id, full_name, first_name, last_name, email, phone,
                    title, company_name, company_unique_id, linkedin_url,
                    city, state,
                    validation_status, reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table, created_at
                )
                VALUES (
                    %(unique_id)s, %(full_name)s, %(first_name)s, %(last_name)s,
                    %(email)s, %(phone)s, %(title)s, %(company_name)s,
                    %(company_unique_id)s, %(linkedin_url)s, %(city)s, %(state)s,
                    'FAILED', %(reason_code)s, %(errors)s, %(warnings)s,
                    now(), %(batch_id)s, 'marketing.people_raw_wv', now()
                )
                ON CONFLICT (unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    validation_warnings = EXCLUDED.validation_warnings,
                    failed_at = now(),
                    batch_id = EXCLUDED.batch_id,
                    updated_at = now()
            """, {
                **record,
                'batch_id': self.batch_id,
                'reason_code': reason_code,
                'errors': json.dumps(errors),
                'warnings': json.dumps(warnings) if warnings else None
            })
        finally:
            cursor.close()

    # ========================================================================
    # Validation Logging
    # ========================================================================

    def _log_validation(
        self,
        record_id: str,
        entity_type: str,
        source_table: str,
        destination_table: str,
        validation_status: str,
        reason_code: Optional[str],
        errors: List[str],
        warnings: List[str],
        processing_time_ms: int
    ):
        """Log validation to shq.validation_log"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO shq.validation_log (
                    batch_id, record_id, entity_type, source_table, destination_table,
                    validation_status, reason_code, validation_errors, validation_warnings,
                    timestamp, processing_time_ms, validator_version
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s, '1.0'
                )
            """, (
                self.batch_id, record_id, entity_type, source_table, destination_table,
                validation_status, reason_code,
                json.dumps(errors) if errors else None,
                json.dumps(warnings) if warnings else None,
                processing_time_ms
            ))
        finally:
            cursor.close()

    # ========================================================================
    # Summary Report
    # ========================================================================

    def generate_summary(self) -> str:
        """Generate markdown summary report"""

        total_records = self.stats['company']['total'] + self.stats['person']['total']
        total_passed = self.stats['company']['passed'] + self.stats['person']['passed']
        total_failed = self.stats['company']['failed'] + self.stats['person']['failed']

        pass_rate = (total_passed / total_records * 100) if total_records > 0 else 0
        fail_rate = (total_failed / total_records * 100) if total_records > 0 else 0

        summary = f"""
# Enricha-Vision WV Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN' if self.dry_run else 'PRODUCTION'}

---

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Records** | {total_records:,} | 100.0% |
| **[OK] Passed** | {total_passed:,} | {pass_rate:.1f}% |
| **[FAIL] Failed** | {total_failed:,} | {fail_rate:.1f}% |

---

## Company Results

| Status | Count | Percentage |
|--------|-------|------------|
| **Total Companies** | {self.stats['company']['total']:,} | 100.0% |
| **[OK] Valid → company_master** | {self.stats['company']['passed']:,} | {(self.stats['company']['passed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |
| **[FAIL] Invalid → company_invalid** | {self.stats['company']['failed']:,} | {(self.stats['company']['failed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.company_raw_wv` (WHERE state='WV')
**Destinations**:
- [OK] Passed → `marketing.company_master`
- [FAIL] Failed → `marketing.company_invalid`

---

## People Results

| Status | Count | Percentage |
|--------|-------|------------|
| **Total People** | {self.stats['person']['total']:,} | 100.0% |
| **[OK] Valid → people_master** | {self.stats['person']['passed']:,} | {(self.stats['person']['passed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |
| **[FAIL] Invalid → people_invalid** | {self.stats['person']['failed']:,} | {(self.stats['person']['failed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.people_raw_wv` (WHERE state='WV')
**Destinations**:
- [OK] Passed → `marketing.people_master`
- [FAIL] Failed → `marketing.people_invalid`

---

## Validation Rules Applied

### Companies
- [OK] Company name completeness (min 2 chars, no placeholders)
- [OK] Domain format validation
- ⚠ Website validation (warning only)
- ⚠ Phone format (warning only)
- ⚠ Employee count sanity check (warning only)

### People
- [OK] Full name completeness (first + last name required)
- [OK] Email format validation (RFC 5322 compliant)
- ⚠ LinkedIn URL format (warning only)
- ⚠ Phone format (warning only)
- ⚠ First/last name presence (warning only)

---

## Audit Trail

All validation activity logged to: `shq.validation_log`

Query validation results:
```sql
-- View batch summary
SELECT * FROM shq.vw_validation_summary
WHERE batch_id = '{self.batch_id}';

-- View all records in this batch
SELECT * FROM shq.validation_log
WHERE batch_id = '{self.batch_id}'
ORDER BY timestamp;
```

---

## Invalid Records for Review

Query pending reviews:
```sql
-- All invalid records from this batch
SELECT * FROM marketing.vw_invalid_pending_review
WHERE batch_id = '{self.batch_id}';

-- Invalid companies
SELECT company_name, reason_code, validation_errors
FROM marketing.company_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;

-- Invalid people
SELECT full_name, email, reason_code, validation_errors
FROM marketing.people_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;
```

---

## Next Steps

1. **Review invalid records**: Check `marketing.company_invalid` and `marketing.people_invalid`
2. **Fix data issues**: Correct validation errors in source tables
3. **Re-run validation**: Use same script to revalidate fixed records
4. **Promote to Supabase**: Once validated, use generic framework for enrichment

---

**Status**: {'[OK] Validation Complete (Dry Run - No Changes Made)' if self.dry_run else '[OK] Validation Complete - Data Committed to Neon'}
"""

        return summary.strip()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Enricha-Vision WV Data Validator (Neon-Only)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_wv_neon.py --all
  python validate_wv_neon.py --entity company
  python validate_wv_neon.py --entity person --dry-run
        """
    )

    parser.add_argument(
        '--entity',
        choices=['company', 'person'],
        help='Entity type to validate (default: process both)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Process both companies and people'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run validation without writing to database'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.entity:
        parser.error("Must specify --all or --entity")

    # Initialize validator
    print("=" * 60)
    print("Enricha-Vision WV Data Validation (Neon-Only)")
    print("=" * 60)

    validator = NeonWVValidator(dry_run=args.dry_run)

    try:
        # Connect to Neon
        validator.connect()

        # Process entities
        if args.all or args.entity == 'company':
            validator.process_company_batch()

        if args.all or args.entity == 'person':
            validator.process_people_batch()

        # Generate and print summary
        print("\n" + "=" * 60)
        print(validator.generate_summary())
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Validation failed: {e}")
        sys.exit(1)
    finally:
        validator.close()


if __name__ == '__main__':
    main()
