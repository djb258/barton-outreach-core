"""
Blog Node Spoke — Pipeline Orchestrator
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 10,000 → 5,000 ft (Full pipeline orchestration)

EXPLICIT SCOPE:
  ✅ Orchestrate pipeline stages in order
  ✅ Enforce kill switches
  ✅ Emit AIR events
  ✅ Track observability metrics
  ✅ Return terminal state

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER contain business logic (delegate only)
  ❌ NEVER create companies
  ❌ NEVER trigger enrichment
  ❌ NEVER retry failures
  ❌ NEVER rescue failed stages

PIPELINE ORDER (Non-Negotiable):
  1. Ingest Article
  2. Parse Content
  3. Extract Entities
  4. Classify Event
  5. Match Company
  6. Validate Signal
  7. Emit BIT Signal

═══════════════════════════════════════════════════════════════════════════
"""

import os
import time
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Pipeline stage imports
from .imo.input.ingest_article import ingest_article, ArticlePayload
from .imo.middle.parse_content import parse_content
from .imo.middle.extract_entities import extract_entities
from .imo.middle.classify_event import classify_event, EventType
from .imo.middle.match_company import match_company
from .imo.middle.validate_signal import validate_signal
from .imo.output.emit_bit_signal import (
    emit_bit_signal,
    log_queued_article,
    log_dropped_article,
    TerminalState,
    EmissionResult
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Kill Switch Configuration
# ─────────────────────────────────────────────────────────────────────────────

KILL_SWITCHES = {
    'KILL_BLOG_SUBHUB': 'ALL',
    'KILL_FUNDING_DETECTION': 'FUNDING_EVENT',
    'KILL_MA_DETECTION': 'ACQUISITION',
    'KILL_LEADERSHIP_DETECTION': 'LEADERSHIP_CHANGE',
    'KILL_BLOG_SIGNALS': 'EMISSION',
}


def _check_kill_switches() -> Optional[str]:
    """
    Check if any kill switches are active.
    
    Returns kill switch name if active, None otherwise.
    """
    for switch, scope in KILL_SWITCHES.items():
        if os.environ.get(switch, 'false').lower() == 'true':
            return switch
    return None


def _check_event_kill_switch(event_type: EventType) -> bool:
    """Check if kill switch is active for specific event type"""
    event_kill_map = {
        EventType.FUNDING_EVENT: 'KILL_FUNDING_DETECTION',
        EventType.ACQUISITION: 'KILL_MA_DETECTION',
        EventType.LEADERSHIP_CHANGE: 'KILL_LEADERSHIP_DETECTION',
    }
    
    switch = event_kill_map.get(event_type)
    if switch:
        return os.environ.get(switch, 'false').lower() == 'true'
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Result
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    """Result of full pipeline execution"""
    correlation_id: str
    article_id: Optional[str]
    terminal_state: TerminalState
    
    # Company match (if successful)
    company_sov_id: Optional[str] = None
    
    # Event (if classified)
    event_type: Optional[str] = None
    confidence: Optional[float] = None
    
    # Timing
    processing_time_ms: int = 0
    
    # Cost attribution
    total_cost: float = 0.0
    
    # AIR event ID
    air_event_id: Optional[str] = None
    
    # Failure info
    failed_stage: Optional[str] = None
    fail_code: Optional[str] = None
    fail_reason: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Blog Node Spoke Class
# ─────────────────────────────────────────────────────────────────────────────

class BlogNodeSpoke:
    """
    Blog Node Spoke - Signal Pipeline Orchestrator
    
    This spoke orchestrates the full pipeline:
    Ingest → Parse → Extract → Classify → Match → Validate → Emit
    
    DOCTRINE:
    - Zero business logic (delegate to stages)
    - FAIL CLOSED on any error
    - Always log to AIR
    - Track all costs
    """
    
    def __init__(self):
        self.name = "blog_node"
        self.stats = {
            'total_processed': 0,
            'emitted': 0,
            'queued': 0,
            'dropped': 0,
            'total_cost': 0.0,
            'kill_switch_blocks': 0,
        }
    
    async def run(self, article_payload: Dict[str, Any]) -> PipelineResult:
        """
        Execute the full Blog Sub-Hub pipeline.
        
        Args:
            article_payload: Raw article data from any source
            
        Returns:
            PipelineResult with terminal state and metadata
            
        DOCTRINE:
            - Orchestration only, no logic
            - FAIL CLOSED on any stage failure
            - Always return terminal state
        """
        start_time = time.time()
        correlation_id = article_payload.get('correlation_id', 'unknown')
        article_id = None
        source = article_payload.get('source', 'unknown')
        source_url = article_payload.get('source_url', '')
        
        logger.info(
            "Blog pipeline started",
            extra={
                'correlation_id': correlation_id,
                'source': source
            }
        )
        
        self.stats['total_processed'] += 1
        
        # ─────────────────────────────────────────────────────────────────────
        # Kill Switch Check (Global)
        # ─────────────────────────────────────────────────────────────────────
        active_switch = _check_kill_switches()
        if active_switch:
            self.stats['kill_switch_blocks'] += 1
            logger.warning(
                f"Pipeline killed by switch: {active_switch}",
                extra={'correlation_id': correlation_id}
            )
            
            return PipelineResult(
                correlation_id=correlation_id,
                article_id=None,
                terminal_state=TerminalState.DROPPED,
                fail_code="BLOG-000",
                fail_reason=f"Kill switch active: {active_switch}",
                failed_stage="kill_switch"
            )
        
        try:
            # ─────────────────────────────────────────────────────────────────
            # Stage 1: Ingest Article
            # ─────────────────────────────────────────────────────────────────
            ingest_result = ingest_article(article_payload)
            
            if not ingest_result.success:
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=None,
                    stage="ingest",
                    fail_code=ingest_result.fail_code,
                    fail_reason=ingest_result.fail_reason,
                    source=source,
                    source_url=source_url,
                    start_time=start_time
                )
            
            payload = ingest_result.payload
            article_id = payload.article_id
            correlation_id = payload.correlation_id
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 2: Parse Content
            # ─────────────────────────────────────────────────────────────────
            parse_result = parse_content(payload)
            
            if not parse_result.success:
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="parse",
                    fail_code=parse_result.fail_code,
                    fail_reason=parse_result.fail_reason,
                    source=source,
                    source_url=source_url,
                    start_time=start_time
                )
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 3: Extract Entities
            # ─────────────────────────────────────────────────────────────────
            extract_result = extract_entities(parse_result.parsed)
            
            if not extract_result.success:
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="extract",
                    fail_code=extract_result.fail_code,
                    fail_reason=extract_result.fail_reason,
                    source=source,
                    source_url=source_url,
                    start_time=start_time
                )
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 4: Classify Event
            # ─────────────────────────────────────────────────────────────────
            classify_result = classify_event(extract_result.entities)
            
            if not classify_result.success:
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="classify",
                    fail_code=classify_result.fail_code,
                    fail_reason=classify_result.fail_reason,
                    source=source,
                    source_url=source_url,
                    start_time=start_time
                )
            
            classified = classify_result.classified
            
            # Check if event type is killed
            if _check_event_kill_switch(classified.event_type):
                self.stats['kill_switch_blocks'] += 1
                logger.warning(
                    f"Event type killed: {classified.event_type.name_str}",
                    extra={'correlation_id': correlation_id}
                )
                
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="classify",
                    fail_code="BLOG-000",
                    fail_reason=f"Event type killed: {classified.event_type.name_str}",
                    source=source,
                    source_url=source_url,
                    start_time=start_time
                )
            
            # Skip if no event detected
            if classified.event_type == EventType.UNKNOWN:
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    "No event detected - pipeline complete (no signal)",
                    extra={
                        'correlation_id': correlation_id,
                        'article_id': article_id,
                        'processing_time_ms': processing_time_ms
                    }
                )
                
                self.stats['dropped'] += 1
                
                air_event_id = await log_dropped_article(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    fail_code="BLOG-003",
                    fail_reason="No event detected",
                    source=source,
                    source_url=source_url,
                    processing_time_ms=processing_time_ms
                )
                
                return PipelineResult(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    terminal_state=TerminalState.DROPPED,
                    event_type="UNKNOWN",
                    confidence=0.0,
                    processing_time_ms=processing_time_ms,
                    air_event_id=air_event_id,
                    fail_code="BLOG-003",
                    fail_reason="No event detected",
                    failed_stage="classify"
                )
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 5: Match Company
            # ─────────────────────────────────────────────────────────────────
            match_result = await match_company(classified)
            
            if not match_result.success:
                if match_result.queued_for_resolution:
                    # Queue for identity resolution
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    self.stats['queued'] += 1
                    
                    air_event_id = await log_queued_article(
                        correlation_id=correlation_id,
                        article_id=article_id,
                        queue_payload=match_result.queue_payload,
                        source=source,
                        source_url=source_url,
                        processing_time_ms=processing_time_ms
                    )
                    
                    return PipelineResult(
                        correlation_id=correlation_id,
                        article_id=article_id,
                        terminal_state=TerminalState.QUEUED,
                        event_type=classified.event_type.name_str,
                        confidence=classified.confidence,
                        processing_time_ms=processing_time_ms,
                        air_event_id=air_event_id,
                        fail_code=match_result.fail_code,
                        fail_reason=match_result.fail_reason,
                        failed_stage="match"
                    )
                else:
                    return await self._handle_failure(
                        correlation_id=correlation_id,
                        article_id=article_id,
                        stage="match",
                        fail_code=match_result.fail_code,
                        fail_reason=match_result.fail_reason,
                        source=source,
                        source_url=source_url,
                        start_time=start_time
                    )
            
            matched = match_result.matched
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 6: Validate Signal
            # ─────────────────────────────────────────────────────────────────
            validate_result = await validate_signal(matched)
            
            if not validate_result.success:
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="validate",
                    fail_code=validate_result.fail_code,
                    fail_reason=validate_result.fail_reason,
                    source=source,
                    source_url=source_url,
                    company_sov_id=matched.company_sov_id,
                    start_time=start_time
                )
            
            # ─────────────────────────────────────────────────────────────────
            # Kill Switch Check (Emission)
            # ─────────────────────────────────────────────────────────────────
            if os.environ.get('KILL_BLOG_SIGNALS', 'false').lower() == 'true':
                self.stats['kill_switch_blocks'] += 1
                return await self._handle_failure(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    stage="emit",
                    fail_code="BLOG-000",
                    fail_reason="Signal emission killed by switch",
                    source=source,
                    source_url=source_url,
                    company_sov_id=matched.company_sov_id,
                    start_time=start_time
                )
            
            # ─────────────────────────────────────────────────────────────────
            # Stage 7: Emit BIT Signal
            # ─────────────────────────────────────────────────────────────────
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            emit_result = await emit_bit_signal(
                validate_result.validated,
                processing_time_ms=processing_time_ms
            )
            
            if emit_result.success:
                self.stats['emitted'] += 1
                self.stats['total_cost'] += emit_result.total_cost
                
                logger.info(
                    "Blog pipeline complete - EMITTED",
                    extra={
                        'correlation_id': correlation_id,
                        'article_id': article_id,
                        'company_sov_id': matched.company_sov_id,
                        'event_type': classified.event_type.name_str,
                        'bit_impact': classified.bit_impact,
                        'processing_time_ms': processing_time_ms
                    }
                )
                
                return PipelineResult(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    terminal_state=TerminalState.EMITTED,
                    company_sov_id=matched.company_sov_id,
                    event_type=classified.event_type.name_str,
                    confidence=classified.confidence,
                    processing_time_ms=processing_time_ms,
                    total_cost=emit_result.total_cost,
                    air_event_id=emit_result.air_event_id
                )
            else:
                self.stats['dropped'] += 1
                
                return PipelineResult(
                    correlation_id=correlation_id,
                    article_id=article_id,
                    terminal_state=TerminalState.DROPPED,
                    company_sov_id=matched.company_sov_id,
                    event_type=classified.event_type.name_str,
                    confidence=classified.confidence,
                    processing_time_ms=processing_time_ms,
                    total_cost=emit_result.total_cost,
                    air_event_id=emit_result.air_event_id,
                    fail_code=emit_result.fail_code,
                    fail_reason=emit_result.fail_reason,
                    failed_stage="emit"
                )
                
        except Exception as e:
            logger.error(
                f"Pipeline exception: {e}",
                extra={
                    'correlation_id': correlation_id,
                    'article_id': article_id,
                    'error': str(e)
                }
            )
            
            return await self._handle_failure(
                correlation_id=correlation_id,
                article_id=article_id,
                stage="exception",
                fail_code="BLOG-999",
                fail_reason=f"Unhandled exception: {e}",
                source=source,
                source_url=source_url,
                start_time=start_time
            )
    
    async def _handle_failure(
        self,
        correlation_id: str,
        article_id: Optional[str],
        stage: str,
        fail_code: str,
        fail_reason: str,
        source: str,
        source_url: str,
        start_time: float,
        company_sov_id: Optional[str] = None
    ) -> PipelineResult:
        """Handle pipeline stage failure"""
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        self.stats['dropped'] += 1
        
        air_event_id = await log_dropped_article(
            correlation_id=correlation_id,
            article_id=article_id or "unknown",
            fail_code=fail_code,
            fail_reason=fail_reason,
            source=source,
            source_url=source_url,
            company_sov_id=company_sov_id,
            processing_time_ms=processing_time_ms
        )
        
        logger.warning(
            f"Pipeline failed at stage: {stage}",
            extra={
                'correlation_id': correlation_id,
                'article_id': article_id,
                'failed_stage': stage,
                'fail_code': fail_code,
                'fail_reason': fail_reason
            }
        )
        
        return PipelineResult(
            correlation_id=correlation_id,
            article_id=article_id,
            terminal_state=TerminalState.DROPPED,
            company_sov_id=company_sov_id,
            processing_time_ms=processing_time_ms,
            air_event_id=air_event_id,
            fail_code=fail_code,
            fail_reason=fail_reason,
            failed_stage=stage
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        total = self.stats['total_processed']
        return {
            'total_processed': total,
            'emitted': self.stats['emitted'],
            'queued': self.stats['queued'],
            'dropped': self.stats['dropped'],
            'emit_rate': f"{self.stats['emitted'] / max(total, 1) * 100:.1f}%",
            'queue_rate': f"{self.stats['queued'] / max(total, 1) * 100:.1f}%",
            'drop_rate': f"{self.stats['dropped'] / max(total, 1) * 100:.1f}%",
            'total_cost': self.stats['total_cost'],
            'kill_switch_blocks': self.stats['kill_switch_blocks'],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Function
# ─────────────────────────────────────────────────────────────────────────────

# Global spoke instance
_spoke = None


def get_spoke() -> BlogNodeSpoke:
    """Get or create global spoke instance"""
    global _spoke
    if _spoke is None:
        _spoke = BlogNodeSpoke()
    return _spoke


async def run(article_payload: Dict[str, Any]) -> PipelineResult:
    """
    Run the Blog Sub-Hub pipeline.
    
    This is the main entry point for the Blog Node Spoke.
    
    Args:
        article_payload: Raw article data
        
    Returns:
        PipelineResult with terminal state
    """
    spoke = get_spoke()
    return await spoke.run(article_payload)
