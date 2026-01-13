"""
Movement Rules
==============
Business rules for classifying engagement signals and determining transitions.

This module contains the logic for:
- Reply classification (positive, negative, OOO, auto-reply)
- Click threshold evaluation
- Open threshold evaluation
- BIT score calculations
- TalentFlow signal validation
- Re-engagement cycle management
- Appointment detection

Architecture:
- Pure logic implementation (no database access)
- Configurable thresholds
- Classification functions return structured results

Usage:
    from movement_engine.movement_rules import MovementRules

    rules = MovementRules()

    # Classify a reply
    result = rules.classify_reply(reply_text="I'd love to learn more")

    # Check click threshold
    should_promote = rules.check_click_threshold(click_count=2)

    # Calculate BIT score
    score = rules.calculate_bit_score(engagement_data)
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


# =============================================================================
# ENUMS
# =============================================================================

class ReplySentiment(Enum):
    """Classification of reply sentiment."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNSUBSCRIBE = "unsubscribe"
    OUT_OF_OFFICE = "ooo"
    AUTO_REPLY = "auto_reply"
    UNKNOWN = "unknown"


class TalentFlowSignalType(Enum):
    """Types of TalentFlow movement signals."""
    JOB_CHANGE = "job_change"
    PROMOTION = "promotion"
    LATERAL = "lateral"
    STARTUP = "startup"
    COMPANY_CHANGE = "company_change"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ReplyClassification:
    """Result of reply classification."""
    sentiment: ReplySentiment
    should_promote: bool
    confidence: float  # 0.0 to 1.0
    reason: str
    keywords_matched: List[str] = field(default_factory=list)


@dataclass
class ThresholdResult:
    """Result of threshold evaluation."""
    threshold_met: bool
    current_value: int
    threshold_value: int
    excess: int
    reason: str


@dataclass
class BITScoreResult:
    """Result of BIT score calculation."""
    total_score: int
    components: Dict[str, int]
    crossed_warm_threshold: bool
    crossed_hot_threshold: bool
    crossed_priority_threshold: bool
    recency_decay: int


@dataclass
class TalentFlowValidation:
    """Result of TalentFlow signal validation."""
    is_valid: bool
    signal_type: Optional[TalentFlowSignalType]
    is_fresh: bool  # Within 90-day window
    age_days: int
    priority_score: int
    reason: str


@dataclass
class ReengagementStatus:
    """Status of re-engagement cycle."""
    current_cycle: int
    max_cycles: int
    is_exhausted: bool
    days_since_last_engagement: int
    next_trigger_date: Optional[datetime]
    reason: str


@dataclass
class CooldownStatus:
    """Status of cooldown period."""
    is_in_cooldown: bool
    cooldown_until: Optional[datetime]
    hours_remaining: int
    can_bypass: bool
    reason: str


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class MovementRulesConfig:
    """Configuration for movement rules thresholds."""
    # Engagement thresholds
    opens_threshold: int = 3
    clicks_threshold: int = 2

    # BIT score thresholds
    bit_warm_threshold: int = 25
    bit_hot_threshold: int = 50
    bit_priority_threshold: int = 75

    # BIT score weights
    bit_open_points: int = 2
    bit_open_max: int = 10
    bit_click_points: int = 5
    bit_click_max: int = 15
    bit_reply_points: int = 15
    bit_website_points: int = 3
    bit_website_max: int = 12
    bit_content_points: int = 8
    bit_content_max: int = 16
    bit_webinar_points: int = 10
    bit_talentflow_points: int = 20
    bit_recency_decay_per_day: int = 1
    bit_recency_decay_max: int = 30

    # Time windows
    engagement_window_days: int = 30
    talentflow_freshness_days: int = 90
    inactivity_threshold_days: int = 30
    cooldown_hours: int = 24
    event_accumulation_hours: int = 4

    # Re-engagement
    max_reengagement_cycles: int = 3
    reengagement_interval_days: int = 60


# =============================================================================
# MOVEMENT RULES
# =============================================================================

class MovementRules:
    """
    Business rules for movement classification and thresholds.

    This class contains all the logic for evaluating engagement signals
    and determining whether they should trigger state transitions.
    """

    # =========================================================================
    # KEYWORD PATTERNS FOR REPLY CLASSIFICATION
    # =========================================================================

    POSITIVE_KEYWORDS = [
        r'\byes\b', r'\binterested\b', r'\blearn more\b', r'\btell me more\b',
        r'\bsounds good\b', r'\blet\'?s talk\b', r'\bschedule\b', r'\bcall\b',
        r'\bmeeting\b', r'\bdemo\b', r'\bgreat\b', r'\bperfect\b',
        r'\babsolutely\b', r'\bdefinitely\b', r'\bsure\b', r'\bplease\b',
        r'\bsend\b.*\binfo\b', r'\bmore details\b', r'\bhow does\b',
        r'\bwhen can\b', r'\bavailable\b', r'\bfree\b.*\btime\b',
    ]

    NEGATIVE_KEYWORDS = [
        r'\bno\b', r'\bnot interested\b', r'\bno thanks\b', r'\bpass\b',
        r'\bunsubscribe\b', r'\bremove\b', r'\bstop\b', r'\bopt.?out\b',
        r'\bdo not contact\b', r'\bleave me alone\b', r'\bnot for us\b',
        r'\bnot a fit\b', r'\bnot looking\b', r'\balready have\b',
        r'\bwrong person\b', r'\bwrong company\b',
    ]

    UNSUBSCRIBE_KEYWORDS = [
        r'\bunsubscribe\b', r'\bremove me\b', r'\bopt.?out\b',
        r'\bstop.?email\b', r'\btake me off\b', r'\bdo not contact\b',
        r'\bremove from.?list\b', r'\bstop contacting\b',
    ]

    OOO_KEYWORDS = [
        r'\bout of.?office\b', r'\baway from\b', r'\bon vacation\b',
        r'\bon leave\b', r'\blimited access\b', r'\breturn\b.*\bdate\b',
        r'\bback on\b', r'\bback in\b', r'\bwill return\b',
        r'\bautomated response\b', r'\bauto.?reply\b',
    ]

    AUTO_REPLY_KEYWORDS = [
        r'\bthis is an automated\b', r'\bauto.?generated\b',
        r'\bdo not reply\b', r'\bthis mailbox is not monitored\b',
        r'\bunmonitored mailbox\b', r'\bautomatic reply\b',
        r'\bthis email address is not monitored\b',
    ]

    def __init__(self, config: Optional[MovementRulesConfig] = None):
        """
        Initialize MovementRules with configuration.

        Args:
            config: Optional configuration object. Uses defaults if not provided.
        """
        self.config = config or MovementRulesConfig()

    # =========================================================================
    # REPLY CLASSIFICATION
    # =========================================================================

    def classify_reply(
        self,
        reply_text: str,
        subject: Optional[str] = None,
        sender_email: Optional[str] = None
    ) -> ReplyClassification:
        """
        Classify an email reply to determine sentiment and action.

        Args:
            reply_text: The body text of the reply
            subject: Optional subject line
            sender_email: Optional sender email for pattern matching

        Returns:
            ReplyClassification with sentiment and promotion decision
        """
        if not reply_text:
            return ReplyClassification(
                sentiment=ReplySentiment.UNKNOWN,
                should_promote=False,
                confidence=0.0,
                reason="Empty reply text"
            )

        text_lower = reply_text.lower()
        subject_lower = (subject or "").lower()
        combined_text = f"{subject_lower} {text_lower}"

        matched_keywords = []

        # Check for auto-reply first (highest priority)
        for pattern in self.AUTO_REPLY_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched_keywords.append(pattern)
        if matched_keywords:
            return ReplyClassification(
                sentiment=ReplySentiment.AUTO_REPLY,
                should_promote=False,
                confidence=0.9,
                reason="Detected auto-reply pattern",
                keywords_matched=matched_keywords
            )

        # Check for OOO
        matched_keywords = []
        for pattern in self.OOO_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched_keywords.append(pattern)
        if matched_keywords:
            return ReplyClassification(
                sentiment=ReplySentiment.OUT_OF_OFFICE,
                should_promote=False,
                confidence=0.85,
                reason="Detected out-of-office pattern",
                keywords_matched=matched_keywords
            )

        # Check for unsubscribe (compliance priority)
        matched_keywords = []
        for pattern in self.UNSUBSCRIBE_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                matched_keywords.append(pattern)
        if matched_keywords:
            return ReplyClassification(
                sentiment=ReplySentiment.UNSUBSCRIBE,
                should_promote=False,
                confidence=0.95,
                reason="Detected unsubscribe request",
                keywords_matched=matched_keywords
            )

        # Check for negative sentiment
        negative_matches = []
        for pattern in self.NEGATIVE_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                negative_matches.append(pattern)

        # Check for positive sentiment
        positive_matches = []
        for pattern in self.POSITIVE_KEYWORDS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                positive_matches.append(pattern)

        # Score-based classification
        negative_score = len(negative_matches)
        positive_score = len(positive_matches)

        if negative_score > positive_score:
            return ReplyClassification(
                sentiment=ReplySentiment.NEGATIVE,
                should_promote=False,
                confidence=min(0.5 + (negative_score * 0.1), 0.9),
                reason="Negative sentiment detected",
                keywords_matched=negative_matches
            )
        elif positive_score > 0:
            return ReplyClassification(
                sentiment=ReplySentiment.POSITIVE,
                should_promote=True,
                confidence=min(0.5 + (positive_score * 0.1), 0.95),
                reason="Positive sentiment detected",
                keywords_matched=positive_matches
            )
        else:
            # Default to neutral - still promotes (any reply is engagement)
            return ReplyClassification(
                sentiment=ReplySentiment.NEUTRAL,
                should_promote=True,
                confidence=0.5,
                reason="No clear sentiment - treating as neutral engagement"
            )

    # =========================================================================
    # ENGAGEMENT THRESHOLD CHECKS
    # =========================================================================

    def check_open_threshold(
        self,
        open_count: int,
        window_days: Optional[int] = None
    ) -> ThresholdResult:
        """
        Check if email opens meet the threshold for promotion.

        Args:
            open_count: Number of unique opens
            window_days: Time window (uses config default if not provided)

        Returns:
            ThresholdResult indicating if threshold is met
        """
        threshold = self.config.opens_threshold
        met = open_count >= threshold

        return ThresholdResult(
            threshold_met=met,
            current_value=open_count,
            threshold_value=threshold,
            excess=max(0, open_count - threshold),
            reason=f"Opens: {open_count}/{threshold}" + (" (threshold met)" if met else " (below threshold)")
        )

    def check_click_threshold(
        self,
        click_count: int,
        window_days: Optional[int] = None
    ) -> ThresholdResult:
        """
        Check if link clicks meet the threshold for promotion.

        Args:
            click_count: Number of unique clicks
            window_days: Time window (uses config default if not provided)

        Returns:
            ThresholdResult indicating if threshold is met
        """
        threshold = self.config.clicks_threshold
        met = click_count >= threshold

        return ThresholdResult(
            threshold_met=met,
            current_value=click_count,
            threshold_value=threshold,
            excess=max(0, click_count - threshold),
            reason=f"Clicks: {click_count}/{threshold}" + (" (threshold met)" if met else " (below threshold)")
        )

    # =========================================================================
    # BIT SCORE CALCULATION
    # =========================================================================

    def calculate_bit_score(
        self,
        opens: int = 0,
        clicks: int = 0,
        replies: int = 0,
        website_visits: int = 0,
        content_downloads: int = 0,
        webinar_attendance: bool = False,
        has_talentflow_signal: bool = False,
        days_since_last_engagement: int = 0
    ) -> BITScoreResult:
        """
        Calculate BIT (Buyer Intent Tool) score.

        Args:
            opens: Number of email opens
            clicks: Number of link clicks
            replies: Number of email replies
            website_visits: Number of website visits
            content_downloads: Number of content downloads
            webinar_attendance: Whether attended a webinar
            has_talentflow_signal: Whether has TalentFlow signal
            days_since_last_engagement: Days since last engagement event

        Returns:
            BITScoreResult with score breakdown
        """
        components = {}

        # Calculate each component with caps
        components['opens'] = min(opens * self.config.bit_open_points, self.config.bit_open_max)
        components['clicks'] = min(clicks * self.config.bit_click_points, self.config.bit_click_max)
        components['replies'] = self.config.bit_reply_points if replies > 0 else 0
        components['website'] = min(website_visits * self.config.bit_website_points, self.config.bit_website_max)
        components['content'] = min(content_downloads * self.config.bit_content_points, self.config.bit_content_max)
        components['webinar'] = self.config.bit_webinar_points if webinar_attendance else 0
        components['talentflow'] = self.config.bit_talentflow_points if has_talentflow_signal else 0

        # Calculate recency decay
        recency_decay = min(
            days_since_last_engagement * self.config.bit_recency_decay_per_day,
            self.config.bit_recency_decay_max
        )
        components['recency_decay'] = -recency_decay

        # Total score (minimum 0)
        total_score = max(0, sum(components.values()))

        return BITScoreResult(
            total_score=total_score,
            components=components,
            crossed_warm_threshold=total_score >= self.config.bit_warm_threshold,
            crossed_hot_threshold=total_score >= self.config.bit_hot_threshold,
            crossed_priority_threshold=total_score >= self.config.bit_priority_threshold,
            recency_decay=recency_decay
        )

    def check_bit_threshold(
        self,
        bit_score: int,
        threshold_type: str = "warm"
    ) -> ThresholdResult:
        """
        Check if BIT score meets a specific threshold.

        Args:
            bit_score: Current BIT score
            threshold_type: Type of threshold ("warm", "hot", "priority")

        Returns:
            ThresholdResult indicating if threshold is met
        """
        thresholds = {
            "warm": self.config.bit_warm_threshold,
            "hot": self.config.bit_hot_threshold,
            "priority": self.config.bit_priority_threshold
        }

        threshold = thresholds.get(threshold_type, self.config.bit_warm_threshold)
        met = bit_score >= threshold

        return ThresholdResult(
            threshold_met=met,
            current_value=bit_score,
            threshold_value=threshold,
            excess=max(0, bit_score - threshold),
            reason=f"BIT Score: {bit_score}/{threshold} ({threshold_type})" + (" (threshold met)" if met else " (below threshold)")
        )

    # =========================================================================
    # TALENTFLOW SIGNAL VALIDATION
    # =========================================================================

    def validate_talentflow_signal(
        self,
        signal_type: str,
        signal_date: datetime,
        is_verified: bool = False,
        old_company: Optional[str] = None,
        new_company: Optional[str] = None
    ) -> TalentFlowValidation:
        """
        Validate a TalentFlow movement signal.

        Args:
            signal_type: Type of movement (job_change, promotion, etc.)
            signal_date: When the movement occurred
            is_verified: Whether the signal has been verified
            old_company: Previous company (for job change validation)
            new_company: New company (for job change validation)

        Returns:
            TalentFlowValidation with validation result
        """
        now = datetime.now()
        age_days = (now - signal_date).days

        # Check freshness
        is_fresh = age_days <= self.config.talentflow_freshness_days

        # Parse signal type
        try:
            signal_type_enum = TalentFlowSignalType(signal_type.lower())
        except ValueError:
            return TalentFlowValidation(
                is_valid=False,
                signal_type=None,
                is_fresh=is_fresh,
                age_days=age_days,
                priority_score=0,
                reason=f"Unknown signal type: {signal_type}"
            )

        # Calculate priority score
        priority_scores = {
            TalentFlowSignalType.JOB_CHANGE: 100,
            TalentFlowSignalType.STARTUP: 90,
            TalentFlowSignalType.PROMOTION: 70,
            TalentFlowSignalType.LATERAL: 50,
            TalentFlowSignalType.COMPANY_CHANGE: 80,
        }
        priority_score = priority_scores.get(signal_type_enum, 50)

        # Validate job change has different companies
        if signal_type_enum == TalentFlowSignalType.JOB_CHANGE:
            if old_company and new_company and old_company.lower() == new_company.lower():
                return TalentFlowValidation(
                    is_valid=False,
                    signal_type=signal_type_enum,
                    is_fresh=is_fresh,
                    age_days=age_days,
                    priority_score=0,
                    reason="Job change signal has same old and new company"
                )

        # Signal is valid if fresh
        is_valid = is_fresh

        reason = []
        if is_valid:
            reason.append(f"Valid {signal_type_enum.value} signal")
        else:
            reason.append(f"Signal expired ({age_days} days old)")

        if is_verified:
            reason.append("verified")
        else:
            reason.append("unverified")

        return TalentFlowValidation(
            is_valid=is_valid,
            signal_type=signal_type_enum,
            is_fresh=is_fresh,
            age_days=age_days,
            priority_score=priority_score if is_valid else 0,
            reason=", ".join(reason)
        )

    # =========================================================================
    # RE-ENGAGEMENT RULES
    # =========================================================================

    def evaluate_reengagement_status(
        self,
        current_cycle: int,
        days_since_last_engagement: int,
        last_reengagement_date: Optional[datetime] = None
    ) -> ReengagementStatus:
        """
        Evaluate re-engagement cycle status.

        Args:
            current_cycle: Current re-engagement cycle number
            days_since_last_engagement: Days since last engagement
            last_reengagement_date: Date of last re-engagement attempt

        Returns:
            ReengagementStatus with cycle information
        """
        max_cycles = self.config.max_reengagement_cycles
        is_exhausted = current_cycle >= max_cycles

        # Calculate next trigger date
        next_trigger_date = None
        if last_reengagement_date and not is_exhausted:
            next_trigger_date = last_reengagement_date + timedelta(
                days=self.config.reengagement_interval_days
            )

        if is_exhausted:
            reason = f"Re-engagement exhausted after {current_cycle} cycles"
        elif days_since_last_engagement >= self.config.inactivity_threshold_days:
            reason = f"Contact inactive for {days_since_last_engagement} days, eligible for re-engagement"
        else:
            reason = f"Contact active, {days_since_last_engagement} days since last engagement"

        return ReengagementStatus(
            current_cycle=current_cycle,
            max_cycles=max_cycles,
            is_exhausted=is_exhausted,
            days_since_last_engagement=days_since_last_engagement,
            next_trigger_date=next_trigger_date,
            reason=reason
        )

    def check_inactivity_threshold(
        self,
        days_since_last_engagement: int
    ) -> ThresholdResult:
        """
        Check if contact has been inactive long enough to trigger re-engagement.

        Args:
            days_since_last_engagement: Days since last engagement

        Returns:
            ThresholdResult indicating if inactivity threshold is met
        """
        threshold = self.config.inactivity_threshold_days
        met = days_since_last_engagement >= threshold

        return ThresholdResult(
            threshold_met=met,
            current_value=days_since_last_engagement,
            threshold_value=threshold,
            excess=max(0, days_since_last_engagement - threshold),
            reason=f"Inactive: {days_since_last_engagement}/{threshold} days" + (" (threshold met)" if met else " (still active)")
        )

    # =========================================================================
    # COOLDOWN RULES
    # =========================================================================

    def check_cooldown(
        self,
        last_transition_time: Optional[datetime],
        current_time: Optional[datetime] = None
    ) -> CooldownStatus:
        """
        Check if contact is in cooldown period.

        Args:
            last_transition_time: Time of last state transition
            current_time: Current time (uses now if not provided)

        Returns:
            CooldownStatus with cooldown information
        """
        current_time = current_time or datetime.now()

        if last_transition_time is None:
            return CooldownStatus(
                is_in_cooldown=False,
                cooldown_until=None,
                hours_remaining=0,
                can_bypass=True,
                reason="No previous transition, cooldown not applicable"
            )

        cooldown_end = last_transition_time + timedelta(hours=self.config.cooldown_hours)
        is_in_cooldown = current_time < cooldown_end

        if is_in_cooldown:
            hours_remaining = int((cooldown_end - current_time).total_seconds() / 3600)
            return CooldownStatus(
                is_in_cooldown=True,
                cooldown_until=cooldown_end,
                hours_remaining=hours_remaining,
                can_bypass=False,  # Bypass logic handled by MovementEngine
                reason=f"In cooldown for {hours_remaining} more hours"
            )
        else:
            return CooldownStatus(
                is_in_cooldown=False,
                cooldown_until=None,
                hours_remaining=0,
                can_bypass=True,
                reason="Cooldown period has expired"
            )

    # =========================================================================
    # APPOINTMENT DETECTION
    # =========================================================================

    def detect_appointment_signal(
        self,
        reply_text: Optional[str] = None,
        calendar_event_created: bool = False,
        calendly_event_id: Optional[str] = None,
        manual_booking: bool = False
    ) -> Tuple[bool, str]:
        """
        Detect if an appointment has been scheduled.

        Args:
            reply_text: Reply text that might contain meeting confirmation
            calendar_event_created: Whether a calendar event was created
            calendly_event_id: Calendly event ID if booked via Calendly
            manual_booking: Whether manually marked as booked

        Returns:
            Tuple of (is_appointment, reason)
        """
        # Direct booking signals
        if calendly_event_id:
            return True, f"Calendly booking detected: {calendly_event_id}"

        if calendar_event_created:
            return True, "Calendar event created"

        if manual_booking:
            return True, "Manual booking confirmation"

        # Reply-based detection
        if reply_text:
            appointment_patterns = [
                r'\bconfirmed?\b.*\b(meeting|call|appointment)\b',
                r'\b(meeting|call|appointment)\b.*\bconfirmed?\b',
                r'\bsee you\b.*\b(monday|tuesday|wednesday|thursday|friday|tomorrow|next week)\b',
                r'\b(booked|scheduled)\b.*\b(meeting|call|time|slot)\b',
                r'\blooking forward to\b.*\b(meeting|talking|call)\b',
            ]

            text_lower = reply_text.lower()
            for pattern in appointment_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True, f"Appointment language detected in reply"

        return False, "No appointment signal detected"
