#!/usr/bin/env python3
"""
Blog Signal Extractor - BIT Signal Generation from Press Pages

Scrapes press/news pages and extracts buyer intent signals:
- FUNDING_ROUND (+25 points)
- ACQUISITION (+20 points)
- LAYOFFS (+15 points)
- EXPANSION (+10 points)
- EXECUTIVE_CHANGE (+12 points)

Tables Written:
- blog.pressure_signals (raw signals)
- outreach.bit_signals (aggregated)
- outreach.bit_scores (score update)

Cost: FREE ($0.00) - Web scraping only
"""

import os
import re
import sys
import uuid
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import psycopg2
from psycopg2.extras import execute_values
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Signal configuration with weights and decay periods
SIGNAL_CONFIG = {
    'FUNDING_ROUND': {
        'weight': 25,
        'decay_days': 90,
        'magnitude_range': (20, 40),
        'pressure_domain': 'NARRATIVE_VOLATILITY',
        'pressure_class': 'COST_PRESSURE',
        'patterns': [
            r'rais(?:ed|es|ing)\s+\$[\d,.]+\s*(?:million|M|billion|B)',
            r'series\s+[A-Z]\s+funding',
            r'funding\s+round',
            r'investment\s+of\s+\$[\d,.]+',
            r'secured\s+\$[\d,.]+',
            r'venture\s+capital',
            r'seed\s+funding',
            r'growth\s+capital',
            r'capital\s+raise',
            r'investor(?:s)?\s+led\s+by',
        ]
    },
    'ACQUISITION': {
        'weight': 20,
        'decay_days': 90,
        'magnitude_range': (15, 35),
        'pressure_domain': 'NARRATIVE_VOLATILITY',
        'pressure_class': 'ORGANIZATIONAL_RECONFIGURATION',
        'patterns': [
            r'acqui(?:red|res|ring|sition)',
            r'merg(?:ed|er|ing)\s+with',
            r'purchase(?:d|s)?\s+(?:by|from)',
            r'bought\s+by',
            r'strategic\s+acquisition',
            r'acquisition\s+agreement',
            r'acquisition\s+complete',
        ]
    },
    'LAYOFFS': {
        'weight': 15,
        'decay_days': 60,
        'magnitude_range': (15, 35),
        'pressure_domain': 'NARRATIVE_VOLATILITY',
        'pressure_class': 'ORGANIZATIONAL_RECONFIGURATION',
        'patterns': [
            r'layoff(?:s)?',
            r'laid\s+off',
            r'workforce\s+reduction',
            r'downsiz(?:ed|ing)',
            r'job\s+cuts',
            r'staff\s+reduction',
            r'eliminat(?:ed|ing)\s+(?:\d+\s+)?(?:jobs|positions|roles)',
            r'restructur(?:ed|ing)',
        ]
    },
    'EXPANSION': {
        'weight': 10,
        'decay_days': 90,
        'magnitude_range': (10, 25),
        'pressure_domain': 'NARRATIVE_VOLATILITY',
        'pressure_class': 'COST_PRESSURE',
        'patterns': [
            r'expand(?:ed|ing|s)\s+(?:to|into|operations)',
            r'open(?:ed|ing)\s+new\s+(?:office|location|facility|headquarters)',
            r'new\s+(?:office|location|facility)\s+in',
            r'growth\s+(?:in|across)',
            r'enter(?:ed|ing)\s+(?:new\s+)?market',
            r'geographic\s+expansion',
            r'added\s+(?:\d+\s+)?new\s+(?:employees|staff|hires)',
            r'hiring\s+(?:\d+\s+)?(?:new\s+)?(?:employees|staff)',
        ]
    },
    'EXECUTIVE_CHANGE': {
        'weight': 12,
        'decay_days': 90,
        'magnitude_range': (12, 30),
        'pressure_domain': 'NARRATIVE_VOLATILITY',
        'pressure_class': 'ORGANIZATIONAL_RECONFIGURATION',
        'patterns': [
            r'appoint(?:ed|s|ing)\s+(?:new\s+)?(?:CEO|CFO|CTO|COO|CMO|CHRO|President)',
            r'new\s+(?:CEO|CFO|CTO|COO|CMO|CHRO|President)',
            r'(?:CEO|CFO|CTO|COO|CMO|CHRO|President)\s+(?:steps\s+down|resigns|retires|departs)',
            r'leadership\s+(?:change|transition)',
            r'executive\s+(?:departure|appointment)',
            r'names?\s+(?:new\s+)?(?:CEO|CFO|CTO|COO|CMO|CHRO|President)',
            r'(?:joins|joined)\s+as\s+(?:CEO|CFO|CTO|COO|CMO|CHRO|President)',
            r'promoted\s+to\s+(?:CEO|CFO|CTO|COO|CMO|CHRO|President)',
        ]
    }
}

# Concurrency settings
MAX_WORKERS = 5
BATCH_SIZE = 50
MAX_COMPANIES = 20000  # Maximum companies to process per run

# Request settings
REQUEST_TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def fetch_page_content(url: str) -> Optional[str]:
    """Fetch and extract text content from a URL."""
    try:
        response = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text content
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)

        # Sanitize NUL characters
        text = text.replace('\x00', '')

        return text[:50000]  # Limit to 50KB

    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
        return None


def extract_signals(content: str, url: str) -> list:
    """Extract BIT signals from page content."""
    signals = []
    content_lower = content.lower()

    for signal_type, config in SIGNAL_CONFIG.items():
        for pattern in config['patterns']:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                # Calculate magnitude based on number of matches
                base_mag = config['magnitude_range'][0]
                max_mag = config['magnitude_range'][1]
                magnitude = min(base_mag + (len(matches) * 5), max_mag)

                # Extract snippet around match
                first_match = re.search(pattern, content, re.IGNORECASE)
                snippet = ""
                if first_match:
                    start = max(0, first_match.start() - 100)
                    end = min(len(content), first_match.end() + 100)
                    snippet = content[start:end].strip()

                signals.append({
                    'signal_type': signal_type,
                    'weight': config['weight'],
                    'decay_days': config['decay_days'],
                    'magnitude': magnitude,
                    'pressure_domain': config['pressure_domain'],
                    'pressure_class': config['pressure_class'],
                    'match_count': len(matches),
                    'snippet': snippet[:500],  # Limit snippet length
                    'source_url': url
                })
                break  # One signal per type per page

    return signals


def get_companies_with_press_pages(conn, limit: int = MAX_COMPANIES) -> list:
    """Get companies with press page URLs that haven't been processed."""
    with conn.cursor() as cur:
        # Get companies with press pages that need signal extraction
        # Bridge via domain since company_unique_id formats differ
        cur.execute("""
            WITH company_domains AS (
                SELECT
                    o.outreach_id,
                    ci.company_domain,
                    cm.unique_id as doctrine_company_id
                FROM outreach.outreach o
                JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
                JOIN company.company_master cm ON ci.company_domain = cm.domain
                WHERE ci.company_domain IS NOT NULL
            )
            SELECT DISTINCT ON (cd.outreach_id)
                cd.outreach_id,
                cd.company_domain,
                cd.doctrine_company_id,
                cu.source_url
            FROM company_domains cd
            JOIN company.company_source_urls cu
                ON cd.doctrine_company_id = cu.company_unique_id
            LEFT JOIN blog.pressure_signals ps
                ON cd.doctrine_company_id = ps.company_unique_id
                AND ps.signal_type IN ('FUNDING_ROUND', 'ACQUISITION', 'LAYOFFS', 'EXPANSION', 'EXECUTIVE_CHANGE')
            WHERE cu.source_type = 'press_page'
              AND cu.is_accessible = true
              AND ps.signal_id IS NULL  -- Not already processed
            ORDER BY cd.outreach_id, cu.discovered_at DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()
        return [
            {
                'outreach_id': row[0],
                'domain': row[1],
                'company_unique_id': row[2],
                'press_url': row[3]
            }
            for row in rows
        ]


def process_company(conn, company: dict) -> dict:
    """Process a single company's press page for signals."""
    result = {
        'outreach_id': company['outreach_id'],
        'company_unique_id': company['company_unique_id'],
        'signals_found': 0,
        'signals_written': 0,
        'error': None
    }

    try:
        content = fetch_page_content(company['press_url'])
        if not content:
            result['error'] = 'fetch_failed'
            return result

        signals = extract_signals(content, company['press_url'])
        result['signals_found'] = len(signals)

        if not signals:
            return result

        # Write signals to blog.pressure_signals
        correlation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        signal_records = []
        bit_signal_records = []

        for signal in signals:
            signal_id = str(uuid.uuid4())
            expires_at = now + timedelta(days=signal['decay_days'])

            # Record for blog.pressure_signals
            signal_records.append((
                signal_id,
                company['company_unique_id'],
                signal['signal_type'],
                signal['pressure_domain'],
                signal['pressure_class'],
                {
                    'snippet': signal['snippet'],
                    'match_count': signal['match_count'],
                    'source_url': signal['source_url']
                },
                signal['magnitude'],
                now,
                expires_at,
                correlation_id,
                company['press_url']
            ))

            # Record for outreach.bit_signals
            bit_signal_records.append((
                str(uuid.uuid4()),
                company['outreach_id'],
                signal['signal_type'],
                signal['weight'],
                'blog',  # source_spoke
                correlation_id,
                {
                    'magnitude': signal['magnitude'],
                    'source_url': signal['source_url'],
                    'pressure_domain': signal['pressure_domain']
                },
                signal['decay_days'],
                signal['weight'],  # decayed_impact (fresh = full)
                now,
                now
            ))

        with conn.cursor() as cur:
            # Insert into blog.pressure_signals
            execute_values(
                cur,
                """
                INSERT INTO blog.pressure_signals (
                    signal_id, company_unique_id, signal_type, pressure_domain,
                    pressure_class, signal_value, magnitude, detected_at,
                    expires_at, correlation_id, source_record_id
                ) VALUES %s
                ON CONFLICT DO NOTHING
                """,
                signal_records,
                template="(%s, %s, %s, %s::pressure_domain, %s::pressure_class, %s::jsonb, %s, %s, %s, %s, %s)"
            )

            # Insert into outreach.bit_signals
            execute_values(
                cur,
                """
                INSERT INTO outreach.bit_signals (
                    signal_id, outreach_id, signal_type, signal_impact,
                    source_spoke, correlation_id, signal_metadata,
                    decay_period_days, decayed_impact, signal_timestamp, processed_at
                ) VALUES %s
                ON CONFLICT DO NOTHING
                """,
                bit_signal_records,
                template="(%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)"
            )

            # Update bit_scores for this company
            total_blog_score = sum(s['weight'] for s in signals)
            cur.execute("""
                INSERT INTO outreach.bit_scores (
                    outreach_id, score, score_tier, signal_count, blog_score,
                    last_signal_at, last_scored_at
                ) VALUES (%s, %s,
                    CASE
                        WHEN %s >= 75 THEN 'BURNING'
                        WHEN %s >= 50 THEN 'HOT'
                        WHEN %s >= 25 THEN 'WARM'
                        ELSE 'COLD'
                    END,
                    %s, %s, %s, %s
                )
                ON CONFLICT (outreach_id) DO UPDATE SET
                    blog_score = outreach.bit_scores.blog_score + EXCLUDED.blog_score,
                    score = outreach.bit_scores.score + EXCLUDED.blog_score,
                    signal_count = outreach.bit_scores.signal_count + EXCLUDED.signal_count,
                    score_tier = CASE
                        WHEN outreach.bit_scores.score + EXCLUDED.blog_score >= 75 THEN 'BURNING'
                        WHEN outreach.bit_scores.score + EXCLUDED.blog_score >= 50 THEN 'HOT'
                        WHEN outreach.bit_scores.score + EXCLUDED.blog_score >= 25 THEN 'WARM'
                        ELSE 'COLD'
                    END,
                    last_signal_at = EXCLUDED.last_signal_at,
                    last_scored_at = EXCLUDED.last_scored_at,
                    updated_at = NOW()
            """, (
                company['outreach_id'],
                total_blog_score,
                total_blog_score, total_blog_score, total_blog_score,  # For CASE
                len(signals),
                total_blog_score,
                now, now
            ))

            # Update extraction status in company_source_urls
            cur.execute("""
                UPDATE company.company_source_urls
                SET extraction_status = 'completed',
                    people_extracted = %s
                WHERE company_unique_id = %s
                  AND source_type = 'press_page'
            """, (len(signals), company['company_unique_id']))

            conn.commit()
            result['signals_written'] = len(signals)

    except Exception as e:
        conn.rollback()
        result['error'] = str(e)
        logger.error(f"Error processing {company['domain']}: {e}")

    return result


def write_report(stats: dict, report_path: str):
    """Write execution report to markdown file."""
    now = datetime.now(timezone.utc)

    report = f"""# Blog Signal Extractor Report

**Execution Date**: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Cost**: $0.00 (FREE)
**Data Source**: company.company_source_urls (press_page URLs)

## Results

| Metric | Count |
|--------|------:|
| Companies processed | {stats['companies_processed']:,} |
| Pages scraped | {stats['pages_scraped']:,} |
| Pages failed | {stats['pages_failed']:,} |
| **Signals found** | **{stats['signals_found']:,}** |
| Signals written | {stats['signals_written']:,} |
| BIT scores updated | {stats['scores_updated']:,} |

## Signal Breakdown

| Signal Type | Count | Weight |
|-------------|------:|-------:|
| FUNDING_ROUND | {stats['signal_types'].get('FUNDING_ROUND', 0):,} | +25 |
| ACQUISITION | {stats['signal_types'].get('ACQUISITION', 0):,} | +20 |
| LAYOFFS | {stats['signal_types'].get('LAYOFFS', 0):,} | +15 |
| EXECUTIVE_CHANGE | {stats['signal_types'].get('EXECUTIVE_CHANGE', 0):,} | +12 |
| EXPANSION | {stats['signal_types'].get('EXPANSION', 0):,} | +10 |

## BIT Score Impact

| Tier | Before | After | Change |
|------|-------:|------:|-------:|
| BURNING (75+) | - | {stats.get('tier_burning', 0):,} | - |
| HOT (50-74) | - | {stats.get('tier_hot', 0):,} | - |
| WARM (25-49) | - | {stats.get('tier_warm', 0):,} | - |
| COLD (0-24) | - | {stats.get('tier_cold', 0):,} | - |

## Tables Written

1. `blog.pressure_signals` - {stats['signals_written']:,} records
2. `outreach.bit_signals` - {stats['signals_written']:,} records
3. `outreach.bit_scores` - {stats['scores_updated']:,} records updated

**Generated**: {now.isoformat()}Z
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)


def main():
    """Main execution function."""
    logger.info("=" * 70)
    logger.info("BLOG SIGNAL EXTRACTOR v1.0")
    logger.info("=" * 70)
    logger.info("Extracting BIT signals from press/news pages")
    logger.info("Signal types: FUNDING, ACQUISITION, LAYOFFS, EXPANSION, EXEC_CHANGE")
    logger.info("Cost: $0.00 (FREE)")
    logger.info("")

    stats = {
        'companies_processed': 0,
        'pages_scraped': 0,
        'pages_failed': 0,
        'signals_found': 0,
        'signals_written': 0,
        'scores_updated': 0,
        'signal_types': {}
    }

    try:
        logger.info("Connecting to database...")
        conn = get_db_connection()
        logger.info("Connected")

        logger.info("-" * 70)
        logger.info("Finding companies with press pages to process...")
        companies = get_companies_with_press_pages(conn, MAX_COMPANIES)
        logger.info(f"Found {len(companies):,} companies with press pages to process")

        if not companies:
            logger.info("No companies to process")
            return

        logger.info("-" * 70)
        logger.info("Scraping press pages (parallel batches)...")

        processed = 0
        for batch_start in range(0, len(companies), BATCH_SIZE):
            batch = companies[batch_start:batch_start + BATCH_SIZE]

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(process_company, conn, c): c for c in batch}

                for future in as_completed(futures):
                    result = future.result()
                    processed += 1
                    stats['companies_processed'] += 1

                    if result['error']:
                        stats['pages_failed'] += 1
                    else:
                        stats['pages_scraped'] += 1
                        stats['signals_found'] += result['signals_found']
                        stats['signals_written'] += result['signals_written']

                        if result['signals_written'] > 0:
                            stats['scores_updated'] += 1

            # Progress update every 100 companies
            if processed % 100 == 0 or processed == len(companies):
                logger.info(
                    f"  Processed {processed}/{len(companies)} - "
                    f"Found {stats['signals_found']} signals, "
                    f"updated {stats['scores_updated']} scores"
                )

        # Get signal type breakdown
        with conn.cursor() as cur:
            cur.execute("""
                SELECT signal_type, COUNT(*)
                FROM blog.pressure_signals
                WHERE detected_at > NOW() - INTERVAL '1 day'
                GROUP BY signal_type
            """)
            for row in cur.fetchall():
                stats['signal_types'][row[0]] = row[1]

            # Get tier distribution
            cur.execute("""
                SELECT score_tier, COUNT(*)
                FROM outreach.bit_scores
                WHERE last_scored_at > NOW() - INTERVAL '1 day'
                GROUP BY score_tier
            """)
            for row in cur.fetchall():
                tier_key = f"tier_{row[0].lower()}"
                stats[tier_key] = row[1]

        conn.close()

        logger.info("-" * 70)
        logger.info("RESULTS")
        logger.info("-" * 70)
        logger.info(f"Companies processed: {stats['companies_processed']:,}")
        logger.info(f"Pages scraped: {stats['pages_scraped']:,}")
        logger.info(f"Pages failed: {stats['pages_failed']:,}")
        logger.info(f"Signals found: {stats['signals_found']:,}")
        logger.info(f"Signals written: {stats['signals_written']:,}")
        logger.info(f"BIT scores updated: {stats['scores_updated']:,}")
        logger.info(f"Cost: $0.00")

        # Write report
        report_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        report_path = os.path.join(report_dir, 'BLOG_SIGNAL_REPORT.md')
        write_report(stats, report_path)
        logger.info(f"Report written to: {report_path}")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
