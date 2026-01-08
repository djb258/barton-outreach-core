"""
Phase 7: Enrichment Queue
=========================
Builds unified enrichment queue for items needing additional processing.
Links all queue items to company_id (Company Hub anchor).

Queue Sources:
- Phase 5: Missing email patterns
- Phase 6: Empty slots, slot conflicts
- People: Missing emails, low confidence

Queue Priorities:
- HIGH: Missing pattern (affects all people at company)
- MEDIUM: Missing Benefits Lead, HR Manager slots
- LOW: Missing Payroll Admin, HR Support, individual emails

Waterfall Integration:
- When enable_waterfall=True, processes PATTERN_MISSING items via waterfall
- Tier 0 (free) → Tier 1 (low cost) → Tier 2 (premium)
- Resolved patterns returned for immediate email generation
- Respects budget and batch limits

REQUIRES: company_id anchor (Company-First doctrine)
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd

# Waterfall integration (optional - enabled via config)
try:
    from .waterfall_integration import Phase7WaterfallProcessor, WaterfallStats
    WATERFALL_AVAILABLE = True
except ImportError:
    WATERFALL_AVAILABLE = False

# Provider Benchmark Engine (System-Level) - Optional import
try:
    from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine
    _PBE_AVAILABLE = True
except ImportError:
    _PBE_AVAILABLE = False


class QueueReason(Enum):
    """Reasons for queueing an item."""
    # Pattern-related (from Phase 5)
    PATTERN_MISSING = "pattern_missing"
    PATTERN_LOW_CONFIDENCE = "pattern_low_confidence"

    # Slot-related (from Phase 6)
    SLOT_EMPTY_CHRO = "slot_empty_chro"
    SLOT_EMPTY_HR_MANAGER = "slot_empty_hr_manager"
    SLOT_EMPTY_BENEFITS = "slot_empty_benefits"
    SLOT_EMPTY_PAYROLL = "slot_empty_payroll"
    SLOT_EMPTY_HR_SUPPORT = "slot_empty_hr_support"
    SLOT_COLLISION = "slot_collision"

    # Email-related
    EMAIL_GENERATION_FAILED = "email_generation_failed"
    EMAIL_LOW_CONFIDENCE = "email_low_confidence"

    # Data quality
    MISSING_COMPANY_ID = "missing_company_id"
    MISSING_NAME = "missing_name"
    MISSING_TITLE = "missing_title"


class QueuePriority(Enum):
    """Priority levels for queued items."""
    HIGH = 1      # Missing pattern (blocks all emails), missing CHRO/Benefits
    MEDIUM = 2    # Missing HR Manager, Payroll Admin
    LOW = 3       # Missing HR Support, individual emails


class EntityType(Enum):
    """Types of entities in the queue."""
    COMPANY = "company"
    PERSON = "person"


@dataclass
class QueuedItem:
    """An item queued for enrichment."""
    queue_id: str
    entity_type: EntityType
    entity_id: str
    company_id: str  # Always present (Company-First doctrine)
    reason: QueueReason
    priority: QueuePriority
    source_phase: int
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_attempt: Optional[datetime] = None
    next_attempt: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, processing, completed, failed


@dataclass
class Phase7Stats:
    """Statistics for Phase 7 execution."""
    total_queued: int = 0
    high_priority: int = 0
    medium_priority: int = 0
    low_priority: int = 0
    company_items: int = 0
    person_items: int = 0
    pattern_missing: int = 0
    slot_missing: int = 0
    email_issues: int = 0
    # Waterfall processing stats
    waterfall_processed: int = 0       # Items processed by waterfall
    waterfall_resolved: int = 0        # Patterns discovered via waterfall
    waterfall_exhausted: int = 0       # Items where all tiers failed
    waterfall_api_calls: int = 0       # Total API calls made
    duration_seconds: float = 0.0


class Phase7EnrichmentQueue:
    """
    Phase 7: Build unified enrichment queue.

    Aggregates all items needing additional enrichment:
    - Companies missing email patterns
    - Companies with empty slots
    - People with failed email generation
    - Slot conflicts

    Movement Engine Integration:
    - Triggers movement for enrichment-driven BIT thresholds
    - Reports EventType.MOVEMENT_BIT_THRESHOLD when enrichment resolves

    REQUIRES: company_id anchor (Company-First doctrine)
    """

    # Priority mapping for queue reasons
    REASON_PRIORITY = {
        # HIGH priority - blocks multiple records
        QueueReason.PATTERN_MISSING: QueuePriority.HIGH,
        QueueReason.SLOT_EMPTY_CHRO: QueuePriority.HIGH,
        QueueReason.SLOT_EMPTY_BENEFITS: QueuePriority.HIGH,
        QueueReason.MISSING_COMPANY_ID: QueuePriority.HIGH,

        # MEDIUM priority - important but not blocking
        QueueReason.PATTERN_LOW_CONFIDENCE: QueuePriority.MEDIUM,
        QueueReason.SLOT_EMPTY_HR_MANAGER: QueuePriority.MEDIUM,
        QueueReason.SLOT_EMPTY_PAYROLL: QueuePriority.MEDIUM,
        QueueReason.SLOT_COLLISION: QueuePriority.MEDIUM,
        QueueReason.MISSING_TITLE: QueuePriority.MEDIUM,

        # LOW priority - individual items
        QueueReason.SLOT_EMPTY_HR_SUPPORT: QueuePriority.LOW,
        QueueReason.EMAIL_GENERATION_FAILED: QueuePriority.LOW,
        QueueReason.EMAIL_LOW_CONFIDENCE: QueuePriority.LOW,
        QueueReason.MISSING_NAME: QueuePriority.LOW,
    }

    def __init__(self, config: Dict[str, Any] = None, movement_engine=None):
        """
        Initialize Phase 7.

        Args:
            config: Configuration dictionary with:
                - max_retries: Max retry attempts per item (default: 3)
                - base_retry_delay: Base delay in seconds (default: 3600 = 1 hour)
                - enable_waterfall: bool - Enable waterfall processing for missing patterns
                - waterfall_mode: int - 0=Tier0 only, 1=Tier0+1, 2=Full (default)
                - waterfall_budget: float - Max budget for waterfall processing
                - waterfall_batch_limit: int - Max items to process per run
                - waterfall_config: dict - Config passed to waterfall processor
            movement_engine: Optional MovementEngine instance for event reporting
        """
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', 3)
        self.base_retry_delay = self.config.get('base_retry_delay', 3600)
        self.movement_engine = movement_engine

        # Waterfall integration (optional)
        self.enable_waterfall = self.config.get('enable_waterfall', False)
        self.waterfall_processor = None
        if self.enable_waterfall and WATERFALL_AVAILABLE:
            waterfall_config = self.config.get('waterfall_config', {})
            waterfall_config['mode'] = self.config.get('waterfall_mode', 2)  # Default: full
            waterfall_config['budget'] = self.config.get('waterfall_budget', None)
            waterfall_config['batch_limit'] = self.config.get('waterfall_batch_limit', 100)
            self.waterfall_processor = Phase7WaterfallProcessor(config=waterfall_config)

        # Provider Benchmark Engine reference
        self._pbe = None
        if _PBE_AVAILABLE:
            try:
                self._pbe = ProviderBenchmarkEngine.get_instance()
            except Exception:
                pass

        # In-memory queue storage (for pipeline run)
        self.queue: List[QueuedItem] = []

    def run(
        self,
        people_missing_pattern_df: pd.DataFrame,
        unslotted_people_df: pd.DataFrame,
        slot_summary_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Phase7Stats]:
        """
        Run enrichment queue phase.

        Args:
            people_missing_pattern_df: People without email patterns (from Phase 5)
            unslotted_people_df: People that couldn't be slotted (from Phase 6)
            slot_summary_df: Slot summary by company (from Phase 6)

        Returns:
            Tuple of (enrichment_queue_df, resolved_patterns_df, Phase7Stats)
            - enrichment_queue_df: Items still needing enrichment
            - resolved_patterns_df: Patterns discovered via waterfall (if enabled)
        """
        start_time = time.time()
        stats = Phase7Stats()
        resolved_patterns_df = pd.DataFrame()

        # Clear any existing queue
        self.queue = []

        # 1. Queue companies with missing patterns
        pattern_queue = self._queue_missing_patterns(people_missing_pattern_df)
        stats.pattern_missing += len(pattern_queue)

        # 2. Queue companies with empty slots
        slot_queue = self._queue_empty_slots(slot_summary_df)
        stats.slot_missing += len(slot_queue)

        # 3. Queue individuals with email issues
        email_queue = self._queue_email_issues(unslotted_people_df)
        stats.email_issues += len(email_queue)

        # 4. Process pattern-missing items with waterfall (if enabled)
        if self.waterfall_processor and pattern_queue:
            resolved_patterns_df, waterfall_stats = self._process_waterfall(
                people_missing_pattern_df
            )
            stats.waterfall_processed = waterfall_stats.get('processed', 0)
            stats.waterfall_resolved = waterfall_stats.get('resolved', 0)
            stats.waterfall_exhausted = waterfall_stats.get('exhausted', 0)
            stats.waterfall_api_calls = waterfall_stats.get('api_calls', 0)

            # Remove resolved items from queue
            resolved_company_ids = set(
                resolved_patterns_df['company_id'].tolist()
            ) if len(resolved_patterns_df) > 0 else set()

            self.queue = [
                item for item in self.queue
                if not (item.reason == QueueReason.PATTERN_MISSING and
                       item.company_id in resolved_company_ids)
            ]

            # Report movement events for resolved enrichments
            # Phase 7 triggers movement for enrichment-driven BIT thresholds
            if self.movement_engine and len(resolved_patterns_df) > 0:
                self._report_enrichment_resolved_events(resolved_patterns_df)

        # Calculate statistics
        stats.total_queued = len(self.queue)
        for item in self.queue:
            if item.priority == QueuePriority.HIGH:
                stats.high_priority += 1
            elif item.priority == QueuePriority.MEDIUM:
                stats.medium_priority += 1
            else:
                stats.low_priority += 1

            if item.entity_type == EntityType.COMPANY:
                stats.company_items += 1
            else:
                stats.person_items += 1

        # Build output DataFrame
        queue_df = self._build_queue_dataframe()

        stats.duration_seconds = time.time() - start_time

        return queue_df, resolved_patterns_df, stats

    def _process_waterfall(
        self,
        people_missing_pattern_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Process pattern-missing items via waterfall.

        Args:
            people_missing_pattern_df: People without patterns from Phase 5

        Returns:
            Tuple of (resolved_patterns_df, waterfall_stats_dict)
        """
        if not self.waterfall_processor:
            return pd.DataFrame(), {'processed': 0, 'resolved': 0, 'exhausted': 0, 'api_calls': 0}

        # Build queue DataFrame for waterfall processor
        # Get unique companies with domains
        queue_records = []
        seen_company_ids = set()

        for idx, row in people_missing_pattern_df.iterrows():
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            domain = str(row.get('domain', '') or row.get('company_domain', '')).strip()
            company_name = str(row.get('company_name', '') or row.get('matched_company_name', '')).strip()
            missing_reason = str(row.get('missing_reason', ''))

            if not company_id or company_id in seen_company_ids:
                continue

            if missing_reason != 'no_pattern_for_company':
                continue

            if domain:
                seen_company_ids.add(company_id)
                queue_records.append({
                    'company_id': company_id,
                    'domain': domain,
                    'company_name': company_name,
                    'reason': 'pattern_missing'
                })

        if not queue_records:
            return pd.DataFrame(), {'processed': 0, 'resolved': 0, 'exhausted': 0, 'api_calls': 0}

        queue_df = pd.DataFrame(queue_records)

        # Process via waterfall
        resolved_df, still_missing_df, waterfall_stats = self.waterfall_processor.process_queue(queue_df)

        # Convert stats to dict
        stats_dict = {
            'processed': waterfall_stats.total_processed if hasattr(waterfall_stats, 'total_processed') else 0,
            'resolved': waterfall_stats.patterns_found if hasattr(waterfall_stats, 'patterns_found') else 0,
            'exhausted': waterfall_stats.exhausted if hasattr(waterfall_stats, 'exhausted') else 0,
            'api_calls': waterfall_stats.api_calls if hasattr(waterfall_stats, 'api_calls') else 0
        }

        return resolved_df, stats_dict

    def _queue_missing_patterns(self, people_missing_pattern_df: pd.DataFrame) -> List[QueuedItem]:
        """
        Queue companies that are missing email patterns.

        Args:
            people_missing_pattern_df: People without patterns from Phase 5

        Returns:
            List of queued items
        """
        queued = []

        if people_missing_pattern_df is None or len(people_missing_pattern_df) == 0:
            return queued

        # Group by company_id to avoid duplicate queue entries
        company_ids_missing_pattern = set()

        for idx, row in people_missing_pattern_df.iterrows():
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            missing_reason = str(row.get('missing_reason', ''))

            if not company_id:
                continue

            # Queue company for pattern discovery
            if missing_reason == 'no_pattern_for_company' and company_id not in company_ids_missing_pattern:
                company_ids_missing_pattern.add(company_id)

                item = self._create_queue_item(
                    entity_type=EntityType.COMPANY,
                    entity_id=company_id,
                    company_id=company_id,
                    reason=QueueReason.PATTERN_MISSING,
                    source_phase=5,
                    metadata={
                        'affected_people_count': len(
                            people_missing_pattern_df[
                                (people_missing_pattern_df.get('company_id', '') == company_id) |
                                (people_missing_pattern_df.get('matched_company_id', '') == company_id)
                            ]
                        ) if 'company_id' in people_missing_pattern_df.columns else 1
                    }
                )
                self.queue.append(item)
                queued.append(item)

        return queued

    def _queue_empty_slots(self, slot_summary_df: pd.DataFrame) -> List[QueuedItem]:
        """
        Queue companies with empty HR slots.

        Args:
            slot_summary_df: Slot summary from Phase 6

        Returns:
            List of queued items
        """
        queued = []

        if slot_summary_df is None or len(slot_summary_df) == 0:
            return queued

        # Mapping from slot name to queue reason
        slot_to_reason = {
            'CHRO': QueueReason.SLOT_EMPTY_CHRO,
            'HR_MANAGER': QueueReason.SLOT_EMPTY_HR_MANAGER,
            'BENEFITS_LEAD': QueueReason.SLOT_EMPTY_BENEFITS,
            'PAYROLL_ADMIN': QueueReason.SLOT_EMPTY_PAYROLL,
            'HR_SUPPORT': QueueReason.SLOT_EMPTY_HR_SUPPORT,
        }

        for idx, row in slot_summary_df.iterrows():
            company_id = str(row.get('company_id', ''))
            missing_slots_str = str(row.get('missing_slots', ''))

            if not company_id or not missing_slots_str:
                continue

            missing_slots = [s.strip() for s in missing_slots_str.split(',') if s.strip()]

            for slot in missing_slots:
                reason = slot_to_reason.get(slot)
                if reason:
                    item = self._create_queue_item(
                        entity_type=EntityType.COMPANY,
                        entity_id=company_id,
                        company_id=company_id,
                        reason=reason,
                        source_phase=6,
                        metadata={
                            'missing_slot': slot,
                            'total_slots_filled': row.get('total_slots_filled', 0)
                        }
                    )
                    self.queue.append(item)
                    queued.append(item)

        return queued

    def _queue_email_issues(self, unslotted_people_df: pd.DataFrame) -> List[QueuedItem]:
        """
        Queue people with email generation issues.

        Args:
            unslotted_people_df: Unslotted people from Phase 6

        Returns:
            List of queued items
        """
        queued = []

        if unslotted_people_df is None or len(unslotted_people_df) == 0:
            return queued

        for idx, row in unslotted_people_df.iterrows():
            person_id = str(row.get('person_id', idx))
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            slot_reason = str(row.get('slot_reason', ''))

            if not company_id:
                # Queue for missing company anchor
                item = self._create_queue_item(
                    entity_type=EntityType.PERSON,
                    entity_id=person_id,
                    company_id='UNANCHORED',
                    reason=QueueReason.MISSING_COMPANY_ID,
                    source_phase=6,
                    metadata={
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'title': row.get('job_title', '') or row.get('title', '')
                    }
                )
                self.queue.append(item)
                queued.append(item)
                continue

            # Determine reason based on slot_reason
            reason = None
            if slot_reason == 'missing_title':
                reason = QueueReason.MISSING_TITLE
            elif slot_reason == 'missing_name':
                reason = QueueReason.MISSING_NAME
            elif slot_reason == 'slot_occupied_by_senior':
                reason = QueueReason.SLOT_COLLISION
            elif slot_reason == 'title_not_recognized':
                # Not an error - just couldn't classify
                continue

            if reason:
                item = self._create_queue_item(
                    entity_type=EntityType.PERSON,
                    entity_id=person_id,
                    company_id=company_id,
                    reason=reason,
                    source_phase=6,
                    metadata={
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'title': row.get('job_title', '') or row.get('title', ''),
                        'slot_reason': slot_reason
                    }
                )
                self.queue.append(item)
                queued.append(item)

        return queued

    def _create_queue_item(
        self,
        entity_type: EntityType,
        entity_id: str,
        company_id: str,
        reason: QueueReason,
        source_phase: int,
        metadata: Dict[str, Any] = None
    ) -> QueuedItem:
        """
        Create a queue item with proper priority.

        Args:
            entity_type: Type of entity
            entity_id: Entity unique ID
            company_id: Company anchor ID
            reason: Queue reason
            source_phase: Phase that triggered queueing
            metadata: Additional context

        Returns:
            QueuedItem
        """
        priority = self.REASON_PRIORITY.get(reason, QueuePriority.LOW)

        return QueuedItem(
            queue_id=self._generate_queue_id(),
            entity_type=entity_type,
            entity_id=entity_id,
            company_id=company_id,
            reason=reason,
            priority=priority,
            source_phase=source_phase,
            metadata=metadata or {}
        )

    def _generate_queue_id(self) -> str:
        """Generate unique queue ID."""
        return f"Q-{uuid.uuid4().hex[:12].upper()}"

    def _build_queue_dataframe(self) -> pd.DataFrame:
        """
        Build DataFrame from queue.

        Returns:
            DataFrame with queue records
        """
        if not self.queue:
            return pd.DataFrame()

        records = []
        for item in self.queue:
            records.append({
                'queue_id': item.queue_id,
                'entity_type': item.entity_type.value,
                'entity_id': item.entity_id,
                'company_id': item.company_id,
                'reason': item.reason.value,
                'priority': item.priority.value,
                'priority_name': item.priority.name,
                'source_phase': item.source_phase,
                'retry_count': item.retry_count,
                'status': item.status,
                'created_at': item.created_at.isoformat(),
                'metadata': str(item.metadata)
            })

        return pd.DataFrame(records)

    def add_to_queue(
        self,
        entity_type: str,
        entity_id: str,
        company_id: str,
        reason: str,
        priority: str = None,
        source_phase: int = 7,
        metadata: Dict = None
    ) -> str:
        """
        Add item to enrichment queue (external API).

        Args:
            entity_type: 'company' or 'person'
            entity_id: Entity unique ID
            company_id: Company anchor ID
            reason: Queue reason string
            priority: Optional priority override
            source_phase: Phase that generated queue request
            metadata: Additional context

        Returns:
            Queue ID for tracking
        """
        # Convert string to enum
        entity_enum = EntityType.COMPANY if entity_type.lower() == 'company' else EntityType.PERSON

        # Parse reason
        try:
            reason_enum = QueueReason(reason)
        except ValueError:
            reason_enum = QueueReason.PATTERN_MISSING  # Default

        item = self._create_queue_item(
            entity_type=entity_enum,
            entity_id=entity_id,
            company_id=company_id,
            reason=reason_enum,
            source_phase=source_phase,
            metadata=metadata
        )

        self.queue.append(item)
        return item.queue_id

    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get current queue statistics.

        Returns:
            Dict with queue counts by reason, priority, etc.
        """
        stats = {
            'total': len(self.queue),
            'by_priority': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'by_entity_type': {'company': 0, 'person': 0},
            'by_reason': {},
            'by_status': {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
        }

        for item in self.queue:
            stats['by_priority'][item.priority.name] += 1
            stats['by_entity_type'][item.entity_type.value] += 1
            stats['by_status'][item.status] += 1

            reason_key = item.reason.value
            stats['by_reason'][reason_key] = stats['by_reason'].get(reason_key, 0) + 1

        return stats

    def get_queue_batch(
        self,
        batch_size: int = 100,
        priority: QueuePriority = None,
        entity_type: EntityType = None
    ) -> List[Dict[str, Any]]:
        """
        Get batch of items from queue for processing.

        Args:
            batch_size: Maximum items to retrieve
            priority: Optional priority filter
            entity_type: Optional entity type filter

        Returns:
            List of queue items as dicts
        """
        filtered = []

        for item in self.queue:
            if item.status != 'pending':
                continue

            if priority and item.priority != priority:
                continue

            if entity_type and item.entity_type != entity_type:
                continue

            filtered.append(item)

            if len(filtered) >= batch_size:
                break

        # Sort by priority (lower number = higher priority)
        filtered.sort(key=lambda x: x.priority.value)

        return [
            {
                'queue_id': item.queue_id,
                'entity_type': item.entity_type.value,
                'entity_id': item.entity_id,
                'company_id': item.company_id,
                'reason': item.reason.value,
                'priority': item.priority.name,
                'metadata': item.metadata
            }
            for item in filtered[:batch_size]
        ]

    def calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay for retries.

        Args:
            retry_count: Number of previous attempts

        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: base_delay * 2^retry_count
        # With cap at 24 hours
        delay = self.base_retry_delay * (2 ** retry_count)
        max_delay = 86400  # 24 hours
        return min(delay, max_delay)

    def _report_enrichment_resolved_events(
        self,
        resolved_patterns_df: pd.DataFrame
    ) -> None:
        """
        Report movement events for resolved enrichments.

        Phase 7 triggers movement for enrichment-driven BIT thresholds.
        When patterns are discovered via waterfall, this signals to the
        Movement Engine that the company's data quality has improved.

        Args:
            resolved_patterns_df: DataFrame with resolved patterns from waterfall
        """
        if not self.movement_engine:
            return

        try:
            for idx, row in resolved_patterns_df.iterrows():
                company_id = str(row.get('company_id', ''))
                if not company_id:
                    continue

                # Report enrichment resolution event
                self.movement_engine.detect_event(
                    company_id=company_id,
                    person_id=None,  # Company-level event
                    event_type='enrichment_resolved',
                    metadata={
                        'phase': 7,
                        'resolution_type': 'pattern_discovered',
                        'pattern': row.get('pattern', ''),
                        'domain': row.get('domain', ''),
                        'source': row.get('source', 'waterfall'),
                        'event_category': 'MOVEMENT_BIT_THRESHOLD'
                    }
                )
        except Exception:
            # Don't fail enrichment queue due to movement event errors
            pass


def build_enrichment_queue(
    people_missing_pattern_df: pd.DataFrame,
    unslotted_people_df: pd.DataFrame,
    slot_summary_df: pd.DataFrame,
    config: Dict[str, Any] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Phase7Stats]:
    """
    Convenience function to build enrichment queue.

    Args:
        people_missing_pattern_df: People without patterns from Phase 5
        unslotted_people_df: Unslotted people from Phase 6
        slot_summary_df: Slot summary from Phase 6
        config: Optional configuration
            - enable_waterfall: bool - Enable waterfall processing
            - waterfall_mode: int - 0=Tier0 only, 1=Tier0+1, 2=Full
            - waterfall_budget: float - Max budget
            - waterfall_batch_limit: int - Max items per run

    Returns:
        Tuple of (enrichment_queue_df, resolved_patterns_df, Phase7Stats)
    """
    phase7 = Phase7EnrichmentQueue(config=config)
    return phase7.run(people_missing_pattern_df, unslotted_people_df, slot_summary_df)
