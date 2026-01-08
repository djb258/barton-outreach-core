"""
DOL Node Spoke - Department of Labor Data
==========================================
Processes DOL Form 5500, Schedule A, and violation data.

This spoke enriches company records with:
- Benefit plan information (Form 5500)
- Insurance broker data (Schedule A)
- Compliance facts (append-only to dol.* tables)

═══════════════════════════════════════════════════════════════════════════════
IMO DOCTRINE (v1.1 - Error-Only Enforcement)
═══════════════════════════════════════════════════════════════════════════════

The DOL Sub-Hub emits facts only.
All failures are DATA DEFICIENCIES, not system failures.
Therefore, the DOL Sub-Hub NEVER writes to AIR.

DOL is a FACTS-ONLY spoke. It:
  ✓ MAY read from company.company_master (EIN lookup)
  ✓ MAY write to dol.* tables (append-only facts)
  ✓ MAY write to shq.error_master (errors ONLY)
  ✗ MAY NOT write to company.company_master (CL sovereignty)
  ✗ MAY NOT emit BIT signals (intent routing violation)
  ✗ MAY NOT mint new company identity
  ✗ MAY NOT write to AIR (dol.air_log is FORBIDDEN)

Geographic Scope: 8 target states only (WV, VA, PA, MD, OH, KY, DE, NC)
Out-of-scope records are silently skipped (no error, no counter).
═══════════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType

# IMO Output layer - ERROR ONLY (no AIR)
from hubs.dol_filings.imo.output.error_writer import (
    write_error_master,
    DOLErrorCode,
    is_in_scope,
    normalize_ein,
    TARGET_STATES,
)

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, HubGateError, GateLevel


logger = logging.getLogger(__name__)


@dataclass
class Form5500Record:
    """A Form 5500 filing record"""
    filing_id: str
    ein: str
    plan_name: str
    plan_year_begin: Optional[datetime] = None
    plan_year_end: Optional[datetime] = None
    total_participants: int = 0
    total_assets: float = 0.0
    plan_effective_date: Optional[datetime] = None
    admin_name: Optional[str] = None
    admin_phone: Optional[str] = None
    is_small_plan: bool = False


@dataclass
class ScheduleARecord:
    """A Schedule A insurance record"""
    schedule_id: str
    filing_id: str
    ein: Optional[str] = None  # EIN from parent Form 5500
    broker_name: Optional[str] = None
    broker_fees: float = 0.0
    carrier_name: Optional[str] = None
    policy_type: Optional[str] = None
    plan_year: Optional[int] = None  # Year of the filing for YoY comparison


class DOLNodeSpoke(Spoke):
    """
    DOL Node - Spoke #2 of the Company Hub.

    Processes Department of Labor data to:
    1. Match Form 5500 filings to companies by EIN (Tool 18)
    2. Extract insurance broker data from Schedule A
    3. Write failures to shq.error_master (ERROR-ONLY, NO AIR)

    EIN Matching (Tool 18):
        DOCTRINE: Exact match only. No fuzzy. Fail closed.
        Uses Company Hub's find_company_by_ein for production lookup.

    IMO Enforcement (v1.1 - Error-Only):
        - DOL emits FACTS ONLY
        - NO BIT signals
        - NO CL writes
        - NO AIR logging (FORBIDDEN)
        - ALL failures route to shq.error_master
        
    Geographic Scope:
        8 target states: WV, VA, PA, MD, OH, KY, DE, NC
        Out-of-scope records are silently skipped.
    """

    def __init__(
        self,
        hub: Hub,
        company_pipeline=None
    ):
        """
        Initialize DOL Node Spoke.

        Args:
            hub: Parent hub instance
            company_pipeline: CompanyPipeline for EIN matching
        """
        super().__init__(name="dol_node", hub=hub)
        self._company_pipeline = company_pipeline

        # Track stats
        self.stats = {
            'total_processed': 0,
            'skipped_out_of_scope': 0,  # Geographic filter
            'matched_by_ein': 0,
            'ein_lookup_misses': 0,
            'errors_written': 0,  # Errors to shq.error_master
            'large_plans': 0,
            'schedule_a_records': 0,
            'broker_changes_detected': 0
        }

        # Broker tracking cache for YoY comparison
        # Structure: { ein: { prior_year: broker_name } }
        self._broker_cache: Dict[str, Dict[int, str]] = {}

    def set_company_pipeline(self, pipeline) -> None:
        """Set company pipeline for EIN matching."""
        self._company_pipeline = pipeline

    def process(self, data: Any, correlation_id: str) -> SpokeResult:
        """
        Process a DOL record and send signals to BIT Engine.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Can process Form5500Record or ScheduleARecord.

        Args:
            data: Form5500Record or ScheduleARecord to process
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            SpokeResult with processing outcome

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "dol.spoke.process"
        correlation_id = validate_correlation_id(correlation_id, process_id, "DOL Spoke")

        self.stats['total_processed'] += 1

        if isinstance(data, Form5500Record):
            return self._process_form_5500(data, correlation_id)
        elif isinstance(data, ScheduleARecord):
            return self._process_schedule_a(data, correlation_id)
        else:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Unknown data type: {type(data).__name__}"
            )

    def _process_form_5500(self, record: Form5500Record, correlation_id: str) -> SpokeResult:
        """
        Process a Form 5500 filing.

        GEOGRAPHIC FILTER: Only process records in 8 target states.
        Out-of-scope records are silently skipped (no error, no counter).

        HUB GATE: Validates company anchor after EIN lookup.
        ERROR-ONLY: Failures route to shq.error_master (no AIR).
        """
        if not record.ein:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason="No EIN in Form 5500 record"
            )

        # Look up company by EIN
        company_id = self._lookup_company_by_ein(record.ein)

        if not company_id:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason=f"No company found for EIN: {record.ein}"
            )

        # HUB GATE: Validate company anchor before sending signals
        gate_result = validate_company_anchor(
            record={'company_id': company_id, 'ein': record.ein},
            level=GateLevel.COMPANY_ID_ONLY,
            process_id="dol.spoke.form5500",
            correlation_id=correlation_id,
            fail_hard=False  # Route failures instead of crashing
        )

        if not gate_result.passed:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason=f"Hub gate failed: {gate_result.failure_reason}"
            )

        self.stats['matched_by_ein'] += 1

        # SUCCESS: Record matched, no error logging needed
        # Facts are stored in dol.form_5500 table directly (not via AIR)

        # Track large plans
        if record.total_participants >= 500:
            self.stats['large_plans'] += 1

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=record,
            # No hub_signal - DOL emits facts only
            metrics={
                'ein': record.ein,
                'participants': record.total_participants,
                'is_large_plan': record.total_participants >= 500
            }
        )

    def _process_schedule_a(self, record: ScheduleARecord, correlation_id: str) -> SpokeResult:
        """
        Process a Schedule A insurance record.

        Note: Schedule A links to Form 5500 by filing_id.
        Hub gate validation happens at parent filing level.

        BROKER_CHANGE Detection:
        - Compare current broker to prior year for same EIN
        - Emit BROKER_CHANGE signal (+7.0) if broker is different
        """
        self.stats['schedule_a_records'] += 1

        # Skip if no EIN or broker info
        if not record.ein or not record.broker_name:
            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=record,
                metrics={
                    'broker_name': record.broker_name,
                    'broker_fees': record.broker_fees,
                    'broker_change_detected': False
                }
            )

        # Normalize EIN and broker name
        ein_normalized = record.ein.replace('-', '').replace(' ', '').strip()
        broker_normalized = record.broker_name.strip().lower()
        current_year = record.plan_year or datetime.now().year

        # Look up company by EIN
        company_id = self._lookup_company_by_ein(ein_normalized)

        broker_changed = False

        # Check for broker change
        if ein_normalized in self._broker_cache:
            prior_years = self._broker_cache[ein_normalized]
            prior_year = current_year - 1

            if prior_year in prior_years:
                prior_broker = prior_years[prior_year]
                if prior_broker and prior_broker.lower() != broker_normalized:
                    broker_changed = True
                    self.stats['broker_changes_detected'] += 1

                    logger.info(
                        f"BROKER_CHANGE detected for EIN {ein_normalized}: "
                        f"{prior_broker} → {record.broker_name}"
                    )

                    # Broker change is a FACT, stored in dol.schedule_a
                    # NO AIR logging - facts go to DOL tables directly

        # Cache current broker for future comparisons
        if ein_normalized not in self._broker_cache:
            self._broker_cache[ein_normalized] = {}
        self._broker_cache[ein_normalized][current_year] = broker_normalized

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=record,
            # No hub_signal - DOL emits facts only (IMO v1.0)
            metrics={
                'broker_name': record.broker_name,
                'broker_fees': record.broker_fees,
                'broker_change_detected': broker_changed
            }
        )

    def _lookup_company_by_ein(self, ein: str) -> Optional[str]:
        """
        Look up company_id by EIN using deterministic matching (Tool 18).

        DOCTRINE: Fail closed on ambiguity. No ML/heuristics. Exact match only.

        Matching Strategy (per Pipeline Tool Doctrine):
        1. Exact EIN match via Company Hub (HIGHEST PRIORITY)
        2. If no match, return None (fail closed)

        Args:
            ein: Employer Identification Number to look up

        Returns:
            company_id if found, None otherwise
        """
        if not ein:
            return None

        # Normalize EIN (remove hyphens, spaces)
        ein_normalized = ein.replace('-', '').replace(' ', '').strip()

        if not ein_normalized or len(ein_normalized) != 9:
            logger.warning(f"Invalid EIN format: {ein}")
            return None

        # PRIORITY 1: Use Company Pipeline if available (production lookup)
        if self._company_pipeline:
            try:
                company = self._company_pipeline.find_company_by_ein(ein_normalized)
                if company:
                    logger.debug(f"EIN {ein_normalized} matched to company {company.company_unique_id}")
                    return company.company_unique_id
            except Exception as e:
                logger.error(f"Company Pipeline EIN lookup failed: {e}")

        # PRIORITY 2: Direct Company Hub lookup via Neon
        try:
            from hub.company import CompanyHub
            company_hub = CompanyHub()
            company = company_hub.find_company_by_ein(ein_normalized)

            if company:
                logger.debug(f"EIN {ein_normalized} matched to company {company.company_unique_id}")
                return company.company_unique_id

        except Exception as e:
            logger.error(f"Company Hub EIN lookup failed: {e}")

        # PRIORITY 3: Legacy hub database lookup (fallback)
        try:
            if hasattr(self.hub, 'db') and self.hub.db:
                result = self.hub.db.execute(
                    """
                    SELECT company_unique_id
                    FROM company.company_master
                    WHERE ein = %s
                    LIMIT 1
                    """,
                    (ein_normalized,)
                )
                row = result.fetchone() if result else None
                if row:
                    company_id = row[0] if isinstance(row, (list, tuple)) else row.get('company_unique_id')
                    logger.debug(f"EIN {ein_normalized} matched via legacy DB: {company_id}")
                    return company_id
        except Exception as e:
            logger.error(f"Legacy EIN lookup failed for {ein}: {e}")

        # FAIL CLOSED: No match found
        self.stats['ein_lookup_misses'] += 1
        logger.debug(f"EIN {ein_normalized} not found in any source - FAIL CLOSED")
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'total_processed': self.stats['total_processed'],
            'skipped_out_of_scope': self.stats.get('skipped_out_of_scope', 0),
            'matched_by_ein': self.stats['matched_by_ein'],
            'match_rate': f"{self.stats['matched_by_ein'] / max(self.stats['total_processed'], 1) * 100:.1f}%",
            'large_plans': self.stats['large_plans'],
            'schedule_a_records': self.stats['schedule_a_records'],
            'errors_written': self.stats.get('errors_written', 0),  # v1.1: errors to shq.error_master
            'broker_changes_detected': self.stats.get('broker_changes_detected', 0)
        }

    def load_broker_history(self, history_data: List[Dict[str, Any]]) -> int:
        """
        Pre-load broker history from database for YoY comparison.

        Args:
            history_data: List of dicts with ein, broker_name, plan_year

        Returns:
            Number of records loaded
        """
        loaded = 0
        for record in history_data:
            ein = record.get('ein', '').replace('-', '').replace(' ', '').strip()
            broker = record.get('broker_name', '').strip().lower()
            year = record.get('plan_year')

            if ein and broker and year:
                if ein not in self._broker_cache:
                    self._broker_cache[ein] = {}
                self._broker_cache[ein][year] = broker
                loaded += 1

        logger.info(f"Loaded {loaded} broker history records for BROKER_CHANGE detection")
        return loaded

    def clear_broker_cache(self):
        """Clear the broker cache (useful for testing or reset)."""
        self._broker_cache.clear()
        logger.info("Broker cache cleared")
