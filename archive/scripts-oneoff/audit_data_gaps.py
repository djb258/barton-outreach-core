#!/usr/bin/env python3
"""
Comprehensive Outreach Pipeline Data Gap Audit
Generates prioritized cleanup to-do list
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

def run_query(cursor, query, description):
    """Execute query and return results"""
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print(f"\n{'='*80}")
        print(f"{description}")
        print('='*80)
        if results:
            headers = results[0].keys()
            rows = [list(row.values()) for row in results]
            print(tabulate(rows, headers=headers, tablefmt='grid'))
        return results
    except Exception as e:
        print(f"ERROR in {description}: {e}")
        return []

def main():
    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return

    # Connect to database
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("\n" + "="*80)
    print("OUTREACH PIPELINE DATA GAP AUDIT")
    print("="*80)

    # Store results for summary
    audit_results = {}

    # 1. COMPANY TARGET - Email Pattern Coverage
    query = """
    SELECT
        COUNT(*) as total,
        COUNT(email_method) as has_pattern,
        COUNT(*) - COUNT(email_method) as missing_pattern,
        ROUND(100.0 * COUNT(email_method) / COUNT(*), 2) as pct
    FROM outreach.company_target;
    """
    results = run_query(cursor, query, "1. COMPANY TARGET (04.04.01) - Email Pattern Coverage")
    if results:
        audit_results['company_target_email_pattern'] = results[0]

    # 2. PEOPLE - Email Coverage
    query = """
    SELECT
        COUNT(*) as total_people,
        COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
        COUNT(*) FILTER (WHERE email IS NULL OR email = '') as missing_email,
        ROUND(100.0 * COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') / COUNT(*), 2) as email_pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id AND cs.is_filled = true
    );
    """
    results = run_query(cursor, query, "2. PEOPLE (04.04.02) - Email Coverage")
    if results:
        audit_results['people_email'] = results[0]

    # 3. PEOPLE - LinkedIn Coverage
    query = """
    SELECT
        COUNT(*) as total,
        COUNT(linkedin_url) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') as has_linkedin,
        ROUND(100.0 * COUNT(linkedin_url) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') / COUNT(*), 2) as linkedin_pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id AND cs.is_filled = true
    );
    """
    results = run_query(cursor, query, "3. PEOPLE (04.04.02) - LinkedIn Coverage")
    if results:
        audit_results['people_linkedin'] = results[0]

    # 4. SLOT FILL RATES
    query = """
    SELECT
        slot_type,
        COUNT(*) as total_slots,
        COUNT(*) FILTER (WHERE is_filled = true) as filled,
        COUNT(*) FILTER (WHERE is_filled = false) as unfilled,
        ROUND(100.0 * COUNT(*) FILTER (WHERE is_filled = true) / COUNT(*), 2) as fill_pct
    FROM people.company_slot
    GROUP BY slot_type
    ORDER BY slot_type;
    """
    results = run_query(cursor, query, "4. SLOT FILL RATES")
    audit_results['slot_fill_rates'] = results

    # 5. BLOG - About URL Coverage
    query = """
    SELECT
        COUNT(*) as total,
        COUNT(about_url) FILTER (WHERE about_url IS NOT NULL AND about_url != '') as has_about,
        ROUND(100.0 * COUNT(about_url) FILTER (WHERE about_url IS NOT NULL AND about_url != '') / COUNT(*), 2) as about_pct
    FROM outreach.blog;
    """
    results = run_query(cursor, query, "5. BLOG (04.04.05) - About URL Coverage")
    if results:
        audit_results['blog_about'] = results[0]

    # 6. BLOG - News URL Coverage
    query = """
    SELECT
        COUNT(*) as total,
        COUNT(news_url) FILTER (WHERE news_url IS NOT NULL AND news_url != '') as has_news,
        ROUND(100.0 * COUNT(news_url) FILTER (WHERE news_url IS NOT NULL AND news_url != '') / COUNT(*), 2) as news_pct
    FROM outreach.blog;
    """
    results = run_query(cursor, query, "6. BLOG (04.04.05) - News URL Coverage")
    if results:
        audit_results['blog_news'] = results[0]

    # 7. BIT SCORES Coverage
    query = """
    SELECT
        COUNT(DISTINCT o.outreach_id) as total_companies,
        COUNT(DISTINCT bs.outreach_id) as has_bit_score,
        COUNT(DISTINCT o.outreach_id) - COUNT(DISTINCT bs.outreach_id) as missing_bit_score,
        ROUND(100.0 * COUNT(DISTINCT bs.outreach_id) / COUNT(DISTINCT o.outreach_id), 2) as bit_pct
    FROM outreach.outreach o
    LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id;
    """
    results = run_query(cursor, query, "7. BIT SCORES Coverage")
    if results:
        audit_results['bit_scores'] = results[0]

    # 8. DOL Coverage
    query = """
    SELECT
        COUNT(DISTINCT o.outreach_id) as total_companies,
        COUNT(DISTINCT d.outreach_id) as has_dol,
        COUNT(DISTINCT o.outreach_id) - COUNT(DISTINCT d.outreach_id) as missing_dol,
        ROUND(100.0 * COUNT(DISTINCT d.outreach_id) / COUNT(DISTINCT o.outreach_id), 2) as dol_pct
    FROM outreach.outreach o
    LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id;
    """
    results = run_query(cursor, query, "8. DOL (04.04.03) Coverage")
    if results:
        audit_results['dol_coverage'] = results[0]

    # 9. Email Verification Status
    query = """
    SELECT
        COALESCE(email_verification_source, 'NULL') as source,
        COUNT(*) as count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id AND cs.is_filled = true
    )
    GROUP BY email_verification_source
    ORDER BY count DESC;
    """
    results = run_query(cursor, query, "9. EMAIL VERIFICATION STATUS")
    audit_results['email_verification'] = results

    # 10. Companies Without Any People in Slots
    query = """
    SELECT COUNT(DISTINCT o.outreach_id) as companies_with_no_people
    FROM outreach.outreach o
    WHERE NOT EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.outreach_id = o.outreach_id AND cs.is_filled = true
    );
    """
    results = run_query(cursor, query, "10. Companies Without ANY People in Slots")
    if results:
        audit_results['companies_no_people'] = results[0]

    # Generate Summary Report
    print("\n" + "="*80)
    print("EXECUTIVE SUMMARY - DATA GAP ANALYSIS")
    print("="*80 + "\n")

    summary_data = []

    # Company Target Email Patterns
    ct = audit_results.get('company_target_email_pattern', {})
    summary_data.append([
        "Company Target",
        "Email Pattern",
        ct.get('total', 0),
        ct.get('has_pattern', 0),
        ct.get('missing_pattern', 0),
        f"{ct.get('pct', 0):.2f}%"
    ])

    # People Email
    pe = audit_results.get('people_email', {})
    summary_data.append([
        "People",
        "Email Address",
        pe.get('total_people', 0),
        pe.get('has_email', 0),
        pe.get('missing_email', 0),
        f"{pe.get('email_pct', 0):.2f}%"
    ])

    # People LinkedIn
    pl = audit_results.get('people_linkedin', {})
    summary_data.append([
        "People",
        "LinkedIn URL",
        pl.get('total', 0),
        pl.get('has_linkedin', 0),
        pl.get('total', 0) - pl.get('has_linkedin', 0),
        f"{pl.get('linkedin_pct', 0):.2f}%"
    ])

    # BIT Scores
    bit = audit_results.get('bit_scores', {})
    summary_data.append([
        "BIT Scores",
        "Score Calculated",
        bit.get('total_companies', 0),
        bit.get('has_bit_score', 0),
        bit.get('missing_bit_score', 0),
        f"{bit.get('bit_pct', 0):.2f}%"
    ])

    # DOL Coverage
    dol = audit_results.get('dol_coverage', {})
    summary_data.append([
        "DOL Filings",
        "EIN/Form 5500",
        dol.get('total_companies', 0),
        dol.get('has_dol', 0),
        dol.get('missing_dol', 0),
        f"{dol.get('dol_pct', 0):.2f}%"
    ])

    # Blog About URLs
    ba = audit_results.get('blog_about', {})
    summary_data.append([
        "Blog",
        "About URL",
        ba.get('total', 0),
        ba.get('has_about', 0),
        ba.get('total', 0) - ba.get('has_about', 0),
        f"{ba.get('about_pct', 0):.2f}%"
    ])

    # Blog News URLs
    bn = audit_results.get('blog_news', {})
    summary_data.append([
        "Blog",
        "News URL",
        bn.get('total', 0),
        bn.get('has_news', 0),
        bn.get('total', 0) - bn.get('has_news', 0),
        f"{bn.get('news_pct', 0):.2f}%"
    ])

    # Companies with No People
    cnp = audit_results.get('companies_no_people', {})
    total_companies = ct.get('total', 0)
    no_people_count = cnp.get('companies_with_no_people', 0)
    summary_data.append([
        "Companies",
        "No Filled Slots",
        total_companies,
        total_companies - no_people_count,
        no_people_count,
        f"{100.0 * (total_companies - no_people_count) / total_companies if total_companies > 0 else 0:.2f}%"
    ])

    headers = ["Hub/Entity", "Metric", "Total", "Complete", "Missing", "Coverage %"]
    print(tabulate(summary_data, headers=headers, tablefmt='grid'))

    # Slot Fill Rates Summary
    print("\n" + "="*80)
    print("SLOT FILL RATES BY TYPE")
    print("="*80 + "\n")

    slot_data = []
    for slot in audit_results.get('slot_fill_rates', []):
        slot_data.append([
            slot['slot_type'],
            slot['total_slots'],
            slot['filled'],
            slot['unfilled'],
            f"{slot['fill_pct']:.2f}%"
        ])

    headers = ["Slot Type", "Total", "Filled", "Unfilled", "Fill %"]
    print(tabulate(slot_data, headers=headers, tablefmt='grid'))

    # PRIORITIZED CLEANUP TO-DO LIST
    print("\n" + "="*80)
    print("PRIORITIZED CLEANUP TO-DO LIST")
    print("="*80 + "\n")

    # Calculate gaps and prioritize
    priorities = []

    # Priority 1: CRITICAL (blocks marketing execution)
    if pe.get('email_pct', 100) < 95:
        priorities.append({
            'priority': 'P1-CRITICAL',
            'gap': f"{pe.get('missing_email', 0):,} people missing emails",
            'impact': 'BLOCKS OUTREACH - Cannot send campaigns without verified emails',
            'coverage': f"{pe.get('email_pct', 0):.2f}%",
            'action': 'Run Phase 5 Email Generation pipeline for all filled slots'
        })

    if ct.get('pct', 100) < 95:
        priorities.append({
            'priority': 'P1-CRITICAL',
            'gap': f"{ct.get('missing_pattern', 0):,} companies missing email patterns",
            'impact': 'BLOCKS EMAIL GENERATION - Phase 5 cannot run without patterns',
            'coverage': f"{ct.get('pct', 0):.2f}%",
            'action': 'Run Phase 3 Email Pattern Waterfall for company_target records'
        })

    if no_people_count > 0:
        priorities.append({
            'priority': 'P1-CRITICAL',
            'gap': f"{no_people_count:,} companies with NO filled slots",
            'impact': 'BLOCKS OUTREACH - No one to contact at these companies',
            'coverage': f"{100.0 * (total_companies - no_people_count) / total_companies if total_companies > 0 else 0:.2f}%",
            'action': 'Run Phase 6 Slot Assignment for all companies missing people'
        })

    # Priority 2: HIGH (reduces campaign effectiveness)
    for slot in audit_results.get('slot_fill_rates', []):
        if slot['fill_pct'] < 50 and slot['slot_type'] in ['CEO', 'CFO', 'HR']:
            priorities.append({
                'priority': 'P2-HIGH',
                'gap': f"{slot['unfilled']:,} {slot['slot_type']} slots unfilled",
                'impact': f"REDUCES OUTREACH - Key {slot['slot_type']} contacts missing",
                'coverage': f"{slot['fill_pct']:.2f}%",
                'action': f"Enrich {slot['slot_type']} slots via Apollo/ZoomInfo"
            })

    if bit.get('bit_pct', 100) < 50:
        priorities.append({
            'priority': 'P2-HIGH',
            'gap': f"{bit.get('missing_bit_score', 0):,} companies missing BIT scores",
            'impact': 'REDUCES TARGETING - Cannot prioritize high-intent companies',
            'coverage': f"{bit.get('bit_pct', 0):.2f}%",
            'action': 'Run BIT Engine calculation for all companies with signals'
        })

    # Priority 3: MEDIUM (enrichment/intelligence gaps)
    if dol.get('dol_pct', 100) < 50:
        priorities.append({
            'priority': 'P3-MEDIUM',
            'gap': f"{dol.get('missing_dol', 0):,} companies missing DOL data",
            'impact': 'REDUCES INTELLIGENCE - Missing retirement plan insights',
            'coverage': f"{dol.get('dol_pct', 0):.2f}%",
            'action': 'Resume WO-DOL-001 - DOL enrichment pipeline (currently DEFERRED)'
        })

    if pl.get('linkedin_pct', 100) < 50:
        priorities.append({
            'priority': 'P3-MEDIUM',
            'gap': f"{pl.get('total', 0) - pl.get('has_linkedin', 0):,} people missing LinkedIn URLs",
            'impact': 'REDUCES VALIDATION - Cannot verify person identity/title',
            'coverage': f"{pl.get('linkedin_pct', 0):.2f}%",
            'action': 'Enrich LinkedIn URLs via Apollo/ZoomInfo API'
        })

    # Priority 4: LOW (content signals)
    if ba.get('about_pct', 100) < 50:
        priorities.append({
            'priority': 'P4-LOW',
            'gap': f"{ba.get('total', 0) - ba.get('has_about', 0):,} companies missing About URLs",
            'impact': 'REDUCES PERSONALIZATION - Missing company narrative',
            'coverage': f"{ba.get('about_pct', 0):.2f}%",
            'action': 'Crawl company websites for /about pages'
        })

    if bn.get('news_pct', 100) < 50:
        priorities.append({
            'priority': 'P4-LOW',
            'gap': f"{bn.get('total', 0) - bn.get('has_news', 0):,} companies missing News URLs",
            'impact': 'REDUCES SIGNALS - Missing content/news monitoring',
            'coverage': f"{bn.get('news_pct', 0):.2f}%",
            'action': 'Crawl company websites for /news or /blog pages'
        })

    # Sort by priority
    priority_order = {'P1-CRITICAL': 1, 'P2-HIGH': 2, 'P3-MEDIUM': 3, 'P4-LOW': 4}
    priorities.sort(key=lambda x: priority_order.get(x['priority'], 99))

    # Display prioritized list
    for i, item in enumerate(priorities, 1):
        print(f"{i}. [{item['priority']}] {item['gap']}")
        print(f"   Coverage: {item['coverage']}")
        print(f"   Impact: {item['impact']}")
        print(f"   Action: {item['action']}")
        print()

    # Close connection
    cursor.close()
    conn.close()

    print("="*80)
    print("AUDIT COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
