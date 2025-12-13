"""
Test Enrichment System - Quick validation run
Tests Firecrawl integration with 10 companies from the validation queue.

Usage:
    python test_enrichment.py
    python test_enrichment.py --dry-run
    python test_enrichment.py --max 5

Barton Doctrine ID: 04.04.02.04.enrichment.test
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    # Load .env from repo root
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
except ImportError:
    print("WARNING: python-dotenv not installed")

# Check for required dependencies
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

from enrichment_waterfall import EnrichmentWaterfall, attempt_enrichment


def test_firecrawl_directly():
    """Test Firecrawl API directly with a single company"""
    print("\n" + "=" * 60)
    print("TEST 1: Direct Firecrawl API Test")
    print("=" * 60)

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key or api_key == "your_firecrawl_api_key_here":
        print("ERROR: FIRECRAWL_API_KEY not set in .env")
        return False

    print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

    # Test company
    test_company = {
        "company_name": "Mountaineer Casino Resort",
        "state": "West Virginia",
        "city": "New Cumberland"
    }

    print(f"\nSearching for: {test_company['company_name']}")
    print(f"Location: {test_company['city']}, {test_company['state']}")

    waterfall = EnrichmentWaterfall()
    result = waterfall._try_firecrawl(test_company)

    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Agent: {result.agent_name}")
    print(f"  Cost: ${result.cost:.2f}")
    if result.success:
        print(f"  Website: {result.enriched_data.get('website', 'N/A')}")
    else:
        print(f"  Errors: {result.errors}")

    return result.success


def check_validation_queue():
    """Check how many companies are in the validation queue"""
    print("\n" + "=" * 60)
    print("TEST 2: Check Validation Queue")
    print("=" * 60)

    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    if not connection_string:
        print("ERROR: DATABASE_URL not set")
        return 0

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'marketing'
                AND table_name = 'company_invalid'
            );
        """)
        table_exists = cursor.fetchone()['exists']

        if not table_exists:
            print("WARNING: marketing.company_invalid table does not exist")
            print("The validation queue table hasn't been created yet.")
            cursor.close()
            conn.close()
            return 0

        # Count records
        cursor.execute("SELECT COUNT(*) as count FROM marketing.company_invalid;")
        count = cursor.fetchone()['count']

        print(f"Companies in validation queue: {count}")

        if count > 0:
            # Show sample records
            cursor.execute("""
                SELECT company_name, reason_code, failed_at
                FROM marketing.company_invalid
                ORDER BY failed_at DESC
                LIMIT 5;
            """)
            samples = cursor.fetchall()
            print("\nSample records:")
            for s in samples:
                print(f"  - {s['company_name']}: {s['reason_code']}")

        cursor.close()
        conn.close()
        return count

    except Exception as e:
        print(f"ERROR connecting to database: {e}")
        return 0


def run_enrichment_test(max_companies: int = 10, dry_run: bool = False):
    """Run enrichment on companies from the queue"""
    print("\n" + "=" * 60)
    print(f"TEST 3: Enrichment Queue Processing (max={max_companies})")
    print("=" * 60)

    if dry_run:
        print("[DRY RUN MODE - No database writes]")

    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    if not connection_string:
        print("ERROR: DATABASE_URL not set")
        return

    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'marketing'
                AND table_name = 'company_invalid'
            );
        """)
        if not cursor.fetchone()['exists']:
            print("No company_invalid table - nothing to process")
            return

        # Get companies to process
        cursor.execute(f"""
            SELECT *
            FROM marketing.company_invalid
            ORDER BY failed_at ASC
            LIMIT {max_companies};
        """)
        companies = cursor.fetchall()

        if not companies:
            print("No companies in validation queue")
            return

        print(f"\nProcessing {len(companies)} companies...")

        # Stats
        stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "total_cost": 0.0,
            "results": []
        }

        for company in companies:
            stats["processed"] += 1
            company_name = company.get("company_name", "Unknown")
            reason = company.get("reason_code", "unknown")

            print(f"\n[{stats['processed']}/{len(companies)}] {company_name}")
            print(f"  Reason: {reason}")

            # Attempt enrichment
            result = attempt_enrichment(dict(company), reason)

            if result["success"]:
                stats["success"] += 1
                stats["total_cost"] += result.get("cost", 0)
                print(f"  SUCCESS: Found {result.get('enriched_data', {})}")
                print(f"  Agent: {result.get('agent_name')}, Cost: ${result.get('cost', 0):.2f}")
            else:
                stats["failed"] += 1
                print(f"  FAILED: {result.get('errors', [])[:2]}")

            stats["results"].append({
                "company": company_name,
                "success": result["success"],
                "agent": result.get("agent_name"),
                "cost": result.get("cost", 0),
                "data": result.get("enriched_data", {})
            })

        # Print summary
        print("\n" + "=" * 60)
        print("ENRICHMENT TEST SUMMARY")
        print("=" * 60)
        print(f"Companies processed: {stats['processed']}")
        print(f"Successful enrichments: {stats['success']}")
        print(f"Failed enrichments: {stats['failed']}")
        print(f"Success rate: {100 * stats['success'] / max(stats['processed'], 1):.1f}%")
        print(f"Total cost: ${stats['total_cost']:.2f}")
        if stats['success'] > 0:
            print(f"Cost per success: ${stats['total_cost'] / stats['success']:.2f}")
        print("=" * 60)

        # Save results
        report_file = f"enrichment_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        print(f"\nResults saved to: {report_file}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Test enrichment system")
    parser.add_argument("--max", type=int, default=10, help="Max companies to process")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--skip-api-test", action="store_true", help="Skip direct API test")
    args = parser.parse_args()

    print("=" * 60)
    print("ENRICHMENT SYSTEM TEST")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check environment
    print("\nEnvironment Check:")
    print(f"  FIRECRAWL_API_KEY: {'SET' if os.getenv('FIRECRAWL_API_KEY') and os.getenv('FIRECRAWL_API_KEY') != 'your_firecrawl_api_key_here' else 'NOT SET'}")
    print(f"  SERPAPI_API_KEY: {'SET' if os.getenv('SERPAPI_API_KEY') and os.getenv('SERPAPI_API_KEY') != 'your_serpapi_api_key_here' else 'NOT SET'}")
    print(f"  DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING') else 'NOT SET'}")

    # Test 1: Direct Firecrawl test
    if not args.skip_api_test:
        firecrawl_works = test_firecrawl_directly()
        if not firecrawl_works:
            print("\nWARNING: Firecrawl test failed. Continuing anyway...")

    # Test 2: Check queue
    queue_count = check_validation_queue()

    # Test 3: Run enrichment
    if queue_count > 0:
        run_enrichment_test(max_companies=args.max, dry_run=args.dry_run)
    else:
        print("\nNo companies in queue to process.")
        print("The 114 WV companies may need to be loaded into marketing.company_invalid first.")


if __name__ == "__main__":
    main()
