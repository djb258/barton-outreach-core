"""
Generate insights about phone data quality and distribution
"""

import os
import psycopg2
from collections import Counter

def get_neon_connection():
    """Get Neon PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def main():
    conn = get_neon_connection()

    with conn.cursor() as cur:
        # Check for duplicate phone numbers
        print("\n" + "=" * 100)
        print("DUPLICATE PHONE NUMBER ANALYSIS")
        print("=" * 100)

        cur.execute("""
            SELECT
                slot_phone,
                COUNT(*) as usage_count,
                STRING_AGG(DISTINCT slot_type, ', ') as slot_types
            FROM people.company_slot
            WHERE slot_phone IS NOT NULL AND slot_phone != ''
            GROUP BY slot_phone
            HAVING COUNT(*) > 1
            ORDER BY usage_count DESC
            LIMIT 20;
        """)

        duplicates = cur.fetchall()
        if duplicates:
            print(f"{'Phone Number':<20} {'Count':<8} {'Slot Types':<30}")
            print("-" * 100)
            for phone, count, slot_types in duplicates:
                print(f"{phone:<20} {count:<8} {slot_types:<30}")
            print(f"\nTotal duplicate phone numbers: {len(duplicates)}")
        else:
            print("No duplicate phone numbers found - all phones are unique!")

        # Area code distribution
        print("\n" + "=" * 100)
        print("TOP 20 AREA CODES (US/Canada)")
        print("=" * 100)

        cur.execute("""
            SELECT
                SUBSTRING(slot_phone FROM '\\+1 (\\d{3})') as area_code,
                COUNT(*) as count
            FROM people.company_slot
            WHERE slot_phone LIKE '+1%'
            GROUP BY area_code
            ORDER BY count DESC
            LIMIT 20;
        """)

        print(f"{'Area Code':<12} {'Count':<8}")
        print("-" * 100)
        for area_code, count in cur.fetchall():
            if area_code:
                print(f"{area_code:<12} {count:<8}")

        # Phone format analysis
        print("\n" + "=" * 100)
        print("PHONE FORMAT ANALYSIS")
        print("=" * 100)

        cur.execute("""
            SELECT
                CASE
                    WHEN slot_phone LIKE '+1%' THEN 'US/Canada (+1)'
                    WHEN slot_phone LIKE '+44%' THEN 'UK (+44)'
                    WHEN slot_phone LIKE '+%' THEN 'International (other)'
                    ELSE 'No country code'
                END as format_type,
                COUNT(*) as count
            FROM people.company_slot
            WHERE slot_phone IS NOT NULL AND slot_phone != ''
            GROUP BY format_type
            ORDER BY count DESC;
        """)

        print(f"{'Format Type':<25} {'Count':<8}")
        print("-" * 100)
        for format_type, count in cur.fetchall():
            print(f"{format_type:<25} {count:<8}")

        # Companies with multiple slots having phones
        print("\n" + "=" * 100)
        print("COMPANIES WITH MULTIPLE PHONE-ENABLED SLOTS")
        print("=" * 100)

        cur.execute("""
            SELECT
                outreach_id,
                COUNT(*) as slots_with_phones,
                STRING_AGG(slot_type, ', ') as slot_types
            FROM people.company_slot
            WHERE slot_phone IS NOT NULL AND slot_phone != ''
            GROUP BY outreach_id
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 10;
        """)

        companies_with_multiple = cur.fetchall()
        if companies_with_multiple:
            print(f"{'Outreach ID':<38} {'Slots':<8} {'Slot Types':<30}")
            print("-" * 100)
            for outreach_id, count, slot_types in companies_with_multiple:
                print(f"{outreach_id:<38} {count:<8} {slot_types:<30}")
            print(f"\nTotal companies with multiple phone-enabled slots: {len(companies_with_multiple)}")
        else:
            print("No companies have multiple slots with phone numbers")

    conn.close()

if __name__ == '__main__':
    main()
