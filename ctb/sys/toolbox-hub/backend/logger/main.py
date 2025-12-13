"""
Logger / Monitor Backend - Barton Toolbox Hub
Barton ID: 04.04.02.04.10000.006
Altitude: 10000ft

Central dashboard for audit + error tracking
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOOL_BARTON_ID = "04.04.02.04.10000.006"
BLUEPRINT_ID = "04.svg.marketing.outreach.v1"


class LoggerMonitor:
    """Central logging and monitoring dashboard"""

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        logger.info(f"[{TOOL_BARTON_ID}] Logger/Monitor initialized")

    def get_recent_errors(self, limit: int = 100) -> List[Dict]:
        """Get recent errors from shq.error_master"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM shq.error_master ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit events"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM shq.audit_log ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            return [dict(row) for row in cur.fetchall()]

    def get_system_stats(self) -> Dict:
        """Get system-wide statistics"""
        stats = {}

        # Error counts by severity
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT severity, COUNT(*) as count
                FROM shq.error_master
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY severity
            """)
            stats["errors_24h"] = {row['severity']: row['count'] for row in cur.fetchall()}

        return stats

    def log_event(self, event_type: str, data: Dict):
        """Log event to audit table"""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO shq.audit_log (event_type, event_data, barton_id, created_at) VALUES (%s, %s, %s, NOW())",
                (event_type, json.dumps(data), TOOL_BARTON_ID)
            )
            self.conn.commit()


def main():
    connection_string = os.getenv("NEON_CONNECTION_STRING", "")
    monitor = LoggerMonitor(connection_string)

    # Get system stats
    stats = monitor.get_system_stats()
    logger.info(f"[{TOOL_BARTON_ID}] System stats: {stats}")


if __name__ == "__main__":
    main()
