"""
Retroactive People Validator - Barton Toolbox Hub
Validates existing people records from Neon database and routes failures via n8n

Doctrine ID: 04.04.02.04.10000.004
Blueprint: 04.svg.marketing.outreach.v1

Usage:
    python backend/validator/retro_validate_people.py --state WV
    python backend/validator/retro_validate_people.py --state WV --limit 100
    python backend/validator/retro_validate_people.py --state WV --dry-run
"""

import os
import sys
import json
import argparse
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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
    from validator.validation_rules import validate_person
except ImportError:
    print("❌ Error: validation_rules.py not found. Make sure it exists in validator/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class PeopleValidationStats:
    """Track people validation statistics"""

    def __init__(self):
        self.total = 0
        self.valid = 0
        self.invalid = 0
        self.routed_to_sheets = 0
        self.webhook_success = 0
        self.webhook_failed = 0
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self) -> Dict:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "routed_to_sheets": self.routed_to_sheets,
            "webhooks": {
                "success": self.webhook_success,
                "failed": self.webhook_failed
            },
            "duration_seconds": round(duration, 2),
            "timestamp": self.end_time.isoformat() if self.end_time else None
        }


class PeopleValidator:
    """Retroactive validator for people records"""

    def __init__(self, connection_string: str, dry_run: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.stats = PeopleValidationStats()
        self.conn = None
        self.cursor = None

        # n8n webhook URL for people failures
        self.people_webhook = os.getenv("N8N_PERSON_FAILURE_WEBHOOK")
        if not self.people_webhook:
            self.people_webhook = "https://n8n.barton.com/webhook/route-person-failure"

        # Generate unique pipeline ID
        self.pipeline_id = f"PEOPLE-VAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not dry_run:
            try:
                self.conn = psycopg2.connect(connection_string)
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                logger.info("✅ Connected to Neon database")
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {e}")
                raise

        # Warn if webhook not configured
        if not self.people_webhook:
            logger.warning("⚠️  N8N_PERSON_FAILURE_WEBHOOK not configured - routing will be skipped")

    def __del__(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def load_people(self, state: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Load people from Neon database"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would load people{' from ' + state if state else ''}")
            return []

        try:
            query = """
                SELECT
                    p.unique_id as person_id,
                    p.full_name,
                    p.email,
                    p.title,
                    p.company_unique_id,
                    p.linkedin_url,
                    p.updated_at as timestamp_last_updated,
                    p.validation_status
                FROM marketing.people_master p
            """

            conditions = []
            params = []

            # Add state filter if provided
            if state:
                query += """
                    JOIN marketing.company_master c ON p.company_unique_id = c.company_unique_id
                """
                conditions.append("c.state = %s")
                params.append(state)

            # Only validate records that haven't been validated yet
            conditions.append("(p.validation_status IS NULL OR p.validation_status = 'pending')")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query, tuple(params) if params else None)
            people = self.cursor.fetchall()

            logger.info(f"✅ Loaded {len(people)} people{' from ' + state if state else ''}")
            return [dict(p) for p in people]

        except Exception as e:
            logger.error(f"❌ Failed to load people: {e}")
            raise

    def get_valid_company_ids(self) -> set:
        """Get set of valid company unique IDs"""
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

    def route_to_n8n(self, person: Dict, result: Dict, state: Optional[str] = None) -> bool:
        """
        Route invalid person to n8n webhook

        n8n will handle routing to Google Sheets
        """
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would route person to n8n webhook")
            return True

        if not self.people_webhook:
            logger.warning(f"⚠️  No webhook configured for people - skipping route")
            return False

        # Prepare webhook payload
        payload = {
            "type": "person",
            "reason_code": result.get("reason", "Validation failed"),
            "row_data": person,
            "state": state or "unknown",
            "timestamp": datetime.now().isoformat(),
            "pipeline_id": self.pipeline_id,
            "failures": result.get("failures", []),
            "sheet_id": os.getenv("GOOGLE_SHEET_ID", "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg"),
            "sheet_tab": "Invalid_People"
        }

        # POST to n8n webhook
        try:
            response = requests.post(
                self.people_webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if 200 <= response.status_code < 300:
                logger.debug(f"✅ Routed person to n8n webhook (HTTP {response.status_code})")
                self.stats.webhook_success += 1
                return True
            else:
                logger.warning(f"⚠️  n8n webhook returned HTTP {response.status_code}")

                # Retry once on 5xx errors
                if response.status_code >= 500:
                    logger.info("🔄 Retrying webhook request...")
                    retry_response = requests.post(self.people_webhook, json=payload, timeout=30)

                    if 200 <= retry_response.status_code < 300:
                        logger.info(f"✅ Retry successful (HTTP {retry_response.status_code})")
                        self.stats.webhook_success += 1
                        return True

                self.stats.webhook_failed += 1
                return False

        except requests.exceptions.Timeout:
            logger.error(f"❌ Webhook request timed out for person")
            self.stats.webhook_failed += 1
            return False
        except Exception as e:
            logger.error(f"❌ Webhook request failed: {e}")
            self.stats.webhook_failed += 1
            return False

    def log_to_pipeline_events(self, person_id: str, passed: bool, reason: str = ""):
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
                "record_type": "person",
                "record_id": person_id,
                "passed": passed,
                "reason": reason,
                "pipeline_id": self.pipeline_id
            }

            self.cursor.execute(query, ("validation_check", json.dumps(payload)))
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
                "people_validation",
                json.dumps(event_data)
            ))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to log to audit_log: {e}")

    def update_validation_status(self, person_id: str, status: str):
        """Update validation_status field in database"""
        if self.dry_run:
            return

        try:
            query = """
                UPDATE marketing.people_master
                SET validation_status = %s,
                    updated_at = NOW()
                WHERE unique_id = %s
            """

            self.cursor.execute(query, (status, person_id))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to update validation_status: {e}")

    def validate_people(self, people: List[Dict], valid_company_ids: set, state: Optional[str] = None):
        """Validate all people and route failures"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Validating {len(people)} People")
        logger.info(f"{'='*70}")

        for person in people:
            self.stats.total += 1
            person_id = person.get("person_id") or person.get("unique_id", "unknown")
            full_name = person.get("full_name", "Unknown")

            # Validate person
            result = validate_person(person, valid_company_ids)

            if result["valid"]:
                self.stats.valid += 1
                logger.debug(f"✅ {full_name}: VALID")

                # Update status to valid
                self.update_validation_status(person_id, "valid")

                # Log to pipeline_events
                self.log_to_pipeline_events(person_id, True)
            else:
                self.stats.invalid += 1
                logger.warning(f"❌ {full_name}: {len(result['failures'])} failure(s)")
                logger.warning(f"   Reason: {result['reason']}")

                # Update status to invalid
                self.update_validation_status(person_id, "invalid")

                # Log to pipeline_events
                self.log_to_pipeline_events(person_id, False, result["reason"])

                # Route to n8n webhook
                if self.route_to_n8n(person, result, state):
                    self.stats.routed_to_sheets += 1

        logger.info(f"\n📊 People Validation Summary:")
        logger.info(f"  Total: {self.stats.total}")
        logger.info(f"  ✅ Valid: {self.stats.valid}")
        logger.info(f"  ❌ Invalid: {self.stats.invalid}")
        logger.info(f"  📄 Routed to Sheets: {self.stats.routed_to_sheets}")

    def run(self, state: Optional[str] = None, limit: Optional[int] = None) -> Dict:
        """
        Execute complete people validation workflow

        Returns: Statistics dictionary
        """
        logger.info("="*70)
        logger.info("🚀 RETROACTIVE PEOPLE VALIDATOR")
        logger.info("="*70)
        logger.info(f"State: {state if state else 'All'}")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Limit: {limit if limit else 'No limit'}")
        logger.info(f"Pipeline ID: {self.pipeline_id}")
        logger.info("")

        try:
            # Log start to audit
            self.log_to_audit(
                component="people_validator",
                message=f"Started people validation{' for ' + state if state else ''}",
                event_data={"state": state, "limit": limit}
            )

            # Load people
            people = self.load_people(state, limit)

            # Get valid company IDs
            valid_company_ids = self.get_valid_company_ids()
            logger.info(f"✅ Loaded {len(valid_company_ids)} valid companies for reference")

            # Validate people
            self.validate_people(people, valid_company_ids, state)

            # Mark completion
            self.stats.end_time = datetime.now()

            # Log completion to audit
            self.log_to_audit(
                component="people_validator",
                message=f"Completed people validation{' for ' + state if state else ''}",
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
                component="people_validator",
                message=f"Failed people validation: {e}",
                event_data={"error": str(e)}
            )

            raise

    def print_summary(self):
        """Print validation summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        print("\n" + "="*70)
        print("📊 PEOPLE VALIDATION SUMMARY")
        print("="*70)
        print(f"\n👤 PEOPLE:")
        print(f"  Total Validated:    {self.stats.total}")
        print(f"  ✅ Valid:            {self.stats.valid}")
        print(f"  ❌ Invalid:          {self.stats.invalid}")
        print(f"  📄 Routed to Sheets: {self.stats.routed_to_sheets}")

        print(f"\n🌐 WEBHOOKS:")
        print(f"  ✅ Success:          {self.stats.webhook_success}")
        print(f"  ❌ Failed:           {self.stats.webhook_failed}")

        print(f"\n⏱️  TIMING:")
        print(f"  Duration:           {duration:.2f}s")
        print("="*70 + "\n")

        if self.dry_run:
            print("🔍 DRY-RUN MODE: No changes were made to the database")
        else:
            print(f"✅ SUCCESS: Validated {self.stats.total} people")
            print(f"📊 Google Sheet ID: {os.getenv('GOOGLE_SHEET_ID', '1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg')}")
            print(f"   - Tab 'Invalid_People': {self.stats.routed_to_sheets} rows")

    def save_report(self, output_path: Optional[str] = None):
        """Save JSON report"""
        if not output_path:
            # Create logs directory if it doesn't exist
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = logs_dir / f"people_validation_report_{timestamp}.json"

        report = self.stats.to_dict()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Report saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Retroactively validate people records and route failures via n8n"
    )
    parser.add_argument(
        "--state",
        help="State code to filter records (e.g., WV)"
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
        validator = PeopleValidator(connection_string, dry_run=args.dry_run)
        report = validator.run(state=args.state, limit=args.limit)

        # Save report
        output_path = args.output if args.output else None
        validator.save_report(output_path)

        # Exit with appropriate code
        if validator.stats.invalid > 0:
            logger.warning(f"⚠️  Found {validator.stats.invalid} invalid people")
            sys.exit(0)  # Still success - failures were routed
        else:
            logger.info("✅ All people are valid!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
