"""
LIVE Production Pipeline Runner - Barton Toolbox Hub
Executes the complete outreach pipeline on real data

⚠️  WARNING: This is a LIVE PRODUCTION script
⚠️  It will modify real data in Neon database and Google Sheets
⚠️  Use --dry-run flag for testing

Usage:
    python run_live_pipeline.py                    # Live production run
    python run_live_pipeline.py --dry-run          # Dry run (no changes)
    python run_live_pipeline.py --limit 50         # Limit records processed
    python run_live_pipeline.py --verbose          # Detailed logging
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from lib.composio_client import ComposioClient, ComposioMCPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Pipeline constants
TOOL_BARTON_ID = "04.04.02.04.50000.001"  # Pipeline orchestrator
BLUEPRINT_ID = "04.svg.marketing.outreach.v1"


class PipelineStats:
    """Track pipeline execution statistics"""

    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = None

        # Intake stats
        self.total_intake_rows = 0
        self.rows_processed = 0

        # Validation stats
        self.validation_passed = 0
        self.validation_failed = 0
        self.validation_errors = []

        # Promotion stats
        self.companies_promoted = 0
        self.people_promoted = 0
        self.promotion_errors = []

        # Routing stats
        self.rows_routed_to_sheet = 0
        self.sheet_creation_errors = []

        # Enrichment stats
        self.enrichment_attempted = 0
        self.enrichment_successful = 0
        self.enrichment_failed = 0

        # Email verification stats
        self.email_checks_attempted = 0
        self.email_checks_successful = 0

        # Talent flow stats
        self.movements_detected = 0
        self.bit_signals_created = 0

        # BIT scoring stats
        self.bit_scores_calculated = 0

        # Error summary
        self.total_errors = 0
        self.critical_errors = 0

    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        execution_time = (self.end_time - self.start_time).total_seconds() if self.end_time else 0

        return {
            "execution_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "execution_time_seconds": execution_time,
                "total_records_processed": self.rows_processed
            },
            "intake": {
                "total_available": self.total_intake_rows,
                "processed": self.rows_processed
            },
            "validation": {
                "passed": self.validation_passed,
                "failed": self.validation_failed,
                "success_rate": f"{(self.validation_passed/self.rows_processed*100):.1f}%" if self.rows_processed > 0 else "0%"
            },
            "promotion": {
                "companies_promoted": self.companies_promoted,
                "people_promoted": self.people_promoted,
                "errors": len(self.promotion_errors)
            },
            "routing": {
                "rows_routed": self.rows_routed_to_sheet,
                "errors": len(self.sheet_creation_errors)
            },
            "enrichment": {
                "attempted": self.enrichment_attempted,
                "successful": self.enrichment_successful,
                "failed": self.enrichment_failed,
                "success_rate": f"{(self.enrichment_successful/self.enrichment_attempted*100):.1f}%" if self.enrichment_attempted > 0 else "0%"
            },
            "email_verification": {
                "attempted": self.email_checks_attempted,
                "successful": self.email_checks_successful
            },
            "talent_flow": {
                "movements_detected": self.movements_detected,
                "bit_signals_created": self.bit_signals_created
            },
            "bit_scoring": {
                "scores_calculated": self.bit_scores_calculated
            },
            "errors": {
                "total": self.total_errors,
                "critical": self.critical_errors
            }
        }


class LivePipelineRunner:
    """
    Production pipeline orchestrator

    Executes complete outreach pipeline:
    1. Load intake data
    2. Validate records
    3. Promote valid records
    4. Route invalid records to Google Sheets
    5. Enrich contacts
    6. Verify emails
    7. Detect talent movements
    8. Calculate BIT scores
    9. Generate summary report
    """

    def __init__(
        self,
        connection_string: str,
        dry_run: bool = False,
        limit: int = 100
    ):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.limit = limit
        self.stats = PipelineStats()

        # Initialize database connection
        self.conn = psycopg2.connect(connection_string)

        # Initialize Composio client (if not dry run)
        self.composio = None if dry_run else ComposioClient()

        # Get Google Sheet config
        self.google_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        self.google_sheet_tab = os.getenv("GOOGLE_SHEET_TAB", "Sheet1")

        logger.info(f"🚀 Pipeline initialized (DRY RUN: {dry_run}, LIMIT: {limit})")

    def log_audit(self, event_type: str, event_data: Dict):
        """Log event to audit log"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would log audit: {event_type}")
            return

        query = """
            INSERT INTO shq.audit_log
            (event_type, event_data, barton_id, created_at)
            VALUES (%s, %s, %s, NOW())
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (event_type, json.dumps(event_data), TOOL_BARTON_ID))
            self.conn.commit()

    def log_error(self, error_code: str, error_message: str, severity: str = "error", context: Dict = None):
        """Log error to error master"""
        self.stats.total_errors += 1
        if severity == "critical":
            self.stats.critical_errors += 1

        if self.dry_run:
            logger.warning(f"[DRY RUN] Would log error: {error_code} - {error_message}")
            return

        query = """
            INSERT INTO shq.error_master
            (error_code, error_message, severity, component, context, barton_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (
                error_code,
                error_message,
                severity,
                "pipeline_orchestrator",
                json.dumps(context or {}),
                TOOL_BARTON_ID
            ))
            self.conn.commit()

    # ==================== STEP 1: LOAD INTAKE DATA ====================

    def load_intake_data(self) -> List[Dict]:
        """
        Load unvalidated records from intake table

        Returns list of intake records
        """
        logger.info("\n" + "="*60)
        logger.info("STEP 1: 🚛 Loading Intake Data")
        logger.info("="*60)

        query = """
            SELECT *
            FROM intake.company_raw_intake
            WHERE validation_status IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (self.limit,))
            records = [dict(row) for row in cur.fetchall()]

        self.stats.total_intake_rows = len(records)
        self.stats.rows_processed = len(records)

        logger.info(f"✅ Loaded {len(records)} unvalidated intake records")

        return records

    # ==================== STEP 2: VALIDATE RECORDS ====================

    def validate_records(self, records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate intake records

        Returns (valid_records, invalid_records)
        """
        logger.info("\n" + "="*60)
        logger.info("STEP 2: ✅ Validating Records")
        logger.info("="*60)

        valid_records = []
        invalid_records = []

        for record in records:
            failures = []

            # Rule 1: Company name required
            if not record.get('company_name'):
                failures.append({
                    "rule": "company_name_required",
                    "field": "company_name",
                    "message": "Company name is required"
                })

            # Rule 2: Contact email format (if provided)
            contact_email = record.get('contact_email', '')
            if contact_email and '@' not in contact_email:
                failures.append({
                    "rule": "email_format",
                    "field": "contact_email",
                    "message": "Invalid email format",
                    "value": contact_email
                })

            # Rule 3: Contact name (if email provided)
            if contact_email and not record.get('contact_name'):
                failures.append({
                    "rule": "contact_name_required",
                    "field": "contact_name",
                    "message": "Contact name required when email provided"
                })

            if failures:
                invalid_records.append({
                    "record": record,
                    "failures": failures
                })
                self.stats.validation_failed += 1
                self.stats.validation_errors.extend(failures)
                logger.warning(f"  ⚠️  {record.get('company_name', 'Unknown')}: {len(failures)} failure(s)")
            else:
                valid_records.append(record)
                self.stats.validation_passed += 1
                logger.info(f"  ✅ {record.get('company_name', 'Unknown')}: VALID")

        logger.info(f"\n📊 Validation Summary:")
        logger.info(f"  Valid: {len(valid_records)}")
        logger.info(f"  Invalid: {len(invalid_records)}")

        return valid_records, invalid_records

    # ==================== STEP 3: PROMOTE VALID RECORDS ====================

    def promote_valid_records(self, valid_records: List[Dict]):
        """Promote valid records to company_master and people_master"""
        logger.info("\n" + "="*60)
        logger.info("STEP 3: 📈 Promoting Valid Records")
        logger.info("="*60)

        for record in valid_records:
            try:
                # Generate Barton IDs
                company_id = f"04.04.02.04.30000.{self.stats.companies_promoted + 1:03d}"

                if self.dry_run:
                    logger.info(f"[DRY RUN] Would promote: {record['company_name']} → {company_id}")
                    self.stats.companies_promoted += 1
                    if record.get('contact_email'):
                        self.stats.people_promoted += 1
                    continue

                # Insert company
                company_query = """
                    INSERT INTO marketing.company_master
                    (company_unique_id, company_name, industry, employee_count, website, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (company_unique_id) DO NOTHING
                """
                with self.conn.cursor() as cur:
                    cur.execute(company_query, (
                        company_id,
                        record.get('company_name'),
                        record.get('industry'),
                        record.get('employee_count'),
                        record.get('website')
                    ))
                    self.conn.commit()

                self.stats.companies_promoted += 1
                logger.info(f"  ✅ Company promoted: {record['company_name']} → {company_id}")

                # Insert contact if provided
                if record.get('contact_email'):
                    person_id = f"04.04.02.04.20000.{self.stats.people_promoted + 1:03d}"

                    person_query = """
                        INSERT INTO marketing.people_master
                        (unique_id, full_name, email, title, company_unique_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (unique_id) DO NOTHING
                    """
                    with self.conn.cursor() as cur:
                        cur.execute(person_query, (
                            person_id,
                            record.get('contact_name'),
                            record.get('contact_email'),
                            record.get('contact_title'),
                            company_id
                        ))
                        self.conn.commit()

                    self.stats.people_promoted += 1
                    logger.info(f"  ✅ Contact promoted: {record.get('contact_name')} → {person_id}")

                # Update intake record status
                update_query = """
                    UPDATE intake.company_raw_intake
                    SET validation_status = 'valid',
                        promoted_at = NOW()
                    WHERE intake_id = %s
                """
                with self.conn.cursor() as cur:
                    cur.execute(update_query, (record['intake_id'],))
                    self.conn.commit()

                # Log audit
                self.log_audit("record.promoted", {
                    "intake_id": record['intake_id'],
                    "company_id": company_id,
                    "company_name": record['company_name']
                })

            except Exception as e:
                logger.error(f"  ❌ Promotion failed for {record.get('company_name')}: {e}")
                self.stats.promotion_errors.append({
                    "record": record,
                    "error": str(e)
                })
                self.log_error("promotion_failed", str(e), "error", {
                    "company_name": record.get('company_name')
                })

        logger.info(f"\n✅ Promoted {self.stats.companies_promoted} companies, {self.stats.people_promoted} contacts")

    # ==================== STEP 4: ROUTE INVALID RECORDS ====================

    def route_invalid_records(self, invalid_records: List[Dict]):
        """Route invalid records to Google Sheets"""
        logger.info("\n" + "="*60)
        logger.info("STEP 4: 📬 Routing Invalid Records to Google Sheets")
        logger.info("="*60)

        if not invalid_records:
            logger.info("  ℹ️  No invalid records to route")
            return

        if self.dry_run:
            logger.info(f"[DRY RUN] Would route {len(invalid_records)} records to Google Sheets")
            self.stats.rows_routed_to_sheet = len(invalid_records)
            return

        if not self.google_sheet_id:
            logger.error("  ❌ GOOGLE_SHEET_ID not configured")
            return

        try:
            # Prepare sheet data
            headers = [
                "Intake ID",
                "Company Name",
                "Contact Name",
                "Contact Email",
                "Rule Failed",
                "Field",
                "Error Message",
                "Status",
                "Corrected Value"
            ]

            data = []
            for item in invalid_records:
                record = item["record"]
                for failure in item["failures"]:
                    row = [
                        str(record.get("intake_id", "")),
                        str(record.get("company_name", "")),
                        str(record.get("contact_name", "")),
                        str(record.get("contact_email", "")),
                        failure.get("rule", ""),
                        failure.get("field", ""),
                        failure.get("message", ""),
                        "PENDING REVIEW",
                        ""  # Empty for manual correction
                    ]
                    data.append(row)

            # Write to existing sheet
            self.composio.write_to_sheet(
                sheet_id=self.google_sheet_id,
                tab_name=self.google_sheet_tab,
                data=[headers] + data,  # Include headers
                start_cell="A1",
                unique_id=f"HEIR-{datetime.now().strftime('%Y%m%d%H%M%S')}-ROUTE"
            )

            self.stats.rows_routed_to_sheet = len(data)
            logger.info(f"  ✅ Routed {len(data)} failure(s) to Google Sheet: {self.google_sheet_id}")

            # Update intake records
            for item in invalid_records:
                record = item["record"]
                update_query = """
                    UPDATE intake.company_raw_intake
                    SET validation_status = 'invalid',
                        routed_at = NOW()
                    WHERE intake_id = %s
                """
                with self.conn.cursor() as cur:
                    cur.execute(update_query, (record['intake_id'],))
                    self.conn.commit()

            # Log audit
            self.log_audit("invalid_records.routed", {
                "sheet_id": self.google_sheet_id,
                "failures_count": len(data)
            })

        except ComposioMCPError as e:
            logger.error(f"  ❌ Composio MCP error: {e}")
            self.stats.sheet_creation_errors.append(str(e))
            self.log_error("sheet_routing_failed", str(e), "error")
        except Exception as e:
            logger.error(f"  ❌ Routing error: {e}")
            self.stats.sheet_creation_errors.append(str(e))
            self.log_error("routing_failed", str(e), "error")

    # ==================== STEP 5: PLACEHOLDER - ENRICH CONTACTS ====================

    def enrich_contacts(self):
        """Placeholder: Enrich newly promoted contacts"""
        logger.info("\n" + "="*60)
        logger.info("STEP 5: 🔍 Enriching Contacts (PLACEHOLDER)")
        logger.info("="*60)

        logger.info("  ℹ️  Enrichment tool not yet implemented")
        logger.info("  ℹ️  Would call Apify/Abacus/Firecrawl agents here")

        self.stats.enrichment_attempted = self.stats.people_promoted
        self.stats.enrichment_successful = 0  # Placeholder

    # ==================== STEP 6-8: PLACEHOLDERS ====================

    def verify_emails(self):
        """Placeholder: Email verification"""
        logger.info("\n" + "="*60)
        logger.info("STEP 6: 📧 Email Verification (PLACEHOLDER)")
        logger.info("="*60)
        logger.info("  ℹ️  Email verification tool not yet implemented")

    def detect_talent_movements(self):
        """Placeholder: Talent flow detection"""
        logger.info("\n" + "="*60)
        logger.info("STEP 7: 🧠 Talent Movement Detection (PLACEHOLDER)")
        logger.info("="*60)
        logger.info("  ℹ️  Talent flow tool not yet implemented")

    def calculate_bit_scores(self):
        """Placeholder: BIT score calculation"""
        logger.info("\n" + "="*60)
        logger.info("STEP 8: 📊 BIT Score Calculation (PLACEHOLDER)")
        logger.info("="*60)
        logger.info("  ℹ️  BIT scoring tool not yet implemented")

    # ==================== PIPELINE ORCHESTRATION ====================

    def run(self) -> Dict:
        """Execute complete pipeline"""
        logger.info("\n" + "="*70)
        logger.info("🚀 BARTON OUTREACH - LIVE PRODUCTION PIPELINE")
        logger.info("="*70)

        if self.dry_run:
            logger.warning("⚠️  DRY RUN MODE - No data will be modified")
        else:
            logger.warning("🔴 LIVE MODE - Real data will be modified!")

        logger.info(f"Record Limit: {self.limit}")
        logger.info(f"Google Sheet ID: {self.google_sheet_id or 'NOT CONFIGURED'}")
        logger.info("")

        try:
            # Step 1: Load intake data
            intake_records = self.load_intake_data()

            if not intake_records:
                logger.warning("⚠️  No unvalidated intake records found")
                self.stats.end_time = datetime.now()
                return self.stats.to_dict()

            # Step 2: Validate records
            valid_records, invalid_records = self.validate_records(intake_records)

            # Step 3: Promote valid records
            if valid_records:
                self.promote_valid_records(valid_records)

            # Step 4: Route invalid records
            if invalid_records:
                self.route_invalid_records(invalid_records)

            # Step 5-8: Placeholder tools
            self.enrich_contacts()
            self.verify_emails()
            self.detect_talent_movements()
            self.calculate_bit_scores()

            # Mark completion
            self.stats.end_time = datetime.now()

            # Log pipeline completion
            self.log_audit("pipeline.completed", self.stats.to_dict())

            logger.info("\n" + "="*70)
            logger.info("✅ PIPELINE EXECUTION COMPLETE")
            logger.info("="*70)

            return self.stats.to_dict()

        except Exception as e:
            logger.error(f"\n❌ PIPELINE FAILED: {e}")
            self.log_error("pipeline_failed", str(e), "critical")
            self.stats.end_time = datetime.now()
            raise

    def print_summary(self, summary: Dict):
        """Print execution summary"""
        print("\n" + "="*70)
        print("📊 PIPELINE EXECUTION SUMMARY")
        print("="*70)

        exec_summary = summary["execution_summary"]
        print(f"\n⏱️  Execution Time: {exec_summary['execution_time_seconds']:.2f}s")
        print(f"📦 Total Records: {exec_summary['total_records_processed']}")

        print(f"\n✅ Validation:")
        val = summary["validation"]
        print(f"   Passed: {val['passed']}")
        print(f"   Failed: {val['failed']}")
        print(f"   Success Rate: {val['success_rate']}")

        print(f"\n📈 Promotion:")
        prom = summary["promotion"]
        print(f"   Companies: {prom['companies_promoted']}")
        print(f"   Contacts: {prom['people_promoted']}")

        print(f"\n📬 Routing:")
        route = summary["routing"]
        print(f"   Routed to Sheet: {route['rows_routed']}")

        print(f"\n❌ Errors:")
        errors = summary["errors"]
        print(f"   Total: {errors['total']}")
        print(f"   Critical: {errors['critical']}")

        print("="*70 + "\n")

    def save_report(self, summary: Dict, output_path: str):
        """Save execution report to JSON"""
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"✅ Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run live outreach pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no data changes)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max records to process (default: 100)"
    )
    parser.add_argument(
        "--output",
        help="Output path for JSON report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get connection string
    connection_string = os.getenv("NEON_CONNECTION_STRING", "")

    if not connection_string:
        logger.error("❌ NEON_CONNECTION_STRING not set")
        sys.exit(1)

    # Initialize and run pipeline
    pipeline = LivePipelineRunner(
        connection_string=connection_string,
        dry_run=args.dry_run,
        limit=args.limit
    )

    try:
        summary = pipeline.run()
        pipeline.print_summary(summary)

        # Save report
        if args.output:
            pipeline.save_report(summary, args.output)
        else:
            # Auto-generate report path
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            report_path = logs_dir / f"outreach_run_{timestamp}.json"
            pipeline.save_report(summary, str(report_path))

        # Exit with success
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
