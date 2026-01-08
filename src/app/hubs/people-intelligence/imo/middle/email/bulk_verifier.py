#!/usr/bin/env python3
"""
Bulk Email Verifier - MillionVerifier Integration
==================================================
Verifies email guesses in bulk using MillionVerifier API.
Discovers company patterns by finding the first valid email.

Cost: ~$37/10,000 verifications (MillionVerifier bulk rate)

Strategy:
1. Take batch of email guesses (sorted by priority)
2. Verify in chunks (avoid rate limits)
3. First valid email per company = discovered pattern
4. Stop verifying other patterns for that company
5. Return discovered patterns + verified emails

Created: 2024-12-11
"""

import os
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# MillionVerifier API
MILLIONVERIFIER_API_KEY = os.getenv('MILLIONVERIFIER_API_KEY')
MILLIONVERIFIER_SINGLE_URL = "https://api.millionverifier.com/api/v3/"
MILLIONVERIFIER_BULK_URL = "https://api.millionverifier.com/api/v3/bulkapi"

# Rate limiting
BATCH_SIZE = 100  # Emails per batch
BATCH_DELAY = 1.0  # Seconds between batches
MAX_CONCURRENT = 10  # Max concurrent requests


@dataclass
class VerificationResult:
    """Result of email verification"""
    email: str
    result: str  # 'ok', 'invalid', 'unknown', 'catch_all', etc.
    result_code: int
    is_valid: bool
    is_catch_all: bool
    is_disposable: bool
    is_free: bool
    is_role: bool
    credits_used: int
    verified_at: str


@dataclass
class PatternDiscovery:
    """Discovered email pattern for a company"""
    company_id: str
    company_name: str
    domain: str
    pattern: str
    verified_email: str
    verified_person: str
    confidence: float
    discovered_at: str


async def verify_single_email(
    session: aiohttp.ClientSession,
    email: str,
    api_key: str
) -> Optional[VerificationResult]:
    """
    Verify a single email using MillionVerifier API.
    """
    url = f"{MILLIONVERIFIER_SINGLE_URL}?api={api_key}&email={email}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()

                # Parse result
                result = data.get('result', 'unknown')
                result_code = data.get('resultcode', 0)

                # Determine validity
                is_valid = result.lower() in ['ok', 'valid', 'deliverable']
                is_catch_all = result.lower() in ['catch_all', 'accept_all']

                return VerificationResult(
                    email=email,
                    result=result,
                    result_code=result_code,
                    is_valid=is_valid,
                    is_catch_all=is_catch_all,
                    is_disposable=data.get('disposable', False),
                    is_free=data.get('free', False),
                    is_role=data.get('role', False),
                    credits_used=data.get('credits', 1),
                    verified_at=datetime.now().isoformat()
                )
            else:
                print(f"  [WARN] API error for {email}: {response.status}")
                return None

    except asyncio.TimeoutError:
        print(f"  [WARN] Timeout for {email}")
        return None
    except Exception as e:
        print(f"  [WARN] Error verifying {email}: {e}")
        return None


async def verify_batch(
    guesses: List[Dict],
    api_key: str,
    discovered_patterns: Dict[str, PatternDiscovery],
    on_pattern_discovered: Optional[callable] = None
) -> Tuple[List[VerificationResult], Dict[str, PatternDiscovery]]:
    """
    Verify a batch of email guesses.
    Stops verifying additional patterns for a company once one is found.

    Args:
        guesses: List of email guesses (sorted by priority)
        api_key: MillionVerifier API key
        discovered_patterns: Already discovered patterns (company_id -> pattern)
        on_pattern_discovered: Callback when pattern is discovered

    Returns:
        Tuple of (verification results, discovered patterns)
    """
    results = []
    companies_to_skip = set(discovered_patterns.keys())

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(guesses), BATCH_SIZE):
            batch = guesses[i:i + BATCH_SIZE]

            # Filter out companies we've already found patterns for
            batch = [g for g in batch if g['company_id'] not in companies_to_skip]

            if not batch:
                continue

            print(f"  [BATCH] Verifying batch {i // BATCH_SIZE + 1}: {len(batch)} emails")

            # Create tasks for concurrent verification
            tasks = []
            for guess in batch:
                task = verify_single_email(session, guess['email'], api_key)
                tasks.append((guess, task))

            # Execute with limited concurrency
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)

            async def limited_verify(guess, task):
                async with semaphore:
                    return guess, await task

            batch_results = await asyncio.gather(
                *[limited_verify(g, t) for g, t in tasks],
                return_exceptions=True
            )

            # Process results
            for item in batch_results:
                if isinstance(item, Exception):
                    continue

                guess, result = item
                if result is None:
                    continue

                results.append(result)

                # Check if we discovered a valid pattern
                if result.is_valid or result.is_catch_all:
                    company_id = guess['company_id']

                    if company_id not in discovered_patterns:
                        discovery = PatternDiscovery(
                            company_id=company_id,
                            company_name=guess.get('company_name', ''),
                            domain=guess['domain'],
                            pattern=guess['pattern'],
                            verified_email=result.email,
                            verified_person=guess.get('full_name', ''),
                            confidence=0.95 if result.is_valid else 0.75,
                            discovered_at=datetime.now().isoformat()
                        )

                        discovered_patterns[company_id] = discovery
                        companies_to_skip.add(company_id)

                        print(f"    [OK] Pattern discovered: {guess['domain']} -> {guess['pattern']}")

                        if on_pattern_discovered:
                            on_pattern_discovered(discovery)

            # Rate limit delay
            if i + BATCH_SIZE < len(guesses):
                await asyncio.sleep(BATCH_DELAY)

    return results, discovered_patterns


def sort_guesses_by_priority(guesses: List[Dict]) -> List[Dict]:
    """
    Sort guesses to maximize pattern discovery efficiency.
    Groups by company, then sorts by pattern priority within each company.
    """
    # Group by company
    by_company = {}
    for guess in guesses:
        company_id = guess['company_id']
        if company_id not in by_company:
            by_company[company_id] = []
        by_company[company_id].append(guess)

    # Sort each company's guesses by priority
    for company_id in by_company:
        by_company[company_id].sort(key=lambda x: x['priority'])

    # Interleave companies (try one pattern from each, then next pattern, etc.)
    # This maximizes pattern discovery across companies
    sorted_guesses = []
    max_priority = max(g['priority'] for g in guesses) if guesses else 0

    for priority in range(max_priority + 1):
        for company_id in by_company:
            company_guesses = by_company[company_id]
            for guess in company_guesses:
                if guess['priority'] == priority:
                    sorted_guesses.append(guess)
                    break

    return sorted_guesses


async def discover_patterns_for_companies(
    people: List[Dict],
    companies: Dict[str, Dict],
    api_key: str = None,
    max_verifications: int = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, any]:
    """
    Main entry point: Discover email patterns for companies.

    Args:
        people: List of person dicts with company assignments
        companies: Dict of company_id -> company info
        api_key: MillionVerifier API key (uses env var if not provided)
        max_verifications: Stop after this many (for testing/cost control)
        progress_callback: Called with progress updates

    Returns:
        {
            'discovered_patterns': {company_id: PatternDiscovery},
            'verification_results': [VerificationResult],
            'stats': {
                'total_people': int,
                'total_companies': int,
                'patterns_discovered': int,
                'verifications_performed': int,
                'estimated_cost': str
            }
        }
    """
    from .pattern_guesser import generate_verification_batch, estimate_verification_cost

    api_key = api_key or MILLIONVERIFIER_API_KEY
    if not api_key:
        raise ValueError("MillionVerifier API key required. Set MILLIONVERIFIER_API_KEY env var.")

    print("=" * 60)
    print("Email Pattern Discovery")
    print("=" * 60)

    # Generate all guesses
    print("\n📊 Generating email guesses...")
    guesses = generate_verification_batch(people, companies)
    print(f"   Total guesses: {len(guesses):,}")

    # Sort for efficiency
    guesses = sort_guesses_by_priority(guesses)

    # Apply max limit
    if max_verifications and len(guesses) > max_verifications:
        print(f"   Limiting to {max_verifications:,} verifications")
        guesses = guesses[:max_verifications]

    # Cost estimate
    unique_companies = len(set(g['company_id'] for g in guesses))
    cost = estimate_verification_cost(len(guesses), 1)  # 1 because guesses already expanded
    print(f"   Companies: {unique_companies:,}")
    print(f"   Estimated cost: {cost['estimated_cost']}")

    # Verify
    print("\n🔍 Starting verification...")
    discovered_patterns = {}
    results, discovered_patterns = await verify_batch(
        guesses,
        api_key,
        discovered_patterns,
        on_pattern_discovered=progress_callback
    )

    # Stats
    stats = {
        'total_people': len(people),
        'total_companies': unique_companies,
        'patterns_discovered': len(discovered_patterns),
        'verifications_performed': len(results),
        'estimated_cost': cost['estimated_cost'],
        'discovery_rate': f"{len(discovered_patterns) / unique_companies * 100:.1f}%" if unique_companies else "0%"
    }

    print("\n" + "=" * 60)
    print("Discovery Complete!")
    print("=" * 60)
    print(f"   Patterns discovered: {stats['patterns_discovered']} / {stats['total_companies']} companies")
    print(f"   Discovery rate: {stats['discovery_rate']}")
    print(f"   Verifications used: {stats['verifications_performed']:,}")
    print(f"   Estimated cost: {stats['estimated_cost']}")

    return {
        'discovered_patterns': discovered_patterns,
        'verification_results': results,
        'stats': stats
    }


def save_discovered_patterns(patterns: Dict[str, PatternDiscovery], output_path: str):
    """Save discovered patterns to file"""
    data = {k: asdict(v) for k, v in patterns.items()}

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[SAVE] Saved {len(patterns)} patterns to {output_path}")


def load_discovered_patterns(input_path: str) -> Dict[str, PatternDiscovery]:
    """Load previously discovered patterns"""
    with open(input_path, 'r') as f:
        data = json.load(f)

    return {k: PatternDiscovery(**v) for k, v in data.items()}


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Bulk Email Verifier - MillionVerifier")
    print("=" * 60)

    # Check API key
    if not MILLIONVERIFIER_API_KEY:
        print("\n[ERROR] MILLIONVERIFIER_API_KEY not set in environment")
        print("   Set it in your .env file or export it")
        sys.exit(1)

    print(f"\n[OK] API Key configured: {MILLIONVERIFIER_API_KEY[:8]}...")

    # Test with a sample
    print("\n[TEST] Running test verification...")

    async def test():
        from .pattern_guesser import generate_all_email_guesses

        # Test data
        test_people = [
            {'person_id': 'TEST-001', 'full_name': 'John Smith', 'company_id': 'COMP-001'},
        ]
        test_companies = {
            'COMP-001': {'company_name': 'Anthropic', 'domain': 'anthropic.com'}
        }

        # Generate guesses
        guesses = []
        for person in test_people:
            company = test_companies.get(person['company_id'], {})
            all_guesses = generate_all_email_guesses(
                person['full_name'],
                company.get('domain', '')
            )
            for guess in all_guesses[:3]:  # Only test first 3 patterns
                guesses.append({
                    'person_id': person['person_id'],
                    'full_name': person['full_name'],
                    'company_id': person['company_id'],
                    'company_name': company.get('company_name', ''),
                    'domain': company.get('domain', ''),
                    'email': guess.email,
                    'pattern': guess.pattern.value,
                    'priority': guess.priority
                })

        print(f"\n   Testing {len(guesses)} email guesses...")

        # Verify (limit to 3 to save credits)
        discovered = {}
        results, discovered = await verify_batch(
            guesses[:3],
            MILLIONVERIFIER_API_KEY,
            discovered
        )

        print(f"\n   Results: {len(results)} verified")
        for r in results:
            status = "✅" if r.is_valid else "❌"
            print(f"   {status} {r.email}: {r.result}")

    asyncio.run(test())
