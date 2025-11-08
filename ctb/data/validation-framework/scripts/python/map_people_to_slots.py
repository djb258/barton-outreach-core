#!/usr/bin/env python3
"""
Map People to Company Slots (CEO, CFO, HR)

Workflow:
1. Create 3 slots (CEO, CFO, HR) for each company in company_master
2. Map people from people_master to slots based on title matching
3. Generate Barton IDs for slots: 04.04.02.04.10000.XXX
4. Track confidence scores for matches
"""

import os, sys, psycopg2, psycopg2.extras, re, uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SlotMapper:
    def __init__(self, dry_run=False):
        self.batch_id = f"SLOT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        self.connection = None
        self.dry_run = dry_run
        self.stats = {
            'slots_created': 0,
            'ceo_filled': 0,
            'cfo_filled': 0,
            'hr_filled': 0,
            'unfilled': 0
        }

        # Title patterns for matching (case-insensitive)
        # Ordered by confidence - more specific matches first
        self.ceo_patterns = [
            r'\bCEO\b',
            r'\bChief Executive Officer\b',
            r'\bChief Executive\b',  # Added
            r'\bPresident\s*[/&,]?\s*CEO\b',
            r'\bCEO\s*[/&,]?\s*President\b',
            r'\bCo-?Founder\s*[/&,]?\s*CEO\b',  # Added
            r'\bCEO\s*[/&,]?\s*Co-?Founder\b',  # Added
            r'\bFounder\s*[/&,]?\s*President\b',  # Added
            r'\bPresident\s*[/&,]?\s*Founder\b',  # Added
            r'\bExecutive Director\b',
            r'\bManaging Director\b',
        ]

        self.cfo_patterns = [
            r'\bCFO\b',
            r'\bChief Financial Officer\b',
            r'\bChief.*Financial\b',  # Catches variations
            r'\bVice President\s*[/&,]?\s*CFO\b',
            r'\bVP\s*[,]?\s*Finance\b',
            r'\bVice President.*Financial\b',
            r'\bVP.*CFO\b',
            r'\bController\b',
            r'\bTreasurer\b',
            r'\bChief School Business Official\b',  # Added for education sector
        ]

        self.hr_patterns = [
            r'\bCHRO\b',
            r'\bChief Human Resources Officer\b',
            r'\bVP\s*[,]?\s*Human Resources\b',
            r'\bVice President.*Human Resources\b',  # Added
            r'\bHR\s+Director\b',
            r'\bHuman Resources Director\b',
            r'\bHR\s+Manager\b',
            r'\bHuman Resources Manager\b',
            r'\bHuman Resources.*Manager\b',  # Catches "HR Payroll Manager"
            r'\bHuman Resources.*Coordinator\b',  # Added
            r'\bHuman Resources.*Specialist\b',  # Added
            r'\bBenefits.*Manager\b',  # Added for "VP & Benefits Manager"
            r'\bPeople\s+Officer\b',
        ]

    def connect(self):
        self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        self.connection.autocommit = False
        print(f"[OK] Connected to Neon")
        if self.dry_run:
            print("[DRY RUN] No data will be written\n")

    def close(self):
        if self.connection:
            self.connection.close()

    def matches_pattern(self, title, patterns):
        """Check if title matches any of the patterns"""
        if not title:
            return False, 0.0

        title_clean = title.strip()

        for i, pattern in enumerate(patterns):
            if re.search(pattern, title_clean, re.IGNORECASE):
                # Higher confidence for exact matches at start of list
                confidence = 1.0 - (i * 0.1)  # 1.0, 0.9, 0.8, etc.
                return True, max(confidence, 0.5)

        return False, 0.0

    def detect_slot_type(self, title):
        """Detect which slot type this person should fill"""
        if not title:
            return None, 0.0

        # Check CEO first (highest priority)
        is_ceo, ceo_conf = self.matches_pattern(title, self.ceo_patterns)
        if is_ceo:
            return 'CEO', ceo_conf

        # Check CFO
        is_cfo, cfo_conf = self.matches_pattern(title, self.cfo_patterns)
        if is_cfo:
            return 'CFO', cfo_conf

        # Check HR
        is_hr, hr_conf = self.matches_pattern(title, self.hr_patterns)
        if is_hr:
            return 'HR', hr_conf

        return None, 0.0

    def create_slots_for_companies(self):
        """Create 3 slots (CEO, CFO, HR) for each company"""
        cursor = self.connection.cursor()

        try:
            # Get all companies
            cursor.execute("SELECT company_unique_id FROM marketing.company_master ORDER BY company_unique_id")
            companies = cursor.fetchall()

            print(f"\n[SLOTS] Creating 3 slots (CEO, CFO, HR) for {len(companies)} companies...")

            slot_counter = 1
            for company_unique_id, in companies:
                for slot_type in ['CEO', 'CFO', 'HR']:
                    # Generate Barton ID: 04.04.02.04.10000.XXX
                    slot_id = f"04.04.02.04.{10000 + (slot_counter % 100):05d}.{slot_counter:03d}"

                    if not self.dry_run:
                        cursor.execute("""
                            INSERT INTO marketing.company_slot (
                                company_slot_unique_id,
                                company_unique_id,
                                slot_type,
                                is_filled,
                                source_system,
                                created_at
                            )
                            VALUES (%s, %s, %s, FALSE, %s, now())
                            ON CONFLICT (company_unique_id, slot_type) DO NOTHING
                        """, (slot_id, company_unique_id, slot_type, 'slot_mapper'))

                    self.stats['slots_created'] += 1
                    slot_counter += 1

            if not self.dry_run:
                self.connection.commit()
                print(f"[OK] Created {self.stats['slots_created']} slots")
            else:
                print(f"[DRY RUN] Would create {self.stats['slots_created']} slots")

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error creating slots: {e}")
            raise
        finally:
            cursor.close()

    def map_people_to_slots(self):
        """Map people to slots based on their titles, handling duplicates intelligently"""
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Step 1: Clear existing mappings
            if not self.dry_run:
                cursor.execute("""
                    UPDATE marketing.company_slot
                    SET person_unique_id = NULL,
                        is_filled = FALSE,
                        confidence_score = NULL,
                        filled_at = NULL,
                        filled_by = NULL
                """)
                print(f"[CLEAR] Cleared existing slot mappings\n")

            # Step 2: Get all people with companies and titles
            cursor.execute("""
                SELECT
                    pm.unique_id,
                    pm.full_name,
                    pm.title,
                    pm.company_unique_id,
                    cm.company_name
                FROM marketing.people_master pm
                JOIN marketing.company_master cm ON pm.company_unique_id = cm.company_unique_id
                WHERE pm.title IS NOT NULL
                ORDER BY pm.unique_id
            """)

            people = cursor.fetchall()
            print(f"[MAPPING] Processing {len(people)} people with titles...\n")

            # Step 3: Group people by (company_id, slot_type) and pick best match
            from collections import defaultdict
            candidates = defaultdict(list)  # {(company_id, slot_type): [(person, confidence), ...]}

            for person in people:
                slot_type, confidence = self.detect_slot_type(person['title'])
                if slot_type:
                    key = (person['company_unique_id'], slot_type)
                    candidates[key].append((person, confidence))

            # Step 4: For each slot, pick the person with highest confidence
            mapped_count = 0
            skipped_count = 0
            duplicate_count = 0

            for (company_id, slot_type), person_list in sorted(candidates.items()):
                if len(person_list) > 1:
                    # DUPLICATE: Multiple people for same slot
                    # Pick the one with highest confidence
                    person_list_sorted = sorted(person_list, key=lambda x: x[1], reverse=True)
                    best_person, best_conf = person_list_sorted[0]
                    duplicate_count += len(person_list) - 1

                    print(f"  [DUPLICATE] {slot_type} at {best_person['company_name'][:40]:40} - {len(person_list)} candidates, picked {best_person['full_name'][:25]:25} (conf: {best_conf:.2f})")
                    for other_person, other_conf in person_list_sorted[1:]:
                        print(f"              Skipped: {other_person['full_name'][:25]:25} (conf: {other_conf:.2f})")

                    person, confidence = best_person, best_conf
                else:
                    person, confidence = person_list[0]

                # Map the selected person to the slot
                if not self.dry_run:
                    cursor.execute("""
                        UPDATE marketing.company_slot
                        SET
                            person_unique_id = %s,
                            is_filled = TRUE,
                            confidence_score = %s,
                            filled_at = now(),
                            filled_by = %s,
                            last_refreshed_at = now()
                        WHERE company_unique_id = %s
                        AND slot_type = %s
                    """, (
                        person['unique_id'],
                        confidence,
                        'slot_mapper_v2',
                        company_id,
                        slot_type
                    ))

                    if cursor.rowcount > 0:
                        mapped_count += 1
                        self.stats[f'{slot_type.lower()}_filled'] += 1
                        if len(person_list) == 1:
                            print(f"  [MAPPED] {person['full_name'][:30]:30} -> {slot_type:3} at {person['company_name'][:40]:40} (conf: {confidence:.2f})")
                    else:
                        skipped_count += 1
                else:
                    mapped_count += 1
                    self.stats[f'{slot_type.lower()}_filled'] += 1
                    print(f"  [WOULD MAP] {person['full_name'][:30]:30} -> {slot_type:3} at {person['company_name'][:40]:40} (conf: {confidence:.2f})")

            # Count people with no matching slot
            no_match_count = len(people) - (mapped_count + duplicate_count)

            if not self.dry_run:
                self.connection.commit()
                print(f"\n[OK] Mapped {mapped_count} people to slots")
                print(f"     Resolved {duplicate_count} duplicates (picked best match)")
                print(f"     Skipped {no_match_count} people (no CEO/CFO/HR title match)")
            else:
                print(f"\n[DRY RUN] Would map {mapped_count} people")
                print(f"          Would resolve {duplicate_count} duplicates")
                print(f"          Would skip {no_match_count} people")

        except Exception as e:
            self.connection.rollback()
            print(f"[FAIL] Error mapping people: {e}")
            raise
        finally:
            cursor.close()

    def calculate_unfilled(self):
        """Calculate unfilled slots"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM marketing.company_slot WHERE is_filled = FALSE")
            self.stats['unfilled'] = cursor.fetchone()[0]
        finally:
            cursor.close()

    def generate_summary(self):
        total_slots = self.stats['slots_created']
        filled = self.stats['ceo_filled'] + self.stats['cfo_filled'] + self.stats['hr_filled']
        fill_rate = (filled / total_slots * 100) if total_slots > 0 else 0

        return f"""
# Slot Mapping Summary

**Batch ID**: `{self.batch_id}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'DRY RUN (no changes)' if self.dry_run else 'PRODUCTION'}

## Results

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Slots Created** | {total_slots:,} | 100.0% |
| **Filled** | {filled:,} | {fill_rate:.1f}% |
| **Unfilled** | {self.stats['unfilled']:,} | {100-fill_rate:.1f}% |

### By Slot Type

| Slot Type | Filled | Unfilled | Total |
|-----------|--------|----------|-------|
| **CEO** | {self.stats['ceo_filled']} | {total_slots//3 - self.stats['ceo_filled']} | {total_slots//3} |
| **CFO** | {self.stats['cfo_filled']} | {total_slots//3 - self.stats['cfo_filled']} | {total_slots//3} |
| **HR** | {self.stats['hr_filled']} | {total_slots//3 - self.stats['hr_filled']} | {total_slots//3} |

## Workflow

```
Step 1: Create Slots
  company_master (453 companies)
         |
         v
  Create 3 slots per company
         |
         v
  company_slot ({total_slots} slots: CEO, CFO, HR)

Step 2: Map People
  people_master (170 people)
         |
         v
  Match title patterns
         |
    ____/ \\____
   /           \\
MATCHED      NO MATCH
   |             |
   v             v
Fill slot    Leave unfilled
```

## Title Matching Patterns

**CEO Patterns**:
- CEO, Chief Executive Officer
- President/CEO, CEO/President
- Executive Director, Managing Director

**CFO Patterns**:
- CFO, Chief Financial Officer
- VP Finance, Vice President Finance
- Controller, Treasurer

**HR Patterns**:
- CHRO, Chief Human Resources Officer
- VP Human Resources, HR Director
- Human Resources Manager

## Query Results

```sql
-- View all filled slots
SELECT
    cs.company_slot_unique_id,
    cm.company_name,
    cs.slot_type,
    pm.full_name as person_name,
    pm.title,
    cs.confidence_score,
    cs.filled_at
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
LEFT JOIN marketing.people_master pm ON cs.person_unique_id = pm.unique_id
WHERE cs.is_filled = TRUE
ORDER BY cm.company_name, cs.slot_type;

-- View unfilled slots
SELECT
    cm.company_name,
    cs.slot_type,
    cs.company_slot_unique_id
FROM marketing.company_slot cs
JOIN marketing.company_master cm ON cs.company_unique_id = cm.company_unique_id
WHERE cs.is_filled = FALSE
ORDER BY cm.company_name, cs.slot_type;

-- Summary by slot type
SELECT
    slot_type,
    COUNT(*) as total,
    COUNT(person_unique_id) as filled,
    COUNT(*) - COUNT(person_unique_id) as unfilled
FROM marketing.company_slot
GROUP BY slot_type
ORDER BY slot_type;
```

---

**Status**: {'DRY RUN Complete' if self.dry_run else 'Mapping Complete'}
"""

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Map people to company slots')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--skip-create', action='store_true', help='Skip slot creation (only map people)')
    args = parser.parse_args()

    print("=" * 70)
    print("Company Slot Mapping (CEO, CFO, HR)")
    print("=" * 70)

    mapper = SlotMapper(dry_run=args.dry_run)

    try:
        mapper.connect()

        if not args.skip_create:
            mapper.create_slots_for_companies()
        else:
            print("\n[SKIP] Skipping slot creation (--skip-create)")

        mapper.map_people_to_slots()
        mapper.calculate_unfilled()

        print("\n" + "=" * 70)
        print(mapper.generate_summary())
        print("=" * 70)

    except Exception as e:
        print(f"\n[FAIL] Mapping failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        mapper.close()

if __name__ == '__main__':
    main()
