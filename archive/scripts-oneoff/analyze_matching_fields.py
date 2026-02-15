#!/usr/bin/env python3
"""Analyze matching fields across 5500 tables and company_master."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*80)
    print('MATCHING FIELD ANALYSIS')
    print('='*80)

    # 1. Company Master - what do we have to match WITH?
    print()
    print('COMPANY_MASTER - Fields available for matching:')
    print('-'*60)
    cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(NULLIF(company_name, '')) as has_name,
            COUNT(NULLIF(address_state, '')) as has_state,
            COUNT(NULLIF(address_city, '')) as has_city,
            COUNT(NULLIF(address_zip, '')) as has_zip,
            COUNT(NULLIF(address_street, '')) as has_street,
            COUNT(NULLIF(company_phone, '')) as has_phone,
            COUNT(ein) as has_ein
        FROM company.company_master
    ''')
    r = cur.fetchone()
    print(f'  Total companies:     {r[0]:,}')
    print(f'  With name:           {r[1]:,} ({r[1]*100//r[0]}%)')
    print(f'  With state:          {r[2]:,} ({r[2]*100//r[0]}%)')
    print(f'  With city:           {r[3]:,} ({r[3]*100//r[0]}%)')
    print(f'  With zip:            {r[4]:,} ({r[4]*100//r[0]}%)')
    print(f'  With street:         {r[5]:,} ({r[5]*100//r[0]}%)')
    print(f'  With phone:          {r[6]:,} ({r[6]*100//r[0]}%)')
    print(f'  With EIN:            {r[7]:,} ({r[7]*100//r[0]}%)')

    # 2. Form 5500 - what matching fields?
    print()
    print('FORM 5500 - Matching fields available:')
    print('-'*60)
    cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT sponsor_dfe_ein) as unique_eins,
            COUNT(NULLIF(sponsor_dfe_name, '')) as has_name,
            COUNT(NULLIF(spons_dfe_dba_name, '')) as has_dba,
            COUNT(NULLIF(spons_dfe_mail_us_state, '')) as has_mail_state,
            COUNT(NULLIF(spons_dfe_mail_us_city, '')) as has_mail_city,
            COUNT(NULLIF(spons_dfe_mail_us_zip, '')) as has_mail_zip,
            COUNT(NULLIF(spons_dfe_loc_us_state, '')) as has_loc_state,
            COUNT(NULLIF(spons_dfe_loc_us_city, '')) as has_loc_city,
            COUNT(NULLIF(spons_dfe_loc_us_zip, '')) as has_loc_zip,
            COUNT(NULLIF(spons_dfe_phone_num, '')) as has_phone,
            COUNT(NULLIF(admin_name, '')) as has_admin_name,
            COUNT(NULLIF(admin_ein, '')) as has_admin_ein
        FROM dol.form_5500
    ''')
    r = cur.fetchone()
    print(f'  Total filings:       {r[0]:,}')
    print(f'  Unique EINs:         {r[1]:,}')
    print(f'  With sponsor name:   {r[2]:,}')
    print(f'  With DBA name:       {r[3]:,} (trade names!)')
    print(f'  With MAIL state:     {r[4]:,}')
    print(f'  With MAIL city:      {r[5]:,}')
    print(f'  With MAIL zip:       {r[6]:,}')
    print(f'  With LOCATION state: {r[7]:,}')
    print(f'  With LOCATION city:  {r[8]:,}')
    print(f'  With LOCATION zip:   {r[9]:,}')
    print(f'  With phone:          {r[10]:,}')
    print(f'  With admin name:     {r[11]:,}')
    print(f'  With admin EIN:      {r[12]:,} (TPA EINs!)')

    # 3. Form 5500_SF - what matching fields?
    print()
    print('FORM 5500_SF - Matching fields available:')
    print('-'*60)
    cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT sf_spons_ein) as unique_eins,
            COUNT(NULLIF(sf_sponsor_name, '')) as has_name,
            COUNT(NULLIF(sf_sponsor_dfe_dba_name, '')) as has_dba,
            COUNT(NULLIF(sf_spons_us_state, '')) as has_mail_state,
            COUNT(NULLIF(sf_spons_us_city, '')) as has_mail_city,
            COUNT(NULLIF(sf_spons_us_zip, '')) as has_mail_zip,
            COUNT(NULLIF(sf_spons_loc_us_state, '')) as has_loc_state,
            COUNT(NULLIF(sf_spons_loc_us_city, '')) as has_loc_city,
            COUNT(NULLIF(sf_spons_loc_us_zip, '')) as has_loc_zip,
            COUNT(NULLIF(sf_spons_phone_num, '')) as has_phone,
            COUNT(NULLIF(sf_admin_name, '')) as has_admin_name,
            COUNT(NULLIF(sf_admin_ein, '')) as has_admin_ein
        FROM dol.form_5500_sf
    ''')
    r = cur.fetchone()
    print(f'  Total filings:       {r[0]:,}')
    print(f'  Unique EINs:         {r[1]:,}')
    print(f'  With sponsor name:   {r[2]:,}')
    print(f'  With DBA name:       {r[3]:,} (trade names!)')
    print(f'  With MAIL state:     {r[4]:,}')
    print(f'  With MAIL city:      {r[5]:,}')
    print(f'  With MAIL zip:       {r[6]:,}')
    print(f'  With LOCATION state: {r[7]:,}')
    print(f'  With LOCATION city:  {r[8]:,}')
    print(f'  With LOCATION zip:   {r[9]:,}')
    print(f'  With phone:          {r[10]:,}')
    print(f'  With admin name:     {r[11]:,}')
    print(f'  With admin EIN:      {r[12]:,} (TPA EINs!)')

    # 4. Schedule A - what matching fields?
    print()
    print('SCHEDULE_A - Matching fields available:')
    print('-'*60)
    cur.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT sch_a_ein) as unique_eins,
            COUNT(NULLIF(sponsor_name, '')) as has_sponsor_name,
            COUNT(NULLIF(sponsor_state, '')) as has_state,
            COUNT(NULLIF(ins_carrier_name, '')) as has_carrier_name,
            COUNT(NULLIF(ins_carrier_ein, '')) as has_carrier_ein
        FROM dol.schedule_a
    ''')
    r = cur.fetchone()
    print(f'  Total records:       {r[0]:,}')
    print(f'  Unique EINs:         {r[1]:,}')
    print(f'  With sponsor name:   {r[2]:,}')
    print(f'  With state:          {r[3]:,}')
    print(f'  With carrier name:   {r[4]:,}')
    print(f'  With carrier EIN:    {r[5]:,}')

    # 5. NEW MATCHING OPPORTUNITIES
    print()
    print('='*80)
    print('NEW MATCHING OPPORTUNITIES')
    print('='*80)
    
    # ZIP code matching potential
    print()
    print('1. ZIP CODE MATCHING:')
    print('-'*60)
    cur.execute('''
        WITH cm_zips AS (
            SELECT DISTINCT LEFT(address_zip, 5) as zip5 
            FROM company.company_master 
            WHERE address_zip IS NOT NULL AND ein IS NULL
        ),
        f5500_zips AS (
            SELECT DISTINCT 
                LEFT(COALESCE(spons_dfe_mail_us_zip, spons_dfe_loc_us_zip), 5) as zip5,
                sponsor_dfe_ein
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL
        )
        SELECT COUNT(DISTINCT cm.zip5)
        FROM cm_zips cm
        JOIN f5500_zips f ON cm.zip5 = f.zip5
    ''')
    r = cur.fetchone()
    print(f'  Companies without EIN sharing ZIP with 5500 filers: {r[0]:,}')
    
    # Phone number matching potential
    print()
    print('2. PHONE NUMBER MATCHING:')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*) FROM company.company_master
        WHERE ein IS NULL 
        AND company_phone IS NOT NULL
        AND LENGTH(REGEXP_REPLACE(company_phone, '[^0-9]', '', 'g')) >= 10
    ''')
    r = cur.fetchone()
    print(f'  Companies without EIN with valid phone: {r[0]:,}')
    
    cur.execute('''
        SELECT COUNT(DISTINCT REGEXP_REPLACE(spons_dfe_phone_num, '[^0-9]', '', 'g'))
        FROM dol.form_5500
        WHERE spons_dfe_phone_num IS NOT NULL
        AND LENGTH(REGEXP_REPLACE(spons_dfe_phone_num, '[^0-9]', '', 'g')) >= 10
    ''')
    r = cur.fetchone()
    print(f'  Unique phone numbers in form_5500: {r[0]:,}')
    
    # Street address matching
    print()
    print('3. STREET ADDRESS MATCHING:')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*) FROM company.company_master
        WHERE ein IS NULL 
        AND address_street IS NOT NULL
        AND address_city IS NOT NULL
        AND address_state IS NOT NULL
    ''')
    r = cur.fetchone()
    print(f'  Companies without EIN with full address: {r[0]:,}')
    
    # Location vs Mail address - many companies file from different addresses
    print()
    print('4. LOCATION vs MAIL ADDRESS:')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*) FROM dol.form_5500
        WHERE spons_dfe_mail_us_state != spons_dfe_loc_us_state
        AND spons_dfe_mail_us_state IS NOT NULL
        AND spons_dfe_loc_us_state IS NOT NULL
    ''')
    r = cur.fetchone()
    print(f'  5500 filings where mail state != location state: {r[0]:,}')
    print('  → We should try BOTH addresses when matching!')
    
    # Companies without state
    print()
    print('5. COMPANIES WITHOUT STATE (NO_STATE errors):')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*) FROM company.company_master
        WHERE ein IS NULL 
        AND (address_state IS NULL OR address_state = '')
    ''')
    r = cur.fetchone()
    print(f'  Companies without EIN and without state: {r[0]:,}')
    
    cur.execute('''
        SELECT COUNT(*) FROM company.company_master
        WHERE ein IS NULL 
        AND (address_state IS NULL OR address_state = '')
        AND address_zip IS NOT NULL
    ''')
    r = cur.fetchone()
    print(f'  ...but HAVE zip code: {r[0]:,}')
    print('  → We can derive state from ZIP!')
    
    # Sample companies without state but with ZIP
    print()
    cur.execute('''
        SELECT company_name, address_city, address_zip, website_url
        FROM company.company_master
        WHERE ein IS NULL 
        AND (address_state IS NULL OR address_state = '')
        AND address_zip IS NOT NULL
        LIMIT 10
    ''')
    print('  Sample companies without state but WITH zip:')
    for r in cur.fetchall():
        print(f'    {r[0][:40]:40} | {r[1] or "":15} | {r[2]} | {r[3]}')
    
    conn.close()

if __name__ == '__main__':
    main()
