"""
Talent Flow — LinkedIn Monitor (Bridge Module)
================================================
Work Packet: wp-20260306-talent-flow-linkedin-monitor
ORBT: Build
CTB: hubs/people-intelligence/imo/middle/movement_engine/ (Middle layer)

BRIDGE between field_monitor vendor tier and the existing movement engine.

Data Flow:
    field_monitor.check_log (vendor tier, written by Cloudflare Workers)
        → THIS MODULE reads WHERE changed=true, domain='www.linkedin.com'
        → Maps linkedin_url path back to person_unique_id in people_master
        → Fires EVENT_TALENTFLOW_MOVE into MovementEngine.detect_event()
        → Existing movement engine processes the event (NO MODIFICATIONS)

Doctrine:
    - Vendor Tier: field_monitor.* — same tier as vendor.people / vendor.blog
    - IMO: All logic in Middle. This module READS from vendor, does NOT write.
    - Kill Switches: KILL_TALENT_FLOW_MONITOR, KILL_LINKEDIN_SEED
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LinkedInChange:
    """Detected change from field_monitor vendor tier."""
    log_id: str
    url_id: str
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    checked_at: datetime
    linkedin_path: str


@dataclass
class BridgeResult:
    """Result of bridging one change into the movement engine."""
    log_id: str
    person_unique_id: Optional[str]
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    event_fired: bool
    reason: str


class LinkedInMonitor:
    """
    Bridge: field_monitor vendor tier → Talent Flow movement engine.

    Reads detected LinkedIn changes from check_log, resolves person,
    fires EVENT_TALENTFLOW_MOVE into existing MovementEngine.
    """

    def __init__(self, db_url: str):
        self.db_url = db_url
        self._conn = None

    def _get_conn(self):
        if self._conn is None:
            import psycopg2
            self._conn = psycopg2.connect(self.db_url)
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ─── BRIDGE ────────────────────────────────────────────────

    def bridge_changes(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[BridgeResult]:
        """
        Read changes from vendor tier, fire events into movement engine.

        Args:
            since: Process changes after this time. Default: last 24h.
            limit: Max changes per run.
        """
        if os.environ.get('KILL_TALENT_FLOW_MONITOR', 'false').lower() == 'true':
            logger.warning("KILL_TALENT_FLOW_MONITOR active — skipping")
            return []

        conn = self._get_conn()
        changes = self._read_changes(conn, since, limit)
        if not changes:
            logger.info("No LinkedIn changes in vendor tier")
            return []

        logger.info(f"Bridging {len(changes)} LinkedIn changes")
        results = []

        for change in changes:
            result = self._bridge_one(conn, change)
            results.append(result)

        return results

    def _bridge_one(self, conn, change: LinkedInChange) -> BridgeResult:
        """Bridge a single change into the movement engine."""
        # Resolve person from linkedin path
        person = self._resolve_person(conn, change.linkedin_path)
        if not person:
            return BridgeResult(
                log_id=change.log_id,
                person_unique_id=None,
                field_name=change.field_name,
                old_value=change.old_value,
                new_value=change.new_value,
                event_fired=False,
                reason=f"No person match for path: {change.linkedin_path}"
            )

        # Build event metadata
        metadata = {
            "source": "field_monitor_linkedin",
            "field_name": change.field_name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "linkedin_url": person["linkedin_url"],
            "signal_date": change.checked_at,
            "vendor_log_id": change.log_id,
        }

        if change.field_name == "current_company":
            metadata["signal_type"] = "company_change"
            metadata["company_from"] = change.old_value
            metadata["company_to"] = change.new_value
        elif change.field_name == "current_title":
            metadata["signal_type"] = "job_change"
            metadata["title_from"] = change.old_value
            metadata["title_to"] = change.new_value

        # Fire into existing movement engine
        try:
            from .movement_engine import MovementEngine
            engine = MovementEngine()
            event = engine.detect_event(
                company_id=person["company_unique_id"],
                person_id=person["unique_id"],
                event_type="talentflow_move",
                metadata=metadata,
                source_system="field_monitor_linkedin",
                event_ts=change.checked_at
            )
            return BridgeResult(
                log_id=change.log_id,
                person_unique_id=person["unique_id"],
                field_name=change.field_name,
                old_value=change.old_value,
                new_value=change.new_value,
                event_fired=True,
                reason=f"EVENT_TALENTFLOW_MOVE fired (event_id={event.event_id})"
            )
        except Exception as e:
            logger.error(f"Bridge failed for {change.log_id}: {e}")
            return BridgeResult(
                log_id=change.log_id,
                person_unique_id=person["unique_id"],
                field_name=change.field_name,
                old_value=change.old_value,
                new_value=change.new_value,
                event_fired=False,
                reason=f"Movement engine error: {e}"
            )

    # ─── VENDOR TIER READ ──────────────────────────────────────

    def _read_changes(
        self, conn, since: Optional[datetime], limit: int
    ) -> List[LinkedInChange]:
        """Read from field_monitor.check_log (vendor tier). READ ONLY."""
        since_sql = (
            f"cl.checked_at >= '{since.isoformat()}'"
            if since else
            "cl.checked_at >= now() - interval '24 hours'"
        )
        query = f"""
            SELECT cl.log_id::text, cl.url_id::text, cl.field_name,
                   cl.old_value, cl.new_value, cl.checked_at, ur.path
            FROM field_monitor.check_log cl
            JOIN field_monitor.url_registry ur ON cl.url_id = ur.url_id
            WHERE cl.changed = true
              AND ur.domain = 'www.linkedin.com'
              AND ur.is_active = true
              AND {since_sql}
            ORDER BY cl.checked_at DESC
            LIMIT {limit}
        """
        with conn.cursor() as cur:
            cur.execute(query)
            return [
                LinkedInChange(
                    log_id=r[0], url_id=r[1], field_name=r[2],
                    old_value=r[3], new_value=r[4],
                    checked_at=r[5], linkedin_path=r[6]
                )
                for r in cur.fetchall()
            ]

    # ─── PERSON RESOLUTION ─────────────────────────────────────

    def _resolve_person(self, conn, linkedin_path: str) -> Optional[Dict[str, Any]]:
        """Map LinkedIn path back to people_master record."""
        query = """
            SELECT pm.unique_id, pm.company_unique_id, pm.linkedin_url
            FROM people.people_master pm
            WHERE pm.linkedin_url LIKE %s
            LIMIT 1
        """
        with conn.cursor() as cur:
            cur.execute(query, (f"%{linkedin_path}%",))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "unique_id": row[0],
            "company_unique_id": row[1],
            "linkedin_url": row[2],
        }

    # ─── SEED (operational setup) ──────────────────────────────

    def seed_urls(self, limit: int = 100) -> Dict[str, int]:
        """
        Seed LinkedIn URLs into vendor tier. One-time setup.
        Executes seed_linkedin_urls.sql.
        """
        if os.environ.get('KILL_LINKEDIN_SEED', 'false').lower() == 'true':
            logger.warning("KILL_LINKEDIN_SEED active — skipping")
            return {"urls_seeded": 0, "fields_created": 0}

        conn = self._get_conn()
        sql_path = os.path.join(
            os.path.dirname(__file__),
            '..', '..', '..', 'scripts', 'seed_linkedin_urls.sql'
        )

        with open(sql_path, 'r') as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM field_monitor.url_registry
                WHERE domain = 'www.linkedin.com' AND is_active = true
            """)
            urls = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM field_monitor.field_state fs
                JOIN field_monitor.url_registry ur ON fs.url_id = ur.url_id
                WHERE ur.domain = 'www.linkedin.com'
            """)
            fields = cur.fetchone()[0]

        logger.info(f"Seeded {urls} URLs, {fields} field_state entries")
        return {"urls_seeded": urls, "fields_created": fields}
