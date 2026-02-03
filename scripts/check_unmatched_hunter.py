#!/usr/bin/env python3
"""Check if Hunter domains from unmatched DOL exist in outreach database."""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Domains from Hunter unmatched DOL test (with DOL state for validation)
hunter_results = [
    ('2silosbrewing.com', '474673790', 'VA', 'VA'),      # MATCH
    ('20degs.com', '830601338', 'DC', 'DC'),             # MATCH
    ('lymefolk.com', '522203967', 'DC', '??'),           # WRONG
    ('2310.gr', '452731616', 'NC', 'Greece'),            # WRONG
    ('23rdgroup.com', '471250023', 'NC', 'NC'),          # MATCH
    ('crhanesthesia.com', '834514033', 'PA', 'GA'),      # WRONG
    ('2320toolanddie.com', '201080666', 'OH', 'OH'),     # MATCH
    ('2lmn.com', '311124011', 'OH', 'OH'),               # MATCH
    ('2ndwave.jp', '262738181', 'DC', 'Japan'),          # WRONG
    ('recycling.com', '473372754', 'DC', 'Netherlands'), # WRONG
    ('hillmgt.com', '922002219', 'NC', 'MD'),            # WRONG
    ('diamonds.net', '202615246', 'PA', 'MI'),           # WRONG
]

print('='*80)
print('HUNTER UNMATCHED DOL DOMAINS vs OUTREACH DATABASE')
print('='*80)
print()
print(f'{"Domain":<25} | {"DOL State":<8} | {"Hunter State":<12} | {"In Outreach?":<15} | {"Has EIN?"}')
print('-'*80)

in_outreach = 0
can_link = 0
already_linked = 0

for domain, ein, dol_state, hunter_state in hunter_results:
    # Check if domain exists in outreach
    cur.execute('SELECT outreach_id FROM outreach.outreach WHERE LOWER(domain) = LOWER(%s)', (domain,))
    result = cur.fetchone()
    
    if result:
        outreach_id = result[0]
        in_outreach += 1
        
        # Check if already has EIN linked
        cur.execute('SELECT ein FROM outreach.dol WHERE outreach_id = %s', (outreach_id,))
        ein_result = cur.fetchone()
        
        if ein_result:
            already_linked += 1
            ein_status = f'Has EIN: {ein_result[0]}'
        else:
            can_link += 1
            ein_status = f'CAN LINK: {ein}'
        
        status = 'YES'
    else:
        status = 'NO - NEW!'
        ein_status = 'N/A'
    
    state_match = '✓' if dol_state == hunter_state else '✗'
    print(f'{domain:<25} | {dol_state:<8} | {hunter_state:<12} | {status:<15} | {ein_status}')

print()
print('='*80)
print('SUMMARY')
print('='*80)
print(f'Total domains checked:    {len(hunter_results)}')
print(f'In outreach database:     {in_outreach}')
print(f'  - Already has EIN:      {already_linked}')
print(f'  - Can link EIN:         {can_link}')
print(f'NOT in outreach (NEW):    {len(hunter_results) - in_outreach}')

conn.close()
