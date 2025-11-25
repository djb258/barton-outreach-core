"""
Validation Queue Processor - Barton Outreach Core
Processes failed validation queue until empty (or limits reached)

Business Rule: Failed validation table is a WORK QUEUE.
- Either enrich & promote to company_master (SUCCESS)
- Or exhaust all tiers and remove from queue (FAILURE)
- Goal: Queue should ALWAYS be empty

Usage:
    python process_validation_queue.py --max-spend 100 --verbose
    python process_validation_queue.py --max-iterations 50
    python process_validation_queue.py --dry-run

Barton Doctrine ID: 04.04.02.04.enrichment.queue_processor
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Using system environment variables only.")

# Import our enrichment modules
from enrichment_waterfall import attempt_enrichment
from revalidate_after_enrichment import revalidate_company

# Import safety mechanisms
try:
    from rate_limiter import get_rate_limiter_status
    SAFETY_ENABLED = True
except ImportError:
    SAFETY_ENABLED = False
    def get_rate_limiter_status():
        return "Rate limiter not available"

# Minimum delay between processing companies (seconds)
# This prevents runaway loops and gives APIs time to cool down
MIN_DELAY_BETWEEN_COMPANIES = 1.0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class QueueProcessorStats:
    """Track queue processing statistics"""

    def __init__(self):
        self.total_processed = 0
        self.successful_enrichments = 0
        self.failed_enrichments = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.promoted_to_master = 0
        self.removed_from_queue = 0
        self.total_cost = 0.0
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self) -> Dict:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return {
            "total_processed": self.total_processed,
            "successful_enrichments": self.successful_enrichments,
            "failed_enrichments": self.failed_enrichments,
            "successful_validations": self.successful_validations,
            "failed_validations": self.failed_validations,
            "promoted_to_master": self.promoted_to_master,
            "removed_from_queue": self.removed_from_queue,
            "total_cost": round(self.total_cost, 2),
            "avg_cost_per_success": round(self.total_cost / max(self.successful_validations, 1), 2),
            "duration_seconds": round(duration, 2),
            "timestamp": self.end_time.isoformat() if self.end_time else None
        }

    def print_summary(self):
        """Print formatted summary report"""
        print("\n" + "="*80)
        print("QUEUE PROCESSING SUMMARY")
        print("="*80)
        print(f"\nCompanies Processed: {self.total_processed}")
        print(f"  Successfully Enriched: {self.successful_enrichments}")
        print(f"  Failed Enrichment: {self.failed_enrichments}")
        print(f"  Successfully Validated: {self.successful_validations}")
        print(f"  Failed Validation: {self.failed_validations}")
        print(f"\nOutcomes:")
        print(f"  Promoted to company_master: {self.promoted_to_master}")
        print(f"  Removed from queue (failed): {self.removed_from_queue}")
        print(f"\nCost:")
        print(f"  Total Cost: ${self.total_cost:.2f}")
        if self.successful_validations > 0:
            print(f"  Avg Cost Per Success: ${self.total_cost / self.successful_validations:.2f}")
        print("\n" + "="*80)


class ValidationQueueProcessor:
    """Process failed validation queue"""

    def __init__(self, connection_string: str, dry_run: bool = False, verbose: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = QueueProcessorStats()
        self.conn = None
        self.cursor = None

        if not dry_run:
            try:
                self.conn = psycopg2.connect(connection_string)
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                logger.info("Connected to Neon database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise

    def __del__(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def get_queue_count(self) -> int:
        """Get count of records in validation queue"""
        self.cursor.execute("SELECT COUNT(*) as count FROM marketing.company_invalid;")
        return self.cursor.fetchone()['count']

    def get_next_company(self) -> Optional[Dict]:
        """
        Get next company from queue (FIFO with priority)

        Priority Order:
        1. Missing only website (easy to find)
        2. Missing LinkedIn (medium difficulty)
        3. Other failures (hardest)
        """
        # For now, simple FIFO
        # TODO: Add priority ordering
        self.cursor.execute("""
            SELECT *
            FROM marketing.company_invalid
            ORDER BY failed_at ASC
            LIMIT 1;
        """)

        result = self.cursor.fetchone()
        return dict(result) if result else None

    def log_to_enrichment_log(self, company: Dict, enrichment_result: Dict):
        """Log enrichment attempt to marketing.data_enrichment_log"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would log to data_enrichment_log: {company['company_unique_id']}")
            return

        # Check if table exists (it might not in all environments)
        self.cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'marketing'
                AND table_name = 'data_enrichment_log'
            );
        """)

        if not self.cursor.fetchone()[0]:
            logger.warning("data_enrichment_log table does not exist, skipping log")
            return

        try:
            self.cursor.execute("""
                INSERT INTO marketing.data_enrichment_log (
                    company_unique_id,
                    agent_name,
                    enrichment_type,
                    status,
                    started_at,
                    completed_at,
                    cost_credits,
                    error_message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                company.get('company_unique_id'),
                enrichment_result.get('agent_name', 'Unknown'),
                'company_website',
                'success' if enrichment_result.get('success') else 'failed',
                datetime.now(),
                datetime.now(),
                enrichment_result.get('cost', 0.0),
                json.dumps(enrichment_result.get('errors', []))
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log to data_enrichment_log: {e}")
            self.conn.rollback()

    def promote_to_master(self, company: Dict, merged_record: Dict):
        """
        Promote company to marketing.company_master

        Steps:
        1. INSERT into company_master
        2. DELETE from company_invalid
        3. Log success
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would promote to company_master: {company['company_unique_id']}")
            return

        try:
            # Insert into company_master
            self.cursor.execute("""
                INSERT INTO marketing.company_master (
                    company_unique_id,
                    company_name,
                    domain,
                    industry,
                    employee_count,
                    website,
                    phone,
                    address,
                    city,
                    state,
                    zip,
                    validation_status,
                    validated_at,
                    batch_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (company_unique_id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    website = EXCLUDED.website,
                    employee_count = EXCLUDED.employee_count,
                    validation_status = 'PASSED',
                    validated_at = NOW();
            """, (
                merged_record.get('company_unique_id'),
                merged_record.get('company_name'),
                merged_record.get('domain'),
                merged_record.get('industry'),
                merged_record.get('employee_count'),
                merged_record.get('website'),
                merged_record.get('phone'),
                merged_record.get('address'),
                merged_record.get('city'),
                merged_record.get('state'),
                merged_record.get('zip'),
                'PASSED',
                datetime.now(),
                merged_record.get('batch_id')
            ))

            # Delete from company_invalid
            self.cursor.execute("""
                DELETE FROM marketing.company_invalid
                WHERE company_unique_id = %s;
            """, (company['company_unique_id'],))

            self.conn.commit()
            logger.info(f"[SUCCESS] Promoted to company_master: {company['company_unique_id']}")
            self.stats.promoted_to_master += 1

        except Exception as e:
            logger.error(f"Failed to promote to company_master: {e}")
            self.conn.rollback()
            raise

    def remove_from_queue(self, company: Dict, reason: str):
        """
        Remove company from queue (permanent failure)

        Args:
            company: Company record
            reason: Why removed (e.g., "all_tiers_failed")
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Would remove from queue: {company['company_unique_id']} (reason: {reason})")
            return

        try:
            # Mark as reviewed and add resolution notes
            self.cursor.execute("""
                UPDATE marketing.company_invalid
                SET
                    reviewed = TRUE,
                    reviewed_at = NOW(),
                    resolution_action = 'discard',
                    resolution_notes = %s,
                    updated_at = NOW()
                WHERE company_unique_id = %s;
            """, (reason, company['company_unique_id']))

            # Then delete
            self.cursor.execute("""
                DELETE FROM marketing.company_invalid
                WHERE company_unique_id = %s;
            """, (company['company_unique_id'],))

            self.conn.commit()
            logger.info(f"[REMOVED] Deleted from queue: {company['company_unique_id']} ({reason})")
            self.stats.removed_from_queue += 1

        except Exception as e:
            logger.error(f"Failed to remove from queue: {e}")
            self.conn.rollback()
            raise

    def process_company(self, company: Dict):
        """
        Process a single company through enrichment waterfall

        Returns: True if should continue processing, False if should stop
        """
        company_id = company.get('company_unique_id', 'Unknown')
        company_name = company.get('company_name', 'Unknown')
        reason = company.get('reason_code', 'Unknown')

        print(f"\n{'='*80}")
        print(f"Processing Company {self.stats.total_processed + 1}")
        print(f"  ID: {company_id}")
        print(f"  Name: {company_name}")
        print(f"  Failed Reason: {reason}")
        print(f"{'='*80}")

        # Step 1: Attempt enrichment (Tier 1 → 2 → 3)
        enrichment_result = attempt_enrichment(company, reason)

        # Log to enrichment log
        self.log_to_enrichment_log(company, enrichment_result)

        # Track cost
        self.stats.total_cost += enrichment_result.get('cost', 0.0)

        if enrichment_result['success']:
            # Enrichment succeeded
            self.stats.successful_enrichments += 1

            # Step 2: Revalidate with enriched data
            validation_result = revalidate_company(company, enrichment_result['enriched_data'])

            if validation_result['passes']:
                # SUCCESS: Validation passed, promote to master
                self.stats.successful_validations += 1
                self.promote_to_master(company, validation_result['merged_record'])
                print(f"\n[SUCCESS] {company_name} promoted to company_master!")

            else:
                # FAILURE: Even with enrichment, still can't validate
                self.stats.failed_validations += 1
                self.remove_from_queue(company, f"enriched_but_failed_validation: {validation_result['still_missing']}")
                print(f"\n[FAILURE] {company_name} enriched but still fails validation. Removed from queue.")

        else:
            # Enrichment failed (all 3 tiers exhausted)
            self.stats.failed_enrichments += 1
            self.remove_from_queue(company, f"all_tiers_failed: {enrichment_result['errors']}")
            print(f"\n[FAILURE] {company_name} - all enrichment tiers failed. Removed from queue.")

        self.stats.total_processed += 1

        # Progress report every 10 companies
        if self.stats.total_processed % 10 == 0:
            print(f"\n{'─'*80}")
            print(f"Progress Report: {self.stats.total_processed} companies processed")
            print(f"  Promoted: {self.stats.promoted_to_master}")
            print(f"  Removed: {self.stats.removed_from_queue}")
            print(f"  Total Cost: ${self.stats.total_cost:.2f}")
            print(f"  Queue Remaining: {self.get_queue_count()}")
            print(f"{'─'*80}")

        return True  # Continue processing

    def process_queue_until_empty(self, max_iterations: int = 1000, spend_limit: float = 100.0):
        """
        Process queue until empty (or limits reached)

        Args:
            max_iterations: Max companies to process
            spend_limit: Max dollars to spend

        Returns:
            QueueProcessorStats
        """
        logger.info(f"Starting queue processing (max_iterations={max_iterations}, spend_limit=${spend_limit})")

        iteration = 0

        while iteration < max_iterations and self.stats.total_cost < spend_limit:
            # Check if queue is empty
            queue_count = self.get_queue_count()
            if queue_count == 0:
                logger.info("Queue is empty! Processing complete.")
                break

            # Get next company
            company = self.get_next_company()
            if not company:
                logger.info("No more companies to process")
                break

            # Process company
            try:
                self.process_company(company)
            except Exception as e:
                logger.error(f"Error processing company: {e}")
                # Continue to next company

            iteration += 1

            # SAFETY: Minimum delay between companies
            # This prevents hammering APIs and gives rate limiter time to work
            if MIN_DELAY_BETWEEN_COMPANIES > 0:
                time.sleep(MIN_DELAY_BETWEEN_COMPANIES)

            # Check spend limit
            if self.stats.total_cost >= spend_limit:
                logger.warning(f"Spend limit reached (${spend_limit}). Stopping.")
                break

            # Progress report with rate limiter status every 10 companies
            if iteration % 10 == 0 and SAFETY_ENABLED:
                print(f"\n{'─'*80}")
                print(f"PROGRESS: {iteration} companies processed, ${self.stats.total_cost:.2f} spent")
                print(get_rate_limiter_status())
                print(f"{'─'*80}\n")

        self.stats.end_time = datetime.now()

        # Final report
        print("\n")
        self.stats.print_summary()

        remaining = self.get_queue_count()
        if remaining > 0:
            print(f"\nWARNING: {remaining} companies still in queue (manual review needed)")
        else:
            print("\nSUCCESS: Queue is now empty!")

        return self.stats.to_dict()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Process failed validation queue until empty"
    )
    parser.add_argument("--max-iterations", type=int, default=1000,
                       help="Max companies to process (default: 1000)")
    parser.add_argument("--max-spend", type=float, default=100.0,
                       help="Max spend in dollars (default: $100)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode (no database writes)")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get database connection
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    if not connection_string:
        print("ERROR: DATABASE_URL not found in environment")
        sys.exit(1)

    # Create processor
    processor = ValidationQueueProcessor(
        connection_string=connection_string,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Process queue
    try:
        stats = processor.process_queue_until_empty(
            max_iterations=args.max_iterations,
            spend_limit=args.max_spend
        )

        # Save report to file
        report_file = f"queue_processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"\nReport saved to: {report_file}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        processor.stats.end_time = datetime.now()
        processor.stats.print_summary()
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
