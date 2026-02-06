"""Database breakdown report - DOL, Companies, and States."""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("=" * 70)
print("DATABASE BREAKDOWN REPORT")
print("=" * 70)

# ============================================================
# DOL DATA
# ============================================================
print("\n" + "=" * 70)
print("DOL DATA")
print("=" * 70)

# Form 5500
cur.execute("SELECT COUNT(*) FROM dol.form_5500")
form_5500_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT sponsor_dfe_ein) FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL")
form_5500_eins = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT company_unique_id) FROM dol.form_5500 WHERE company_unique_id IS NOT NULL")
form_5500_companies = cur.fetchone()[0]
print(f"\nForm 5500:")
print(f"  Total filings: {form_5500_count:,}")
print(f"  Unique EINs: {form_5500_eins:,}")
print(f"  Unique company_unique_id: {form_5500_companies:,}")

# Form 5500-SF
cur.execute("SELECT COUNT(*) FROM dol.form_5500_sf")
form_5500_sf_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT company_unique_id) FROM dol.form_5500_sf WHERE company_unique_id IS NOT NULL")
form_5500_sf_companies = cur.fetchone()[0]
print(f"\nForm 5500-SF:")
print(f"  Total filings: {form_5500_sf_count:,}")
print(f"  Unique companies: {form_5500_sf_companies:,}")

# Schedule A
cur.execute("SELECT COUNT(*) FROM dol.schedule_a")
schedule_a_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT sch_a_ein) FROM dol.schedule_a WHERE sch_a_ein IS NOT NULL")
schedule_a_eins = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT company_unique_id) FROM dol.schedule_a WHERE company_unique_id IS NOT NULL")
schedule_a_companies = cur.fetchone()[0]
print(f"\nSchedule A:")
print(f"  Total records: {schedule_a_count:,}")
print(f"  Unique EINs: {schedule_a_eins:,}")
print(f"  Unique companies: {schedule_a_companies:,}")

# ICP Filtered
cur.execute("SELECT COUNT(*) FROM dol.form_5500_icp_filtered")
icp_count = cur.fetchone()[0]
print(f"\nForm 5500 ICP Filtered:")
print(f"  Total records: {icp_count:,}")

# ============================================================
# OUTREACH DATA
# ============================================================
print("\n" + "=" * 70)
print("OUTREACH DATA")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM outreach.outreach")
total_outreach = cur.fetchone()[0]
cur.execute("SELECT COUNT(DISTINCT domain) FROM outreach.outreach WHERE domain IS NOT NULL")
unique_domains = cur.fetchone()[0]
print(f"\nTotal outreach records: {total_outreach:,}")
print(f"Unique domains: {unique_domains:,}")

# By has_appointment flag
cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE has_appointment = TRUE")
warm = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE has_appointment = FALSE OR has_appointment IS NULL")
cold = cur.fetchone()[0]
print(f"\nBy appointment status:")
print(f"  Warm leads (has_appointment=TRUE): {warm:,}")
print(f"  Cold leads (has_appointment=FALSE): {cold:,}")

# ============================================================
# COMPANY DATA BY SCHEMA/HUB
# ============================================================
print("\n" + "=" * 70)
print("COMPANIES BY SCHEMA/HUB")
print("=" * 70)

# Check what schemas/tables have company data
schemas_to_check = [
    ('company', 'companies'),
    ('company', 'company'),
    ('enrichment', 'hunter_contact'),
    ('enrichment', 'clay_enrichment'),
    ('people', 'contacts'),
]

for schema, table in schemas_to_check:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
        count = cur.fetchone()[0]
        print(f"{schema}.{table}: {count:,}")
    except Exception as e:
        pass

# Check all tables in key schemas
print("\n--- All tables by schema ---")
for schema in ['company', 'enrichment', 'outreach', 'people', 'dol']:
    try:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s
            ORDER BY table_name
        """, (schema,))
        tables = [row[0] for row in cur.fetchall()]
        if tables:
            print(f"\n{schema} schema:")
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count:,}")
                except Exception as e:
                    conn.rollback()
                    print(f"  {table}: (error)")
    except Exception as e:
        conn.rollback()
        print(f"\n{schema} schema: (error accessing)")

# ============================================================
# STATE BREAKDOWN - DOL
# ============================================================
print("\n" + "=" * 70)
print("DOL FILINGS BY STATE (Form 5500)")
print("=" * 70)

cur.execute("""
    SELECT spons_dfe_mail_us_state, COUNT(*) as cnt
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IS NOT NULL 
    AND spons_dfe_mail_us_state != ''
    GROUP BY spons_dfe_mail_us_state
    ORDER BY cnt DESC
""")
print("\nState | Filings")
print("-" * 30)
for row in cur.fetchall():
    print(f"{row[0]:5} | {row[1]:,}")

# ============================================================
# STATE BREAKDOWN - OUTREACH
# ============================================================
print("\n" + "=" * 70)
print("OUTREACH BY STATE")
print("=" * 70)

# Check if state column exists
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'outreach'
    AND column_name ILIKE '%state%'
""")
state_cols = [row[0] for row in cur.fetchall()]
print(f"State columns found: {state_cols}")

if state_cols:
    state_col = state_cols[0]
    cur.execute(f"""
        SELECT {state_col}, COUNT(*) as cnt
        FROM outreach.outreach
        WHERE {state_col} IS NOT NULL 
        AND {state_col} != ''
        GROUP BY {state_col}
        ORDER BY cnt DESC
        LIMIT 30
    """)
    print(f"\nState | Records")
    print("-" * 30)
    for row in cur.fetchall():
        print(f"{row[0]:5} | {row[1]:,}")

# ============================================================
# APPOINTMENTS
# ============================================================
print("\n" + "=" * 70)
print("APPOINTMENTS")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM outreach.appointments")
appts = cur.fetchone()[0]
print(f"Total appointments: {appts:,}")

cur.execute("""
    SELECT state, COUNT(*) as cnt
    FROM outreach.appointments
    WHERE state IS NOT NULL
    GROUP BY state
    ORDER BY cnt DESC
""")
print("\nBy state:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,}")

conn.close()
print("\n" + "=" * 70)
print("REPORT COMPLETE")
print("=" * 70)
