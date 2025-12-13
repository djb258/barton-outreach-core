"""
Enrichment Orchestrator - Universal Batch Enrichment Engine
Barton Doctrine ID: 04.04.02.04.50000.100

This orchestrator:
1. Pulls batches from invalid tables (company_invalid, people_invalid)
2. Analyzes validation_errors to determine what needs enrichment
3. Routes to appropriate agents (Apify, Abacus, Firecrawl)
4. Merges enriched data back to records
5. Re-validates records
6. Promotes to master tables if now valid
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.apify_agent import ApifyAgent
from agents.abacus_agent import AbacusAgent
from agents.firecrawl_agent import FirecrawlAgent
from agents.scraperapi_agent import ScraperAPIAgent
from agents.zenrows_agent import ZenRowsAgent
from agents.scrapingbee_agent import ScrapingBeeAgent
from agents.serpapi_agent import SerpAPIAgent
from agents.clearbit_agent import ClearbitAgent
from agents.clay_agent import ClayAgent
from agents.rocketreach_agent import RocketReachAgent
from agents.peopledatalabs_agent import PeopleDataLabsAgent


class EnrichmentOrchestrator:
    """
    Universal enrichment orchestrator

    Handles batch processing of invalid records with throttling and timeouts
    """

    def __init__(self, config: Dict, db_connection):
        """
        Initialize orchestrator

        Args:
            config: Configuration from agent_config.json
            db_connection: Database connection for reading/writing records
        """
        self.config = config
        self.db = db_connection

        # Initialize agents
        self.agents = {}
        agent_configs = config.get('agents', {})

        if agent_configs.get('apify', {}).get('enabled'):
            self.agents['apify'] = ApifyAgent(agent_configs['apify'])

        if agent_configs.get('abacus', {}).get('enabled'):
            self.agents['abacus'] = AbacusAgent(agent_configs['abacus'])

        if agent_configs.get('firecrawl', {}).get('enabled'):
            self.agents['firecrawl'] = FirecrawlAgent(agent_configs['firecrawl'])

        if agent_configs.get('scraperapi', {}).get('enabled'):
            self.agents['scraperapi'] = ScraperAPIAgent(agent_configs['scraperapi'])

        if agent_configs.get('zenrows', {}).get('enabled'):
            self.agents['zenrows'] = ZenRowsAgent(agent_configs['zenrows'])

        if agent_configs.get('scrapingbee', {}).get('enabled'):
            self.agents['scrapingbee'] = ScrapingBeeAgent(agent_configs['scrapingbee'])

        if agent_configs.get('serpapi', {}).get('enabled'):
            self.agents['serpapi'] = SerpAPIAgent(agent_configs['serpapi'])

        if agent_configs.get('clearbit', {}).get('enabled'):
            self.agents['clearbit'] = ClearbitAgent(agent_configs['clearbit'])

        if agent_configs.get('clay', {}).get('enabled'):
            self.agents['clay'] = ClayAgent(agent_configs['clay'])

        if agent_configs.get('rocketreach', {}).get('enabled'):
            self.agents['rocketreach'] = RocketReachAgent(agent_configs['rocketreach'])

        if agent_configs.get('peopledatalabs', {}).get('enabled'):
            self.agents['peopledatalabs'] = PeopleDataLabsAgent(agent_configs['peopledatalabs'])

        # Enrichment config
        self.enrichment_config = config.get('enrichment_config', {})
        self.batch_size = self.enrichment_config.get('batch_size', 10)
        self.max_concurrent = self.enrichment_config.get('max_concurrent_agents', 3)

        # Field routing (validation error field → agents to try)
        self.field_routing = config.get('field_routing', {})

        # Throttle rules
        self.throttle_rules = config.get('throttle_rules', {})
        self.max_time_per_record = self.throttle_rules.get('max_time_per_record_seconds', 180)
        self.max_agents_per_field = self.throttle_rules.get('max_agents_per_field', 2)

        # Stats
        self.stats = {
            'total_processed': 0,
            'total_enriched': 0,
            'total_promoted': 0,
            'total_failed': 0,
            'total_cost': 0.0
        }

    async def enrich_batch(
        self,
        table_name: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich a batch of invalid records

        Args:
            table_name: 'company_invalid' or 'people_invalid'
            limit: Optional limit (overrides config batch_size)

        Returns:
            {
                'processed': 10,
                'enriched': 7,
                'promoted': 3,
                'failed': 3,
                'cost': 0.15
            }
        """
        batch_size = limit or self.batch_size

        # Determine record type
        record_type = 'company' if 'company' in table_name else 'person'

        print(f"\n📦 Starting batch enrichment for {table_name}")
        print(f"   Batch size: {batch_size}")
        print(f"   Record type: {record_type}")

        # Pull batch from database
        records = await self._pull_batch(table_name, batch_size)

        if not records:
            print("   No records to enrich")
            return {
                'processed': 0,
                'enriched': 0,
                'promoted': 0,
                'failed': 0,
                'cost': 0.0
            }

        print(f"   Pulled {len(records)} records\n")

        # Process each record
        tasks = []
        for record in records:
            task = self._enrich_single_record(record, table_name, record_type)
            tasks.append(task)

        # Run with concurrency limit
        results = []
        for i in range(0, len(tasks), self.max_concurrent):
            batch_tasks = tasks[i:i + self.max_concurrent]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)

        # Aggregate results
        batch_stats = {
            'processed': len(records),
            'enriched': sum(1 for r in results if isinstance(r, dict) and r.get('enriched')),
            'promoted': sum(1 for r in results if isinstance(r, dict) and r.get('promoted')),
            'failed': sum(1 for r in results if isinstance(r, Exception) or (isinstance(r, dict) and r.get('failed'))),
            'cost': sum(r.get('cost', 0.0) for r in results if isinstance(r, dict))
        }

        # Update global stats
        self.stats['total_processed'] += batch_stats['processed']
        self.stats['total_enriched'] += batch_stats['enriched']
        self.stats['total_promoted'] += batch_stats['promoted']
        self.stats['total_failed'] += batch_stats['failed']
        self.stats['total_cost'] += batch_stats['cost']

        print(f"\n✅ Batch complete:")
        print(f"   Processed: {batch_stats['processed']}")
        print(f"   Enriched: {batch_stats['enriched']}")
        print(f"   Promoted: {batch_stats['promoted']}")
        print(f"   Failed: {batch_stats['failed']}")
        print(f"   Cost: ${batch_stats['cost']:.4f}")

        return batch_stats

    async def _pull_batch(
        self,
        table_name: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Pull batch of records from invalid table

        Returns records that:
        - Have not been recently attempted (avoid infinite loops)
        - Have validation_errors that we can fix
        """
        query = f"""
            SELECT *
            FROM marketing.{table_name}
            WHERE reviewed = FALSE
              AND (last_enrichment_attempt IS NULL
                   OR last_enrichment_attempt < NOW() - INTERVAL '1 hour')
            ORDER BY failed_at ASC
            LIMIT {limit}
        """

        return await self.db.fetch(query)

    async def _enrich_single_record(
        self,
        record: Dict[str, Any],
        table_name: str,
        record_type: str
    ) -> Dict[str, Any]:
        """
        Enrich a single record

        This is the core enrichment logic:
        1. Analyze validation_errors to see what needs enrichment
        2. Route to appropriate agents
        3. Call agents with timeout
        4. Merge results
        5. Update record
        6. Re-validate
        7. Promote if valid
        """
        record_id = record['id']
        record_name = record.get('company_name') or record.get('full_name', 'Unknown')

        print(f"🔄 Enriching: {record_name} (ID: {record_id})")

        start_time = asyncio.get_event_loop().time()
        total_cost = 0.0
        enriched_fields = {}

        try:
            # Parse validation errors
            validation_errors = record.get('validation_errors', [])
            if isinstance(validation_errors, str):
                validation_errors = json.loads(validation_errors)

            if not validation_errors:
                print(f"   ⚠️  No validation errors to fix")
                return {'enriched': False, 'promoted': False, 'cost': 0.0}

            print(f"   Found {len(validation_errors)} validation errors")

            # Get locked fields (fields manually corrected by user)
            locked_fields = record.get('locked_fields', [])
            if isinstance(locked_fields, str):
                locked_fields = json.loads(locked_fields) if locked_fields else []

            # Build tier-based enrichment plan
            enrichment_plan = self._build_enrichment_plan(
                validation_errors,
                record_type,
                locked_fields
            )

            total_agents = sum(len(enrichment_plan[tier]) for tier in ['tier_1', 'tier_2', 'tier_3'])
            if total_agents == 0:
                print(f"   ⚠️  No enrichment agents available for these errors")
                return {'enriched': False, 'promoted': False, 'cost': 0.0, 'status': 'no_agents'}

            print(f"   Enrichment plan: Tier 1: {len(enrichment_plan['tier_1'])}, Tier 2: {len(enrichment_plan['tier_2'])}, Tier 3: {len(enrichment_plan['tier_3'])}")

            # Execute TIER 1: Cheap Hammers
            print(f"   🔨 TIER 1: Cheap Hammers")
            await self._execute_tier(
                enrichment_plan['tier_1'],
                record,
                enriched_fields,
                total_cost,
                start_time
            )

            # Check if all fields resolved after Tier 1
            if self._all_fields_resolved(validation_errors, enriched_fields):
                print(f"   ✅ All fields resolved in Tier 1! Stopping.")
                await self._update_record(table_name, record_id, enriched_fields)
                is_valid = await self._revalidate_record(table_name, record_id, record_type)
                if is_valid:
                    await self._promote_to_master(table_name, record_id, record_type)
                    print(f"   🎉 Promoted to master table!")
                    return {'enriched': True, 'promoted': True, 'cost': total_cost, 'status': 'ready'}
                return {'enriched': True, 'promoted': False, 'cost': total_cost, 'status': 'ready'}

            # Execute TIER 2: Mid-Cost Precision
            print(f"   ⚙️  TIER 2: Mid-Cost Precision")
            await self._execute_tier(
                enrichment_plan['tier_2'],
                record,
                enriched_fields,
                total_cost,
                start_time
            )

            # Check if all fields resolved after Tier 2
            if self._all_fields_resolved(validation_errors, enriched_fields):
                print(f"   ✅ All fields resolved in Tier 2! Stopping.")
                await self._update_record(table_name, record_id, enriched_fields)
                is_valid = await self._revalidate_record(table_name, record_id, record_type)
                if is_valid:
                    await self._promote_to_master(table_name, record_id, record_type)
                    print(f"   🎉 Promoted to master table!")
                    return {'enriched': True, 'promoted': True, 'cost': total_cost, 'status': 'ready'}
                return {'enriched': True, 'promoted': False, 'cost': total_cost, 'status': 'ready'}

            # Execute TIER 3: High-Accuracy, High-Cost (ONCE ONLY)
            print(f"   💎 TIER 3: High-Accuracy, High-Cost (Last Resort)")
            await self._execute_tier(
                enrichment_plan['tier_3'],
                record,
                enriched_fields,
                total_cost,
                start_time,
                single_run=True
            )

            # Final check
            if self._all_fields_resolved(validation_errors, enriched_fields):
                print(f"   ✅ All fields resolved in Tier 3!")
                await self._update_record(table_name, record_id, enriched_fields)
                is_valid = await self._revalidate_record(table_name, record_id, record_type)
                if is_valid:
                    await self._promote_to_master(table_name, record_id, record_type)
                    print(f"   🎉 Promoted to master table!")
                    return {'enriched': True, 'promoted': True, 'cost': total_cost, 'status': 'ready'}
                return {'enriched': True, 'promoted': False, 'cost': total_cost, 'status': 'ready'}
            else:
                print(f"   ⚠️  Still incomplete after all 3 tiers - marking as IRREPARABLE")
                await self._update_record(table_name, record_id, enriched_fields)
                await self._mark_irreparable(table_name, record_id)
                return {'enriched': False, 'promoted': False, 'cost': total_cost, 'status': 'irreparable'}


        except Exception as e:
            print(f"   ❌ Fatal error: {str(e)}")
            return {
                'enriched': False,
                'promoted': False,
                'failed': True,
                'cost': total_cost,
                'error': str(e)
            }

    async def _execute_tier(
        self,
        tier_plan: List[Dict],
        record: Dict,
        enriched_fields: Dict,
        total_cost: float,
        start_time: float,
        single_run: bool = False
    ):
        """
        Execute all agents in a single tier

        Args:
            tier_plan: List of agent calls for this tier
            record: Record data
            enriched_fields: Dict to update with enriched data (modified in place)
            total_cost: Running cost total (not modified, returned separately)
            start_time: Start time for timeout checking
            single_run: If True (Tier 3), run only once and don't retry
        """
        cost_this_tier = 0.0

        for plan_item in tier_plan:
            # Check time budget
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > self.max_time_per_record:
                print(f"      ⏱️  Timeout reached ({self.max_time_per_record}s), skipping rest of tier")
                break

            agent_name = plan_item['agent']
            capability = plan_item['capability']
            field = plan_item['field']
            tier = plan_item['tier']

            print(f"      → {agent_name}.{capability} for '{field}'")

            # Get agent
            agent = self.agents.get(agent_name)
            if not agent:
                print(f"         ❌ Agent not available")
                continue

            # Call agent
            try:
                result = await agent.enrich_with_retry(
                    capability,
                    record,
                    timeout_seconds=None
                )

                if result['success']:
                    # Merge enriched data
                    enriched_data = result['data']
                    enriched_fields.update(enriched_data)
                    cost_this_tier += result.get('cost', 0.0)

                    print(f"         ✅ {list(enriched_data.keys())}")
                else:
                    print(f"         ❌ {result.get('error', 'Failed')}")

            except Exception as e:
                print(f"         ❌ Exception: {str(e)}")

        return cost_this_tier

    def _all_fields_resolved(
        self,
        validation_errors: List[Dict],
        enriched_fields: Dict
    ) -> bool:
        """
        Check if all validation errors have been resolved

        Args:
            validation_errors: Original validation errors
            enriched_fields: Fields that have been enriched

        Returns:
            True if all required fields are now present
        """
        for error in validation_errors:
            field = error.get('field')
            if field and field not in enriched_fields:
                return False
            if field and not enriched_fields.get(field):
                return False
        return True

    async def _mark_irreparable(
        self,
        table_name: str,
        record_id: int
    ):
        """
        Mark record as irreparable (can't be enriched further)

        Sets enrichment_status = 'irreparable'
        """
        query = f"""
            UPDATE marketing.{table_name}
            SET enrichment_status = 'irreparable',
                updated_at = NOW()
            WHERE id = {record_id}
        """
        await self.db.execute(query)

    def _build_enrichment_plan(
        self,
        validation_errors: List[Dict],
        record_type: str,
        locked_fields: List[str] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Build tier-based enrichment plan from validation errors

        Args:
            validation_errors: List of validation error objects
            record_type: 'company' or 'person'
            locked_fields: Fields that are manually locked (don't enrich)

        Returns:
            {
                'tier_1': [{'agent': 'firecrawl', 'capability': 'search_company', 'field': 'website'}, ...],
                'tier_2': [{'agent': 'clearbit', 'capability': 'enrich_company', 'field': 'website'}, ...],
                'tier_3': [{'agent': 'rocketreach', 'capability': 'find_executive', 'field': 'email'}, ...]
            }
        """
        locked_fields = locked_fields or []
        plan = {'tier_1': [], 'tier_2': [], 'tier_3': []}
        routing = self.field_routing.get(record_type, {})

        # Track which fields need enrichment
        fields_needed = set()
        for error in validation_errors:
            field = error.get('field')
            if field and field not in locked_fields:
                fields_needed.add(field)

        # Build tier-based plan
        for field in fields_needed:
            if field not in routing:
                continue

            field_routing = routing[field]

            # Tier 1: Cheap Hammers (try all)
            tier_1_agents = field_routing.get('tier_1', [])
            tier_1_max = self.throttle_rules.get('tier_1_max_agents', 4)
            for agent_cap in tier_1_agents[:tier_1_max]:
                agent_name, capability = agent_cap.split('.')
                plan['tier_1'].append({
                    'agent': agent_name,
                    'capability': capability,
                    'field': field,
                    'tier': 1
                })

            # Tier 2: Mid-Cost Precision (try up to 2)
            tier_2_agents = field_routing.get('tier_2', [])
            tier_2_max = self.throttle_rules.get('tier_2_max_agents', 2)
            for agent_cap in tier_2_agents[:tier_2_max]:
                agent_name, capability = agent_cap.split('.')
                plan['tier_2'].append({
                    'agent': agent_name,
                    'capability': capability,
                    'field': field,
                    'tier': 2
                })

            # Tier 3: High-Cost, Last Resort (try only 1)
            tier_3_agents = field_routing.get('tier_3', [])
            if tier_3_agents:
                agent_cap = tier_3_agents[0]  # Only first agent
                agent_name, capability = agent_cap.split('.')
                plan['tier_3'].append({
                    'agent': agent_name,
                    'capability': capability,
                    'field': field,
                    'tier': 3
                })

        return plan

    async def _update_record(
        self,
        table_name: str,
        record_id: int,
        enriched_fields: Dict[str, Any]
    ):
        """
        Update record with enriched fields
        """
        # Build SET clause
        set_clauses = []
        for field, value in enriched_fields.items():
            if isinstance(value, str):
                set_clauses.append(f"{field} = '{value}'")
            elif isinstance(value, (int, float)):
                set_clauses.append(f"{field} = {value}")
            elif value is None:
                set_clauses.append(f"{field} = NULL")

        if not set_clauses:
            return

        set_clause = ', '.join(set_clauses)

        query = f"""
            UPDATE marketing.{table_name}
            SET {set_clause},
                updated_at = NOW(),
                last_enrichment_attempt = NOW()
            WHERE id = {record_id}
        """

        await self.db.execute(query)

    async def _revalidate_record(
        self,
        table_name: str,
        record_id: int,
        record_type: str
    ) -> bool:
        """
        Re-validate record after enrichment

        Returns:
            True if now valid, False otherwise
        """
        # This would call your validation_rules.py
        # For now, simplified check
        query = f"""
            SELECT * FROM marketing.{table_name}
            WHERE id = {record_id}
        """

        record = await self.db.fetchrow(query)

        # Simple validation (you'd use validation_rules.py here)
        if record_type == 'company':
            required = ['company_name', 'website', 'employee_count', 'linkedin_url']
        else:
            required = ['full_name', 'email', 'title', 'linkedin_url']

        for field in required:
            if not record.get(field):
                return False

        return True

    async def _promote_to_master(
        self,
        table_name: str,
        record_id: int,
        record_type: str
    ):
        """
        Promote record from invalid to master table

        1. INSERT into company_master or people_master
        2. DELETE from company_invalid or people_invalid
        3. If company: CREATE slots (CEO, CFO, HR)
        """
        # Get record
        query = f"""
            SELECT * FROM marketing.{table_name}
            WHERE id = {record_id}
        """
        record = await self.db.fetchrow(query)

        if record_type == 'company':
            # Insert into company_master
            await self.db.execute(f"""
                INSERT INTO marketing.company_master (
                    company_unique_id, company_name, website, employee_count,
                    linkedin_url, industry, domain, created_at
                )
                VALUES (
                    '{record['company_unique_id']}',
                    '{record['company_name']}',
                    '{record['website']}',
                    {record['employee_count']},
                    '{record['linkedin_url']}',
                    '{record.get('industry', '')}',
                    '{record.get('domain', '')}',
                    NOW()
                )
                ON CONFLICT (company_unique_id) DO UPDATE
                SET company_name = EXCLUDED.company_name,
                    website = EXCLUDED.website,
                    employee_count = EXCLUDED.employee_count,
                    linkedin_url = EXCLUDED.linkedin_url
            """)

            # Create slots (CEO, CFO, HR)
            for slot_type in ['CEO', 'CFO', 'HR']:
                await self.db.execute(f"""
                    INSERT INTO marketing.company_slot (
                        company_slot_unique_id,
                        company_unique_id,
                        slot_type,
                        is_filled,
                        created_at
                    )
                    VALUES (
                        '{record['company_unique_id']}.{slot_type}',
                        '{record['company_unique_id']}',
                        '{slot_type}',
                        FALSE,
                        NOW()
                    )
                    ON CONFLICT DO NOTHING
                """)

        else:
            # Insert into people_master
            await self.db.execute(f"""
                INSERT INTO marketing.people_master (
                    unique_id, full_name, email, title,
                    company_unique_id, linkedin_url, created_at
                )
                VALUES (
                    '{record['unique_id']}',
                    '{record['full_name']}',
                    '{record['email']}',
                    '{record['title']}',
                    '{record.get('company_unique_id', '')}',
                    '{record['linkedin_url']}',
                    NOW()
                )
                ON CONFLICT (unique_id) DO UPDATE
                SET full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    title = EXCLUDED.title,
                    linkedin_url = EXCLUDED.linkedin_url
            """)

        # Delete from invalid table
        await self.db.execute(f"""
            DELETE FROM marketing.{table_name}
            WHERE id = {record_id}
        """)

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            'agents': {
                name: agent.get_stats()
                for name, agent in self.agents.items()
            }
        }
