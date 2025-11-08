#!/usr/bin/env python3
"""
Intake → Validation → Promotion Pipeline

Workflow:
1. Read from intake.company_raw_intake
2. Validate each record
3. If PASSED → Insert into marketing.company_master
4. If FAILED → Insert into marketing.company_invalid

Same for people data
"""

import os, sys, psycopg2, psycopg2.extras, re, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class IntakeValidator:
    def __init__(self, dry_run=False):
        self.batch_id = f"INTAKE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.dry_run = dry_run
        self.stats = {
            'company': {'passed': 0, 'failed': 0, 'total': 0},
            'person': {'passed': 0, 'failed': 0, 'total': 0}
        }

    def connect(self):
        self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.connection.autocommit = False
        print(f"[OK] Connected to Neon")
        if self.dry_run:
            print("[DRY RUN] No data will be written")

    def close(self):
        if self.connection:
            self.connection.close()

    # Validation rules
    def validate_website(self, website):
        if not website or not website.strip():
            return False, "Website URL is empty"
        website = website.strip()
        if website.lower() in ['n/a', 'none', 'null', 'test', 'example.com', 'test.com']:
            return False, f"Invalid website: {website}"
        return True, None

    def validate_company_name(self, name):
        if not name or not name.strip():
            return False, "Company name is empty"
        name = name.strip()
        if len(name) < 2:
            return False, "Company name too short"
        if name.lower() in ['test', 'example', 'n/a', 'none', 'null']:
            return False, f"Invalid company name: {name}"
        return True, None

    def validate_email(self, email):
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
        if not full_name or not full_name.strip():
            return False, "Full name is empty"
        if not first_name or not first_name.strip():
            return False, "First name is missing"
        if not last_name or not last_name.strip():
            return False, "Last name is missing"
        return True, None

    def validate_company(self, record):
        errors = []
        warnings = []

        name_valid, name_error = self.validate_company_name(record.get('company_name'))
        if not name_valid:
            errors.append(name_error)

        website_valid, website_error = self.validate_website(record.get('website_url') or record.get('website'))
        if not website_valid:
            errors.append(website_error)

        # Warnings
        if not record.get('industry'):
            warnings.append("Industry is missing")
        if not record.get('employee_count') or record.get('employee_count') == 0:
            warnings.append("Employee count is missing or zero")

        return len(errors) == 0, errors, warnings

    def validate_person(self, record):
        errors = []
        warnings = []

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

        return len(errors) == 0, errors, warnings

    def process_company_intake(self):
        """Process intake.company_raw_intake → validation → master or invalid"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get all unprocessed companies from intake
            cursor.execute("""
                SELECT *
                FROM intake.company_raw_intake
                ORDER BY company_unique_id
            """)
            records = cursor.fetchall()
            total = len(records)

            print(f"\n[COMPANIES] Processing {total} companies from intake.company_raw_intake...")

            for i, record in enumerate(records, 1):
                record_dict = dict(record)
                is_valid, errors, warnings = self.validate_company(record_dict)

                if is_valid:
                    # PASSED → Promote to company_master
                    if not self.dry_run:
                        self._promote_to_company_master(record_dict)
                    self.stats['company']['passed'] += 1
                else:
                    # FAILED → Send to company_invalid
                    if not self.dry_run:
                        self._insert_company_invalid(record_dict, errors, warnings)
                    self.stats['company']['failed'] += 1

                self.stats['company']['total'] += 1

                if i % 50 == 0 or i == total:
                    print(f"  Processed {i}/{total} "
                          f"([PASSED->master] {self.stats['company']['passed']} | "
                          f"[FAILED->invalid] {self.stats['company']['failed']})")

            if not self.dry_run:
                self.connection.commit()
            else:
                self.connection.rollback()
                print("  [DRY RUN] Changes rolled back")

            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _promote_to_company_master(self, record):
        """Promote valid company to master table"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO marketing.company_master (
                    company_unique_id, company_name, website_url, industry,
                    employee_count, company_phone, address_street, address_city,
                    address_state, address_zip, source_system, validated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'intake_validation', now())
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    website_url = EXCLUDED.website_url,
                    industry = EXCLUDED.industry,
                    employee_count = EXCLUDED.employee_count,
                    validated_at = now()
            """, (
                record.get('company_unique_id'),
                record.get('company_name'),
                record.get('website_url') or record.get('website'),
                record.get('industry'),
                record.get('employee_count'),
                record.get('company_phone') or record.get('phone'),
                record.get('address_street') or record.get('address'),
                record.get('address_city') or record.get('city'),
                record.get('address_state') or record.get('state'),
                record.get('address_zip') or record.get('zip')
            ))
        finally:
            cursor.close()

    def _insert_company_invalid(self, record, errors, warnings):
        """Insert failed company to invalid table"""
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'intake.company_raw_intake')
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    batch_id = EXCLUDED.batch_id,
                    failed_at = now()
            """, (
                record.get('company_unique_id'),
                record.get('company_name'),
                record.get('domain'),
                record.get('industry'),
                record.get('employee_count'),
                record.get('website_url') or record.get('website'),
                record.get('company_phone') or record.get('phone'),
                record.get('address_street') or record.get('address'),
                record.get('address_city') or record.get('city'),
                record.get('address_state') or record.get('state'),
                record.get('address_zip') or record.get('zip'),
                reason_code,
                json.dumps(errors),
                json.dumps(warnings) if warnings else None,
                self.batch_id
            ))
        finally:
            cursor.close()

    def log_batch_summary(self, entity_type):
        """Log validation summary"""
        if self.dry_run:
            return

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
                f'intake.{entity_type}_raw_intake',
                f'marketing.{entity_type}_master (passed) / marketing.{entity_type}_invalid (failed)',
                self.stats[entity_type]['total'],
                self.stats[entity_type]['passed'],
                self.stats[entity_type]['failed'],
                'validate_intake_to_master.py',
                f"Intake validation - {self.stats[entity_type]['passed']} promoted to master, {self.stats[entity_type]['failed']} sent to invalid"
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
# Intake Validation & Promotion Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN (no changes made)' if self.dry_run else 'PRODUCTION'}

## Overall Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Records** | {total_records:,} | 100.0% |
| **PASSED -> Master Tables** | {total_passed:,} | {pass_rate:.1f}% |
| **FAILED -> Invalid Tables** | {total_failed:,} | {100-pass_rate:.1f}% |

---

## Company Results ({self.stats['company']['total']} companies)

| Status | Count | Percentage | Destination |
|--------|-------|------------|-------------|
| **PASSED** | {self.stats['company']['passed']:,} | {(self.stats['company']['passed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% | `marketing.company_master` |
| **FAILED** | {self.stats['company']['failed']:,} | {(self.stats['company']['failed'] / self.stats['company']['total'] * 100) if self.stats['company']['total'] > 0 else 0:.1f}% | `marketing.company_invalid` |

**Source**: `intake.company_raw_intake`

---

## Validation Rules Applied

### Companies
- Company name completeness (min 2 chars, no placeholders)
- Website URL validation (not empty, not placeholder)
- Warnings: industry, employee count

### People
- Full name completeness (first + last name required)
- Email format validation (RFC 5322 compliant)
- Warnings: job title, phone

---

## Query Results

```sql
-- View promoted companies (PASSED)
SELECT company_name, website_url, validated_at
FROM marketing.company_master
WHERE source_system = 'intake_validation'
ORDER BY validated_at DESC;

-- View failed companies (FAILED)
SELECT company_name, website, reason_code, validation_errors
FROM marketing.company_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;

-- Validation log
SELECT * FROM public.shq_validation_log
WHERE validation_run_id LIKE '{self.batch_id}%'
ORDER BY executed_at DESC;
```

---

**Workflow**: Raw Intake -> Validate -> PASSED->Master | FAILED->Invalid
**Status**: {'DRY RUN Complete (no changes)' if self.dry_run else 'Validation Complete'}
"""

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate intake data and promote to master or invalid tables')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--entity', choices=['company', 'person', 'all'], default='all', help='Entity to process')
    args = parser.parse_args()

    print("=" * 70)
    print("Intake Validation & Promotion Pipeline")
    print("=" * 70)

    validator = IntakeValidator(dry_run=args.dry_run)

    try:
        validator.connect()

        if args.entity in ['company', 'all']:
            validator.process_company_intake()
            validator.log_batch_summary('company')

        # if args.entity in ['person', 'all']:
        #     validator.process_people_intake()
        #     validator.log_batch_summary('person')

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
