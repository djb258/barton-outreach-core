"""
Verify phone data in people.company_slot
"""

import os
import psycopg2

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
        # Check phone population by slot type
        cur.execute("""
            SELECT
                slot_type,
                COUNT(*) FILTER (WHERE slot_phone IS NOT NULL AND slot_phone != '') as with_phone,
                COUNT(*) FILTER (WHERE slot_phone_source = 'hunter') as from_hunter,
                COUNT(*) as total,
                ROUND(100.0 * COUNT(*) FILTER (WHERE slot_phone IS NOT NULL AND slot_phone != '') / COUNT(*), 2) as pct_with_phone
            FROM people.company_slot
            WHERE slot_type IN ('CEO', 'CFO', 'HR')
            GROUP BY slot_type
            ORDER BY slot_type;
        """)

        print("\n" + "=" * 100)
        print("PHONE NUMBER POPULATION BY SLOT TYPE")
        print("=" * 100)
        print(f"{'Slot Type':<12} {'With Phone':<12} {'From Hunter':<15} {'Total':<12} {'% Coverage':<12}")
        print("-" * 100)

        for row in cur.fetchall():
            slot_type, with_phone, from_hunter, total, pct = row
            print(f"{slot_type:<12} {with_phone:<12} {from_hunter:<15} {total:<12} {pct:<12.2f}%")

        # Sample some phone records
        cur.execute("""
            SELECT outreach_id, slot_type, slot_phone, slot_phone_source, slot_phone_updated_at
            FROM people.company_slot
            WHERE slot_phone IS NOT NULL AND slot_phone != ''
            ORDER BY slot_phone_updated_at DESC NULLS LAST
            LIMIT 10;
        """)

        print("\n" + "=" * 100)
        print("SAMPLE PHONE RECORDS (Most Recently Updated)")
        print("=" * 100)
        for row in cur.fetchall():
            outreach_id, slot_type, phone, source, updated_at = row
            print(f"{slot_type:<6} {phone:<20} {source or 'N/A':<10} {str(updated_at)[:19] if updated_at else 'N/A':<20} {outreach_id[:8]}...")

    conn.close()

if __name__ == '__main__':
    main()
