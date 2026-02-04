#!/usr/bin/env python3
"""Try matching DOL to outreach via phone number"""
import csv
import psycopg2
import os
import re

def normalize_phone(phone):
    """Strip to just digits"""
    if not phone:
        return ''
    return re.sub(r'\D', '', str(phone))[-10:]  # Last 10 digits

# DOL data
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build DOL phone lookup
dol_by_phone = {}
for row in dol_rows:
    phone = normalize_phone(row.get('phone', ''))
    if len(phone) == 10:
        dol_by_phone[phone] = row

print(f'DOL unique phones (10-digit): {len(dol_by_phone):,}')

# Get Hunter phones linked to outreach domains
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute('''
    SELECT DISTINCT o.outreach_id, o.domain, hc.phone_number
    FROM outreach.outreach o
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE hc.phone_number IS NOT NULL AND hc.phone_number != ''
''')
outreach_phones = cur.fetchall()
print(f'Outreach records with Hunter phone: {len(outreach_phones):,}')

# Try matching
phone_matches = {}
for outreach_id, domain, hunter_phone in outreach_phones:
    norm_phone = normalize_phone(hunter_phone)
    if norm_phone in dol_by_phone:
        dol_row = dol_by_phone[norm_phone]
        phone_matches[outreach_id] = {
            'domain': domain,
            'phone': hunter_phone,
            'ein': dol_row.get('ein'),
            'dol_company': dol_row.get('company_name'),
        }

print(f'Phone matches: {len(phone_matches):,}')

if phone_matches:
    print('\nSAMPLE PHONE MATCHES:')
    for oid, data in list(phone_matches.items())[:10]:
        print(f"  {data['domain']:<30} | Phone: {data['phone']:<15} | EIN: {data['ein']} | {data['dol_company'][:30]}")

conn.close()
