#!/usr/bin/env python3
"""
Analyze Hunter source URLs for About/News patterns
and assess outreach.blog schema requirements.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_neon_connection():
    """Create Neon database connection."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def analyze_hunter_urls():
    """Analyze Hunter source URLs for About/News patterns."""
    conn = get_neon_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("HUNTER SOURCE URL ANALYSIS FOR OUTREACH.BLOG")
    print("=" * 80)
    print()

    # 1. Count About-type URLs
    print("1. ABOUT-TYPE URLs IN HUNTER SOURCES")
    print("-" * 80)
    cur.execute("""
        SELECT COUNT(*) as about_urls
        FROM enrichment.v_hunter_contact_sources
        WHERE source_url ILIKE '%/about%'
           OR source_url ILIKE '%/about-us%'
           OR source_url ILIKE '%/team%'
           OR source_url ILIKE '%/our-team%'
           OR source_url ILIKE '%/leadership%'
           OR source_url ILIKE '%/who-we-are%'
           OR source_url ILIKE '%/company%'
    """)
    result = cur.fetchone()
    print(f"Total About URLs: {result['about_urls']:,}")
    print()

    # 2. Count News/Press URLs
    print("2. NEWS/PRESS URLs IN HUNTER SOURCES")
    print("-" * 80)
    cur.execute("""
        SELECT COUNT(*) as news_urls
        FROM enrichment.v_hunter_contact_sources
        WHERE source_url ILIKE '%/news%'
           OR source_url ILIKE '%/press%'
           OR source_url ILIKE '%/media%'
           OR source_url ILIKE '%/announcements%'
           OR source_url ILIKE '%prnewswire%'
           OR source_url ILIKE '%businesswire%'
           OR source_url ILIKE '%/blog%'
    """)
    result = cur.fetchone()
    print(f"Total News URLs: {result['news_urls']:,}")
    print()

    # 3. Count outreach companies with About URLs
    print("3. OUTREACH COMPANIES COVERAGE - ABOUT URLs")
    print("-" * 80)
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as companies_with_about
        FROM outreach.outreach o
        JOIN enrichment.v_hunter_contact_sources vhcs ON LOWER(o.domain) = LOWER(vhcs.domain)
        WHERE vhcs.source_url ILIKE '%/about%'
           OR vhcs.source_url ILIKE '%/about-us%'
           OR vhcs.source_url ILIKE '%/team%'
           OR vhcs.source_url ILIKE '%/leadership%'
           OR vhcs.source_url ILIKE '%/who-we-are%'
           OR vhcs.source_url ILIKE '%/our-team%'
           OR vhcs.source_url ILIKE '%/company%'
    """)
    result = cur.fetchone()
    companies_with_about = result['companies_with_about']
    print(f"Outreach companies with About URLs: {companies_with_about:,}")

    # Get total outreach companies
    cur.execute("SELECT COUNT(*) as total FROM outreach.outreach")
    total_outreach = cur.fetchone()['total']
    coverage_pct = (companies_with_about / total_outreach * 100) if total_outreach > 0 else 0
    print(f"Total outreach companies: {total_outreach:,}")
    print(f"Coverage: {coverage_pct:.1f}%")
    print()

    # 4. Count outreach companies with News URLs
    print("4. OUTREACH COMPANIES COVERAGE - NEWS URLs")
    print("-" * 80)
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as companies_with_news
        FROM outreach.outreach o
        JOIN enrichment.v_hunter_contact_sources vhcs ON LOWER(o.domain) = LOWER(vhcs.domain)
        WHERE vhcs.source_url ILIKE '%/news%'
           OR vhcs.source_url ILIKE '%/press%'
           OR vhcs.source_url ILIKE '%/media%'
           OR vhcs.source_url ILIKE '%/announcements%'
           OR vhcs.source_url ILIKE '%prnewswire%'
           OR vhcs.source_url ILIKE '%businesswire%'
           OR vhcs.source_url ILIKE '%/blog%'
    """)
    result = cur.fetchone()
    companies_with_news = result['companies_with_news']
    print(f"Outreach companies with News URLs: {companies_with_news:,}")
    coverage_pct = (companies_with_news / total_outreach * 100) if total_outreach > 0 else 0
    print(f"Coverage: {coverage_pct:.1f}%")
    print()

    # 5. Check current outreach.blog schema
    print("5. CURRENT OUTREACH.BLOG SCHEMA")
    print("-" * 80)
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'outreach' AND table_name = 'blog'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    if columns:
        print(f"{'Column Name':<30} {'Type':<20} {'Length':<10} {'Nullable':<10}")
        print("-" * 80)
        for col in columns:
            length = str(col['character_maximum_length']) if col['character_maximum_length'] else 'N/A'
            nullable = 'YES' if col['is_nullable'] == 'YES' else 'NO'
            print(f"{col['column_name']:<30} {col['data_type']:<20} {length:<10} {nullable:<10}")
    else:
        print("No columns found - table may not exist")
    print()

    # 6. Sample About URLs
    print("6. SAMPLE ABOUT URLs (Top 20 by frequency)")
    print("-" * 80)
    cur.execute("""
        SELECT vhcs.source_url, COUNT(*) as frequency
        FROM enrichment.v_hunter_contact_sources vhcs
        WHERE vhcs.source_url ILIKE '%/about%'
           OR vhcs.source_url ILIKE '%/about-us%'
           OR vhcs.source_url ILIKE '%/team%'
           OR vhcs.source_url ILIKE '%/leadership%'
           OR vhcs.source_url ILIKE '%/who-we-are%'
           OR vhcs.source_url ILIKE '%/our-team%'
           OR vhcs.source_url ILIKE '%/company%'
        GROUP BY vhcs.source_url
        ORDER BY frequency DESC
        LIMIT 20
    """)
    about_samples = cur.fetchall()
    for row in about_samples:
        print(f"{row['frequency']:>5}x  {row['source_url']}")
    print()

    # 7. Sample News URLs
    print("7. SAMPLE NEWS URLs (Top 20 by frequency)")
    print("-" * 80)
    cur.execute("""
        SELECT vhcs.source_url, COUNT(*) as frequency
        FROM enrichment.v_hunter_contact_sources vhcs
        WHERE vhcs.source_url ILIKE '%/news%'
           OR vhcs.source_url ILIKE '%/press%'
           OR vhcs.source_url ILIKE '%/media%'
           OR vhcs.source_url ILIKE '%/announcements%'
           OR vhcs.source_url ILIKE '%prnewswire%'
           OR vhcs.source_url ILIKE '%businesswire%'
           OR vhcs.source_url ILIKE '%/blog%'
        GROUP BY vhcs.source_url
        ORDER BY frequency DESC
        LIMIT 20
    """)
    news_samples = cur.fetchall()
    for row in news_samples:
        print(f"{row['frequency']:>5}x  {row['source_url']}")
    print()

    # 8. Recommendations
    print("8. SCHEMA RECOMMENDATIONS")
    print("-" * 80)
    print("Based on the analysis above, outreach.blog should have:")
    print()
    print("REQUIRED COLUMNS:")
    print("  - about_url (TEXT, NULLABLE)         : Company About page URL")
    print("  - news_url (TEXT, NULLABLE)          : Company News/Press page URL")
    print("  - blog_url (TEXT, NULLABLE)          : Company Blog URL")
    print("  - source_metadata (JSONB, NULLABLE)  : Hunter source frequency data")
    print("  - last_extracted_at (TIMESTAMP)      : When URLs were extracted")
    print("  - extraction_method (TEXT)           : 'hunter_api' or 'manual'")
    print()
    print("INDEXING RECOMMENDATIONS:")
    print("  - CREATE INDEX idx_blog_about_url ON outreach.blog(about_url) WHERE about_url IS NOT NULL;")
    print("  - CREATE INDEX idx_blog_news_url ON outreach.blog(news_url) WHERE news_url IS NOT NULL;")
    print()
    print("NEXT STEPS:")
    print("  1. Review current outreach.blog schema above")
    print("  2. Create ALTER TABLE migration if columns missing")
    print("  3. Create URL extraction + population script")
    print("  4. Run deduplication logic (prefer most frequent URL per pattern)")
    print()

    cur.close()
    conn.close()

if __name__ == "__main__":
    analyze_hunter_urls()
