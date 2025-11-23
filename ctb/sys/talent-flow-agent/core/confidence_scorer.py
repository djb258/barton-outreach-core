"""
Confidence Scorer - Calculate final confidence scores

CORRECTIONS LIVE HERE: All confidence calculation logic isolated
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ConfidenceScorer:
    """
    Calculate confidence scores based on data source, recency, completeness

    All scoring logic lives here - fix weights without touching other modules
    """

    def __init__(self, confidence_config: Dict[str, Any]):
        self.source_weights = confidence_config['data_source_weights']
        self.recency_multipliers = confidence_config['recency_multipliers']
        self.field_completeness_bonus = confidence_config['field_completeness_bonus']
        self.critical_fields = confidence_config['critical_fields']
        self.movement_modifiers = confidence_config['movement_confidence_modifiers']
        self.min_confidence = confidence_config['minimum_base_confidence']
        self.max_confidence = confidence_config['maximum_confidence']

    def calculate_final_confidence(
        self,
        base_confidence: float,
        movement_type: str,
        person_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate final confidence score

        Formula:
        final = base_confidence * source_weight * recency_multiplier + completeness_bonus + movement_bonus

        Capped at min/max confidence thresholds
        """
        # Start with base confidence from movement classifier
        score = base_confidence

        # Apply data source weight
        data_source = person_data.get('data_source', 'unknown')
        source_weight = self.source_weights.get(data_source, self.source_weights['unknown'])
        score *= source_weight

        # Apply recency multiplier
        updated_at = person_data.get('updated_at')
        if updated_at:
            recency_mult = self._get_recency_multiplier(updated_at)
            score *= recency_mult

        # Add field completeness bonus
        completeness_bonus = self._calculate_completeness_bonus(person_data)
        score += completeness_bonus

        # Add movement-specific modifiers
        movement_bonus = self._calculate_movement_bonus(movement_type, person_data, metadata)
        score += movement_bonus

        # Cap at min/max
        score = max(self.min_confidence, min(self.max_confidence, score))

        return round(score, 3)

    def _get_recency_multiplier(self, updated_at: datetime) -> float:
        """Get recency multiplier based on how recent the data is"""
        if not isinstance(updated_at, datetime):
            return self.recency_multipliers['days_365_plus']

        days_ago = (datetime.now() - updated_at).days

        if days_ago <= 7:
            return self.recency_multipliers['days_0_7']
        elif days_ago <= 30:
            return self.recency_multipliers['days_8_30']
        elif days_ago <= 90:
            return self.recency_multipliers['days_31_90']
        elif days_ago <= 180:
            return self.recency_multipliers['days_91_180']
        elif days_ago <= 365:
            return self.recency_multipliers['days_181_365']
        else:
            return self.recency_multipliers['days_365_plus']

    def _calculate_completeness_bonus(self, person_data: Dict[str, Any]) -> float:
        """Calculate bonus based on field completeness"""
        # Check critical fields
        critical_present = sum(1 for field in self.critical_fields if person_data.get(field))
        critical_total = len(self.critical_fields)

        if critical_present == critical_total:
            # Check all fields
            all_fields = ['full_name', 'title', 'company_name', 'linkedin_url', 'start_date', 'company_unique_id']
            all_present = sum(1 for field in all_fields if person_data.get(field))

            if all_present == len(all_fields):
                return self.field_completeness_bonus['all_fields_present']
            else:
                return self.field_completeness_bonus['critical_fields_present']
        elif critical_present >= 2:
            return self.field_completeness_bonus['partial_fields']
        else:
            return self.field_completeness_bonus['minimal_fields']

    def _calculate_movement_bonus(
        self,
        movement_type: str,
        person_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate bonus based on movement-specific indicators"""
        if movement_type not in self.movement_modifiers:
            return 0.0

        modifiers = self.movement_modifiers[movement_type]
        bonus = 0.0

        # Check each modifier condition
        for condition, value in modifiers.items():
            if self._check_modifier_condition(condition, person_data, metadata):
                bonus += value

        return bonus

    def _check_modifier_condition(
        self,
        condition: str,
        person_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> bool:
        """Check if a modifier condition is met"""
        if condition == 'has_start_date':
            return bool(person_data.get('start_date'))

        if condition == 'has_end_date':
            return bool(person_data.get('end_date'))

        if condition == 'linkedin_verified':
            linkedin_url = person_data.get('linkedin_url', '')
            return 'linkedin.com' in linkedin_url

        if condition == 'multiple_sources':
            # Would check if data came from multiple enrichment sources
            # For now, simplified check
            return person_data.get('data_source') in ['peopledatalabs', 'rocketreach', 'clearbit']

        if condition == 'title_level_clear':
            title = person_data.get('title', '')
            # Check if title has clear seniority indicators
            keywords = ['VP', 'SVP', 'Director', 'Manager', 'Senior', 'Lead', 'Chief']
            return any(kw.lower() in title.lower() for kw in keywords)

        if condition == 'same_company_verified':
            # Check if company_unique_id is present
            return bool(person_data.get('company_unique_id'))

        if condition == 'department_clear':
            # Would check if department field is present
            return 'department' in metadata

        return False

    def get_confidence_tier(self, confidence: float) -> str:
        """
        Get confidence tier label

        Returns: 'high', 'medium', 'low'
        """
        if confidence >= 0.85:
            return 'high'
        elif confidence >= 0.65:
            return 'medium'
        else:
            return 'low'
