"""
Validator (Neon Agent) Backend - Barton Toolbox Hub
Barton ID: 04.04.02.04.10000.002
Altitude: 18000ft

Validation engine powered by Neon-stored rules for company data, executive slots, and enrichment results.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.composio_client import ComposioClient, ComposioMCPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Barton Doctrine IDs
TOOL_BARTON_ID = "04.04.02.04.10000.002"
BLUEPRINT_ID = "04.svg.marketing.outreach.v1"


class ValidationSeverity(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Validation rule definition"""
    rule_id: int
    rule_name: str
    rule_type: str  # field_required, field_format, field_range, cross_field, etc.
    table_name: str
    field_name: str
    validation_logic: Dict
    severity: ValidationSeverity
    error_message: str
    enabled: bool = True


@dataclass
class ValidationResult:
    """Result of a validation check"""
    passed: bool
    rule_name: str
    severity: ValidationSeverity
    error_message: Optional[str] = None
    field_name: Optional[str] = None
    actual_value: Any = None


class NeonDatabase:
    """Neon PostgreSQL database connector"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info(f"[{TOOL_BARTON_ID}] Connected to Neon database")
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Database connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"[{TOOL_BARTON_ID}] Disconnected from Neon database")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Query execution failed: {e}")
            raise

    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Execute INSERT query and return row ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()
                if cur.rowcount > 0 and cur.description:
                    return cur.fetchone()[0]
                return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"[{TOOL_BARTON_ID}] Insert execution failed: {e}")
            raise

    def log_audit(self, event_type: str, event_data: Dict, user_id: str = "system"):
        """Log event to shq.audit_log"""
        query = """
            INSERT INTO shq.audit_log
            (event_type, event_data, user_id, barton_id, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING audit_id
        """
        params = (event_type, json.dumps(event_data), user_id, TOOL_BARTON_ID)
        return self.execute_insert(query, params)

    def log_error(self, error_code: str, error_message: str, severity: str = "error", context: Dict = None):
        """Log error to shq.error_master"""
        try:
            query = """
                INSERT INTO shq.error_master
                (error_code, error_message, severity, component, context, barton_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING error_id
            """
            params = (
                error_code,
                error_message,
                severity,
                "validator",
                json.dumps(context or {}),
                TOOL_BARTON_ID
            )
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log error: {e}")


class ValidationEngine:
    """Core validation engine"""

    def __init__(self, db: NeonDatabase):
        self.db = db
        self.rules: List[ValidationRule] = []
        self.validation_count = 0
        self.failure_count = 0

    def load_validation_rules(self, table_name: Optional[str] = None):
        """Load validation rules from Neon database"""
        query = """
            SELECT
                rule_id,
                rule_name,
                rule_type,
                table_name,
                field_name,
                validation_logic,
                severity,
                error_message,
                enabled
            FROM marketing.validation_rules
            WHERE enabled = true
        """
        params = None

        if table_name:
            query += " AND table_name = %s"
            params = (table_name,)

        query += " ORDER BY rule_id"

        results = self.db.execute_query(query, params)

        self.rules = [
            ValidationRule(
                rule_id=row['rule_id'],
                rule_name=row['rule_name'],
                rule_type=row['rule_type'],
                table_name=row['table_name'],
                field_name=row['field_name'],
                validation_logic=row['validation_logic'],
                severity=ValidationSeverity(row['severity']),
                error_message=row['error_message'],
                enabled=row['enabled']
            )
            for row in results
        ]

        logger.info(f"[{TOOL_BARTON_ID}] Loaded {len(self.rules)} validation rules")

    def validate_field_required(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """Validate that required field is not null/empty"""
        passed = value is not None and value != ""

        return ValidationResult(
            passed=passed,
            rule_name=rule.rule_name,
            severity=rule.severity,
            error_message=rule.error_message if not passed else None,
            field_name=rule.field_name,
            actual_value=value
        )

    def validate_field_format(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """Validate field format (email, phone, URL, etc.)"""
        import re

        if value is None:
            return ValidationResult(passed=True, rule_name=rule.rule_name, severity=rule.severity)

        pattern = rule.validation_logic.get('pattern', '.*')
        passed = bool(re.match(pattern, str(value)))

        return ValidationResult(
            passed=passed,
            rule_name=rule.rule_name,
            severity=rule.severity,
            error_message=rule.error_message if not passed else None,
            field_name=rule.field_name,
            actual_value=value
        )

    def validate_field_range(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """Validate field value is within acceptable range"""
        if value is None:
            return ValidationResult(passed=True, rule_name=rule.rule_name, severity=rule.severity)

        min_val = rule.validation_logic.get('min')
        max_val = rule.validation_logic.get('max')

        passed = True
        if min_val is not None and value < min_val:
            passed = False
        if max_val is not None and value > max_val:
            passed = False

        return ValidationResult(
            passed=passed,
            rule_name=rule.rule_name,
            severity=rule.severity,
            error_message=rule.error_message if not passed else None,
            field_name=rule.field_name,
            actual_value=value
        )

    def validate_record(self, record: Dict, table_name: str) -> List[ValidationResult]:
        """Validate a single record against all applicable rules"""
        results = []

        # Filter rules for this table
        table_rules = [r for r in self.rules if r.table_name == table_name]

        for rule in table_rules:
            field_value = record.get(rule.field_name)

            # Apply appropriate validation based on rule type
            if rule.rule_type == "field_required":
                result = self.validate_field_required(field_value, rule)
            elif rule.rule_type == "field_format":
                result = self.validate_field_format(field_value, rule)
            elif rule.rule_type == "field_range":
                result = self.validate_field_range(field_value, rule)
            else:
                # Unknown rule type
                logger.warning(f"[{TOOL_BARTON_ID}] Unknown rule type: {rule.rule_type}")
                continue

            results.append(result)
            self.validation_count += 1

            if not result.passed:
                self.failure_count += 1

        return results

    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            "total_validations": self.validation_count,
            "total_failures": self.failure_count,
            "success_rate": (
                (self.validation_count - self.failure_count) / self.validation_count * 100
                if self.validation_count > 0 else 0
            ),
            "active_rules": len(self.rules)
        }


class Validator:
    """Main Validator class"""

    def __init__(self, connection_string: str):
        self.db = NeonDatabase(connection_string)
        self.engine = ValidationEngine(self.db)
        self.composio = ComposioClient()

    def initialize(self):
        """Initialize validator and load rules"""
        self.db.connect()
        self.engine.load_validation_rules()

        logger.info(f"[{TOOL_BARTON_ID}] Validator initialized with {len(self.engine.rules)} rules")

        # Log initialization
        self.db.log_audit("validator.initialized", {
            "barton_id": TOOL_BARTON_ID,
            "blueprint_id": BLUEPRINT_ID,
            "rules_loaded": len(self.engine.rules),
            "timestamp": datetime.now().isoformat()
        })

    def shutdown(self):
        """Shutdown validator"""
        stats = self.engine.get_validation_stats()

        # Log shutdown with stats
        self.db.log_audit("validator.shutdown", {
            "barton_id": TOOL_BARTON_ID,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })

        self.db.disconnect()
        logger.info(f"[{TOOL_BARTON_ID}] Validator shutdown")

    def validate_companies(self, limit: int = 100) -> Dict:
        """Validate company records"""
        # Get companies to validate
        query = """
            SELECT *
            FROM marketing.company_master
            ORDER BY updated_at DESC
            LIMIT %s
        """
        companies = self.db.execute_query(query, (limit,))

        logger.info(f"[{TOOL_BARTON_ID}] Validating {len(companies)} companies")

        validation_summary = {
            "total_records": len(companies),
            "records_with_failures": 0,
            "total_failures": 0,
            "failures_by_severity": {}
        }

        for company in companies:
            results = self.engine.validate_record(company, "company_master")

            # Check for failures
            failures = [r for r in results if not r.passed]
            if failures:
                validation_summary["records_with_failures"] += 1
                validation_summary["total_failures"] += len(failures)

                # Log to pipeline_errors if critical
                critical_failures = [f for f in failures if f.severity == ValidationSeverity.CRITICAL]
                if critical_failures:
                    self.log_pipeline_error(company, critical_failures)

        # Log summary
        self.db.log_audit("validation.companies_validated", validation_summary)

        return validation_summary

    def log_pipeline_error(self, record: Dict, failures: List[ValidationResult]):
        """Log validation failures to pipeline_errors table"""
        for failure in failures:
            query = """
                INSERT INTO marketing.pipeline_errors
                (company_unique_id, error_type, error_message, error_payload, resolution_status, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            params = (
                record.get('company_unique_id'),
                'validation_failure',
                failure.error_message,
                json.dumps({
                    "rule": failure.rule_name,
                    "field": failure.field_name,
                    "value": str(failure.actual_value),
                    "severity": failure.severity.value
                }),
                'pending'
            )
            self.db.execute_insert(query, params)

    def export_failures_to_sheet(self, failures_data: List[Dict]) -> Optional[str]:
        """
        Export validation failures to Google Sheet for review

        Args:
            failures_data: List of failure dictionaries with record + failure info

        Returns:
            Google Sheet ID if successful, None otherwise
        """
        if not failures_data:
            logger.warning(f"[{TOOL_BARTON_ID}] No failures to export")
            return None

        try:
            # Prepare sheet data
            sheet_title = f"Validation Failures - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            headers = [
                "Company ID",
                "Company Name",
                "Rule Name",
                "Field Name",
                "Current Value",
                "Severity",
                "Error Message",
                "Status",
                "Corrected Value"
            ]

            # Convert failures to rows
            data = []
            for item in failures_data:
                record = item.get('record', {})
                failure = item.get('failure', {})

                row = [
                    str(record.get('company_unique_id', '')),
                    str(record.get('company_name', '')),
                    str(failure.get('rule_name', '')),
                    str(failure.get('field_name', '')),
                    str(failure.get('actual_value', '')),
                    str(failure.get('severity', '')),
                    str(failure.get('error_message', '')),
                    'PENDING REVIEW',
                    ''  # Empty column for manual correction
                ]
                data.append(row)

            # Create sheet via Composio MCP
            unique_id = f"HEIR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-VALIDATOR-EXPORT"

            sheet_id = self.composio.create_google_sheet(
                title=sheet_title,
                data=data,
                headers=headers,
                unique_id=unique_id
            )

            # Log successful export
            self.db.log_audit("validation.failures_exported", {
                "barton_id": TOOL_BARTON_ID,
                "sheet_id": sheet_id,
                "failures_count": len(failures_data),
                "sheet_title": sheet_title
            })

            logger.info(f"[{TOOL_BARTON_ID}] ✅ Exported {len(failures_data)} failure(s) to sheet: {sheet_id}")

            return sheet_id

        except ComposioMCPError as e:
            logger.error(f"[{TOOL_BARTON_ID}] Composio MCP error: {e}")
            self.db.log_error("composio_mcp_failed", str(e), "error", {
                "action": "export_failures",
                "failures_count": len(failures_data)
            })
            return None
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Unexpected error: {e}")
            self.db.log_error("sheet_export_failed", str(e), "error", {
                "failures_count": len(failures_data)
            })
            return None


def main():
    """Main entry point"""
    logger.info(f"[{TOOL_BARTON_ID}] Starting Validator (Neon Agent)")

    # Load configuration
    connection_string = os.getenv("NEON_CONNECTION_STRING", "")

    if not connection_string:
        logger.error(f"[{TOOL_BARTON_ID}] NEON_CONNECTION_STRING not set")
        return

    # Initialize validator
    validator = Validator(connection_string)
    validator.initialize()

    try:
        # Run validation
        summary = validator.validate_companies(limit=100)

        logger.info(f"[{TOOL_BARTON_ID}] Validation complete: {summary}")

    except Exception as e:
        logger.error(f"[{TOOL_BARTON_ID}] Fatal error: {e}")
        validator.db.log_error("fatal_error", str(e), "critical")
    finally:
        # Cleanup
        validator.shutdown()


if __name__ == "__main__":
    main()
