"""
Neon Database Connector for Backfill Agent
Barton Doctrine ID: 04.04.02.04.80000.006

All database operations isolated to this file.
Edit SQL queries here, not in main agent code.
"""

import asyncpg
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class NeonConnector:
    """
    Handle all database operations for Backfill Agent

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
    # COMPANY OPERATIONS
    # ================================================================

    async def get_all_companies(self) -> List[Dict[str, Any]]:
        """Get all companies from company_master"""
        query = """
        SELECT
            company_unique_id,
            company_name,
            company_domain,
            company_website,
            industry,
            employee_count,
            locked_fields,
            manual_overrides,
            created_at,
            updated_at
        FROM marketing.company_master
        ORDER BY company_name ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def insert_company(self, company_data: Dict[str, Any]) -> str:
        """
        Insert new company to company_master

        Returns: company_unique_id
        """
        query = """
        INSERT INTO marketing.company_master (
            company_name,
            company_domain,
            company_website,
            industry,
            employee_count,
            created_at,
            updated_at
        ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        RETURNING company_unique_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                company_data.get('company_name'),
                company_data.get('company_domain'),
                company_data.get('company_website'),
                company_data.get('industry'),
                company_data.get('employee_count', 0)
            )
            return row['company_unique_id']

    async def update_company(
        self,
        company_unique_id: str,
        updates: Dict[str, Any],
        updated_fields: List[str]
    ):
        """Update existing company (respecting locked fields)"""
        if not updates or not updated_fields:
            return

        # Build SET clause dynamically
        set_parts = []
        values = []
        param_num = 2  # Start at 2 ($1 is company_unique_id)

        for field in updated_fields:
            if field in updates:
                set_parts.append(f"{field} = ${param_num}")
                values.append(updates[field])
                param_num += 1

        if not set_parts:
            return

        # Add updated_at
        set_parts.append("updated_at = NOW()")

        query = f"""
        UPDATE marketing.company_master
        SET {', '.join(set_parts)}
        WHERE company_unique_id = $1
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, company_unique_id, *values)

    # ================================================================
    # PEOPLE OPERATIONS
    # ================================================================

    async def get_people_by_company(self, company_unique_id: str) -> List[Dict[str, Any]]:
        """Get all people for a specific company"""
        query = """
        SELECT
            unique_id,
            full_name,
            first_name,
            last_name,
            title,
            email,
            phone,
            linkedin_url,
            company_unique_id,
            locked_fields,
            manual_overrides,
            manually_corrected_email,
            manually_corrected_title,
            manually_corrected_domain,
            notes_internal,
            created_at,
            updated_at
        FROM marketing.people_master
        WHERE company_unique_id = $1
        ORDER BY full_name ASC
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, company_unique_id)
            return [dict(row) for row in rows]

    async def insert_person(self, person_data: Dict[str, Any]) -> str:
        """
        Insert new person to people_master

        Returns: unique_id (person_unique_id)
        """
        query = """
        INSERT INTO marketing.people_master (
            full_name,
            first_name,
            last_name,
            title,
            email,
            phone,
            linkedin_url,
            company_unique_id,
            created_at,
            updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
        RETURNING unique_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                person_data.get('full_name'),
                person_data.get('first_name'),
                person_data.get('last_name'),
                person_data.get('title'),
                person_data.get('email'),
                person_data.get('phone'),
                person_data.get('linkedin_url'),
                person_data.get('company_unique_id')
            )
            return row['unique_id']

    async def update_person(
        self,
        person_unique_id: str,
        updates: Dict[str, Any],
        updated_fields: List[str]
    ):
        """Update existing person (respecting locked fields)"""
        if not updates or not updated_fields:
            return

        # Build SET clause dynamically
        set_parts = []
        values = []
        param_num = 2  # Start at 2 ($1 is unique_id)

        for field in updated_fields:
            if field in updates:
                set_parts.append(f"{field} = ${param_num}")
                values.append(updates[field])
                param_num += 1

        if not set_parts:
            return

        # Add updated_at
        set_parts.append("updated_at = NOW()")

        query = f"""
        UPDATE marketing.people_master
        SET {', '.join(set_parts)}
        WHERE unique_id = $1
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, person_unique_id, *values)

    # ================================================================
    # BIT BASELINE OPERATIONS
    # ================================================================

    async def insert_bit_baseline(self, baseline_data: Dict[str, Any]) -> int:
        """
        Insert BIT baseline snapshot

        Returns: baseline_id
        """
        query = """
        INSERT INTO marketing.bit_baseline_snapshot (
            person_unique_id,
            company_unique_id,
            historical_open_count,
            historical_reply_count,
            historical_meeting_count,
            last_engaged_at,
            baseline_score,
            baseline_tier,
            signals_generated,
            source,
            metadata,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        ON CONFLICT (person_unique_id, company_unique_id) DO NOTHING
        RETURNING baseline_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                baseline_data['person_unique_id'],
                baseline_data['company_unique_id'],
                baseline_data['historical_open_count'],
                baseline_data['historical_reply_count'],
                baseline_data['historical_meeting_count'],
                baseline_data.get('last_engaged_at'),
                baseline_data['baseline_score'],
                baseline_data['baseline_tier'],
                baseline_data['signals_generated'],
                'backfill_agent',
                baseline_data.get('metadata', {})
            )
            return row['baseline_id'] if row else None

    async def insert_bit_signal_from_baseline(
        self,
        person_unique_id: str,
        company_unique_id: str,
        signal: Dict[str, Any]
    ) -> int:
        """
        Insert BIT signal from baseline generation

        Returns: signal_id
        """
        query = """
        INSERT INTO marketing.bit_signal (
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
        ) VALUES ($1, $2, $3, $4, NULL, $5, $6, NOW(), NOW(), FALSE)
        RETURNING signal_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                person_unique_id,
                company_unique_id,
                signal['signal_type'],
                signal['signal_weight'],
                signal['source_type'],
                signal.get('metadata', {})
            )
            return row['signal_id']

    # ================================================================
    # TALENT FLOW BASELINE OPERATIONS
    # ================================================================

    async def insert_talent_flow_baseline(self, baseline_data: Dict[str, Any]) -> int:
        """
        Insert Talent Flow baseline snapshot

        Returns: baseline_id
        """
        query = """
        INSERT INTO marketing.talent_flow_baseline (
            person_unique_id,
            enrichment_hash,
            snapshot_data,
            baseline_date,
            source,
            metadata,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
        ON CONFLICT (person_unique_id) DO NOTHING
        RETURNING baseline_id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                baseline_data['person_unique_id'],
                baseline_data['enrichment_hash'],
                baseline_data['snapshot_data'],
                baseline_data['baseline_date'],
                'backfill_agent',
                baseline_data.get('metadata', {})
            )
            return row['baseline_id'] if row else None

    # ================================================================
    # BACKFILL LOG OPERATIONS
    # ================================================================

    async def log_backfill_operation(
        self,
        log_data: Dict[str, Any],
        worker_id: str,
        process_id: str
    ):
        """Log backfill operation to backfill_log"""
        query = """
        INSERT INTO marketing.backfill_log (
            source_row_hash,
            source_data,
            match_type,
            match_confidence,
            matched_company_id,
            matched_person_id,
            resolution_status,
            actions_taken,
            error_message,
            notes,
            worker_id,
            process_id,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                log_data['source_row_hash'],
                log_data['source_data'],
                log_data.get('match_type'),
                log_data.get('match_confidence'),
                log_data.get('matched_company_id'),
                log_data.get('matched_person_id'),
                log_data['resolution_status'],
                log_data.get('actions_taken', {}),
                log_data.get('error_message'),
                log_data.get('notes'),
                worker_id,
                process_id
            )

    # ================================================================
    # GARAGE MISSING PARTS OPERATIONS
    # ================================================================

    async def insert_missing_part(
        self,
        source_data: Dict[str, Any],
        issue_type: str,
        match_attempts: Dict[str, Any],
        confidence_score: float
    ):
        """Insert unresolved match to garage.missing_parts"""
        query = """
        INSERT INTO garage.missing_parts (
            source,
            issue_type,
            source_data,
            match_attempts,
            confidence_score,
            resolved,
            created_at
        ) VALUES ($1, $2, $3, $4, $5, FALSE, NOW())
        """

        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                'backfill_agent',
                issue_type,
                source_data,
                match_attempts,
                confidence_score
            )

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
