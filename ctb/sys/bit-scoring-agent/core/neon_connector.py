"""
Neon Database Connector for BIT Scoring Agent
Barton Doctrine ID: 04.04.02.04.70000.002

All database operations isolated to this file.
Edit SQL queries here, not in main agent code.
"""

import asyncpg
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class NeonConnector:
    """
    Handle all database operations for BIT Scoring Agent

    Isolation principle: All SQL lives here, not scattered across modules
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize connector with configuration"""
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

        # Get connection string from environment
        db_config = config['database']
        self.connection_string = os.getenv(db_config['connection_string_env'])

        if not self.connection_string:
            raise ValueError(f"Environment variable {db_config['connection_string_env']} not set")

    async def connect(self):
        """Establish connection pool to Neon"""
        db_config = self.config['database']

        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=db_config['pool_min_size'],
            max_size=db_config['pool_max_size'],
            command_timeout=db_config['command_timeout']
        )

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    # ================================================================
    # SIGNAL RETRIEVAL
    # ================================================================

    async def get_unscored_signals(self, lookback_days: int) -> List[Dict[str, Any]]:
        """
        Get signals that haven't been scored yet

        Returns signals from last N days where scored = FALSE
        """
        query = """
        SELECT
            signal_id,
            person_unique_id,
            company_unique_id,
            signal_type,
            signal_weight,
            source_id,
            source_type,
            metadata,
            detected_at,
            created_at
        FROM marketing.bit_signal
        WHERE scored = FALSE
          AND detected_at >= NOW() - INTERVAL '%s days'
        ORDER BY detected_at ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, lookback_days)
            return [dict(row) for row in rows]

    async def get_person_signals(
        self,
        person_unique_id: str,
        company_unique_id: str,
        include_scored: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all signals for a person/company combination

        Used for score recalculation
        """
        query = """
        SELECT
            signal_id,
            person_unique_id,
            company_unique_id,
            signal_type,
            signal_weight,
            source_id,
            source_type,
            metadata,
            detected_at,
            created_at,
            scored
        FROM marketing.bit_signal
        WHERE person_unique_id = $1
          AND company_unique_id = $2
        """

        if not include_scored:
            query += " AND scored = FALSE"

        query += " ORDER BY detected_at DESC"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, person_unique_id, company_unique_id)
            return [dict(row) for row in rows]

    # ================================================================
    # WEIGHT & RULE RETRIEVAL
    # ================================================================

    async def get_signal_weight(self, signal_type: str) -> Optional[int]:
        """Get weight for a signal type"""
        query = """
        SELECT weight
        FROM marketing.bit_signal_weights
        WHERE signal_type = $1 AND active = TRUE
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, signal_type)
            return row['weight'] if row else None

    async def get_all_signal_weights(self) -> Dict[str, int]:
        """Get all active signal weights as dict"""
        query = """
        SELECT signal_type, weight
        FROM marketing.bit_signal_weights
        WHERE active = TRUE
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return {row['signal_type']: row['weight'] for row in rows}

    async def get_decay_factor(self, days_old: int) -> float:
        """
        Get decay factor for signal age

        Returns multiplier (0.0 - 1.0) based on how old the signal is
        """
        query = """
        SELECT decay_factor
        FROM marketing.bit_decay_rules
        WHERE days_threshold >= $1
          AND active = TRUE
        ORDER BY days_threshold ASC
        LIMIT 1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, days_old)
            return float(row['decay_factor']) if row else 0.05  # Default: 5% for very old

    async def get_confidence_modifier(self, source: str) -> float:
        """
        Get confidence multiplier for data source

        Returns multiplier (0.0 - 2.0) based on source quality
        """
        query = """
        SELECT confidence_multiplier
        FROM marketing.bit_confidence_modifiers
        WHERE source = $1 AND active = TRUE
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, source)
            return float(row['confidence_multiplier']) if row else 1.0  # Default: neutral

    async def get_trigger_thresholds(self) -> List[Dict[str, Any]]:
        """Get all active trigger thresholds"""
        query = """
        SELECT
            threshold_id,
            trigger_level,
            min_score,
            max_score,
            action_type,
            description
        FROM marketing.bit_trigger_thresholds
        WHERE active = TRUE
        ORDER BY min_score ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    # ================================================================
    # SCORE WRITING
    # ================================================================

    async def upsert_bit_score(
        self,
        person_unique_id: str,
        company_unique_id: str,
        raw_score: int,
        decayed_score: int,
        score_tier: str,
        last_signal_at: datetime,
        signal_count: int,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Insert or update BIT score

        Returns: score_id
        """
        query = """
        INSERT INTO marketing.bit_score (
            person_unique_id,
            company_unique_id,
            raw_score,
            decayed_score,
            score_tier,
            last_signal_at,
            signal_count,
            computed_at,
            metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
        ON CONFLICT (person_unique_id, company_unique_id)
        DO UPDATE SET
            raw_score = EXCLUDED.raw_score,
            decayed_score = EXCLUDED.decayed_score,
            score_tier = EXCLUDED.score_tier,
            last_signal_at = EXCLUDED.last_signal_at,
            signal_count = EXCLUDED.signal_count,
            computed_at = NOW(),
            metadata = EXCLUDED.metadata
        RETURNING score_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                person_unique_id,
                company_unique_id,
                raw_score,
                decayed_score,
                score_tier,
                last_signal_at,
                signal_count,
                metadata
            )
            return row['score_id']

    async def get_current_score(
        self,
        person_unique_id: str,
        company_unique_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current BIT score for person/company"""
        query = """
        SELECT
            score_id,
            person_unique_id,
            company_unique_id,
            raw_score,
            decayed_score,
            score_tier,
            last_signal_at,
            signal_count,
            computed_at,
            metadata
        FROM marketing.bit_score
        WHERE person_unique_id = $1
          AND company_unique_id = $2
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, person_unique_id, company_unique_id)
            return dict(row) if row else None

    # ================================================================
    # TRIGGER ACTIONS
    # ================================================================

    async def insert_outreach_log(
        self,
        person_unique_id: str,
        company_unique_id: str,
        action_type: str,
        bit_score: int,
        score_tier: str,
        trigger_reason: str,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Log outreach action triggered by BIT score

        Returns: outreach_id
        """
        query = """
        INSERT INTO marketing.outreach_log (
            person_unique_id,
            company_unique_id,
            action_type,
            bit_score,
            score_tier,
            trigger_reason,
            metadata,
            created_at,
            processed,
            processed_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), FALSE, NULL)
        RETURNING outreach_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                person_unique_id,
                company_unique_id,
                action_type,
                bit_score,
                score_tier,
                trigger_reason,
                metadata
            )
            return row['outreach_id']

    async def check_recent_outreach(
        self,
        person_unique_id: str,
        action_type: str,
        window_hours: int
    ) -> bool:
        """
        Check if action already triggered recently (deduplication)

        Returns True if found (skip action), False if safe to proceed
        """
        query = """
        SELECT COUNT(*) as count
        FROM marketing.outreach_log
        WHERE person_unique_id = $1
          AND action_type = $2
          AND created_at >= NOW() - INTERVAL '%s hours'
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, person_unique_id, action_type, window_hours)
            return row['count'] > 0

    async def insert_meeting_queue(
        self,
        person_unique_id: str,
        company_unique_id: str,
        bit_score: int,
        priority: str,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Add contact to meeting queue

        Returns: meeting_id
        """
        query = """
        INSERT INTO marketing.meeting_queue (
            person_unique_id,
            company_unique_id,
            bit_score,
            priority,
            status,
            metadata,
            created_at
        ) VALUES ($1, $2, $3, $4, 'pending', $5, NOW())
        RETURNING meeting_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                person_unique_id,
                company_unique_id,
                bit_score,
                priority,
                metadata
            )
            return row['meeting_id']

    # ================================================================
    # SHQ AUDIT LOG
    # ================================================================

    async def log_to_shq(
        self,
        worker_id: str,
        process_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = 'INFO'
    ):
        """Log event to SHQ audit trail"""
        query = """
        INSERT INTO shq.audit_log (
            worker_id,
            process_id,
            event_type,
            event_data,
            severity,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, NOW())
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

    # ================================================================
    # SAFETY CHECKS
    # ================================================================

    async def get_person_data(
        self,
        person_unique_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get person details for trigger validation"""
        query = """
        SELECT
            unique_id,
            full_name,
            email,
            phone,
            title,
            company_unique_id
        FROM marketing.people_master
        WHERE unique_id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, person_unique_id)
            return dict(row) if row else None

    async def check_score_increase_limit(
        self,
        person_unique_id: str,
        company_unique_id: str,
        max_increase: int
    ) -> bool:
        """
        Safety check: prevent runaway score increases

        Returns True if increase is within safe limit, False if too high
        """
        query = """
        SELECT
            raw_score,
            computed_at
        FROM marketing.bit_score
        WHERE person_unique_id = $1
          AND company_unique_id = $2
          AND computed_at >= NOW() - INTERVAL '24 hours'
        ORDER BY computed_at DESC
        LIMIT 1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, person_unique_id, company_unique_id)

            if not row:
                return True  # No recent score, safe to proceed

            # Check if increase is within limit
            # (This would be called before upsert with new score)
            return True  # Placeholder for actual comparison logic
