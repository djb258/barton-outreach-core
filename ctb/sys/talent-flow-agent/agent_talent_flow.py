"""
Talent Flow Agent - Movement Detection Engine
Barton Doctrine ID: 04.04.02.04.60000.001
CTB Layer: System (Yellow - AI/SHQ nerve)

Mission: Detect human movement (hires, exits, promotions, transfers) and convert to BIT signals

Architecture: Modular (config-driven, easy corrections)
- Config files control rules
- Core modules are standalone
- No hardcoded logic in main agent

Kill Switches:
- No reprocessing same hash
- No multi-pass on contradictions
- Cooldown period enforcement
- Max movements per person per month
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.neon_connector import NeonConnector
from core.diff_engine import DiffEngine
from core.movement_classifier import MovementClassifier
from core.confidence_scorer import ConfidenceScorer


class TalentFlowAgent:
    """
    Main orchestrator for talent flow detection

    Reads configs, coordinates modules, enforces safety rules
    """

    def __init__(self, config_dir: str = 'config'):
        """Initialize agent with configuration"""
        # Load configurations
        self.config = self._load_config(f'{config_dir}/agent_config.json')
        self.movement_rules = self._load_config(f'{config_dir}/movement_rules.json')
        self.confidence_config = self._load_config(f'{config_dir}/confidence_weights.json')

        # Initialize core modules
        self.db = NeonConnector(self.config)
        self.diff_engine = DiffEngine(self.movement_rules['hash_fields'])
        self.classifier = MovementClassifier(self.movement_rules)
        self.scorer = ConfidenceScorer(self.confidence_config)

        # Generate worker/process IDs
        self.worker_id = f"talent-flow-{uuid.uuid4().hex[:8]}"
        self.process_id = f"PRC-TF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Stats
        self.stats = {
            'processed': 0,
            'movements_detected': 0,
            'hires': 0,
            'exits': 0,
            'promotions': 0,
            'transfers': 0,
            'bit_signals_generated': 0,
            'snapshots_saved': 0,
            'contradictions_detected': 0,
            'skipped_cooldown': 0,
            'skipped_no_change': 0,
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
        2. Pull active people
        3. For each person:
           - Compute current hash
           - Compare to last snapshot
           - If changed → detect movement
           - Calculate confidence
           - Write movement + BIT signal
           - Save new snapshot
        4. Close connection
        """
        print(f"🚀 Talent Flow Agent Starting")
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

            # Pull active people
            lookback_days = self.config['processing']['lookback_days']
            people = await self.db.get_active_people(lookback_days)
            print(f"📊 Found {len(people)} people to process (last {lookback_days} days)")
            print()

            # Process in batches
            batch_size = self.config['processing']['batch_size']
            for i in range(0, len(people), batch_size):
                batch = people[i:i + batch_size]
                print(f"📦 Processing batch {i // batch_size + 1} ({len(batch)} people)")

                await self._process_batch(batch)

                print()

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

    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of people"""
        tasks = [self._process_person(person) for person in batch]

        if self.config['processing']['enable_parallel_processing']:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = [await task for task in tasks]

        # Count results
        for result in results:
            if isinstance(result, Exception):
                self.stats['errors'] += 1

    async def _process_person(self, person: Dict[str, Any]):
        """
        Process a single person

        Main logic:
        1. Compute hash
        2. Compare to last snapshot
        3. If changed → detect movement
        4. Calculate confidence
        5. Write results
        6. Save snapshot
        """
        person_id = person['person_unique_id']
        name = person.get('full_name', 'Unknown')

        try:
            self.stats['processed'] += 1

            # Safety check: Cooldown period
            cooldown_hours = self.config['safety']['cooldown_hours']
            if await self.db.check_recent_movement(person_id, cooldown_hours):
                print(f"⏸️  {name}: Skipped (cooldown)")
                self.stats['skipped_cooldown'] += 1
                return

            # Safety check: Max movements this month
            max_movements = self.config['safety']['max_movements_per_person_per_month']
            movement_count = await self.db.get_movement_count_this_month(person_id)
            if movement_count >= max_movements:
                print(f"⏸️  {name}: Skipped (max movements reached)")
                self.stats['skipped_cooldown'] += 1
                return

            # Compute current hash
            current_hash = self.diff_engine.compute_hash(person)

            # Get last snapshot
            last_snapshot = await self.db.get_person_snapshot(person_id)
            last_hash = last_snapshot['enrichment_hash'] if last_snapshot else None

            # Check if hash changed
            if not self.diff_engine.is_hash_different(current_hash, last_hash):
                print(f"   {name}: No change")
                self.stats['skipped_no_change'] += 1

                # Still save snapshot (update timestamp)
                await self.db.save_snapshot(person_id, current_hash, person)
                self.stats['snapshots_saved'] += 1
                return

            # Hash changed → detect movement
            print(f"🔄 {name}: Hash changed, analyzing...")

            old_state = last_snapshot['snapshot_data'] if last_snapshot else {}
            new_state = person

            # Detect changes
            changes = self.diff_engine.detect_changes(old_state, new_state)
            print(f"   Changed fields: {changes['changed_fields']}")

            # Check for contradictions
            if self.config['safety']['no_multipass_contradictions']:
                contradiction = self.diff_engine.check_contradiction(person_id, old_state, new_state, changes)
                if contradiction:
                    print(f"   ⚠️  Contradiction detected: {contradiction['contradictions']}")
                    self.stats['contradictions_detected'] += 1
                    # Log to Garage B (contradictions table)
                    await self._log_event('contradiction_detected', contradiction, severity='WARNING')
                    # Still continue processing (contradiction logged, not blocking)

            # Classify movement
            movement = self.classifier.classify(old_state, new_state, changes)

            if not movement:
                print(f"   ℹ️  No movement pattern matched")
                # Save snapshot anyway
                await self.db.save_snapshot(person_id, current_hash, new_state)
                self.stats['snapshots_saved'] += 1
                return

            # Calculate final confidence
            final_confidence = self.scorer.calculate_final_confidence(
                movement['base_confidence'],
                movement['movement_type'],
                person,
                movement['metadata']
            )

            confidence_tier = self.scorer.get_confidence_tier(final_confidence)

            print(f"   ✅ {movement['movement_type'].upper()}: {final_confidence:.2f} ({confidence_tier})")
            print(f"      Rules matched: {movement['matched_rules']}")

            # Write movement to database
            movement_id = await self.db.insert_movement(
                person_unique_id=person_id,
                movement_type=movement['movement_type'],
                confidence=final_confidence,
                old_state=old_state,
                new_state=new_state,
                data_source=person.get('data_source', 'unknown'),
                metadata={
                    **movement['metadata'],
                    'confidence_tier': confidence_tier,
                    'worker_id': self.worker_id,
                    'process_id': self.process_id
                }
            )

            self.stats['movements_detected'] += 1
            self.stats[f"{movement['movement_type']}s"] += 1

            # Generate BIT signal (if enabled)
            if self.config['bit_integration']['enabled']:
                await self._generate_bit_signal(person, movement, movement_id, final_confidence)

            # Save snapshot
            await self.db.save_snapshot(person_id, current_hash, new_state)
            self.stats['snapshots_saved'] += 1

        except Exception as e:
            print(f"   ❌ Error processing {name}: {str(e)}")
            self.stats['errors'] += 1
            await self._log_event('person_processing_error', {
                'person_id': person_id,
                'error': str(e)
            }, severity='ERROR')

    async def _generate_bit_signal(
        self,
        person: Dict[str, Any],
        movement: Dict[str, Any],
        movement_id: int,
        confidence: float
    ):
        """Generate BIT signal from movement"""
        movement_type = movement['movement_type']
        signal_weights = self.config['bit_integration']['movement_signal_weights']

        signal_weight = signal_weights.get(movement_type, 40)

        # Adjust signal weight by confidence
        adjusted_weight = int(signal_weight * confidence)

        await self.db.insert_bit_signal(
            person_unique_id=person['person_unique_id'],
            company_unique_id=person.get('company_unique_id', ''),
            signal_type=f'movement_{movement_type}',
            signal_weight=adjusted_weight,
            movement_id=movement_id,
            metadata={
                'movement_type': movement_type,
                'confidence': confidence,
                'worker_id': self.worker_id,
                'process_id': self.process_id
            }
        )

        self.stats['bit_signals_generated'] += 1
        print(f"      → BIT signal generated (weight: {adjusted_weight})")

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
        print("📊 TALENT FLOW AGENT - EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Processed: {self.stats['processed']}")
        print(f"Movements Detected: {self.stats['movements_detected']}")
        print(f"  - Hires: {self.stats['hires']}")
        print(f"  - Exits: {self.stats['exits']}")
        print(f"  - Promotions: {self.stats['promotions']}")
        print(f"  - Transfers: {self.stats['transfers']}")
        print(f"BIT Signals Generated: {self.stats['bit_signals_generated']}")
        print(f"Snapshots Saved: {self.stats['snapshots_saved']}")
        print(f"Contradictions Detected: {self.stats['contradictions_detected']}")
        print(f"Skipped (Cooldown): {self.stats['skipped_cooldown']}")
        print(f"Skipped (No Change): {self.stats['skipped_no_change']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)


if __name__ == "__main__":
    agent = TalentFlowAgent()
    asyncio.run(agent.run())
