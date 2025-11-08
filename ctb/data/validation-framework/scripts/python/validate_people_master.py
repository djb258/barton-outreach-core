#!/usr/bin/env python3
"""
Validate existing people in marketing.people_master

Workflow:
marketing.people_master -> Validate -> Keep in master (PASSED) | Move to people_invalid (FAILED)

Validation Rules:
- Full name completeness (first + last name OR full_name)
- Email format validation (RFC 5322 basic check)
- Warnings: missing phone, LinkedIn, title
"""

import os, sys, psycopg2, psycopg2.extras, re, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class PeopleValidator:
    def __init__(self, dry_run=False):
        self.batch_id = f"PEOPLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.dry_run = dry_run
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

    def validate_email(self, email):
        if not email or not email.strip():
            return False, "Email is empty"
        email = email.strip()
        # Basic RFC 5322 email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, f"Invalid email format: {email}"
        if email.lower() in ['test@test.com', 'example@example.com', 'n/a@n/a.com']:
            return False, f"Placeholder email: {email}"
        return True, None

    def validate_full_name(self, record):
        first_name = record.get('first_name')
        last_name = record.get('last_name')
        full_name = record.get('full_name')

        # Check if we have first + last OR full_name
        has_first_last = first_name and first_name.strip() and last_name and last_name.strip()
        has_full = full_name and full_name.strip() and len(full_name.strip()) >= 3

        if not has_first_last and not has_full:
            return False, "Missing complete name (need first+last OR full_name)"

        # Check for placeholders
        if first_name and first_name.lower() in ['test', 'example', 'n/a', 'none', 'null']:
            return False, f"Placeholder first name: {first_name}"
        if last_name and last_name.lower() in ['test', 'example', 'n/a', 'none', 'null']:
            return False, f"Placeholder last name: {last_name}"
        if full_name and full_name.lower() in ['test', 'example', 'n/a', 'none', 'null', 'test test']:
            return False, f"Placeholder full name: {full_name}"

        return True, None

    def validate_person(self, record):
        errors = []
        warnings = []

        # Critical validations
        name_valid, name_error = self.validate_full_name(record)
        if not name_valid:
            errors.append(name_error)

        email_valid, email_error = self.validate_email(record.get('email'))
        if not email_valid:
            errors.append(email_error)

        # Warnings
        if not record.get('title'):
            warnings.append("Title is missing")
        if not record.get('work_phone_e164') and not record.get('personal_phone_e164'):
            warnings.append("No phone number available")
        if not record.get('linkedin_url'):
            warnings.append("LinkedIn URL is missing")

        return len(errors) == 0, errors, warnings

    def process_people(self):
        """Process marketing.people_master"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            cursor.execute("""
                SELECT *
                FROM marketing.people_master
                ORDER BY unique_id
            """)

            records = cursor.fetchall()
            total = len(records)

            if total == 0:
                print("\n[INFO] No people records found in people_master")
                return 0

            print(f"\n[PEOPLE] Processing {total} people from marketing.people_master...\n")

            for i, record in enumerate(records, 1):
                record_dict = dict(record)
                is_valid, errors, warnings = self.validate_person(record_dict)

                if is_valid:
                    # PASSED - Keep in master (no action needed, already there)
                    self.stats['passed'] += 1
                    status = "[PASSED]"
                else:
                    # FAILED - Copy to people_invalid
                    if not self.dry_run:
                        self._insert_invalid(record_dict, errors, warnings)
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

    def _insert_invalid(self, record, errors, warnings):
        """Insert failed person to people_invalid"""
        cursor = self.connection.cursor()
        try:
            unique_id = record.get('unique_id')
            reason_code = errors[0] if errors else 'Validation failed'

            cursor.execute("""
                INSERT INTO marketing.people_invalid (
                    unique_id, full_name, first_name, last_name,
                    email, phone, title, linkedin_url,
                    company_unique_id, validation_status,
                    reason_code, validation_errors, validation_warnings,
                    failed_at, batch_id, source_table
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'FAILED', %s, %s, %s, now(), %s, 'marketing.people_master')
                ON CONFLICT (unique_id) DO UPDATE SET
                    reason_code = EXCLUDED.reason_code,
                    validation_errors = EXCLUDED.validation_errors,
                    batch_id = EXCLUDED.batch_id,
                    failed_at = now()
            """, (
                unique_id,
                record.get('full_name'),
                record.get('first_name'),
                record.get('last_name'),
                record.get('email'),
                record.get('work_phone_e164') or record.get('personal_phone_e164'),
                record.get('title'),
                record.get('linkedin_url'),
                record.get('company_unique_id'),
                reason_code,
                json.dumps(errors),
                json.dumps(warnings) if warnings else None,
                self.batch_id
            ))
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
                'marketing.people_master',
                'marketing.people_master (passed) / marketing.people_invalid (failed)',
                self.stats['total'],
                self.stats['passed'],
                self.stats['failed'],
                'validate_people_master.py',
                f"People validation - {self.stats['passed']} kept in master, {self.stats['failed']} sent to invalid"
            ))
            self.connection.commit()
        finally:
            cursor.close()

    def generate_summary(self):
        pass_rate = (self.stats['passed'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0

        return f"""
# People Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN (no changes)' if self.dry_run else 'PRODUCTION'}

## Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Processed** | {self.stats['total']:,} | 100.0% |
| **PASSED (kept in master)** | {self.stats['passed']:,} | {pass_rate:.1f}% |
| **FAILED -> people_invalid** | {self.stats['failed']:,} | {100-pass_rate:.1f}% |

## Workflow

```
marketing.people_master
         |
         v
   [VALIDATION]
         |
    ____/ \\____
   /           \\
PASSED        FAILED
   |             |
   v             v
(stay in       people_invalid
 master)
```

## Validation Rules

- Full name completeness (first+last OR full_name, min 3 chars)
- Email format validation (RFC 5322)
- No placeholder names/emails (test, example, n/a)
- Warnings: missing title, phone, LinkedIn

## Query Results

```sql
-- View all people (still in master)
SELECT unique_id, full_name, email, title
FROM marketing.people_master
ORDER BY created_at DESC;

-- View failed people (copied to invalid)
SELECT unique_id, full_name, email, reason_code, validation_errors
FROM marketing.people_invalid
WHERE batch_id = '{self.batch_id}'
ORDER BY failed_at DESC;

-- Count by validation status
SELECT
    CASE WHEN pi.unique_id IS NULL THEN 'PASSED' ELSE 'FAILED' END as status,
    COUNT(*) as count
FROM marketing.people_master pm
LEFT JOIN marketing.people_invalid pi ON pm.unique_id = pi.unique_id
    AND pi.batch_id = '{self.batch_id}'
GROUP BY CASE WHEN pi.unique_id IS NULL THEN 'PASSED' ELSE 'FAILED' END;
```

---

**Status**: {'DRY RUN Complete' if self.dry_run else 'Validation Complete'}
"""

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate people in people_master')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    args = parser.parse_args()

    print("=" * 70)
    print("People Validation Pipeline (people_master)")
    print("=" * 70)

    validator = PeopleValidator(dry_run=args.dry_run)

    try:
        validator.connect()
        validator.process_people()
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
