#!/usr/bin/env python3
"""Compare company_master to DOL records"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']

print('Company Master vs DOL Comparison')
print('=' * 60)

# Total in company_master
cur.execute('SELECT COUNT(*) FROM company.company_master')
total_cm = cur.fetchone()[0]
print(f'Total company_master: {total_cm:,}')

# In target states
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE address_state = ANY(%s)', (states,))
cm_target = cur.fetchone()[0]
print(f'company_master in target states: {cm_target:,}')

# With EIN
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
with_ein = cur.fetchone()[0]
print(f'company_master with EIN: {with_ein:,}')

# With EIN in target states
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL AND address_state = ANY(%s)', (states,))
with_ein_target = cur.fetchone()[0]
print(f'company_master with EIN in target states: {with_ein_target:,}')

print()
print('By State:')
print('-' * 60)
header = f"{'State':<6} {'company_master':>15} {'with EIN':>12}"
print(header)
print('-' * 60)

for state in states:
    cur.execute('SELECT COUNT(*) FROM company.company_master WHERE address_state = %s', (state,))
    cm = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM company.company_master WHERE address_state = %s AND ein IS NOT NULL', (state,))
    ein = cur.fetchone()[0]
    print(f'{state:<6} {cm:>15,} {ein:>12,}')

print()
print('=' * 60)
print('SUMMARY:')
print(f'  company_master in target states: {cm_target:,}')
print(f'  DOL unmatched EINs (5500 + SF):  128,386')
print(f'  Ratio: DOL has {128386 / cm_target:.1f}x more companies than we have')
print('=' * 60)

cur.close()
conn.close()
