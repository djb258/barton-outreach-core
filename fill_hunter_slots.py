#!/usr/bin/env python3
"""
Fill company slots with Hunter contacts from CSV files.

Processes CEO, CFO, and HR slot contacts:
1. Creates records in people.people_master
2. Updates corresponding slots in people.company_slot

Author: Claude Code
Date: 2026-02-07
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters from environment
DB_CONFIG = {
    'host': os.environ['NEON_HOST'],
    'database': os.environ['NEON_DATABASE'],
    'user': os.environ['NEON_USER'],
    'password': os.environ['NEON_PASSWORD'],
    'sslmode': 'require'
}

# CSV file paths
CSV_FILES = {
    'CEO': r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\slot_contacts\ceo_slot_contacts.csv',
    'CFO': r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\slot_contacts\cfo_slot_contacts.csv',
    'HR': r'C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\slot_contacts\hr_slot_contacts.csv'
}


class SlotFiller:
    """Processes Hunter contacts and fills company slots."""

    def __init__(self):
        self.conn = None
        self.stats = {
            'people_created': 0,
            'people_existing': 0,
            'slots_filled': 0,
            'slots_already_filled': 0,
            'slots_not_found': 0,
            'errors': []
        }

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("[OK] Connected to Neon PostgreSQL")
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("\n[OK] Database connection closed")

    def read_csv(self, filepath: str) -> List[Dict]:
        """Read CSV file and return list of contact records."""
        contacts = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    contacts.append(row)
            print(f"[OK] Read {len(contacts)} contacts from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[ERROR] Error reading {filepath}: {e}")
            self.stats['errors'].append(f"CSV read error: {filepath} - {e}")

        return contacts

    def create_person(self, contact: Dict, cursor) -> str:
        """
        Create person in people.people_master.
        Returns unique_id (new or existing).
        """
        # Generate deterministic unique_id based on email to avoid duplicates
        email = contact['email'].strip().lower()

        # Check if person already exists by email
        cursor.execute(
            "SELECT unique_id FROM people.people_master WHERE LOWER(email) = %s",
            (email,)
        )
        existing = cursor.fetchone()

        if existing:
            self.stats['people_existing'] += 1
            return existing[0]

        # Insert new person
        insert_query = """
            INSERT INTO people.people_master (
                unique_id,
                first_name,
                last_name,
                full_name,
                email,
                title,
                linkedin_url,
                source_system,
                created_at
            ) VALUES (
                gen_random_uuid()::text,
                %s, %s, %s, %s, %s, %s, %s, NOW()
            )
            RETURNING unique_id
        """

        first_name = contact['first_name'].strip()
        last_name = contact['last_name'].strip()
        full_name = f"{first_name} {last_name}"
        job_title = contact['job_title'].strip() if contact['job_title'] else None
        linkedin = contact['linkedin'].strip() if contact['linkedin'] else None

        try:
            cursor.execute(
                insert_query,
                (first_name, last_name, full_name, email, job_title, linkedin, 'hunter')
            )
            unique_id = cursor.fetchone()[0]
            self.stats['people_created'] += 1
            return unique_id

        except Exception as e:
            # If there's a conflict despite our check, try to get existing ID
            cursor.execute(
                "SELECT unique_id FROM people.people_master WHERE LOWER(email) = %s",
                (email,)
            )
            result = cursor.fetchone()
            if result:
                self.stats['people_existing'] += 1
                return result[0]
            else:
                raise e

    def fill_slot(self, contact: Dict, person_unique_id: str, cursor) -> bool:
        """
        Update company_slot with person_unique_id.
        Returns True if slot was filled, False otherwise.
        """
        outreach_id = contact['outreach_id'].strip()
        slot_type = contact['slot_type'].strip().upper()

        # Check if slot exists and is not already filled
        cursor.execute(
            """
            SELECT slot_id, is_filled, person_unique_id
            FROM people.company_slot
            WHERE outreach_id = %s
              AND slot_type = %s
            """,
            (outreach_id, slot_type)
        )

        result = cursor.fetchone()

        if not result:
            self.stats['slots_not_found'] += 1
            self.stats['errors'].append(
                f"Slot not found: outreach_id={outreach_id}, slot_type={slot_type}"
            )
            return False

        slot_id, is_filled, existing_person_id = result

        if is_filled and existing_person_id:
            self.stats['slots_already_filled'] += 1
            return False

        # Update the slot
        update_query = """
            UPDATE people.company_slot
            SET
                person_unique_id = %s,
                is_filled = TRUE,
                filled_at = NOW(),
                source_system = 'hunter',
                updated_at = NOW()
            WHERE slot_id = %s
        """

        try:
            cursor.execute(update_query, (person_unique_id, slot_id))
            self.stats['slots_filled'] += 1
            return True

        except Exception as e:
            self.stats['errors'].append(
                f"Slot update failed: slot_id={slot_id}, error={e}"
            )
            return False

    def process_contacts(self, contacts: List[Dict], slot_type: str):
        """Process a batch of contacts for a specific slot type."""
        cursor = self.conn.cursor()

        print(f"\n{'='*60}")
        print(f"Processing {slot_type} contacts ({len(contacts)} records)")
        print(f"{'='*60}")

        batch_stats = {
            'processed': 0,
            'people_created': 0,
            'slots_filled': 0
        }

        for idx, contact in enumerate(contacts, 1):
            try:
                # Create or get person
                person_unique_id = self.create_person(contact, cursor)

                # Fill slot
                filled = self.fill_slot(contact, person_unique_id, cursor)

                batch_stats['processed'] += 1

                if idx % 100 == 0:
                    self.conn.commit()
                    print(f"  Progress: {idx}/{len(contacts)} ({idx/len(contacts)*100:.1f}%)")

            except Exception as e:
                self.stats['errors'].append(
                    f"{slot_type} - Row {idx}: {e}"
                )
                self.conn.rollback()
                continue

        # Final commit
        self.conn.commit()
        cursor.close()

        print(f"\n{slot_type} Batch Complete:")
        print(f"  Processed: {batch_stats['processed']}")
        print(f"  New people created: {self.stats['people_created']}")
        print(f"  Slots filled: {self.stats['slots_filled']}")

    def run(self):
        """Main execution flow."""
        print("\n" + "="*60)
        print("HUNTER SLOT FILLER - Starting")
        print("="*60)

        self.connect()

        # Process each CSV file
        for slot_type, filepath in CSV_FILES.items():
            if not os.path.exists(filepath):
                print(f"\n[ERROR] File not found: {filepath}")
                continue

            contacts = self.read_csv(filepath)
            if contacts:
                self.process_contacts(contacts, slot_type)

        self.close()
        self.print_summary()

    def print_summary(self):
        """Print final statistics summary."""
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"\nPeople Master:")
        print(f"  New people created:     {self.stats['people_created']:,}")
        print(f"  Existing people found:  {self.stats['people_existing']:,}")
        print(f"  Total people processed: {self.stats['people_created'] + self.stats['people_existing']:,}")

        print(f"\nCompany Slots:")
        print(f"  Slots filled:           {self.stats['slots_filled']:,}")
        print(f"  Slots already filled:   {self.stats['slots_already_filled']:,}")
        print(f"  Slots not found:        {self.stats['slots_not_found']:,}")

        if self.stats['errors']:
            print(f"\nErrors ({len(self.stats['errors'])}):")
            # Show first 10 errors
            for error in self.stats['errors'][:10]:
                print(f"  • {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
        else:
            print(f"\n[OK] No errors encountered")

        print("\n" + "="*60)


if __name__ == '__main__':
    filler = SlotFiller()
    try:
        filler.run()
    except KeyboardInterrupt:
        print("\n\n[ERROR] Process interrupted by user")
        if filler.conn:
            filler.conn.rollback()
            filler.close()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        if filler.conn:
            filler.conn.rollback()
            filler.close()
        sys.exit(1)
