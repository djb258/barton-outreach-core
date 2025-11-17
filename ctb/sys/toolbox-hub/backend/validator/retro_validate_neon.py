"""
Retroactive Neon Data Validator - Barton Toolbox Hub
Validates existing West Virginia company and people data in Neon database
Routes failures to Google Sheets via n8n webhooks

Doctrine ID: 04.04.02.04.10000.002
Blueprint: 04.svg.marketing.outreach.v1

Usage:
    python backend/validator/retro_validate_neon.py --state WV
    python backend/validator/retro_validate_neon.py --state WV --limit 100
    python backend/validator/retro_validate_neon.py --state WV --dry-run
"""

import os
import sys
import json
import argparse
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Warning: python-dotenv not installed. Using system environment variables only.")

# Import validation rules
try:
    from validator.validation_rules import validate_company, validate_person
except ImportError:
    print("❌ Error: validation_rules.py not found. Make sure it exists in validator/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class RetroValidationStats:
    """Track retroactive validation statistics"""

    def __init__(self):
        # Company stats
        self.companies_total = 0
        self.companies_valid = 0
        self.companies_invalid = 0
        self.companies_routed = 0

        # People stats
        self.people_total = 0
        self.people_valid = 0
        self.people_invalid = 0
        self.people_routed = 0

        # Webhook stats
        self.webhook_success = 0
        self.webhook_failed = 0

        # Timing
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self) -> Dict:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return {
            "companies": {
                "total": self.companies_total,
                "valid": self.companies_valid,
                "invalid": self.companies_invalid,
                "routed_to_sheets": self.companies_routed
            },
            "people": {
                "total": self.people_total,
                "valid": self.people_valid,
                "invalid": self.people_invalid,
                "routed_to_sheets": self.people_routed
            },
            "webhooks": {
                "success": self.webhook_success,
                "failed": self.webhook_failed
            },
            "duration_seconds": round(duration, 2),
            "timestamp": self.end_time.isoformat() if self.end_time else None
        }


class RetroValidator:
    """Retroactive validator for existing Neon data"""

    def __init__(self, connection_string: str, dry_run: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.stats = RetroValidationStats()
        self.conn = None
        self.cursor = None

        # n8n webhook URLs
        self.company_webhook = os.getenv("N8N_COMPANY_FAILURE_WEBHOOK")
        self.person_webhook = os.getenv("N8N_PERSON_FAILURE_WEBHOOK")

        # Generate unique pipeline ID
        self.pipeline_id = f"RETRO-VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not dry_run:
            try:
                self.conn = psycopg2.connect(connection_string)
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                logger.info("✅ Connected to Neon database")
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {e}")
                raise

        # Warn if webhooks not configured
        if not self.company_webhook:
            logger.warning("⚠️  N8N_COMPANY_FAILURE_WEBHOOK not configured - company routing will be skipped")
        if not self.person_webhook:
            logger.warning("⚠️  N8N_PERSON_FAILURE_WEBHOOK not configured - person routing will be skipped")

    def __del__(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def load_companies(self, state: str = "WV", limit: Optional[int] = None) -> List[Dict]:
        """Load companies from Neon database"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would load companies from {state}")
            return []

        try:
            query = """
                SELECT *
                FROM marketing.company_master
                WHERE state = %s
                  AND (validation_status IS NULL OR validation_status = 'pending')
            """

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query, (state,))
            companies = self.cursor.fetchall()

            logger.info(f"✅ Loaded {len(companies)} companies from {state}")
            return [dict(c) for c in companies]

        except Exception as e:
            logger.error(f"❌ Failed to load companies: {e}")
            raise

    def load_people(self, state: str = "WV", limit: Optional[int] = None) -> List[Dict]:
        """Load people from Neon database"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would load people from {state}")
            return []

        try:
            query = """
                SELECT p.*
                FROM marketing.people_master p
                JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
                WHERE c.state = %s
                  AND (p.validation_status IS NULL OR p.validation_status = 'pending')
            """

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query, (state,))
            people = self.cursor.fetchall()

            logger.info(f"✅ Loaded {len(people)} people from {state}")
            return [dict(p) for p in people]

        except Exception as e:
            logger.error(f"❌ Failed to load people: {e}")
            raise

    def get_valid_company_ids(self) -> set:
        """Get set of valid company unique IDs for person validation"""
        if self.dry_run:
            return set()

        try:
            query = "SELECT company_unique_id FROM marketing.company_master"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return {r['company_unique_id'] for r in results}
        except Exception as e:
            logger.warning(f"⚠️  Failed to load valid company IDs: {e}")
            return set()

    def route_to_n8n(self, record_type: str, record: Dict, failures: List[Dict], state: str) -> bool:
        """
        Route invalid record to n8n webhook

        n8n will handle routing to Google Sheets
        """
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would route {record_type} to n8n webhook")
            return True

        # Select webhook based on record type
        webhook_url = self.company_webhook if record_type == "company" else self.person_webhook

        if not webhook_url:
            logger.warning(f"⚠️  No webhook configured for {record_type} - skipping route")
            return False

        # Prepare webhook payload
        payload = {
            "type": record_type,
            "reason_code": ", ".join([f"{f['field']}: {f['message']}" for f in failures]),
            "row_data": record,
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "pipeline_id": self.pipeline_id,
            "failures": failures,
            "sheet_id": os.getenv("GOOGLE_SHEET_ID", "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg"),
            "sheet_tab": "Invalid_Companies" if record_type == "company" else "Invalid_People"
        }

        # POST to n8n webhook
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code >= 200 and response.status_code < 300:
                logger.debug(f"✅ Routed {record_type} to n8n webhook (HTTP {response.status_code})")
                self.stats.webhook_success += 1
                return True
            else:
                logger.warning(f"⚠️  n8n webhook returned HTTP {response.status_code}")

                # Retry once on 5xx errors
                if response.status_code >= 500:
                    logger.info("🔄 Retrying webhook request...")
                    retry_response = requests.post(webhook_url, json=payload, timeout=30)

                    if retry_response.status_code >= 200 and retry_response.status_code < 300:
                        logger.info(f"✅ Retry successful (HTTP {retry_response.status_code})")
                        self.stats.webhook_success += 1
                        return True

                self.stats.webhook_failed += 1
                return False

        except requests.exceptions.Timeout:
            logger.error(f"❌ Webhook request timed out for {record_type}")
            self.stats.webhook_failed += 1
            return False
        except Exception as e:
            logger.error(f"❌ Webhook request failed: {e}")
            self.stats.webhook_failed += 1
            return False

    def log_to_pipeline_events(self, event_type: str, record_type: str, record_id: str, passed: bool, reason: str = ""):
        """Log validation event to pipeline_events table"""
        if self.dry_run:
            return

        try:
            query = """
                INSERT INTO marketing.pipeline_events
                (event_type, payload, created_at)
                VALUES (%s, %s, NOW())
            """

            payload = {
                "record_type": record_type,
                "record_id": record_id,
                "passed": passed,
                "reason": reason,
                "pipeline_id": self.pipeline_id
            }

            self.cursor.execute(query, (event_type, json.dumps(payload)))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to log to pipeline_events: {e}")

    def log_to_audit(self, component: str, message: str, event_data: Dict = None):
        """Log to shq.audit_log table"""
        if self.dry_run:
            return

        try:
            query = """
                INSERT INTO shq.audit_log
                (component, event_type, event_data, created_at)
                VALUES (%s, %s, %s, NOW())
            """

            event_data = event_data or {}
            event_data["pipeline_id"] = self.pipeline_id

            self.cursor.execute(query, (
                component,
                "retro_validation",
                json.dumps(event_data)
            ))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to log to audit_log: {e}")

    def update_validation_status(self, table: str, id_field: str, record_id: str, status: str):
        """Update validation_status field in database"""
        if self.dry_run:
            return

        try:
            query = f"""
                UPDATE marketing.{table}
                SET validation_status = %s,
                    updated_at = NOW()
                WHERE {id_field} = %s
            """

            self.cursor.execute(query, (status, record_id))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to update validation_status: {e}")

    def validate_companies(self, companies: List[Dict], state: str) -> List[Dict]:
        """Validate all companies and route failures"""
        invalid_companies = []

        logger.info(f"\n{'='*60}")
        logger.info(f"Validating {len(companies)} Companies")
        logger.info(f"{'='*60}")

        for company in companies:
            self.stats.companies_total += 1
            company_id = company.get("company_unique_id", "unknown")
            company_name = company.get("company_name", "Unknown")

            # Validate company
            is_valid, failures = validate_company(company, state=state)

            if is_valid:
                self.stats.companies_valid += 1
                logger.debug(f"✅ {company_name}: VALID")

                # Update status to valid
                if not self.dry_run:
                    self.update_validation_status("company_master", "company_unique_id", company_id, "valid")

                # Log to pipeline_events
                self.log_to_pipeline_events(
                    event_type="validation_check",
                    record_type="company",
                    record_id=company_id,
                    passed=True
                )
            else:
                self.stats.companies_invalid += 1
                failure_summary = ", ".join([f"{f['field']}: {f['message']}" for f in failures])
                logger.warning(f"❌ {company_name}: {len(failures)} failure(s)")
                logger.warning(f"   Failures: {failure_summary}")

                invalid_companies.append({
                    "company": company,
                    "failures": failures
                })

                # Update status to invalid
                if not self.dry_run:
                    self.update_validation_status("company_master", "company_unique_id", company_id, "invalid")

                # Log to pipeline_events
                self.log_to_pipeline_events(
                    event_type="validation_check",
                    record_type="company",
                    record_id=company_id,
                    passed=False,
                    reason=failure_summary
                )

                # Route to n8n webhook
                if self.route_to_n8n("company", company, failures, state):
                    self.stats.companies_routed += 1

        logger.info(f"\n📊 Company Validation Summary:")
        logger.info(f"  Total: {self.stats.companies_total}")
        logger.info(f"  ✅ Valid: {self.stats.companies_valid}")
        logger.info(f"  ❌ Invalid: {self.stats.companies_invalid}")
        logger.info(f"  📄 Routed to Sheets: {self.stats.companies_routed}")

        return invalid_companies

    def validate_people(self, people: List[Dict], state: str) -> List[Dict]:
        """Validate all people and route failures"""
        invalid_people = []

        # Get valid company IDs for validation
        valid_company_ids = self.get_valid_company_ids()

        logger.info(f"\n{'='*60}")
        logger.info(f"Validating {len(people)} People")
        logger.info(f"{'='*60}")

        for person in people:
            self.stats.people_total += 1
            person_id = person.get("unique_id", "unknown")
            person_name = person.get("full_name", "Unknown")

            # Validate person
            is_valid, failures = validate_person(person, valid_company_ids=valid_company_ids)

            if is_valid:
                self.stats.people_valid += 1
                logger.debug(f"✅ {person_name}: VALID")

                # Update status to valid
                if not self.dry_run:
                    self.update_validation_status("people_master", "unique_id", person_id, "valid")

                # Log to pipeline_events
                self.log_to_pipeline_events(
                    event_type="validation_check",
                    record_type="person",
                    record_id=person_id,
                    passed=True
                )
            else:
                self.stats.people_invalid += 1
                failure_summary = ", ".join([f"{f['field']}: {f['message']}" for f in failures])
                logger.warning(f"❌ {person_name}: {len(failures)} failure(s)")
                logger.warning(f"   Failures: {failure_summary}")

                invalid_people.append({
                    "person": person,
                    "failures": failures
                })

                # Update status to invalid
                if not self.dry_run:
                    self.update_validation_status("people_master", "unique_id", person_id, "invalid")

                # Log to pipeline_events
                self.log_to_pipeline_events(
                    event_type="validation_check",
                    record_type="person",
                    record_id=person_id,
                    passed=False,
                    reason=failure_summary
                )

                # Route to n8n webhook
                if self.route_to_n8n("person", person, failures, state):
                    self.stats.people_routed += 1

        logger.info(f"\n📊 People Validation Summary:")
        logger.info(f"  Total: {self.stats.people_total}")
        logger.info(f"  ✅ Valid: {self.stats.people_valid}")
        logger.info(f"  ❌ Invalid: {self.stats.people_invalid}")
        logger.info(f"  📄 Routed to Sheets: {self.stats.people_routed}")

        return invalid_people

    def run(self, state: str = "WV", limit: Optional[int] = None) -> Dict:
        """
        Execute complete retroactive validation workflow

        Returns: Statistics dictionary
        """
        logger.info("="*70)
        logger.info("🚀 RETROACTIVE NEON DATA VALIDATOR")
        logger.info("="*70)
        logger.info(f"State: {state}")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Limit: {limit if limit else 'No limit'}")
        logger.info(f"Pipeline ID: {self.pipeline_id}")
        logger.info("")

        try:
            # Log start to audit
            self.log_to_audit(
                component="retro_validator",
                message=f"Started retroactive validation for {state}",
                event_data={"state": state, "limit": limit}
            )

            # Step 1: Load and validate companies
            companies = self.load_companies(state, limit)
            invalid_companies = self.validate_companies(companies, state)

            # Step 2: Load and validate people
            people = self.load_people(state, limit)
            invalid_people = self.validate_people(people, state)

            # Mark completion
            self.stats.end_time = datetime.now()

            # Log completion to audit
            self.log_to_audit(
                component="retro_validator",
                message=f"Completed retroactive validation for {state}",
                event_data=self.stats.to_dict()
            )

            # Print summary
            self.print_summary()

            return self.stats.to_dict()

        except Exception as e:
            self.stats.end_time = datetime.now()
            logger.error(f"❌ Fatal error: {e}")

            # Log error to audit
            self.log_to_audit(
                component="retro_validator",
                message=f"Failed retroactive validation: {e}",
                event_data={"error": str(e)}
            )

            raise

    def print_summary(self):
        """Print validation summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        print("\n" + "="*70)
        print("📊 RETROACTIVE VALIDATION SUMMARY")
        print("="*70)
        print(f"\n🏢 COMPANIES:")
        print(f"  Total Validated:    {self.stats.companies_total}")
        print(f"  ✅ Valid:            {self.stats.companies_valid}")
        print(f"  ❌ Invalid:          {self.stats.companies_invalid}")
        print(f"  📄 Routed to Sheets: {self.stats.companies_routed}")

        print(f"\n👤 PEOPLE:")
        print(f"  Total Validated:    {self.stats.people_total}")
        print(f"  ✅ Valid:            {self.stats.people_valid}")
        print(f"  ❌ Invalid:          {self.stats.people_invalid}")
        print(f"  📄 Routed to Sheets: {self.stats.people_routed}")

        print(f"\n🌐 WEBHOOKS:")
        print(f"  ✅ Success:          {self.stats.webhook_success}")
        print(f"  ❌ Failed:           {self.stats.webhook_failed}")

        print(f"\n⏱️  TIMING:")
        print(f"  Duration:           {duration:.2f}s")
        print("="*70 + "\n")

        if self.dry_run:
            print("🔍 DRY-RUN MODE: No changes were made to the database")
        else:
            print(f"✅ SUCCESS: Validated {self.stats.companies_total + self.stats.people_total} total records")
            print(f"📊 Google Sheet ID: {os.getenv('GOOGLE_SHEET_ID', '1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg')}")
            print(f"   - Tab 'Invalid_Companies': {self.stats.companies_routed} rows")
            print(f"   - Tab 'Invalid_People': {self.stats.people_routed} rows")

    def save_report(self, output_path: Optional[str] = None):
        """Save JSON report"""
        if not output_path:
            # Create logs directory if it doesn't exist
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = logs_dir / f"retro_validation_report_{timestamp}.json"

        report = self.stats.to_dict()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Report saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Retroactively validate Neon database records and route failures via n8n"
    )
    parser.add_argument(
        "--state",
        default="WV",
        help="State code to filter records (default: WV)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records to process (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test validation logic without making changes"
    )
    parser.add_argument(
        "--output",
        help="Path to save JSON report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get connection string from environment
    connection_string = os.getenv("NEON_CONNECTION_STRING")

    if not connection_string and not args.dry_run:
        logger.error("❌ NEON_CONNECTION_STRING not set in environment")
        logger.info("Set it in .env file or export it:")
        logger.info("export NEON_CONNECTION_STRING='postgresql://...'")
        sys.exit(1)

    # Run validator
    try:
        validator = RetroValidator(connection_string, dry_run=args.dry_run)
        report = validator.run(state=args.state, limit=args.limit)

        # Save report
        output_path = args.output if args.output else None
        validator.save_report(output_path)

        # Exit with appropriate code
        if validator.stats.companies_invalid > 0 or validator.stats.people_invalid > 0:
            logger.warning(f"⚠️  Found {validator.stats.companies_invalid + validator.stats.people_invalid} invalid records")
            sys.exit(0)  # Still success - failures were routed
        else:
            logger.info("✅ All records are valid!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
