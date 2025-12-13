"""
Phase 2: Outreach Readiness Evaluator - Barton Toolbox Hub
Evaluates whether validated companies are ready for outreach campaigns

Doctrine ID: 04.04.02.04.10000.003
Blueprint: 04.svg.marketing.outreach.v1

Phase 2 Requirements:
- Company validation_status = 'valid' (Phase 1 passed)
- All 3 slots (CEO, CFO, HR) must be FILLED
- Each person must have successful enrichment
- Each person's email must be verified
- Each person's title must match slot type

Usage:
    python backend/enrichment/evaluate_outreach_readiness.py --company 04.04.02.04.30000.005
    python backend/enrichment/evaluate_outreach_readiness.py --state WV --only-validated
"""

import os
import sys
import json
import argparse
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class OutreachReadinessStats:
    """Track outreach readiness evaluation statistics"""

    def __init__(self):
        self.total_evaluated = 0
        self.ready = 0
        self.not_ready = 0
        self.already_ready = 0
        self.invalid = 0  # Not Phase 1 validated

        # Failure breakdown
        self.slot_not_filled = 0
        self.person_not_found = 0
        self.enrichment_missing = 0
        self.email_not_verified = 0
        self.title_mismatch = 0

        # Timing
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self) -> Dict:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return {
            "total_evaluated": self.total_evaluated,
            "outreach_ready": self.ready,
            "not_ready": self.not_ready,
            "already_ready": self.already_ready,
            "invalid": self.invalid,
            "failures": {
                "slot_not_filled": self.slot_not_filled,
                "person_not_found": self.person_not_found,
                "enrichment_missing": self.enrichment_missing,
                "email_not_verified": self.email_not_verified,
                "title_mismatch": self.title_mismatch
            },
            "duration_seconds": round(duration, 2),
            "timestamp": self.end_time.isoformat() if self.end_time else None
        }


class OutreachReadinessEvaluator:
    """Evaluate outreach readiness for validated companies"""

    def __init__(self, connection_string: str, dry_run: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.stats = OutreachReadinessStats()
        self.conn = None
        self.cursor = None

        # Generate unique pipeline ID
        self.pipeline_id = f"READINESS-EVAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if not dry_run:
            try:
                self.conn = psycopg2.connect(connection_string)
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                logger.info("✅ Connected to Neon database")
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {e}")
                raise

    def __del__(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_company(self, company_unique_id: str) -> Optional[Dict]:
        """Load single company from database"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would load company {company_unique_id}")
            return None

        try:
            query = """
                SELECT
                    company_unique_id,
                    company_name,
                    validation_status,
                    outreach_ready,
                    state
                FROM marketing.company_master
                WHERE company_unique_id = %s
            """
            self.cursor.execute(query, (company_unique_id,))
            company = self.cursor.fetchone()

            if company:
                return dict(company)
            return None

        except Exception as e:
            logger.error(f"❌ Failed to load company {company_unique_id}: {e}")
            return None

    def get_validated_companies(self, state: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Load validated companies (Phase 1 passed)"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would load validated companies")
            return []

        try:
            query = """
                SELECT
                    company_unique_id,
                    company_name,
                    validation_status,
                    outreach_ready,
                    state
                FROM marketing.company_master
                WHERE validation_status = 'valid'
            """

            params = []
            if state:
                query += " AND state = %s"
                params.append(state)

            if limit:
                query += f" LIMIT {limit}"

            self.cursor.execute(query, tuple(params) if params else None)
            companies = self.cursor.fetchall()

            logger.info(f"✅ Loaded {len(companies)} validated companies")
            return [dict(c) for c in companies]

        except Exception as e:
            logger.error(f"❌ Failed to load validated companies: {e}")
            raise

    def get_company_slots(self, company_unique_id: str) -> List[Dict]:
        """Load CEO, CFO, HR slots for company"""
        if self.dry_run:
            return []

        try:
            query = """
                SELECT
                    slot_type,
                    is_filled,
                    person_unique_id,
                    filled_at,
                    last_refreshed_at
                FROM marketing.company_slot
                WHERE company_unique_id = %s
                  AND slot_type IN ('CEO', 'CFO', 'HR')
            """
            self.cursor.execute(query, (company_unique_id,))
            slots = self.cursor.fetchall()
            return [dict(s) for s in slots]

        except Exception as e:
            logger.warning(f"⚠️  Failed to load slots for {company_unique_id}: {e}")
            return []

    def get_person(self, person_unique_id: str) -> Optional[Dict]:
        """Load person from people_master"""
        if self.dry_run or not person_unique_id:
            return None

        try:
            query = """
                SELECT
                    unique_id,
                    full_name,
                    email,
                    title,
                    linkedin_url,
                    company_unique_id
                FROM marketing.people_master
                WHERE unique_id = %s
            """
            self.cursor.execute(query, (person_unique_id,))
            person = self.cursor.fetchone()

            if person:
                return dict(person)
            return None

        except Exception as e:
            logger.warning(f"⚠️  Failed to load person {person_unique_id}: {e}")
            return None

    def check_enrichment_status(self, person_unique_id: str) -> bool:
        """Check if person has successful enrichment record"""
        if self.dry_run or not person_unique_id:
            return False

        try:
            query = """
                SELECT COUNT(*) as count
                FROM marketing.contact_enrichment
                WHERE person_unique_id = %s
                  AND enrichment_status = 'success'
                ORDER BY enriched_at DESC
                LIMIT 1
            """
            self.cursor.execute(query, (person_unique_id,))
            result = self.cursor.fetchone()
            return result['count'] > 0 if result else False

        except Exception as e:
            logger.warning(f"⚠️  Failed to check enrichment for {person_unique_id}: {e}")
            return False

    def check_email_verification(self, person_unique_id: str) -> bool:
        """Check if person's email is verified"""
        if self.dry_run or not person_unique_id:
            return False

        try:
            query = """
                SELECT email_status
                FROM marketing.email_verification
                WHERE person_unique_id = %s
                ORDER BY verified_at DESC
                LIMIT 1
            """
            self.cursor.execute(query, (person_unique_id,))
            result = self.cursor.fetchone()
            return result['email_status'] == 'valid' if result else False

        except Exception as e:
            logger.warning(f"⚠️  Failed to check email verification for {person_unique_id}: {e}")
            return False

    def check_title_match(self, slot_type: str, title: Optional[str]) -> bool:
        """Check if person's title matches slot type"""
        if not title:
            return False

        title_lower = title.lower()

        if slot_type == "CEO":
            return "ceo" in title_lower or "chief executive" in title_lower
        elif slot_type == "CFO":
            return "cfo" in title_lower or "chief financial" in title_lower
        elif slot_type == "HR":
            return any(keyword in title_lower for keyword in ["hr", "human resources", "people", "talent"])

        return False

    def evaluate_slot(self, slot: Dict) -> Dict:
        """Evaluate single slot for outreach readiness"""
        slot_type = slot.get("slot_type")
        person_unique_id = slot.get("person_unique_id")
        is_filled = slot.get("is_filled", False)

        result = {
            "slot_type": slot_type,
            "person_id": person_unique_id,
            "checks": {
                "is_filled": is_filled,
                "exists_in_people": False,
                "enriched": False,
                "email_verified": False,
                "title_matches": False
            },
            "failures": [],
            "passed": False
        }

        # Check 1: Slot must be filled
        if not is_filled or not person_unique_id:
            result["failures"].append(f"{slot_type} slot not filled")
            self.stats.slot_not_filled += 1
            return result

        # Check 2: Person must exist in people_master
        person = self.get_person(person_unique_id)
        if not person:
            result["failures"].append(f"Person {person_unique_id} not found in people_master")
            self.stats.person_not_found += 1
            return result

        result["checks"]["exists_in_people"] = True

        # Check 3: Person must have successful enrichment
        enriched = self.check_enrichment_status(person_unique_id)
        result["checks"]["enriched"] = enriched
        if not enriched:
            result["failures"].append(f"Person {person_unique_id} missing enrichment data")
            self.stats.enrichment_missing += 1

        # Check 4: Person email must be verified
        email_verified = self.check_email_verification(person_unique_id)
        result["checks"]["email_verified"] = email_verified
        if not email_verified:
            result["failures"].append(f"Person {person_unique_id} email not verified")
            self.stats.email_not_verified += 1

        # Check 5: Person title must match slot type
        title_matches = self.check_title_match(slot_type, person.get("title"))
        result["checks"]["title_matches"] = title_matches
        if not title_matches:
            result["failures"].append(f"Person title '{person.get('title', 'N/A')}' does not match {slot_type}")
            self.stats.title_mismatch += 1

        # Slot passes if all checks pass
        result["passed"] = (
            result["checks"]["is_filled"] and
            result["checks"]["exists_in_people"] and
            result["checks"]["enriched"] and
            result["checks"]["email_verified"] and
            result["checks"]["title_matches"]
        )

        return result

    def evaluate_outreach_readiness(self, company_unique_id: str) -> Dict:
        """
        Evaluate if company is ready for outreach

        Returns:
            {
                "company_unique_id": "...",
                "outreach_ready": True/False,
                "reason": "Missing HR enrichment data",
                "slot_results": [...],
                "missing_slots": [],
                "total_checks": 15,
                "passed_checks": 12
            }
        """
        # Load company
        company = self.get_company(company_unique_id)

        if not company:
            return {
                "company_unique_id": company_unique_id,
                "outreach_ready": False,
                "reason": "Company not found",
                "slot_results": [],
                "missing_slots": ["CEO", "CFO", "HR"],
                "total_checks": 0,
                "passed_checks": 0
            }

        # Check Phase 1 validation status
        if company.get("validation_status") != "valid":
            self.stats.invalid += 1
            return {
                "company_unique_id": company_unique_id,
                "company_name": company.get("company_name"),
                "outreach_ready": False,
                "reason": f"Company not validated (status: {company.get('validation_status', 'NULL')})",
                "slot_results": [],
                "missing_slots": [],
                "total_checks": 0,
                "passed_checks": 0
            }

        # Load slots
        slots = self.get_company_slots(company_unique_id)

        # Check all required slots exist
        required_slots = {"CEO", "CFO", "HR"}
        existing_slot_types = {s.get("slot_type") for s in slots}
        missing_slots = list(required_slots - existing_slot_types)

        if missing_slots:
            return {
                "company_unique_id": company_unique_id,
                "company_name": company.get("company_name"),
                "outreach_ready": False,
                "reason": f"Missing slot records: {', '.join(missing_slots)}",
                "slot_results": [],
                "missing_slots": missing_slots,
                "total_checks": 0,
                "passed_checks": 0
            }

        # Evaluate each slot
        slot_results = []
        all_slots_passed = True
        first_failure_reason = None

        for slot in slots:
            slot_result = self.evaluate_slot(slot)
            slot_results.append(slot_result)

            if not slot_result["passed"]:
                all_slots_passed = False
                if not first_failure_reason and slot_result["failures"]:
                    first_failure_reason = slot_result["failures"][0]

        # Calculate statistics
        total_checks = len(slots) * 5  # 5 checks per slot
        passed_checks = sum(
            sum(1 for check_passed in sr["checks"].values() if check_passed)
            for sr in slot_results
        )

        # Determine readiness
        outreach_ready = all_slots_passed

        return {
            "company_unique_id": company_unique_id,
            "company_name": company.get("company_name"),
            "outreach_ready": outreach_ready,
            "reason": "All checks passed" if outreach_ready else first_failure_reason,
            "slot_results": slot_results,
            "missing_slots": [],
            "total_checks": total_checks,
            "passed_checks": passed_checks
        }

    def update_outreach_ready_status(self, company_unique_id: str, outreach_ready: bool):
        """Update company_master.outreach_ready field"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would update {company_unique_id} outreach_ready = {outreach_ready}")
            return

        try:
            query = """
                UPDATE marketing.company_master
                SET outreach_ready = %s,
                    updated_at = NOW()
                WHERE company_unique_id = %s
            """
            self.cursor.execute(query, (outreach_ready, company_unique_id))
            self.conn.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update outreach_ready for {company_unique_id}: {e}")
            if self.conn:
                self.conn.rollback()

    def log_to_pipeline_events(self, company_id: str, result: Dict):
        """Log evaluation result to pipeline_events"""
        if self.dry_run:
            return

        try:
            query = """
                INSERT INTO marketing.pipeline_events
                (event_type, payload, created_at)
                VALUES (%s, %s, NOW())
            """

            payload = {
                "company_unique_id": company_id,
                "outreach_ready": result["outreach_ready"],
                "reason": result["reason"],
                "passed_checks": result["passed_checks"],
                "total_checks": result["total_checks"],
                "pipeline_id": self.pipeline_id
            }

            self.cursor.execute(query, ("outreach_readiness_check", json.dumps(payload)))
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
                "outreach_readiness_evaluation",
                json.dumps(event_data)
            ))
            self.conn.commit()

        except Exception as e:
            logger.warning(f"⚠️  Failed to log to audit_log: {e}")

    def evaluate_batch(self, companies: List[Dict]) -> List[Dict]:
        """Evaluate multiple companies"""
        results = []

        logger.info(f"\n{'='*70}")
        logger.info(f"Evaluating {len(companies)} Companies for Outreach Readiness")
        logger.info(f"{'='*70}")

        for company in companies:
            self.stats.total_evaluated += 1
            company_id = company.get("company_unique_id")
            company_name = company.get("company_name", "Unknown")

            # Check if already marked ready
            if company.get("outreach_ready"):
                self.stats.already_ready += 1
                logger.debug(f"✅ {company_name}: Already marked outreach_ready")
                continue

            # Evaluate
            result = self.evaluate_outreach_readiness(company_id)

            if result["outreach_ready"]:
                self.stats.ready += 1
                logger.info(f"✅ {company_name}: READY ({result['passed_checks']}/{result['total_checks']} checks)")

                # Update status
                self.update_outreach_ready_status(company_id, True)
            else:
                self.stats.not_ready += 1
                logger.warning(f"❌ {company_name}: NOT READY - {result['reason']}")
                logger.warning(f"   Checks: {result['passed_checks']}/{result['total_checks']}")

                # Update status (mark as not ready)
                self.update_outreach_ready_status(company_id, False)

            # Log to pipeline_events
            self.log_to_pipeline_events(company_id, result)

            results.append(result)

        return results

    def run(self, company_id: Optional[str] = None, state: Optional[str] = None,
            only_validated: bool = False, limit: Optional[int] = None) -> Dict:
        """
        Execute outreach readiness evaluation

        Args:
            company_id: Single company to evaluate
            state: Filter by state (e.g., "WV")
            only_validated: Only evaluate validated companies
            limit: Limit number of companies

        Returns: Statistics dictionary
        """
        logger.info("="*70)
        logger.info("🚀 OUTREACH READINESS EVALUATOR - Phase 2")
        logger.info("="*70)
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Pipeline ID: {self.pipeline_id}")
        logger.info("")

        try:
            # Log start to audit
            self.log_to_audit(
                component="outreach_readiness_evaluator",
                message="Started outreach readiness evaluation",
                event_data={"company_id": company_id, "state": state, "limit": limit}
            )

            results = []

            if company_id:
                # Single company evaluation
                logger.info(f"Evaluating single company: {company_id}")
                result = self.evaluate_outreach_readiness(company_id)

                if result["outreach_ready"]:
                    self.stats.ready += 1
                    logger.info(f"✅ READY: {result.get('company_name', company_id)}")
                    logger.info(f"   Passed: {result['passed_checks']}/{result['total_checks']} checks")
                    self.update_outreach_ready_status(company_id, True)
                else:
                    self.stats.not_ready += 1
                    logger.warning(f"❌ NOT READY: {result.get('company_name', company_id)}")
                    logger.warning(f"   Reason: {result['reason']}")
                    logger.warning(f"   Passed: {result['passed_checks']}/{result['total_checks']} checks")
                    self.update_outreach_ready_status(company_id, False)

                self.log_to_pipeline_events(company_id, result)
                results.append(result)

            else:
                # Batch evaluation
                companies = self.get_validated_companies(state, limit) if only_validated else []

                if not companies and not only_validated:
                    logger.error("❌ No companies to evaluate. Use --only-validated flag.")
                    return {}

                results = self.evaluate_batch(companies)

            # Mark completion
            self.stats.end_time = datetime.now()

            # Log completion to audit
            self.log_to_audit(
                component="outreach_readiness_evaluator",
                message="Completed outreach readiness evaluation",
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
                component="outreach_readiness_evaluator",
                message=f"Failed outreach readiness evaluation: {e}",
                event_data={"error": str(e)}
            )

            raise

    def print_summary(self):
        """Print evaluation summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        print("\n" + "="*70)
        print("📊 OUTREACH READINESS EVALUATION SUMMARY")
        print("="*70)
        print(f"\n📈 RESULTS:")
        print(f"  Total Evaluated:    {self.stats.total_evaluated}")
        print(f"  ✅ Ready:            {self.stats.ready}")
        print(f"  ❌ Not Ready:        {self.stats.not_ready}")
        print(f"  📌 Already Ready:    {self.stats.already_ready}")
        print(f"  ⚠️  Not Validated:   {self.stats.invalid}")

        print(f"\n🔍 FAILURE BREAKDOWN:")
        print(f"  Slot Not Filled:     {self.stats.slot_not_filled}")
        print(f"  Person Not Found:    {self.stats.person_not_found}")
        print(f"  Enrichment Missing:  {self.stats.enrichment_missing}")
        print(f"  Email Not Verified:  {self.stats.email_not_verified}")
        print(f"  Title Mismatch:      {self.stats.title_mismatch}")

        print(f"\n⏱️  TIMING:")
        print(f"  Duration:           {duration:.2f}s")
        print("="*70 + "\n")

        if self.dry_run:
            print("🔍 DRY-RUN MODE: No changes were made to the database")
        else:
            print(f"✅ SUCCESS: Evaluated {self.stats.total_evaluated} companies")
            print(f"   {self.stats.ready} companies marked outreach_ready = true")

    def save_report(self, output_path: Optional[str] = None) -> Path:
        """Save JSON report"""
        if not output_path:
            # Create logs directory if it doesn't exist
            logs_dir = Path(__file__).parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = logs_dir / f"outreach_readiness_report_{timestamp}.json"

        report = self.stats.to_dict()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Report saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate outreach readiness for validated companies (Phase 2)"
    )
    parser.add_argument(
        "--company",
        help="Single company unique ID to evaluate"
    )
    parser.add_argument(
        "--state",
        help="State code to filter companies (e.g., WV)"
    )
    parser.add_argument(
        "--only-validated",
        action="store_true",
        help="Only evaluate companies with validation_status = 'valid'"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of companies to evaluate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test evaluation logic without making changes"
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

    # Validate arguments
    if not args.company and not args.only_validated:
        logger.error("❌ Must specify either --company or --only-validated")
        logger.info("Examples:")
        logger.info("  python evaluate_outreach_readiness.py --company 04.04.02.04.30000.005")
        logger.info("  python evaluate_outreach_readiness.py --state WV --only-validated")
        sys.exit(1)

    # Run evaluator
    try:
        evaluator = OutreachReadinessEvaluator(connection_string, dry_run=args.dry_run)
        report = evaluator.run(
            company_id=args.company,
            state=args.state,
            only_validated=args.only_validated,
            limit=args.limit
        )

        # Save report
        if report:
            output_path = args.output if args.output else None
            evaluator.save_report(output_path)

        # Exit with appropriate code
        if evaluator.stats.ready > 0:
            logger.info(f"✅ {evaluator.stats.ready} companies ready for outreach!")
            sys.exit(0)
        elif evaluator.stats.not_ready > 0:
            logger.warning(f"⚠️  {evaluator.stats.not_ready} companies not yet ready")
            sys.exit(0)
        else:
            logger.info("ℹ️  No companies evaluated")
            sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
