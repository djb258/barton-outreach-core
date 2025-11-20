"""
Baseline Generator
Barton Doctrine ID: 04.04.02.04.80000.005

Generate initial BIT and Talent Flow baselines from historical data.
All baseline creation logic lives here.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaselineGenerator:
    """
    Generate BIT and Talent Flow baselines from historical engagement data

    Design: Transform historical counts into initial state
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.baseline_config = config['baseline_generation']
        self.bit_config = self.baseline_config['bit_baseline']
        self.tf_config = self.baseline_config['talent_flow_baseline']

    def generate_bit_baseline(
        self,
        person_unique_id: str,
        company_unique_id: str,
        normalized_row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate BIT baseline from historical engagement counts

        Args:
            person_unique_id: Person unique ID
            company_unique_id: Company unique ID
            normalized_row: Normalized backfill row with historical counts

        Returns:
            {
                'person_unique_id': str,
                'company_unique_id': str,
                'historical_open_count': int,
                'historical_reply_count': int,
                'historical_meeting_count': int,
                'last_engaged_at': str | None,
                'baseline_score': int,
                'baseline_tier': str,
                'signals_to_generate': [...]
            }
        """
        # Extract historical counts
        open_count = normalized_row.get('historical_open_count', 0)
        reply_count = normalized_row.get('historical_reply_count', 0)
        meeting_count = normalized_row.get('historical_meeting_count', 0)
        last_engaged_at = normalized_row.get('last_engaged_at')

        # Get signal weights from config
        signal_weights = self.bit_config['signal_weights']
        open_weight = signal_weights.get('historical_open', 5)
        reply_weight = signal_weights.get('historical_reply', 30)
        meeting_weight = signal_weights.get('historical_meeting', 50)

        # Calculate baseline score
        baseline_score = (
            (open_count * open_weight) +
            (reply_count * reply_weight) +
            (meeting_count * meeting_weight)
        )

        # Determine baseline tier
        baseline_tier = self._calculate_baseline_tier(baseline_score)

        # Generate signals (if enabled)
        signals_to_generate = []

        if self.bit_config.get('generate_bit_signals', True):
            # Generate signal for each historical event type
            if open_count > 0:
                signals_to_generate.append({
                    'signal_type': 'historical_open',
                    'signal_weight': open_weight * open_count,
                    'source_type': 'backfill_baseline',
                    'metadata': {
                        'count': open_count,
                        'unit_weight': open_weight
                    }
                })

            if reply_count > 0:
                signals_to_generate.append({
                    'signal_type': 'historical_reply',
                    'signal_weight': reply_weight * reply_count,
                    'source_type': 'backfill_baseline',
                    'metadata': {
                        'count': reply_count,
                        'unit_weight': reply_weight
                    }
                })

            if meeting_count > 0:
                signals_to_generate.append({
                    'signal_type': 'historical_meeting',
                    'signal_weight': meeting_weight * meeting_count,
                    'source_type': 'backfill_baseline',
                    'metadata': {
                        'count': meeting_count,
                        'unit_weight': meeting_weight
                    }
                })

        return {
            'person_unique_id': person_unique_id,
            'company_unique_id': company_unique_id,
            'historical_open_count': open_count,
            'historical_reply_count': reply_count,
            'historical_meeting_count': meeting_count,
            'last_engaged_at': last_engaged_at,
            'baseline_score': baseline_score,
            'baseline_tier': baseline_tier,
            'signals_to_generate': signals_to_generate,
            'signals_generated': len(signals_to_generate)
        }

    def generate_talent_flow_baseline(
        self,
        person_unique_id: str,
        normalized_row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Talent Flow baseline snapshot

        Args:
            person_unique_id: Person unique ID
            normalized_row: Normalized backfill row

        Returns:
            {
                'person_unique_id': str,
                'enrichment_hash': str,
                'snapshot_data': {...},
                'baseline_date': str
            }
        """
        # Get hash fields from config
        hash_fields = self.tf_config.get('hash_fields', [])

        # Compute enrichment hash
        enrichment_hash = self._compute_talent_flow_hash(normalized_row, hash_fields)

        # Create snapshot data (full person record)
        snapshot_data = {
            'full_name': normalized_row.get('full_name', ''),
            'first_name': normalized_row.get('first_name', ''),
            'last_name': normalized_row.get('last_name', ''),
            'title': normalized_row.get('title', ''),
            'company_name': normalized_row.get('company_name', ''),
            'company_domain': normalized_row.get('company_domain', ''),
            'email': normalized_row.get('email', ''),
            'phone': normalized_row.get('phone', ''),
            'linkedin_url': normalized_row.get('linkedin_url', ''),
            'last_engaged_at': normalized_row.get('last_engaged_at')
        }

        return {
            'person_unique_id': person_unique_id,
            'enrichment_hash': enrichment_hash,
            'snapshot_data': snapshot_data,
            'baseline_date': datetime.now().strftime('%Y-%m-%d')
        }

    def _calculate_baseline_tier(self, baseline_score: int) -> str:
        """
        Determine baseline tier from score

        Uses same thresholds as BIT Scoring Agent
        """
        if baseline_score >= 300:
            return 'burning'
        elif baseline_score >= 200:
            return 'hot'
        elif baseline_score >= 100:
            return 'engaged'
        elif baseline_score >= 50:
            return 'warm'
        else:
            return 'cold'

    def _compute_talent_flow_hash(
        self,
        person_data: Dict[str, Any],
        hash_fields: List[str]
    ) -> str:
        """
        Compute MD5 hash for Talent Flow baseline

        Same logic as Talent Flow Agent's diff engine
        """
        hash_data = {}

        for field in hash_fields:
            value = person_data.get(field, '')

            # Normalize value for hashing
            if isinstance(value, str):
                value = value.lower().strip()
            elif value is None:
                value = ''

            hash_data[field] = value

        # Sort and serialize
        hash_string = json.dumps(hash_data, sort_keys=True)

        # Compute MD5
        return hashlib.md5(hash_string.encode()).hexdigest()

    def should_generate_baseline(
        self,
        normalized_row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if baseline should be generated for this row

        Args:
            normalized_row: Normalized backfill row

        Returns:
            {
                'should_generate_bit': bool,
                'should_generate_tf': bool,
                'reason': str
            }
        """
        # Check if BIT baseline should be generated
        should_bit = self.bit_config.get('enabled', True)

        # Only generate if there's engagement history
        has_engagement = (
            normalized_row.get('historical_open_count', 0) > 0 or
            normalized_row.get('historical_reply_count', 0) > 0 or
            normalized_row.get('historical_meeting_count', 0) > 0
        )

        if should_bit and not has_engagement:
            should_bit = False

        # Check if Talent Flow baseline should be generated
        should_tf = self.tf_config.get('enabled', True)

        # Only generate if we have required fields
        required_tf_fields = ['full_name', 'title', 'company_name']
        has_tf_fields = all(normalized_row.get(field) for field in required_tf_fields)

        if should_tf and not has_tf_fields:
            should_tf = False

        # Determine reason
        reasons = []

        if not should_bit and not should_tf:
            reasons.append("No engagement history and missing TF fields")
        elif not should_bit:
            reasons.append("No engagement history")
        elif not should_tf:
            reasons.append("Missing required TF fields")
        else:
            reasons.append("All baselines enabled and data present")

        return {
            'should_generate_bit': should_bit,
            'should_generate_tf': should_tf,
            'reason': '; '.join(reasons)
        }

    def get_baseline_summary(
        self,
        bit_baseline: Optional[Dict[str, Any]],
        tf_baseline: Optional[Dict[str, Any]]
    ) -> str:
        """
        Get human-readable baseline summary

        Args:
            bit_baseline: BIT baseline result (or None)
            tf_baseline: TF baseline result (or None)

        Returns:
            Summary string
        """
        parts = []

        # BIT baseline
        if bit_baseline:
            score = bit_baseline['baseline_score']
            tier = bit_baseline['baseline_tier']
            signals = bit_baseline['signals_generated']
            parts.append(f"BIT: {score} pts ({tier} tier, {signals} signals)")
        else:
            parts.append("BIT: Skipped")

        # TF baseline
        if tf_baseline:
            parts.append("TF: Snapshot created")
        else:
            parts.append("TF: Skipped")

        return " | ".join(parts)
