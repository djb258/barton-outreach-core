#!/usr/bin/env python3
"""
Domain Quality Audit & Cleanup.

Detects and flags bad domains in outreach.outreach using 3 signals:
  1. BLOCKLIST  — Known PEOs, carriers, big corps, data vendors
  2. MULTI-USE  — Same domain assigned to 3+ different company names
  3. NAME-MISS  — Domain root has zero word overlap with company name

Can scope to a coverage_id (market) or run spine-wide.
In live mode, NULLs bad domains in outreach.outreach so Google Places
can re-discover real ones.

Usage:
    doppler run -- python scripts/domain_quality_audit.py --dry-run
    doppler run -- python scripts/domain_quality_audit.py --coverage-id <id> --dry-run
    doppler run -- python scripts/domain_quality_audit.py --coverage-id <id>
    doppler run -- python scripts/domain_quality_audit.py --spine-wide --dry-run
"""
import os
import sys
import io
import re
import csv
import argparse
from datetime import datetime, timezone
from collections import Counter

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

# ── Signal 1: BLOCKLIST ──────────────────────────────────────────────
# PEOs (Professional Employer Organizations)
PEOS = {
    'trinet.com', 'adp.com', 'paychex.com', 'insperity.com', 'justworks.com',
    'oasisadvantage.com', 'papaya.com', 'deel.com', 'rippling.com',
    'gusto.com', 'zenefits.com', 'bamboohr.com', 'namely.com',
    'paylocity.com', 'paycom.com', 'ceridian.com', 'ultimatesoftware.com',
    'accuchex.com', 'adpemploymentreport.com', 'myworkday.com',
}

# Insurance carriers / brokers
CARRIERS = {
    'chubb.com', 'allstate.com', 'statefarm.com', 'progressive.com',
    'geico.com', 'travelers.com', 'nationwide.com', 'libertymutual.com',
    'metlife.com', 'prudential.com', 'cigna.com', 'aetna.com',
    'anthem.com', 'humana.com', 'unitedhealthgroup.com', 'uhc.com',
    'bcbs.com', 'bluecross.com', 'blueshield.com', 'kaiserpermanente.org',
    'hartfordlife.com', 'thehartford.com', 'aflac.com', 'unum.com',
    'lincoln.com', 'lincolnfinancial.com', 'sunlife.com', 'guardianlife.com',
    'mutual-of-omaha.com', 'principalfinancial.com', 'principal.com',
    'massgeneral.org', 'voya.com', 'transamerica.com', 'empower.com',
    'fidelity.com', 'tiaa.org', 'valic.com', 'johnhancock.com',
    'greatwestlife.com',
}

# Big corps / Fortune 500 / tech giants that small companies can't be
BIG_CORPS = {
    'apple.com', 'microsoft.com', 'google.com', 'amazon.com', 'meta.com',
    'facebook.com', 'netflix.com', 'tesla.com', 'nvidia.com', 'intel.com',
    'ibm.com', 'oracle.com', 'cisco.com', 'adobe.com', 'salesforce.com',
    'sap.com', 'vmware.com', 'dell.com', 'hp.com', 'hpe.com', 'hpinc.com',
    'qualcomm.com', 'broadcom.com', 'servicenow.com',
    'disney.com', 'waltdisney.com', 'nbcuniversal.com', 'warnerbros.com',
    'coca-colacompany.com', 'pepsico.com', 'nestle.com', 'unilever.com',
    'pg.com', 'jnj.com', 'pfizer.com', 'merck.com', 'abbvie.com',
    'walmart.com', 'samsclub.com', 'target.com', 'costco.com', 'kroger.com',
    'homedepot.com', 'lowes.com', 'bestbuy.com',
    'jpmorgan.com', 'jpmorganchase.com', 'bankofamerica.com', 'wellsfargo.com',
    'goldmansachs.com', 'morganstanley.com', 'citi.com', 'citigroup.com',
    'ge.com', 'boeing.com', 'lockheedmartin.com', 'northropgrumman.com',
    'raytheon.com', 'l3harris.com', 'generaldynamics.com',
    'exxonmobil.com', 'chevron.com', 'shell.com', 'bp.com',
    'att.com', 'verizon.com', 'tmobile.com', 'comcast.com', 'charter.com',
    'fedex.com', 'ups.com', 'usps.com',
    'marriott.com', 'hilton.com', 'hyatt.com', 'ihg.com',
    'mcdonalds.com', 'starbucks.com', 'yum.com', 'dominos.com',
    'ford.com', 'gm.com', 'stellantis.com', 'toyota.com', 'honda.com',
    'nucor.com', 'caterpillar.com', 'deere.com', '3m.com',
    'motorolasolutions.com', 'motorola.com',
    'illumina.com', 'thermofisher.com',
    'acme.com', 'king.com', 'best.com',  # generic domains mismatched to local cos
    'mlb.com', 'nfl.com', 'nba.com', 'nhl.com',
    'hearst.com', 'gannett.com', 'meredith.com',
    'mantech.com', 'agiledefense.com',
    'turnerconstruction.com', 'aecom.com', 'jacobs.com',
}

# Data vendors / enrichment tools (not real company domains)
DATA_VENDORS = {
    'seamless.ai', 'rocketreach.co', 'zoominfo.com', 'apollo.io',
    'lusha.com', 'clearbit.com', 'hunter.io', 'snov.io', 'findthat.email',
    'voilanorbert.com', 'anymail.io', 'emailhunter.co',
    'healthgrades.com', 'guidestar.org', 'propublica.org',
    'marketsizeandtrends.com',  # SEO spam domain
    'uschamber.com',
}

# Government / education TLDs
GOV_EDU_TLDS = {'.gov', '.edu', '.mil'}

ALL_BLOCKLIST = PEOS | CARRIERS | BIG_CORPS | DATA_VENDORS
MULTI_USE_THRESHOLD = 3  # domains used by this many different company names = flagged


def get_conn():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        dbname=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require',
    )


SUFFIX_WORDS = {
    'LLC', 'INC', 'INCORPORATED', 'CORP', 'CORPORATION', 'COMPANY', 'CO',
    'LTD', 'LIMITED', 'LP', 'LLP', 'PC', 'PA', 'PLLC', 'GROUP', 'HOLDINGS',
    'SERVICES', 'ENTERPRISES', 'ASSOCIATES', 'INTERNATIONAL', 'THE', 'OF',
    'AND', 'A', 'AN', 'IN', 'FOR', 'AT', 'BY', 'DBA',
}


def domain_root_words(domain):
    """Extract meaningful words from a domain for name matching."""
    if not domain:
        return set()
    # Strip TLD
    parts = domain.split('.')
    if len(parts) >= 2:
        root = parts[0]
    else:
        root = domain
    # Split camelCase or hyphens
    words = re.split(r'[-_]', root)
    # Only words 3+ chars
    return {w.upper() for w in words if len(w) >= 3}


def domain_root_clean(domain):
    """Get clean alphanumeric root of domain for abbreviation checks."""
    if not domain:
        return ''
    parts = domain.split('.')
    root = parts[0] if parts else domain
    return re.sub(r'[^A-Z0-9]', '', root.upper())


def company_name_words(name):
    """Extract meaningful words from company name."""
    if not name:
        return set()
    n = re.sub(r'[^A-Z0-9 ]', '', name.upper())
    words = n.split()
    return {w for w in words if len(w) >= 3 and w not in SUFFIX_WORDS}


def company_name_meaningful(name):
    """Get meaningful words (2+ chars) for abbreviation building."""
    if not name:
        return []
    n = re.sub(r'[^A-Z0-9 ]', '', name.upper())
    words = n.split()
    return [w for w in words if len(w) >= 2 and w not in SUFFIX_WORDS]


def is_abbreviation_domain(name, domain):
    """Check if domain looks like an abbreviation of the company name."""
    root = domain_root_clean(domain)
    if not root or not name:
        return False

    meaningful = company_name_meaningful(name)
    if not meaningful:
        return False

    # Check 1: domain root starts with initials of company name
    initials = ''.join(w[0] for w in meaningful)
    if len(initials) >= 2 and (root.startswith(initials) or initials.startswith(root)):
        return True

    # Check 2: domain root is a substring of concatenated company name
    name_concat = re.sub(r'[^A-Z0-9]', '', name.upper())
    if len(root) >= 3 and root in name_concat:
        return True

    # Check 3: company first word matches domain root start (or vice versa)
    first = re.sub(r'[^A-Z0-9]', '', meaningful[0]) if meaningful else ''
    if first and len(first) >= 3 and (root.startswith(first) or first.startswith(root)):
        return True

    # Check 4: any company word (4+ chars) is contained in domain root
    for w in meaningful:
        if len(w) >= 4 and w in root:
            return True

    return False


def main():
    parser = argparse.ArgumentParser(description='Domain quality audit & cleanup')
    parser.add_argument('--dry-run', action='store_true', help='Report only, no DB changes')
    parser.add_argument('--coverage-id', default=None, help='Scope to a market')
    parser.add_argument('--spine-wide', action='store_true', help='Audit entire spine')
    args = parser.parse_args()

    if not args.coverage_id and not args.spine_wide:
        print("ERROR: Specify --coverage-id <id> or --spine-wide")
        sys.exit(1)

    print("=" * 60)
    print("Domain Quality Audit")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE — will NULL bad domains'}")
    print(f"Scope: {'Spine-wide' if args.spine_wide else f'Coverage {args.coverage_id}'}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)

    conn = get_conn()
    cur = conn.cursor()

    # ── Build scope ───────────────────────────────────────────
    if args.spine_wide:
        cur.execute("""
            SELECT o.outreach_id::text, ci.company_name, LOWER(TRIM(o.domain)),
                   ci.source_system
            FROM outreach.outreach o
            JOIN cl.company_identity ci ON o.sovereign_id = ci.company_unique_id
            WHERE o.domain IS NOT NULL AND o.domain != ''
            ORDER BY ci.company_name
        """)
    else:
        cur.execute('SELECT zip FROM coverage.v_service_agent_coverage_zips WHERE coverage_id = %s',
                    (args.coverage_id,))
        zips = [r[0] for r in cur.fetchall()]
        if not zips:
            print("ERROR: No ZIPs for coverage_id")
            sys.exit(1)

        cur.execute("""
            SELECT DISTINCT UPPER(TRIM(ct.state))
            FROM outreach.company_target ct
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND ct.state IS NOT NULL
        """, (zips,))
        states = [r[0] for r in cur.fetchall() if r[0] and len(r[0]) == 2]

        cur.execute("""
            SELECT o.outreach_id::text, ci.company_name, LOWER(TRIM(o.domain)),
                   ci.source_system
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            JOIN cl.company_identity ci ON ct.company_unique_id = ci.company_unique_id::text
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND UPPER(TRIM(ct.state)) = ANY(%s)
              AND o.domain IS NOT NULL AND o.domain != ''
            ORDER BY ci.company_name
        """, (zips, states))

    rows = cur.fetchall()
    print(f"\n  Companies with domain in scope: {len(rows):,}")

    # ── Build multi-use map (spine-wide, always) ──────────────
    cur.execute("""
        SELECT LOWER(TRIM(o.domain)), COUNT(DISTINCT ci.company_name)
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_id = ci.company_unique_id
        WHERE o.domain IS NOT NULL AND o.domain != ''
        GROUP BY LOWER(TRIM(o.domain))
        HAVING COUNT(DISTINCT ci.company_name) >= %s
    """, (MULTI_USE_THRESHOLD,))
    multi_use_domains = {r[0]: r[1] for r in cur.fetchall()}
    print(f"  Multi-use domains (>={MULTI_USE_THRESHOLD} companies): {len(multi_use_domains):,}")

    # ── Classify each row ─────────────────────────────────────
    flagged = []  # (outreach_id, company_name, domain, reason, source_system)
    clean = 0

    for oid, name, domain, source in rows:
        if not domain:
            clean += 1
            continue

        reasons = []

        # Signal 1: Blocklist
        if domain in ALL_BLOCKLIST:
            if domain in PEOS:
                reasons.append('BLOCKLIST:PEO')
            elif domain in CARRIERS:
                reasons.append('BLOCKLIST:CARRIER')
            elif domain in BIG_CORPS:
                reasons.append('BLOCKLIST:BIG_CORP')
            elif domain in DATA_VENDORS:
                reasons.append('BLOCKLIST:DATA_VENDOR')

        # Signal 1b: Gov/edu TLD
        for tld in GOV_EDU_TLDS:
            if domain.endswith(tld):
                reasons.append(f'BLOCKLIST:TLD_{tld.upper().strip(".")}')
                break

        # Signal 2: Multi-use
        if domain in multi_use_domains:
            reasons.append(f'MULTI_USE:{multi_use_domains[domain]}_companies')

        # Signal 3: Name mismatch (only if not already flagged)
        if not reasons:
            d_words = domain_root_words(domain)
            n_words = company_name_words(name)
            if d_words and n_words and not (d_words & n_words):
                # Check if domain is an abbreviation of company name
                if is_abbreviation_domain(name, domain):
                    pass  # Abbreviation match — skip
                else:
                    reasons.append('NAME_MISMATCH')

        if reasons:
            flagged.append((oid, name, domain, '|'.join(reasons), source))
        else:
            clean += 1

    # ── Report ────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"  Total in scope:    {len(rows):,}")
    print(f"  Clean:             {clean:,}")
    print(f"  Flagged:           {len(flagged):,} ({100*len(flagged)/max(len(rows),1):.1f}%)")

    # Breakdown by reason
    reason_counts = Counter()
    for _, _, _, reasons, _ in flagged:
        for r in reasons.split('|'):
            tag = r.split(':')[0] if ':' in r else r
            reason_counts[tag] += 1

    print(f"\n  By signal:")
    for tag, cnt in reason_counts.most_common():
        print(f"    {tag}: {cnt:,}")

    # Breakdown by source system
    source_counts = Counter()
    for _, _, _, _, src in flagged:
        source_counts[src or 'unknown'] += 1

    print(f"\n  By source system:")
    for src, cnt in source_counts.most_common():
        print(f"    {src}: {cnt:,}")

    # Sample flagged
    print(f"\n  Sample flagged (first 25):")
    for oid, name, domain, reasons, src in flagged[:25]:
        print(f"    {name[:40]:<40} {domain:<30} {reasons}")

    # ── Export CSV ────────────────────────────────────────────
    scope_label = 'spine' if args.spine_wide else args.coverage_id[:8]
    csv_path = f"exports/domain_audit_{scope_label}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['outreach_id', 'company_name', 'bad_domain', 'flag_reason', 'source_system'])
        for row in flagged:
            w.writerow(row)
    print(f"\n  Exported flagged to: {csv_path}")

    # ── Clean (LIVE mode) ────────────────────────────────────
    if not args.dry_run and flagged:
        print(f"\n{'=' * 60}")
        print("CLEANUP: Nulling bad domains in outreach.outreach")
        print(f"{'=' * 60}")

        nulled = 0
        for oid, name, domain, reasons, src in flagged:
            try:
                cur.execute("""
                    UPDATE outreach.outreach
                    SET domain = NULL
                    WHERE outreach_id = %s::uuid AND LOWER(TRIM(domain)) = %s
                """, (oid, domain))
                if cur.rowcount > 0:
                    nulled += 1
                if nulled % 500 == 0 and nulled > 0:
                    conn.commit()
                    print(f"    ... nulled {nulled:,}")
            except Exception as e:
                print(f"    ERROR {oid}: {e}")
                conn.rollback()

        conn.commit()
        print(f"  Domains nulled: {nulled:,}")

        # Verify
        if args.spine_wide:
            cur.execute("""
                SELECT COUNT(*) FROM outreach.outreach
                WHERE domain IS NOT NULL AND domain != ''
            """)
        else:
            cur.execute("""
                SELECT COUNT(*)
                FROM outreach.company_target ct
                JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
                WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
                  AND UPPER(TRIM(ct.state)) = ANY(%s)
                  AND (o.domain IS NULL OR o.domain = '')
            """, (zips, states))
        remaining_no_domain = cur.fetchone()[0]
        print(f"  Now without domain in scope: {remaining_no_domain:,}")

    elif args.dry_run and flagged:
        print(f"\n  DRY RUN — no changes made. Run without --dry-run to null {len(flagged):,} bad domains.")

    conn.close()


if __name__ == '__main__':
    main()
