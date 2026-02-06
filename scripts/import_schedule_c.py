"""
Import DOL Schedule C (Service Provider) Data into Neon

Schedule C contains:
- Service provider names (advisors, TPAs, record keepers, brokers)
- Compensation amounts
- Service codes

Download 2023 data from:
https://askebsa.dol.gov/FOIA%20Files/2023/Latest/F_SCH_C_PART1_2023_Latest.zip

Steps:
1. Download and unzip to get the CSV
2. Run this script pointing to the CSV file
"""
import psycopg2
import pandas as pd
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Schedule C Part 1 key columns (service provider info)
SCHEDULE_C_COLUMNS = {
    'ACK_ID': 'ack_id',
    'FORM_PLAN_YEAR_BEGIN_DATE': 'plan_year_begin',
    'FORM_TAX_PRD': 'tax_period',
    'SPONS_DFE_EIN': 'sponsor_ein',
    'SPONS_DFE_PN': 'plan_number',
    'SCH_C_PROVIDER_NAME': 'provider_name',           # <-- ADVISOR NAME
    'SCH_C_PROVIDER_EIN': 'provider_ein',
    'SCH_C_PROVIDER_PN': 'provider_pn',
    'SCH_C_DIRECT_COMP_AMT': 'direct_comp_amt',        # Direct compensation
    'SCH_C_INDIRECT_COMP_AMT': 'indirect_comp_amt',    # Indirect compensation
    'SCH_C_SVC_CODE1': 'service_code_1',               # Service type codes
    'SCH_C_SVC_CODE2': 'service_code_2',
    'SCH_C_SVC_CODE3': 'service_code_3',
    'SCH_C_SVC_CODE4': 'service_code_4',
    'SCH_C_RELATIONSHIP_CODE': 'relationship_code',
    'SCH_C_TERM_IND': 'termination_ind'
}

# Service codes reference
SERVICE_CODES = {
    '01': 'Accounting',
    '02': 'Actuarial',
    '03': 'Contract Administrator',
    '04': 'Consulting',
    '05': 'Custodial / Trust',
    '06': 'Legal',
    '07': 'Investment Advisory',      # <-- ADVISORS
    '08': 'Investment Management',    # <-- ADVISORS
    '09': 'Insurance Agents/Brokers', # <-- BROKERS
    '10': 'Named Fiduciary',
    '11': 'Plan Administrator',
    '12': 'Recordkeeping',
    '13': 'Securities Brokerage',     # <-- BROKERS
    '14': 'Trustee (individual)',
    '15': 'Trustee (corporate/bank)',
    '16': 'Valuation',
    '17': 'Other'
}


def create_schedule_c_table(conn):
    """Create the schedule_c table in dol schema"""
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dol.schedule_c (
            schedule_c_id SERIAL PRIMARY KEY,
            ack_id VARCHAR(50),
            plan_year_begin DATE,
            tax_period VARCHAR(10),
            sponsor_ein VARCHAR(20),
            plan_number VARCHAR(10),
            provider_name VARCHAR(255),
            provider_ein VARCHAR(20),
            provider_pn VARCHAR(10),
            direct_comp_amt NUMERIC(15,2),
            indirect_comp_amt NUMERIC(15,2),
            service_code_1 VARCHAR(5),
            service_code_2 VARCHAR(5),
            service_code_3 VARCHAR(5),
            service_code_4 VARCHAR(5),
            relationship_code VARCHAR(5),
            termination_ind VARCHAR(5),
            form_year INTEGER DEFAULT 2023,
            created_at TIMESTAMP DEFAULT NOW(),
            
            -- Indexes for common lookups
            CONSTRAINT schedule_c_ack_provider UNIQUE (ack_id, provider_name, provider_ein)
        );
        
        CREATE INDEX IF NOT EXISTS idx_schedule_c_ein ON dol.schedule_c(sponsor_ein);
        CREATE INDEX IF NOT EXISTS idx_schedule_c_provider_name ON dol.schedule_c(provider_name);
        CREATE INDEX IF NOT EXISTS idx_schedule_c_service_code ON dol.schedule_c(service_code_1);
    """)
    
    conn.commit()
    print("✓ Created dol.schedule_c table")


def import_schedule_c(csv_path, conn):
    """Import Schedule C CSV into database"""
    
    print(f"Reading {csv_path}...")
    
    # Read CSV - DOL files are usually pipe-delimited or comma
    try:
        df = pd.read_csv(csv_path, low_memory=False, encoding='latin-1')
    except:
        df = pd.read_csv(csv_path, sep='|', low_memory=False, encoding='latin-1')
    
    print(f"Loaded {len(df):,} rows")
    print(f"Columns: {list(df.columns)[:10]}...")
    
    # Rename columns to our schema
    col_mapping = {}
    for orig, new in SCHEDULE_C_COLUMNS.items():
        if orig in df.columns:
            col_mapping[orig] = new
        elif orig.lower() in [c.lower() for c in df.columns]:
            # Case-insensitive match
            actual = [c for c in df.columns if c.lower() == orig.lower()][0]
            col_mapping[actual] = new
    
    df = df.rename(columns=col_mapping)
    
    # Keep only mapped columns that exist
    keep_cols = [c for c in SCHEDULE_C_COLUMNS.values() if c in df.columns]
    df = df[keep_cols]
    
    print(f"Mapped columns: {keep_cols}")
    
    # Clean up data
    if 'direct_comp_amt' in df.columns:
        df['direct_comp_amt'] = pd.to_numeric(df['direct_comp_amt'], errors='coerce')
    if 'indirect_comp_amt' in df.columns:
        df['indirect_comp_amt'] = pd.to_numeric(df['indirect_comp_amt'], errors='coerce')
    
    df['form_year'] = 2023
    
    # Insert in batches
    cur = conn.cursor()
    batch_size = 5000
    total = len(df)
    
    for i in range(0, total, batch_size):
        batch = df.iloc[i:i+batch_size]
        
        cols = list(batch.columns)
        placeholders = ','.join(['%s'] * len(cols))
        col_names = ','.join(cols)
        
        values = [tuple(row) for row in batch.itertuples(index=False, name=None)]
        
        # Use ON CONFLICT to handle duplicates
        insert_sql = f"""
            INSERT INTO dol.schedule_c ({col_names})
            VALUES ({placeholders})
            ON CONFLICT (ack_id, provider_name, provider_ein) DO NOTHING
        """
        
        try:
            cur.executemany(insert_sql, values)
            conn.commit()
        except Exception as e:
            print(f"Error at batch {i}: {e}")
            conn.rollback()
            # Try without conflict handling
            insert_sql = f"INSERT INTO dol.schedule_c ({col_names}) VALUES ({placeholders})"
            cur.executemany(insert_sql, values)
            conn.commit()
        
        print(f"  Imported {min(i+batch_size, total):,} / {total:,}")
    
    print(f"✓ Imported {total:,} Schedule C records")
    
    # Show sample
    cur.execute("""
        SELECT provider_name, service_code_1, COUNT(*) as cnt,
               SUM(direct_comp_amt) as total_comp
        FROM dol.schedule_c
        GROUP BY provider_name, service_code_1
        ORDER BY cnt DESC
        LIMIT 10
    """)
    
    print("\nTop providers by count:")
    for row in cur.fetchall():
        svc = SERVICE_CODES.get(row[1], row[1])
        print(f"  {row[0]}: {row[2]:,} plans ({svc})")


def search_advisor(name_pattern, conn):
    """Search for an advisor by name"""
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT sc.provider_name, sc.service_code_1, 
               f.sponsor_dfe_name, f.spons_dfe_mail_us_state, f.sponsor_dfe_ein
        FROM dol.schedule_c sc
        JOIN dol.form_5500 f ON sc.sponsor_ein = f.sponsor_dfe_ein
        WHERE sc.provider_name ILIKE %s
        ORDER BY sc.provider_name
        LIMIT 100
    """, (f'%{name_pattern}%',))
    
    results = cur.fetchall()
    print(f"\nFound {len(results)} matches for '{name_pattern}':")
    for r in results:
        svc = SERVICE_CODES.get(r[1], r[1])
        print(f"  {r[0]} ({svc}) → {r[2]} ({r[3]})")
    
    return results


if __name__ == '__main__':
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    
    if len(sys.argv) < 2:
        print("""
Usage: python import_schedule_c.py <csv_file>
       python import_schedule_c.py --search "Matt Fuqua"

Download 2023 Schedule C from:
  https://askebsa.dol.gov/FOIA%20Files/2023/Latest/F_SCH_C_PART1_2023_Latest.zip
        """)
        sys.exit(1)
    
    if sys.argv[1] == '--search':
        search_advisor(sys.argv[2], conn)
    elif sys.argv[1] == '--create':
        create_schedule_c_table(conn)
    else:
        csv_path = sys.argv[1]
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            sys.exit(1)
        
        create_schedule_c_table(conn)
        import_schedule_c(csv_path, conn)
    
    conn.close()
