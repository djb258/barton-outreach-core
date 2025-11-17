"""
N8N Webhook Validation Script - Barton Toolbox Hub

Tests all N8N webhook endpoints defined in n8n_endpoints.config.json
Validates connectivity, authentication, and response format.

Usage:
    python validate_n8n_webhooks.py
    python validate_n8n_webhooks.py --verbose
    python validate_n8n_webhooks.py --tool router
"""

import os
import sys
import json
import logging
import argparse
import requests
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class N8NWebhookValidator:
    """Validates N8N webhook endpoints"""

    def __init__(self, config_path: str, api_key: Optional[str] = None):
        self.config_path = config_path
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        self.config = self._load_config()
        self.results = []

    def _load_config(self) -> Dict:
        """Load N8N endpoints configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"✅ Loaded config from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config file: {e}")
            sys.exit(1)

    def validate_endpoint(self, endpoint: Dict) -> Dict:
        """
        Validate a single N8N webhook endpoint

        Args:
            endpoint: Endpoint configuration dictionary

        Returns:
            Validation result dictionary
        """
        tool_id = endpoint.get('tool_id')
        tool_name = endpoint.get('tool_name')
        full_url = endpoint.get('full_url')

        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {tool_name} ({tool_id})")
        logger.info(f"URL: {full_url}")

        result = {
            "tool_id": tool_id,
            "tool_name": tool_name,
            "url": full_url,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }

        # Test 1: URL Reachability
        try:
            logger.info("  🔍 Test 1: Checking URL reachability...")

            headers = endpoint.get('headers', {})
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # Try a simple GET request first (some webhooks accept GET for health)
            response = requests.get(
                full_url,
                headers=headers,
                timeout=10,
                allow_redirects=True
            )

            result["tests"]["reachability"] = {
                "status": "pass" if response.status_code in [200, 405, 501] else "fail",
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }

            if response.status_code in [200, 405, 501]:
                logger.info(f"  ✅ URL is reachable (HTTP {response.status_code})")
            else:
                logger.warning(f"  ⚠️  Unexpected status code: {response.status_code}")

        except requests.exceptions.Timeout:
            result["tests"]["reachability"] = {"status": "fail", "error": "Timeout"}
            logger.error("  ❌ Request timeout")
        except requests.exceptions.ConnectionError:
            result["tests"]["reachability"] = {"status": "fail", "error": "Connection failed"}
            logger.error("  ❌ Connection failed - endpoint may not exist")
        except Exception as e:
            result["tests"]["reachability"] = {"status": "fail", "error": str(e)}
            logger.error(f"  ❌ Error: {e}")

        # Test 2: POST Request with Sample Payload
        try:
            logger.info("  🔍 Test 2: Testing POST with sample payload...")

            # Get first event type as sample
            event_types = endpoint.get('event_types', [])
            if event_types:
                sample_event = event_types[0]
                sample_payload = sample_event.get('payload_example', {})

                response = requests.post(
                    full_url,
                    json=sample_payload,
                    headers=headers,
                    timeout=10
                )

                result["tests"]["post_request"] = {
                    "status": "pass" if response.status_code in [200, 201, 202] else "fail",
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }

                if response.status_code in [200, 201, 202]:
                    logger.info(f"  ✅ POST request accepted (HTTP {response.status_code})")

                    # Try to parse response
                    try:
                        response_data = response.json()
                        result["tests"]["post_request"]["response_format"] = "json"

                        # Check HEIR/ORBT format
                        if "heir_id" in response_data and "status" in response_data:
                            result["tests"]["post_request"]["heir_orbt_compliant"] = True
                            logger.info("  ✅ Response follows HEIR/ORBT format")
                        else:
                            result["tests"]["post_request"]["heir_orbt_compliant"] = False
                            logger.warning("  ⚠️  Response doesn't follow HEIR/ORBT format")

                    except json.JSONDecodeError:
                        result["tests"]["post_request"]["response_format"] = "non-json"
                        logger.warning("  ⚠️  Response is not JSON")

                else:
                    logger.warning(f"  ⚠️  POST returned HTTP {response.status_code}")
            else:
                result["tests"]["post_request"] = {"status": "skip", "reason": "No event types defined"}
                logger.info("  ⏭️  Skipped - no event types configured")

        except requests.exceptions.Timeout:
            result["tests"]["post_request"] = {"status": "fail", "error": "Timeout"}
            logger.error("  ❌ POST request timeout")
        except Exception as e:
            result["tests"]["post_request"] = {"status": "fail", "error": str(e)}
            logger.error(f"  ❌ POST error: {e}")

        # Test 3: Authentication
        logger.info("  🔍 Test 3: Testing authentication...")

        if self.api_key:
            # Try request without auth
            try:
                response_no_auth = requests.post(
                    full_url,
                    json={},
                    timeout=5
                )

                # If webhook requires auth, it should return 401/403 without it
                if response_no_auth.status_code in [401, 403]:
                    result["tests"]["authentication"] = {"status": "pass", "requires_auth": True}
                    logger.info("  ✅ Authentication is required and enforced")
                elif response_no_auth.status_code in [200, 201, 202]:
                    result["tests"]["authentication"] = {"status": "warning", "requires_auth": False}
                    logger.warning("  ⚠️  Endpoint accepts unauthenticated requests")
                else:
                    result["tests"]["authentication"] = {"status": "unknown", "status_code": response_no_auth.status_code}
                    logger.info(f"  ℹ️  Auth status unclear (HTTP {response_no_auth.status_code})")

            except Exception as e:
                result["tests"]["authentication"] = {"status": "error", "error": str(e)}
                logger.error(f"  ❌ Auth test error: {e}")
        else:
            result["tests"]["authentication"] = {"status": "skip", "reason": "No API key provided"}
            logger.info("  ⏭️  Skipped - no API key set")

        # Calculate overall status
        test_statuses = [test.get("status") for test in result["tests"].values()]
        if "fail" in test_statuses:
            result["overall_status"] = "fail"
        elif "warning" in test_statuses:
            result["overall_status"] = "warning"
        elif "pass" in test_statuses:
            result["overall_status"] = "pass"
        else:
            result["overall_status"] = "unknown"

        logger.info(f"Overall Status: {result['overall_status'].upper()}")

        return result

    def validate_all(self, tool_filter: Optional[str] = None) -> List[Dict]:
        """
        Validate all webhook endpoints

        Args:
            tool_filter: Optional tool_id to filter (e.g., "router")

        Returns:
            List of validation results
        """
        endpoints = self.config.get('endpoints', [])

        if tool_filter:
            endpoints = [e for e in endpoints if e.get('tool_id') == tool_filter]
            if not endpoints:
                logger.error(f"❌ No endpoints found for tool: {tool_filter}")
                return []

        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 N8N WEBHOOK VALIDATION")
        logger.info(f"{'='*60}")
        logger.info(f"Total endpoints to test: {len(endpoints)}")
        logger.info(f"Base URL: {self.config.get('base_url')}")

        for endpoint in endpoints:
            result = self.validate_endpoint(endpoint)
            self.results.append(result)

        return self.results

    def generate_report(self) -> Dict:
        """Generate validation summary report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('overall_status') == 'pass')
        failed = sum(1 for r in self.results if r.get('overall_status') == 'fail')
        warnings = sum(1 for r in self.results if r.get('overall_status') == 'warning')

        report = {
            "summary": {
                "total_endpoints": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "N/A"
            },
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }

        return report

    def print_summary(self):
        """Print validation summary to console"""
        report = self.generate_report()

        print(f"\n{'='*60}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Endpoints:  {report['summary']['total_endpoints']}")
        print(f"✅ Passed:         {report['summary']['passed']}")
        print(f"❌ Failed:         {report['summary']['failed']}")
        print(f"⚠️  Warnings:       {report['summary']['warnings']}")
        print(f"Success Rate:     {report['summary']['success_rate']}")
        print(f"{'='*60}\n")

        # Print per-endpoint status
        print("Per-Endpoint Status:")
        for result in self.results:
            status_emoji = {
                "pass": "✅",
                "fail": "❌",
                "warning": "⚠️",
                "unknown": "❓"
            }.get(result['overall_status'], "❓")

            print(f"  {status_emoji} {result['tool_name']} ({result['tool_id']})")

    def save_report(self, output_path: str):
        """Save validation report to JSON file"""
        report = self.generate_report()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n✅ Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate N8N webhook endpoints")
    parser.add_argument(
        "--config",
        default="../../config/n8n_endpoints.config.json",
        help="Path to N8N endpoints config file"
    )
    parser.add_argument(
        "--tool",
        help="Filter by tool ID (e.g., router, validator)"
    )
    parser.add_argument(
        "--output",
        help="Output path for JSON report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve config path relative to script location
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config

    if not config_path.exists():
        logger.error(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    # Initialize validator
    validator = N8NWebhookValidator(str(config_path))

    # Run validation
    validator.validate_all(tool_filter=args.tool)

    # Print summary
    validator.print_summary()

    # Save report if requested
    if args.output:
        validator.save_report(args.output)

    # Exit with appropriate code
    report = validator.generate_report()
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
