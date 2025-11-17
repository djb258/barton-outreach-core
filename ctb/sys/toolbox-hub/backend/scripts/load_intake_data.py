"""
Intake Data Loader - Barton Toolbox Hub
Loads CSV files into intake.company_raw_intake table for pipeline processing

Workflow:
1. CSV File → This Script → intake.company_raw_intake
2. intake.company_raw_intake → run_live_pipeline.py → Validated Data

Features:
- CSV parsing with flexible column mapping
- Schema validation
- Duplicate detection
- Bulk insert to Neon database
- Dry-run mode for testing
- Comprehensive statistics and logging

Usage:
    python load_intake_data.py input.csv
    python load_intake_data.py input.csv --dry-run
    python load_intake_data.py input.csv --mapping custom_mapping.json
    python load_intake_data.py input.csv --batch-size 500
"""

import os
import sys
import csv
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
    from psycopg2.extras import RealDictCursor, execute_values
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


class IntakeStats:
    """Track intake loading statistics"""

    def __init__(self):
        self.total_rows = 0
        self.valid_rows = 0
        self.invalid_rows = 0
        self.duplicate_rows = 0
        self.inserted_rows = 0
        self.errors = []
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self) -> Dict:
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        return {
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "duplicate_rows": self.duplicate_rows,
            "inserted_rows": self.inserted_rows,
            "error_count": len(self.errors),
            "errors": self.errors[:10],  # First 10 errors
            "duration_seconds": round(duration, 2),
            "timestamp": self.end_time.isoformat() if self.end_time else None
        }


class IntakeDataLoader:
    """Loads CSV data into intake.company_raw_intake table"""

    # Default CSV column mapping
    DEFAULT_MAPPING = {
        "company_name": ["company_name", "company", "name", "organization"],
        "industry": ["industry", "sector", "vertical"],
        "employee_count": ["employee_count", "employees", "headcount", "size"],
        "website": ["website", "url", "domain"],
        "contact_name": ["contact_name", "contact", "name", "full_name"],
        "contact_email": ["contact_email", "email", "contact_email_address"],
        "contact_title": ["contact_title", "title", "job_title", "position"],
        "source": ["source", "data_source", "origin"]
    }

    def __init__(self, connection_string: str, dry_run: bool = False):
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.stats = IntakeStats()
        self.conn = None
        self.cursor = None

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

    def normalize_headers(self, headers: List[str]) -> Dict[str, str]:
        """
        Map CSV headers to database columns

        Returns: Dict mapping database_column -> csv_column
        """
        mapping = {}
        headers_lower = [h.lower().strip() for h in headers]

        for db_column, possible_names in self.DEFAULT_MAPPING.items():
            for possible_name in possible_names:
                if possible_name.lower() in headers_lower:
                    csv_index = headers_lower.index(possible_name.lower())
                    mapping[db_column] = headers[csv_index]
                    break

        logger.info(f"📊 Column Mapping: {mapping}")
        return mapping

    def load_custom_mapping(self, mapping_file: str) -> Dict[str, str]:
        """Load custom column mapping from JSON file"""
        try:
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
            logger.info(f"✅ Loaded custom mapping from {mapping_file}")
            return mapping
        except Exception as e:
            logger.error(f"❌ Failed to load mapping file: {e}")
            raise

    def validate_row(self, row: Dict, row_number: int) -> Tuple[bool, Optional[str]]:
        """
        Validate a single row

        Returns: (is_valid, error_message)
        """
        # Required fields
        if not row.get("company_name"):
            return False, f"Row {row_number}: Missing company_name"

        # Email format check (if provided)
        contact_email = row.get("contact_email", "")
        if contact_email and "@" not in contact_email:
            return False, f"Row {row_number}: Invalid email format: {contact_email}"

        # Employee count must be numeric (if provided)
        employee_count = row.get("employee_count", "")
        if employee_count:
            try:
                int(employee_count)
            except ValueError:
                return False, f"Row {row_number}: Invalid employee_count: {employee_count}"

        return True, None

    def check_duplicate(self, company_name: str) -> bool:
        """Check if company already exists in intake table"""
        if self.dry_run:
            return False

        try:
            query = """
                SELECT COUNT(*) as count
                FROM intake.company_raw_intake
                WHERE LOWER(company_name) = LOWER(%s)
            """
            self.cursor.execute(query, (company_name,))
            result = self.cursor.fetchone()
            return result['count'] > 0
        except Exception as e:
            logger.warning(f"⚠️  Duplicate check failed: {e}")
            return False

    def parse_csv(self, csv_file: str, column_mapping: Optional[Dict] = None) -> List[Dict]:
        """
        Parse CSV file and map to database schema

        Returns: List of validated records ready for insertion
        """
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        logger.info(f"📂 Reading CSV file: {csv_file}")

        valid_records = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            # Determine column mapping
            if column_mapping:
                mapping = column_mapping
            else:
                mapping = self.normalize_headers(headers)

            # Process rows
            for row_number, csv_row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                self.stats.total_rows += 1

                # Map CSV columns to database columns
                db_row = {}
                for db_col, csv_col in mapping.items():
                    value = csv_row.get(csv_col, "").strip()
                    db_row[db_col] = value if value else None

                # Add metadata
                db_row["source"] = db_row.get("source") or f"CSV Upload - {Path(csv_file).name}"
                db_row["loaded_at"] = datetime.now().isoformat()

                # Validate row
                is_valid, error_msg = self.validate_row(db_row, row_number)

                if not is_valid:
                    self.stats.invalid_rows += 1
                    self.stats.errors.append(error_msg)
                    logger.warning(f"⚠️  {error_msg}")
                    continue

                # Check duplicates
                company_name = db_row.get("company_name")
                if self.check_duplicate(company_name):
                    self.stats.duplicate_rows += 1
                    logger.debug(f"⏭️  Skipping duplicate: {company_name}")
                    continue

                self.stats.valid_rows += 1
                valid_records.append(db_row)

        logger.info(f"✅ Parsed {self.stats.total_rows} rows: {self.stats.valid_rows} valid, {self.stats.invalid_rows} invalid, {self.stats.duplicate_rows} duplicates")

        return valid_records

    def insert_records(self, records: List[Dict], batch_size: int = 100):
        """Bulk insert records into intake.company_raw_intake"""
        if self.dry_run:
            logger.info(f"🔍 [DRY-RUN] Would insert {len(records)} records")
            self.stats.inserted_rows = len(records)
            return

        if not records:
            logger.info("ℹ️  No records to insert")
            return

        try:
            # Prepare insert query
            columns = ["company_name", "industry", "employee_count", "website",
                      "contact_name", "contact_email", "contact_title", "source", "loaded_at"]

            query = f"""
                INSERT INTO intake.company_raw_intake
                ({', '.join(columns)})
                VALUES %s
            """

            # Prepare data tuples
            data_tuples = []
            for record in records:
                tuple_data = tuple(record.get(col) for col in columns)
                data_tuples.append(tuple_data)

            # Batch insert
            total_batches = (len(data_tuples) + batch_size - 1) // batch_size

            for i in range(0, len(data_tuples), batch_size):
                batch = data_tuples[i:i + batch_size]
                batch_num = (i // batch_size) + 1

                execute_values(self.cursor, query, batch)
                self.conn.commit()

                self.stats.inserted_rows += len(batch)
                logger.info(f"✅ Inserted batch {batch_num}/{total_batches} ({len(batch)} records)")

            logger.info(f"🎉 Successfully inserted {self.stats.inserted_rows} records")

        except Exception as e:
            self.conn.rollback()
            error_msg = f"Failed to insert records: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats.errors.append(error_msg)
            raise

    def load(self, csv_file: str, batch_size: int = 100, column_mapping: Optional[Dict] = None):
        """
        Complete intake loading workflow

        1. Parse CSV
        2. Validate records
        3. Insert into database
        4. Generate report
        """
        logger.info("="*70)
        logger.info("🚀 INTAKE DATA LOADER - BARTON TOOLBOX HUB")
        logger.info("="*70)
        logger.info(f"CSV File: {csv_file}")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"Batch Size: {batch_size}")
        logger.info("")

        try:
            # Step 1: Parse CSV
            logger.info("📊 Step 1: Parsing CSV file...")
            valid_records = self.parse_csv(csv_file, column_mapping)

            # Step 2: Insert records
            logger.info(f"\n💾 Step 2: Inserting {len(valid_records)} records to database...")
            self.insert_records(valid_records, batch_size)

            # Mark completion
            self.stats.end_time = datetime.now()

            # Step 3: Print summary
            self.print_summary()

            return self.stats.to_dict()

        except Exception as e:
            self.stats.end_time = datetime.now()
            logger.error(f"❌ Fatal error: {e}")
            raise

    def print_summary(self):
        """Print loading summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds()

        print("\n" + "="*70)
        print("📊 INTAKE LOADING SUMMARY")
        print("="*70)
        print(f"Total Rows Processed:  {self.stats.total_rows}")
        print(f"✅ Valid Rows:          {self.stats.valid_rows}")
        print(f"❌ Invalid Rows:        {self.stats.invalid_rows}")
        print(f"⏭️  Duplicate Rows:      {self.stats.duplicate_rows}")
        print(f"💾 Inserted Rows:       {self.stats.inserted_rows}")
        print(f"⏱️  Duration:            {duration:.2f}s")
        print("")

        if self.stats.errors:
            print(f"⚠️  Errors ({len(self.stats.errors)} total, showing first 10):")
            for error in self.stats.errors[:10]:
                print(f"   - {error}")

        print("="*70 + "\n")

        if self.dry_run:
            print("🔍 DRY-RUN MODE: No changes were made to the database")
        else:
            print(f"✅ SUCCESS: {self.stats.inserted_rows} records loaded into intake.company_raw_intake")
            print(f"🚀 Next step: Run pipeline with: python run_live_pipeline.py")

    def save_report(self, output_path: Optional[str] = None):
        """Save JSON report"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"intake_load_report_{timestamp}.json"

        report = self.stats.to_dict()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Report saved to: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Load CSV data into intake.company_raw_intake table"
    )
    parser.add_argument(
        "csv_file",
        help="Path to CSV file to load"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV without inserting to database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to insert per batch (default: 100)"
    )
    parser.add_argument(
        "--mapping",
        help="Path to custom JSON column mapping file"
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

    # Load custom mapping if provided
    column_mapping = None
    if args.mapping:
        try:
            with open(args.mapping, 'r') as f:
                column_mapping = json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load mapping file: {e}")
            sys.exit(1)

    # Run loader
    try:
        loader = IntakeDataLoader(connection_string, dry_run=args.dry_run)
        report = loader.load(args.csv_file, batch_size=args.batch_size, column_mapping=column_mapping)

        # Save report if requested
        if args.output:
            loader.save_report(args.output)

        # Exit with appropriate code
        if loader.stats.inserted_rows == 0 and not args.dry_run:
            sys.exit(1)  # Failure if no records inserted
        else:
            sys.exit(0)  # Success

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
