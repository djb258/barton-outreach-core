#!/usr/bin/env python3
"""
Apollo Import Completeness Validation

Company COMPLETE when:
- Address (city + state minimum)
- Website URL
- Company LinkedIn URL
- ALL 3 slots filled (CEO + CFO + HR)

Person COMPLETE when:
- Mapped to a company slot
- Email address
- LinkedIn URL
- Phone (optional - nice to have)

Incomplete records → enrichment_queue for agents to fix
After agent enrichment → re-validate immediately
"""

import os, sys, psycopg2, psycopg2.extras, json, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CompletenessValidator:
    def __init__(self, dry_run=False):
        self.batch_id = f"COMPLETE-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.dry_run = dry_run
        self.stats = {
            'companies_complete': 0,
            'companies_incomplete': 0,
            'people_complete': 0,
            'people_incomplete': 0,
        }

    def connect(self):
        self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.connection.autocommit = False
        print(f"[OK] Connected to Neon")
        if self.dry_run:
            print("[DRY RUN] No data will be written\n")

    def close(self):
        if self.connection:
            self.connection.close()

    def validate_company_completeness(self, company):
        """
        Check if company has ALL required data:
        - City + State (address)
        - Website URL
        - Company LinkedIn
        - All 3 slots filled (CEO, CFO, HR)
        """
        missing = []
        warnings = []

        # Required: Address (city + state minimum)
        if not company.get('address_city') or not company.get('address_state'):
            missing.append('address (need city + state)')

        # Required: Website
        if not company.get('website_url'):
            missing.append('website URL')

        # Required: Company LinkedIn
        if not company.get('linkedin_url'):
            missing.append('company LinkedIn')

        # Required: All 3 slots filled
        filled_slots = self.get_filled_slot_count(company['company_unique_id'])
        if filled_slots < 3:
            missing.append(f'executives ({filled_slots}/3 filled - need CEO, CFO, HR)')

        # Optional: Full address
        if not company.get('address_street'):
            warnings.append('Missing street address (only have city/state)')

        is_complete = len(missing) == 0
        return is_complete, missing, warnings

    def validate_person_completeness(self, person):
        """
        Check if person has ALL required data:
        - Mapped to company slot (CEO, CFO, or HR)
        - Email
        - LinkedIn URL
        - Phone (optional)
        """
        missing = []
        warnings = []

        # Required: Must be in a company slot
        if not person.get('is_in_slot'):
            missing.append('not mapped to company slot (CEO/CFO/HR)')

        # Required: Email
        if not person.get('email'):
            missing.append('email')

        # Required: LinkedIn
        if not person.get('linkedin_url'):
            missing.append('LinkedIn URL')

        # Optional: Phone (just warning)
        if not person.get('work_phone_e164') and not person.get('personal_phone_e164'):
            warnings.append('phone number (nice to have)')

        is_complete = len(missing) == 0
        return is_complete, missing, warnings

    def get_filled_slot_count(self, company_unique_id):
        """Get number of filled slots for a company"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM marketing.company_slot
                WHERE company_unique_id = %s
                AND is_filled = TRUE
            """, (company_unique_id,))
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def process_companies(self):
        """Validate all companies for completeness"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get all companies
            cursor.execute("""
                SELECT
                    company_unique_id,
                    company_name,
                    address_street,
                    address_city,
                    address_state,
                    website_url,
                    linkedin_url,
                    employee_count
                FROM marketing.company_master
                ORDER BY company_name
            """)

            companies = cursor.fetchall()
            total = len(companies)

            print(f"\n[COMPANIES] Validating {total} companies for completeness...\n")

            for i, company in enumerate(companies, 1):
                is_complete, missing, warnings = self.validate_company_completeness(company)

                if is_complete:
                    # COMPLETE - mark as validated
                    self.stats['companies_complete'] += 1
                    if not self.dry_run:
                        self.mark_company_complete(company['company_unique_id'])

                    if i % 100 == 0:
                        print(f"  [COMPLETE] {i}/{total} - {company['company_name'][:50]:50}")

                else:
                    # INCOMPLETE - send to enrichment queue
                    self.stats['companies_incomplete'] += 1
                    if not self.dry_run:
                        self.send_company_to_enrichment_queue(company, missing, warnings)

                    print(f"  [INCOMPLETE] {company['company_name'][:50]:50} | Missing: {', '.join(missing)}")

            if not self.dry_run:
                self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def process_people(self):
        """Validate all people for completeness"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get all people with slot information
            cursor.execute("""
                SELECT
                    pm.unique_id,
                    pm.full_name,
                    pm.email,
                    pm.linkedin_url,
                    pm.work_phone_e164,
                    pm.personal_phone_e164,
                    pm.company_unique_id,
                    cm.company_name,
                    cs.slot_type,
                    cs.is_filled as is_in_slot
                FROM marketing.people_master pm
                JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
                LEFT JOIN marketing.company_slot cs ON pm.unique_id = cs.person_unique_id
                ORDER BY pm.full_name
            """)

            people = cursor.fetchall()
            total = len(people)

            print(f"\n[PEOPLE] Validating {total} people for completeness...\n")

            for i, person in enumerate(people, 1):
                is_complete, missing, warnings = self.validate_person_completeness(person)

                if is_complete:
                    # COMPLETE
                    self.stats['people_complete'] += 1

                    if i % 100 == 0:
                        print(f"  [COMPLETE] {i}/{total} - {person['full_name'][:40]:40} ({person.get('slot_type', 'N/A')})")

                else:
                    # INCOMPLETE - send to enrichment queue
                    self.stats['people_incomplete'] += 1
                    if not self.dry_run:
                        self.send_person_to_enrichment_queue(person, missing, warnings)

                    print(f"  [INCOMPLETE] {person['full_name'][:40]:40} | Missing: {', '.join(missing)}")

            if not self.dry_run:
                self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error: {e}")
            raise
        finally:
            cursor.close()

    def mark_company_complete(self, company_unique_id):
        """Mark company as complete (no enrichment needed)"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                UPDATE marketing.company_master
                SET
                    completeness_validated = TRUE,
                    completeness_validated_at = now(),
                    needs_enrichment = FALSE
                WHERE company_unique_id = %s
            """, (company_unique_id,))
        finally:
            cursor.close()

    def send_company_to_enrichment_queue(self, company, missing, warnings):
        """Send incomplete company to enrichment queue"""
        cursor = self.connection.cursor()
        try:
            # Create enrichment task
            enrichment_tasks = []

            if 'address' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'find_address',
                    'priority': 'high',
                    'agent': 'google_maps_api'
                })

            if 'website URL' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'find_website',
                    'priority': 'high',
                    'agent': 'clearbit_or_google'
                })

            if 'company LinkedIn' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'find_company_linkedin',
                    'priority': 'high',
                    'agent': 'linkedin_api'
                })

            if 'executives' in ', '.join(missing):
                # Parse how many slots are missing
                import re
                match = re.search(r'(\d+)/3 filled', ', '.join(missing))
                if match:
                    filled = int(match.group(1))
                    missing_count = 3 - filled

                enrichment_tasks.append({
                    'task': 'find_executives',
                    'priority': 'critical',
                    'agent': 'apollo_linkedin_scraper',
                    'details': f'Need {missing_count} more executives (total: {filled}/3)',
                    'target_roles': self.get_missing_slot_types(company['company_unique_id'])
                })

            cursor.execute("""
                INSERT INTO marketing.enrichment_queue (
                    entity_type,
                    entity_id,
                    company_name,
                    missing_fields,
                    enrichment_tasks,
                    priority,
                    status,
                    created_at,
                    batch_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, now(), %s)
                ON CONFLICT (entity_type, entity_id) DO UPDATE SET
                    missing_fields = EXCLUDED.missing_fields,
                    enrichment_tasks = EXCLUDED.enrichment_tasks,
                    status = 'pending',
                    updated_at = now()
            """, (
                'company',
                company['company_unique_id'],
                company['company_name'],
                json.dumps(missing),
                json.dumps(enrichment_tasks),
                'high' if 'executives' in ', '.join(missing) else 'medium',
                'pending',
                self.batch_id
            ))

            # Also update company_master
            cursor.execute("""
                UPDATE marketing.company_master
                SET
                    completeness_validated = FALSE,
                    needs_enrichment = TRUE,
                    enrichment_queued_at = now()
                WHERE company_unique_id = %s
            """, (company['company_unique_id'],))

        finally:
            cursor.close()

    def send_person_to_enrichment_queue(self, person, missing, warnings):
        """Send incomplete person to enrichment queue"""
        cursor = self.connection.cursor()
        try:
            enrichment_tasks = []

            if 'email' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'find_email',
                    'priority': 'high',
                    'agent': 'apollo_hunter_io'
                })

            if 'LinkedIn URL' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'find_linkedin_profile',
                    'priority': 'high',
                    'agent': 'linkedin_api'
                })

            if 'not mapped to company slot' in ', '.join(missing):
                enrichment_tasks.append({
                    'task': 'determine_role',
                    'priority': 'critical',
                    'agent': 'title_classifier',
                    'details': f"Title: {person.get('title', 'unknown')}"
                })

            if 'phone number' in ', '.join(warnings):
                enrichment_tasks.append({
                    'task': 'find_phone',
                    'priority': 'low',
                    'agent': 'apollo_zoominfo'
                })

            cursor.execute("""
                INSERT INTO marketing.enrichment_queue (
                    entity_type,
                    entity_id,
                    company_name,
                    person_name,
                    missing_fields,
                    enrichment_tasks,
                    priority,
                    status,
                    created_at,
                    batch_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s)
                ON CONFLICT (entity_type, entity_id) DO UPDATE SET
                    missing_fields = EXCLUDED.missing_fields,
                    enrichment_tasks = EXCLUDED.enrichment_tasks,
                    status = 'pending',
                    updated_at = now()
            """, (
                'person',
                person['unique_id'],
                person.get('company_name'),
                person['full_name'],
                json.dumps(missing),
                json.dumps(enrichment_tasks),
                'high' if 'not mapped' in ', '.join(missing) else 'medium',
                'pending',
                self.batch_id
            ))

        finally:
            cursor.close()

    def get_missing_slot_types(self, company_unique_id):
        """Get which slot types are empty for a company"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT slot_type
                FROM marketing.company_slot
                WHERE company_unique_id = %s
                AND is_filled = FALSE
            """, (company_unique_id,))
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def generate_summary(self):
        total_companies = self.stats['companies_complete'] + self.stats['companies_incomplete']
        total_people = self.stats['people_complete'] + self.stats['people_incomplete']

        company_complete_rate = (self.stats['companies_complete'] / total_companies * 100) if total_companies > 0 else 0
        people_complete_rate = (self.stats['people_complete'] / total_people * 100) if total_people > 0 else 0

        return f"""
# Completeness Validation Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN' if self.dry_run else 'PRODUCTION'}

## Companies

| Status | Count | Percentage |
|--------|-------|------------|
| **COMPLETE** | {self.stats['companies_complete']:,} | {company_complete_rate:.1f}% |
| **INCOMPLETE (→ enrichment)** | {self.stats['companies_incomplete']:,} | {100-company_complete_rate:.1f}% |
| **TOTAL** | {total_companies:,} | 100.0% |

## People

| Status | Count | Percentage |
|--------|-------|------------|
| **COMPLETE** | {self.stats['people_complete']:,} | {people_complete_rate:.1f}% |
| **INCOMPLETE (→ enrichment)** | {self.stats['people_incomplete']:,} | {100-people_complete_rate:.1f}% |
| **TOTAL** | {total_people:,} | 100.0% |

## Completeness Criteria

### Company is COMPLETE when:
✅ Address (city + state minimum)
✅ Website URL
✅ Company LinkedIn URL
✅ ALL 3 slots filled (CEO + CFO + HR)

### Person is COMPLETE when:
✅ Mapped to company slot (CEO, CFO, or HR)
✅ Email address
✅ LinkedIn URL
⚠️ Phone (optional - nice to have)

## Next Steps

1. **Process enrichment queue** ({self.stats['companies_incomplete'] + self.stats['people_incomplete']:,} records)
   - Agents find missing data
   - Re-validate immediately after enrichment

2. **Query enrichment tasks**:
```sql
-- Companies needing enrichment
SELECT * FROM marketing.enrichment_queue
WHERE entity_type = 'company' AND status = 'pending'
ORDER BY priority DESC, created_at;

-- People needing enrichment
SELECT * FROM marketing.enrichment_queue
WHERE entity_type = 'person' AND status = 'pending'
ORDER BY priority DESC, created_at;
```

3. **Monitor completion rate**:
```sql
SELECT
    COUNT(*) FILTER (WHERE completeness_validated = TRUE) as complete,
    COUNT(*) FILTER (WHERE needs_enrichment = TRUE) as needs_enrichment,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE completeness_validated = TRUE) / COUNT(*), 1) as complete_pct
FROM marketing.company_master;
```

---

**Status**: {'DRY RUN Complete' if self.dry_run else 'Validation Complete - Enrichment Queue Ready'}
"""

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Validate completeness of Apollo import')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--companies-only', action='store_true', help='Only validate companies')
    parser.add_argument('--people-only', action='store_true', help='Only validate people')
    args = parser.parse_args()

    print("=" * 70)
    print("Apollo Import Completeness Validation")
    print("=" * 70)

    validator = CompletenessValidator(dry_run=args.dry_run)

    try:
        validator.connect()

        if not args.people_only:
            validator.process_companies()

        if not args.companies_only:
            validator.process_people()

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
