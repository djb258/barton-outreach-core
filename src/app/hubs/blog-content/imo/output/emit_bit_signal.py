"""
Blog Sub-Hub — Signal Emission Layer (Output)
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 4,500 ft (Final output)

EXPLICIT SCOPE:
  ✅ Emit validated signals to BIT Engine
  ✅ Write to AIR log
  ✅ Record cost attribution (if LLM used)
  ✅ Return terminal state

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER modify company data
  ❌ NEVER trigger enrichment
  ❌ NEVER retry failed emissions
  ❌ NEVER emit unvalidated signals

TERMINAL STATES:
  - EMITTED: Signal successfully sent to BIT Engine
  - QUEUED: Article queued for identity resolution
  - DROPPED: Signal failed validation

═══════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import logging

from ..middle.validate_signal import ValidatedSignal

logger = logging.getLogger(__name__)


class TerminalState(Enum):
    """Pipeline terminal states"""
    EMITTED = "EMITTED"  # Signal sent to BIT Engine
    QUEUED = "QUEUED"    # Queued for identity resolution
    DROPPED = "DROPPED"  # Failed validation


@dataclass
class EmittedSignal:
    """Record of emitted signal"""
    correlation_id: str
    article_id: str
    
    # Signal details
    signal_id: str  # Generated ID for this emission
    company_sov_id: str
    event_type: str
    bit_impact: float
    
    # Metadata
    emitted_at: datetime
    source: str
    confidence: float
    
    # Cost tracking
    llm_used: bool
    llm_cost: float


@dataclass
class EmissionResult:
    """Result of signal emission"""
    success: bool
    terminal_state: TerminalState
    
    # Emission details (if successful)
    emitted: Optional[EmittedSignal] = None
    
    # Failure details (if failed)
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None
    
    # Cost attribution
    total_cost: float = 0.0
    
    # AIR log entry
    air_event_id: Optional[str] = None


@dataclass
class AIRLogEntry:
    """Audit, Intelligence, and Reporting log entry"""
    event_id: str
    correlation_id: str
    article_id: str
    timestamp: datetime
    
    # Event details
    event_type: str
    terminal_state: str
    
    # Company (if matched)
    company_sov_id: Optional[str]
    
    # Signal (if emitted)
    signal_type: Optional[str]
    bit_impact: Optional[float]
    confidence: Optional[float]
    
    # Processing metadata
    source: str
    source_url: str
    processing_time_ms: int
    
    # Cost attribution
    llm_used: bool
    llm_cost: float
    
    # Failure info (if any)
    fail_code: Optional[str]
    fail_reason: Optional[str]


# ─────────────────────────────────────────────────────────────────────────────
# BIT Engine Integration (Stub)
# ─────────────────────────────────────────────────────────────────────────────

async def _send_to_bit_engine(signal: ValidatedSignal) -> bool:
    """
    Send signal to BIT Engine.
    
    In production, this calls the BIT Engine API:
    POST /api/v1/signals
    {
        "company_sov_id": "...",
        "signal_type": "FUNDING_EVENT",
        "impact": 15.0,
        "source": "blog_subhub",
        "correlation_id": "...",
        "metadata": {...}
    }
    """
    # STUB: Replace with actual BIT Engine call
    logger.info(
        f"BIT Engine signal (STUB): {signal.event_type.name_str} for {signal.company_sov_id}",
        extra={
            'correlation_id': signal.correlation_id,
            'company_sov_id': signal.company_sov_id,
            'event_type': signal.event_type.name_str,
            'bit_impact': signal.bit_impact
        }
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# AIR Logging
# ─────────────────────────────────────────────────────────────────────────────

_air_log: list = []  # In production, this writes to database


def _generate_event_id() -> str:
    """Generate unique event ID for AIR log"""
    import uuid
    return f"AIR-BLOG-{uuid.uuid4().hex[:12].upper()}"


def _generate_signal_id() -> str:
    """Generate unique signal ID"""
    import uuid
    return f"SIG-BLOG-{uuid.uuid4().hex[:12].upper()}"


async def _write_air_log(entry: AIRLogEntry) -> str:
    """
    Write entry to AIR log.
    
    In production, this writes to:
    INSERT INTO air.blog_events (...)
    """
    _air_log.append(entry)
    
    logger.info(
        f"AIR log entry: {entry.event_type} -> {entry.terminal_state}",
        extra={
            'event_id': entry.event_id,
            'correlation_id': entry.correlation_id,
            'article_id': entry.article_id,
            'terminal_state': entry.terminal_state,
            'company_sov_id': entry.company_sov_id
        }
    )
    
    return entry.event_id


# ─────────────────────────────────────────────────────────────────────────────
# Main Emission Function
# ─────────────────────────────────────────────────────────────────────────────

async def emit_bit_signal(
    validated: ValidatedSignal,
    processing_time_ms: int = 0
) -> EmissionResult:
    """
    Emit validated signal to BIT Engine.
    
    Pipeline Stage 7: Signal Emission (Final)
    
    Args:
        validated: ValidatedSignal from validation stage
        processing_time_ms: Total pipeline processing time
        
    Returns:
        EmissionResult with terminal state
        
    DOCTRINE:
        - Only emit validated signals
        - No retries on failure
        - Always write AIR log
        - Track cost attribution
    """
    logger.info(
        "Signal emission started",
        extra={
            'correlation_id': validated.correlation_id,
            'article_id': validated.article_id,
            'company_sov_id': validated.company_sov_id,
            'event_type': validated.event_type.name_str
        }
    )
    
    event_id = _generate_event_id()
    signal_id = _generate_signal_id()
    
    # Get LLM cost from classification stage
    llm_used = validated.matched_event.classified_event.llm_used
    llm_cost = validated.matched_event.classified_event.llm_cost
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # Send to BIT Engine
        # ─────────────────────────────────────────────────────────────────────
        bit_success = await _send_to_bit_engine(validated)
        
        if not bit_success:
            # BIT Engine unavailable - fail but log
            air_entry = AIRLogEntry(
                event_id=event_id,
                correlation_id=validated.correlation_id,
                article_id=validated.article_id,
                timestamp=datetime.utcnow(),
                event_type="SIGNAL_EMISSION",
                terminal_state=TerminalState.DROPPED.value,
                company_sov_id=validated.company_sov_id,
                signal_type=validated.event_type.name_str,
                bit_impact=validated.bit_impact,
                confidence=validated.confidence,
                source=validated.source,
                source_url=validated.source_url,
                processing_time_ms=processing_time_ms,
                llm_used=llm_used,
                llm_cost=llm_cost,
                fail_code="BLOG-201",
                fail_reason="BIT Engine unavailable"
            )
            
            await _write_air_log(air_entry)
            
            return EmissionResult(
                success=False,
                terminal_state=TerminalState.DROPPED,
                fail_reason="BIT Engine unavailable",
                fail_code="BLOG-201",
                total_cost=llm_cost,
                air_event_id=event_id
            )
        
        # ─────────────────────────────────────────────────────────────────────
        # Build emitted signal record
        # ─────────────────────────────────────────────────────────────────────
        emitted = EmittedSignal(
            correlation_id=validated.correlation_id,
            article_id=validated.article_id,
            signal_id=signal_id,
            company_sov_id=validated.company_sov_id,
            event_type=validated.event_type.name_str,
            bit_impact=validated.bit_impact,
            emitted_at=datetime.utcnow(),
            source=validated.source,
            confidence=validated.confidence,
            llm_used=llm_used,
            llm_cost=llm_cost
        )
        
        # ─────────────────────────────────────────────────────────────────────
        # Write AIR log
        # ─────────────────────────────────────────────────────────────────────
        air_entry = AIRLogEntry(
            event_id=event_id,
            correlation_id=validated.correlation_id,
            article_id=validated.article_id,
            timestamp=datetime.utcnow(),
            event_type="SIGNAL_EMISSION",
            terminal_state=TerminalState.EMITTED.value,
            company_sov_id=validated.company_sov_id,
            signal_type=validated.event_type.name_str,
            bit_impact=validated.bit_impact,
            confidence=validated.confidence,
            source=validated.source,
            source_url=validated.source_url,
            processing_time_ms=processing_time_ms,
            llm_used=llm_used,
            llm_cost=llm_cost,
            fail_code=None,
            fail_reason=None
        )
        
        await _write_air_log(air_entry)
        
        logger.info(
            "Signal emission successful",
            extra={
                'correlation_id': validated.correlation_id,
                'article_id': validated.article_id,
                'signal_id': signal_id,
                'company_sov_id': validated.company_sov_id,
                'event_type': validated.event_type.name_str,
                'bit_impact': validated.bit_impact,
                'terminal_state': TerminalState.EMITTED.value
            }
        )
        
        return EmissionResult(
            success=True,
            terminal_state=TerminalState.EMITTED,
            emitted=emitted,
            total_cost=llm_cost,
            air_event_id=event_id
        )
        
    except Exception as e:
        logger.error(
            f"Signal emission failed: {e}",
            extra={
                'correlation_id': validated.correlation_id,
                'article_id': validated.article_id,
                'error': str(e)
            }
        )
        
        # Write failure to AIR log
        air_entry = AIRLogEntry(
            event_id=event_id,
            correlation_id=validated.correlation_id,
            article_id=validated.article_id,
            timestamp=datetime.utcnow(),
            event_type="SIGNAL_EMISSION",
            terminal_state=TerminalState.DROPPED.value,
            company_sov_id=validated.company_sov_id,
            signal_type=validated.event_type.name_str,
            bit_impact=validated.bit_impact,
            confidence=validated.confidence,
            source=validated.source,
            source_url=validated.source_url,
            processing_time_ms=processing_time_ms,
            llm_used=llm_used,
            llm_cost=llm_cost,
            fail_code="BLOG-204",
            fail_reason=str(e)
        )
        
        await _write_air_log(air_entry)
        
        return EmissionResult(
            success=False,
            terminal_state=TerminalState.DROPPED,
            fail_reason=f"Emission error: {e}",
            fail_code="BLOG-204",
            total_cost=llm_cost,
            air_event_id=event_id
        )


# ─────────────────────────────────────────────────────────────────────────────
# Queue/Drop Functions (for failed pipelines)
# ─────────────────────────────────────────────────────────────────────────────

async def log_queued_article(
    correlation_id: str,
    article_id: str,
    queue_payload: Dict[str, Any],
    source: str,
    source_url: str,
    processing_time_ms: int = 0
) -> str:
    """Log article queued for identity resolution"""
    
    event_id = _generate_event_id()
    
    air_entry = AIRLogEntry(
        event_id=event_id,
        correlation_id=correlation_id,
        article_id=article_id,
        timestamp=datetime.utcnow(),
        event_type="ARTICLE_QUEUED",
        terminal_state=TerminalState.QUEUED.value,
        company_sov_id=None,
        signal_type=None,
        bit_impact=None,
        confidence=None,
        source=source,
        source_url=source_url,
        processing_time_ms=processing_time_ms,
        llm_used=False,
        llm_cost=0.0,
        fail_code="BLOG-004",
        fail_reason="Company not matched - queued for identity resolution"
    )
    
    await _write_air_log(air_entry)
    
    logger.info(
        "Article queued for identity resolution",
        extra={
            'correlation_id': correlation_id,
            'article_id': article_id,
            'event_id': event_id,
            'terminal_state': TerminalState.QUEUED.value
        }
    )
    
    return event_id


async def log_dropped_article(
    correlation_id: str,
    article_id: str,
    fail_code: str,
    fail_reason: str,
    source: str,
    source_url: str,
    company_sov_id: Optional[str] = None,
    processing_time_ms: int = 0,
    llm_cost: float = 0.0
) -> str:
    """Log article dropped due to validation failure"""
    
    event_id = _generate_event_id()
    
    air_entry = AIRLogEntry(
        event_id=event_id,
        correlation_id=correlation_id,
        article_id=article_id,
        timestamp=datetime.utcnow(),
        event_type="ARTICLE_DROPPED",
        terminal_state=TerminalState.DROPPED.value,
        company_sov_id=company_sov_id,
        signal_type=None,
        bit_impact=None,
        confidence=None,
        source=source,
        source_url=source_url,
        processing_time_ms=processing_time_ms,
        llm_used=False,
        llm_cost=llm_cost,
        fail_code=fail_code,
        fail_reason=fail_reason
    )
    
    await _write_air_log(air_entry)
    
    logger.warning(
        f"Article dropped: {fail_reason}",
        extra={
            'correlation_id': correlation_id,
            'article_id': article_id,
            'event_id': event_id,
            'fail_code': fail_code,
            'terminal_state': TerminalState.DROPPED.value
        }
    )
    
    return event_id
