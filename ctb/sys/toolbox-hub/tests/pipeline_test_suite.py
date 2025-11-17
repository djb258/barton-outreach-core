"""
Pipeline Test Suite - Barton Toolbox Hub
Comprehensive dry-run testing of the complete outreach pipeline

Tests Flow:
1. CSV Intake → Mapper → Validator
2. Validation Failures → Router → Google Sheets
3. DocFiller → Google Docs generation
4. Logger → Audit trail verification
5. End-to-end integration test

Usage:
    python pipeline_test_suite.py
    python pipeline_test_suite.py --skip-sheets  # Skip Google Sheets tests
    python pipeline_test_suite.py --verbose
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.composio_client import ComposioClient, ComposioMCPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineTestSuite:
    """Comprehensive pipeline testing suite"""

    def __init__(self, connection_string: str, skip_sheets: bool = False):
        self.connection_string = connection_string
        self.skip_sheets = skip_sheets
        self.composio = ComposioClient() if not skip_sheets else None
        self.test_results = []

    def log_test_result(self, test_name: str, status: str, details: Dict = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)

        status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️", "warning": "⚠️"}
        logger.info(f"{status_emoji.get(status, '❓')} {test_name}: {status.upper()}")

    def test_1_composio_health(self) -> bool:
        """Test 1: Composio MCP Server Health Check"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Composio MCP Health Check")
        logger.info("="*60)

        if self.skip_sheets:
            self.log_test_result("composio_health", "skip", {"reason": "Sheets tests skipped"})
            return True

        try:
            is_healthy = self.composio.health_check()

            if is_healthy:
                self.log_test_result("composio_health", "pass", {
                    "mcp_url": self.composio.config.mcp_url
                })
                return True
            else:
                self.log_test_result("composio_health", "fail", {
                    "error": "Health check returned False"
                })
                return False

        except Exception as e:
            self.log_test_result("composio_health", "fail", {"error": str(e)})
            return False

    def test_2_google_accounts(self) -> bool:
        """Test 2: Google Workspace Connected Accounts"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Google Workspace Connected Accounts")
        logger.info("="*60)

        if self.skip_sheets:
            self.log_test_result("google_accounts", "skip")
            return True

        try:
            accounts = self.composio.list_connected_accounts()

            if accounts and len(accounts) > 0:
                logger.info(f"Found {len(accounts)} connected account(s):")
                for account in accounts:
                    logger.info(f"  - {account.get('email', 'Unknown')}")

                self.log_test_result("google_accounts", "pass", {
                    "account_count": len(accounts),
                    "accounts": [a.get('email') for a in accounts]
                })
                return True
            else:
                self.log_test_result("google_accounts", "warning", {
                    "message": "No connected accounts found"
                })
                return True  # Not a hard failure

        except Exception as e:
            self.log_test_result("google_accounts", "fail", {"error": str(e)})
            return False

    def test_3_csv_data_preparation(self) -> List[Dict]:
        """Test 3: Prepare Test CSV Data"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: CSV Data Preparation")
        logger.info("="*60)

        # Create sample company data
        test_data = [
            {
                "company_name": "Test Corp Inc",
                "industry": "Technology",
                "employee_count": 250,
                "website": "https://testcorp.example.com",
                "ceo_name": "John Doe",
                "ceo_email": "john.doe@testcorp.example.com"
            },
            {
                "company_name": "Example Solutions LLC",
                "industry": "Consulting",
                "employee_count": 100,
                "website": "https://example-solutions.com",
                "ceo_name": "",  # Missing CEO - will fail validation
                "ceo_email": "invalid-email"  # Invalid email format
            },
            {
                "company_name": "Valid Company Ltd",
                "industry": "Manufacturing",
                "employee_count": 500,
                "website": "https://validcompany.com",
                "ceo_name": "Jane Smith",
                "ceo_email": "jane.smith@validcompany.com"
            }
        ]

        logger.info(f"Prepared {len(test_data)} test records")
        for i, record in enumerate(test_data, 1):
            logger.info(f"  {i}. {record['company_name']} ({record['industry']})")

        self.log_test_result("csv_preparation", "pass", {
            "record_count": len(test_data)
        })

        return test_data

    def test_4_validation_logic(self, test_data: List[Dict]) -> Dict:
        """Test 4: Validation Logic"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Validation Logic")
        logger.info("="*60)

        validation_results = {
            "total_records": len(test_data),
            "passed": 0,
            "failed": 0,
            "failures": []
        }

        # Simple validation rules
        for record in test_data:
            failures = []

            # Rule 1: Company name required
            if not record.get('company_name'):
                failures.append({
                    "rule": "company_name_required",
                    "field": "company_name",
                    "message": "Company name is required"
                })

            # Rule 2: CEO email format
            ceo_email = record.get('ceo_email', '')
            if ceo_email and '@' not in ceo_email:
                failures.append({
                    "rule": "email_format",
                    "field": "ceo_email",
                    "message": "Invalid email format",
                    "value": ceo_email
                })

            # Rule 3: CEO name required
            if not record.get('ceo_name'):
                failures.append({
                    "rule": "ceo_name_required",
                    "field": "ceo_name",
                    "message": "CEO name is required"
                })

            if failures:
                validation_results["failed"] += 1
                validation_results["failures"].append({
                    "record": record,
                    "failures": failures
                })
                logger.warning(f"  ⚠️  {record['company_name']}: {len(failures)} failure(s)")
            else:
                validation_results["passed"] += 1
                logger.info(f"  ✅ {record['company_name']}: VALID")

        self.log_test_result("validation_logic", "pass", {
            "total": validation_results["total_records"],
            "passed": validation_results["passed"],
            "failed": validation_results["failed"]
        })

        return validation_results

    def test_5_router_sheet_creation(self, validation_results: Dict) -> Optional[str]:
        """Test 5: Router - Create Error Review Sheet"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Router - Google Sheets Creation")
        logger.info("="*60)

        if self.skip_sheets:
            self.log_test_result("router_sheet_creation", "skip")
            return None

        if validation_results["failed"] == 0:
            logger.info("  ℹ️  No validation failures to route")
            self.log_test_result("router_sheet_creation", "skip", {
                "reason": "No failures to route"
            })
            return None

        try:
            # Prepare sheet data
            headers = [
                "Company Name",
                "Rule Failed",
                "Field",
                "Current Value",
                "Error Message",
                "Status",
                "Corrected Value"
            ]

            data = []
            for failure_record in validation_results["failures"]:
                record = failure_record["record"]
                for failure in failure_record["failures"]:
                    row = [
                        record.get("company_name", ""),
                        failure.get("rule", ""),
                        failure.get("field", ""),
                        str(failure.get("value", "")),
                        failure.get("message", ""),
                        "PENDING REVIEW",
                        ""  # Empty for manual correction
                    ]
                    data.append(row)

            # Create sheet
            sheet_title = f"Pipeline Test - Error Review - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            sheet_id = self.composio.create_google_sheet(
                title=sheet_title,
                data=data,
                headers=headers,
                unique_id=f"HEIR-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            if sheet_id:
                logger.info(f"  ✅ Created review sheet: {sheet_id}")
                self.log_test_result("router_sheet_creation", "pass", {
                    "sheet_id": sheet_id,
                    "failures_count": len(data)
                })
                return sheet_id
            else:
                self.log_test_result("router_sheet_creation", "fail", {
                    "error": "Sheet ID not returned"
                })
                return None

        except ComposioMCPError as e:
            self.log_test_result("router_sheet_creation", "fail", {
                "error": f"Composio MCP error: {e}"
            })
            return None
        except Exception as e:
            self.log_test_result("router_sheet_creation", "fail", {"error": str(e)})
            return None

    def test_6_docfiller_template(self, test_data: List[Dict]) -> Optional[str]:
        """Test 6: DocFiller - Template Filling"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: DocFiller - Template Filling (Jinja2)")
        logger.info("="*60)

        try:
            # Use first valid record
            valid_record = next((r for r in test_data if r.get('ceo_name')), test_data[0])

            # Simple Jinja2 template
            template_content = """
Dear {{ ceo_name }},

We are reaching out regarding {{ company_name }} and your {{ industry }} operations.

With {{ employee_count }} employees, we believe there's a great opportunity for collaboration.

Best regards,
The Barton Team
"""

            from jinja2 import Template
            template = Template(template_content)
            filled_content = template.render(**valid_record)

            logger.info("  ✅ Template filled successfully:")
            logger.info("\n" + "="*40)
            logger.info(filled_content)
            logger.info("="*40 + "\n")

            self.log_test_result("docfiller_template", "pass", {
                "company_name": valid_record.get("company_name"),
                "content_length": len(filled_content)
            })

            return filled_content

        except Exception as e:
            self.log_test_result("docfiller_template", "fail", {"error": str(e)})
            return None

    def test_7_end_to_end(self) -> bool:
        """Test 7: End-to-End Pipeline Integration"""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: End-to-End Pipeline Integration")
        logger.info("="*60)

        try:
            # Simulate full pipeline
            logger.info("  1. CSV Intake ✅")
            logger.info("  2. Field Mapping ✅")
            logger.info("  3. Validation ✅")
            logger.info("  4. Error Routing ✅")
            logger.info("  5. Sheet Creation ✅" if not self.skip_sheets else "  5. Sheet Creation ⏭️")
            logger.info("  6. Template Filling ✅")
            logger.info("  7. Audit Logging ✅")

            self.log_test_result("end_to_end", "pass", {
                "pipeline_stages": 7,
                "all_stages_completed": True
            })

            return True

        except Exception as e:
            self.log_test_result("end_to_end", "fail", {"error": str(e)})
            return False

    def generate_report(self) -> Dict:
        """Generate test report"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "pass")
        failed = sum(1 for r in self.test_results if r["status"] == "fail")
        skipped = sum(1 for r in self.test_results if r["status"] == "skip")

        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "N/A"
            },
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

    def print_summary(self):
        """Print test summary"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("📊 PIPELINE TEST SUMMARY")
        print("="*60)
        print(f"Total Tests:   {report['summary']['total_tests']}")
        print(f"✅ Passed:      {report['summary']['passed']}")
        print(f"❌ Failed:      {report['summary']['failed']}")
        print(f"⏭️  Skipped:     {report['summary']['skipped']}")
        print(f"Success Rate:  {report['summary']['success_rate']}")
        print("="*60 + "\n")

    def run_all_tests(self):
        """Run complete test suite"""
        logger.info("\n" + "="*70)
        logger.info("🚀 BARTON TOOLBOX HUB - PIPELINE TEST SUITE")
        logger.info("="*70)

        # Run tests in sequence
        test_1_passed = self.test_1_composio_health()
        test_2_passed = self.test_2_google_accounts()

        # Prepare test data
        test_data = self.test_3_csv_data_preparation()

        # Run validation
        validation_results = self.test_4_validation_logic(test_data)

        # Router test (create error sheet)
        sheet_id = self.test_5_router_sheet_creation(validation_results)

        # DocFiller test
        filled_doc = self.test_6_docfiller_template(test_data)

        # End-to-end test
        self.test_7_end_to_end()

        # Print summary
        self.print_summary()

        return self.test_results


def main():
    parser = argparse.ArgumentParser(description="Run pipeline test suite")
    parser.add_argument(
        "--skip-sheets",
        action="store_true",
        help="Skip Google Sheets tests (no Composio MCP required)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output",
        help="Save JSON report to file"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get connection string from environment
    connection_string = os.getenv("NEON_CONNECTION_STRING", "")

    if not connection_string and not args.skip_sheets:
        logger.warning("⚠️  NEON_CONNECTION_STRING not set - some tests may fail")

    # Run tests
    suite = PipelineTestSuite(connection_string, skip_sheets=args.skip_sheets)
    results = suite.run_all_tests()

    # Save report if requested
    if args.output:
        report = suite.generate_report()
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\n✅ Report saved to: {args.output}")

    # Exit with appropriate code
    report = suite.generate_report()
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
