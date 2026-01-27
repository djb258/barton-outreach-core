"""
Load DOL URL discovery results into dol.ein_urls table.
Source: domain_results_VALID.csv (119,469 validated EIN→URL mappings)
"""
import os
import csv
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ.get("DATABASE_URL")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=" * 70)
    print("LOAD DOL URL DISCOVERY INTO dol.ein_urls")
    print("=" * 70)
    
    # Step 1: Create the table
    print("\n[1] Creating dol.ein_urls table...")
    cur.execute("""
        DROP TABLE IF EXISTS dol.ein_urls;
        
        CREATE TABLE dol.ein_urls (
            ein VARCHAR(9) PRIMARY KEY,
            company_name TEXT NOT NULL,
            city TEXT,
            state VARCHAR(2),
            domain TEXT,
            url TEXT,
            discovered_at TIMESTAMP DEFAULT NOW(),
            discovery_method TEXT DEFAULT 'domain_construction'
        );
        
        COMMENT ON TABLE dol.ein_urls IS 'DOL EIN to URL mappings discovered via domain construction (FREE Tier 0)';
        COMMENT ON COLUMN dol.ein_urls.ein IS 'EIN from DOL Form 5500 filing';
        COMMENT ON COLUMN dol.ein_urls.company_name IS 'Sponsor name from DOL filing';
        COMMENT ON COLUMN dol.ein_urls.domain IS 'Discovered domain (e.g., company.com)';
        COMMENT ON COLUMN dol.ein_urls.url IS 'Full URL with https://';
        COMMENT ON COLUMN dol.ein_urls.discovery_method IS 'How URL was found: domain_construction, clay, manual';
    """)
    conn.commit()
    print("    Table created!")
    
    # Step 2: Load the CSV data
    print("\n[2] Loading domain_results_VALID.csv...")
    
    rows = []
    with open('scripts/domain_results_VALID.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('domain'):
                rows.append((
                    row['ein'],
                    row['company_name'],
                    row.get('city', ''),
                    row.get('state', ''),
                    row['domain'],
                    row.get('url', '')
                ))
    
    print(f"    Loaded {len(rows):,} valid records from CSV")
    
    # Step 3: Insert in batches
    print("\n[3] Inserting into dol.ein_urls...")
    
    batch_size = 5000
    inserted = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        execute_values(cur, """
            INSERT INTO dol.ein_urls (ein, company_name, city, state, domain, url)
            VALUES %s
            ON CONFLICT (ein) DO UPDATE SET
                domain = EXCLUDED.domain,
                url = EXCLUDED.url,
                discovered_at = NOW()
        """, batch)
        conn.commit()
        inserted += len(batch)
        print(f"    Inserted {inserted:,} / {len(rows):,}")
    
    # Step 4: Create indexes
    print("\n[4] Creating indexes...")
    cur.execute("""
        CREATE INDEX idx_ein_urls_domain ON dol.ein_urls(domain);
        CREATE INDEX idx_ein_urls_state ON dol.ein_urls(state);
    """)
    conn.commit()
    print("    Indexes created!")
    
    # Step 5: Verify
    print("\n[5] Verification...")
    cur.execute("SELECT COUNT(*) FROM dol.ein_urls")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT state, COUNT(*) FROM dol.ein_urls GROUP BY state ORDER BY COUNT(*) DESC LIMIT 10")
    by_state = cur.fetchall()
    
    print(f"\n    Total records: {total:,}")
    print("\n    By state:")
    for state, count in by_state:
        print(f"        {state}: {count:,}")
    
    # Sample data
    print("\n    Sample records:")
    cur.execute("SELECT ein, company_name, domain, url FROM dol.ein_urls LIMIT 5")
    for row in cur.fetchall():
        print(f"        {row[0]} | {row[1][:30]:30} | {row[2]}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("COMPLETE - dol.ein_urls loaded with {:,} records".format(total))
    print("=" * 70)

if __name__ == "__main__":
    main()
