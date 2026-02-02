#!/usr/bin/env python3
"""
Phase 1: FREE Error Remediation
================================
Archives structural errors and runs free tools on retryable errors.

Execute with: doppler run -- python scripts/phase1_free_remediation.py

Actions:
1. Archive DOL structural errors (29,740)
2. Archive CT parked errors (26)
3. Delete stale validation log (2)
4. MX re-verification on CT RETRY errors
5. Web scraping for email patterns

Cost: $0
"""

import os
import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from pathlib import Path
import dns.resolver
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

# Stats tracking
STATS = {
    "dol_archived": 0,
    "ct_parked_archived": 0,
    "validation_deleted": 0,
    "mx_checked": 0,
    "mx_valid": 0,
    "mx_invalid": 0,
    "domains_scraped": 0,
    "patterns_found": 0,
    "emails_discovered": 0,
    "ct_resolved": 0,
}


def log(msg, level="INFO"):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


# =============================================================================
# STEP 1: Archive DOL Structural Errors
# =============================================================================

def archive_dol_errors(conn):
    """Archive all PARKED DOL errors (NO_MATCH, NO_STATE)."""
    log("STEP 1: Archiving DOL structural errors...")

    with conn.cursor() as cur:
        # Mark PARKED errors as ARCHIVED (change disposition)
        cur.execute("""
            UPDATE outreach.dol_errors
            SET
                disposition = 'ARCHIVED',
                archived_at = NOW(),
                park_reason = COALESCE(park_reason, '') || ' [Phase 1 cleanup]'
            WHERE disposition = 'PARKED'
        """)

        STATS["dol_archived"] = cur.rowcount
        conn.commit()

    log(f"  Archived {STATS['dol_archived']:,} DOL errors")


# =============================================================================
# STEP 2: Archive CT Parked Errors
# =============================================================================

def archive_ct_parked_errors(conn):
    """Archive PARKED CT errors (retry exhausted)."""
    log("STEP 2: Archiving CT parked errors...")

    with conn.cursor() as cur:
        # Mark PARKED errors as ARCHIVED (change disposition)
        cur.execute("""
            UPDATE outreach.company_target_errors
            SET
                disposition = 'ARCHIVED',
                archived_at = NOW(),
                park_reason = COALESCE(park_reason, '') || ' [Phase 1 cleanup]'
            WHERE disposition = 'PARKED'
        """)

        STATS["ct_parked_archived"] = cur.rowcount
        conn.commit()

    log(f"  Archived {STATS['ct_parked_archived']:,} CT parked errors")


# =============================================================================
# STEP 3: Delete Stale Validation Log
# =============================================================================

def delete_stale_validation(conn):
    """Delete stale validation_failures_log entries from 2025."""
    log("STEP 3: Deleting stale validation log entries...")

    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM company.validation_failures_log
            WHERE created_at < '2026-01-01'
        """)

        STATS["validation_deleted"] = cur.rowcount
        conn.commit()

    log(f"  Deleted {STATS['validation_deleted']:,} stale validation entries")


# =============================================================================
# STEP 4: MX Re-verification
# =============================================================================

def verify_mx(domain: str) -> tuple:
    """Verify domain has MX records. Returns (domain, has_mx, mx_records)."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        mx_records = [str(r.exchange).rstrip('.') for r in answers]
        return (domain, True, mx_records)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return (domain, False, [])
    except Exception:
        return (domain, False, [])


def run_mx_verification(conn):
    """Re-verify MX records for CT RETRY errors."""
    log("STEP 4: Running MX re-verification on CT errors...")

    # Get domains from CT errors
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT ci.normalized_domain as domain
            FROM outreach.company_target_errors cte
            JOIN outreach.company_target ct ON cte.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            WHERE cte.disposition = 'RETRY'
              AND ci.normalized_domain IS NOT NULL
              AND ci.normalized_domain <> ''
        """)
        domains = [r['domain'] for r in cur.fetchall()]

    log(f"  Found {len(domains):,} unique domains to verify")

    if not domains:
        return {}

    # Verify MX in parallel
    mx_results = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(verify_mx, d): d for d in domains}

        for i, future in enumerate(as_completed(futures)):
            domain, has_mx, mx_records = future.result()
            mx_results[domain] = has_mx
            STATS["mx_checked"] += 1

            if has_mx:
                STATS["mx_valid"] += 1
            else:
                STATS["mx_invalid"] += 1

            if (i + 1) % 100 == 0:
                log(f"    Verified {i + 1}/{len(domains)} domains...")

    log(f"  MX valid: {STATS['mx_valid']:,}, MX invalid: {STATS['mx_invalid']:,}")

    return mx_results


# =============================================================================
# STEP 5: Web Scraping for Email Patterns
# =============================================================================

def extract_emails(html: str, domain: str) -> list:
    """Extract emails matching domain from HTML."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    found = re.findall(pattern, html.lower())
    return [e for e in set(found) if e.endswith(f"@{domain}")]


def extract_pattern(emails: list, domain: str) -> str:
    """Extract email pattern from sample emails."""
    if not emails:
        return None

    # Look for common patterns
    patterns = {}
    for email in emails:
        local = email.split('@')[0]

        # Check if it looks like first.last
        if '.' in local:
            parts = local.split('.')
            if len(parts) == 2 and parts[0].isalpha() and parts[1].isalpha():
                patterns['{first}.{last}'] = patterns.get('{first}.{last}', 0) + 1

        # Check if it looks like flast (first initial + last)
        elif len(local) > 2 and local[0].isalpha() and local[1:].isalpha():
            patterns['{f}{last}'] = patterns.get('{f}{last}', 0) + 1

    if patterns:
        return max(patterns, key=patterns.get)
    return None


def scrape_domain(domain: str) -> tuple:
    """Scrape domain for emails. Returns (domain, emails, pattern)."""
    urls = [
        f"https://{domain}",
        f"https://{domain}/contact",
        f"https://{domain}/about",
        f"https://{domain}/team",
        f"https://www.{domain}",
        f"https://www.{domain}/contact",
    ]

    all_emails = []

    for url in urls:
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                response = client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; EmailBot/1.0)'
                })
                if response.status_code == 200:
                    emails = extract_emails(response.text, domain)
                    all_emails.extend(emails)
        except Exception:
            continue

    unique_emails = list(set(all_emails))
    pattern = extract_pattern(unique_emails, domain) if unique_emails else None

    return (domain, unique_emails, pattern)


def run_web_scraping(conn, mx_results: dict):
    """Scrape websites for email patterns (only domains with valid MX)."""
    log("STEP 5: Running web scraping for email patterns...")

    # Filter to domains with valid MX
    valid_domains = [d for d, has_mx in mx_results.items() if has_mx]
    log(f"  Scraping {len(valid_domains):,} domains with valid MX")

    if not valid_domains:
        return {}

    # Scrape in parallel (but slower to avoid blocking)
    scrape_results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_domain, d): d for d in valid_domains[:500]}  # Limit to 500

        for i, future in enumerate(as_completed(futures)):
            domain, emails, pattern = future.result()
            STATS["domains_scraped"] += 1

            if emails:
                STATS["emails_discovered"] += len(emails)
            if pattern:
                STATS["patterns_found"] += 1
                scrape_results[domain] = {
                    'emails': emails,
                    'pattern': pattern
                }

            if (i + 1) % 50 == 0:
                log(f"    Scraped {i + 1}/{min(len(valid_domains), 500)} domains...")

    log(f"  Patterns found: {STATS['patterns_found']:,}")
    log(f"  Emails discovered: {STATS['emails_discovered']:,}")

    return scrape_results


# =============================================================================
# STEP 6: Update CT Records with Discovered Patterns
# =============================================================================

def update_ct_with_patterns(conn, scrape_results: dict):
    """Update company_target records with discovered patterns."""
    log("STEP 6: Updating CT records with discovered patterns...")

    if not scrape_results:
        log("  No patterns to update")
        return

    updated = 0

    with conn.cursor() as cur:
        for domain, data in scrape_results.items():
            pattern = data['pattern']

            # Update company_target for this domain
            cur.execute("""
                UPDATE outreach.company_target ct
                SET
                    email_method = %s,
                    method_type = 'scraped_pattern',
                    confidence_score = 0.6,
                    execution_status = 'ready',
                    imo_completed_at = NOW()
                FROM outreach.outreach o
                JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
                WHERE ct.outreach_id = o.outreach_id
                  AND ci.normalized_domain = %s
                  AND ct.email_method IS NULL
            """, (pattern, domain))

            updated += cur.rowcount

        conn.commit()

    STATS["ct_resolved"] = updated
    log(f"  Updated {updated:,} CT records with patterns")


# =============================================================================
# STEP 7: Resolve CT Errors for Fixed Records
# =============================================================================

def resolve_ct_errors(conn):
    """Mark CT errors as RESOLVED where CT is now ready."""
    log("STEP 7: Resolving CT errors for fixed records...")

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE outreach.company_target_errors cte
            SET
                disposition = 'RESOLVED',
                resolved_at = NOW(),
                resolution_note = 'Pattern discovered via Phase 1 free remediation'
            FROM outreach.company_target ct
            WHERE cte.outreach_id = ct.outreach_id
              AND cte.disposition = 'RETRY'
              AND ct.execution_status = 'ready'
              AND ct.email_method IS NOT NULL
        """)

        resolved = cur.rowcount
        conn.commit()

    log(f"  Resolved {resolved:,} CT errors")
    return resolved


# =============================================================================
# Report Generation
# =============================================================================

def generate_report() -> str:
    """Generate Phase 1 report."""

    report = f"""# Phase 1 FREE Remediation Report

**Execution Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
**Cost**: $0.00 (FREE)

---

## Actions Completed

### Step 1: Archive DOL Structural Errors
| Metric | Count |
|--------|-------|
| DOL errors archived | {STATS['dol_archived']:,} |

### Step 2: Archive CT Parked Errors
| Metric | Count |
|--------|-------|
| CT parked errors archived | {STATS['ct_parked_archived']:,} |

### Step 3: Delete Stale Validation Log
| Metric | Count |
|--------|-------|
| Stale entries deleted | {STATS['validation_deleted']:,} |

### Step 4: MX Re-verification
| Metric | Count |
|--------|-------|
| Domains checked | {STATS['mx_checked']:,} |
| MX valid | {STATS['mx_valid']:,} |
| MX invalid | {STATS['mx_invalid']:,} |

### Step 5: Web Scraping
| Metric | Count |
|--------|-------|
| Domains scraped | {STATS['domains_scraped']:,} |
| Patterns found | {STATS['patterns_found']:,} |
| Emails discovered | {STATS['emails_discovered']:,} |

### Step 6-7: CT Updates
| Metric | Count |
|--------|-------|
| CT records updated with patterns | {STATS['ct_resolved']:,} |

---

## Summary

| Category | Before | After | Change |
|----------|-------:|------:|-------:|
| DOL errors | 29,740 | 0 | -29,740 (archived) |
| CT parked | 26 | 0 | -26 (archived) |
| CT RETRY | 4,378 | ~{4378 - STATS['ct_resolved']:,} | -{STATS['ct_resolved']:,} (resolved) |
| Validation log | 2 | 0 | -2 (deleted) |

**Total errors archived/resolved**: {STATS['dol_archived'] + STATS['ct_parked_archived'] + STATS['ct_resolved'] + STATS['validation_deleted']:,}

---

## Remaining Work (Phase 2)

| Error Type | Remaining | Next Action |
|------------|----------:|-------------|
| CT RETRY | ~{4378 - STATS['ct_resolved']:,} | Apollo enrichment |
| People RETRY | 1,053 | Apollo enrichment |

---

**Generated by**: Phase 1 FREE Remediation Script
**Timestamp**: {datetime.now(timezone.utc).isoformat()}Z
"""

    return report


# =============================================================================
# Main
# =============================================================================

def main():
    """Run Phase 1 FREE remediation."""
    log("=" * 70)
    log("PHASE 1: FREE ERROR REMEDIATION")
    log("=" * 70)
    log("Cost: $0.00")
    log("")

    # Check environment
    required_vars = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    missing = [v for v in required_vars if v not in os.environ]
    if missing:
        log(f"Missing environment variables: {missing}", "ERROR")
        sys.exit(1)

    # Connect
    log("Connecting to Neon PostgreSQL...")
    try:
        conn = connect_db()
        log("Connected successfully")
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        sys.exit(1)

    try:
        # Step 1: Archive DOL errors
        log("-" * 70)
        archive_dol_errors(conn)

        # Step 2: Archive CT parked errors
        log("-" * 70)
        archive_ct_parked_errors(conn)

        # Step 3: Delete stale validation log
        log("-" * 70)
        delete_stale_validation(conn)

        # Step 4: MX verification
        log("-" * 70)
        mx_results = run_mx_verification(conn)

        # Step 5: Web scraping
        log("-" * 70)
        scrape_results = run_web_scraping(conn, mx_results)

        # Step 6: Update CT records
        log("-" * 70)
        update_ct_with_patterns(conn, scrape_results)

        # Step 7: Resolve CT errors
        log("-" * 70)
        resolve_ct_errors(conn)

        # Generate report
        log("-" * 70)
        log("Generating report...")
        report = generate_report()
        report_path = Path(__file__).parent.parent / "PHASE1_REMEDIATION_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        log(f"Report written to: {report_path}")

        # Final summary
        log("=" * 70)
        log("PHASE 1 COMPLETE")
        log("=" * 70)
        log(f"DOL archived: {STATS['dol_archived']:,}")
        log(f"CT parked archived: {STATS['ct_parked_archived']:,}")
        log(f"Validation deleted: {STATS['validation_deleted']:,}")
        log(f"MX verified: {STATS['mx_checked']:,} ({STATS['mx_valid']:,} valid)")
        log(f"Patterns found: {STATS['patterns_found']:,}")
        log(f"CT resolved: {STATS['ct_resolved']:,}")
        log(f"Total cost: $0.00")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
