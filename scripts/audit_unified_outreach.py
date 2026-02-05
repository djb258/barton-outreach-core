#!/usr/bin/env python3
"""
Comprehensive READ-ONLY audit of all outreach companies as ONE unified dataset.
No more "Hunter DOL" vs "Original" distinction - just outreach_id.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
load_dotenv()

def get_connection():
    """Create database connection using Neon credentials"""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        port=os.getenv('NEON_PORT', '5432'),
        sslmode='require'
    )

def run_audit():
    """Run comprehensive audit queries"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("UNIFIED OUTREACH AUDIT REPORT")
    print("=" * 80)
    print()

    # 1. Total Universe
    print("1. TOTAL UNIVERSE")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as total_companies FROM outreach.outreach;")
    result = cursor.fetchone()
    print(f"Total Companies: {result['total_companies']:,}")
    print()

    # 2. Company Target Sub-Hub Status
    print("2. COMPANY TARGET SUB-HUB STATUS")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE ct.outreach_id IS NOT NULL) as has_company_target,
            COUNT(*) FILTER (WHERE ct.outreach_id IS NULL) as missing_company_target,
            COUNT(*) FILTER (WHERE ct.email_method IS NOT NULL) as has_email_method,
            COUNT(*) FILTER (WHERE ct.email_method IS NULL AND ct.outreach_id IS NOT NULL) as needs_email_method
        FROM outreach.outreach o
        LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total']:,}")
    print(f"Has Company Target:        {result['has_company_target']:,} ({100*result['has_company_target']/result['total']:.1f}%)")
    print(f"Missing Company Target:    {result['missing_company_target']:,}")
    print(f"Has Email Method:          {result['has_email_method']:,} ({100*result['has_email_method']/result['total']:.1f}%)")
    print(f"Needs Email Method:        {result['needs_email_method']:,}")
    print()

    # 3. DOL Sub-Hub Status
    print("3. DOL SUB-HUB STATUS")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE d.outreach_id IS NOT NULL) as has_dol_record,
            COUNT(*) FILTER (WHERE d.outreach_id IS NULL) as missing_dol_record,
            COUNT(*) FILTER (WHERE d.ein IS NOT NULL) as has_ein,
            COUNT(*) FILTER (WHERE d.filing_present = true) as has_filing
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total']:,}")
    print(f"Has DOL Record:            {result['has_dol_record']:,} ({100*result['has_dol_record']/result['total']:.1f}%)")
    print(f"Missing DOL Record:        {result['missing_dol_record']:,}")
    print(f"Has EIN:                   {result['has_ein']:,} ({100*result['has_ein']/result['total']:.1f}%)")
    print(f"Has Filing:                {result['has_filing']:,} ({100*result['has_filing']/result['total']:.1f}%)")
    print()

    # 4. People Slots Status
    print("4. PEOPLE SLOTS STATUS")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(DISTINCT o.outreach_id) as total,
            COUNT(DISTINCT o.outreach_id) FILTER (WHERE cs.outreach_id IS NOT NULL) as has_slots,
            COUNT(DISTINCT o.outreach_id) FILTER (WHERE cs.outreach_id IS NULL) as missing_slots
        FROM outreach.outreach o
        LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total']:,}")
    print(f"Has Slots:                 {result['has_slots']:,} ({100*result['has_slots']/result['total']:.1f}%)")
    print(f"Missing Slots:             {result['missing_slots']:,}")
    print()

    # 5. Slot Fill Status
    print("5. SLOT FILL STATUS (for companies WITH slots)")
    print("-" * 80)
    cursor.execute("""
        SELECT
            slot_type,
            COUNT(*) as total_slots,
            COUNT(*) FILTER (WHERE is_filled = true) as filled,
            COUNT(*) FILTER (WHERE is_filled = false OR is_filled IS NULL) as unfilled,
            ROUND(100.0 * COUNT(*) FILTER (WHERE is_filled = true) / COUNT(*), 1) as fill_pct
        FROM people.company_slot
        GROUP BY slot_type
        ORDER BY slot_type;
    """)
    results = cursor.fetchall()
    print(f"{'Slot Type':<15} {'Total':<10} {'Filled':<10} {'Unfilled':<10} {'Fill %':<10}")
    print("-" * 80)
    for row in results:
        print(f"{row['slot_type']:<15} {row['total_slots']:<10,} {row['filled']:<10,} {row['unfilled']:<10,} {row['fill_pct']:<10}%")
    print()

    # 6. Blog Sub-Hub Status
    print("6. BLOG SUB-HUB STATUS")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE b.outreach_id IS NOT NULL) as has_blog_record,
            COUNT(*) FILTER (WHERE b.outreach_id IS NULL) as missing_blog_record,
            COUNT(*) FILTER (WHERE b.about_url IS NOT NULL) as has_about_url,
            COUNT(*) FILTER (WHERE b.news_url IS NOT NULL) as has_news_url,
            COUNT(*) FILTER (WHERE b.about_url IS NOT NULL OR b.news_url IS NOT NULL) as has_any_url,
            COUNT(*) FILTER (WHERE b.about_url IS NULL AND b.news_url IS NULL AND b.outreach_id IS NOT NULL) as needs_urls
        FROM outreach.outreach o
        LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total']:,}")
    print(f"Has Blog Record:           {result['has_blog_record']:,} ({100*result['has_blog_record']/result['total']:.1f}%)")
    print(f"Missing Blog Record:       {result['missing_blog_record']:,}")
    print(f"Has About URL:             {result['has_about_url']:,} ({100*result['has_about_url']/result['total']:.1f}%)")
    print(f"Has News URL:              {result['has_news_url']:,} ({100*result['has_news_url']/result['total']:.1f}%)")
    print(f"Has Any URL:               {result['has_any_url']:,} ({100*result['has_any_url']/result['total']:.1f}%)")
    print(f"Needs URLs:                {result['needs_urls']:,}")
    print()

    # 7. BIT Scores Status
    print("7. BIT SCORES STATUS")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE bs.outreach_id IS NOT NULL) as has_bit_score,
            COUNT(*) FILTER (WHERE bs.outreach_id IS NULL) as needs_bit_score
        FROM outreach.outreach o
        LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total']:,}")
    print(f"Has BIT Score:             {result['has_bit_score']:,} ({100*result['has_bit_score']/result['total']:.1f}%)")
    print(f"Needs BIT Score:           {result['needs_bit_score']:,}")
    print()

    # 8. Full Company Readiness Summary
    print("8. FULL COMPANY READINESS SUMMARY")
    print("-" * 80)
    cursor.execute("""
        SELECT
            COUNT(*) as total_companies,
            COUNT(*) FILTER (WHERE ct.outreach_id IS NOT NULL) as has_ct,
            COUNT(*) FILTER (WHERE d.ein IS NOT NULL) as has_ein,
            COUNT(*) FILTER (WHERE cs_filled.outreach_id IS NOT NULL) as has_filled_slot,
            COUNT(*) FILTER (WHERE b.about_url IS NOT NULL OR b.news_url IS NOT NULL) as has_blog_url,
            COUNT(*) FILTER (WHERE bs.outreach_id IS NOT NULL) as has_bit_score,
            COUNT(*) FILTER (
                WHERE ct.outreach_id IS NOT NULL
                AND cs_filled.outreach_id IS NOT NULL
                AND (b.about_url IS NOT NULL OR b.news_url IS NOT NULL)
            ) as fully_enriched
        FROM outreach.outreach o
        LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        LEFT JOIN (SELECT DISTINCT outreach_id FROM people.company_slot WHERE is_filled = true) cs_filled ON o.outreach_id = cs_filled.outreach_id
        LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
        LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id;
    """)
    result = cursor.fetchone()
    print(f"Total Companies:           {result['total_companies']:,}")
    print(f"Has Company Target:        {result['has_ct']:,} ({100*result['has_ct']/result['total_companies']:.1f}%)")
    print(f"Has EIN:                   {result['has_ein']:,} ({100*result['has_ein']/result['total_companies']:.1f}%)")
    print(f"Has Filled Slot:           {result['has_filled_slot']:,} ({100*result['has_filled_slot']/result['total_companies']:.1f}%)")
    print(f"Has Blog URL:              {result['has_blog_url']:,} ({100*result['has_blog_url']/result['total_companies']:.1f}%)")
    print(f"Has BIT Score:             {result['has_bit_score']:,} ({100*result['has_bit_score']/result['total_companies']:.1f}%)")
    print(f"FULLY ENRICHED:            {result['fully_enriched']:,} ({100*result['fully_enriched']/result['total_companies']:.1f}%)")
    print()

    # 9. Work Remaining by Category
    print("9. WORK REMAINING BY CATEGORY")
    print("-" * 80)
    cursor.execute("""
        WITH company_status AS (
            SELECT
                o.outreach_id,
                CASE WHEN ct.outreach_id IS NULL THEN 1 ELSE 0 END as needs_ct,
                CASE WHEN ct.email_method IS NULL AND ct.outreach_id IS NOT NULL THEN 1 ELSE 0 END as needs_email_method,
                CASE WHEN cs.outreach_id IS NULL THEN 1 ELSE 0 END as needs_slots,
                CASE WHEN cs_ceo.is_filled IS NOT TRUE THEN 1 ELSE 0 END as needs_ceo,
                CASE WHEN cs_cfo.is_filled IS NOT TRUE THEN 1 ELSE 0 END as needs_cfo,
                CASE WHEN cs_hr.is_filled IS NOT TRUE THEN 1 ELSE 0 END as needs_hr,
                CASE WHEN b.about_url IS NULL THEN 1 ELSE 0 END as needs_about_url,
                CASE WHEN b.news_url IS NULL THEN 1 ELSE 0 END as needs_news_url,
                CASE WHEN bs.outreach_id IS NULL THEN 1 ELSE 0 END as needs_bit_score
            FROM outreach.outreach o
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN (SELECT DISTINCT outreach_id FROM people.company_slot) cs ON o.outreach_id = cs.outreach_id
            LEFT JOIN people.company_slot cs_ceo ON o.outreach_id = cs_ceo.outreach_id AND cs_ceo.slot_type = 'CEO'
            LEFT JOIN people.company_slot cs_cfo ON o.outreach_id = cs_cfo.outreach_id AND cs_cfo.slot_type = 'CFO'
            LEFT JOIN people.company_slot cs_hr ON o.outreach_id = cs_hr.outreach_id AND cs_hr.slot_type = 'HR'
            LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
            LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id
        )
        SELECT
            SUM(needs_ct) as needs_company_target,
            SUM(needs_email_method) as needs_email_method,
            SUM(needs_slots) as needs_slots_created,
            SUM(needs_ceo) as needs_ceo_filled,
            SUM(needs_cfo) as needs_cfo_filled,
            SUM(needs_hr) as needs_hr_filled,
            SUM(needs_about_url) as needs_about_url,
            SUM(needs_news_url) as needs_news_url,
            SUM(needs_bit_score) as needs_bit_score
        FROM company_status;
    """)
    result = cursor.fetchone()
    print("WORKLIST:")
    print(f"  Needs Company Target:      {result['needs_company_target']:,}")
    print(f"  Needs Email Method:        {result['needs_email_method']:,}")
    print(f"  Needs Slots Created:       {result['needs_slots_created']:,}")
    print(f"  Needs CEO Filled:          {result['needs_ceo_filled']:,}")
    print(f"  Needs CFO Filled:          {result['needs_cfo_filled']:,}")
    print(f"  Needs HR Filled:           {result['needs_hr_filled']:,}")
    print(f"  Needs About URL:           {result['needs_about_url']:,}")
    print(f"  Needs News URL:            {result['needs_news_url']:,}")
    print(f"  Needs BIT Score:           {result['needs_bit_score']:,}")
    print()

    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    run_audit()
