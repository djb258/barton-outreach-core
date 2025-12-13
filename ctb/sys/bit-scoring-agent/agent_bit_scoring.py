"""
BIT Scoring Agent - Signal to Score Engine
Barton Doctrine ID: 04.04.02.04.70000.001
CTB Layer: System (Yellow - AI/SHQ nerve)

Mission: Convert events (signals) into numeric Buyer Intent Scores that trigger sales actions

Architecture: Modular (config-driven, easy corrections)
- Config files control weights, thresholds, triggers
- Core modules are standalone
- No hardcoded scoring logic in main agent

Kill Switches:
- No double-scoring (idempotent writes)
- No runaway escalations (score increase caps)
- No missing weight defaults (explicit fallback)
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.neon_connector import NeonConnector
from core.score_calculator import ScoreCalculator
from core.trigger_evaluator import TriggerEvaluator


class BITScoringAgent:
    """
    Main orchestrator for BIT scoring

    Reads configs, coordinates modules, enforces safety rules
    """

    def __init__(self, config_dir: str = 'config'):
        """Initialize agent with configuration"""
        # Load configurations
        self.config = self._load_config(f'{config_dir}/scoring_config.json')
        self.trigger_config = self._load_config(f'{config_dir}/trigger_config.json')

        # Initialize core modules
        self.db = NeonConnector(self.config)
        self.calculator = ScoreCalculator(self.config)
        self.evaluator = TriggerEvaluator(self.trigger_config)

        # Generate worker/process IDs
        self.worker_id = f"bit-scoring-{uuid.uuid4().hex[:8]}"
        self.process_id = f"PRC-BIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Stats
        self.stats = {
            'signals_processed': 0,
            'scores_calculated': 0,
            'scores_updated': 0,
            'triggers_fired': 0,
            'meetings_queued': 0,
            'skipped_duplicate': 0,
            'skipped_validation': 0,
            'errors': 0
        }

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        with open(path, 'r') as f:
            return json.load(f)

    async def run(self):
        """
        Main execution flow

        1. Connect to database
        2. Load weight/decay/confidence tables
        3. Pull unscored signals
        4. Group by person/company
        5. For each person/company:
           - Get all signals
           - Calculate score (with decay + confidence)
           - Determine tier
           - Evaluate triggers
           - Write score + trigger actions
        6. Close connection
        """
        print(f"🚀 BIT Scoring Agent Starting")
        print(f"   Worker ID: {self.worker_id}")
        print(f"   Process ID: {self.process_id}")
        print(f"   Barton Doctrine ID: {self.config['barton_doctrine_id']}")
        print()

        try:
            # Connect to database
            await self.db.connect()
            print(f"✅ Connected to Neon database")

            # Log start
            await self._log_event('agent_started', {'config': self.config['agent_name']})

            # Load weight tables
            await self._load_weight_tables()

            # Pull unscored signals
            lookback_days = self.config['processing']['lookback_days']
            signals = await self.db.get_unscored_signals(lookback_days)
            print(f"📊 Found {len(signals)} unscored signals (last {lookback_days} days)")
            print()

            # Group signals by person/company
            grouped_signals = self._group_signals(signals)
            print(f"👥 Processing {len(grouped_signals)} person/company combinations")
            print()

            # Process each person/company
            for (person_id, company_id), signal_list in grouped_signals.items():
                await self._process_person_company(person_id, company_id, signal_list)

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

    async def _load_weight_tables(self):
        """Load signal weights and confidence modifiers from database"""
        print(f"📥 Loading weight tables...")

        # Load signal weights
        signal_weights = await self.db.get_all_signal_weights()
        self.calculator.load_weights(signal_weights)
        print(f"   ✅ Loaded {len(signal_weights)} signal weights")

        # Load confidence modifiers
        # (We'll query per-source in real-time via decay_lookup_fn)
        print(f"   ✅ Weight tables loaded")
        print()

    def _group_signals(self, signals: List[Dict[str, Any]]) -> Dict[tuple, List[Dict[str, Any]]]:
        """
        Group signals by (person_unique_id, company_unique_id)

        Returns: {(person_id, company_id): [signal1, signal2, ...]}
        """
        grouped = {}

        for signal in signals:
            key = (signal['person_unique_id'], signal['company_unique_id'])

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(signal)

        return grouped

    async def _process_person_company(
        self,
        person_unique_id: str,
        company_unique_id: str,
        new_signals: List[Dict[str, Any]]
    ):
        """
        Process a single person/company combination

        Main logic:
        1. Get all signals (including previously scored)
        2. Calculate score
        3. Determine tier
        4. Evaluate trigger
        5. Write score + actions
        """
        try:
            self.stats['signals_processed'] += len(new_signals)

            # Get person data
            person_data = await self.db.get_person_data(person_unique_id)

            if not person_data:
                print(f"⚠️  Person {person_unique_id} not found, skipping")
                return

            name = person_data.get('full_name', 'Unknown')

            print(f"🔢 {name}: Calculating BIT score...")

            # Get current score (for comparison)
            current_score = await self.db.get_current_score(person_unique_id, company_unique_id)

            # Get ALL signals for this person/company (including old ones for full score)
            all_signals = await self.db.get_person_signals(
                person_unique_id,
                company_unique_id,
                include_scored=True
            )

            # Calculate score
            score_result = self.calculator.calculate_score(
                signals=all_signals,
                decay_lookup_fn=self.db.get_decay_factor,
                person_data=person_data
            )

            raw_score = score_result['raw_score']
            decayed_score = score_result['decayed_score']
            signal_count = score_result['signal_count']
            last_signal_at = score_result['last_signal_at']

            # Get thresholds
            thresholds = await self.db.get_trigger_thresholds()

            # Determine tier
            score_tier = self.calculator.get_score_tier(decayed_score, thresholds)

            print(f"   Raw: {raw_score}, Decayed: {decayed_score}, Tier: {score_tier}")

            # Safety check: validate score increase
            old_decayed = current_score['decayed_score'] if current_score else None
            validation = self.calculator.validate_score_increase(
                old_decayed,
                decayed_score,
                self.config['safety']['max_score_increase_per_day']
            )

            if not validation['valid']:
                print(f"   ⚠️  {validation['reason']}")
                decayed_score = validation['capped_score']

            # Write score to database
            score_id = await self.db.upsert_bit_score(
                person_unique_id=person_unique_id,
                company_unique_id=company_unique_id,
                raw_score=raw_score,
                decayed_score=decayed_score,
                score_tier=score_tier,
                last_signal_at=last_signal_at,
                signal_count=signal_count,
                metadata={
                    'worker_id': self.worker_id,
                    'process_id': self.process_id,
                    'breakdown': score_result['score_breakdown']
                }
            )

            if current_score:
                self.stats['scores_updated'] += 1
            else:
                self.stats['scores_calculated'] += 1

            # Evaluate trigger
            if self.config['trigger']['enabled']:
                await self._evaluate_and_trigger(
                    person_unique_id,
                    company_unique_id,
                    person_data,
                    decayed_score,
                    score_tier,
                    current_score,
                    score_result
                )

        except Exception as e:
            print(f"   ❌ Error processing {person_unique_id}: {str(e)}")
            self.stats['errors'] += 1
            await self._log_event('person_processing_error', {
                'person_id': person_unique_id,
                'error': str(e)
            }, severity='ERROR')

    async def _evaluate_and_trigger(
        self,
        person_unique_id: str,
        company_unique_id: str,
        person_data: Dict[str, Any],
        decayed_score: int,
        score_tier: str,
        old_score: Optional[Dict[str, Any]],
        score_result: Dict[str, Any]
    ):
        """
        Evaluate trigger conditions and fire actions

        Args:
            person_unique_id: Person ID
            company_unique_id: Company ID
            person_data: Person details
            decayed_score: Calculated score
            score_tier: Score tier (cold/warm/engaged/hot/burning)
            old_score: Previous score (or None)
            score_result: Full score calculation result
        """
        # Evaluate trigger
        trigger_result = self.evaluator.evaluate_trigger(
            decayed_score=decayed_score,
            score_tier=score_tier,
            person_data=person_data,
            old_score=old_score
        )

        if not trigger_result['should_trigger']:
            print(f"   ℹ️  No trigger: {trigger_result['reason']}")
            return

        action_type = trigger_result['action_type']
        priority = trigger_result['priority']

        # Check deduplication
        dedup = self.evaluator.check_deduplication(
            action_type,
            person_unique_id,
            self.db.check_recent_outreach
        )

        if dedup['is_duplicate']:
            print(f"   ⏸️  Skipped (duplicate): {dedup['reason']}")
            self.stats['skipped_duplicate'] += 1
            return

        # Validation passed, trigger action
        print(f"   🔔 TRIGGER: {action_type} (priority: {priority})")

        # Get score delta for reason
        score_delta = self.calculator.get_score_delta_analysis(old_score, {
            'decayed_score': decayed_score,
            'score_tier': score_tier
        })

        trigger_reason = self.evaluator.get_trigger_reason(trigger_result, score_delta)

        # Log to outreach_log
        if self.config['trigger']['auto_create_outreach_log']:
            outreach_id = await self.db.insert_outreach_log(
                person_unique_id=person_unique_id,
                company_unique_id=company_unique_id,
                action_type=action_type,
                bit_score=decayed_score,
                score_tier=score_tier,
                trigger_reason=trigger_reason,
                metadata={
                    **trigger_result['metadata'],
                    'worker_id': self.worker_id,
                    'process_id': self.process_id
                }
            )

            self.stats['triggers_fired'] += 1
            print(f"      → Outreach log created (ID: {outreach_id})")

        # Queue meeting if action is auto_meeting
        if action_type == 'auto_meeting' and self.config['trigger']['auto_queue_meetings']:
            meeting_check = self.evaluator.should_create_meeting(
                action_type,
                person_data,
                decayed_score
            )

            if meeting_check['should_queue']:
                meeting_id = await self.db.insert_meeting_queue(
                    person_unique_id=person_unique_id,
                    company_unique_id=company_unique_id,
                    bit_score=decayed_score,
                    priority=meeting_check['priority'],
                    metadata={
                        'trigger_reason': trigger_reason,
                        'worker_id': self.worker_id,
                        'process_id': self.process_id
                    }
                )

                self.stats['meetings_queued'] += 1
                print(f"      → Meeting queued (ID: {meeting_id}, priority: {meeting_check['priority']})")

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
        print("📊 BIT SCORING AGENT - EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Signals Processed: {self.stats['signals_processed']}")
        print(f"Scores Calculated: {self.stats['scores_calculated']}")
        print(f"Scores Updated: {self.stats['scores_updated']}")
        print(f"Triggers Fired: {self.stats['triggers_fired']}")
        print(f"  - Meetings Queued: {self.stats['meetings_queued']}")
        print(f"Skipped (Duplicate): {self.stats['skipped_duplicate']}")
        print(f"Skipped (Validation): {self.stats['skipped_validation']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)


if __name__ == "__main__":
    agent = BITScoringAgent()
    asyncio.run(agent.run())
