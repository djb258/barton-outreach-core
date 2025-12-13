"""
Neon Database Connector
Handles all database operations for Talent Flow Agent

CORRECTIONS LIVE HERE: All DB queries isolated to this file
"""

import asyncpg
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class NeonConnector:
    """
    Standalone database connector

    All SQL queries live here - easy to fix without touching other modules
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_url = os.getenv(config['database']['connection_string_env'])
        self.schema = config['database']['schema']
        self.pool = None

    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            max_size=self.config['database']['max_connections'],
            command_timeout=self.config['database']['timeout_seconds']
        )

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    async def get_active_people(self, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """
        Get all active people from people_master

        Returns people who:
        - Have been updated in last N days OR
        - Are marked for review OR
        - Have no movement snapshot yet
        """
        query = f"""
            SELECT
                p.unique_id as person_unique_id,
                p.full_name,
                p.title,
                p.company_unique_id,
                p.company_name,
                p.linkedin_url,
                p.start_date,
                p.end_date,
                p.created_at,
                p.updated_at,
                p.last_enrichment_attempt,
                p.data_source,
                s.enrichment_hash as last_snapshot_hash,
                s.snapshot_date as last_snapshot_date
            FROM {self.schema}.people_master p
            LEFT JOIN {self.schema}.talent_flow_snapshots s
                ON p.unique_id = s.person_unique_id
                AND s.snapshot_date = (
                    SELECT MAX(snapshot_date)
                    FROM {self.schema}.talent_flow_snapshots
                    WHERE person_unique_id = p.unique_id
                )
            WHERE
                p.updated_at >= NOW() - INTERVAL '{lookback_days} days'
                OR s.snapshot_date IS NULL
            ORDER BY p.updated_at DESC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def get_person_snapshot(self, person_unique_id: str) -> Optional[Dict[str, Any]]:
        """Get most recent snapshot for a person"""
        query = f"""
            SELECT *
            FROM {self.schema}.talent_flow_snapshots
            WHERE person_unique_id = $1
            ORDER BY snapshot_date DESC
            LIMIT 1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, person_unique_id)
            return dict(row) if row else None

    async def save_snapshot(
        self,
        person_unique_id: str,
        enrichment_hash: str,
        snapshot_data: Dict[str, Any]
    ):
        """Save current state snapshot"""
        query = f"""
            INSERT INTO {self.schema}.talent_flow_snapshots (
                person_unique_id,
                enrichment_hash,
                snapshot_data,
                snapshot_date,
                created_at
            )
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (person_unique_id, snapshot_date)
            DO UPDATE SET
                enrichment_hash = EXCLUDED.enrichment_hash,
                snapshot_data = EXCLUDED.snapshot_data
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                person_unique_id,
                enrichment_hash,
                snapshot_data
            )

    async def insert_movement(
        self,
        person_unique_id: str,
        movement_type: str,
        confidence: float,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any],
        data_source: str,
        metadata: Dict[str, Any]
    ) -> int:
        """Insert detected movement"""
        query = f"""
            INSERT INTO {self.schema}.talent_flow_movements (
                person_unique_id,
                movement_type,
                confidence,
                old_state,
                new_state,
                data_source,
                metadata,
                detected_at,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            RETURNING movement_id
        """

        async with self.pool.acquire() as conn:
            movement_id = await conn.fetchval(
                query,
                person_unique_id,
                movement_type,
                confidence,
                old_state,
                new_state,
                data_source,
                metadata
            )
            return movement_id

    async def insert_bit_signal(
        self,
        person_unique_id: str,
        company_unique_id: str,
        signal_type: str,
        signal_weight: int,
        movement_id: int,
        metadata: Dict[str, Any]
    ):
        """Generate BIT signal from movement"""
        query = f"""
            INSERT INTO {self.schema}.bit_signal (
                person_unique_id,
                company_unique_id,
                signal_type,
                signal_weight,
                source_id,
                source_type,
                metadata,
                detected_at,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, 'talent_flow_movement', $6, NOW(), NOW())
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                person_unique_id,
                company_unique_id,
                signal_type,
                signal_weight,
                movement_id,
                metadata
            )

    async def log_to_shq(
        self,
        worker_id: str,
        process_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = 'INFO'
    ):
        """Log to SHQ audit log"""
        query = """
            INSERT INTO shq.audit_log (
                worker_id,
                process_id,
                event_type,
                event_data,
                severity,
                created_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                worker_id,
                process_id,
                event_type,
                event_data,
                severity
            )

    async def check_recent_movement(
        self,
        person_unique_id: str,
        cooldown_hours: int
    ) -> bool:
        """Check if person already has recent movement (prevent reprocessing)"""
        query = f"""
            SELECT COUNT(*)
            FROM {self.schema}.talent_flow_movements
            WHERE person_unique_id = $1
              AND detected_at >= NOW() - INTERVAL '{cooldown_hours} hours'
        """

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query, person_unique_id)
            return count > 0

    async def get_movement_count_this_month(self, person_unique_id: str) -> int:
        """Get number of movements detected this month"""
        query = f"""
            SELECT COUNT(*)
            FROM {self.schema}.talent_flow_movements
            WHERE person_unique_id = $1
              AND detected_at >= DATE_TRUNC('month', NOW())
        """

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, person_unique_id)
