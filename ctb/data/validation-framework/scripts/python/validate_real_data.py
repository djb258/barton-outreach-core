#!/usr/bin/env python3
"""
Validate REAL data from company_master and people_master
Checks all 453 WV companies and 170 people
"""

import os, sys, psycopg2, psycopg2.extras, re, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RealDataValidator:
    def __init__(self):
        self.batch_id = f"REAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.stats = {
            'company': {'passed': 0, 'failed': 0, 'total': 0},
            'person': {'passed': 0, 'failed': 0, 'total': 0}
        }

    def connect(self):
        self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.connection.autocommit = False
        print("[OK] Connected to Neon")

    def close(self):
        if self.connection:
            self.connection.close()

    def validate_website(self, website):
        """Validate website URL"""
        if not website or not website.strip():
            return False, "Website URL is empty"
        website = website.strip()
        if website.lower() in ['n/a', 'none', 'null', 'test', 'example.com']:
            return False, f"Invalid website: {website}"
        return True, None

    def validate_company_name(self, name):
        """Validate company name"""
        if not name or not name.strip():
            return False, "Company name is empty"
        name = name.strip()
        if len(name) < 2:
            return False, "Company name too short"
        if name.lower() in ['test', 'example', 'n/a', 'none', 'null']:
            return False, f"Invalid company name: {name}"
        return True, None

    def validate_email(self, email):
        """Validate email"""
        if not email or not email.strip():
            return False, "Email is empty"
        email = email.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        invalid_patterns = ['noreply@', 'no-reply@', 'test@', 'example@', '@test.com', '@example.com']
        if any(p in email for p in invalid_patterns):
            return False, "Invalid email pattern"
        return True, None

    def validate_person_name(self, full_name, first_name, last_name):
        """Validate person name"""
        if not full_name or not full_name.strip():
            return False, "Full name is empty"
        if not first_name or not first_name.strip():
            return False, "First name is missing"
        if not last_name or not last_name.strip():
            return False, "Last name is missing"
        if len(full_name.split()) < 2:
            return False, "Full name should have at least 2 parts"
        return True, None

    def validate_company(self, record):
        """Validate company record from company_master"""
        errors = []
        warnings = []

        # Critical validations
        name_valid, name_error = self.validate_company_name(record.get('company_name'))
        if not name_valid:
            errors.append(name_error)

        website_valid, website_error = self.validate_website(record.get('website_url'))
        if not website_valid:
            errors.append(website_error)

        # Data quality warnings
        if not record.get('industry'):
            warnings.append("Industry is missing")
        if not record.get('employee_count') or record.get('employee_count') == 0:
            warnings.append("Employee count is missing or zero")
        if not record.get('company_phone'):
            warnings.append("Phone number is missing")

        return len(errors) == 0, errors, warnings

    def validate_person(self, record):
        """Validate person record from people_master"""
        errors = []
        warnings = []

        # Critical validations
        name_valid, name_error = self.validate_person_name(
            record.get('full_name'),
            record.get('first_name'),
            record.get('last_name')
        )
        if not name_valid:
            errors.append(name_error)

        email_valid, email_error = self.validate_email(record.get('email'))
        if not email_valid:
            errors.append(email_error)

        # Warnings
        if not record.get('title'):
            warnings.append("Job title is missing")
        if not record.get('linkedin_url'):
            warnings.append("LinkedIn URL is missing")
        if not record.get('work_phone_e164') and not record.get('personal_phone_e164'):
            warnings.append("No phone number")

        return len(errors) == 0, errors, warnings

    def process_companies(self):
        """Validate all companies in company_master"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get all companies (453 total)
            cursor.execute("""
                SELECT *
                FROM marketing.company_master
                ORDER BY company_unique_id
            """)
            records = cursor.fetchall()
            total = len(records)

            print(f"\n[COMPANIES] Validating {total} companies from company_master...")

            for i, record in enumerate(records, 1):
                is_valid, errors, warnings = self.validate_company(dict(record))

                if is_valid:
                    self.stats['company']['passed'] += 1
                else:
                    # Insert into company_invalid
                    self._insert_company_invalid(record, errors, warnings)
                    self.stats['company']['failed'] += 1

                self.stats['company']['total'] += 1

                if i % 50 == 0 or i == total:
                    print(f"  Processed {i}/{total} companies "
                          f"([OK] {self.stats['company']['passed']} | "
                          f"[FAIL] {self.stats['company']['failed']})")

            self.connection.commit()
            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _insert_company_invalid(self, record, errors, warnings):
        """Insert invalid company"""
        cursor = self.connection.cursor()
        try:
            reason_code = errors[0] if errors else 'Validation failed'
            cursor.execute("""
                INSERT INTO marketing.company_invalid (
                    company_unique_id, company_name, domain, industry,
                    employee_count, website, phone, address, city, state, zip,
                    validation_status, reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'marketing.company_master')
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    failed_at = now()
            """, (
                record['company_unique_id'],
                record.get('company_name'),
                None,  # domain not in schema
                record.get('industry'),
                record.get('employee_count'),
                record.get('website_url'),
                record.get('company_phone'),
                record.get('address_street'),
                record.get('address_city'),
                record.get('address_state'),
                record.get('address_zip'),
                reason_code,
                json.dumps(errors),
                json.dumps(warnings) if warnings else None,
                self.batch_id
            ))
        finally:
            cursor.close()

    def process_people(self):
        """Validate all people in people_master"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get all people (170 total)
            cursor.execute("""
                SELECT *
                FROM marketing.people_master
                ORDER BY unique_id
            """)
            records = cursor.fetchall()
            total = len(records)

            print(f"\n[PEOPLE] Validating {total} people from people_master...")

            for i, record in enumerate(records, 1):
                is_valid, errors, warnings = self.validate_person(dict(record))

                if is_valid:
                    self.stats['person']['passed'] += 1
                else:
                    # Insert into people_invalid
                    self._insert_people_invalid(record, errors, warnings)
                    self.stats['person']['failed'] += 1

                self.stats['person']['total'] += 1

                if i % 25 == 0 or i == total:
                    print(f"  Processed {i}/{total} people "
                          f"([OK] {self.stats['person']['passed']} | "
                          f"[FAIL] {self.stats['person']['failed']})")

            self.connection.commit()
            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _insert_people_invalid(self, record, errors, warnings):
        """Insert invalid person"""
        cursor = self.connection.cursor()
        try:
            reason_code = errors[0] if errors else 'Validation failed'
            cursor.execute("""
                INSERT INTO marketing.people_invalid (
                    unique_id, full_name, first_name, last_name, email, phone,
                    title, company_name, company_unique_id, linkedin_url, city, state,
                    validation_status, reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'marketing.people_master')
                ON CONFLICT (unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    failed_at = now()
            """, (
                record['unique_id'],
                record.get('full_name'),
                record.get('first_name'),
                record.get('last_name'),
                record.get('email'),
                record.get('work_phone_e164') or record.get('personal_phone_e164'),
                record.get('title'),
                None,  # company_name not in schema
                record.get('company_unique_id'),
                record.get('linkedin_url'),
                None,  # city not in schema
                None,  # state not in schema
                reason_code,
                json.dumps(errors),
                json.dumps(warnings) if warnings else None,
                self.batch_id
            ))
        finally:
            cursor.close()

    def log_batch_summary(self, entity_type):
        """Log to validation_log"""
        cursor = self.connection.cursor()
        try:
            run_id = f"{self.batch_id}-{entity_type}"
            cursor.execute("""
                INSERT INTO public.shq_validation_log (
                    validation_run_id, source_table, target_table,
                    total_records, passed_records, failed_records,
                    executed_by, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                run_id,
                f'marketing.{entity_type}_master',
                f'marketing.{entity_type}_invalid',
                self.stats[entity_type]['total'],
                self.stats[entity_type]['passed'],
                self.stats[entity_type]['failed'],
                'validate_real_data.py',
                f"Real data validation - {self.stats[entity_type]['passed']} passed, {self.stats[entity_type]['failed']} failed"
            ))
            self.connection.commit()
        finally:
            cursor.close()

    def generate_summary(self):
        total_records = self.stats['company']['total'] + self.stats['person']['total']
        total_passed = self.stats['company']['passed'] + self.stats['person']['passed']
        total_failed = self.stats['company']['failed'] + self.stats['person']['failed']
        pass_rate = (total_passed / total_records * 100) if total_records > 0 else 0

        return f"""
# Real WV Data Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Records** | {total_records:,} | 100.0% |
| **PASSED** | {total_passed:,} | {pass_rate:.1f}% |
| **FAILED** | {total_failed:,} | {100-pass_rate:.1f}% |

## Company Results ({self.stats['company']['total']} companies)

| Status | Count | Percentage |
|--------|-------|------------|
| **PASSED** | {self.stats['company']['passed']:,} | {(self.stats['company']['passed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |
| **FAILED** | {self.stats['company']['failed']:,} | {(self.stats['company']['failed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.company_master` (all WV companies)

## People Results ({self.stats['person']['total']} people)

| Status | Count | Percentage |
|--------|-------|------------|
| **PASSED** | {self.stats['person']['passed']:,} | {(self.stats['person']['passed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |
| **FAILED** | {self.stats['person']['failed']:,} | {(self.stats['person']['failed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.people_master`

## Query Failed Records

```sql
-- Failed companies
SELECT company_name, website_url, reason_code, validation_errors
FROM marketing.company_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;

-- Failed people
SELECT full_name, email, reason_code, validation_errors
FROM marketing.people_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;
```

**Status**: Validation Complete
"""

def main():
    print("=" * 70)
    print("Real WV Data Validation (453 Companies + 170 People)")
    print("=" * 70)

    validator = RealDataValidator()

    try:
        validator.connect()
        validator.process_companies()
        validator.log_batch_summary('company')
        validator.process_people()
        validator.log_batch_summary('person')

        print("\n" + "=" * 70)
        print(validator.generate_summary())
        print("=" * 70)

    except Exception as e:
        print(f"\n[FAIL] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        validator.close()

if __name__ == '__main__':
    main()
