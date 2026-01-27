#!/usr/bin/env python3
"""Check EIN column in form_5500_sf"""
import psycopg2
import os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_schema='dol' AND table_name='form_5500_sf' AND column_name LIKE '%ein%'""")
print('EIN columns in form_5500_sf:')
for row in cur.fetchall():
    print(f'  {row[0]}')

# Also check state column
cur.execute("""SELECT column_name FROM information_schema.columns WHERE table_schema='dol' AND table_name='form_5500_sf' AND column_name LIKE '%state%'""")
print('\nState columns in form_5500_sf:')
for row in cur.fetchall():
    print(f'  {row[0]}')
    
cur.close()
conn.close()
