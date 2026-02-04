"""Analyze the appointments file with Hunter enrichment."""
import pandas as pd

# Load the file
df = pd.read_csv(r'C:\Users\CUSTOM PC\Desktop\appts-already-had-2129971 full email addresses.csv')

print('=== FILE OVERVIEW ===')
print(f'Total rows: {len(df):,}')
print(f'Total columns: {len(df.columns)}')

print('\n=== ALL COLUMNS ===')
for i, col in enumerate(df.columns):
    print(f'{i+1}. {col}')

print('\n=== KEY COLUMN STATS ===')
key_cols = ['ProspectKeycodeId', 'Appt #', 'Appt Date', 'First', 'Last', 'Title', 'Company', 
            'City', 'State', 'Phone', 'Email', 'Domain', 'Email address', 'Domain name',
            'Organization', 'Headcount', 'Confidence score', 'First name', 'Last name',
            'Department', 'Job title', 'LinkedIn URL', 'Phone number', 'Industry', 'Verification status']
for col in key_cols:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f'{col}: {non_null:,} non-null')

print('\n=== UNIQUE COUNTS ===')
print(f"Unique ProspectKeycodeId: {df['ProspectKeycodeId'].nunique():,}")
print(f"Unique Appt #: {df['Appt #'].nunique():,}")
print(f"Unique Companies: {df['Company'].nunique():,}")
print(f"Unique Domains: {df['Domain'].nunique():,}")
print(f"Unique Email addresses (enriched): {df['Email address'].nunique():,}")

print('\n=== SAMPLE APPOINTMENTS ===')
appt_cols = ['Company', 'First', 'Last', 'Title', 'City', 'State', 'Email']
print(df[appt_cols].drop_duplicates(subset=['Company']).head(15).to_string())

print('\n=== SAMPLE ENRICHED CONTACTS ===')
enrich_cols = ['Company', 'Domain', 'First name', 'Last name', 'Job title', 'Email address', 'Confidence score']
print(df[enrich_cols].head(15).to_string())

print('\n=== VERIFICATION STATUS ===')
print(df['Verification status'].value_counts())

print('\n=== DEPARTMENTS ===')
print(df['Department'].value_counts().head(15))
