"""
Event Detection Engine
======================
Detects business events from news article content using
keyword patterns and entity extraction.

Per PRD v2.1: Uses spaCy for NER, with fallback to keyword patterns.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .models import (
    NewsArticle,
    DetectedEvent,
    EventType,
    FundingDetails,
    AcquisitionDetails,
    LeadershipChangeDetails,
    LayoffDetails,
    ExpansionDetails,
)


logger = logging.getLogger(__name__)


# =============================================================================
# KEYWORD PATTERNS (Per PRD Section 5)
# =============================================================================

FUNDING_KEYWORDS = [
    'raised', 'funding', 'series a', 'series b', 'series c', 'series d',
    'seed round', 'venture capital', 'investment round', 'growth round',
    'led by', 'participated in', 'million in funding', 'billion in funding',
    'closes', 'announces funding', 'funding round', 'capital raise',
    'pre-seed', 'seed funding', 'late stage', 'growth equity',
    'strategic investment', 'financing round', 'secured funding'
]

MA_KEYWORDS = [
    'acquired', 'acquisition', 'merger', 'merged with', 'buys', 'purchased',
    'deal', 'transaction', 'to acquire', 'acquisition of', 'merger agreement',
    'combined company', 'will acquire', 'being acquired', 'takeover',
    'buyout', 'spin-off', 'spinoff', 'carve-out', 'divestiture'
]

LEADERSHIP_KEYWORDS = [
    'appointed', 'named', 'promoted', 'joins', 'steps down', 'departs',
    'resigned', 'retiring', 'new ceo', 'new cfo', 'new cto', 'new coo',
    'chief executive', 'chief financial', 'chief technology', 'chief operating',
    'new president', 'new chairman', 'board of directors', 'executive team',
    'announces departure', 'succession', 'replaces', 'succeeds'
]

LAYOFF_KEYWORDS = [
    'layoff', 'layoffs', 'workforce reduction', 'cutting jobs', 'job cuts',
    'downsizing', 'restructuring', 'letting go', 'eliminating', 'job losses',
    'reducing headcount', 'staff reduction', 'reduction in force', 'rif',
    'laying off', 'cuts staff', 'cutting workforce', 'downsizes'
]

EXPANSION_KEYWORDS = [
    'expansion', 'expands', 'expanding', 'new office', 'opens office',
    'new market', 'entering market', 'launches in', 'growing presence',
    'opening headquarters', 'new facility', 'hiring spree', 'plans to hire',
    'expanding operations', 'new location', 'international expansion'
]

PRODUCT_LAUNCH_KEYWORDS = [
    'launches', 'announces', 'introduces', 'unveils', 'releases',
    'new product', 'product launch', 'now available', 'general availability',
    'ga release', 'beta launch', 'public beta', 'new feature', 'new service',
    'rolling out', 'launching today'
]

PARTNERSHIP_KEYWORDS = [
    'partnership', 'partners with', 'partners', 'strategic alliance',
    'collaboration', 'collaborates', 'joint venture', 'teaming up',
    'agreement with', 'deal with', 'signs agreement', 'integrates with'
]

NEGATIVE_NEWS_KEYWORDS = [
    'lawsuit', 'sued', 'investigation', 'scandal', 'fraud', 'breach',
    'data breach', 'security breach', 'regulatory action', 'fine',
    'penalty', 'settlement', 'bankruptcy', 'chapter 11', 'default',
    'credit downgrade', 'sec investigation', 'ftc investigation'
]


# =============================================================================
# AMOUNT EXTRACTION PATTERNS
# =============================================================================

AMOUNT_PATTERN = re.compile(
    r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|m|b|mn|bn)?',
    re.IGNORECASE
)

PERCENTAGE_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:workforce|employees|staff|jobs)?',
    re.IGNORECASE
)

HEADCOUNT_PATTERN = re.compile(
    r'(\d+(?:,\d{3})*)\s*(?:employees|workers|jobs|positions|staff|people)',
    re.IGNORECASE
)


# =============================================================================
# ROUND TYPE DETECTION
# =============================================================================

ROUND_PATTERNS = {
    'Pre-Seed': re.compile(r'pre[- ]?seed', re.IGNORECASE),
    'Seed': re.compile(r'\bseed\b(?!\s+round)', re.IGNORECASE),
    'Series A': re.compile(r'series\s*a\b', re.IGNORECASE),
    'Series B': re.compile(r'series\s*b\b', re.IGNORECASE),
    'Series C': re.compile(r'series\s*c\b', re.IGNORECASE),
    'Series D': re.compile(r'series\s*d\b', re.IGNORECASE),
    'Series E': re.compile(r'series\s*e\b', re.IGNORECASE),
    'Growth': re.compile(r'growth\s*(?:round|equity|funding)', re.IGNORECASE),
    'Late Stage': re.compile(r'late[- ]?stage', re.IGNORECASE),
}


# =============================================================================
# EVENT DETECTOR
# =============================================================================

class EventDetector:
    """
    Detects business events from news article content.

    Detection Pipeline:
    1. Keyword matching (fast, baseline)
    2. Entity extraction (NER if available)
    3. Confidence scoring based on:
       - Keyword density
       - Entity quality
       - Source reliability
    """

    def __init__(self, min_confidence: float = 0.50):
        """
        Initialize event detector.

        Args:
            min_confidence: Minimum confidence to emit signal (default 0.50)
        """
        self.min_confidence = min_confidence
        self._nlp = None  # Lazy load spaCy

        # Stats
        self._stats = {
            'total_processed': 0,
            'events_detected': 0,
            'funding_events': 0,
            'acquisition_events': 0,
            'leadership_events': 0,
            'layoff_events': 0,
            'expansion_events': 0,
            'product_launch_events': 0,
            'partnership_events': 0,
            'negative_news_events': 0,
        }

    def _get_nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_lg")
                logger.info("spaCy model loaded successfully")
            except Exception as e:
                logger.warning(f"spaCy not available, using keyword-only: {e}")
                self._nlp = False  # Mark as unavailable
        return self._nlp if self._nlp else None

    def detect_events(self, article: NewsArticle) -> List[DetectedEvent]:
        """
        Detect all business events in an article.

        Args:
            article: NewsArticle to process

        Returns:
            List of DetectedEvent objects
        """
        self._stats['total_processed'] += 1
        events = []

        # Combine title and content for analysis
        text = f"{article.title}\n\n{article.content}"
        text_lower = text.lower()

        # Extract entities using NER if available
        entities = self._extract_entities(text)
        article.person_mentions = entities.get('PERSON', [])
        article.company_mentions = entities.get('ORG', [])
        article.amount_mentions = self._extract_amounts(text)

        # Detect each event type
        funding_event = self._detect_funding(text, text_lower, entities)
        if funding_event and funding_event.confidence >= self.min_confidence:
            events.append(funding_event)
            self._stats['funding_events'] += 1

        ma_event = self._detect_acquisition(text, text_lower, entities)
        if ma_event and ma_event.confidence >= self.min_confidence:
            events.append(ma_event)
            self._stats['acquisition_events'] += 1

        leadership_event = self._detect_leadership_change(text, text_lower, entities)
        if leadership_event and leadership_event.confidence >= self.min_confidence:
            events.append(leadership_event)
            self._stats['leadership_events'] += 1

        layoff_event = self._detect_layoff(text, text_lower, entities)
        if layoff_event and layoff_event.confidence >= self.min_confidence:
            events.append(layoff_event)
            self._stats['layoff_events'] += 1

        expansion_event = self._detect_expansion(text, text_lower, entities)
        if expansion_event and expansion_event.confidence >= self.min_confidence:
            events.append(expansion_event)
            self._stats['expansion_events'] += 1

        product_event = self._detect_product_launch(text, text_lower, entities)
        if product_event and product_event.confidence >= self.min_confidence:
            events.append(product_event)
            self._stats['product_launch_events'] += 1

        partnership_event = self._detect_partnership(text, text_lower, entities)
        if partnership_event and partnership_event.confidence >= self.min_confidence:
            events.append(partnership_event)
            self._stats['partnership_events'] += 1

        negative_event = self._detect_negative_news(text, text_lower, entities)
        if negative_event and negative_event.confidence >= self.min_confidence:
            events.append(negative_event)
            self._stats['negative_news_events'] += 1

        self._stats['events_detected'] += len(events)
        return events

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy or fallback."""
        entities: Dict[str, List[str]] = {
            'PERSON': [],
            'ORG': [],
            'MONEY': [],
            'GPE': [],
        }

        nlp = self._get_nlp()
        if nlp:
            try:
                doc = nlp(text[:10000])  # Limit for performance
                for ent in doc.ents:
                    if ent.label_ in entities:
                        entities[ent.label_].append(ent.text)
            except Exception as e:
                logger.warning(f"NER extraction failed: {e}")

        return entities

    def _extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts from text."""
        amounts = []
        for match in AMOUNT_PATTERN.finditer(text):
            amounts.append(match.group(0))
        return amounts

    def _count_keyword_matches(self, text_lower: str, keywords: List[str]) -> Tuple[int, List[str]]:
        """Count keyword matches and return matched keywords."""
        matched = []
        for kw in keywords:
            if kw in text_lower:
                matched.append(kw)
        return len(matched), matched

    def _calculate_confidence(
        self,
        keyword_count: int,
        max_keywords: int,
        has_entities: bool,
        entity_count: int = 0
    ) -> float:
        """
        Calculate event detection confidence.

        Base confidence from keyword density, boosted by entity presence.
        """
        if keyword_count == 0:
            return 0.0

        # Base confidence from keyword density (0.3 - 0.7)
        keyword_ratio = min(keyword_count / max(max_keywords, 1), 1.0)
        base_confidence = 0.3 + (keyword_ratio * 0.4)

        # Boost for entities (up to +0.25)
        entity_boost = 0.0
        if has_entities:
            entity_boost = min(entity_count * 0.05, 0.25)

        # Cap at 0.95
        return min(base_confidence + entity_boost, 0.95)

    def _detect_funding(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect funding events."""
        count, matched = self._count_keyword_matches(text_lower, FUNDING_KEYWORDS)
        if count == 0:
            return None

        # Extract funding-specific details
        amounts = self._extract_amounts(text)
        round_type = self._extract_round_type(text)
        investors = entities.get('ORG', [])[:3]  # Top 3 orgs as potential investors

        has_amount = len(amounts) > 0
        confidence = self._calculate_confidence(
            count, 5, has_amount, len(amounts) + (1 if round_type else 0)
        )

        funding_details = FundingDetails(
            amount=amounts[0] if amounts else None,
            round_type=round_type,
            lead_investor=investors[0] if investors else None,
            participating_investors=investors[1:] if len(investors) > 1 else [],
            confidence=confidence
        )

        return DetectedEvent(
            event_type=EventType.FUNDING_EVENT,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'amounts': amounts, 'investors': investors},
            funding_details=funding_details
        )

    def _extract_round_type(self, text: str) -> Optional[str]:
        """Extract funding round type from text."""
        for round_name, pattern in ROUND_PATTERNS.items():
            if pattern.search(text):
                return round_name
        return None

    def _detect_acquisition(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect acquisition/M&A events."""
        count, matched = self._count_keyword_matches(text_lower, MA_KEYWORDS)
        if count == 0:
            return None

        amounts = self._extract_amounts(text)
        orgs = entities.get('ORG', [])[:3]

        confidence = self._calculate_confidence(
            count, 4, len(orgs) >= 2, len(orgs)
        )

        acquisition_details = AcquisitionDetails(
            acquisition_type='acquisition' if 'acquired' in text_lower else 'merger',
            target_company=orgs[1] if len(orgs) > 1 else None,
            acquirer_company=orgs[0] if orgs else None,
            deal_value=amounts[0] if amounts else None,
            confidence=confidence
        )

        return DetectedEvent(
            event_type=EventType.ACQUISITION,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'companies': orgs, 'amounts': amounts},
            acquisition_details=acquisition_details
        )

    def _detect_leadership_change(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect leadership change events."""
        count, matched = self._count_keyword_matches(text_lower, LEADERSHIP_KEYWORDS)
        if count == 0:
            return None

        persons = entities.get('PERSON', [])[:2]
        orgs = entities.get('ORG', [])[:2]

        has_person = len(persons) > 0
        confidence = self._calculate_confidence(
            count, 4, has_person, len(persons)
        )

        # Determine change type
        change_type = 'unknown'
        if any(kw in text_lower for kw in ['appointed', 'named', 'joins']):
            change_type = 'hired'
        elif any(kw in text_lower for kw in ['promoted']):
            change_type = 'promoted'
        elif any(kw in text_lower for kw in ['departs', 'resigned', 'steps down']):
            change_type = 'departed'
        elif any(kw in text_lower for kw in ['retiring']):
            change_type = 'retired'

        leadership_details = LeadershipChangeDetails(
            person_name=persons[0] if persons else None,
            change_type=change_type,
            confidence=confidence
        )

        return DetectedEvent(
            event_type=EventType.LEADERSHIP_CHANGE,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'persons': persons, 'companies': orgs},
            leadership_details=leadership_details
        )

    def _detect_layoff(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect layoff events."""
        count, matched = self._count_keyword_matches(text_lower, LAYOFF_KEYWORDS)
        if count == 0:
            return None

        # Extract headcount and percentage
        headcount = None
        percentage = None

        headcount_match = HEADCOUNT_PATTERN.search(text)
        if headcount_match:
            try:
                headcount = int(headcount_match.group(1).replace(',', ''))
            except ValueError:
                pass

        percentage_match = PERCENTAGE_PATTERN.search(text)
        if percentage_match:
            try:
                percentage = float(percentage_match.group(1))
            except ValueError:
                pass

        has_numbers = headcount is not None or percentage is not None
        confidence = self._calculate_confidence(
            count, 3, has_numbers, (1 if headcount else 0) + (1 if percentage else 0)
        )

        layoff_details = LayoffDetails(
            headcount=headcount,
            percentage=percentage,
            confidence=confidence
        )

        return DetectedEvent(
            event_type=EventType.LAYOFF,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'headcount': headcount, 'percentage': percentage},
            layoff_details=layoff_details
        )

    def _detect_expansion(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect expansion events."""
        count, matched = self._count_keyword_matches(text_lower, EXPANSION_KEYWORDS)
        if count == 0:
            return None

        locations = entities.get('GPE', [])[:3]

        confidence = self._calculate_confidence(
            count, 3, len(locations) > 0, len(locations)
        )

        expansion_details = ExpansionDetails(
            expansion_type='office' if 'office' in text_lower else 'market',
            location=locations[0] if locations else None,
            confidence=confidence
        )

        return DetectedEvent(
            event_type=EventType.EXPANSION,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'locations': locations},
            expansion_details=expansion_details
        )

    def _detect_product_launch(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect product launch events."""
        count, matched = self._count_keyword_matches(text_lower, PRODUCT_LAUNCH_KEYWORDS)
        if count == 0:
            return None

        confidence = self._calculate_confidence(count, 3, False, 0)

        return DetectedEvent(
            event_type=EventType.PRODUCT_LAUNCH,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={}
        )

    def _detect_partnership(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect partnership events."""
        count, matched = self._count_keyword_matches(text_lower, PARTNERSHIP_KEYWORDS)
        if count == 0:
            return None

        orgs = entities.get('ORG', [])[:3]
        has_multiple_orgs = len(orgs) >= 2

        confidence = self._calculate_confidence(
            count, 3, has_multiple_orgs, len(orgs)
        )

        return DetectedEvent(
            event_type=EventType.PARTNERSHIP,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={'companies': orgs}
        )

    def _detect_negative_news(
        self,
        text: str,
        text_lower: str,
        entities: Dict[str, List[str]]
    ) -> Optional[DetectedEvent]:
        """Detect negative news events."""
        count, matched = self._count_keyword_matches(text_lower, NEGATIVE_NEWS_KEYWORDS)
        if count == 0:
            return None

        confidence = self._calculate_confidence(count, 3, False, 0)

        return DetectedEvent(
            event_type=EventType.NEGATIVE_NEWS,
            confidence=confidence,
            keywords_matched=matched,
            entities_extracted={}
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return self._stats.copy()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "EventDetector",
    # Keyword lists (for testing/inspection)
    "FUNDING_KEYWORDS",
    "MA_KEYWORDS",
    "LEADERSHIP_KEYWORDS",
    "LAYOFF_KEYWORDS",
    "EXPANSION_KEYWORDS",
    "PRODUCT_LAUNCH_KEYWORDS",
    "PARTNERSHIP_KEYWORDS",
    "NEGATIVE_NEWS_KEYWORDS",
]
