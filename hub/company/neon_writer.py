"""
Company Hub Neon Writer
=======================
Reads and writes Company Hub data to Neon PostgreSQL.

Per Doctrine:
- Company Hub is the MASTER NODE - all spokes anchor here
- All database operations require correlation_id
- The Golden Rule: company_id + domain + email_pattern required for spoke readiness

Target Tables:
- marketing.company_master: Company records (the central axle)
- funnel.bit_signal_log: BIT Engine signals
- funnel.suspect_universe: Companies in funnel

Barton ID Format: 04.04.01.XX.XXXXX.XXX
"""

import os
import time
import logging
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

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
        # URL-encode the database name if it has spaces
        db_encoded = self.database.replace(" ", "%20")
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{db_encoded}?sslmode={self.ssl_mode}"
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
    records_updated: int = 0
    records_failed: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class CompanyWriterStats:
    """Statistics for Company Neon writer."""
    total_writes: int = 0
    successful_writes: int = 0
    failed_writes: int = 0
    companies_inserted: int = 0
    companies_updated: int = 0
    signals_logged: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""


# =============================================================================
# COMPANY NEON WRITER
# =============================================================================

class CompanyNeonWriter:
    """
    Writes Company Hub data to Neon PostgreSQL.

    This is the foundation - all spokes depend on companies existing here.
    """

    # SQL for company operations
    UPSERT_COMPANY_SQL = """
        INSERT INTO marketing.company_master (
            company_unique_id,
            company_name,
            domain,
            email_pattern,
            ein,
            industry,
            employee_count,
            address_state,
            bit_score,
            data_quality_score,
            created_at,
            updated_at
        ) VALUES (
            %(company_unique_id)s,
            %(company_name)s,
            %(domain)s,
            %(email_pattern)s,
            %(ein)s,
            %(industry)s,
            %(employee_count)s,
            %(address_state)s,
            %(bit_score)s,
            %(data_quality_score)s,
            %(created_at)s,
            %(updated_at)s
        )
        ON CONFLICT (company_unique_id) DO UPDATE SET
            company_name = EXCLUDED.company_name,
            domain = COALESCE(EXCLUDED.domain, marketing.company_master.domain),
            email_pattern = COALESCE(EXCLUDED.email_pattern, marketing.company_master.email_pattern),
            ein = COALESCE(EXCLUDED.ein, marketing.company_master.ein),
            industry = COALESCE(EXCLUDED.industry, marketing.company_master.industry),
            employee_count = COALESCE(EXCLUDED.employee_count, marketing.company_master.employee_count),
            address_state = COALESCE(EXCLUDED.address_state, marketing.company_master.address_state),
            bit_score = EXCLUDED.bit_score,
            data_quality_score = EXCLUDED.data_quality_score,
            updated_at = EXCLUDED.updated_at
    """

    UPDATE_DOMAIN_SQL = """
        UPDATE marketing.company_master
        SET domain = %(domain)s,
            updated_at = %(updated_at)s
        WHERE company_unique_id = %(company_unique_id)s
    """

    UPDATE_PATTERN_SQL = """
        UPDATE marketing.company_master
        SET email_pattern = %(email_pattern)s,
            updated_at = %(updated_at)s
        WHERE company_unique_id = %(company_unique_id)s
    """

    UPDATE_BIT_SCORE_SQL = """
        UPDATE marketing.company_master
        SET bit_score = %(bit_score)s,
            updated_at = %(updated_at)s
        WHERE company_unique_id = %(company_unique_id)s
    """

    INSERT_BIT_SIGNAL_SQL = """
        INSERT INTO funnel.bit_signal_log (
            signal_id,
            company_unique_id,
            signal_type,
            signal_impact,
            source_spoke,
            correlation_id,
            signal_hash,
            created_at
        ) VALUES (
            %(signal_id)s,
            %(company_unique_id)s,
            %(signal_type)s,
            %(signal_impact)s,
            %(source_spoke)s,
            %(correlation_id)s,
            %(signal_hash)s,
            %(created_at)s
        )
        ON CONFLICT (signal_hash) DO NOTHING
    """

    LOAD_COMPANIES_SQL = """
        SELECT
            company_unique_id,
            company_name,
            domain,
            email_pattern,
            ein,
            industry,
            employee_count,
            address_state,
            bit_score,
            data_quality_score,
            created_at,
            updated_at
        FROM marketing.company_master
        ORDER BY company_unique_id
    """

    LOAD_COMPANY_BY_ID_SQL = """
        SELECT
            company_unique_id,
            company_name,
            domain,
            email_pattern,
            ein,
            industry,
            employee_count,
            address_state,
            bit_score,
            data_quality_score,
            created_at,
            updated_at
        FROM marketing.company_master
        WHERE company_unique_id = %(company_unique_id)s
    """

    FIND_COMPANY_BY_DOMAIN_SQL = """
        SELECT company_unique_id, company_name, domain, email_pattern
        FROM marketing.company_master
        WHERE domain = %(domain)s
        LIMIT 1
    """

    FIND_COMPANY_BY_EIN_SQL = """
        SELECT company_unique_id, company_name, domain, email_pattern, ein
        FROM marketing.company_master
        WHERE ein = %(ein)s
        LIMIT 1
    """

    FIND_COMPANY_BY_NAME_SQL = """
        SELECT company_unique_id, company_name, domain, email_pattern
        FROM marketing.company_master
        WHERE LOWER(company_name) = LOWER(%(company_name)s)
        LIMIT 10
    """

    def __init__(self, config: NeonConfig = None):
        """Initialize with Neon configuration."""
        self.config = config or NeonConfig.from_env()
        self._connection = None

    def _get_connection(self):
        """Get database connection (lazy initialization)."""
        if self._connection is None or self._connection.closed:
            try:
                import psycopg2
                self._connection = psycopg2.connect(self.config.connection_string)
                self._connection.autocommit = False
            except ImportError:
                logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Neon: {e}")
                raise
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    # -------------------------------------------------------------------------
    # WRITE OPERATIONS
    # -------------------------------------------------------------------------

    def write_company(
        self,
        company_data: Dict[str, Any],
        correlation_id: str
    ) -> WriteResult:
        """
        Upsert a single company to Neon.

        Args:
            company_data: Company record dictionary
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with operation status
        """
        # Doctrine: correlation_id is MANDATORY
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_master")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Prepare data with timestamps
                now = datetime.now()
                params = {
                    'company_unique_id': company_data.get('company_unique_id'),
                    'company_name': company_data.get('company_name'),
                    'domain': company_data.get('domain'),
                    'email_pattern': company_data.get('email_pattern'),
                    'ein': company_data.get('ein'),
                    'industry': company_data.get('industry'),
                    'employee_count': company_data.get('employee_count'),
                    'address_state': company_data.get('address_state'),
                    'bit_score': company_data.get('bit_score', 0.0),
                    'data_quality_score': company_data.get('data_quality_score', 0.0),
                    'created_at': company_data.get('created_at', now),
                    'updated_at': now,
                }

                cursor.execute(self.UPSERT_COMPANY_SQL, params)

                # Check if insert or update
                if cursor.rowcount > 0:
                    result.records_written = 1

                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to write company: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def write_companies_batch(
        self,
        companies: List[Dict[str, Any]],
        correlation_id: str
    ) -> WriteResult:
        """
        Batch upsert multiple companies to Neon.

        Args:
            companies: List of company dictionaries
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with batch operation status
        """
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_master")

        if not companies:
            result.success = True
            return result

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                for company in companies:
                    try:
                        params = {
                            'company_unique_id': company.get('company_unique_id'),
                            'company_name': company.get('company_name'),
                            'domain': company.get('domain'),
                            'email_pattern': company.get('email_pattern'),
                            'ein': company.get('ein'),
                            'industry': company.get('industry'),
                            'employee_count': company.get('employee_count'),
                            'address_state': company.get('address_state'),
                            'bit_score': company.get('bit_score', 0.0),
                            'data_quality_score': company.get('data_quality_score', 0.0),
                            'created_at': company.get('created_at', now),
                            'updated_at': now,
                        }
                        cursor.execute(self.UPSERT_COMPANY_SQL, params)
                        result.records_written += 1
                    except Exception as e:
                        logger.warning(f"Failed to write company {company.get('company_unique_id')}: {e}")
                        result.records_failed += 1
                        result.errors.append(str(e))

                conn.commit()
                result.success = result.records_failed == 0

        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def update_domain(
        self,
        company_id: str,
        domain: str,
        correlation_id: str
    ) -> WriteResult:
        """Update company domain (Phase 2 output)."""
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_master")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.UPDATE_DOMAIN_SQL, {
                    'company_unique_id': company_id,
                    'domain': domain,
                    'updated_at': datetime.now()
                })
                result.records_updated = cursor.rowcount
                conn.commit()
                result.success = True
        except Exception as e:
            logger.error(f"Failed to update domain: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def update_email_pattern(
        self,
        company_id: str,
        email_pattern: str,
        correlation_id: str
    ) -> WriteResult:
        """Update company email pattern (Phase 3 output)."""
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_master")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.UPDATE_PATTERN_SQL, {
                    'company_unique_id': company_id,
                    'email_pattern': email_pattern,
                    'updated_at': datetime.now()
                })
                result.records_updated = cursor.rowcount
                conn.commit()
                result.success = True
        except Exception as e:
            logger.error(f"Failed to update email pattern: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def update_bit_score(
        self,
        company_id: str,
        bit_score: float,
        correlation_id: str
    ) -> WriteResult:
        """Update company BIT score."""
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_master")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.UPDATE_BIT_SCORE_SQL, {
                    'company_unique_id': company_id,
                    'bit_score': bit_score,
                    'updated_at': datetime.now()
                })
                result.records_updated = cursor.rowcount
                conn.commit()
                result.success = True
        except Exception as e:
            logger.error(f"Failed to update BIT score: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def log_bit_signal(
        self,
        company_id: str,
        signal_type: str,
        signal_impact: float,
        source_spoke: str,
        correlation_id: str
    ) -> WriteResult:
        """
        Log a BIT signal to funnel.bit_signal_log.

        Uses signal_hash for deduplication (Tool 10).
        """
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="funnel.bit_signal_log")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                # Generate signal hash for deduplication (24h window)
                window_date = now.strftime("%Y-%m-%d")
                hash_input = f"{signal_type}:{company_id}:{window_date}"
                signal_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]

                # Generate signal ID
                import uuid
                signal_id = f"04.04.01.BIT.{uuid.uuid4().hex[:8].upper()}"

                cursor.execute(self.INSERT_BIT_SIGNAL_SQL, {
                    'signal_id': signal_id,
                    'company_unique_id': company_id,
                    'signal_type': signal_type,
                    'signal_impact': signal_impact,
                    'source_spoke': source_spoke,
                    'correlation_id': correlation_id,
                    'signal_hash': signal_hash,
                    'created_at': now
                })

                # ON CONFLICT DO NOTHING means rowcount=0 if duplicate
                result.records_written = cursor.rowcount
                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to log BIT signal: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    # -------------------------------------------------------------------------
    # READ OPERATIONS (Bootstrap & Lookup)
    # -------------------------------------------------------------------------

    def load_all_companies(self) -> List[Dict[str, Any]]:
        """
        Load all companies from Neon for hub bootstrap.

        Returns:
            List of company dictionaries
        """
        companies = []

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_COMPANIES_SQL)
                columns = [desc[0] for desc in cursor.description]

                for row in cursor.fetchall():
                    companies.append(dict(zip(columns, row)))

                logger.info(f"Loaded {len(companies)} companies from Neon")

        except Exception as e:
            logger.error(f"Failed to load companies: {e}")

        return companies

    def load_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Load a single company by ID."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_COMPANY_BY_ID_SQL, {
                    'company_unique_id': company_id
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to load company {company_id}: {e}")
        return None

    def find_company_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Find company by domain (Tool 1: GOLD match)."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.FIND_COMPANY_BY_DOMAIN_SQL, {
                    'domain': domain.lower()
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to find company by domain: {e}")
        return None

    def find_company_by_ein(self, ein: str) -> Optional[Dict[str, Any]]:
        """Find company by EIN (Tool 18: Exact EIN match)."""
        # Normalize EIN (remove hyphens, spaces)
        normalized_ein = ''.join(c for c in ein if c.isdigit())

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.FIND_COMPANY_BY_EIN_SQL, {
                    'ein': normalized_ein
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to find company by EIN: {e}")
        return None

    def find_companies_by_name(self, company_name: str) -> List[Dict[str, Any]]:
        """Find companies by name (for fuzzy matching candidates)."""
        companies = []
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.FIND_COMPANY_BY_NAME_SQL, {
                    'company_name': company_name
                })
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    companies.append(dict(zip(columns, row)))
        except Exception as e:
            logger.error(f"Failed to find companies by name: {e}")
        return companies

    # -------------------------------------------------------------------------
    # SLOT OPERATIONS (marketing.company_slot)
    # -------------------------------------------------------------------------

    UPSERT_SLOT_SQL = """
        INSERT INTO marketing.company_slot (
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            person_unique_id,
            is_filled,
            filled_at,
            last_refreshed_at,
            created_at,
            updated_at
        ) VALUES (
            %(company_slot_unique_id)s,
            %(company_unique_id)s,
            %(slot_type)s,
            %(person_unique_id)s,
            %(is_filled)s,
            %(filled_at)s,
            %(last_refreshed_at)s,
            %(created_at)s,
            %(updated_at)s
        )
        ON CONFLICT (company_unique_id, slot_type) DO UPDATE SET
            person_unique_id = EXCLUDED.person_unique_id,
            is_filled = EXCLUDED.is_filled,
            filled_at = CASE WHEN EXCLUDED.is_filled THEN EXCLUDED.filled_at ELSE NULL END,
            last_refreshed_at = EXCLUDED.last_refreshed_at,
            updated_at = EXCLUDED.updated_at
    """

    LOAD_SLOTS_BY_COMPANY_SQL = """
        SELECT
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            person_unique_id,
            is_filled,
            filled_at,
            last_refreshed_at,
            created_at,
            updated_at
        FROM marketing.company_slot
        WHERE company_unique_id = %(company_unique_id)s
    """

    LOAD_ALL_SLOTS_SQL = """
        SELECT
            company_slot_unique_id,
            company_unique_id,
            slot_type,
            person_unique_id,
            is_filled,
            filled_at,
            last_refreshed_at,
            created_at,
            updated_at
        FROM marketing.company_slot
        ORDER BY company_unique_id, slot_type
    """

    def write_slot(
        self,
        slot_data: Dict[str, Any],
        correlation_id: str
    ) -> WriteResult:
        """
        Upsert a company slot to Neon.

        Args:
            slot_data: Slot record dictionary with:
                - company_slot_unique_id: Barton ID for slot
                - company_unique_id: Parent company ID
                - slot_type: CEO, CFO, HR
                - person_unique_id: Person filling slot (or None)
                - is_filled: Boolean
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with operation status
        """
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_slot")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()
                is_filled = slot_data.get('is_filled', False)

                params = {
                    'company_slot_unique_id': slot_data.get('company_slot_unique_id'),
                    'company_unique_id': slot_data.get('company_unique_id'),
                    'slot_type': slot_data.get('slot_type'),
                    'person_unique_id': slot_data.get('person_unique_id'),
                    'is_filled': is_filled,
                    'filled_at': slot_data.get('filled_at') if is_filled else None,
                    'last_refreshed_at': now,
                    'created_at': slot_data.get('created_at', now),
                    'updated_at': now,
                }

                cursor.execute(self.UPSERT_SLOT_SQL, params)
                result.records_written = cursor.rowcount
                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to write slot: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def write_slots_batch(
        self,
        slots: List[Dict[str, Any]],
        correlation_id: str
    ) -> WriteResult:
        """Batch upsert multiple slots to Neon."""
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.company_slot")

        if not slots:
            result.success = True
            return result

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                for slot in slots:
                    try:
                        is_filled = slot.get('is_filled', False)
                        params = {
                            'company_slot_unique_id': slot.get('company_slot_unique_id'),
                            'company_unique_id': slot.get('company_unique_id'),
                            'slot_type': slot.get('slot_type'),
                            'person_unique_id': slot.get('person_unique_id'),
                            'is_filled': is_filled,
                            'filled_at': slot.get('filled_at') if is_filled else None,
                            'last_refreshed_at': now,
                            'created_at': slot.get('created_at', now),
                            'updated_at': now,
                        }
                        cursor.execute(self.UPSERT_SLOT_SQL, params)
                        result.records_written += 1
                    except Exception as e:
                        logger.warning(f"Failed to write slot: {e}")
                        result.records_failed += 1
                        result.errors.append(str(e))

                conn.commit()
                result.success = result.records_failed == 0

        except Exception as e:
            logger.error(f"Batch slot write failed: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def load_slots_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Load all slots for a company."""
        slots = []
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_SLOTS_BY_COMPANY_SQL, {
                    'company_unique_id': company_id
                })
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    slots.append(dict(zip(columns, row)))
        except Exception as e:
            logger.error(f"Failed to load slots for company {company_id}: {e}")
        return slots

    def load_all_slots(self) -> List[Dict[str, Any]]:
        """Load all slots from Neon for hub bootstrap."""
        slots = []
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_ALL_SLOTS_SQL)
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    slots.append(dict(zip(columns, row)))
                logger.info(f"Loaded {len(slots)} slots from Neon")
        except Exception as e:
            logger.error(f"Failed to load slots: {e}")
        return slots

    # -------------------------------------------------------------------------
    # PEOPLE OPERATIONS (marketing.people_master)
    # -------------------------------------------------------------------------

    UPSERT_PERSON_SQL = """
        INSERT INTO marketing.people_master (
            person_unique_id,
            full_name,
            first_name,
            last_name,
            email,
            email_verified,
            title,
            seniority,
            seniority_rank,
            linkedin_url,
            company_unique_id,
            slot_type,
            data_quality_score,
            created_at,
            updated_at
        ) VALUES (
            %(person_unique_id)s,
            %(full_name)s,
            %(first_name)s,
            %(last_name)s,
            %(email)s,
            %(email_verified)s,
            %(title)s,
            %(seniority)s,
            %(seniority_rank)s,
            %(linkedin_url)s,
            %(company_unique_id)s,
            %(slot_type)s,
            %(data_quality_score)s,
            %(created_at)s,
            %(updated_at)s
        )
        ON CONFLICT (person_unique_id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            email = COALESCE(EXCLUDED.email, marketing.people_master.email),
            email_verified = EXCLUDED.email_verified,
            title = COALESCE(EXCLUDED.title, marketing.people_master.title),
            seniority = COALESCE(EXCLUDED.seniority, marketing.people_master.seniority),
            seniority_rank = COALESCE(EXCLUDED.seniority_rank, marketing.people_master.seniority_rank),
            linkedin_url = COALESCE(EXCLUDED.linkedin_url, marketing.people_master.linkedin_url),
            company_unique_id = EXCLUDED.company_unique_id,
            slot_type = EXCLUDED.slot_type,
            data_quality_score = EXCLUDED.data_quality_score,
            updated_at = EXCLUDED.updated_at
    """

    LOAD_PERSON_BY_ID_SQL = """
        SELECT
            person_unique_id,
            full_name,
            first_name,
            last_name,
            email,
            email_verified,
            title,
            seniority,
            seniority_rank,
            linkedin_url,
            company_unique_id,
            slot_type,
            data_quality_score,
            created_at,
            updated_at
        FROM marketing.people_master
        WHERE person_unique_id = %(person_unique_id)s
    """

    FIND_PERSON_BY_EMAIL_SQL = """
        SELECT
            person_unique_id,
            full_name,
            email,
            title,
            company_unique_id
        FROM marketing.people_master
        WHERE LOWER(email) = LOWER(%(email)s)
        LIMIT 1
    """

    FIND_PERSON_BY_LINKEDIN_SQL = """
        SELECT
            person_unique_id,
            full_name,
            email,
            title,
            linkedin_url,
            company_unique_id
        FROM marketing.people_master
        WHERE linkedin_url = %(linkedin_url)s
        LIMIT 1
    """

    LOAD_PEOPLE_BY_COMPANY_SQL = """
        SELECT
            person_unique_id,
            full_name,
            first_name,
            last_name,
            email,
            email_verified,
            title,
            seniority,
            seniority_rank,
            linkedin_url,
            company_unique_id,
            slot_type,
            data_quality_score,
            created_at,
            updated_at
        FROM marketing.people_master
        WHERE company_unique_id = %(company_unique_id)s
        ORDER BY seniority_rank ASC
    """

    def write_person(
        self,
        person_data: Dict[str, Any],
        correlation_id: str
    ) -> WriteResult:
        """
        Upsert a person to Neon.

        Args:
            person_data: Person record dictionary
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with operation status
        """
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.people_master")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                params = {
                    'person_unique_id': person_data.get('person_unique_id'),
                    'full_name': person_data.get('full_name'),
                    'first_name': person_data.get('first_name'),
                    'last_name': person_data.get('last_name'),
                    'email': person_data.get('email'),
                    'email_verified': person_data.get('email_verified', False),
                    'title': person_data.get('title'),
                    'seniority': person_data.get('seniority'),
                    'seniority_rank': person_data.get('seniority_rank', 999),
                    'linkedin_url': person_data.get('linkedin_url'),
                    'company_unique_id': person_data.get('company_unique_id'),
                    'slot_type': person_data.get('slot_type'),
                    'data_quality_score': person_data.get('data_quality_score', 0.0),
                    'created_at': person_data.get('created_at', now),
                    'updated_at': now,
                }

                cursor.execute(self.UPSERT_PERSON_SQL, params)
                result.records_written = cursor.rowcount
                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to write person: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def write_people_batch(
        self,
        people: List[Dict[str, Any]],
        correlation_id: str
    ) -> WriteResult:
        """Batch upsert multiple people to Neon."""
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.people_master")

        if not people:
            result.success = True
            return result

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                for person in people:
                    try:
                        params = {
                            'person_unique_id': person.get('person_unique_id'),
                            'full_name': person.get('full_name'),
                            'first_name': person.get('first_name'),
                            'last_name': person.get('last_name'),
                            'email': person.get('email'),
                            'email_verified': person.get('email_verified', False),
                            'title': person.get('title'),
                            'seniority': person.get('seniority'),
                            'seniority_rank': person.get('seniority_rank', 999),
                            'linkedin_url': person.get('linkedin_url'),
                            'company_unique_id': person.get('company_unique_id'),
                            'slot_type': person.get('slot_type'),
                            'data_quality_score': person.get('data_quality_score', 0.0),
                            'created_at': person.get('created_at', now),
                            'updated_at': now,
                        }
                        cursor.execute(self.UPSERT_PERSON_SQL, params)
                        result.records_written += 1
                    except Exception as e:
                        logger.warning(f"Failed to write person: {e}")
                        result.records_failed += 1
                        result.errors.append(str(e))

                conn.commit()
                result.success = result.records_failed == 0

        except Exception as e:
            logger.error(f"Batch people write failed: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def load_person_by_id(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Load a single person by ID."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_PERSON_BY_ID_SQL, {
                    'person_unique_id': person_id
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to load person {person_id}: {e}")
        return None

    def find_person_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find person by email (case-insensitive)."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.FIND_PERSON_BY_EMAIL_SQL, {
                    'email': email
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to find person by email: {e}")
        return None

    def find_person_by_linkedin(self, linkedin_url: str) -> Optional[Dict[str, Any]]:
        """Find person by LinkedIn URL."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.FIND_PERSON_BY_LINKEDIN_SQL, {
                    'linkedin_url': linkedin_url
                })
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
        except Exception as e:
            logger.error(f"Failed to find person by LinkedIn: {e}")
        return None

    def load_people_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Load all people for a company."""
        people = []
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_PEOPLE_BY_COMPANY_SQL, {
                    'company_unique_id': company_id
                })
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    people.append(dict(zip(columns, row)))
        except Exception as e:
            logger.error(f"Failed to load people for company {company_id}: {e}")
        return people

    # -------------------------------------------------------------------------
    # OUTREACH OPERATIONS (marketing.outreach_log)
    # -------------------------------------------------------------------------

    INSERT_OUTREACH_LOG_SQL = """
        INSERT INTO marketing.outreach_log (
            outreach_id,
            company_unique_id,
            person_unique_id,
            campaign_id,
            sequence_step,
            outreach_type,
            bit_score_at_send,
            scheduled_at,
            sent_at,
            status,
            correlation_id,
            created_at
        ) VALUES (
            %(outreach_id)s,
            %(company_unique_id)s,
            %(person_unique_id)s,
            %(campaign_id)s,
            %(sequence_step)s,
            %(outreach_type)s,
            %(bit_score_at_send)s,
            %(scheduled_at)s,
            %(sent_at)s,
            %(status)s,
            %(correlation_id)s,
            %(created_at)s
        )
    """

    UPDATE_OUTREACH_STATUS_SQL = """
        UPDATE marketing.outreach_log
        SET status = %(status)s,
            sent_at = %(sent_at)s,
            updated_at = %(updated_at)s
        WHERE outreach_id = %(outreach_id)s
    """

    LOAD_OUTREACH_HISTORY_SQL = """
        SELECT
            outreach_id,
            company_unique_id,
            person_unique_id,
            campaign_id,
            sequence_step,
            outreach_type,
            bit_score_at_send,
            scheduled_at,
            sent_at,
            status,
            correlation_id,
            created_at
        FROM marketing.outreach_log
        WHERE company_unique_id = %(company_unique_id)s
        ORDER BY created_at DESC
        LIMIT %(limit)s
    """

    def write_outreach_log(
        self,
        outreach_data: Dict[str, Any],
        correlation_id: str
    ) -> WriteResult:
        """
        Log an outreach event to Neon.

        Args:
            outreach_data: Outreach event data
            correlation_id: MANDATORY - Pipeline trace ID

        Returns:
            WriteResult with operation status
        """
        validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.outreach_log")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                now = datetime.now()

                # Generate outreach ID
                import uuid
                outreach_id = f"04.04.02.04.70000.{uuid.uuid4().hex[:3].upper()}"

                params = {
                    'outreach_id': outreach_data.get('outreach_id', outreach_id),
                    'company_unique_id': outreach_data.get('company_unique_id'),
                    'person_unique_id': outreach_data.get('person_unique_id'),
                    'campaign_id': outreach_data.get('campaign_id'),
                    'sequence_step': outreach_data.get('sequence_step', 1),
                    'outreach_type': outreach_data.get('outreach_type', 'email'),
                    'bit_score_at_send': outreach_data.get('bit_score_at_send'),
                    'scheduled_at': outreach_data.get('scheduled_at'),
                    'sent_at': outreach_data.get('sent_at'),
                    'status': outreach_data.get('status', 'scheduled'),
                    'correlation_id': correlation_id,
                    'created_at': now,
                }

                cursor.execute(self.INSERT_OUTREACH_LOG_SQL, params)
                result.records_written = cursor.rowcount
                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to write outreach log: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def update_outreach_status(
        self,
        outreach_id: str,
        status: str,
        sent_at: datetime = None,
        correlation_id: str = None
    ) -> WriteResult:
        """Update outreach log status."""
        if correlation_id:
            validate_correlation_id(correlation_id)

        start_time = time.time()
        result = WriteResult(success=False, table_name="marketing.outreach_log")

        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.UPDATE_OUTREACH_STATUS_SQL, {
                    'outreach_id': outreach_id,
                    'status': status,
                    'sent_at': sent_at or datetime.now(),
                    'updated_at': datetime.now()
                })
                result.records_updated = cursor.rowcount
                conn.commit()
                result.success = True

        except Exception as e:
            logger.error(f"Failed to update outreach status: {e}")
            result.errors.append(str(e))
            if self._connection:
                self._connection.rollback()

        result.duration_seconds = time.time() - start_time
        return result

    def load_outreach_history(
        self,
        company_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Load outreach history for a company."""
        history = []
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(self.LOAD_OUTREACH_HISTORY_SQL, {
                    'company_unique_id': company_id,
                    'limit': limit
                })
                columns = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    history.append(dict(zip(columns, row)))
        except Exception as e:
            logger.error(f"Failed to load outreach history for {company_id}: {e}")
        return history

    def get_last_outreach_date(self, company_id: str) -> Optional[datetime]:
        """Get the last outreach date for a company (for cooling off period)."""
        history = self.load_outreach_history(company_id, limit=1)
        if history and history[0].get('sent_at'):
            return history[0]['sent_at']
        return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def check_company_neon_connection() -> bool:
    """Check if Neon connection is available."""
    config = NeonConfig.from_env()
    if not config.is_valid():
        logger.warning("Neon configuration incomplete")
        return False

    try:
        writer = CompanyNeonWriter(config)
        conn = writer._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        writer.close()
        return True
    except Exception as e:
        logger.error(f"Neon connection check failed: {e}")
        return False


def bootstrap_company_hub(hub) -> int:
    """
    Bootstrap CompanyHub with data from Neon.

    Args:
        hub: CompanyHub instance to populate

    Returns:
        Number of companies loaded
    """
    from .company_hub import CompanyHubRecord

    writer = CompanyNeonWriter()
    companies = writer.load_all_companies()
    writer.close()

    loaded = 0
    for company_data in companies:
        record = CompanyHubRecord(
            company_unique_id=company_data['company_unique_id'],
            company_name=company_data['company_name'],
            domain=company_data.get('domain'),
            email_pattern=company_data.get('email_pattern'),
            ein=company_data.get('ein'),
            industry=company_data.get('industry'),
            employee_count=company_data.get('employee_count'),
            address_state=company_data.get('address_state'),
            bit_score=company_data.get('bit_score', 0.0),
            data_quality_score=company_data.get('data_quality_score', 0.0),
            created_at=company_data.get('created_at'),
            updated_at=company_data.get('updated_at'),
        )
        if hub.add_company(record):
            loaded += 1

    logger.info(f"Bootstrapped CompanyHub with {loaded} companies from Neon")
    return loaded
