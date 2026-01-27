"""
Export outreach records that do NOT have an EIN attached.
These are companies in outreach.outreach that are NOT in outreach.dol
"""
import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 70)
    print("EXPORT OUTREACH RECORDS WITHOUT EIN")
    print("=" * 70)
    
    # First, get counts
    print("\n[1] Checking counts...")
    
    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    total_outreach = cur.fetchone()['count']
    
    cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol")
    with_ein = cur.fetchone()['count']
    
    without_ein = total_outreach - with_ein
    
    print(f"    Total outreach records: {total_outreach:,}")
    print(f"    With EIN (in outreach.dol): {with_ein:,}")
    print(f"    WITHOUT EIN: {without_ein:,}")
    
    # Query for records without EIN - simple query
    print("\n[2] Querying outreach records without EIN...")
    
    cur.execute("""
        SELECT 
            o.outreach_id,
            o.domain,
            o.sovereign_id
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        WHERE d.outreach_id IS NULL
        ORDER BY o.outreach_id
    """)
    
    rows = cur.fetchall()
    print(f"    Found {len(rows):,} records without EIN")
    
    # Write to CSV
    print("\n[3] Writing to CSV...")
    
    output_file = 'scripts/outreach_without_ein.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['outreach_id', 'domain', 'sovereign_id'])
        
        for row in rows:
            writer.writerow([
                row['outreach_id'],
                row['domain'],
                row['sovereign_id']
            ])
    
    print(f"    Saved to {output_file}")
    
    # Show sample
    print("\n[4] Sample records:")
    for row in rows[:5]:
        print(f"    {row['outreach_id']} | {row['domain'] or 'N/A'}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"COMPLETE - {len(rows):,} records exported to {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
