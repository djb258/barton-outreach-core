"""
Movement Classifier - Detect hire/exit/promotion/transfer

CORRECTIONS LIVE HERE: All movement detection rules isolated
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class MovementClassifier:
    """
    Classify movement type based on state changes

    All classification logic lives here - fix rules without touching other modules
    """

    def __init__(self, movement_rules: Dict[str, Any]):
        self.rules = movement_rules['movement_types']
        self.title_levels = movement_rules['title_levels']

    def classify(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Classify movement type from state delta

        Returns:
            {
                'movement_type': 'promotion',
                'base_confidence': 0.85,
                'matched_rules': ['title_changed AND company_unchanged AND title_level_increased'],
                'metadata': {...}
            }

        Returns None if no movement detected
        """
        if not changes['has_changes']:
            return None

        # Try each movement type
        for movement_type, rule_config in self.rules.items():
            match_result = self._check_movement_type(
                movement_type,
                rule_config,
                old_state,
                new_state,
                changes
            )

            if match_result and match_result['confidence'] >= rule_config['min_confidence']:
                return {
                    'movement_type': movement_type,
                    'base_confidence': match_result['confidence'],
                    'matched_rules': match_result['matched_rules'],
                    'metadata': match_result['metadata']
                }

        return None

    def _check_movement_type(
        self,
        movement_type: str,
        rule_config: Dict[str, Any],
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if state delta matches a specific movement type"""
        matched_rules = []
        total_weight = 0.0
        max_weight = 0.0

        for rule in rule_config['rules']:
            condition = rule['condition']
            weight = rule['weight']
            max_weight = max(max_weight, weight)

            if self._evaluate_condition(condition, old_state, new_state, changes, movement_type):
                matched_rules.append(condition)
                total_weight = max(total_weight, weight)  # Take highest matching rule weight

        if not matched_rules:
            return None

        # Confidence = highest matched rule weight
        confidence = total_weight

        metadata = self._extract_metadata(movement_type, old_state, new_state, changes)

        return {
            'confidence': confidence,
            'matched_rules': matched_rules,
            'metadata': metadata
        }

    def _evaluate_condition(
        self,
        condition: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any],
        movement_type: str
    ) -> bool:
        """
        Evaluate a rule condition

        Supported conditions:
        - company_name_changed
        - company_name_unchanged
        - title_changed
        - title_exists
        - title_null
        - title_level_increased
        - title_level_decreased
        - title_level_same
        - start_date_recent
        - end_date_exists
        - etc.
        """
        parts = condition.split(' AND ')
        return all(self._evaluate_single_condition(part.strip(), old_state, new_state, changes, movement_type) for part in parts)

    def _evaluate_single_condition(
        self,
        condition: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any],
        movement_type: str
    ) -> bool:
        """Evaluate a single condition"""
        # Company conditions
        if condition == 'company_name_changed':
            return 'company_name' in changes['changed_fields']
        if condition == 'company_name_unchanged' or condition == 'company_unchanged':
            return 'company_name' not in changes['changed_fields']

        # Title conditions
        if condition == 'title_changed':
            return 'title' in changes['changed_fields']
        if condition == 'title_exists':
            return bool(new_state.get('title'))
        if condition == 'title_null':
            return not new_state.get('title')
        if condition == 'previously_had_title':
            return bool(old_state.get('title'))

        # Title level conditions
        if condition == 'title_level_increased':
            return self._compare_title_levels(old_state.get('title'), new_state.get('title')) > 0
        if condition == 'title_level_decreased':
            return self._compare_title_levels(old_state.get('title'), new_state.get('title')) < 0
        if condition == 'title_level_same':
            return self._compare_title_levels(old_state.get('title'), new_state.get('title')) == 0

        # Promotion keywords
        if condition == 'title_keywords_match_promotion' and movement_type == 'promotion':
            promotion_keywords = self.rules['promotion'].get('promotion_keywords', [])
            new_title = new_state.get('title', '').lower()
            return any(kw.lower() in new_title for kw in promotion_keywords)

        # Date conditions
        if condition == 'start_date_recent':
            start_date = new_state.get('start_date')
            if start_date and isinstance(start_date, datetime):
                return (datetime.now() - start_date).days <= 90
            return False

        if condition == 'end_date_exists':
            return bool(new_state.get('end_date'))

        # Company null conditions
        if condition == 'previous_company_null':
            return not old_state.get('company_name')
        if condition == 'current_company_exists':
            return bool(new_state.get('company_name'))
        if condition == 'company_name_null':
            return not new_state.get('company_name')
        if condition == 'previously_had_company':
            return bool(old_state.get('company_name'))

        # Department conditions (if field exists)
        if condition == 'department_changed':
            return 'department' in changes['changed_fields']

        # Org layer conditions (if field exists)
        if condition == 'org_layer_increased':
            old_layer = old_state.get('org_layer', 0)
            new_layer = new_state.get('org_layer', 0)
            return new_layer > old_layer

        # Default: unknown condition = False
        return False

    def _compare_title_levels(self, old_title: Optional[str], new_title: Optional[str]) -> int:
        """
        Compare title seniority levels

        Returns:
            1 if new_title is more senior
            -1 if new_title is less senior
            0 if same level or can't determine
        """
        if not old_title or not new_title:
            return 0

        old_level = self._get_title_level(old_title)
        new_level = self._get_title_level(new_title)

        level_order = ['individual_contributor', 'management', 'senior_management', 'executive']

        try:
            old_idx = level_order.index(old_level)
            new_idx = level_order.index(new_level)

            if new_idx > old_idx:
                return 1
            elif new_idx < old_idx:
                return -1
            return 0
        except ValueError:
            return 0

    def _get_title_level(self, title: str) -> str:
        """Determine title level category"""
        title_lower = title.lower()

        for level, keywords in self.title_levels.items():
            if any(kw.lower() in title_lower for kw in keywords):
                return level

        return 'individual_contributor'  # Default

    def _extract_metadata(
        self,
        movement_type: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relevant metadata for this movement type"""
        metadata = {
            'changed_fields': changes['changed_fields'],
            'old_title': old_state.get('title'),
            'new_title': new_state.get('title'),
            'old_company': old_state.get('company_name'),
            'new_company': new_state.get('company_name')
        }

        if movement_type == 'hire':
            metadata['start_date'] = new_state.get('start_date')

        if movement_type == 'exit':
            metadata['end_date'] = new_state.get('end_date')

        if movement_type == 'promotion':
            metadata['old_level'] = self._get_title_level(old_state.get('title', ''))
            metadata['new_level'] = self._get_title_level(new_state.get('title', ''))

        return metadata
