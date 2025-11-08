#!/usr/bin/env python3
"""
CORRECT Intake Validation Pipeline

Workflow:
intake.company_raw_intake → Validate → PASSED→company_master | FAILED→company_invalid

Uses actual intake schema with columns: company, num_employees, website, etc.
"""

import os, sys, psycopg2, psycopg2.extras, re, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class IntakeValidator:
    def __init__(self, dry_run=False, revalidate=False):
        self.batch_id = f"INTAKE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.dry_run = dry_run
        self.revalidate = revalidate  # If True, revalidate already validated records
        self.stats = {'passed': 0, 'failed': 0, 'total': 0}

    def connect(self):
        self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.connection.autocommit = False
        print(f"[OK] Connected to Neon")
        if self.dry_run:
            print("[DRY RUN] No data will be written\n")

    def close(self):
        if self.connection:
            self.connection.close()

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

    def validate_company(self, record):
        errors = []
        warnings = []

        # Critical validations
        name_valid, name_error = self.validate_company_name(record.get('company'))
        if not name_valid:
            errors.append(name_error)

        website_valid, website_error = self.validate_website(record.get('website'))
        if not website_valid:
            errors.append(website_error)

        # Warnings
        if not record.get('industry'):
            warnings.append("Industry is missing")
        if not record.get('num_employees') or record.get('num_employees') == 0:
            warnings.append("Employee count is missing or zero")
        if not record.get('company_phone'):
            warnings.append("Phone number is missing")

        return len(errors) == 0, errors, warnings

    def process_intake(self):
        """Process intake.company_raw_intake"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get companies that need validation
            where_clause = "WHERE validated IS NULL OR validated = FALSE" if not self.revalidate else ""

            cursor.execute(f"""
                SELECT *
                FROM intake.company_raw_intake
                {where_clause}
                ORDER BY id
            """)

            records = cursor.fetchall()
            total = len(records)

            if total == 0:
                print("\n[INFO] No records to validate (all already validated)")
                print("       Use --revalidate to revalidate existing records")
                return 0

            print(f"\n[COMPANIES] Processing {total} companies from intake.company_raw_intake...")

            for i, record in enumerate(records, 1):
                record_dict = dict(record)
                is_valid, errors, warnings = self.validate_company(record_dict)

                if is_valid:
                    # PASSED → Promote to company_master
                    if not self.dry_run:
                        self._promote_to_master(record_dict)
                        self._mark_validated(record_dict['id'], True, "Passed validation")
                    self.stats['passed'] += 1
                    status = "[PASSED->master]"
                else:
                    # FAILED → Send to company_invalid
                    if not self.dry_run:
                        self._insert_invalid(record_dict, errors, warnings)
                        self._mark_validated(record_dict['id'], False, errors[0])
                    self.stats['failed'] += 1
                    status = "[FAILED->invalid]"

                self.stats['total'] += 1

                if i % 50 == 0 or i == total:
                    print(f"  {status} Processed {i}/{total} "
                          f"(Passed: {self.stats['passed']} | Failed: {self.stats['failed']})")

            if not self.dry_run:
                self.connection.commit()
                print("\n[OK] Changes committed to database")
            else:
                self.connection.rollback()
                print("\n[DRY RUN] Changes rolled back (no data modified)")

            return total

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def _promote_to_master(self, record):
        """Promote valid company to company_master"""
        cursor = self.connection.cursor()
        try:
            # Generate Barton ID in correct format: 04.04.01.XX.XXXXX.XXX
            # XX cycles 00-99 (modulo 100), XXXXX is sequential, XXX is modulo 1000
            record_num = record['id']
            company_unique_id = f"04.04.01.{record_num % 100:02d}.{record_num:05d}.{record_num % 1000:03d}"

            cursor.execute("""
                INSERT INTO marketing.company_master (
                    company_unique_id, company_name, website_url, industry,
                    employee_count, company_phone, address_street, address_city,
                    address_state, address_zip, linkedin_url, facebook_url,
                    twitter_url, sic_codes, founded_year,
                    source_system, source_record_id, validated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    website_url = EXCLUDED.website_url,
                    industry = EXCLUDED.industry,
                    employee_count = EXCLUDED.employee_count,
                    validated_at = now()
            """, (
                company_unique_id,
                record.get('company'),
                record.get('website'),
                record.get('industry'),
                record.get('num_employees'),
                record.get('company_phone'),
                record.get('company_street'),
                record.get('company_city'),
                record.get('company_state'),
                record.get('company_postal_code'),
                record.get('company_linkedin_url'),
                record.get('facebook_url'),
                record.get('twitter_url'),
                record.get('sic_codes'),
                record.get('founded_year'),
                'intake_validation',
                str(record.get('id'))
            ))
        finally:
            cursor.close()

    def _insert_invalid(self, record, errors, warnings):
        """Insert failed company to company_invalid"""
        cursor = self.connection.cursor()
        try:
            # Generate Barton ID in correct format: 04.04.01.XX.XXXXX.XXX
            # XX cycles 00-99 (modulo 100), XXXXX is sequential, XXX is modulo 1000
            record_num = record['id']
            company_unique_id = f"04.04.01.{record_num % 100:02d}.{record_num:05d}.{record_num % 1000:03d}"
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
                company_unique_id,
                record.get('company'),
                None,  # domain not in intake schema
                record.get('industry'),
                record.get('num_employees'),
                record.get('website'),
                record.get('company_phone'),
                record.get('company_street'),
                record.get('company_city'),
                record.get('company_state'),
                record.get('company_postal_code'),
                reason_code,
                json.dumps(errors),
                json.dumps(warnings) if warnings else None,
                self.batch_id
            ))
        finally:
            cursor.close()

    def _mark_validated(self, record_id, passed, notes):
        """Mark record as validated in intake table"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                UPDATE intake.company_raw_intake
                SET
                    validated = %s,
                    validation_notes = %s,
                    validated_at = now(),
                    validated_by = 'validate_intake_final.py'
                WHERE id = %s
            """, (passed, notes, record_id))
        finally:
            cursor.close()

    def log_batch_summary(self):
        """Log validation summary"""
        if self.dry_run:
            return

        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO public.shq_validation_log (
                    validation_run_id, source_table, target_table,
                    total_records, passed_records, failed_records,
                    executed_by, notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.batch_id,
                'intake.company_raw_intake',
                'marketing.company_master (passed) / marketing.company_invalid (failed)',
                self.stats['total'],
                self.stats['passed'],
                self.stats['failed'],
                'validate_intake_final.py',
                f"Intake validation - {self.stats['passed']} promoted to master, {self.stats['failed']} sent to invalid"
            ))
            self.connection.commit()
        finally:
            cursor.close()

    def generate_summary(self):
        pass_rate = (self.stats['passed'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0

        return f"""
# Intake Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN (no changes)' if self.dry_run else 'PRODUCTION'}

## Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Processed** | {self.stats['total']:,} | 100.0% |
| **PASSED -> company_master** | {self.stats['passed']:,} | {pass_rate:.1f}% |
| **FAILED -> company_invalid** | {self.stats['failed']:,} | {100-pass_rate:.1f}% |

## Workflow

```
intake.company_raw_intake
         |
         v
   [VALIDATION]
         |
    ____/ \____
   /           \
PASSED        FAILED
   |             |
   v             v
company_master  company_invalid
```

## Validation Rules

- Company name completeness (min 2 chars, no placeholders)
- Website URL validation (not empty, not placeholder)
- Warnings: industry, employee count, phone

## Query Results

```sql
-- View promoted companies (PASSED)
SELECT company_name, website_url, validated_at
FROM marketing.company_master
WHERE source_system = 'intake_validation'
AND source_record_id::integer IN (
    SELECT id FROM intake.company_raw_intake WHERE validated = TRUE
)
ORDER BY validated_at DESC;

-- View failed companies (FAILED)
SELECT company_name, website, reason_code, validation_errors
FROM marketing.company_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;

-- Check intake validation status
SELECT
    validated,
    COUNT(*) as count
FROM intake.company_raw_intake
GROUP BY validated;
```

---

**Status**: {'DRY RUN Complete' if self.dry_run else 'Validation Complete'}
"""

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate intake data')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--revalidate', action='store_true', help='Revalidate already validated records')
    args = parser.parse_args()

    print("=" * 70)
    print("Intake Validation Pipeline")
    print("=" * 70)

    validator = IntakeValidator(dry_run=args.dry_run, revalidate=args.revalidate)

    try:
        validator.connect()
        validator.process_intake()
        if not args.dry_run:
            validator.log_batch_summary()

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
