"""
Diff Engine - Hash Comparison & Change Detection

CORRECTIONS LIVE HERE: All hash logic and diff detection isolated
"""

import json
from hashlib import md5
from typing import Dict, Any, List, Optional
from datetime import datetime


class DiffEngine:
    """
    Compute hashes and detect state changes

    All diff logic lives here - fix hash algorithms without touching other modules
    """

    def __init__(self, hash_fields: List[str]):
        self.hash_fields = hash_fields

    def compute_hash(self, person_data: Dict[str, Any]) -> str:
        """
        Compute deterministic hash from person data

        Uses specified fields from config (default: name, title, company, dates, linkedin)
        """
        # Extract only hash fields
        hash_data = {}
        for field in self.hash_fields:
            value = person_data.get(field)
            # Normalize: None, empty string, "null" all become empty
            if value in (None, '', 'null', 'NULL'):
                hash_data[field] = ''
            else:
                hash_data[field] = str(value).strip()

        # Sort keys for deterministic hashing
        hash_string = json.dumps(hash_data, sort_keys=True)
        return md5(hash_string.encode()).hexdigest()

    def detect_changes(
        self,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect what fields changed between states

        Returns:
            {
                'changed_fields': ['title', 'company_name'],
                'old_values': {'title': 'Engineer', 'company_name': 'Acme'},
                'new_values': {'title': 'Senior Engineer', 'company_name': 'Acme'},
                'has_changes': True
            }
        """
        changed_fields = []
        old_values = {}
        new_values = {}

        for field in self.hash_fields:
            old_val = self._normalize_value(old_state.get(field))
            new_val = self._normalize_value(new_state.get(field))

            if old_val != new_val:
                changed_fields.append(field)
                old_values[field] = old_val
                new_values[field] = new_val

        return {
            'changed_fields': changed_fields,
            'old_values': old_values,
            'new_values': new_values,
            'has_changes': len(changed_fields) > 0
        }

    def _normalize_value(self, value: Any) -> str:
        """Normalize value for comparison"""
        if value in (None, '', 'null', 'NULL'):
            return ''
        return str(value).strip()

    def is_hash_different(self, hash1: str, hash2: Optional[str]) -> bool:
        """Check if two hashes are different"""
        if hash2 is None:
            return True  # No previous snapshot = treat as changed
        return hash1 != hash2

    def extract_field_delta(
        self,
        field_name: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract specific field change details

        Example: title change from 'Engineer' to 'Senior Engineer'
        """
        old_val = self._normalize_value(old_state.get(field_name))
        new_val = self._normalize_value(new_state.get(field_name))

        return {
            'field': field_name,
            'old_value': old_val,
            'new_value': new_val,
            'changed': old_val != new_val,
            'was_null': old_val == '',
            'is_null': new_val == ''
        }

    def check_contradiction(
        self,
        person_unique_id: str,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect contradictions (e.g., multiple conflicting updates same day)

        Returns contradiction data if detected, None otherwise
        """
        # Check for suspicious patterns
        contradictions = []

        # Pattern 1: Company and title both change, but company_unique_id stays same
        if 'company_name' in changes['changed_fields'] and 'title' in changes['changed_fields']:
            old_company_id = old_state.get('company_unique_id')
            new_company_id = new_state.get('company_unique_id')
            if old_company_id == new_company_id and old_company_id:
                contradictions.append({
                    'type': 'company_name_mismatch',
                    'description': 'Company name changed but company_unique_id stayed same',
                    'severity': 'medium'
                })

        # Pattern 2: Title went backwards (promotion keywords removed)
        title_delta = self.extract_field_delta('title', old_state, new_state)
        if title_delta['changed']:
            if self._is_title_downgrade(title_delta['old_value'], title_delta['new_value']):
                contradictions.append({
                    'type': 'title_downgrade',
                    'description': f"Title went from '{title_delta['old_value']}' to '{title_delta['new_value']}'",
                    'severity': 'low'
                })

        # Pattern 3: End date in future
        end_date = new_state.get('end_date')
        if end_date and isinstance(end_date, datetime):
            if end_date > datetime.now():
                contradictions.append({
                    'type': 'future_end_date',
                    'description': f'End date is in the future: {end_date}',
                    'severity': 'high'
                })

        if contradictions:
            return {
                'person_unique_id': person_unique_id,
                'contradictions': contradictions,
                'detected_at': datetime.now().isoformat(),
                'old_state': old_state,
                'new_state': new_state
            }

        return None

    def _is_title_downgrade(self, old_title: str, new_title: str) -> bool:
        """Check if title appears to be a downgrade"""
        promotion_keywords = ['VP', 'SVP', 'Chief', 'Director', 'Senior', 'Lead', 'Head']

        old_has_keywords = any(kw.lower() in old_title.lower() for kw in promotion_keywords)
        new_has_keywords = any(kw.lower() in new_title.lower() for kw in promotion_keywords)

        # If old had keywords but new doesn't = possible downgrade
        return old_has_keywords and not new_has_keywords
