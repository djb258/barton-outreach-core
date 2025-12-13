#!/usr/bin/env python3
"""
Enrichment CLI Runner
Barton Doctrine ID: 04.04.02.04.50000.200

Usage:
    python run_enrichment.py --table company_invalid --limit 10
    python run_enrichment.py --table people_invalid --limit 5
    python run_enrichment.py --continuous  # Run continuous loop
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from orchestrator.enrichment_orchestrator import EnrichmentOrchestrator


class SimpleDBConnection:
    """
    Simple async database connection wrapper
    (In production, use asyncpg directly)
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None

    async def connect(self):
        """Create connection pool"""
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=5
            )
            print("✅ Connected to database")
        except ImportError:
            print("❌ asyncpg not installed. Run: pip install asyncpg")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()

    async def fetch(self, query: str):
        """Fetch multiple rows"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str):
        """Fetch single row"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return dict(row) if row else None

    async def execute(self, query: str):
        """Execute query without return"""
        async with self._pool.acquire() as conn:
            await conn.execute(query)


async def run_single_batch(
    orchestrator: EnrichmentOrchestrator,
    table: str,
    limit: int
):
    """Run a single enrichment batch"""
    print("\n" + "=" * 80)
    print(f"ENRICHMENT BATCH - {table}")
    print("=" * 80)

    stats = await orchestrator.enrich_batch(table, limit)

    print("\n" + "=" * 80)
    print("BATCH SUMMARY")
    print("=" * 80)
    print(f"Processed:  {stats['processed']}")
    print(f"Enriched:   {stats['enriched']}")
    print(f"Promoted:   {stats['promoted']}")
    print(f"Failed:     {stats['failed']}")
    print(f"Cost:       ${stats['cost']:.4f}")
    print("=" * 80)

    return stats


async def run_continuous(
    orchestrator: EnrichmentOrchestrator,
    interval_seconds: int = 300
):
    """Run continuous enrichment loop"""
    print("\n🔄 Starting continuous enrichment loop")
    print(f"   Interval: {interval_seconds} seconds\n")

    iteration = 0

    while True:
        iteration += 1
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")

        # Run companies
        company_stats = await orchestrator.enrich_batch('company_invalid')

        # Run people
        people_stats = await orchestrator.enrich_batch('people_invalid')

        # Print cumulative stats
        cumulative = orchestrator.get_stats()
        print(f"\n📊 Cumulative Stats:")
        print(f"   Total Processed: {cumulative['total_processed']}")
        print(f"   Total Enriched:  {cumulative['total_enriched']}")
        print(f"   Total Promoted:  {cumulative['total_promoted']}")
        print(f"   Total Failed:    {cumulative['total_failed']}")
        print(f"   Total Cost:      ${cumulative['total_cost']:.4f}")

        # If nothing to process, increase wait time
        total_processed = company_stats['processed'] + people_stats['processed']
        if total_processed == 0:
            print(f"\n😴 No records to process, waiting {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)
        else:
            print(f"\n⏸️  Waiting {interval_seconds}s before next iteration...")
            await asyncio.sleep(interval_seconds)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run enrichment agents')
    parser.add_argument(
        '--table',
        choices=['company_invalid', 'people_invalid', 'both'],
        default='both',
        help='Which table to enrich'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Batch size (default: 10)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous enrichment loop'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Seconds between continuous runs (default: 300)'
    )

    args = parser.parse_args()

    # Load config
    config_path = Path(__file__).parent / 'config' / 'agent_config.json'
    with open(config_path) as f:
        config = json.load(f)

    # Get database URL
    database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Set it in .env file")
        sys.exit(1)

    # Create database connection
    db = SimpleDBConnection(database_url)
    await db.connect()

    try:
        # Create orchestrator
        orchestrator = EnrichmentOrchestrator(config, db)

        print("\n🤖 Enrichment Orchestrator Ready")
        print(f"   Agents enabled: {list(orchestrator.agents.keys())}")
        print(f"   Batch size: {orchestrator.batch_size}")
        print(f"   Max time per record: {orchestrator.max_time_per_record}s")

        if args.continuous:
            # Continuous mode
            await run_continuous(orchestrator, args.interval)
        else:
            # Single batch mode
            if args.table == 'both':
                await run_single_batch(orchestrator, 'company_invalid', args.limit)
                await run_single_batch(orchestrator, 'people_invalid', args.limit)
            else:
                await run_single_batch(orchestrator, args.table, args.limit)

            # Print final stats
            final_stats = orchestrator.get_stats()
            print("\n📊 Agent Statistics:")
            for agent_name, agent_stats in final_stats['agents'].items():
                print(f"\n   {agent_name.upper()}:")
                print(f"      Total calls: {agent_stats['total_calls']}")
                print(f"      Total cost:  ${agent_stats['total_cost']:.4f}")
                print(f"      Status:      {agent_stats['rate_limit_status']}")

    finally:
        await db.close()
        print("\n✅ Enrichment complete")


if __name__ == '__main__':
    from datetime import datetime
    asyncio.run(main())
