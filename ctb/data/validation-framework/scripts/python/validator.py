#!/usr/bin/env python3
"""
============================================================================
Generic Validation & Promotion Framework - Python Validator
============================================================================
CTB Branch: data/validation-framework
Barton ID: 05.03.01
Purpose: Schema-agnostic validator for Neon → Supabase → Promotion flow
Last Updated: 2025-11-07
============================================================================

DOCTRINE COMPLIANCE:
- Every validation creates audit trail
- Failed records NEVER reach Neon master
- All operations logged for traceability
- Barton ID format enforced where applicable

USAGE:
    python validator.py --entity company --batch-size 100
    python validator.py --entity person --dry-run
    python validator.py --all-entities
"""

import os
import sys
import re
import json
import time
import yaml
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Loader
# ============================================================================

class ConfigLoader:
    """Loads and validates configuration from YAML"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config in same repo
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(base_path, 'config', 'validation_config.yaml')

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def get_entity_config(self, entity: str) -> Dict:
        """Get configuration for specific entity"""
        if entity not in self.config.get('entities', {}):
            raise ValueError(f"Entity '{entity}' not found in configuration")

        entity_config = self.config['entities'][entity]

        if not entity_config.get('enabled', True):
            raise ValueError(f"Entity '{entity}' is disabled in configuration")

        return entity_config

    def get_global_config(self) -> Dict:
        """Get global configuration"""
        return self.config.get('global', {})

    def get_rule_definitions(self) -> Dict:
        """Get rule definitions"""
        return self.config.get('rule_definitions', {})


# ============================================================================
# Database Connectors
# ============================================================================

class DatabaseConnector:
    """Manages connections to Neon and Supabase"""

    def __init__(self, global_config: Dict):
        self.global_config = global_config
        self.neon_conn = None
        self.supabase_conn = None

    def connect_neon(self) -> psycopg2.extensions.connection:
        """Connect to Neon (vault)"""
        if self.neon_conn and not self.neon_conn.closed:
            return self.neon_conn

        conn_string_env = self.global_config['neon']['connection_string_env']
        conn_string = os.getenv(conn_string_env)

        if not conn_string:
            raise ValueError(f"Environment variable {conn_string_env} not set")

        self.neon_conn = psycopg2.connect(conn_string)
        logger.info("Connected to Neon (vault)")
        return self.neon_conn

    def connect_supabase(self) -> psycopg2.extensions.connection:
        """Connect to Supabase (workspace)"""
        if self.supabase_conn and not self.supabase_conn.closed:
            return self.supabase_conn

        conn_string_env = self.global_config['supabase']['connection_string_env']
        conn_string = os.getenv(conn_string_env)

        if not conn_string:
            raise ValueError(f"Environment variable {conn_string_env} not set")

        self.supabase_conn = psycopg2.connect(conn_string)
        logger.info("Connected to Supabase (workspace)")
        return self.supabase_conn

    def close_all(self):
        """Close all connections"""
        if self.neon_conn and not self.neon_conn.closed:
            self.neon_conn.close()
            logger.info("Closed Neon connection")

        if self.supabase_conn and not self.supabase_conn.closed:
            self.supabase_conn.close()
            logger.info("Closed Supabase connection")


# ============================================================================
# Validation Rules Engine
# ============================================================================

class ValidationEngine:
    """Generic validation engine that applies rules dynamically"""

    def __init__(self, rule_definitions: Dict):
        self.rule_definitions = rule_definitions

    def validate_record(self, record: Dict, rules: List[Dict]) -> Tuple[bool, List[Dict], List[Dict]]:
        """
        Validate a single record against rules

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        for rule_config in rules:
            field = rule_config['field']
            rule_name = rule_config['rule']
            severity = rule_config.get('severity', 'warning')
            error_message = rule_config.get('error_message', f"{field} failed {rule_name}")
            params = rule_config.get('params', {})

            # Get field value
            value = record.get(field)

            # Apply rule
            is_valid, reason = self._apply_rule(rule_name, value, params)

            if not is_valid:
                error_obj = {
                    'field': field,
                    'rule': rule_name,
                    'severity': severity,
                    'message': error_message,
                    'reason': reason,
                    'value': str(value) if value is not None else None
                }

                if severity == 'critical':
                    errors.append(error_obj)
                else:
                    warnings.append(error_obj)

        # Determine overall validity
        is_valid = len(errors) == 0

        return is_valid, errors, warnings

    def _apply_rule(self, rule_name: str, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """
        Apply a single validation rule

        Returns:
            (is_valid, reason_if_invalid)
        """
        # Map rule names to validation functions
        rules_map = {
            'not_null': self._rule_not_null,
            'min_length': self._rule_min_length,
            'max_length': self._rule_max_length,
            'starts_with': self._rule_starts_with,
            'ends_with': self._rule_ends_with,
            'contains': self._rule_contains,
            'regex_match': self._rule_regex_match,
            'email_format': self._rule_email_format,
            'phone_format': self._rule_phone_format,
            'url_format': self._rule_url_format,
            'positive_integer': self._rule_positive_integer,
            'positive_number': self._rule_positive_number,
            'in_range': self._rule_in_range,
        }

        if rule_name not in rules_map:
            return False, f"Unknown rule: {rule_name}"

        try:
            return rules_map[rule_name](value, params)
        except Exception as e:
            return False, f"Rule execution failed: {str(e)}"

    # ──────────────────────────────────────────────────────────────
    # Rule Implementations
    # ──────────────────────────────────────────────────────────────

    def _rule_not_null(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must not be None or empty"""
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return False, "Value is null or empty"
        return True, None

    def _rule_min_length(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must have minimum length"""
        if value is None:
            return False, "Value is null"
        min_len = params.get('length', 1)
        if len(str(value)) < min_len:
            return False, f"Length {len(str(value))} < minimum {min_len}"
        return True, None

    def _rule_max_length(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must not exceed maximum length"""
        if value is None:
            return True, None  # Null is ok for max_length
        max_len = params.get('length', 255)
        if len(str(value)) > max_len:
            return False, f"Length {len(str(value))} > maximum {max_len}"
        return True, None

    def _rule_starts_with(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must start with prefix"""
        if value is None:
            return False, "Value is null"
        prefix = params.get('prefix', '')
        if not str(value).startswith(prefix):
            return False, f"Does not start with '{prefix}'"
        return True, None

    def _rule_ends_with(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must end with suffix"""
        if value is None:
            return False, "Value is null"
        suffix = params.get('suffix', '')
        if not str(value).endswith(suffix):
            return False, f"Does not end with '{suffix}'"
        return True, None

    def _rule_contains(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must contain substring"""
        if value is None:
            return False, "Value is null"
        substring = params.get('substring', '')
        if substring not in str(value):
            return False, f"Does not contain '{substring}'"
        return True, None

    def _rule_regex_match(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """String must match regex pattern"""
        if value is None:
            return False, "Value is null"
        pattern = params.get('pattern', '')
        if not re.match(pattern, str(value)):
            return False, f"Does not match pattern '{pattern}'"
        return True, None

    def _rule_email_format(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be valid email"""
        if value is None:
            return False, "Value is null"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, str(value)):
            return False, "Invalid email format"
        return True, None

    def _rule_phone_format(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be valid phone"""
        if value is None:
            return False, "Value is null"
        pattern = r'^\+?1?\d{9,15}$'
        if not re.match(pattern, str(value).replace('-', '').replace(' ', '')):
            return False, "Invalid phone format"
        return True, None

    def _rule_url_format(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be valid URL"""
        if value is None:
            return False, "Value is null"
        pattern = r'^https?://[^\s]+$'
        if not re.match(pattern, str(value)):
            return False, "Invalid URL format"
        return True, None

    def _rule_positive_integer(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be positive integer"""
        if value is None:
            return False, "Value is null"
        try:
            num = int(value)
            if num <= 0:
                return False, f"Value {num} is not positive"
            return True, None
        except (ValueError, TypeError):
            return False, "Not a valid integer"

    def _rule_positive_number(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be positive number"""
        if value is None:
            return False, "Value is null"
        try:
            num = float(value)
            if num <= 0:
                return False, f"Value {num} is not positive"
            return True, None
        except (ValueError, TypeError):
            return False, "Not a valid number"

    def _rule_in_range(self, value: Any, params: Dict) -> Tuple[bool, Optional[str]]:
        """Value must be within range"""
        if value is None:
            return False, "Value is null"
        try:
            num = float(value)
            min_val = params.get('min', float('-inf'))
            max_val = params.get('max', float('inf'))
            if num < min_val or num > max_val:
                return False, f"Value {num} not in range [{min_val}, {max_val}]"
            return True, None
        except (ValueError, TypeError):
            return False, "Not a valid number"


# ============================================================================
# Main Validator
# ============================================================================

class GenericValidator:
    """
    Main validation orchestrator

    Handles the complete flow:
    1. Fetch from Neon source
    2. Load into Supabase workspace
    3. Validate
    4. Promote valid records
    5. Flag invalid for enrichment
    """

    def __init__(self, entity: str, config_loader: ConfigLoader, db_connector: DatabaseConnector):
        self.entity = entity
        self.entity_config = config_loader.get_entity_config(entity)
        self.global_config = config_loader.get_global_config()
        self.db_connector = db_connector

        self.validation_engine = ValidationEngine(config_loader.get_rule_definitions())

        self.stats = {
            'fetched': 0,
            'validated': 0,
            'passed': 0,
            'failed': 0,
            'promoted': 0,
            'errors': 0,
            'start_time': time.time()
        }

    def run(self, batch_size: int = None, dry_run: bool = False):
        """
        Run the complete validation and promotion pipeline

        Args:
            batch_size: Number of records to process (default from config)
            dry_run: If True, don't write to databases
        """
        if batch_size is None:
            batch_size = self.global_config.get('batch_size', 100)

        logger.info(f"Starting validation for entity '{self.entity}' (batch_size={batch_size}, dry_run={dry_run})")

        try:
            # Step 1: Fetch unprocessed records from Neon
            records = self._fetch_from_neon(batch_size)
            self.stats['fetched'] = len(records)

            if not records:
                logger.info("No unprocessed records found")
                return self.stats

            logger.info(f"Fetched {len(records)} records from Neon")

            # Step 2: Load into Supabase workspace
            if not dry_run:
                self._load_to_supabase(records)

            # Step 3: Validate records
            validation_results = self._validate_records(records)

            # Step 4: Update Supabase with validation results
            if not dry_run:
                self._update_validation_status(validation_results)

            # Step 5: Promote valid records back to Neon
            valid_records = [r for r in validation_results if r['is_valid']]
            if valid_records and not dry_run:
                self._promote_to_neon(valid_records)

            # Step 6: Mark as processed in Neon source
            if not dry_run:
                self._mark_as_processed([r['record']['unique_id'] for r in records])

            # Calculate stats
            self.stats['validated'] = len(records)
            self.stats['passed'] = len([r for r in validation_results if r['is_valid']])
            self.stats['failed'] = len([r for r in validation_results if not r['is_valid']])
            self.stats['promoted'] = len(valid_records)
            self.stats['duration'] = time.time() - self.stats['start_time']

            self._log_summary()

            return self.stats

        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            raise

    def _fetch_from_neon(self, batch_size: int) -> List[Dict]:
        """Fetch unprocessed records from Neon source table"""
        conn = self.db_connector.connect_neon()
        source_table = self.entity_config['source_table']
        key_field = self.entity_config['key_field']

        query = f"""
            SELECT *
            FROM {source_table}
            WHERE processed_at IS NULL
            LIMIT %s
        """

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (batch_size,))
            records = cur.fetchall()

        return [{'unique_id': r[key_field], 'record': dict(r)} for r in records]

    def _load_to_supabase(self, records: List[Dict]):
        """Load records into Supabase workspace table"""
        conn = self.db_connector.connect_supabase()
        workspace_table = f"public.{self.entity_config['workspace_table']}"

        values = [(r['unique_id'], json.dumps(r['record'])) for r in records]

        query = f"""
            INSERT INTO {workspace_table} (unique_id, payload, validation_status)
            VALUES %s
            ON CONFLICT (unique_id) DO UPDATE
            SET payload = EXCLUDED.payload,
                validation_status = 'PENDING',
                updated_at = now()
        """

        with conn.cursor() as cur:
            execute_values(cur, query, values)
            conn.commit()

        logger.info(f"Loaded {len(records)} records into Supabase workspace")

    def _validate_records(self, records: List[Dict]) -> List[Dict]:
        """Validate all records"""
        rules = self.entity_config.get('rules', [])
        results = []

        for record_wrapper in records:
            record = record_wrapper['record']
            unique_id = record_wrapper['unique_id']

            is_valid, errors, warnings = self.validation_engine.validate_record(record, rules)

            results.append({
                'unique_id': unique_id,
                'record': record,
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings
            })

            if not is_valid:
                logger.warning(f"Record {unique_id} failed validation: {len(errors)} errors")

        return results

    def _update_validation_status(self, validation_results: List[Dict]):
        """Update validation status in Supabase"""
        conn = self.db_connector.connect_supabase()
        workspace_table = f"public.{self.entity_config['workspace_table']}"

        with conn.cursor() as cur:
            for result in validation_results:
                status = 'PASSED' if result['is_valid'] else 'FAILED'

                query = f"""
                    UPDATE {workspace_table}
                    SET validation_status = %s,
                        validation_errors = %s,
                        validation_warnings = %s,
                        last_validated_at = now()
                    WHERE unique_id = %s
                """

                cur.execute(query, (
                    status,
                    json.dumps(result['errors']),
                    json.dumps(result['warnings']),
                    result['unique_id']
                ))

            conn.commit()

        logger.info(f"Updated validation status for {len(validation_results)} records")

    def _promote_to_neon(self, valid_records: List[Dict]):
        """Promote valid records to Neon master table"""
        conn = self.db_connector.connect_neon()
        target_table = self.entity_config['target_table']
        field_mapping = self.entity_config.get('field_mapping', {})

        # Build insert query dynamically
        target_fields = list(field_mapping.values())
        placeholders = ', '.join(['%s'] * len(target_fields))

        query = f"""
            INSERT INTO {target_table} ({', '.join(target_fields)})
            VALUES ({placeholders})
            ON CONFLICT ({target_fields[0]}) DO UPDATE
            SET {', '.join([f"{f} = EXCLUDED.{f}" for f in target_fields[1:]])}
        """

        with conn.cursor() as cur:
            for result in valid_records:
                record = result['record']
                # Map fields from source to target
                values = [record.get(source_field) for source_field in field_mapping.keys()]

                cur.execute(query, values)

            conn.commit()

        logger.info(f"Promoted {len(valid_records)} records to Neon master")

    def _mark_as_processed(self, unique_ids: List[str]):
        """Mark source records as processed"""
        conn = self.db_connector.connect_neon()
        source_table = self.entity_config['source_table']
        key_field = self.entity_config['key_field']

        query = f"""
            UPDATE {source_table}
            SET processed_at = now()
            WHERE {key_field} = ANY(%s)
        """

        with conn.cursor() as cur:
            cur.execute(query, (unique_ids,))
            conn.commit()

        logger.info(f"Marked {len(unique_ids)} records as processed")

    def _log_summary(self):
        """Log validation summary"""
        logger.info("=" * 60)
        logger.info(f"Validation Summary - Entity: {self.entity}")
        logger.info("=" * 60)
        logger.info(f"Fetched: {self.stats['fetched']}")
        logger.info(f"Validated: {self.stats['validated']}")
        logger.info(f"Passed: {self.stats['passed']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Promoted: {self.stats['promoted']}")
        logger.info(f"Duration: {self.stats['duration']:.2f}s")
        logger.info("=" * 60)


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Generic Validation & Promotion Framework')
    parser.add_argument('--entity', type=str, help='Entity to validate (company, person, etc.)')
    parser.add_argument('--all-entities', action='store_true', help='Validate all enabled entities')
    parser.add_argument('--batch-size', type=int, help='Batch size (overrides config)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no database writes)')
    parser.add_argument('--config', type=str, help='Path to config file')

    args = parser.parse_args()

    if not args.entity and not args.all_entities:
        parser.error("Must specify --entity or --all-entities")

    # Load configuration
    config_loader = ConfigLoader(args.config)

    # Initialize database connector
    db_connector = DatabaseConnector(config_loader.get_global_config())

    try:
        if args.all_entities:
            # Process all enabled entities
            entities = config_loader.config['entities']
            for entity_name, entity_config in entities.items():
                if entity_config.get('enabled', True):
                    logger.info(f"\n\nProcessing entity: {entity_name}\n")
                    validator = GenericValidator(entity_name, config_loader, db_connector)
                    validator.run(batch_size=args.batch_size, dry_run=args.dry_run)
        else:
            # Process single entity
            validator = GenericValidator(args.entity, config_loader, db_connector)
            validator.run(batch_size=args.batch_size, dry_run=args.dry_run)

    finally:
        db_connector.close_all()


if __name__ == '__main__':
    main()
