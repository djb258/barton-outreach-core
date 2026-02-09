#!/usr/bin/env python3
"""Check current email verification status."""

import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    database=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

# Check verification status for filled slots
cur.execute('''
    SELECT
        cs.slot_type,
        COUNT(*) as total_filled,
        COUNT(pm.email) as with_email,
        COUNT(CASE WHEN pm.email_verified_at IS NOT NULL THEN 1 END) as checked,
        COUNT(CASE WHEN pm.email_verified = TRUE THEN 1 END) as verified_valid,
        COUNT(CASE WHEN pm.email_verified = FALSE AND pm.email_verified_at IS NOT NULL THEN 1 END) as verified_invalid,
        COUNT(CASE WHEN pm.outreach_ready = TRUE THEN 1 END) as message_ready
    FROM people.company_slot cs
    LEFT JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
    WHERE cs.is_filled = TRUE
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
''')

print('=' * 90)
print('SLOT VERIFICATION STATUS (Filled Slots Only)')
print('=' * 90)
print('Slot     Filled  w/Email  Checked    Valid  Invalid   MsgReady')
print('-' * 90)

totals = [0, 0, 0, 0, 0, 0]
for row in cur.fetchall():
    slot_type, total, with_email, checked, valid, invalid, ready = row
    print(f'{slot_type:<6} {total:>8,} {with_email or 0:>8,} {checked or 0:>8,} {valid or 0:>8,} {invalid or 0:>8,} {ready or 0:>10,}')
    totals[0] += total or 0
    totals[1] += with_email or 0
    totals[2] += checked or 0
    totals[3] += valid or 0
    totals[4] += invalid or 0
    totals[5] += ready or 0

print('-' * 90)
print(f'TOTAL  {totals[0]:>8,} {totals[1]:>8,} {totals[2]:>8,} {totals[3]:>8,} {totals[4]:>8,} {totals[5]:>10,}')
print()

# Remaining unique emails
cur.execute('''
    SELECT COUNT(DISTINCT LOWER(pm.email))
    FROM people.company_slot cs
    JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
    WHERE cs.is_filled = TRUE
      AND pm.email IS NOT NULL
      AND pm.email_verified_at IS NULL
''')
remaining = cur.fetchone()[0]
print(f'Unique emails remaining: {remaining:,}')
print(f'Estimated cost: ${remaining * 0.001:,.2f}')
print(f'Estimated time: ~{remaining * 0.4 / 60:.1f} minutes')

conn.close()
