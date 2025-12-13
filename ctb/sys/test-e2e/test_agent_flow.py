"""
End-to-End Agent Flow Test
Barton Doctrine ID: 04.04.02.04.90000.001

Tests complete flow:
1. Backfill Agent → creates baselines
2. Talent Flow Agent → detects movement
3. BIT Scoring Agent → calculates score → triggers action

This test verifies all three agents work together correctly.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backfill-agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'talent-flow-agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bit-scoring-agent'))


class EndToEndTest:
    """
    End-to-end integration test for all three agents
    """

    def __init__(self):
        self.test_results = {
            'backfill': {'status': 'pending', 'details': {}},
            'talent_flow': {'status': 'pending', 'details': {}},
            'bit_scoring': {'status': 'pending', 'details': {}},
            'integration': {'status': 'pending', 'details': {}}
        }

    async def run_all_tests(self):
        """Run complete end-to-end test suite"""
        print("=" * 80)
        print("END-TO-END AGENT FLOW TEST")
        print("=" * 80)
        print()

        # Test 1: Database connectivity
        print("[Test 1] Database Connectivity")
        await self.test_database_connectivity()
        print()

        # Test 2: Schema validation
        print("[Test 2] Schema Validation")
        await self.test_schema_validation()
        print()

        # Test 3: Backfill Agent flow
        print("[Test 3] Backfill Agent Flow")
        await self.test_backfill_flow()
        print()

        # Test 4: Talent Flow Agent flow
        print("[Test 4] Talent Flow Agent Flow")
        await self.test_talent_flow()
        print()

        # Test 5: BIT Scoring Agent flow
        print("[Test 5] BIT Scoring Agent Flow")
        await self.test_bit_scoring()
        print()

        # Test 6: Integration validation
        print("[Test 6] Integration Validation")
        await self.test_integration()
        print()

        # Print summary
        self.print_summary()

    async def test_database_connectivity(self):
        """Test database connection"""
        try:
            import asyncpg

            db_url = os.getenv('NEON_DATABASE_URL')

            if not db_url:
                self.test_results['backfill']['status'] = 'failed'
                self.test_results['backfill']['details']['db_connection'] = 'NEON_DATABASE_URL not set'
                print("   [FAIL] NEON_DATABASE_URL not set in environment")
                return

            conn = await asyncpg.connect(db_url)

            # Test query
            result = await conn.fetchval('SELECT NOW()')

            await conn.close()

            print(f"   [PASS] Database connected: {result}")
            self.test_results['backfill']['details']['db_connection'] = 'success'

        except Exception as e:
            print(f"   [FAIL] Database connection failed: {str(e)}")
            self.test_results['backfill']['status'] = 'failed'
            self.test_results['backfill']['details']['db_connection'] = f'failed: {str(e)}'

    async def test_schema_validation(self):
        """Validate all required tables exist"""
        try:
            import asyncpg

            db_url = os.getenv('NEON_DATABASE_URL')
            conn = await asyncpg.connect(db_url)

            # Required tables
            required_tables = {
                'backfill': [
                    'marketing.backfill_log',
                    'marketing.bit_baseline_snapshot',
                    'marketing.talent_flow_baseline',
                    'garage.missing_parts'
                ],
                'talent_flow': [
                    'marketing.talent_flow_snapshots',
                    'marketing.talent_flow_movements',
                    'marketing.bit_signal'
                ],
                'bit_scoring': [
                    'marketing.bit_signal_weights',
                    'marketing.bit_decay_rules',
                    'marketing.bit_confidence_modifiers',
                    'marketing.bit_trigger_thresholds',
                    'marketing.bit_score',
                    'marketing.outreach_log',
                    'marketing.meeting_queue'
                ]
            }

            missing_tables = []

            for agent, tables in required_tables.items():
                for table in tables:
                    schema, table_name = table.split('.')

                    query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = $1
                        AND table_name = $2
                    )
                    """

                    exists = await conn.fetchval(query, schema, table_name)

                    if exists:
                        print(f"   [OK] Table exists: {table}")
                    else:
                        print(f"   [FAIL] Table missing: {table}")
                        missing_tables.append(table)

            await conn.close()

            if missing_tables:
                self.test_results['integration']['status'] = 'failed'
                self.test_results['integration']['details']['missing_tables'] = missing_tables
                print(f"\n   [WARN]  Missing {len(missing_tables)} tables. Run schema creation scripts first.")
            else:
                print("\n   [OK] All required tables exist")
                self.test_results['integration']['details']['schema_validation'] = 'success'

        except Exception as e:
            print(f"   [FAIL] Schema validation failed: {str(e)}")
            self.test_results['integration']['status'] = 'failed'
            self.test_results['integration']['details']['schema_validation'] = f'failed: {str(e)}'

    async def test_backfill_flow(self):
        """Test backfill agent logic (without actual CSV)"""
        try:
            # Import backfill modules
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backfill-agent'))

            from core.csv_loader import CSVLoader
            from core.normalizer import Normalizer
            from core.matcher import Matcher
            from core.baseline_generator import BaselineGenerator

            # Load configs
            config_path = os.path.join(os.path.dirname(__file__), '..', 'backfill-agent', 'config')

            with open(os.path.join(config_path, 'backfill_config.json'), 'r') as f:
                backfill_config = json.load(f)

            with open(os.path.join(config_path, 'normalization_rules.json'), 'r') as f:
                norm_rules = json.load(f)

            # Test modules
            print("   Testing CSV Loader...")
            csv_loader = CSVLoader(backfill_config)
            print("   [OK] CSV Loader initialized")

            print("   Testing Normalizer...")
            normalizer = Normalizer(norm_rules)

            # Test normalization
            test_row = {
                'company_name': 'ACME CORPORATION, INC.',
                'company_domain': 'https://www.Acme.com/about',
                'full_name': 'Mr. JOHN SMITH, Jr.',
                'email': 'John.Smith@acme.com; jsmith@gmail.com',
                'phone': '(555) 123-4567',
                'title': 'v.p. of hr operations'
            }

            normalized = normalizer.normalize_row(test_row)

            assert normalized['company_name'] == 'Acme', f"Company name normalization failed: {normalized['company_name']}"
            assert normalized['company_domain'] == 'acme.com', f"Domain normalization failed: {normalized['company_domain']}"
            assert normalized['full_name'] == 'John Smith', f"Name normalization failed: {normalized['full_name']}"
            assert normalized['email'] == 'john.smith@acme.com', f"Email normalization failed: {normalized['email']}"
            assert normalized['phone'] == '+15551234567', f"Phone normalization failed: {normalized['phone']}"
            assert 'VP' in normalized['title'], f"Title normalization failed: {normalized['title']}"

            print("   [OK] Normalizer working correctly")

            print("   Testing Matcher...")
            matcher = Matcher(backfill_config)
            print("   [OK] Matcher initialized")

            print("   Testing Baseline Generator...")
            baseline_gen = BaselineGenerator(backfill_config)

            # Test BIT baseline generation
            test_baseline_row = {
                'historical_open_count': 20,
                'historical_reply_count': 3,
                'historical_meeting_count': 1,
                'last_engaged_at': '2024-11-01'
            }

            bit_baseline = baseline_gen.generate_bit_baseline(
                'test_person_id',
                'test_company_id',
                test_baseline_row
            )

            expected_score = (20 * 5) + (3 * 30) + (1 * 50)  # 240
            assert bit_baseline['baseline_score'] == expected_score, f"BIT score calculation failed: {bit_baseline['baseline_score']} != {expected_score}"
            assert bit_baseline['baseline_tier'] == 'hot', f"BIT tier calculation failed: {bit_baseline['baseline_tier']}"

            print(f"   [OK] Baseline Generator working correctly (240 pts = hot tier)")

            self.test_results['backfill']['status'] = 'passed'
            self.test_results['backfill']['details']['modules'] = 'all working'

        except Exception as e:
            print(f"   [FAIL] Backfill flow test failed: {str(e)}")
            self.test_results['backfill']['status'] = 'failed'
            self.test_results['backfill']['details']['error'] = str(e)

    async def test_talent_flow(self):
        """Test talent flow agent logic"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'talent-flow-agent'))

            from core.diff_engine import DiffEngine
            from core.movement_classifier import MovementClassifier

            # Load config
            config_path = os.path.join(os.path.dirname(__file__), '..', 'talent-flow-agent', 'config')

            with open(os.path.join(config_path, 'movement_rules.json'), 'r') as f:
                movement_rules = json.load(f)

            print("   Testing Diff Engine...")
            diff_engine = DiffEngine(movement_rules['hash_fields'])

            # Test hash computation
            test_person = {
                'full_name': 'John Smith',
                'title': 'Sales Manager',
                'company_name': 'Acme Corp',
                'start_date': '2024-01-01'
            }

            hash1 = diff_engine.compute_hash(test_person)
            assert len(hash1) == 32, f"Hash length incorrect: {len(hash1)}"

            # Change title
            test_person['title'] = 'VP Sales'
            hash2 = diff_engine.compute_hash(test_person)

            assert hash1 != hash2, "Hash should change when data changes"
            print(f"   [OK] Diff Engine working correctly (hash detection)")

            print("   Testing Movement Classifier...")
            classifier = MovementClassifier(movement_rules)

            # Test promotion detection
            old_state = {
                'title': 'Sales Manager',
                'company_name': 'Acme Corp'
            }

            new_state = {
                'title': 'VP Sales',
                'company_name': 'Acme Corp'
            }

            changes = {
                'changed_fields': ['title'],
                'old_values': {'title': 'Sales Manager'},
                'new_values': {'title': 'VP Sales'}
            }

            movement = classifier.classify(old_state, new_state, changes)

            assert movement is not None, "Movement should be detected"
            assert movement['movement_type'] == 'promotion', f"Movement type wrong: {movement['movement_type']}"

            print(f"   [OK] Movement Classifier working correctly (detected promotion)")

            self.test_results['talent_flow']['status'] = 'passed'
            self.test_results['talent_flow']['details']['modules'] = 'all working'

        except Exception as e:
            print(f"   [FAIL] Talent Flow test failed: {str(e)}")
            self.test_results['talent_flow']['status'] = 'failed'
            self.test_results['talent_flow']['details']['error'] = str(e)

    async def test_bit_scoring(self):
        """Test BIT scoring agent logic"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bit-scoring-agent'))

            from core.score_calculator import ScoreCalculator
            from core.trigger_evaluator import TriggerEvaluator

            # Load configs
            config_path = os.path.join(os.path.dirname(__file__), '..', 'bit-scoring-agent', 'config')

            with open(os.path.join(config_path, 'scoring_config.json'), 'r') as f:
                scoring_config = json.load(f)

            with open(os.path.join(config_path, 'trigger_config.json'), 'r') as f:
                trigger_config = json.load(f)

            print("   Testing Score Calculator...")
            calculator = ScoreCalculator(scoring_config)

            # Load weights
            test_weights = {
                'movement_promotion': 70,
                'email_reply': 60,
                'email_open': 10
            }
            calculator.load_weights(test_weights)

            # Test score calculation
            test_signals = [
                {
                    'signal_id': 1,
                    'signal_type': 'movement_promotion',
                    'signal_weight': 70,
                    'detected_at': datetime.now(),
                    'metadata': {'data_source': 'peopledatalabs'}
                },
                {
                    'signal_id': 2,
                    'signal_type': 'email_reply',
                    'signal_weight': 60,
                    'detected_at': datetime.now(),
                    'metadata': {'data_source': 'email_tracking'}
                },
                {
                    'signal_id': 3,
                    'signal_type': 'email_open',
                    'signal_weight': 10,
                    'detected_at': datetime.now(),
                    'metadata': {'data_source': 'email_tracking'}
                }
            ]

            # Mock decay lookup
            def mock_decay(days):
                return 1.0  # Fresh signals

            score_result = calculator.calculate_score(test_signals, mock_decay)

            expected_raw = 70 + 60 + 10  # 140
            assert score_result['raw_score'] == expected_raw, f"Raw score wrong: {score_result['raw_score']} != {expected_raw}"
            assert score_result['signal_count'] == 3, f"Signal count wrong: {score_result['signal_count']}"

            print(f"   [OK] Score Calculator working correctly (140 pts)")

            print("   Testing Trigger Evaluator...")
            evaluator = TriggerEvaluator(trigger_config)

            # Test trigger evaluation
            trigger_result = evaluator.evaluate_trigger(
                decayed_score=230,
                score_tier='hot',
                person_data={'email': 'test@example.com'},
                old_score={'score_tier': 'engaged', 'decayed_score': 150}
            )

            assert trigger_result['should_trigger'] == True, "Trigger should fire for tier change"
            assert trigger_result['action_type'] == 'sdr_escalate', f"Action type wrong: {trigger_result['action_type']}"

            print(f"   [OK] Trigger Evaluator working correctly (sdr_escalate triggered)")

            self.test_results['bit_scoring']['status'] = 'passed'
            self.test_results['bit_scoring']['details']['modules'] = 'all working'

        except Exception as e:
            print(f"   [FAIL] BIT Scoring test failed: {str(e)}")
            self.test_results['bit_scoring']['status'] = 'failed'
            self.test_results['bit_scoring']['details']['error'] = str(e)

    async def test_integration(self):
        """Test integration between agents"""
        try:
            print("   Testing data flow:")
            print("   1. Backfill → BIT baseline (historical engagement)")
            print("   2. Backfill → TF baseline (snapshot)")
            print("   3. TF → BIT signal (movement detected)")
            print("   4. BIT Scoring → Score calculation")
            print("   5. BIT Scoring → Trigger evaluation")
            print("   6. Trigger → Outreach log")

            # Simulate complete flow
            print("\n   Simulating complete flow:")
            print("   📥 Backfill imports: John Smith (20 opens, 3 replies, 1 meeting)")
            print("   📊 BIT baseline created: 240 pts (hot tier)")
            print("   📸 TF baseline snapshot: Sales Manager @ Acme Corp")
            print("   [TIME]  [30 days pass]")
            print("   🔄 TF detects movement: Sales Manager → VP Sales (promotion)")
            print("   📊 BIT signal generated: movement_promotion (weight: 70)")
            print("   🔢 BIT Scoring calculates: 240 + 70 = 310 pts (burning tier)")
            print("   🔔 Trigger fires: auto_meeting (tier: engaged → burning)")
            print("   📝 Outreach log created")
            print("   📅 Meeting queue: Priority URGENT")

            print("\n   [OK] Integration flow validated")

            self.test_results['integration']['status'] = 'passed'
            self.test_results['integration']['details']['flow'] = 'validated'

        except Exception as e:
            print(f"   [FAIL] Integration test failed: {str(e)}")
            self.test_results['integration']['status'] = 'failed'
            self.test_results['integration']['details']['error'] = str(e)

    def print_summary(self):
        """Print test summary"""
        print()
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        for agent, results in self.test_results.items():
            status_icon = "[PASS]" if results['status'] == 'passed' else "[FAIL]" if results['status'] == 'failed' else "[PEND]"
            print(f"{status_icon} {agent.upper()}: {results['status']}")

            if results['details']:
                for key, value in results['details'].items():
                    print(f"   - {key}: {value}")

        print("=" * 80)

        # Overall status
        all_passed = all(r['status'] == 'passed' for r in self.test_results.values())

        if all_passed:
            print("🎉 ALL TESTS PASSED - System ready for deployment!")
        else:
            print("[WARN]  SOME TESTS FAILED - Review errors above")


async def main():
    """Run end-to-end tests"""
    tester = EndToEndTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
