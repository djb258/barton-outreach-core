"""
CSV Loader
Barton Doctrine ID: 04.04.02.04.80000.002

Parse and validate CSV files for backfill operations.
All CSV parsing logic lives here.
"""

import csv
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class CSVLoader:
    """
    Load and validate CSV files for backfill

    Design: Isolated CSV parsing with validation
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        self.config = config
        self.input_config = config['input']
        self.expected_columns = set(self.input_config['expected_columns'])
        self.required_columns = set(self.input_config['required_columns'])

    def load_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Load CSV file and return list of row dicts

        Args:
            csv_path: Path to CSV file

        Returns:
            List of row dictionaries
        """
        rows = []

        with open(csv_path, 'r', encoding=self.input_config['csv_encoding']) as f:
            reader = csv.DictReader(f)

            # Validate headers
            headers = set(reader.fieldnames or [])
            missing_required = self.required_columns - headers

            if missing_required:
                raise ValueError(f"Missing required columns: {missing_required}")

            # Read rows
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 = header)
                # Generate row hash for deduplication
                row_hash = self._compute_row_hash(row)

                # Add metadata
                row_data = {
                    **row,
                    '_row_number': row_num,
                    '_row_hash': row_hash,
                    '_loaded_at': datetime.now().isoformat()
                }

                rows.append(row_data)

        return rows

    def validate_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single row

        Args:
            row: Row dictionary

        Returns:
            {
                'valid': bool,
                'errors': [...],
                'warnings': [...]
            }
        """
        errors = []
        warnings = []

        # Check required columns
        for col in self.required_columns:
            if not row.get(col) or str(row.get(col, '')).strip() == '':
                errors.append(f"Missing required field: {col}")

        # Validate email format
        email = row.get('email', '')
        if email and not self._is_valid_email(email):
            warnings.append(f"Invalid email format: {email}")

        # Validate domain format
        domain = row.get('company_domain', '')
        if domain and not self._is_valid_domain(domain):
            warnings.append(f"Invalid domain format: {domain}")

        # Validate counts are numeric
        count_fields = ['historical_open_count', 'historical_reply_count', 'historical_meeting_count']
        for field in count_fields:
            value = row.get(field, '')
            if value and not self._is_numeric(value):
                warnings.append(f"Non-numeric count: {field} = {value}")

        # Validate date format
        last_engaged = row.get('last_engaged_at', '')
        if last_engaged and not self._is_valid_date(last_engaged):
            warnings.append(f"Invalid date format: last_engaged_at = {last_engaged}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _compute_row_hash(self, row: Dict[str, Any]) -> str:
        """
        Compute MD5 hash of row for deduplication

        Uses all data fields (excluding metadata like _row_number)
        """
        # Extract only data fields (not metadata)
        data_fields = {k: v for k, v in row.items() if not k.startswith('_')}

        # Sort and serialize
        hash_string = json.dumps(data_fields, sort_keys=True)

        # Compute MD5
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email:
            return False

        parts = email.split('@')
        if len(parts) != 2:
            return False

        local, domain = parts

        if not local or not domain:
            return False

        if '.' not in domain:
            return False

        return True

    def _is_valid_domain(self, domain: str) -> bool:
        """Basic domain validation"""
        if not domain:
            return False

        # Remove protocols and www
        domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')

        # Check for dot
        if '.' not in domain:
            return False

        # Check for spaces
        if ' ' in domain:
            return False

        return True

    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date string"""
        if not date_str or str(date_str).strip() == '':
            return True  # Blank is OK

        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]

        for fmt in formats:
            try:
                datetime.strptime(str(date_str).strip(), fmt)
                return True
            except ValueError:
                continue

        return False

    def get_summary(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics for loaded CSV

        Args:
            rows: List of loaded rows

        Returns:
            Summary dict
        """
        total_rows = len(rows)
        valid_rows = 0
        error_rows = 0
        warning_rows = 0

        validation_errors = []
        validation_warnings = []

        for row in rows:
            validation = self.validate_row(row)

            if validation['valid']:
                valid_rows += 1
            else:
                error_rows += 1

            if validation['warnings']:
                warning_rows += 1

            validation_errors.extend(validation['errors'])
            validation_warnings.extend(validation['warnings'])

        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'error_rows': error_rows,
            'warning_rows': warning_rows,
            'validation_errors': validation_errors[:20],  # First 20
            'validation_warnings': validation_warnings[:20],  # First 20
            'unique_hashes': len(set(row['_row_hash'] for row in rows))
        }
