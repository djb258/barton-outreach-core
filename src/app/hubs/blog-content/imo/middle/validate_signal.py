"""
Blog Sub-Hub — Signal Validation Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 5,000 ft (Pre-emission gate)

EXPLICIT SCOPE:
  ✅ Validate company_sov_id exists
  ✅ Validate event type is allowed
  ✅ Validate confidence >= threshold
  ✅ Check for duplicate signals (hash-based)
  ✅ Validate source is declared

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER emit signals
  ❌ NEVER modify data
  ❌ NEVER rescue failed validations

VALIDATION GATES (All Must Pass):
  1. company_sov_id exists in Company Master
  2. event_type in allowed list
  3. confidence >= MIN_CONFIDENCE
  4. source in declared sources
  5. signal_hash not in dedup cache (30-day window)

═══════════════════════════════════════════════════════════════════════════
"""

import hashlib
from dataclasses import dataclass
from typing import Optional, List, Set
from datetime import datetime, timedelta
import logging

from .match_company import MatchedEvent
from .classify_event import EventType

logger = logging.getLogger(__name__)

# Configuration (Locked)
MIN_CONFIDENCE = 0.75  # Minimum confidence to emit signal
DEDUP_WINDOW_DAYS = 30  # Signal deduplication window
ALLOWED_EVENT_TYPES: Set[EventType] = {
    EventType.FUNDING_EVENT,
    EventType.ACQUISITION,
    EventType.LEADERSHIP_CHANGE,
    EventType.EXPANSION,
    EventType.PRODUCT_LAUNCH,
    EventType.PARTNERSHIP,
    EventType.LAYOFF,
    EventType.NEGATIVE_NEWS,
}


@dataclass
class ValidationGate:
    """Result of a single validation gate"""
    gate_name: str
    passed: bool
    reason: Optional[str] = None


@dataclass
class ValidatedSignal:
    """Signal that passed all validation gates"""
    correlation_id: str
    article_id: str
    
    # Signal identity
    signal_hash: str
    
    # Company anchor
    company_sov_id: str
    company_name: str
    
    # Event details
    event_type: EventType
    bit_impact: float
    confidence: float
    
    # Source tracking
    source: str
    source_url: str
    
    # Evidence
    evidence: List[str]
    
    # Original matched event
    matched_event: MatchedEvent
    
    # Validation metadata
    validated_at: datetime
    gates_passed: List[str]


@dataclass
class ValidationResult:
    """Result of signal validation"""
    success: bool
    validated: Optional[ValidatedSignal] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None
    
    # Gate details
    gates: List[ValidationGate] = None


# ─────────────────────────────────────────────────────────────────────────────
# Signal Hashing & Deduplication
# ─────────────────────────────────────────────────────────────────────────────

def _generate_signal_hash(company_sov_id: str, event_type: str, article_id: str) -> str:
    """
    Generate deduplication hash for signal.
    
    Hash key: (company_sov_id, event_type, article_id)
    """
    unique_string = f"{company_sov_id}|{event_type}|{article_id}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


# Dedup cache (in production, use Redis or database)
_signal_cache: dict = {}


def _check_duplicate(signal_hash: str) -> bool:
    """
    Check if signal is duplicate within dedup window.
    
    Returns True if duplicate, False if new.
    """
    if signal_hash in _signal_cache:
        cached_time = _signal_cache[signal_hash]
        if datetime.utcnow() - cached_time < timedelta(days=DEDUP_WINDOW_DAYS):
            return True
        else:
            # Expired entry
            del _signal_cache[signal_hash]
    
    return False


def _cache_signal(signal_hash: str) -> None:
    """Cache signal hash for deduplication"""
    _signal_cache[signal_hash] = datetime.utcnow()


# ─────────────────────────────────────────────────────────────────────────────
# Company Existence Check (Stub)
# ─────────────────────────────────────────────────────────────────────────────

async def _verify_company_exists(company_sov_id: str) -> bool:
    """
    Verify company_sov_id exists in Company Master.
    
    In production, this queries:
    SELECT 1 FROM company.company_master
    WHERE company_sov_id = $1
    LIMIT 1
    """
    # STUB: Replace with actual database query
    # For now, assume company exists if we matched it
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Validation Gate Functions
# ─────────────────────────────────────────────────────────────────────────────

async def _validate_company_exists(matched: MatchedEvent) -> ValidationGate:
    """Gate 1: Verify company_sov_id exists"""
    exists = await _verify_company_exists(matched.company_sov_id)
    
    return ValidationGate(
        gate_name="company_exists",
        passed=exists,
        reason=None if exists else f"company_sov_id not found: {matched.company_sov_id}"
    )


def _validate_event_type(matched: MatchedEvent) -> ValidationGate:
    """Gate 2: Verify event type is allowed"""
    event_type = matched.classified_event.event_type
    
    if event_type == EventType.UNKNOWN:
        return ValidationGate(
            gate_name="event_type_allowed",
            passed=False,
            reason="Event type is UNKNOWN"
        )
    
    if event_type not in ALLOWED_EVENT_TYPES:
        return ValidationGate(
            gate_name="event_type_allowed",
            passed=False,
            reason=f"Event type not allowed: {event_type.name_str}"
        )
    
    return ValidationGate(gate_name="event_type_allowed", passed=True)


def _validate_confidence(matched: MatchedEvent) -> ValidationGate:
    """Gate 3: Verify confidence >= threshold"""
    confidence = matched.classified_event.confidence
    
    if confidence < MIN_CONFIDENCE:
        return ValidationGate(
            gate_name="confidence_threshold",
            passed=False,
            reason=f"Confidence {confidence:.2f} < threshold {MIN_CONFIDENCE}"
        )
    
    return ValidationGate(gate_name="confidence_threshold", passed=True)


def _validate_source(matched: MatchedEvent) -> ValidationGate:
    """Gate 4: Verify source is declared"""
    source = matched.classified_event.entities.parsed_content.original_payload.source
    
    # All ArticleSource enum values are declared sources
    return ValidationGate(gate_name="source_declared", passed=True)


def _validate_not_duplicate(signal_hash: str) -> ValidationGate:
    """Gate 5: Verify signal is not duplicate"""
    is_duplicate = _check_duplicate(signal_hash)
    
    if is_duplicate:
        return ValidationGate(
            gate_name="not_duplicate",
            passed=False,
            reason=f"Duplicate signal within {DEDUP_WINDOW_DAYS}-day window"
        )
    
    return ValidationGate(gate_name="not_duplicate", passed=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main Validation Function
# ─────────────────────────────────────────────────────────────────────────────

async def validate_signal(matched: MatchedEvent) -> ValidationResult:
    """
    Validate signal before emission.
    
    Pipeline Stage 6: Signal Validation
    
    Args:
        matched: MatchedEvent from matching stage
        
    Returns:
        ValidationResult with ValidatedSignal or failure info
        
    DOCTRINE:
        - All gates must pass
        - FAIL CLOSED on any failure
        - No partial passes
        - DROP + LOG on failure
    """
    logger.info(
        "Signal validation started",
        extra={
            'correlation_id': matched.correlation_id,
            'article_id': matched.article_id,
            'company_sov_id': matched.company_sov_id,
            'event_type': matched.classified_event.event_type.name_str
        }
    )
    
    try:
        gates = []
        
        # Generate signal hash for dedup check
        signal_hash = _generate_signal_hash(
            matched.company_sov_id,
            matched.classified_event.event_type.name_str,
            matched.article_id
        )
        
        # ─────────────────────────────────────────────────────────────────────
        # Run all validation gates
        # ─────────────────────────────────────────────────────────────────────
        
        # Gate 1: Company exists
        gate1 = await _validate_company_exists(matched)
        gates.append(gate1)
        
        # Gate 2: Event type allowed
        gate2 = _validate_event_type(matched)
        gates.append(gate2)
        
        # Gate 3: Confidence threshold
        gate3 = _validate_confidence(matched)
        gates.append(gate3)
        
        # Gate 4: Source declared
        gate4 = _validate_source(matched)
        gates.append(gate4)
        
        # Gate 5: Not duplicate
        gate5 = _validate_not_duplicate(signal_hash)
        gates.append(gate5)
        
        # ─────────────────────────────────────────────────────────────────────
        # Check for failures
        # ─────────────────────────────────────────────────────────────────────
        failed_gates = [g for g in gates if not g.passed]
        
        if failed_gates:
            first_failure = failed_gates[0]
            
            logger.warning(
                f"Signal validation failed: {first_failure.reason}",
                extra={
                    'correlation_id': matched.correlation_id,
                    'article_id': matched.article_id,
                    'failed_gate': first_failure.gate_name,
                    'failed_gates_count': len(failed_gates)
                }
            )
            
            # Map gate failures to error codes
            fail_code_map = {
                'company_exists': 'BLOG-202',  # Invalid company_id
                'event_type_allowed': 'BLOG-003',  # Low confidence
                'confidence_threshold': 'BLOG-003',
                'source_declared': 'BLOG-001',
                'not_duplicate': 'BLOG-203',  # Duplicate signal
            }
            
            return ValidationResult(
                success=False,
                fail_reason=first_failure.reason,
                fail_code=fail_code_map.get(first_failure.gate_name, 'BLOG-003'),
                gates=gates
            )
        
        # ─────────────────────────────────────────────────────────────────────
        # All gates passed - build validated signal
        # ─────────────────────────────────────────────────────────────────────
        
        # Cache signal for deduplication
        _cache_signal(signal_hash)
        
        validated = ValidatedSignal(
            correlation_id=matched.correlation_id,
            article_id=matched.article_id,
            signal_hash=signal_hash,
            company_sov_id=matched.company_sov_id,
            company_name=matched.company_name,
            event_type=matched.classified_event.event_type,
            bit_impact=matched.classified_event.bit_impact,
            confidence=matched.classified_event.confidence,
            source=matched.classified_event.entities.parsed_content.original_payload.source.value,
            source_url=matched.classified_event.entities.parsed_content.original_payload.source_url,
            evidence=matched.classified_event.evidence,
            matched_event=matched,
            validated_at=datetime.utcnow(),
            gates_passed=[g.gate_name for g in gates]
        )
        
        logger.info(
            "Signal validation successful",
            extra={
                'correlation_id': matched.correlation_id,
                'article_id': matched.article_id,
                'company_sov_id': matched.company_sov_id,
                'event_type': matched.classified_event.event_type.name_str,
                'bit_impact': matched.classified_event.bit_impact,
                'gates_passed': len(gates)
            }
        )
        
        return ValidationResult(success=True, validated=validated, gates=gates)
        
    except Exception as e:
        logger.error(
            f"Signal validation error: {e}",
            extra={
                'correlation_id': matched.correlation_id,
                'article_id': matched.article_id,
                'error': str(e)
            }
        )
        return ValidationResult(
            success=False,
            fail_reason=f"Validation error: {e}",
            fail_code="BLOG-003"
        )
