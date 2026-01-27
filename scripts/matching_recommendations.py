#!/usr/bin/env python3
"""Matching strategy recommendations and analysis."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*80)
    print('MATCHING STRATEGY RECOMMENDATIONS')
    print('='*80)

    # Strategy 1: Lower threshold with name normalization
    print()
    print('STRATEGY 1: NAME NORMALIZATION + LOWER THRESHOLD')
    print('-'*60)
    print('Current: SIMILARITY(name, 5500_name) > 0.85')
    print('Issues found:')
    print('  - "Amplity" vs "AMPLITY, INC." = 0.67 (should match!)')
    print('  - "National OnDemand, Inc." vs "NATIONAL ON DEMAND" = 0.64')
    print()
    print('Recommendation: Normalize names BEFORE similarity:')
    print('  1. Remove Inc, LLC, Corp, Ltd, Co')
    print('  2. Remove punctuation (commas, periods)')
    print('  3. Normalize ampersand to "and"')
    print('  4. Remove "The " prefix')
    print()

    # Test normalized matching
    cur.execute('''
        WITH normalized AS (
            SELECT 
                company_unique_id,
                company_name,
                address_state,
                UPPER(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                REGEXP_REPLACE(
                                    REGEXP_REPLACE(company_name, ',? (Inc\\.?|LLC|Corp\\.?|Ltd\\.?|Co\\.?)$', '', 'i'),
                                    '^The ', '', 'i'
                                ),
                                ' & ', ' and ', 'g'
                            ),
                            '[^a-zA-Z0-9 ]', '', 'g'
                        ),
                        '\\s+', ' ', 'g'
                    )
                ) as normalized_name
            FROM company.company_master
            WHERE ein IS NULL
            LIMIT 1000
        ),
        f5500_normalized AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein as ein,
                spons_dfe_mail_us_state as state,
                UPPER(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                REGEXP_REPLACE(
                                    REGEXP_REPLACE(sponsor_dfe_name, ',? (Inc\\.?|LLC|Corp\\.?|Ltd\\.?|Co\\.?)$', '', 'i'),
                                    '^The ', '', 'i'
                                ),
                                ' & ', ' and ', 'g'
                            ),
                            '[^a-zA-Z0-9 ]', '', 'g'
                        ),
                        '\\s+', ' ', 'g'
                    )
                ) as normalized_name
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL
        )
        SELECT 
            n.company_name,
            n.normalized_name,
            f.normalized_name as f5500_normalized,
            SIMILARITY(n.normalized_name, f.normalized_name) as sim
        FROM normalized n
        JOIN f5500_normalized f ON f.state = n.address_state
        WHERE SIMILARITY(n.normalized_name, f.normalized_name) > 0.80
        ORDER BY sim DESC
        LIMIT 20
    ''')
    print('Test results with normalized matching (>0.80):')
    for r in cur.fetchall():
        print(f'  {r[0][:35]:35} | {r[1][:20]:20} | {r[2][:20]:20} | {r[3]:.2f}')

    # Strategy 2: Cross-state matching for national companies
    print()
    print()
    print('STRATEGY 2: CROSS-STATE MATCHING')
    print('-'*60)
    print('Found 221 companies with exact name match in DIFFERENT state')
    print()
    print('These could be:')
    print('  1. National companies filing from HQ in another state')
    print('  2. Subsidiaries using parent company name')
    print()
    print('Recommendation: For high-confidence exact matches, allow cross-state')
    
    # Show examples
    cur.execute('''
        SELECT DISTINCT 
            cm.company_name, 
            cm.address_state as cm_state, 
            f.spons_dfe_mail_us_state as f5500_state,
            f.sponsor_dfe_ein
        FROM company.company_master cm
        JOIN dol.form_5500 f ON UPPER(f.sponsor_dfe_name) = UPPER(cm.company_name)
        WHERE cm.ein IS NULL
        AND f.spons_dfe_mail_us_state != cm.address_state
        LIMIT 10
    ''')
    print()
    print('Examples:')
    for r in cur.fetchall():
        print(f'  {r[0][:40]:40} | Our: {r[1]} | 5500: {r[2]} | EIN: {r[3]}')

    # Strategy 3: Admin name matching
    print()
    print()
    print('STRATEGY 3: ADMIN NAME MATCHING (TPA reverse lookup)')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(DISTINCT admin_ein) FROM dol.form_5500 WHERE admin_ein IS NOT NULL
    ''')
    r = cur.fetchone()
    print(f'  Unique Admin EINs in form_5500: {r[0]:,}')

    cur.execute('''
        SELECT COUNT(DISTINCT sf_admin_ein) FROM dol.form_5500_sf WHERE sf_admin_ein IS NOT NULL
    ''')
    r = cur.fetchone()
    print(f'  Unique Admin EINs in form_5500_sf: {r[0]:,}')

    print()
    print('Admin is usually the TPA (Third Party Administrator)')
    print('If we know the TPA, we could potentially use them as a reference')

    # Strategy 4: Business code matching
    print()
    print()
    print('STRATEGY 4: BUSINESS CODE (SIC/NAICS) MATCHING')
    print('-'*60)
    cur.execute('''
        SELECT business_code, COUNT(*) as cnt
        FROM dol.form_5500
        WHERE business_code IS NOT NULL
        GROUP BY business_code
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    print('Top business codes in form_5500:')
    for r in cur.fetchall():
        print(f'  {r[0]:10} | {r[1]:,} filings')

    cur.execute('''
        SELECT sic_codes, COUNT(*) as cnt
        FROM company.company_master
        WHERE sic_codes IS NOT NULL
        GROUP BY sic_codes
        ORDER BY cnt DESC
        LIMIT 5
    ''')
    print()
    print('SIC codes in company_master:')
    for r in cur.fetchall():
        code = r[0][:30] if r[0] else ''
        print(f'  {code:30} | {r[1]:,} companies')

    # Strategy 5: Word-based matching
    print()
    print()
    print('STRATEGY 5: SIGNIFICANT WORD MATCHING')
    print('-'*60)
    print('Instead of full name similarity, match on significant words')
    print()
    print('Example: "Penn Power Group - Fleet Services"')
    print('  Significant words: [Penn, Power, Group, Fleet, Services]')
    print('  If 3+ words match AND same state -> high confidence')

    # Strategy 6: Test lowering threshold with city match
    print()
    print()
    print('STRATEGY 6: CITY + NAME FUZZY (lower threshold)')
    print('-'*60)
    cur.execute('''
        WITH sample AS (
            SELECT company_name, address_state, address_city
            FROM company.company_master
            WHERE ein IS NULL AND address_city IS NOT NULL
            LIMIT 500
        )
        SELECT 
            s.company_name,
            f.sponsor_dfe_name,
            s.address_city,
            f.spons_dfe_mail_us_city,
            SIMILARITY(UPPER(s.company_name), UPPER(f.sponsor_dfe_name)) as sim
        FROM sample s
        JOIN dol.form_5500 f 
            ON f.spons_dfe_mail_us_state = s.address_state
            AND UPPER(f.spons_dfe_mail_us_city) = UPPER(s.address_city)
        WHERE SIMILARITY(UPPER(s.company_name), UPPER(f.sponsor_dfe_name)) BETWEEN 0.50 AND 0.70
        ORDER BY sim DESC
        LIMIT 15
    ''')
    print('Matches with SAME CITY and similarity 0.50-0.70:')
    for r in cur.fetchall():
        print(f'  {r[0][:30]:30} vs {r[1][:30]:30} | {r[2]:15} | {r[4]:.2f}')

    # NEW: Check partial name matching (first word)
    print()
    print()
    print('STRATEGY 7: FIRST WORD MATCHING')
    print('-'*60)
    cur.execute('''
        WITH cm_first_word AS (
            SELECT 
                company_unique_id,
                company_name,
                address_state,
                UPPER(SPLIT_PART(company_name, ' ', 1)) as first_word
            FROM company.company_master
            WHERE ein IS NULL
            AND LENGTH(SPLIT_PART(company_name, ' ', 1)) >= 5  -- significant first word
        ),
        f5500_first_word AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein,
                sponsor_dfe_name,
                spons_dfe_mail_us_state,
                UPPER(SPLIT_PART(sponsor_dfe_name, ' ', 1)) as first_word
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL
            AND LENGTH(SPLIT_PART(sponsor_dfe_name, ' ', 1)) >= 5
        )
        SELECT 
            cm.company_name,
            f.sponsor_dfe_name,
            cm.first_word,
            SIMILARITY(UPPER(cm.company_name), UPPER(f.sponsor_dfe_name)) as full_sim
        FROM cm_first_word cm
        JOIN f5500_first_word f 
            ON cm.first_word = f.first_word
            AND cm.address_state = f.spons_dfe_mail_us_state
        WHERE SIMILARITY(UPPER(cm.company_name), UPPER(f.sponsor_dfe_name)) BETWEEN 0.40 AND 0.70
        ORDER BY full_sim DESC
        LIMIT 15
    ''')
    print('Matches with SAME FIRST WORD (5+ chars) but low full similarity:')
    for r in cur.fetchall():
        print(f'  {r[0][:35]:35} vs {r[1][:35]:35} | {r[3]:.2f}')

    conn.close()

if __name__ == '__main__':
    main()
