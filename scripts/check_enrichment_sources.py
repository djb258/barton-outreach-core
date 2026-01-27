#!/usr/bin/env python3
"""Check all potential sources of enrichment URL data."""

import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# List all schemas
print('=== All Schemas ===')
cur.execute("""
    SELECT schema_name FROM information_schema.schemata 
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    ORDER BY schema_name
""")
for row in cur.fetchall():
    print(f'  {row[0]}')

# Find tables with url, domain, enrichment in name
print('\n=== Tables containing url, domain, enrichment, clay, blog ===')
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_type = 'BASE TABLE'
    AND (
        table_name ILIKE '%url%' OR 
        table_name ILIKE '%domain%' OR 
        table_name ILIKE '%enrichment%' OR
        table_name ILIKE '%clay%' OR
        table_name ILIKE '%blog%' OR
        table_name ILIKE '%staging%'
    )
    ORDER BY table_schema, table_name
""")
for row in cur.fetchall():
    print(f'  {row[0]}.{row[1]}')

# Check dol_filings for URL columns
print('\n=== dol_filings schema tables ===')
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'dol_filings' AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
for row in cur.fetchall():
    print(f'  {row[0]}')

# Check dol_filings columns with url/domain
print('\n=== dol_filings columns with url/domain ===')
cur.execute("""
    SELECT table_name, column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol_filings'
    AND (column_name ILIKE '%url%' OR column_name ILIKE '%domain%' OR column_name ILIKE '%website%')
    ORDER BY table_name, column_name
""")
for row in cur.fetchall():
    print(f'  {row[0]}.{row[1]}')

# Check company.company_source_urls
print('\n=== company.company_source_urls columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'company_source_urls'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check company.company_source_urls count
print('\n=== company.company_source_urls count ===')
cur.execute("SELECT count(*) FROM company.company_source_urls")
print(f'  Total: {cur.fetchone()[0]}')

# Sample from company.company_source_urls
print('\n=== Sample company.company_source_urls ===')
cur.execute("SELECT * FROM company.company_source_urls LIMIT 5")
cols = [d[0] for d in cur.description]
print(f'  Columns: {cols}')
for row in cur.fetchall():
    print(f'  {row}')

# Check company.contact_enrichment
print('\n=== company.contact_enrichment columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'contact_enrichment'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check company.contact_enrichment count
print('\n=== company.contact_enrichment count ===')
cur.execute("SELECT count(*) FROM company.contact_enrichment")
print(f'  Total: {cur.fetchone()[0]}')

# Check company.url_discovery_failures
print('\n=== company.url_discovery_failures columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'url_discovery_failures'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check cl.company_domains
print('\n=== cl.company_domains columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_domains'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check cl.company_domains count
print('\n=== cl.company_domains count ===')
cur.execute("SELECT count(*) FROM cl.company_domains")
print(f'  Total: {cur.fetchone()[0]}')

# Sample from cl.company_domains
print('\n=== Sample cl.company_domains ===')
cur.execute("SELECT * FROM cl.company_domains LIMIT 5")
cols = [d[0] for d in cur.description]
print(f'  Columns: {cols}')
for row in cur.fetchall():
    print(f'  {row}')

# List all views that might have URL data
print('\n=== Views in all schemas ===')
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.views 
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND (
        table_name ILIKE '%url%' OR 
        table_name ILIKE '%domain%' OR 
        table_name ILIKE '%enrichment%' OR
        table_name ILIKE '%blog%' OR
        table_name ILIKE '%diagnostic%'
    )
    ORDER BY table_schema, table_name
""")
for row in cur.fetchall():
    print(f'  {row[0]}.{row[1]}')

cur.close()
conn.close()
