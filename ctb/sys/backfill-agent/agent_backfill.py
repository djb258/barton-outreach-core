"""
Backfill & Historical State Agent
Barton Doctrine ID: 04.04.02.04.80000.001
CTB Layer: System (Yellow - AI/SHQ nerve)

Mission: Import legacy data, match against existing records, generate baselines

Architecture: Modular (config-driven, easy corrections)
- Config files control matching rules, normalization
- Core modules are standalone
- No hardcoded logic in main agent

Kill Switches:
- No overwriting locked fields
- No duplicate entries
- No Tier 3 enrichment calls
- Fuzzy matches require confidence scores
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

from core.neon_connector import NeonConnector
from core.csv_loader import CSVLoader
from core.normalizer import Normalizer
from core.matcher import Matcher
from core.baseline_generator import BaselineGenerator


class BackfillAgent:
    """
    Main orchestrator for backfill operations

    Reads CSV, normalizes, matches, generates baselines
    """

    def __init__(self, config_dir: str = 'config'):
        """Initialize agent with configuration"""
        # Load configurations
        self.config = self._load_config(f'{config_dir}/backfill_config.json')
        self.norm_rules = self._load_config(f'{config_dir}/normalization_rules.json')

        # Initialize core modules
        self.db = NeonConnector(self.config)
        self.csv_loader = CSVLoader(self.config)
        self.normalizer = Normalizer(self.norm_rules)
        self.matcher = Matcher(self.config)
        self.baseline_generator = BaselineGenerator(self.config)

        # Generate worker/process IDs
        self.worker_id = f"backfill-{uuid.uuid4().hex[:8]}"
        self.process_id = f"PRC-BF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Stats
        self.stats = {
            'rows_loaded': 0,
            'rows_processed': 0,
            'companies_matched': 0,
            'companies_created': 0,
            'people_matched': 0,
            'people_created': 0,
            'people_updated': 0,
            'bit_baselines_created': 0,
            'tf_baselines_created': 0,
            'unresolved': 0,
            'duplicates': 0,
            'locked_field_skips': 0,
            'errors': 0
        }

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        with open(path, 'r') as f:
            return json.load(f)

    async def run(self, csv_path: str):
        """
        Main execution flow

        1. Load CSV
        2. Normalize data
        3. Match against existing records
        4. Insert/update as needed
        5. Generate baselines
        6. Log results
        """
        print(f"🚀 Backfill Agent Starting")
        print(f"   Worker ID: {self.worker_id}")
        print(f"   Process ID: {self.process_id}")
        print(f"   Barton Doctrine ID: {self.config['barton_doctrine_id']}")
        print(f"   CSV Path: {csv_path}")
        print()

        try:
            # Connect to database
            await self.db.connect()
            print(f"✅ Connected to Neon database")

            # Log start
            await self._log_event('agent_started', {'csv_path': csv_path})

            # Load CSV
            print(f"📥 Loading CSV...")
            rows = self.csv_loader.load_csv(csv_path)
            self.stats['rows_loaded'] = len(rows)
            print(f"✅ Loaded {len(rows)} rows")

            # Get CSV summary
            summary = self.csv_loader.get_summary(rows)
            print(f"   Valid: {summary['valid_rows']}, Errors: {summary['error_rows']}, Warnings: {summary['warning_rows']}")
            print()

            # Load existing companies (for matching)
            print(f"📊 Loading existing companies...")
            existing_companies = await self.db.get_all_companies()
            print(f"✅ Loaded {len(existing_companies)} existing companies")
            print()

            # Process each row
            print(f"⚙️  Processing rows...")
            for row in rows:
                await self._process_row(row, existing_companies)

            # Log completion
            await self._log_event('agent_completed', self.stats)

            # Print summary
            self._print_summary()

        except Exception as e:
            print(f"❌ Fatal error: {str(e)}")
            await self._log_event('agent_error', {'error': str(e)}, severity='ERROR')
            self.stats['errors'] += 1

        finally:
            await self.db.close()
            print(f"🔌 Disconnected from database")

    async def _process_row(
        self,
        row: Dict[str, Any],
        existing_companies: List[Dict[str, Any]]
    ):
        """
        Process a single CSV row

        Flow:
        1. Validate row
        2. Normalize data
        3. Match company
        4. Match person
        5. Insert/update as needed
        6. Generate baselines
        7. Log result
        """
        try:
            self.stats['rows_processed'] += 1

            row_hash = row['_row_hash']
            row_num = row['_row_number']

            # Validate row
            validation = self.csv_loader.validate_row(row)

            if not validation['valid']:
                print(f"   ⚠️  Row {row_num}: Validation failed - {validation['errors'][0]}")
                await self._log_backfill_operation(
                    row_hash,
                    row,
                    'error',
                    None,
                    None,
                    error_message='; '.join(validation['errors'])
                )
                self.stats['errors'] += 1
                return

            # Normalize data
            normalized = self.normalizer.normalize_row(row)

            company_name = normalized.get('company_name', 'Unknown')
            person_name = normalized.get('full_name', 'Unknown')

            # Match company
            company_match = self.matcher.match_company(normalized, existing_companies)

            company_id = None
            company_created = False

            if company_match['match_type'] == 'no_match':
                # Create new company
                company_id = await self.db.insert_company(normalized)
                self.stats['companies_created'] += 1
                company_created = True
                print(f"   ➕ Created company: {company_name} (ID: {company_id})")

                # Add to existing companies list for future matches
                existing_companies.append({
                    'company_unique_id': company_id,
                    'company_name': normalized['company_name'],
                    'company_domain': normalized['company_domain']
                })
            else:
                # Use existing company
                company_id = company_match['matched_company']['company_unique_id']
                self.stats['companies_matched'] += 1

                # Update company if fuzzy match with new data
                if company_match['match_type'] == 'fuzzy_company':
                    locked_fields = self.matcher.check_locked_fields(company_match['matched_company'])

                    if locked_fields:
                        print(f"   🔒 Company {company_name}: Locked fields {locked_fields}, skipping update")
                        self.stats['locked_field_skips'] += 1
                    else:
                        # Merge and update
                        merged = self.matcher.merge_records(company_match['matched_company'], normalized)
                        updated_fields = merged.get('_backfill_updated_fields', [])

                        if updated_fields:
                            await self.db.update_company(company_id, merged, updated_fields)
                            print(f"   🔄 Updated company: {company_name} (fields: {', '.join(updated_fields)})")

            # Match person
            existing_people = await self.db.get_people_by_company(company_id)
            person_match = self.matcher.match_person(normalized, company_id, existing_people)

            person_id = None
            person_created = False

            if person_match['match_type'] == 'no_match':
                # Create new person
                person_data = {**normalized, 'company_unique_id': company_id}
                person_id = await self.db.insert_person(person_data)
                self.stats['people_created'] += 1
                person_created = True
                print(f"   ➕ Created person: {person_name} at {company_name}")
            else:
                # Use existing person
                person_id = person_match['matched_person']['unique_id']
                self.stats['people_matched'] += 1

                # Update person if fuzzy match with new data
                if person_match['match_type'] == 'fuzzy_person':
                    locked_fields = self.matcher.check_locked_fields(person_match['matched_person'])

                    if locked_fields:
                        print(f"   🔒 Person {person_name}: Locked fields {locked_fields}, skipping update")
                        self.stats['locked_field_skips'] += 1
                    else:
                        # Merge and update
                        merged = self.matcher.merge_records(person_match['matched_person'], normalized)
                        updated_fields = merged.get('_backfill_updated_fields', [])

                        if updated_fields:
                            await self.db.update_person(person_id, merged, updated_fields)
                            self.stats['people_updated'] += 1
                            print(f"   🔄 Updated person: {person_name} (fields: {', '.join(updated_fields)})")

            # Generate baselines
            baseline_check = self.baseline_generator.should_generate_baseline(normalized)

            # BIT baseline
            if baseline_check['should_generate_bit']:
                bit_baseline = self.baseline_generator.generate_bit_baseline(
                    person_id,
                    company_id,
                    normalized
                )

                baseline_id = await self.db.insert_bit_baseline(bit_baseline)

                if baseline_id:
                    self.stats['bit_baselines_created'] += 1

                    # Generate BIT signals
                    for signal in bit_baseline['signals_to_generate']:
                        await self.db.insert_bit_signal_from_baseline(person_id, company_id, signal)

                    print(f"   📊 BIT baseline: {bit_baseline['baseline_score']} pts ({bit_baseline['baseline_tier']})")

            # Talent Flow baseline
            if baseline_check['should_generate_tf']:
                tf_baseline = self.baseline_generator.generate_talent_flow_baseline(person_id, normalized)

                baseline_id = await self.db.insert_talent_flow_baseline(tf_baseline)

                if baseline_id:
                    self.stats['tf_baselines_created'] += 1
                    print(f"   📸 TF baseline: Snapshot created")

            # Log backfill operation
            resolution_status = 'initialized'

            if company_created and person_created:
                resolution_status = 'initialized'
            elif company_match['match_type'] == 'no_match' or person_match['match_type'] == 'no_match':
                resolution_status = 'unresolved'
                self.stats['unresolved'] += 1

            await self._log_backfill_operation(
                row_hash,
                row,
                resolution_status,
                company_match,
                person_match,
                company_id=company_id,
                person_id=person_id
            )

            # If low confidence, add to garage
            if (
                company_match['match_confidence'] < self.config['safety']['fallout_bucket_threshold'] or
                person_match['match_confidence'] < self.config['safety']['fallout_bucket_threshold']
            ):
                await self.db.insert_missing_part(
                    source_data=row,
                    issue_type='low_confidence_match',
                    match_attempts={
                        'company_match': company_match,
                        'person_match': person_match
                    },
                    confidence_score=min(company_match['match_confidence'], person_match['match_confidence'])
                )

        except Exception as e:
            print(f"   ❌ Error processing row {row.get('_row_number', '?')}: {str(e)}")
            self.stats['errors'] += 1
            await self._log_backfill_operation(
                row.get('_row_hash', ''),
                row,
                'error',
                None,
                None,
                error_message=str(e)
            )

    async def _log_backfill_operation(
        self,
        row_hash: str,
        row_data: Dict[str, Any],
        resolution_status: str,
        company_match: Optional[Dict[str, Any]],
        person_match: Optional[Dict[str, Any]],
        company_id: Optional[str] = None,
        person_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Log backfill operation to backfill_log"""
        log_data = {
            'source_row_hash': row_hash,
            'source_data': {k: v for k, v in row_data.items() if not k.startswith('_')},
            'match_type': person_match['match_type'] if person_match else None,
            'match_confidence': person_match['match_confidence'] if person_match else 0.0,
            'matched_company_id': company_id,
            'matched_person_id': person_id,
            'resolution_status': resolution_status,
            'actions_taken': {
                'company_match': company_match['match_type'] if company_match else None,
                'person_match': person_match['match_type'] if person_match else None
            },
            'error_message': error_message,
            'notes': None
        }

        await self.db.log_backfill_operation(log_data, self.worker_id, self.process_id)

    async def _log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = 'INFO'
    ):
        """Log event to SHQ audit log"""
        if not self.config['logging']['log_to_shq']:
            return

        await self.db.log_to_shq(
            worker_id=self.worker_id,
            process_id=self.process_id,
            event_type=event_type,
            event_data=event_data,
            severity=severity
        )

    def _print_summary(self):
        """Print execution summary"""
        print()
        print("=" * 60)
        print("📊 BACKFILL AGENT - EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Rows Loaded: {self.stats['rows_loaded']}")
        print(f"Rows Processed: {self.stats['rows_processed']}")
        print()
        print(f"Companies:")
        print(f"  - Matched: {self.stats['companies_matched']}")
        print(f"  - Created: {self.stats['companies_created']}")
        print()
        print(f"People:")
        print(f"  - Matched: {self.stats['people_matched']}")
        print(f"  - Created: {self.stats['people_created']}")
        print(f"  - Updated: {self.stats['people_updated']}")
        print()
        print(f"Baselines:")
        print(f"  - BIT Baselines: {self.stats['bit_baselines_created']}")
        print(f"  - TF Baselines: {self.stats['tf_baselines_created']}")
        print()
        print(f"Issues:")
        print(f"  - Unresolved: {self.stats['unresolved']}")
        print(f"  - Duplicates: {self.stats['duplicates']}")
        print(f"  - Locked Field Skips: {self.stats['locked_field_skips']}")
        print(f"  - Errors: {self.stats['errors']}")
        print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python agent_backfill.py <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]

    agent = BackfillAgent()
    asyncio.run(agent.run(csv_path))
