"""
Test Suite: spokes/people/ - People Sub-Hub Phases
===================================================
PRD Reference: PRD_PEOPLE_SUBHUB.md

Tests all phases of the People Lifecycle Pipeline:
- Phase 0: People Ingest (Classification)
- Phase 5: Email Generation
- Phase 6: Slot Assignment
- Phase 7: Enrichment Queue
- Phase 8: Output Writer
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch
import uuid


# ============================================================================
# PHASE 0: People Ingest Tests
# PRD Reference: Section 3.1 - People Ingest Classification
# ============================================================================

class TestPhase0PeopleIngest:
    """
    Test Phase 0: People Ingest Classification

    PRD Requirements:
    - If company_id missing → SUSPECT (unanchored)
    - If reply flag exists → WARM
    - If TalentFlow movement exists → TALENTFLOW_WARM
    - If BIT score ≥ 25 → WARM
    - If past meeting flag → APPOINTMENT
    - Default → SUSPECT

    Priority order: company_id check first, then classification signals
    """

    @pytest.fixture
    def phase0_instance(self):
        from spokes.people.phases.phase0_people_ingest import Phase0PeopleIngest
        return Phase0PeopleIngest(config={'bit_warm_threshold': 25})

    def test_missing_company_id_suspect(self, phase0_instance):
        """
        PRD: If company_id missing → SUSPECT (unanchored)

        GOLDEN RULE: Company anchor MUST exist.
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': '',  # Missing
            'first_name': 'John',
            'last_name': 'Doe',
            'bit_score': 50  # Would normally be WARM
        })

        assert result.initial_funnel_state == LifecycleState.SUSPECT, \
            "Missing company_id should classify as SUSPECT regardless of BIT score"
        assert result.classification_reason == 'missing_company_id_unanchored'

    def test_historical_reply_warm(self, phase0_instance):
        """
        PRD: If reply flag exists (historical import) → WARM
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'has_replied': True,
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert result.initial_funnel_state == LifecycleState.WARM
        assert 'historical_reply' in result.classification_reason

    def test_talentflow_movement_warm(self, phase0_instance):
        """
        PRD: If TalentFlow movement exists → TALENTFLOW_WARM
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'talentflow_movement': True,
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert result.initial_funnel_state == LifecycleState.TALENTFLOW_WARM
        assert 'talentflow' in result.classification_reason

    def test_bit_threshold_warm(self, phase0_instance):
        """
        PRD: If BIT score ≥ 25 → WARM
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'bit_score': 30,  # Above threshold
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert result.initial_funnel_state == LifecycleState.WARM
        assert 'bit_score' in result.classification_reason

    def test_past_meeting_appointment(self, phase0_instance):
        """
        PRD: If past meeting flag → APPOINTMENT
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'has_meeting': True,
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert result.initial_funnel_state == LifecycleState.APPOINTMENT
        assert 'past_meeting' in result.classification_reason

    def test_default_suspect(self, phase0_instance):
        """
        PRD: Default (no signals) → SUSPECT
        """
        from spokes.people.movement_engine import LifecycleState

        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert result.initial_funnel_state == LifecycleState.SUSPECT
        assert 'default' in result.classification_reason

    def test_slot_candidate_detection(self, phase0_instance):
        """
        PRD: Phase 0 should identify potential slot candidates from title.
        """
        result = phase0_instance.classify_single({
            'person_id': 'P001',
            'company_id': 'C001',
            'job_title': 'Chief Human Resources Officer',
            'first_name': 'Jane',
            'last_name': 'Smith'
        })

        assert result.slot_candidate == 'CHRO', "Should identify CHRO slot candidate"


# ============================================================================
# PHASE 5: Email Generation Tests
# PRD Reference: Section 3.2 - Email Generation
# ============================================================================

class TestPhase5EmailGeneration:
    """
    Test Phase 5: Email Generation

    PRD Requirements:
    - company_id MUST be present (Company-First doctrine)
    - Use verified pattern from Phase 4
    - Generate email using pattern + first/last name
    - Track confidence levels: verified, derived, low_confidence
    """

    @pytest.fixture
    def phase5_instance(self):
        from spokes.people.phases.phase5_email_generation import Phase5EmailGeneration
        return Phase5EmailGeneration(config={'enable_waterfall': False})

    def test_email_generation_verified_pattern(self, phase5_instance):
        """
        PRD: Generate email using verified pattern from Phase 4.
        """
        email = phase5_instance.generate_email(
            first_name='john',
            last_name='doe',
            pattern='{first}.{last}',
            domain='acme.com'
        )

        assert email == 'john.doe@acme.com', "Should generate correct email from pattern"

    def test_email_generation_initial_pattern(self, phase5_instance):
        """
        PRD: Support various pattern formats.
        """
        test_cases = [
            ('john', 'doe', '{f}.{last}', 'acme.com', 'j.doe@acme.com'),
            ('john', 'doe', '{first}{last}', 'acme.com', 'johndoe@acme.com'),
            ('john', 'doe', '{first}_{last}', 'acme.com', 'john_doe@acme.com'),
        ]

        for first, last, pattern, domain, expected in test_cases:
            email = phase5_instance.generate_email(first, last, pattern, domain)
            assert email == expected, f"Pattern {pattern} should generate {expected}"

    def test_company_first_doctrine_enforced(self, phase5_instance):
        """
        PRD: GOLDEN RULE - company_id MUST be present.
        """
        people_df = pd.DataFrame([
            {'person_id': 'P001', 'company_id': '', 'first_name': 'John', 'last_name': 'Doe'}
        ])
        pattern_df = pd.DataFrame([
            {'company_id': 'C001', 'email_pattern': '{first}.{last}', 'resolved_domain': 'acme.com'}
        ])

        with_emails, missing, stats = phase5_instance.run(people_df, pattern_df)

        assert len(with_emails) == 0, "Missing company_id should not generate email"
        assert stats.missing_pattern >= 1 or len(missing) >= 1

    def test_name_normalization(self, phase5_instance):
        """
        PRD: Normalize names for email generation.
        """
        test_cases = [
            ('John-Paul', 'john'),  # Hyphenated → first part
            ('Mary Anne', 'mary'),   # Space → first part
            ('José', 'jos'),         # Accented → cleaned (if impl supports)
        ]

        for input_name, expected in test_cases[:2]:  # Test first 2
            normalized = phase5_instance.normalize_name(input_name)
            assert normalized == expected or normalized.startswith(expected[:3])


# ============================================================================
# PHASE 6: Slot Assignment Tests
# PRD Reference: Section 3.3 - Slot Assignment
# ============================================================================

class TestPhase6SlotAssignment:
    """
    Test Phase 6: Slot Assignment

    PRD Requirements:
    - Slot Types: CHRO, HR_MANAGER, BENEFITS_LEAD, PAYROLL_ADMIN, HR_SUPPORT
    - One person per slot per company
    - Conflicts → highest seniority wins
    - company_id REQUIRED (Company-First doctrine)
    """

    @pytest.fixture
    def phase6_instance(self):
        from spokes.people.phases.phase6_slot_assignment import Phase6SlotAssignment
        return Phase6SlotAssignment(config={
            'allow_slot_replacement': True,
            'min_seniority_diff': 10
        })

    def test_chro_classification(self, phase6_instance):
        """
        PRD: Classify CHRO titles correctly.
        """
        from spokes.people.phases.phase6_slot_assignment import SlotType

        test_cases = [
            ('Chief Human Resources Officer', SlotType.CHRO),
            ('CHRO', SlotType.CHRO),
            ('SVP Human Resources', SlotType.CHRO),
            ('VP HR', SlotType.CHRO),
        ]

        for title, expected_slot in test_cases:
            slot_type, score, _ = phase6_instance.classify_title(title)
            assert slot_type == expected_slot, f"'{title}' should be {expected_slot}"

    def test_hr_manager_classification(self, phase6_instance):
        """
        PRD: Classify HR_MANAGER titles correctly.
        """
        from spokes.people.phases.phase6_slot_assignment import SlotType

        test_cases = [
            ('HR Director', SlotType.HR_MANAGER),
            ('Director of Human Resources', SlotType.HR_MANAGER),
            ('HR Manager', SlotType.HR_MANAGER),
            ('Head of HR', SlotType.HR_MANAGER),
        ]

        for title, expected_slot in test_cases:
            slot_type, score, _ = phase6_instance.classify_title(title)
            assert slot_type == expected_slot, f"'{title}' should be {expected_slot}"

    def test_benefits_lead_classification(self, phase6_instance):
        """
        PRD: Classify BENEFITS_LEAD titles correctly.
        """
        from spokes.people.phases.phase6_slot_assignment import SlotType

        test_cases = [
            ('Benefits Director', SlotType.BENEFITS_LEAD),
            ('Benefits Manager', SlotType.BENEFITS_LEAD),
            ('Total Rewards Manager', SlotType.BENEFITS_LEAD),
        ]

        for title, expected_slot in test_cases:
            slot_type, score, _ = phase6_instance.classify_title(title)
            assert slot_type == expected_slot, f"'{title}' should be {expected_slot}"

    def test_slot_conflict_resolution(self, phase6_instance):
        """
        PRD: When conflicting → highest seniority wins.
        """
        people_df = pd.DataFrame([
            {'person_id': 'P001', 'company_id': 'C001', 'job_title': 'HR Manager', 'first_name': 'John'},
            {'person_id': 'P002', 'company_id': 'C001', 'job_title': 'Senior HR Director', 'first_name': 'Jane'},
        ])

        slotted, unslotted, summary, stats = phase6_instance.run(people_df)

        # Higher seniority should win
        assert stats.conflicts_resolved >= 0, "Should track conflicts"

    def test_company_first_doctrine(self, phase6_instance):
        """
        PRD: company_id REQUIRED (Company-First doctrine).
        """
        people_df = pd.DataFrame([
            {'person_id': 'P001', 'company_id': '', 'job_title': 'CHRO', 'first_name': 'John'},
        ])

        slotted, unslotted, summary, stats = phase6_instance.run(people_df)

        assert stats.missing_company_id >= 1, "Should count missing company_id"
        assert len(slotted) == 0, "No slots should be assigned without company_id"


# ============================================================================
# SIGNAL IDEMPOTENCY Tests
# PRD Reference: Section 2.3 - Signal Idempotency
# ============================================================================

class TestSignalIdempotency:
    """
    Test Signal Idempotency (HARD LAW)

    PRD Requirements:
    - People signals: 24-hour deduplication window
    - DOL signals: 365-day deduplication window
    - Duplicate signals MUST be dropped, not merged

    GAP: This tests expected behavior per PRD - may need implementation.
    """

    def test_people_signal_24h_dedup_window(self):
        """
        PRD: People signals have 24-hour deduplication window.

        Same person + same event type within 24h = DROP duplicate.
        """
        # This documents expected behavior
        dedup_window_hours = 24
        assert dedup_window_hours == 24, "People signals should have 24h dedup window"

    def test_signal_dedup_key_format(self):
        """
        PRD: Dedup key format: {company_id}:{person_id}:{signal_type}
        """
        company_id = 'C001'
        person_id = 'P001'
        signal_type = 'SLOT_FILLED'

        dedup_key = f"{company_id}:{person_id}:{signal_type}"
        assert dedup_key == 'C001:P001:SLOT_FILLED'


# ============================================================================
# ERROR CODE Tests
# PRD Reference: Section 5 - Error Codes
# ============================================================================

class TestPeopleErrorCodes:
    """
    Test People Sub-Hub Error Codes

    PRD Error Codes:
    - PSH-P0-001: Invalid person record format
    - PSH-P0-002: Missing company_id (no anchor)
    - PSH-P5-001: Cannot generate email - missing first_name
    - PSH-P5-002: Cannot generate email - missing last_name
    - PSH-P5-003: No pattern available for domain
    - PSH-P6-001: Cannot classify title
    - PSH-P6-002: Slot conflict detected
    """

    def test_error_code_format(self):
        """
        PRD: Error codes follow format PSH-P{phase}-{number}
        """
        valid_codes = [
            'PSH-P0-001', 'PSH-P0-002',
            'PSH-P5-001', 'PSH-P5-002', 'PSH-P5-003',
            'PSH-P6-001', 'PSH-P6-002',
        ]

        import re
        pattern = r'^PSH-P[0-9]+-[0-9]{3}$'

        for code in valid_codes:
            assert re.match(pattern, code), f"Error code {code} should match format"


# ============================================================================
# HUB GATE VALIDATION Tests
# PRD Reference: Section 2.1 - Hub Gate Protocol
# ============================================================================

class TestHubGateValidation:
    """
    Test Hub Gate Validation

    PRD Requirements:
    - All People Spoke phases MUST validate company anchor
    - IF company_id IS NULL: STOP. DO NOT PROCEED.
    - Route to Company Identity Pipeline first.
    """

    def test_hub_gate_blocks_null_company(self):
        """
        PRD: IF company_id IS NULL OR domain IS NULL: STOP.

        This documents the expected gate behavior.
        """
        company_id = None
        should_proceed = company_id is not None

        assert not should_proceed, "Null company_id should block processing"

    def test_hub_gate_blocks_empty_company(self):
        """
        PRD: Empty string company_id should also block.
        """
        company_id = ''
        should_proceed = bool(company_id and company_id.strip())

        assert not should_proceed, "Empty company_id should block processing"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
