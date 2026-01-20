#!/usr/bin/env python3
"""Test the slot_assignment_history trigger."""

import os
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_url = os.getenv("DATABASE_URL")
import psycopg2
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

print("="*60)
print("TESTING SLOT ASSIGNMENT HISTORY TRIGGER")
print("="*60)

# Find a test slot to update
print("\n1. Finding a test slot...")
cursor.execute("""
    SELECT company_slot_unique_id, company_unique_id, slot_type, person_unique_id, is_filled
    FROM people.company_slot
    WHERE person_unique_id IS NULL
    LIMIT 1
""")
test_slot = cursor.fetchone()

if not test_slot:
    print("No empty slots found. Looking for filled slot to test displacement...")
    cursor.execute("""
        SELECT company_slot_unique_id, company_unique_id, slot_type, person_unique_id, is_filled
        FROM people.company_slot
        WHERE person_unique_id IS NOT NULL
        LIMIT 1
    """)
    test_slot = cursor.fetchone()

if not test_slot:
    print("No slots found to test!")
    sys.exit(1)

slot_id, company_id, slot_type, current_person, is_filled = test_slot
print(f"   Found slot: {slot_id}")
print(f"   Company: {company_id}")
print(f"   Slot type: {slot_type}")
print(f"   Current person: {current_person}")
print(f"   Is filled: {is_filled}")

# Count history before
cursor.execute("SELECT COUNT(*) FROM people.slot_assignment_history")
count_before = cursor.fetchone()[0]
print(f"\n2. History records before: {count_before}")

# Find an existing person to use (FK constraint requires valid person)
cursor.execute("""
    SELECT unique_id FROM people.people_master LIMIT 1
""")
existing_person = cursor.fetchone()

if existing_person:
    test_person_id = existing_person[0]
else:
    print("No existing person found in people_master. Creating test record...")
    test_person_id = "TEST_PERSON_HISTORY_" + str(int(time.time()))
    cursor.execute("""
        INSERT INTO people.people_master (unique_id, full_name, created_at)
        VALUES (%s, 'Test Person', NOW())
        ON CONFLICT DO NOTHING
    """, (test_person_id,))
    conn.commit()

print(f"\n3. Assigning test person: {test_person_id}")

cursor.execute("""
    UPDATE people.company_slot
    SET person_unique_id = %s,
        is_filled = TRUE,
        filled_at = NOW(),
        source_system = 'history_test'
    WHERE company_slot_unique_id = %s
""", (test_person_id, slot_id))
conn.commit()

# Count history after
cursor.execute("SELECT COUNT(*) FROM people.slot_assignment_history")
count_after = cursor.fetchone()[0]
print(f"\n4. History records after: {count_after}")
print(f"   New records created: {count_after - count_before}")

# Show the history records
print("\n5. Recent history entries:")
cursor.execute("""
    SELECT history_id, event_type, slot_type, person_unique_id,
           displaced_by_person_id, source_system, event_ts
    FROM people.slot_assignment_history
    WHERE company_slot_unique_id = %s
    ORDER BY event_ts DESC
    LIMIT 5
""", (slot_id,))
for row in cursor.fetchall():
    print(f"   [{row[0]}] {row[1]}: {row[3]} (slot: {row[2]}, source: {row[5]})")

# Revert the test change
print("\n6. Reverting test change...")
cursor.execute("""
    UPDATE people.company_slot
    SET person_unique_id = %s,
        is_filled = %s,
        source_system = 'history_test_revert'
    WHERE company_slot_unique_id = %s
""", (current_person, is_filled, slot_id))
conn.commit()

# Count history after revert
cursor.execute("SELECT COUNT(*) FROM people.slot_assignment_history")
count_final = cursor.fetchone()[0]
print(f"\n7. History records after revert: {count_final}")
print(f"   Additional records from revert: {count_final - count_after}")

# Show all history for this slot
print("\n8. All history for test slot:")
cursor.execute("""
    SELECT history_id, event_type, person_unique_id, displaced_by_person_id,
           source_system, event_ts::text
    FROM people.slot_assignment_history
    WHERE company_slot_unique_id = %s
    ORDER BY event_ts
""", (slot_id,))
for row in cursor.fetchall():
    print(f"   [{row[0]}] {row[1]}: person={row[2]}, displaced_by={row[3]}, source={row[4]}, ts={row[5]}")

print("\n" + "="*60)
if count_after > count_before:
    print("SUCCESS: Trigger is working - history records are being created!")
else:
    print("WARNING: No new history records created. Check trigger.")
print("="*60)

cursor.close()
conn.close()
