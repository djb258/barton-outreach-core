"""Search DOL tables for Matt/Matthew Fuqua and export to CSV"""
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])

print("=" * 60)
print("SEARCHING DOL TABLES FOR 'FUQUA'")
print("=" * 60)

# Search form_5500
query_5500 = """
    SELECT sponsor_dfe_ein, sponsor_dfe_name, plan_name, admin_name, preparer_name, preparer_firm_name,
           spons_dfe_mail_us_city, spons_dfe_mail_us_state, ack_id
    FROM dol.form_5500
    WHERE admin_name ILIKE '%fuqua%' 
       OR preparer_name ILIKE '%fuqua%' 
       OR preparer_firm_name ILIKE '%fuqua%'
       OR sponsor_dfe_name ILIKE '%fuqua%'
"""
df_5500 = pd.read_sql(query_5500, conn)
print(f"\n=== FORM 5500 MATCHES: {len(df_5500)} ===")
if len(df_5500) > 0:
    for i, row in df_5500.iterrows():
        print(f"\nEIN: {row['sponsor_dfe_ein']}")
        print(f"  Company: {row['sponsor_dfe_name']}")
        print(f"  Plan: {row['plan_name']}")
        print(f"  Admin: {row['admin_name']}")
        print(f"  Preparer: {row['preparer_name']}")
        print(f"  Preparer Firm: {row['preparer_firm_name']}")
        print(f"  Location: {row['spons_dfe_mail_us_city']}, {row['spons_dfe_mail_us_state']}")

# Search form_5500_sf
query_sf = """
    SELECT sf_spons_ein, sf_sponsor_name, sf_plan_name, sf_admin_name, sf_preparer_name, sf_preparer_firm_name,
           sf_spons_us_city, sf_spons_us_state, ack_id
    FROM dol.form_5500_sf
    WHERE sf_admin_name ILIKE '%fuqua%' 
       OR sf_preparer_name ILIKE '%fuqua%' 
       OR sf_preparer_firm_name ILIKE '%fuqua%'
       OR sf_sponsor_name ILIKE '%fuqua%'
"""
df_sf = pd.read_sql(query_sf, conn)
print(f"\n\n=== FORM 5500-SF MATCHES: {len(df_sf)} ===")
if len(df_sf) > 0:
    for i, row in df_sf.iterrows():
        print(f"\nEIN: {row['sf_spons_ein']}")
        print(f"  Company: {row['sf_sponsor_name']}")
        print(f"  Plan: {row['sf_plan_name']}")
        print(f"  Admin: {row['sf_admin_name']}")
        print(f"  Preparer: {row['sf_preparer_name']}")
        print(f"  Preparer Firm: {row['sf_preparer_firm_name']}")
        print(f"  Location: {row['sf_spons_us_city']}, {row['sf_spons_us_state']}")

# Search schedule_a
query_sched = """
    SELECT sch_a_ein, sponsor_name, ins_carrier_name, sponsor_state
    FROM dol.schedule_a
    WHERE sponsor_name ILIKE '%fuqua%' 
       OR ins_carrier_name ILIKE '%fuqua%'
"""
df_sched = pd.read_sql(query_sched, conn)
print(f"\n\n=== SCHEDULE A MATCHES: {len(df_sched)} ===")

conn.close()

# Export to CSV
desktop = r"C:\Users\CUSTOM PC\Desktop"

# Normalize column names for combined export
if len(df_5500) > 0:
    df_5500_norm = df_5500.rename(columns={
        'sponsor_dfe_ein': 'ein',
        'sponsor_dfe_name': 'company_name',
        'plan_name': 'plan_name',
        'admin_name': 'admin_name',
        'preparer_name': 'preparer_name',
        'preparer_firm_name': 'preparer_firm_name',
        'spons_dfe_mail_us_city': 'city',
        'spons_dfe_mail_us_state': 'state'
    })
    df_5500_norm['source'] = 'form_5500'
else:
    df_5500_norm = pd.DataFrame()

if len(df_sf) > 0:
    df_sf_norm = df_sf.rename(columns={
        'sf_spons_ein': 'ein',
        'sf_sponsor_name': 'company_name',
        'sf_plan_name': 'plan_name',
        'sf_admin_name': 'admin_name',
        'sf_preparer_name': 'preparer_name',
        'sf_preparer_firm_name': 'preparer_firm_name',
        'sf_spons_us_city': 'city',
        'sf_spons_us_state': 'state'
    })
    df_sf_norm['source'] = 'form_5500_sf'
else:
    df_sf_norm = pd.DataFrame()

# Combine all
combined = pd.concat([df_5500_norm, df_sf_norm], ignore_index=True)
if len(combined) > 0:
    # Select columns for export
    export_cols = ['ein', 'company_name', 'plan_name', 'admin_name', 'preparer_name', 'preparer_firm_name', 'city', 'state', 'source']
    combined = combined[export_cols]
    
    csv_path = os.path.join(desktop, "fuqua_advisor_matches.csv")
    combined.to_csv(csv_path, index=False)
    print(f"\n\n{'='*60}")
    print(f"EXPORTED: {csv_path}")
    print(f"Total records: {len(combined)}")
    print(f"  - From form_5500: {len(df_5500)}")
    print(f"  - From form_5500_sf: {len(df_sf)}")
    print("="*60)
