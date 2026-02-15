#!/usr/bin/env python3
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('VERIFICATION SOURCE BREAKDOWN')
print('='*60)

# people_master verification sources
cur.execute('''
SELECT email_verification_source, COUNT(*) 
FROM people.people_master 
WHERE email_verified = true
GROUP BY email_verification_source
ORDER BY COUNT(*) DESC
''')
print('people_master verified emails by source:')
for r in cur.fetchall():
    src = r[0] if r[0] else 'NULL'
    print(f'  {src}: {r[1]:,}')

print()

# outreach.people verification sources  
cur.execute('''
SELECT email_verification_source, COUNT(*) 
FROM outreach.people 
WHERE email_verified = true
GROUP BY email_verification_source
ORDER BY COUNT(*) DESC
''')
print('outreach.people verified emails by source:')
for r in cur.fetchall():
    src = r[0] if r[0] else 'NULL'
    print(f'  {src}: {r[1]:,}')

conn.close()
