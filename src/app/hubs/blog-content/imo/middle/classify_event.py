"""
Blog Sub-Hub — Event Classification Layer
═══════════════════════════════════════════════════════════════════════════

Doctrine: /hubs/blog-content/PRD.md
Altitude: 6,000 ft (Event detection)

EXPLICIT SCOPE:
  ✅ Classify article into event types
  ✅ Apply hard rules FIRST (deterministic)
  ✅ LLM tie-breaker ONLY for ambiguous cases
  ✅ Return confidence scores

EXPLICIT NON-GOALS (STRICTLY FORBIDDEN):
  ❌ NEVER match companies
  ❌ NEVER emit signals
  ❌ NEVER override hard negative rules with LLM

EVENT TYPES (Locked):
  - FUNDING_EVENT (+15.0)
  - ACQUISITION (+12.0)
  - LEADERSHIP_CHANGE (+8.0)
  - EXPANSION (+7.0)
  - PRODUCT_LAUNCH (+5.0)
  - PARTNERSHIP (+5.0)
  - LAYOFF (-3.0)
  - NEGATIVE_NEWS (-5.0)

═══════════════════════════════════════════════════════════════════════════
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import logging

from .extract_entities import ExtractedEntities, MonetaryValue

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Locked event types with BIT impact"""
    FUNDING_EVENT = ("FUNDING_EVENT", 15.0)
    ACQUISITION = ("ACQUISITION", 12.0)
    LEADERSHIP_CHANGE = ("LEADERSHIP_CHANGE", 8.0)
    EXPANSION = ("EXPANSION", 7.0)
    PRODUCT_LAUNCH = ("PRODUCT_LAUNCH", 5.0)
    PARTNERSHIP = ("PARTNERSHIP", 5.0)
    LAYOFF = ("LAYOFF", -3.0)
    NEGATIVE_NEWS = ("NEGATIVE_NEWS", -5.0)
    UNKNOWN = ("UNKNOWN", 0.0)
    
    @property
    def name_str(self) -> str:
        return self.value[0]
    
    @property
    def bit_impact(self) -> float:
        return self.value[1]


@dataclass
class ClassificationCandidate:
    """A potential event classification"""
    event_type: EventType
    confidence: float  # 0.0 - 1.0
    evidence: List[str]  # Keywords/patterns that triggered
    method: str  # "hard_rule", "keyword", "llm"


@dataclass
class ClassifiedEvent:
    """Final event classification"""
    correlation_id: str
    article_id: str
    
    # Primary classification
    event_type: EventType
    confidence: float
    bit_impact: float
    
    # Supporting data
    candidates: List[ClassificationCandidate]
    evidence: List[str]
    
    # Extracted entities reference
    entities: ExtractedEntities
    
    # Classification method
    classification_method: str  # hard_rule, keyword, llm, hybrid
    llm_used: bool
    llm_cost: float  # Token cost if LLM was used


@dataclass
class ClassificationResult:
    """Result of event classification"""
    success: bool
    classified: Optional[ClassifiedEvent] = None
    fail_reason: Optional[str] = None
    fail_code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Hard Rule Keywords (Deterministic First)
# ─────────────────────────────────────────────────────────────────────────────

FUNDING_KEYWORDS = [
    r'\braised\b.*\$',
    r'\bfunding\b',
    r'\bseries\s+[a-z]\b',
    r'\bseed\s+round\b',
    r'\bventure\s+capital\b',
    r'\binvestment\s+round\b',
    r'\bmillion\s+in\s+funding\b',
    r'\bbillion\s+in\s+funding\b',
    r'\bcloses\b.*funding',
    r'\bannounces\s+funding\b',
    r'\bpre-seed\b',
    r'\bgrowth\s+round\b',
]

ACQUISITION_KEYWORDS = [
    r'\bacquired\b',
    r'\bacquisition\b',
    r'\bmerger\b',
    r'\bmerged\s+with\b',
    r'\bbuys\b',
    r'\bpurchased\b',
    r'\bto\s+acquire\b',
    r'\bacquisition\s+of\b',
    r'\bmerger\s+agreement\b',
    r'\bcombined\s+company\b',
    r'\bwill\s+acquire\b',
    r'\btakeover\b',
]

LEADERSHIP_KEYWORDS = [
    r'\bappointed\b',
    r'\bnamed\b.*(?:CEO|CFO|CTO|COO|President)',
    r'\bpromoted\b',
    r'\bjoins\b.*(?:CEO|CFO|CTO|COO|executive)',
    r'\bsteps\s+down\b',
    r'\bdeparts\b',
    r'\bresigned\b',
    r'\bretiring\b',
    r'\bnew\s+(?:CEO|CFO|CTO|COO)\b',
    r'\bchief\s+(?:executive|financial|technology|operating)\b',
    r'\bhires\b.*(?:executive|officer)',
]

EXPANSION_KEYWORDS = [
    r'\bexpansion\b',
    r'\bnew\s+office\b',
    r'\bopening\b.*(?:office|location|facility)',
    r'\bexpanding\s+to\b',
    r'\benters\b.*market',
    r'\blaunch(?:ing|es)?\b.*(?:market|region)',
    r'\bnew\s+headquarters\b',
    r'\brelocation\b',
]

PRODUCT_LAUNCH_KEYWORDS = [
    r'\blaunches\b',
    r'\bintroduces\b',
    r'\bannounces\b.*(?:product|service|platform)',
    r'\bnew\s+product\b',
    r'\bproduct\s+launch\b',
    r'\breleases\b.*(?:version|update)',
    r'\bunveils\b',
]

PARTNERSHIP_KEYWORDS = [
    r'\bpartnership\b',
    r'\bpartners\s+with\b',
    r'\bcollaboration\b',
    r'\bjoint\s+venture\b',
    r'\balliance\b',
    r'\bteams\s+up\b',
    r'\bstrategic\s+partnership\b',
]

LAYOFF_KEYWORDS = [
    r'\blayoff\b',
    r'\blayoffs\b',
    r'\bworkforce\s+reduction\b',
    r'\bcutting\s+jobs\b',
    r'\bjob\s+cuts\b',
    r'\bdownsizing\b',
    r'\brestructuring\b',
    r'\bletting\s+go\b',
    r'\beliminating\b.*(?:jobs|positions)',
    r'\breducing\s+headcount\b',
    r'\bstaff\s+reduction\b',
]

NEGATIVE_NEWS_KEYWORDS = [
    r'\blawsuit\b',
    r'\bsued\b',
    r'\blegal\s+action\b',
    r'\bfraud\b',
    r'\bscandal\b',
    r'\binvestigation\b',
    r'\bregulatory\s+action\b',
    r'\bfines\b',
    r'\bpenalties\b',
    r'\bbankruptcy\b',
    r'\bdefault\b',
]

# SEC 8-K Item Codes (Hard Rules)
SEC_8K_EVENT_MAP = {
    '1.01': EventType.ACQUISITION,  # Entry into Material Agreement
    '2.01': EventType.ACQUISITION,  # Completion of Acquisition
    '5.02': EventType.LEADERSHIP_CHANGE,  # Departure/Appointment of Officers
    '8.01': EventType.FUNDING_EVENT,  # Other Events (often funding)
}


# ─────────────────────────────────────────────────────────────────────────────
# Classification Functions
# ─────────────────────────────────────────────────────────────────────────────

def _check_sec_8k_rules(entities: ExtractedEntities) -> Optional[ClassificationCandidate]:
    """
    Check SEC 8-K item codes for deterministic classification.
    
    HARD RULE: SEC codes are authoritative for their respective event types.
    """
    metadata = entities.parsed_content.original_payload.raw_metadata
    item_codes = metadata.get('item_codes', [])
    
    for code in item_codes:
        if code in SEC_8K_EVENT_MAP:
            return ClassificationCandidate(
                event_type=SEC_8K_EVENT_MAP[code],
                confidence=0.95,  # Very high for SEC filings
                evidence=[f"SEC 8-K Item {code}"],
                method="hard_rule"
            )
    
    return None


def _match_keywords(text: str, patterns: List[str]) -> List[str]:
    """Match keyword patterns against text, return matches"""
    matches = []
    text_lower = text.lower()
    
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matches.append(pattern)
    
    return matches


def _classify_by_keywords(text: str) -> List[ClassificationCandidate]:
    """
    Classify event by keyword matching.
    
    Returns all candidates with confidence based on keyword density.
    """
    candidates = []
    
    keyword_sets = [
        (FUNDING_KEYWORDS, EventType.FUNDING_EVENT),
        (ACQUISITION_KEYWORDS, EventType.ACQUISITION),
        (LEADERSHIP_KEYWORDS, EventType.LEADERSHIP_CHANGE),
        (EXPANSION_KEYWORDS, EventType.EXPANSION),
        (PRODUCT_LAUNCH_KEYWORDS, EventType.PRODUCT_LAUNCH),
        (PARTNERSHIP_KEYWORDS, EventType.PARTNERSHIP),
        (LAYOFF_KEYWORDS, EventType.LAYOFF),
        (NEGATIVE_NEWS_KEYWORDS, EventType.NEGATIVE_NEWS),
    ]
    
    for patterns, event_type in keyword_sets:
        matches = _match_keywords(text, patterns)
        
        if matches:
            # Confidence based on number of matches
            confidence = min(0.90, 0.60 + (len(matches) * 0.10))
            
            candidates.append(ClassificationCandidate(
                event_type=event_type,
                confidence=confidence,
                evidence=matches,
                method="keyword"
            ))
    
    return candidates


def _validate_funding_with_amount(
    candidate: ClassificationCandidate,
    monetary_values: List[MonetaryValue]
) -> ClassificationCandidate:
    """
    Boost funding confidence if monetary values are present.
    """
    if candidate.event_type != EventType.FUNDING_EVENT:
        return candidate
    
    # Look for significant funding amounts
    for mv in monetary_values:
        if mv.amount >= 1_000_000:  # At least $1M
            return ClassificationCandidate(
                event_type=candidate.event_type,
                confidence=min(0.95, candidate.confidence + 0.10),
                evidence=candidate.evidence + [f"Funding amount: {mv.raw_text}"],
                method=candidate.method
            )
    
    return candidate


def _resolve_candidates(candidates: List[ClassificationCandidate]) -> Optional[ClassificationCandidate]:
    """
    Resolve multiple candidates to single classification.
    
    Rules:
    1. Hard rules always win
    2. Highest confidence wins
    3. Tie-breaker: More evidence wins
    """
    if not candidates:
        return None
    
    # Hard rules first
    hard_rules = [c for c in candidates if c.method == "hard_rule"]
    if hard_rules:
        return max(hard_rules, key=lambda c: c.confidence)
    
    # Sort by confidence, then evidence count
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (c.confidence, len(c.evidence)),
        reverse=True
    )
    
    top = sorted_candidates[0]
    
    # Check if there's ambiguity (multiple high-confidence candidates)
    if len(sorted_candidates) > 1:
        second = sorted_candidates[1]
        if abs(top.confidence - second.confidence) < 0.15:
            # Ambiguous - might need LLM tiebreaker
            top = ClassificationCandidate(
                event_type=top.event_type,
                confidence=top.confidence * 0.90,  # Reduce confidence due to ambiguity
                evidence=top.evidence + ["AMBIGUOUS: Multiple event types detected"],
                method="keyword_ambiguous"
            )
    
    return top


# ─────────────────────────────────────────────────────────────────────────────
# LLM Tiebreaker (Only for Ambiguous Cases)
# ─────────────────────────────────────────────────────────────────────────────

async def _llm_tiebreaker(
    text: str,
    headline: str,
    candidates: List[ClassificationCandidate],
    entities: ExtractedEntities
) -> Optional[ClassificationCandidate]:
    """
    Use LLM to resolve ambiguous classifications.
    
    DOCTRINE:
    - LLM cannot override hard negatives
    - LLM can only choose from existing candidates
    - LLM output is a classifier, not authority
    
    Returns None if LLM is not available or fails.
    """
    # This is a placeholder for LLM integration
    # In production, this would call GPT-4 or Claude
    
    logger.info(
        "LLM tiebreaker skipped (not configured)",
        extra={
            'correlation_id': entities.correlation_id,
            'candidates': [c.event_type.name_str for c in candidates]
        }
    )
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main Classification Function
# ─────────────────────────────────────────────────────────────────────────────

def classify_event(entities: ExtractedEntities) -> ClassificationResult:
    """
    Classify article into event type.
    
    Pipeline Stage 4: Event Classification
    
    Args:
        entities: ExtractedEntities from extraction stage
        
    Returns:
        ClassificationResult with ClassifiedEvent or failure info
        
    DOCTRINE:
        - Hard rules FIRST (SEC 8-K codes)
        - Keyword matching SECOND
        - LLM tiebreaker ONLY for ambiguous
        - FAIL CLOSED if no classification
    """
    logger.info(
        "Event classification started",
        extra={
            'correlation_id': entities.correlation_id,
            'article_id': entities.article_id
        }
    )
    
    try:
        text = entities.parsed_content.clean_text
        headline = entities.parsed_content.headline
        candidates = []
        llm_used = False
        llm_cost = 0.0
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 1: Check SEC 8-K hard rules
        # ─────────────────────────────────────────────────────────────────────
        sec_candidate = _check_sec_8k_rules(entities)
        if sec_candidate:
            candidates.append(sec_candidate)
            logger.info(
                f"SEC 8-K hard rule matched: {sec_candidate.event_type.name_str}",
                extra={'correlation_id': entities.correlation_id}
            )
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 2: Keyword classification
        # ─────────────────────────────────────────────────────────────────────
        keyword_candidates = _classify_by_keywords(text)
        
        # Boost funding if monetary values present
        keyword_candidates = [
            _validate_funding_with_amount(c, entities.monetary_values)
            for c in keyword_candidates
        ]
        
        candidates.extend(keyword_candidates)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 3: Resolve candidates
        # ─────────────────────────────────────────────────────────────────────
        final_candidate = _resolve_candidates(candidates)
        
        if final_candidate is None:
            # No event detected - this is OK, not all articles are events
            logger.info(
                "No event detected (below threshold or no keywords)",
                extra={
                    'correlation_id': entities.correlation_id,
                    'article_id': entities.article_id
                }
            )
            
            final_candidate = ClassificationCandidate(
                event_type=EventType.UNKNOWN,
                confidence=0.0,
                evidence=["No event keywords detected"],
                method="none"
            )
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 4: Build classified event
        # ─────────────────────────────────────────────────────────────────────
        classified = ClassifiedEvent(
            correlation_id=entities.correlation_id,
            article_id=entities.article_id,
            event_type=final_candidate.event_type,
            confidence=final_candidate.confidence,
            bit_impact=final_candidate.event_type.bit_impact,
            candidates=candidates,
            evidence=final_candidate.evidence,
            entities=entities,
            classification_method=final_candidate.method,
            llm_used=llm_used,
            llm_cost=llm_cost
        )
        
        logger.info(
            "Event classification successful",
            extra={
                'correlation_id': entities.correlation_id,
                'article_id': entities.article_id,
                'event_type': final_candidate.event_type.name_str,
                'confidence': final_candidate.confidence,
                'method': final_candidate.method,
                'evidence_count': len(final_candidate.evidence)
            }
        )
        
        return ClassificationResult(success=True, classified=classified)
        
    except Exception as e:
        logger.error(
            f"Event classification failed: {e}",
            extra={
                'correlation_id': entities.correlation_id,
                'article_id': entities.article_id,
                'error': str(e)
            }
        )
        return ClassificationResult(
            success=False,
            fail_reason=f"Classification error: {e}",
            fail_code="BLOG-003"  # Low confidence / classification failed
        )
