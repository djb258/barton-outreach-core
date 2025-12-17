#!/usr/bin/env python3
"""
Email Pattern Discovery Pipeline
=================================
Orchestrates the full pattern discovery process:
1. Load companies needing patterns
2. Generate email guesses (FREE - local computation)
3. Smart batch verification (CHEAP - MillionVerifier)
4. Store discovered patterns to Neon
5. Apply patterns to generate emails

Cost Breakdown for 67,000 companies:
------------------------------------
Pattern Guessing:     $0 (local)
Verification:         ~$500-1000 (depends on discovery rate)
Total:               ~$500-1000 (vs $6,700+ with Hunter.io)

Smart Batching Strategy:
------------------------
- Priority 1 patterns first (first.last@domain.com - 35% success rate)
- Stop verifying company once pattern found
- Early termination = fewer verifications = lower cost

Expected Cost Model:
- Best case (50% find on P1): 67K * 1 = 67K verifications = ~$297
- Average case (find by P3): 67K * 2.5 = 167K verifications = ~$500
- Worst case (check all 8): 67K * 8 = 536K verifications = ~$1,000

Created: 2024-12-11
"""

import os
import csv
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import our modules
from pattern_guesser import (
    generate_verification_batch,
    estimate_verification_cost,
    apply_discovered_pattern,
    PatternType,
    PATTERN_PRIORITY
)


DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')


def load_companies_needing_patterns(limit: Optional[int] = None) -> Dict[str, Dict]:
    """
    Load companies from Neon that need email patterns discovered.

    Criteria:
    - Has domain
    - Does NOT have email_pattern set
    """
    import psycopg2

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    query = """
        SELECT
            company_unique_id,
            company_name,
            domain,
            email_pattern
        FROM marketing.company_master
        WHERE domain IS NOT NULL
          AND domain != ''
          AND (email_pattern IS NULL OR email_pattern = '')
    """

    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    companies = {}
    for row in rows:
        companies[row[0]] = {
            'company_id': row[0],
            'company_name': row[1],
            'domain': row[2],
            'email_pattern': row[3]
        }

    return companies


def load_people_with_slots(company_ids: List[str]) -> List[Dict]:
    """
    Load people who have slots at companies.
    We need at least one person per company to verify patterns.
    """
    import psycopg2

    if not company_ids:
        return []

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Get one person per company (preferably with slot_complete)
    placeholders = ','.join(['%s'] * len(company_ids))
    query = f"""
        SELECT DISTINCT ON (pm.company_unique_id)
            pm.unique_id,
            pm.full_name,
            pm.company_unique_id,
            pm.slot_complete
        FROM marketing.people_master pm
        WHERE pm.company_unique_id IN ({placeholders})
          AND pm.full_name IS NOT NULL
          AND pm.full_name != ''
        ORDER BY pm.company_unique_id, pm.slot_complete DESC NULLS LAST
    """

    cur.execute(query, company_ids)
    rows = cur.fetchall()
    conn.close()

    people = []
    for row in rows:
        people.append({
            'person_id': row[0],
            'full_name': row[1],
            'company_id': row[2],
            'slot_complete': row[3]
        })

    return people


def save_patterns_to_neon(patterns: Dict) -> int:
    """
    Save discovered patterns to company_master in Neon.
    """
    import psycopg2

    if not patterns:
        return 0

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    updated = 0
    for company_id, pattern_info in patterns.items():
        cur.execute("""
            UPDATE marketing.company_master
            SET email_pattern = %s,
                pattern_confidence = %s,
                updated_at = NOW()
            WHERE company_unique_id = %s
        """, (pattern_info.pattern, pattern_info.confidence, company_id))
        updated += cur.rowcount

    conn.commit()
    conn.close()

    return updated


def generate_smart_batch(
    companies: Dict[str, Dict],
    people: List[Dict],
    max_patterns: int = 3
) -> List[Dict]:
    """
    Generate a smart batch of email guesses.

    Strategy: Only generate top N patterns per company to minimize cost.
    Most companies will be found in first 1-3 patterns.
    """
    from pattern_guesser import generate_all_email_guesses

    batch = []

    # Create person lookup by company
    people_by_company = {}
    for person in people:
        cid = person.get('company_id')
        if cid and cid not in people_by_company:
            people_by_company[cid] = person

    for company_id, company in companies.items():
        domain = company.get('domain')
        if not domain:
            continue

        # Get a person from this company
        person = people_by_company.get(company_id)
        if not person:
            continue

        # Generate guesses (limited to max_patterns)
        guesses = generate_all_email_guesses(person['full_name'], domain)

        for guess in guesses[:max_patterns]:
            batch.append({
                'person_id': person.get('person_id'),
                'full_name': person.get('full_name'),
                'company_id': company_id,
                'company_name': company.get('company_name', ''),
                'domain': domain,
                'email': guess.email,
                'pattern': guess.pattern.value,
                'priority': guess.priority
            })

    return batch


async def run_pattern_discovery(
    limit: Optional[int] = None,
    max_patterns_per_company: int = 3,
    dry_run: bool = False,
    output_dir: str = None
) -> Dict:
    """
    Main pipeline entry point.

    Args:
        limit: Max companies to process (for testing)
        max_patterns_per_company: How many patterns to try before giving up
        dry_run: If True, don't call API or update database
        output_dir: Where to save results

    Returns:
        Pipeline results dict
    """
    output_dir = output_dir or os.path.join(
        os.path.dirname(__file__),
        '..', '..', 'output'
    )
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("EMAIL PATTERN DISCOVERY PIPELINE")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Dry run: {dry_run}")
    print(f"Max patterns per company: {max_patterns_per_company}")

    # Step 1: Load companies
    print("\n" + "=" * 70)
    print("STEP 1: Loading companies needing patterns")
    print("=" * 70)

    companies = load_companies_needing_patterns(limit)
    print(f"  Companies without patterns: {len(companies):,}")

    if not companies:
        print("  [!] No companies need pattern discovery")
        return {'status': 'no_work', 'companies': 0}

    # Step 2: Load people
    print("\n" + "=" * 70)
    print("STEP 2: Loading people for pattern verification")
    print("=" * 70)

    company_ids = list(companies.keys())
    people = load_people_with_slots(company_ids)
    print(f"  People available: {len(people):,}")

    companies_with_people = set(p['company_id'] for p in people)
    companies_without_people = set(company_ids) - companies_with_people
    print(f"  Companies with people: {len(companies_with_people):,}")
    print(f"  Companies without people: {len(companies_without_people):,}")

    # Step 3: Generate smart batch
    print("\n" + "=" * 70)
    print("STEP 3: Generating email guesses")
    print("=" * 70)

    batch = generate_smart_batch(companies, people, max_patterns_per_company)
    print(f"  Total guesses: {len(batch):,}")

    # Cost estimate
    cost_estimate = estimate_verification_cost(len(batch), 1)
    print(f"  Estimated cost: {cost_estimate['estimated_cost']}")
    print(f"  Cost per company: ${float(cost_estimate['estimated_cost'].replace('$', '')) / len(companies_with_people):.4f}")

    # Save batch for review
    batch_path = os.path.join(output_dir, 'pattern_discovery_batch.csv')
    with open(batch_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'company_id', 'company_name', 'domain', 'person_id',
            'full_name', 'email', 'pattern', 'priority'
        ])
        writer.writeheader()
        writer.writerows(batch)
    print(f"  Saved batch to: {batch_path}")

    if dry_run:
        print("\n[DRY RUN] Skipping verification and database updates")
        return {
            'status': 'dry_run',
            'companies': len(companies),
            'people': len(people),
            'guesses': len(batch),
            'estimated_cost': cost_estimate['estimated_cost']
        }

    # Step 4: Verify emails
    print("\n" + "=" * 70)
    print("STEP 4: Verifying emails with MillionVerifier")
    print("=" * 70)

    from bulk_verifier import verify_batch

    api_key = os.getenv('MILLIONVERIFIER_API_KEY')
    if not api_key:
        print("  [ERROR] MILLIONVERIFIER_API_KEY not set")
        return {'status': 'error', 'error': 'API key not configured'}

    discovered_patterns = {}

    def on_discovery(pattern):
        print(f"    [OK] {pattern.domain} -> {pattern.pattern}")

    results, discovered_patterns = await verify_batch(
        batch,
        api_key,
        discovered_patterns,
        on_pattern_discovered=on_discovery
    )

    print(f"\n  Verifications performed: {len(results):,}")
    print(f"  Patterns discovered: {len(discovered_patterns):,}")

    # Step 5: Save to Neon
    print("\n" + "=" * 70)
    print("STEP 5: Saving discovered patterns to Neon")
    print("=" * 70)

    updated = save_patterns_to_neon(discovered_patterns)
    print(f"  Companies updated: {updated:,}")

    # Save results
    results_path = os.path.join(output_dir, 'pattern_discovery_results.json')
    with open(results_path, 'w') as f:
        json.dump({
            'discovered_patterns': {
                k: {
                    'domain': v.domain,
                    'pattern': v.pattern,
                    'verified_email': v.verified_email,
                    'confidence': v.confidence
                }
                for k, v in discovered_patterns.items()
            },
            'stats': {
                'companies_processed': len(companies),
                'patterns_discovered': len(discovered_patterns),
                'verifications_performed': len(results),
                'discovery_rate': f"{len(discovered_patterns) / len(companies_with_people) * 100:.1f}%"
            }
        }, f, indent=2)
    print(f"  Saved results to: {results_path}")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Companies processed: {len(companies):,}")
    print(f"  Patterns discovered: {len(discovered_patterns):,}")
    print(f"  Discovery rate: {len(discovered_patterns) / len(companies_with_people) * 100:.1f}%")
    print(f"  Verifications used: {len(results):,}")
    print(f"  Companies updated in Neon: {updated:,}")

    return {
        'status': 'success',
        'companies': len(companies),
        'patterns_discovered': len(discovered_patterns),
        'verifications': len(results),
        'updated': updated,
        'discovery_rate': f"{len(discovered_patterns) / len(companies_with_people) * 100:.1f}%"
    }


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Email Pattern Discovery Pipeline')
    parser.add_argument('--limit', type=int, help='Max companies to process')
    parser.add_argument('--patterns', type=int, default=3, help='Max patterns per company (default: 3)')
    parser.add_argument('--dry-run', action='store_true', help='Generate batch without calling API')
    parser.add_argument('--output', type=str, help='Output directory')

    args = parser.parse_args()

    result = asyncio.run(run_pattern_discovery(
        limit=args.limit,
        max_patterns_per_company=args.patterns,
        dry_run=args.dry_run,
        output_dir=args.output
    ))

    print(f"\nFinal Result: {result}")
