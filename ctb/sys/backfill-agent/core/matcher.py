"""
Matcher - Perfect and Fuzzy Matching
Barton Doctrine ID: 04.04.02.04.80000.004

Match backfill records against existing company_master and people_master tables.
All matching logic lives here.
"""

from typing import Dict, Any, List, Optional, Tuple
import difflib


class Matcher:
    """
    Match backfill records against existing database records

    Design: Perfect match first, then fuzzy match with confidence scores
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.matching_config = config['matching']
        self.perfect_match_config = self.matching_config['perfect_match']
        self.fuzzy_match_config = self.matching_config['fuzzy_match']
        self.locked_fields = set(self.matching_config['locked_fields'])

    def match_company(
        self,
        normalized_row: Dict[str, Any],
        existing_companies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match company against existing company_master records

        Args:
            normalized_row: Normalized backfill row
            existing_companies: List of existing company records

        Returns:
            {
                'match_type': 'perfect_company' | 'fuzzy_company' | 'no_match',
                'match_confidence': float,
                'matched_company': {...} | None,
                'reason': str
            }
        """
        # Try perfect match first
        perfect_match = self._perfect_match_company(normalized_row, existing_companies)
        if perfect_match:
            return {
                'match_type': 'perfect_company',
                'match_confidence': 1.0,
                'matched_company': perfect_match,
                'reason': 'Perfect domain match'
            }

        # Try fuzzy match
        if self.fuzzy_match_config.get('enable_fuzzy_matching', True):
            fuzzy_result = self._fuzzy_match_company(normalized_row, existing_companies)
            if fuzzy_result['confidence'] >= self.fuzzy_match_config['company_name_threshold']:
                return {
                    'match_type': 'fuzzy_company',
                    'match_confidence': fuzzy_result['confidence'],
                    'matched_company': fuzzy_result['company'],
                    'reason': f"Fuzzy name match ({fuzzy_result['confidence']:.2f} confidence)"
                }

        # No match
        return {
            'match_type': 'no_match',
            'match_confidence': 0.0,
            'matched_company': None,
            'reason': 'No company match found'
        }

    def match_person(
        self,
        normalized_row: Dict[str, Any],
        company_unique_id: str,
        existing_people: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match person against existing people_master records

        Args:
            normalized_row: Normalized backfill row
            company_unique_id: Matched company ID
            existing_people: List of existing person records (filtered by company)

        Returns:
            {
                'match_type': 'perfect_person' | 'fuzzy_person' | 'no_match',
                'match_confidence': float,
                'matched_person': {...} | None,
                'reason': str
            }
        """
        # Try perfect match first
        perfect_match = self._perfect_match_person(normalized_row, existing_people)
        if perfect_match:
            return {
                'match_type': 'perfect_person',
                'match_confidence': 1.0,
                'matched_person': perfect_match,
                'reason': 'Perfect email or LinkedIn match'
            }

        # Try fuzzy match
        if self.fuzzy_match_config.get('enable_fuzzy_matching', True):
            fuzzy_result = self._fuzzy_match_person(normalized_row, existing_people)
            if fuzzy_result['confidence'] >= self.fuzzy_match_config['person_name_threshold']:
                return {
                    'match_type': 'fuzzy_person',
                    'match_confidence': fuzzy_result['confidence'],
                    'matched_person': fuzzy_result['person'],
                    'reason': f"Fuzzy name match ({fuzzy_result['confidence']:.2f} confidence)"
                }

        # No match
        return {
            'match_type': 'no_match',
            'match_confidence': 0.0,
            'matched_person': None,
            'reason': 'No person match found'
        }

    def _perfect_match_company(
        self,
        normalized_row: Dict[str, Any],
        existing_companies: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Perfect match company by domain

        Returns matched company or None
        """
        domain = normalized_row.get('company_domain', '').lower()

        if not domain:
            return None

        for company in existing_companies:
            company_domain = company.get('company_domain', '').lower()

            if domain == company_domain:
                return company

        return None

    def _perfect_match_person(
        self,
        normalized_row: Dict[str, Any],
        existing_people: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Perfect match person by email or LinkedIn URL

        Returns matched person or None
        """
        email = normalized_row.get('email', '').lower()
        linkedin_url = normalized_row.get('linkedin_url', '').lower()

        for person in existing_people:
            # Check LinkedIn URL (strongest signal)
            if linkedin_url and person.get('linkedin_url', '').lower() == linkedin_url:
                return person

            # Check email
            if email and person.get('email', '').lower() == email:
                return person

        return None

    def _fuzzy_match_company(
        self,
        normalized_row: Dict[str, Any],
        existing_companies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fuzzy match company by name

        Returns:
            {
                'confidence': float,
                'company': {...} | None
            }
        """
        company_name = normalized_row.get('company_name', '').lower()

        if not company_name:
            return {'confidence': 0.0, 'company': None}

        best_match = None
        best_confidence = 0.0

        for company in existing_companies:
            existing_name = company.get('company_name', '').lower()

            if not existing_name:
                continue

            # Calculate similarity
            confidence = self._calculate_string_similarity(company_name, existing_name)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = company

        return {
            'confidence': best_confidence,
            'company': best_match
        }

    def _fuzzy_match_person(
        self,
        normalized_row: Dict[str, Any],
        existing_people: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Fuzzy match person by name

        Returns:
            {
                'confidence': float,
                'person': {...} | None
            }
        """
        full_name = normalized_row.get('full_name', '').lower()
        first_name = normalized_row.get('first_name', '').lower()
        last_name = normalized_row.get('last_name', '').lower()

        if not (full_name or (first_name and last_name)):
            return {'confidence': 0.0, 'person': None}

        best_match = None
        best_confidence = 0.0

        for person in existing_people:
            existing_full = person.get('full_name', '').lower()
            existing_first = person.get('first_name', '').lower()
            existing_last = person.get('last_name', '').lower()

            # Try full name match
            if full_name and existing_full:
                confidence = self._calculate_string_similarity(full_name, existing_full)
            # Try first + last name match
            elif first_name and last_name and existing_first and existing_last:
                first_conf = self._calculate_string_similarity(first_name, existing_first)
                last_conf = self._calculate_string_similarity(last_name, existing_last)
                confidence = (first_conf + last_conf) / 2
            else:
                confidence = 0.0

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = person

        return {
            'confidence': best_confidence,
            'person': best_match
        }

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings

        Uses SequenceMatcher (Levenshtein-like)

        Returns:
            Similarity score (0.0 - 1.0)
        """
        if not str1 or not str2:
            return 0.0

        # Normalize whitespace
        str1 = ' '.join(str1.split())
        str2 = ' '.join(str2.split())

        # Calculate similarity
        return difflib.SequenceMatcher(None, str1, str2).ratio()

    def check_locked_fields(self, existing_record: Dict[str, Any]) -> List[str]:
        """
        Check which fields are locked in existing record

        Args:
            existing_record: Existing database record

        Returns:
            List of locked field names
        """
        locked = []

        for field in self.locked_fields:
            if existing_record.get(field):
                locked.append(field)

        # Also check if there's a locked_fields array
        if 'locked_fields' in existing_record and existing_record['locked_fields']:
            locked.extend(existing_record['locked_fields'])

        return list(set(locked))

    def should_update_field(
        self,
        field_name: str,
        existing_record: Dict[str, Any],
        new_value: Any
    ) -> bool:
        """
        Determine if field should be updated

        Args:
            field_name: Field name
            existing_record: Existing database record
            new_value: New value from backfill

        Returns:
            True if should update, False if should skip
        """
        # Check if field is locked
        locked_fields = self.check_locked_fields(existing_record)

        if field_name in locked_fields:
            return False

        # Don't overwrite existing value with empty value
        existing_value = existing_record.get(field_name)

        if existing_value and not new_value:
            return False

        # OK to update
        return True

    def merge_records(
        self,
        existing_record: Dict[str, Any],
        backfill_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge backfill record into existing record (respecting locked fields)

        Args:
            existing_record: Existing database record
            backfill_record: Normalized backfill record

        Returns:
            Merged record with updates
        """
        merged = existing_record.copy()

        # Track which fields were updated
        updated_fields = []

        for field, new_value in backfill_record.items():
            # Skip metadata fields
            if field.startswith('_'):
                continue

            # Check if should update
            if self.should_update_field(field, existing_record, new_value):
                merged[field] = new_value
                updated_fields.append(field)

        # Add metadata
        merged['_backfill_updated'] = True
        merged['_backfill_updated_fields'] = updated_fields

        return merged

    def get_match_summary(
        self,
        company_match: Dict[str, Any],
        person_match: Dict[str, Any]
    ) -> str:
        """
        Get human-readable match summary

        Args:
            company_match: Company match result
            person_match: Person match result

        Returns:
            Summary string
        """
        parts = []

        # Company match
        if company_match['match_type'] == 'perfect_company':
            parts.append("✓ Company: Perfect match")
        elif company_match['match_type'] == 'fuzzy_company':
            conf = company_match['match_confidence']
            parts.append(f"~ Company: Fuzzy match ({conf:.2f})")
        else:
            parts.append("✗ Company: No match")

        # Person match
        if person_match['match_type'] == 'perfect_person':
            parts.append("✓ Person: Perfect match")
        elif person_match['match_type'] == 'fuzzy_person':
            conf = person_match['match_confidence']
            parts.append(f"~ Person: Fuzzy match ({conf:.2f})")
        else:
            parts.append("✗ Person: No match")

        return " | ".join(parts)
