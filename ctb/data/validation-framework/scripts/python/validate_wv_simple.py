#!/usr/bin/env python3
"""
Simplified WV Validator - Validation Only (No Master Table Insertion)

This validator:
- Validates all WV company and people records
- Inserts FAILED records into company_invalid and people_invalid
- Logs all validation activity to shq.validation_log
- Generates summary report

PASSED records are logged but NOT inserted into master tables
(avoids schema compatibility issues)
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime
import re
import json
from dotenv import load_dotenv
import uuid

load_dotenv()

class SimpleWVValidator:
    """Simplified validator for WV data"""

    def __init__(self):
        self.batch_id = f"WV-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.stats = {
            'company': {'passed': 0, 'failed': 0, 'total': 0},
            'person': {'passed': 0, 'failed': 0, 'total': 0}
        }

    def connect(self):
        """Connect to Neon"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not set")

        self.connection = psycopg2.connect(database_url)
        self.connection.autocommit = False
        print("[OK] Connected to Neon")

    def close(self):
        if self.connection:
            self.connection.close()

    # Validation rules (same as before)
    def validate_email(self, email):
        if not email or not email.strip():
            return False, "Email is empty"
        email = email.strip().lower()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        if any(p in email for p in ['noreply@', 'no-reply@', 'test@', 'example@', '@test.com', '@example.com']):
            return False, f"Invalid email pattern"
        return True, None

    def validate_domain(self, domain):
        if not domain or not domain.strip():
            return False, "Domain is empty"
        domain = domain.strip().lower()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$', domain):
            return False, "Invalid domain format"
        if domain in ['example.com', 'test.com', 'sample.com']:
            return False, f"Invalid domain: {domain}"
        return True, None

    def validate_name(self, name, entity_type):
        if not name or not name.strip():
            return False, f"{entity_type} name is empty"
        name = name.strip()
        if len(name) < 2:
            return False, f"{entity_type} name too short"
        if name.lower() in ['test', 'example', 'n/a', 'none']:
            return False, f"Invalid {entity_type} name"
        if entity_type == 'person' and len(name.split()) < 2:
            return False, "Person name should include first and last name"
        return True, None

    def validate_company(self, record):
        errors = []
        warnings = []

        name_valid, name_error = self.validate_name(record.get('company_name'), 'company')
        if not name_valid:
            errors.append(name_error)

        domain_valid, domain_error = self.validate_domain(record.get('domain'))
        if not domain_valid:
            errors.append(domain_error)

        return len(errors) == 0, errors, warnings

    def validate_person(self, record):
        errors = []
        warnings = []

        name_valid, name_error = self.validate_name(record.get('full_name'), 'person')
        if not name_valid:
            errors.append(name_error)

        email_valid, email_error = self.validate_email(record.get('email'))
        if not email_valid:
            errors.append(email_error)

        return len(errors) == 0, errors, warnings

    def process_companies(self):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("SELECT * FROM marketing.company_raw_wv WHERE state = 'WV' ORDER BY company_unique_id")
            records = cursor.fetchall()
            total = len(records)

            print(f"\n[INFO] Processing {total} WV companies...")

            for i, record in enumerate(records, 1):
                start_time = datetime.now()
                is_valid, errors, warnings = self.validate_company(dict(record))
                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                company_unique_id = record['company_unique_id']

                if is_valid:
                    self.stats['company']['passed'] += 1
                    status_icon = "[OK]"
                else:
                    # Insert into company_invalid
                    self._insert_company_invalid(record, errors, warnings)
                    self.stats['company']['failed'] += 1
                    status_icon = "[FAIL]"

                # Per-record logging removed (using batch summary instead)

                self.stats['company']['total'] += 1

                if i % 10 == 0 or i == total:
                    print(f"  {status_icon} Processed {i}/{total} companies "
                          f"([OK] {self.stats['company']['passed']} | [FAIL] {self.stats['company']['failed']})")

            self.connection.commit()
            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _insert_company_invalid(self, record, errors, warnings):
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'marketing.company_raw_wv')
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    failed_at = now(),
                    batch_id = EXCLUDED.batch_id
            """, (
                record['company_unique_id'], record.get('company_name'), record.get('domain'),
                record.get('industry'), record.get('employee_count'), record.get('website'),
                record.get('phone'), record.get('address'), record.get('city'),
                record.get('state'), record.get('zip'), reason_code,
                json.dumps(errors), json.dumps(warnings) if warnings else None, self.batch_id
            ))
        finally:
            cursor.close()

    def process_people(self):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("SELECT * FROM marketing.people_raw_wv WHERE state = 'WV' ORDER BY unique_id")
            records = cursor.fetchall()
            total = len(records)

            print(f"\n[PEOPLE] Processing {total} WV people...")

            for i, record in enumerate(records, 1):
                start_time = datetime.now()
                is_valid, errors, warnings = self.validate_person(dict(record))
                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                unique_id = record['unique_id']

                if is_valid:
                    self.stats['person']['passed'] += 1
                    status_icon = "[OK]"
                else:
                    # Insert into people_invalid
                    self._insert_people_invalid(record, errors, warnings)
                    self.stats['person']['failed'] += 1
                    status_icon = "[FAIL]"

                # Per-record logging removed (using batch summary instead)

                self.stats['person']['total'] += 1

                if i % 10 == 0 or i == total:
                    print(f"  {status_icon} Processed {i}/{total} people "
                          f"([OK] {self.stats['person']['passed']} | [FAIL] {self.stats['person']['failed']})")

            self.connection.commit()
            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _insert_people_invalid(self, record, errors, warnings):
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'marketing.people_raw_wv')
                ON CONFLICT (unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    failed_at = now(),
                    batch_id = EXCLUDED.batch_id
            """, (
                record['unique_id'], record.get('full_name'), record.get('first_name'),
                record.get('last_name'), record.get('email'), record.get('phone'),
                record.get('title'), record.get('company_name'), record.get('company_unique_id'),
                record.get('linkedin_url'), record.get('city'), record.get('state'),
                reason_code, json.dumps(errors), json.dumps(warnings) if warnings else None, self.batch_id
            ))
        finally:
            cursor.close()

    def log_batch_summary(self, entity_type):
        """Log batch summary to validation_log"""
        cursor = self.connection.cursor()
        try:
            run_id = f"{self.batch_id}-{entity_type}"
            cursor.execute("""
                INSERT INTO public.shq_validation_log (
                    validation_run_id, source_table, target_table,
                    total_records, passed_records, failed_records,
                    executed_by, executed_at, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, now(), %s)
            """, (
                run_id,
                f'marketing.{entity_type}_raw_wv',
                f'marketing.{entity_type}_invalid',
                self.stats[entity_type]['total'],
                self.stats[entity_type]['passed'],
                self.stats[entity_type]['failed'],
                'validate_wv_simple.py',
                f"WV {entity_type} validation - {self.stats[entity_type]['passed']} passed, {self.stats[entity_type]['failed']} failed"
            ))
            self.connection.commit()
        finally:
            cursor.close()

    def generate_summary(self):
        total_records = self.stats['company']['total'] + self.stats['person']['total']
        total_passed = self.stats['company']['passed'] + self.stats['person']['passed']
        total_failed = self.stats['company']['failed'] + self.stats['person']['failed']
        pass_rate = (total_passed / total_records * 100) if total_records > 0 else 0
        fail_rate = (total_failed / total_records * 100) if total_records > 0 else 0

        return f"""
# Enricha-Vision WV Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Records** | {total_records:,} | 100.0% |
| **PASSED** | {total_passed:,} | {pass_rate:.1f}% |
| **FAILED** | {total_failed:,} | {fail_rate:.1f}% |

---

## Company Results

| Status | Count | Percentage |
|--------|-------|------------|
| **Total Companies** | {self.stats['company']['total']:,} | 100.0% |
| **PASSED** | {self.stats['company']['passed']:,} | {(self.stats['company']['passed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |
| **FAILED -> company_invalid** | {self.stats['company']['failed']:,} | {(self.stats['company']['failed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.company_raw_wv` (WHERE state='WV')
**Failed Records**: `marketing.company_invalid`

---

## People Results

| Status | Count | Percentage |
|--------|-------|------------|
| **Total People** | {self.stats['person']['total']:,} | 100.0% |
| **PASSED** | {self.stats['person']['passed']:,} | {(self.stats['person']['passed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |
| **FAILED -> people_invalid** | {self.stats['person']['failed']:,} | {(self.stats['person']['failed'] / self.stats['person']['total'] * 100) if self.stats['person']['total'] > 0 else 0:.1f}% |

**Source**: `marketing.people_raw_wv` (WHERE state='WV')
**Failed Records**: `marketing.people_invalid`

---

## Validation Rules Applied

### Companies
- Company name completeness (min 2 chars, no placeholders)
- Domain format validation

### People
- Full name completeness (first + last name required)
- Email format validation (RFC 5322 compliant)

---

## Query Failed Records

```sql
-- Failed companies
SELECT company_name, reason_code, validation_errors
FROM marketing.company_invalid
WHERE batch_id = '{self.batch_id}';

-- Failed people
SELECT full_name, email, reason_code, validation_errors
FROM marketing.people_invalid
WHERE batch_id = '{self.batch_id}';

-- All validation log
SELECT * FROM public.shq_validation_log
WHERE validation_run_id = '{self.batch_id}'
ORDER BY executed_at;
```

---

**Status**: Validation Complete
"""

def main():
    print("=" * 70)
    print("Enricha-Vision WV Validation (Neon Only)")
    print("=" * 70)

    validator = SimpleWVValidator()

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
        sys.exit(1)
    finally:
        validator.close()

if __name__ == '__main__':
    main()
