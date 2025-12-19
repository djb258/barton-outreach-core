"""
Phase 6: Slot Assignment
========================
Assigns people to company HR slots based on title classification.
Links slot assignments to company_id (Company Hub anchor).

Slot Types (HR-focused):
- CHRO: Chief HR Officer, VP HR, SVP HR (Executive level)
- HR_MANAGER: HR Manager, HR Director, HR Lead
- BENEFITS_LEAD: Benefits Manager, Benefits Director, Benefits Admin
- PAYROLL_ADMIN: Payroll Manager, Payroll Director, Payroll Specialist
- HR_SUPPORT: HR Coordinator, HR Specialist, HR Generalist
- UNSLOTTED: Could not classify

Slot Rules:
- One person per slot per company
- If conflicting → highest seniority wins
- Empty slots → recorded in slot_enrichment_queue
- REQUIRES: company_id anchor (Company-First doctrine)

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
- hub_gate validation - company_id REQUIRED
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor, GateLevel


class SlotType(Enum):
    """Valid slot types for HR positions (seniority order)."""
    CHRO = "CHRO"                    # Chief HR Officer (highest)
    HR_MANAGER = "HR_MANAGER"        # HR Manager/Director
    BENEFITS_LEAD = "BENEFITS_LEAD"  # Benefits Manager
    PAYROLL_ADMIN = "PAYROLL_ADMIN"  # Payroll Manager
    HR_SUPPORT = "HR_SUPPORT"        # HR Coordinator/Specialist
    UNSLOTTED = "UNSLOTTED"          # Cannot classify

    @classmethod
    def seniority_rank(cls, slot_type: 'SlotType') -> int:
        """Return seniority rank (higher = more senior)."""
        ranks = {
            cls.CHRO: 100,
            cls.HR_MANAGER: 80,
            cls.BENEFITS_LEAD: 60,
            cls.PAYROLL_ADMIN: 50,
            cls.HR_SUPPORT: 30,
            cls.UNSLOTTED: 0
        }
        return ranks.get(slot_type, 0)


@dataclass
class SlotAssignment:
    """Result of slot assignment."""
    person_id: str
    company_id: str
    slot_type: SlotType
    title: str
    title_normalized: str
    seniority_score: int = 0
    assignment_reason: str = ""
    replaced_person_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Phase6Stats:
    """Statistics for Phase 6 execution."""
    total_input: int = 0
    slots_assigned: int = 0
    chro_count: int = 0
    hr_manager_count: int = 0
    benefits_lead_count: int = 0
    payroll_admin_count: int = 0
    hr_support_count: int = 0
    unslotted_count: int = 0
    conflicts_resolved: int = 0
    missing_company_id: int = 0
    missing_title: int = 0
    hub_gate_failures: int = 0
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase6SlotAssignment:
    """
    Phase 6: Assign people to company HR slots.

    Uses deterministic keyword-based classification.
    No fuzzy matching - exact keyword presence only.

    Movement Engine Integration:
    - Triggers movement if slot assignment changes seniority
    - Reports EventType.MOVEMENT_WARM_ENGAGEMENT for slot assignments

    REQUIRES: company_id anchor (Company-First doctrine)
    """

    # Title classification patterns (ORDER MATTERS - checked first to last)
    # Each pattern: (keywords, slot_type, seniority_score)
    TITLE_PATTERNS = [
        # CHRO - Executive HR (highest priority)
        (["chief human resources", "chief people", "chro", "cpo"], SlotType.CHRO, 100),
        (["svp hr", "svp human resources", "svp people"], SlotType.CHRO, 95),
        (["senior vice president hr", "senior vice president human resources"], SlotType.CHRO, 95),
        (["evp hr", "evp human resources", "evp people"], SlotType.CHRO, 95),
        (["executive vice president hr", "executive vice president human resources"], SlotType.CHRO, 95),
        (["vp hr", "vp human resources", "vp people", "vice president hr"], SlotType.CHRO, 90),
        (["vp of hr", "vp of human resources", "vice president of hr"], SlotType.CHRO, 90),

        # HR_MANAGER - Director/Manager level
        (["hr director", "human resources director", "director of hr"], SlotType.HR_MANAGER, 80),
        (["director human resources", "director of human resources"], SlotType.HR_MANAGER, 80),
        (["people director", "director of people"], SlotType.HR_MANAGER, 78),
        (["hr manager", "human resources manager", "manager of hr"], SlotType.HR_MANAGER, 75),
        (["hr lead", "human resources lead", "hr team lead"], SlotType.HR_MANAGER, 72),
        (["head of hr", "head of human resources", "hr head"], SlotType.HR_MANAGER, 85),
        (["people operations manager", "people ops manager"], SlotType.HR_MANAGER, 73),
        (["talent director", "talent acquisition director"], SlotType.HR_MANAGER, 76),

        # BENEFITS_LEAD - Benefits focused
        (["benefits director", "director of benefits"], SlotType.BENEFITS_LEAD, 70),
        (["vp benefits", "vice president benefits"], SlotType.BENEFITS_LEAD, 85),
        (["benefits manager", "manager of benefits"], SlotType.BENEFITS_LEAD, 65),
        (["benefits lead", "benefits team lead"], SlotType.BENEFITS_LEAD, 62),
        (["benefits administrator", "benefits admin"], SlotType.BENEFITS_LEAD, 55),
        (["benefits coordinator"], SlotType.BENEFITS_LEAD, 50),
        (["benefits specialist"], SlotType.BENEFITS_LEAD, 48),
        (["compensation and benefits", "compensation & benefits"], SlotType.BENEFITS_LEAD, 68),
        (["total rewards"], SlotType.BENEFITS_LEAD, 72),

        # PAYROLL_ADMIN - Payroll focused
        (["payroll director", "director of payroll"], SlotType.PAYROLL_ADMIN, 70),
        (["vp payroll", "vice president payroll"], SlotType.PAYROLL_ADMIN, 85),
        (["payroll manager", "manager of payroll"], SlotType.PAYROLL_ADMIN, 65),
        (["payroll lead", "payroll team lead"], SlotType.PAYROLL_ADMIN, 60),
        (["payroll administrator", "payroll admin"], SlotType.PAYROLL_ADMIN, 55),
        (["payroll coordinator"], SlotType.PAYROLL_ADMIN, 50),
        (["payroll specialist"], SlotType.PAYROLL_ADMIN, 48),
        (["payroll analyst"], SlotType.PAYROLL_ADMIN, 45),

        # HR_SUPPORT - Generalist/Coordinator level
        (["hr coordinator", "human resources coordinator"], SlotType.HR_SUPPORT, 45),
        (["hr specialist", "human resources specialist"], SlotType.HR_SUPPORT, 48),
        (["hr generalist", "human resources generalist"], SlotType.HR_SUPPORT, 50),
        (["hr associate", "human resources associate"], SlotType.HR_SUPPORT, 40),
        (["hr assistant", "human resources assistant"], SlotType.HR_SUPPORT, 35),
        (["hr analyst", "human resources analyst"], SlotType.HR_SUPPORT, 47),
        (["hr business partner", "hrbp"], SlotType.HR_SUPPORT, 55),
        (["people coordinator", "people specialist"], SlotType.HR_SUPPORT, 45),
        (["talent coordinator", "talent specialist"], SlotType.HR_SUPPORT, 45),
        (["recruiting coordinator", "recruitment coordinator"], SlotType.HR_SUPPORT, 42),
        (["recruiter", "talent acquisition"], SlotType.HR_SUPPORT, 45),
    ]

    def __init__(self, config: Dict[str, Any] = None, movement_engine=None):
        """
        Initialize Phase 6.

        Args:
            config: Configuration dictionary with:
                - allow_slot_replacement: Whether to allow replacing existing (default: True)
                - min_seniority_diff: Min score diff to replace existing (default: 10)
            movement_engine: Optional MovementEngine instance for event reporting
        """
        self.config = config or {}
        self.allow_slot_replacement = self.config.get('allow_slot_replacement', True)
        self.min_seniority_diff = self.config.get('min_seniority_diff', 10)
        self.movement_engine = movement_engine

    def run(self, people_with_emails_df: pd.DataFrame,
            correlation_id: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Phase6Stats]:
        """
        Run slot assignment phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            people_with_emails_df: DataFrame with generated emails from Phase 5
                Required columns: person_id, company_id, first_name, last_name,
                                 job_title (or title), generated_email
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            Tuple of:
                - slotted_people_df: People with slot assignments
                - unslotted_people_df: People that couldn't be slotted
                - slot_summary_df: Summary of slots by company
                - Phase6Stats

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "people.lifecycle.slotting.phase6"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 6")

        start_time = time.time()
        stats = Phase6Stats(total_input=len(people_with_emails_df), correlation_id=correlation_id)

        # Track slot assignments by company
        # company_id -> {slot_type -> SlotAssignment}
        company_slots: Dict[str, Dict[SlotType, SlotAssignment]] = {}

        slotted_records = []
        unslotted_records = []

        for idx, row in people_with_emails_df.iterrows():
            person_id = str(row.get('person_id', idx))
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            title = str(row.get('job_title', '') or row.get('title', '') or '').strip()

            # HUB GATE: Validate company anchor (Company-First doctrine)
            gate_result = validate_company_anchor(
                record=row.to_dict(),
                level=GateLevel.COMPANY_ID_ONLY,
                process_id=process_id,
                correlation_id=correlation_id,
                fail_hard=False  # Phase 6 routes failures to unslotted
            )

            if not gate_result.passed:
                stats.hub_gate_failures += 1
                stats.missing_company_id += 1
                unslotted_records.append({
                    **row.to_dict(),
                    'slot_type': SlotType.UNSLOTTED.value,
                    'slot_reason': 'hub_gate_failed_no_company_id',
                    'seniority_score': 0,
                    'hub_gate_failure': gate_result.failure_reason
                })
                continue

            # Check for title
            if not title:
                stats.missing_title += 1
                unslotted_records.append({
                    **row.to_dict(),
                    'slot_type': SlotType.UNSLOTTED.value,
                    'slot_reason': 'missing_title',
                    'seniority_score': 0
                })
                continue

            # Classify title
            slot_type, seniority_score, title_normalized = self.classify_title(title)

            # Initialize company slots if needed
            if company_id not in company_slots:
                company_slots[company_id] = {}

            # Handle slot assignment
            if slot_type == SlotType.UNSLOTTED:
                stats.unslotted_count += 1
                unslotted_records.append({
                    **row.to_dict(),
                    'slot_type': SlotType.UNSLOTTED.value,
                    'slot_reason': 'title_not_recognized',
                    'seniority_score': seniority_score,
                    'title_normalized': title_normalized
                })
                continue

            # Check for existing slot holder
            existing = company_slots[company_id].get(slot_type)

            if existing is None:
                # Slot is empty - assign directly
                assignment = SlotAssignment(
                    person_id=person_id,
                    company_id=company_id,
                    slot_type=slot_type,
                    title=title,
                    title_normalized=title_normalized,
                    seniority_score=seniority_score,
                    assignment_reason='first_assignment'
                )
                company_slots[company_id][slot_type] = assignment
                self._update_slot_stats(stats, slot_type)

                slotted_records.append({
                    **row.to_dict(),
                    'slot_type': slot_type.value,
                    'slot_reason': 'assigned',
                    'seniority_score': seniority_score,
                    'title_normalized': title_normalized,
                    'replaced_person_id': None
                })

                # Report movement event for slot assignment
                # Phase 6 triggers movement for slot assignments
                self._report_slot_assignment_event(
                    company_id=company_id,
                    person_id=person_id,
                    slot_type=slot_type,
                    seniority_score=seniority_score,
                    is_replacement=False
                )

            else:
                # Slot already filled - check if should replace
                should_replace, reason = self._should_replace(
                    new_score=seniority_score,
                    existing_score=existing.seniority_score
                )

                if should_replace:
                    stats.conflicts_resolved += 1

                    # Replace existing holder
                    old_person_id = existing.person_id
                    assignment = SlotAssignment(
                        person_id=person_id,
                        company_id=company_id,
                        slot_type=slot_type,
                        title=title,
                        title_normalized=title_normalized,
                        seniority_score=seniority_score,
                        assignment_reason=reason,
                        replaced_person_id=old_person_id
                    )
                    company_slots[company_id][slot_type] = assignment

                    slotted_records.append({
                        **row.to_dict(),
                        'slot_type': slot_type.value,
                        'slot_reason': reason,
                        'seniority_score': seniority_score,
                        'title_normalized': title_normalized,
                        'replaced_person_id': old_person_id
                    })

                    # Report movement event for slot replacement
                    # Phase 6 triggers movement when seniority changes
                    self._report_slot_assignment_event(
                        company_id=company_id,
                        person_id=person_id,
                        slot_type=slot_type,
                        seniority_score=seniority_score,
                        is_replacement=True,
                        replaced_person_id=old_person_id
                    )

                    # Previous holder becomes unslotted
                    # Note: We don't have the original row for the replaced person
                    # They'll need to be tracked separately if needed

                else:
                    # Keep existing holder - new person is unslotted
                    unslotted_records.append({
                        **row.to_dict(),
                        'slot_type': SlotType.UNSLOTTED.value,
                        'slot_reason': 'slot_occupied_by_senior',
                        'seniority_score': seniority_score,
                        'title_normalized': title_normalized,
                        'existing_holder_id': existing.person_id
                    })

        # Calculate total slots assigned
        stats.slots_assigned = (
            stats.chro_count + stats.hr_manager_count +
            stats.benefits_lead_count + stats.payroll_admin_count +
            stats.hr_support_count
        )

        # Build output DataFrames
        slotted_df = pd.DataFrame(slotted_records) if slotted_records else pd.DataFrame()
        unslotted_df = pd.DataFrame(unslotted_records) if unslotted_records else pd.DataFrame()

        # Build slot summary by company
        slot_summary = self._build_slot_summary(company_slots)
        slot_summary_df = pd.DataFrame(slot_summary) if slot_summary else pd.DataFrame()

        stats.duration_seconds = time.time() - start_time

        return slotted_df, unslotted_df, slot_summary_df, stats

    def classify_title(self, title: str) -> Tuple[SlotType, int, str]:
        """
        Classify job title to slot type using deterministic keyword matching.

        Args:
            title: Job title to classify

        Returns:
            Tuple of (SlotType, seniority_score, normalized_title)
        """
        if not title:
            return SlotType.UNSLOTTED, 0, ""

        # Normalize title
        title_normalized = self._normalize_title(title)

        # Check each pattern group (order matters - more specific first)
        for keywords, slot_type, base_score in self.TITLE_PATTERNS:
            for keyword in keywords:
                if keyword in title_normalized:
                    # Adjust score based on additional seniority indicators
                    adjusted_score = self._adjust_seniority_score(title_normalized, base_score)
                    return slot_type, adjusted_score, title_normalized

        # No match found
        return SlotType.UNSLOTTED, 0, title_normalized

    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for matching.

        Args:
            title: Raw job title

        Returns:
            Normalized title (lowercase, cleaned)
        """
        if not title:
            return ""

        # Lowercase
        normalized = title.lower().strip()

        # Replace common abbreviations
        replacements = {
            "sr.": "senior",
            "sr ": "senior ",
            "jr.": "junior",
            "jr ": "junior ",
            "mgr": "manager",
            "dir": "director",
            "coord": "coordinator",
            "spec": "specialist",
            "admin": "administrator",
            "asst": "assistant",
            "exec": "executive",
            "vp": "vp",  # Keep as-is for pattern matching
            "svp": "svp",
            "evp": "evp",
        }

        for abbrev, full in replacements.items():
            normalized = normalized.replace(abbrev, full)

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized.strip()

    def _adjust_seniority_score(self, title_normalized: str, base_score: int) -> int:
        """
        Adjust seniority score based on modifiers in title.

        Args:
            title_normalized: Normalized title
            base_score: Base score from pattern match

        Returns:
            Adjusted seniority score
        """
        score = base_score

        # Senior modifiers (increase score)
        if any(mod in title_normalized for mod in ["senior", "lead", "head"]):
            score += 5

        if "global" in title_normalized or "corporate" in title_normalized:
            score += 3

        if "regional" in title_normalized or "area" in title_normalized:
            score += 2

        # Junior modifiers (decrease score)
        if any(mod in title_normalized for mod in ["junior", "entry", "intern"]):
            score -= 10

        if "assistant" in title_normalized or "associate" in title_normalized:
            score -= 5

        return max(0, min(100, score))  # Clamp to 0-100

    def _should_replace(self, new_score: int, existing_score: int) -> Tuple[bool, str]:
        """
        Determine if new person should replace existing slot holder.

        Args:
            new_score: New person's seniority score
            existing_score: Existing holder's seniority score

        Returns:
            Tuple of (should_replace, reason)
        """
        if not self.allow_slot_replacement:
            return False, "replacement_disabled"

        score_diff = new_score - existing_score

        if score_diff >= self.min_seniority_diff:
            return True, f"higher_seniority_by_{score_diff}"

        return False, "existing_holder_kept"

    def _update_slot_stats(self, stats: Phase6Stats, slot_type: SlotType):
        """Update statistics for slot type."""
        if slot_type == SlotType.CHRO:
            stats.chro_count += 1
        elif slot_type == SlotType.HR_MANAGER:
            stats.hr_manager_count += 1
        elif slot_type == SlotType.BENEFITS_LEAD:
            stats.benefits_lead_count += 1
        elif slot_type == SlotType.PAYROLL_ADMIN:
            stats.payroll_admin_count += 1
        elif slot_type == SlotType.HR_SUPPORT:
            stats.hr_support_count += 1

    def _build_slot_summary(self, company_slots: Dict[str, Dict[SlotType, SlotAssignment]]) -> List[Dict[str, Any]]:
        """
        Build slot summary by company.

        Args:
            company_slots: Mapping of company_id to slot assignments

        Returns:
            List of summary records
        """
        summary = []

        for company_id, slots in company_slots.items():
            record = {
                'company_id': company_id,
                'has_chro': SlotType.CHRO in slots,
                'has_hr_manager': SlotType.HR_MANAGER in slots,
                'has_benefits_lead': SlotType.BENEFITS_LEAD in slots,
                'has_payroll_admin': SlotType.PAYROLL_ADMIN in slots,
                'has_hr_support': SlotType.HR_SUPPORT in slots,
                'total_slots_filled': len(slots),
                'missing_slots': [],
            }

            # Identify missing slots
            for slot_type in [SlotType.CHRO, SlotType.HR_MANAGER, SlotType.BENEFITS_LEAD,
                            SlotType.PAYROLL_ADMIN, SlotType.HR_SUPPORT]:
                if slot_type not in slots:
                    record['missing_slots'].append(slot_type.value)

            record['missing_slots'] = ','.join(record['missing_slots'])
            summary.append(record)

        return summary

    def get_empty_slots(self, slot_summary_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract companies with empty slots for enrichment queue.

        Args:
            slot_summary_df: Slot summary from run()

        Returns:
            DataFrame with companies and their missing slots
        """
        if slot_summary_df is None or len(slot_summary_df) == 0:
            return pd.DataFrame()

        # Filter to companies with missing slots
        has_missing = slot_summary_df[slot_summary_df['missing_slots'] != '']

        queue_records = []
        for idx, row in has_missing.iterrows():
            company_id = row['company_id']
            missing = row['missing_slots'].split(',')

            for slot in missing:
                if slot:
                    # Determine priority based on slot type
                    priority = self._get_slot_priority(slot)
                    queue_records.append({
                        'company_id': company_id,
                        'missing_slot': slot,
                        'priority': priority,
                        'queue_reason': 'empty_slot'
                    })

        return pd.DataFrame(queue_records) if queue_records else pd.DataFrame()

    def _get_slot_priority(self, slot_type_str: str) -> str:
        """
        Get priority for missing slot.

        Args:
            slot_type_str: Slot type as string

        Returns:
            Priority level (HIGH, MEDIUM, LOW)
        """
        high_priority = ['CHRO', 'BENEFITS_LEAD']
        medium_priority = ['HR_MANAGER', 'PAYROLL_ADMIN']

        if slot_type_str in high_priority:
            return 'HIGH'
        elif slot_type_str in medium_priority:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _report_slot_assignment_event(
        self,
        company_id: str,
        person_id: str,
        slot_type: SlotType,
        seniority_score: int,
        is_replacement: bool = False,
        replaced_person_id: str = None
    ) -> None:
        """
        Report movement event for slot assignment.

        Phase 6 triggers movement if slot assignment changes seniority.
        This signals to the Movement Engine that the person has been slotted
        and may qualify for state advancement based on their role.

        Args:
            company_id: Company anchor ID
            person_id: Person unique ID
            slot_type: Assigned slot type
            seniority_score: Seniority score for this assignment
            is_replacement: Whether this replaced an existing slot holder
            replaced_person_id: ID of person who was replaced (if any)
        """
        if not self.movement_engine:
            return

        try:
            # High-seniority slots (CHRO, HR_MANAGER) indicate warmer contacts
            event_metadata = {
                'phase': 6,
                'slot_type': slot_type.value,
                'seniority_score': seniority_score,
                'is_replacement': is_replacement,
                'event_category': 'MOVEMENT_WARM_ENGAGEMENT'
            }

            if replaced_person_id:
                event_metadata['replaced_person_id'] = replaced_person_id

            # Report slot assignment event
            self.movement_engine.detect_event(
                company_id=company_id,
                person_id=person_id,
                event_type='slot_assigned',
                metadata=event_metadata
            )
        except Exception:
            # Don't fail slot assignment due to movement event errors
            pass


def assign_slots(people_with_emails_df: pd.DataFrame,
                config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Phase6Stats]:
    """
    Convenience function to run slot assignment.

    Args:
        people_with_emails_df: DataFrame with people and emails from Phase 5
        config: Optional configuration

    Returns:
        Tuple of (slotted_df, unslotted_df, slot_summary_df, Phase6Stats)
    """
    phase6 = Phase6SlotAssignment(config=config)
    return phase6.run(people_with_emails_df)
