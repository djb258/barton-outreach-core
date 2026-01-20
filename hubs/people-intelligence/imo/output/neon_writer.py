"""
Neon Database Writer
====================
Writes People Pipeline results to Neon PostgreSQL.

Per Doctrine:
- All database writes require correlation_id
- Company anchor (company_id) required for all records
- Batch writes with transaction support
- Error handling with retry logic

Target Tables:
- marketing.people_master: Person records
- marketing.company_slot: Slot assignments
- marketing.data_enrichment_log: Enrichment tracking
"""

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# Doctrine enforcement
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError


logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class NeonConfig:
    """Neon database connection configuration."""
    host: str = ""
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""
    ssl_mode: str = "require"

    @classmethod
    def from_env(cls) -> 'NeonConfig':
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("NEON_HOST", ""),
            port=int(os.getenv("NEON_PORT", "5432")),
            database=os.getenv("NEON_DATABASE", ""),
            user=os.getenv("NEON_USER", ""),
            password=os.getenv("NEON_PASSWORD", ""),
            ssl_mode=os.getenv("NEON_SSL_MODE", "require"),
        )

    @property
    def connection_string(self) -> str:
        """Build connection string."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.host and self.database and self.user and self.password)


# =============================================================================
# WRITE RESULTS
# =============================================================================

@dataclass
class WriteResult:
    """Result of a database write operation."""
    success: bool
    table_name: str
    records_written: int = 0
    records_failed: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class NeonWriterStats:
    """Statistics for Neon writer."""
    total_writes: int = 0
    successful_writes: int = 0
    failed_writes: int = 0
    people_inserted: int = 0
    people_updated: int = 0
    slots_assigned: int = 0
    enrichment_logged: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""


# =============================================================================
# NEON DATABASE WRITER
# =============================================================================

class NeonDatabaseWriter:
    """
    Writes People Pipeline results to Neon PostgreSQL.

    Handles:
    - Bulk inserts with COPY for performance
    - Upserts for existing records
    - Transaction management
    - Error handling and rollback
    """

    def __init__(self, config: NeonConfig = None):
        """
        Initialize Neon database writer.

        Args:
            config: Neon configuration (loads from env if not provided)
        """
        self.config = config or NeonConfig.from_env()
        self._conn = None
        self._psycopg2 = None

    def _get_connection(self):
        """Get database connection (lazy load)."""
        if self._conn is None or self._conn.closed:
            if self._psycopg2 is None:
                try:
                    import psycopg2
                    import psycopg2.extras
                    self._psycopg2 = psycopg2
                except ImportError:
                    raise ImportError("psycopg2 not installed: pip install psycopg2-binary")

            self._conn = self._psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                sslmode=self.config.ssl_mode
            )
        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def write_people(
        self,
        people_df,
        correlation_id: str,
        mode: str = "upsert"
    ) -> WriteResult:
        """
        Write people records to marketing.people_master.

        Args:
            people_df: DataFrame with people records
            correlation_id: MANDATORY - Pipeline trace ID
            mode: "insert", "upsert", or "update"

        Returns:
            WriteResult with statistics
        """
        # Validate correlation_id
        process_id = "people.neon.write_people"
        correlation_id = validate_correlation_id(correlation_id, process_id, "NeonWriter")

        start_time = time.time()
        result = WriteResult(success=True, table_name="marketing.people_master")

        if people_df is None or len(people_df) == 0:
            return result

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            for idx, row in people_df.iterrows():
                try:
                    # Extract fields - preserve original data_source if provided
                    raw_data_source = row.get('data_source', '') or row.get('source', '')
                    person_data = {
                        'person_unique_id': str(row.get('person_id', '')),
                        'full_name': row.get('full_name', '') or f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'title': row.get('job_title', '') or row.get('title', ''),
                        'email': row.get('generated_email', '') or row.get('email', ''),
                        'linkedin_url': row.get('linkedin_url', ''),
                        'company_unique_id': row.get('company_id', '') or row.get('matched_company_id', ''),
                        'seniority': row.get('seniority', ''),
                        'seniority_rank': int(row.get('seniority_rank', 0) or 0),
                        'email_confidence': row.get('email_confidence', ''),
                        'pattern_used': row.get('pattern_used', ''),
                        'slot_type': row.get('slot_type', ''),
                        'data_source': raw_data_source if raw_data_source else 'people_pipeline',
                        'correlation_id': correlation_id,
                    }

                    # Skip if no person_id
                    if not person_data['person_unique_id']:
                        continue

                    if mode == "upsert":
                        cursor.execute("""
                            INSERT INTO marketing.people_master (
                                person_unique_id, full_name, first_name, last_name,
                                title, email, linkedin_url, company_unique_id,
                                seniority, seniority_rank, email_confidence,
                                pattern_used, slot_type, data_source, created_at, updated_at
                            ) VALUES (
                                %(person_unique_id)s, %(full_name)s, %(first_name)s, %(last_name)s,
                                %(title)s, %(email)s, %(linkedin_url)s, %(company_unique_id)s,
                                %(seniority)s, %(seniority_rank)s, %(email_confidence)s,
                                %(pattern_used)s, %(slot_type)s, %(data_source)s, NOW(), NOW()
                            )
                            ON CONFLICT (person_unique_id) DO UPDATE SET
                                full_name = EXCLUDED.full_name,
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name,
                                title = EXCLUDED.title,
                                email = EXCLUDED.email,
                                linkedin_url = COALESCE(EXCLUDED.linkedin_url, marketing.people_master.linkedin_url),
                                company_unique_id = EXCLUDED.company_unique_id,
                                seniority = EXCLUDED.seniority,
                                seniority_rank = EXCLUDED.seniority_rank,
                                email_confidence = EXCLUDED.email_confidence,
                                pattern_used = EXCLUDED.pattern_used,
                                slot_type = EXCLUDED.slot_type,
                                updated_at = NOW()
                        """, person_data)
                    elif mode == "insert":
                        cursor.execute("""
                            INSERT INTO marketing.people_master (
                                person_unique_id, full_name, first_name, last_name,
                                title, email, linkedin_url, company_unique_id,
                                seniority, seniority_rank, email_confidence,
                                pattern_used, slot_type, data_source, created_at, updated_at
                            ) VALUES (
                                %(person_unique_id)s, %(full_name)s, %(first_name)s, %(last_name)s,
                                %(title)s, %(email)s, %(linkedin_url)s, %(company_unique_id)s,
                                %(seniority)s, %(seniority_rank)s, %(email_confidence)s,
                                %(pattern_used)s, %(slot_type)s, %(data_source)s, NOW(), NOW()
                            )
                            ON CONFLICT (person_unique_id) DO NOTHING
                        """, person_data)

                    result.records_written += 1

                except Exception as e:
                    result.records_failed += 1
                    result.errors.append(f"Row {idx}: {str(e)}")

            conn.commit()
            cursor.close()

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Failed to write people: {e}")

        result.duration_seconds = time.time() - start_time
        return result

    def write_slot_assignments(
        self,
        slot_df,
        correlation_id: str
    ) -> WriteResult:
        """
        Write slot assignments to marketing.company_slot.

        Args:
            slot_df: DataFrame with slot assignments
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with statistics
        """
        process_id = "people.neon.write_slots"
        correlation_id = validate_correlation_id(correlation_id, process_id, "NeonWriter")

        start_time = time.time()
        result = WriteResult(success=True, table_name="marketing.company_slot")

        if slot_df is None or len(slot_df) == 0:
            return result

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            for idx, row in slot_df.iterrows():
                try:
                    # Extract data_source for history tracking
                    raw_data_source = row.get('data_source', '') or row.get('source', '')
                    slot_data = {
                        'company_unique_id': row.get('company_id', ''),
                        'person_unique_id': row.get('person_id', ''),
                        'slot_type': row.get('slot_type', ''),
                        'slot_reason': row.get('slot_reason', ''),
                        'seniority_score': float(row.get('seniority_score', 0) or 0),
                        'data_source': raw_data_source if raw_data_source else 'people_pipeline',
                    }

                    if not slot_data['company_unique_id'] or not slot_data['person_unique_id']:
                        continue

                    # Note: Uses people.company_slot (not marketing.company_slot)
                    # The trg_slot_assignment_history trigger will capture history on person changes
                    cursor.execute("""
                        INSERT INTO people.company_slot (
                            company_slot_unique_id, company_unique_id, person_unique_id, slot_type,
                            source_system, is_filled, filled_at, confidence_score, created_at, slot_status
                        ) VALUES (
                            gen_random_uuid()::text, %(company_unique_id)s, %(person_unique_id)s, %(slot_type)s,
                            %(data_source)s, TRUE, NOW(), %(seniority_score)s, NOW(), 'filled'
                        )
                        ON CONFLICT (company_unique_id, slot_type) DO UPDATE SET
                            person_unique_id = EXCLUDED.person_unique_id,
                            source_system = EXCLUDED.source_system,
                            confidence_score = EXCLUDED.confidence_score,
                            is_filled = TRUE,
                            filled_at = NOW(),
                            slot_status = 'filled'
                    """, slot_data)

                    result.records_written += 1

                except Exception as e:
                    result.records_failed += 1
                    result.errors.append(f"Row {idx}: {str(e)}")

            conn.commit()
            cursor.close()

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Failed to write slots: {e}")

        result.duration_seconds = time.time() - start_time
        return result

    def write_enrichment_queue(
        self,
        queue_df,
        correlation_id: str
    ) -> WriteResult:
        """
        Write enrichment queue items to marketing.data_enrichment_log.

        Args:
            queue_df: DataFrame with enrichment queue items
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with statistics
        """
        process_id = "people.neon.write_enrichment"
        correlation_id = validate_correlation_id(correlation_id, process_id, "NeonWriter")

        start_time = time.time()
        result = WriteResult(success=True, table_name="marketing.data_enrichment_log")

        if queue_df is None or len(queue_df) == 0:
            return result

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            for idx, row in queue_df.iterrows():
                try:
                    enrichment_data = {
                        'company_unique_id': row.get('company_id', ''),
                        'person_unique_id': row.get('person_id', ''),
                        'enrichment_type': row.get('reason', 'pipeline_queue'),
                        'priority': row.get('priority', 'medium'),
                        'status': 'pending',
                        'correlation_id': correlation_id,
                    }

                    if not enrichment_data['company_unique_id']:
                        continue

                    cursor.execute("""
                        INSERT INTO marketing.data_enrichment_log (
                            company_unique_id, person_unique_id, enrichment_type,
                            priority, status, correlation_id, created_at
                        ) VALUES (
                            %(company_unique_id)s, %(person_unique_id)s, %(enrichment_type)s,
                            %(priority)s, %(status)s, %(correlation_id)s, NOW()
                        )
                    """, enrichment_data)

                    result.records_written += 1

                except Exception as e:
                    result.records_failed += 1
                    result.errors.append(f"Row {idx}: {str(e)}")

            conn.commit()
            cursor.close()

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"Failed to write enrichment queue: {e}")

        result.duration_seconds = time.time() - start_time
        return result

    def run_pipeline_output(
        self,
        people_df,
        slotted_df,
        enrichment_queue_df,
        correlation_id: str
    ) -> Tuple[NeonWriterStats, List[WriteResult]]:
        """
        Write all pipeline output to database.

        Args:
            people_df: People with emails and slots
            slotted_df: Slot assignments
            enrichment_queue_df: Enrichment queue
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            Tuple of (NeonWriterStats, List of WriteResults)
        """
        start_time = time.time()
        stats = NeonWriterStats(correlation_id=correlation_id)
        results = []

        # Write people
        people_result = self.write_people(people_df, correlation_id)
        results.append(people_result)
        stats.people_inserted += people_result.records_written
        stats.total_writes += 1
        if people_result.success:
            stats.successful_writes += 1
        else:
            stats.failed_writes += 1

        # Write slots
        slot_result = self.write_slot_assignments(slotted_df, correlation_id)
        results.append(slot_result)
        stats.slots_assigned += slot_result.records_written
        stats.total_writes += 1
        if slot_result.success:
            stats.successful_writes += 1
        else:
            stats.failed_writes += 1

        # Write enrichment queue
        queue_result = self.write_enrichment_queue(enrichment_queue_df, correlation_id)
        results.append(queue_result)
        stats.enrichment_logged += queue_result.records_written
        stats.total_writes += 1
        if queue_result.success:
            stats.successful_writes += 1
        else:
            stats.failed_writes += 1

        stats.duration_seconds = time.time() - start_time

        logger.info(
            f"Neon write complete: {stats.people_inserted} people, "
            f"{stats.slots_assigned} slots, {stats.enrichment_logged} queue items "
            f"({stats.duration_seconds:.2f}s)"
        )

        return stats, results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def write_to_neon(
    people_df,
    slotted_df,
    enrichment_queue_df,
    correlation_id: str,
    config: Dict[str, Any] = None
) -> Tuple[NeonWriterStats, List[WriteResult]]:
    """
    Convenience function to write pipeline output to Neon.

    Args:
        people_df: People with emails and slots
        slotted_df: Slot assignments
        enrichment_queue_df: Enrichment queue
        correlation_id: MANDATORY - Pipeline trace ID
        config: Optional configuration overrides

    Returns:
        Tuple of (NeonWriterStats, List of WriteResults)
    """
    neon_config = NeonConfig.from_env()
    if config:
        for key, value in config.items():
            if hasattr(neon_config, key):
                setattr(neon_config, key, value)

    writer = NeonDatabaseWriter(config=neon_config)
    try:
        return writer.run_pipeline_output(
            people_df, slotted_df, enrichment_queue_df, correlation_id
        )
    finally:
        writer.close()


def check_neon_connection() -> bool:
    """Check if Neon database is reachable."""
    config = NeonConfig.from_env()
    if not config.is_valid():
        logger.warning("Neon configuration incomplete")
        return False

    try:
        writer = NeonDatabaseWriter(config=config)
        conn = writer._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        writer.close()
        return True
    except Exception as e:
        logger.error(f"Neon connection failed: {e}")
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "NeonConfig",
    # Writer
    "NeonDatabaseWriter",
    "WriteResult",
    "NeonWriterStats",
    # Convenience
    "write_to_neon",
    "check_neon_connection",
]
