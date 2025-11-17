"""
Router (Messy Logic) Backend - Barton Toolbox Hub
Barton ID: 04.04.02.04.10000.001
Altitude: 20000ft

Routes invalid data to Google Sheets for manual review and sync back to pipeline.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
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
TOOL_BARTON_ID = "04.04.02.04.10000.001"
BLUEPRINT_ID = "04.svg.marketing.outreach.v1"


@dataclass
class RouterConfig:
    """Router configuration from environment"""
    neon_connection_string: str
    google_sheets_api_key: str
    google_service_account_email: str
    kill_switch_threshold: float = 0.5

    @classmethod
    def from_env(cls):
        return cls(
            neon_connection_string=os.getenv("NEON_CONNECTION_STRING", ""),
            google_sheets_api_key=os.getenv("GOOGLE_SHEETS_API_KEY", ""),
            google_service_account_email=os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
        )


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
            self.log_error("database_connection_failed", str(e))
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
            self.log_error("query_execution_failed", str(e), {"query": query})
            raise

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute INSERT query and return row ID"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()
                return cur.fetchone()[0] if cur.rowcount > 0 else None
        except Exception as e:
            self.conn.rollback()
            self.log_error("insert_execution_failed", str(e), {"query": query})
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

    def log_error(self, error_code: str, error_message: str, context: Dict = None):
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
                "error",
                "router",
                json.dumps(context or {}),
                TOOL_BARTON_ID
            )
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log error: {e}")


class MessyFlowRouter:
    """Main Router class for handling invalid data routing"""

    def __init__(self, config: RouterConfig):
        self.config = config
        self.db = NeonDatabase(config.neon_connection_string)
        self.composio = ComposioClient()
        self.error_count = 0
        self.success_count = 0

    def initialize(self):
        """Initialize router and database connection"""
        self.db.connect()
        logger.info(f"[{TOOL_BARTON_ID}] MessyFlow Router initialized")

        # Log initialization
        self.db.log_audit("router.initialized", {
            "barton_id": TOOL_BARTON_ID,
            "blueprint_id": BLUEPRINT_ID,
            "timestamp": datetime.now().isoformat()
        })

    def shutdown(self):
        """Shutdown router and cleanup"""
        self.db.disconnect()
        logger.info(f"[{TOOL_BARTON_ID}] MessyFlow Router shutdown")

    def check_kill_switch(self) -> bool:
        """Check if kill switch should be triggered"""
        total = self.error_count + self.success_count
        if total == 0:
            return False

        error_rate = self.error_count / total
        if error_rate > self.config.kill_switch_threshold:
            logger.critical(f"[{TOOL_BARTON_ID}] Kill switch triggered! Error rate: {error_rate:.2%}")
            self.db.log_error(
                "kill_switch_triggered",
                f"Error rate {error_rate:.2%} exceeds threshold {self.config.kill_switch_threshold:.2%}",
                {"error_count": self.error_count, "success_count": self.success_count}
            )
            return True
        return False

    def get_pending_errors(self) -> List[Dict]:
        """Retrieve pending errors from pipeline_errors table"""
        query = """
            SELECT
                error_id,
                company_unique_id,
                error_type,
                error_message,
                error_payload,
                created_at
            FROM marketing.pipeline_errors
            WHERE resolution_status = 'pending'
            ORDER BY created_at DESC
            LIMIT 100
        """
        return self.db.execute_query(query)

    def route_to_google_sheet(self, error_record: Dict) -> Optional[str]:
        """
        Create Google Sheet for manual review of error
        Returns sheet_id if successful, None otherwise
        """
        try:
            # Prepare sheet data
            sheet_title = f"Error Review - {error_record.get('error_type', 'Unknown')} - {datetime.now().strftime('%Y-%m-%d')}"

            headers = [
                "Error ID",
                "Company ID",
                "Error Type",
                "Error Message",
                "Payload",
                "Created At",
                "Status",
                "Resolution Notes"
            ]

            # Create single row for this error
            data = [[
                str(error_record.get('error_id', '')),
                str(error_record.get('company_unique_id', '')),
                str(error_record.get('error_type', '')),
                str(error_record.get('error_message', '')),
                json.dumps(error_record.get('error_payload', {})),
                str(error_record.get('created_at', '')),
                'PENDING REVIEW',
                ''  # Empty column for manual notes
            ]]

            # Create sheet via Composio MCP
            unique_id = f"HEIR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-ROUTE-{error_record['error_id']}"

            sheet_id = self.composio.create_google_sheet(
                title=sheet_title,
                data=data,
                headers=headers,
                unique_id=unique_id
            )

            # Log successful routing
            self.db.log_audit("error.routed_to_sheet", {
                "error_id": error_record['error_id'],
                "company_unique_id": error_record.get('company_unique_id'),
                "sheet_id": sheet_id,
                "error_type": error_record.get('error_type'),
                "sheet_title": sheet_title
            })

            logger.info(f"[{TOOL_BARTON_ID}] ✅ Created sheet for error {error_record['error_id']}: {sheet_id}")
            self.success_count += 1

            return sheet_id

        except ComposioMCPError as e:
            logger.error(f"[{TOOL_BARTON_ID}] Composio MCP error: {e}")
            self.error_count += 1
            self.db.log_error(
                "composio_mcp_failed",
                str(e),
                {"error_record": error_record}
            )
            return None
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Unexpected error: {e}")
            self.error_count += 1
            self.db.log_error(
                "sheet_creation_failed",
                str(e),
                {"error_record": error_record}
            )
            return None

    def mark_error_routed(self, error_id: int, sheet_id: str):
        """Mark error as routed in database"""
        query = """
            UPDATE marketing.pipeline_errors
            SET
                resolution_status = 'routed',
                resolution_metadata = jsonb_build_object('sheet_id', %s),
                updated_at = NOW()
            WHERE error_id = %s
        """
        self.db.execute_insert(query, (sheet_id, error_id))

    def sync_from_google_sheet(self, sheet_id: str, tab_name: str = "Sheet1") -> Optional[Dict]:
        """
        Sync cleaned data back from Google Sheet
        Returns cleaned data if successful, None otherwise
        """
        try:
            # Read data from Google Sheet
            unique_id = f"HEIR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-SYNC-{sheet_id}"

            sheet_data = self.composio.read_from_sheet(
                sheet_id=sheet_id,
                tab_name=tab_name,
                range_spec="A1:Z1000",
                unique_id=unique_id
            )

            if not sheet_data or len(sheet_data) < 2:
                logger.warning(f"[{TOOL_BARTON_ID}] No data found in sheet {sheet_id}")
                return None

            # Parse data (first row is headers)
            headers = sheet_data[0]
            rows = sheet_data[1:]

            # Convert to list of dictionaries
            cleaned_records = []
            for row in rows:
                record = {}
                for i, header in enumerate(headers):
                    record[header] = row[i] if i < len(row) else ""
                cleaned_records.append(record)

            # Log successful sync
            self.db.log_audit("sheet.synced", {
                "sheet_id": sheet_id,
                "action": "data_retrieved",
                "records_count": len(cleaned_records)
            })

            logger.info(f"[{TOOL_BARTON_ID}] ✅ Synced {len(cleaned_records)} record(s) from sheet {sheet_id}")

            return {
                "sheet_id": sheet_id,
                "records": cleaned_records,
                "record_count": len(cleaned_records)
            }

        except ComposioMCPError as e:
            logger.error(f"[{TOOL_BARTON_ID}] Composio MCP error during sync: {e}")
            self.error_count += 1
            self.db.log_error(
                "composio_mcp_failed",
                str(e),
                {"sheet_id": sheet_id, "action": "sync"}
            )
            return None
        except Exception as e:
            logger.error(f"[{TOOL_BARTON_ID}] Unexpected error during sync: {e}")
            self.error_count += 1
            self.db.log_error(
                "sheet_sync_failed",
                str(e),
                {"sheet_id": sheet_id}
            )
            return None

    def process_routing_queue(self):
        """Main processing loop for routing errors"""
        logger.info(f"[{TOOL_BARTON_ID}] Starting routing queue processing")

        # Check kill switch before processing
        if self.check_kill_switch():
            logger.critical(f"[{TOOL_BARTON_ID}] Processing halted due to kill switch")
            return

        # Get pending errors
        pending_errors = self.get_pending_errors()
        logger.info(f"[{TOOL_BARTON_ID}] Found {len(pending_errors)} pending errors")

        for error in pending_errors:
            # Route to Google Sheet
            sheet_id = self.route_to_google_sheet(error)

            if sheet_id:
                # Mark as routed
                self.mark_error_routed(error['error_id'], sheet_id)

        # Log summary
        self.db.log_audit("routing.queue_processed", {
            "total_processed": len(pending_errors),
            "success_count": self.success_count,
            "error_count": self.error_count
        })


def main():
    """Main entry point"""
    logger.info(f"[{TOOL_BARTON_ID}] Starting MessyFlow Router")

    # Load configuration
    config = RouterConfig.from_env()

    # Initialize router
    router = MessyFlowRouter(config)
    router.initialize()

    try:
        # Process routing queue
        router.process_routing_queue()
    except Exception as e:
        logger.error(f"[{TOOL_BARTON_ID}] Fatal error: {e}")
        router.db.log_error("fatal_error", str(e))
    finally:
        # Cleanup
        router.shutdown()


if __name__ == "__main__":
    main()
