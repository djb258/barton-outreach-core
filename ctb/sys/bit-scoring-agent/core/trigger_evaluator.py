"""
Trigger Evaluator
Barton Doctrine ID: 04.04.02.04.70000.004

Evaluates score thresholds and determines actions.
No vibes. Pure rules.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class TriggerEvaluator:
    """
    Evaluate BIT score thresholds and determine actions

    Design: Configuration-driven trigger logic
    """

    def __init__(self, trigger_config: Dict[str, Any]):
        """Initialize with trigger configuration"""
        self.config = trigger_config
        self.trigger_levels = trigger_config['trigger_levels']
        self.action_rules = trigger_config['action_rules']
        self.deduplication = trigger_config['deduplication']

    def evaluate_trigger(
        self,
        decayed_score: int,
        score_tier: str,
        person_data: Dict[str, Any],
        old_score: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if score triggers an action

        Args:
            decayed_score: Current BIT score
            score_tier: Score tier (cold/warm/engaged/hot/burning)
            person_data: Person details for validation
            old_score: Previous score (for tier change detection)

        Returns:
            {
                'should_trigger': bool,
                'action_type': str,
                'priority': str,
                'reason': str,
                'validation_passed': bool,
                'metadata': {...}
            }
        """
        # Get trigger level config
        trigger_level = self.trigger_levels.get(score_tier)

        if not trigger_level:
            return {
                'should_trigger': False,
                'action_type': None,
                'priority': 'none',
                'reason': f'Unknown tier: {score_tier}',
                'validation_passed': False,
                'metadata': {}
            }

        # Check if auto-execute enabled
        if not trigger_level.get('auto_execute', False):
            return {
                'should_trigger': False,
                'action_type': trigger_level['action'],
                'priority': trigger_level.get('priority', 'low'),
                'reason': 'Auto-execute disabled for this tier',
                'validation_passed': True,
                'metadata': {'manual_review_required': True}
            }

        # Check if tier changed (only trigger on tier increase)
        tier_changed = self._check_tier_change(old_score, score_tier)

        if not tier_changed and old_score is not None:
            return {
                'should_trigger': False,
                'action_type': trigger_level['action'],
                'priority': trigger_level.get('priority', 'low'),
                'reason': 'Tier unchanged (already triggered)',
                'validation_passed': True,
                'metadata': {'tier': score_tier}
            }

        # Get action type
        action_type = trigger_level['action']

        # Validate action requirements
        validation = self._validate_action_requirements(action_type, person_data)

        if not validation['valid']:
            return {
                'should_trigger': False,
                'action_type': action_type,
                'priority': trigger_level.get('priority', 'low'),
                'reason': f"Validation failed: {validation['reason']}",
                'validation_passed': False,
                'metadata': validation['missing_fields']
            }

        # All checks passed
        return {
            'should_trigger': True,
            'action_type': action_type,
            'priority': trigger_level.get('priority', 'medium'),
            'reason': f"Score tier: {score_tier} ({decayed_score} points)",
            'validation_passed': True,
            'metadata': {
                'tier': score_tier,
                'score': decayed_score,
                'tier_changed': tier_changed,
                'nurture_sequence': trigger_level.get('nurture_sequence'),
                'meeting_priority': trigger_level.get('meeting_priority')
            }
        }

    def _check_tier_change(
        self,
        old_score: Optional[Dict[str, Any]],
        new_tier: str
    ) -> bool:
        """
        Check if score tier increased

        Returns True if tier changed (or first score), False if same
        """
        if not old_score:
            return True  # First score, always trigger

        old_tier = old_score.get('score_tier', 'cold')

        # Define tier hierarchy
        tier_order = ['cold', 'warm', 'engaged', 'hot', 'burning']

        try:
            old_index = tier_order.index(old_tier)
            new_index = tier_order.index(new_tier)
            return new_index > old_index  # Only trigger on increase
        except ValueError:
            # Unknown tier, assume changed
            return True

    def _validate_action_requirements(
        self,
        action_type: str,
        person_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate person data meets action requirements

        Returns:
            {
                'valid': bool,
                'reason': str,
                'missing_fields': {...}
            }
        """
        action_rules = self.action_rules.get(action_type, {})

        missing = {}

        # Check email requirement
        if action_rules.get('require_email', False):
            if not person_data.get('email'):
                missing['email'] = 'required'

        # Check phone requirement
        if action_rules.get('require_email_or_phone', False):
            if not person_data.get('email') and not person_data.get('phone'):
                missing['contact_method'] = 'email or phone required'

        if missing:
            return {
                'valid': False,
                'reason': 'Missing required contact information',
                'missing_fields': missing
            }

        return {
            'valid': True,
            'reason': 'All requirements met',
            'missing_fields': {}
        }

    def get_trigger_reason(
        self,
        trigger_result: Dict[str, Any],
        score_delta: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable trigger reason

        Args:
            trigger_result: Output from evaluate_trigger()
            score_delta: Output from ScoreCalculator.get_score_delta_analysis()

        Returns:
            Formatted reason string
        """
        if not trigger_result['should_trigger']:
            return trigger_result['reason']

        tier = trigger_result['metadata'].get('tier', 'unknown')
        score = trigger_result['metadata'].get('score', 0)

        if score_delta['is_new']:
            return f"Initial BIT score: {score} ({tier} tier)"

        delta = score_delta['delta']
        old_tier = score_delta['old_tier']
        new_tier = score_delta['new_tier']

        if score_delta['tier_changed']:
            return f"Tier escalation: {old_tier} → {new_tier} (+{delta} points, now {score})"

        return f"Score increase: +{delta} points (now {score}, {tier} tier)"

    def should_create_meeting(
        self,
        action_type: str,
        person_data: Dict[str, Any],
        score: int
    ) -> Dict[str, Any]:
        """
        Determine if contact should be queued for meeting

        Args:
            action_type: Triggered action type
            person_data: Person details
            score: BIT score

        Returns:
            {
                'should_queue': bool,
                'priority': str,
                'reason': str
            }
        """
        if action_type != 'auto_meeting':
            return {
                'should_queue': False,
                'priority': 'none',
                'reason': f'Action type {action_type} does not queue meetings'
            }

        meeting_rules = self.action_rules.get('auto_meeting', {})

        # Check if email exists
        if meeting_rules.get('require_email', False) and not person_data.get('email'):
            return {
                'should_queue': False,
                'priority': 'none',
                'reason': 'Email required for meeting scheduling'
            }

        # Determine priority based on score
        if score >= 500:
            priority = 'urgent'
        elif score >= 300:
            priority = 'high'
        else:
            priority = 'medium'

        return {
            'should_queue': True,
            'priority': priority,
            'reason': f'High BIT score ({score}) warrants urgent meeting'
        }

    def check_deduplication(
        self,
        action_type: str,
        person_unique_id: str,
        recent_outreach_check_fn
    ) -> Dict[str, Any]:
        """
        Check if action should be skipped due to recent duplicate

        Args:
            action_type: Action type to check
            person_unique_id: Person ID
            recent_outreach_check_fn: Function(person_id, action, window_hours) -> bool

        Returns:
            {
                'is_duplicate': bool,
                'reason': str
            }
        """
        if not self.deduplication['enabled']:
            return {
                'is_duplicate': False,
                'reason': 'Deduplication disabled'
            }

        window_hours = self.deduplication['window_hours']

        # Check if same action triggered recently
        is_recent = recent_outreach_check_fn(
            person_unique_id,
            action_type,
            window_hours
        )

        if is_recent:
            return {
                'is_duplicate': True,
                'reason': f'Same action triggered within {window_hours} hours'
            }

        return {
            'is_duplicate': False,
            'reason': 'No recent duplicate found'
        }

    def get_action_priority_score(self, action_type: str) -> int:
        """
        Get numeric priority for action type

        Used for queue sorting
        """
        priority_map = {
            'ignore': 0,
            'watch': 10,
            'nurture': 50,
            'sdr_escalate': 100,
            'auto_meeting': 200
        }

        return priority_map.get(action_type, 0)
