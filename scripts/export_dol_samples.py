"""Export sample CSVs from DOL 5500 tables."""
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])

# Check what DOL tables exist
cur = conn.cursor()
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name ILIKE '%5500%' OR table_name ILIKE '%schedule%'
    ORDER BY table_schema, table_name
""")
print('DOL-related tables found:')
tables = []
for row in cur.fetchall():
    print(f'  {row[0]}.{row[1]}')
    tables.append((row[0], row[1]))

# Export samples
output_dir = r'C:\Users\CUSTOM PC\Desktop'

for schema, table in tables:
    full_name = f'{schema}.{table}'
    print(f'\nExporting {full_name}...')
    
    try:
        df = pd.read_sql(f'SELECT * FROM {full_name} LIMIT 10', conn)
        filename = f'{output_dir}\\sample_{table}.csv'
        df.to_csv(filename, index=False)
        print(f'  ✓ Saved {filename} ({len(df.columns)} columns)')
    except Exception as e:
        print(f'  ✗ Error: {e}')

conn.close()
print('\nDone!')
