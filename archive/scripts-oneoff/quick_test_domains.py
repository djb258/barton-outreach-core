#!/usr/bin/env python3
"""Quick test of domain validation."""
import os
import psycopg2
import httpx
import time
import re

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
    SELECT sponsor_dfe_ein, sponsor_dfe_name
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state = 'NC'
    AND sponsor_dfe_ein IS NOT NULL
    LIMIT 10
""")

records = cur.fetchall()
print(f'Testing {len(records)} DOL records...')
print()

valid_count = 0
for ein, name in records:
    print(f'{name[:50]}')
    clean = name.lower()
    for s in [' inc', ' llc', ' corp', ' co', ' ltd']:
        clean = clean.replace(s, '')
    slug = re.sub(r'[^a-z0-9]', '', clean.strip())
    url = f'https://{slug}.com'
    print(f'  Trying: {url}')
    
    try:
        with httpx.Client(timeout=3.0) as c:
            r = c.head(url, follow_redirects=True)
            status = r.status_code
            if status < 400:
                print(f'  ✓ VALID (status={status})')
                valid_count += 1
            else:
                print(f'  ✗ Invalid (status={status})')
    except httpx.ConnectError:
        print(f'  ✗ ConnectError - domain does not exist')
    except httpx.TimeoutException:
        print(f'  ✗ Timeout')
    except Exception as e:
        print(f'  ✗ Error: {type(e).__name__}')
    time.sleep(0.3)
    print()

cur.close()
conn.close()
print(f'RESULT: {valid_count}/{len(records)} domains validated')
