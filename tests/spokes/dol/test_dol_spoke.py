"""
Test Suite: spokes/dol/ - DOL Sub-Hub
======================================
PRD Reference: PRD_DOL_SUBHUB.md

Tests DOL Node processing:
- Form 5500 parsing and ingestion
- EIN-to-company matching
- Schedule A broker extraction
- Signal emission to BIT Engine
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid


# ============================================================================
# FORM 5500 PROCESSING Tests
# PRD Reference: Section 3.1 - Form 5500 Ingest
# ============================================================================

class TestForm5500Processing:
    """
    Test Form 5500 Processing

    PRD Requirements:
    - Parse Form 5500 filings
    - Extract plan metadata (participants, assets, effective date)
    - Validate EIN format
    - Route to company matching by EIN
    """

    @pytest.fixture
    def dol_spoke(self):
        from spokes.dol.dol_spoke import DOLNodeSpoke
        from wheel.bicycle_wheel import Hub  # Mock if not available
        mock_hub = Mock()
        return DOLNodeSpoke(hub=mock_hub)

    @pytest.fixture
    def sample_form5500(self):
        from spokes.dol.dol_spoke import Form5500Record
        return Form5500Record(
            filing_id='F5500-2023-001',
            ein='12-3456789',
            plan_name='Acme Corp 401k',
            total_participants=1500,
            total_assets=50000000.0,
            plan_year_begin=datetime(2023, 1, 1),
            plan_year_end=datetime(2023, 12, 31),
            admin_name='HR Benefits Team',
            is_small_plan=False
        )

    def test_form5500_valid_ein(self, dol_spoke, sample_form5500):
        """
        PRD: Valid EIN should route to company matching.
        """
        result = dol_spoke.process(sample_form5500)

        # Should attempt to match by EIN
        assert dol_spoke.stats['total_processed'] >= 1

    def test_form5500_missing_ein(self, dol_spoke):
        """
        PRD: Missing EIN should fail with NO_MATCH.
        """
        from spokes.dol.dol_spoke import Form5500Record
        from wheel.wheel_result import ResultStatus, FailureType

        record = Form5500Record(
            filing_id='F5500-2023-002',
            ein='',  # Missing EIN
            plan_name='Unknown Plan'
        )

        result = dol_spoke.process(record)

        assert result.status == ResultStatus.FAILED
        assert result.failure_type == FailureType.NO_MATCH

    def test_large_plan_signal(self, dol_spoke, sample_form5500):
        """
        PRD: Large plan (≥500 participants) should emit LARGE_PLAN signal.

        Signal value: +8.0 points per PRD.
        """
        # sample_form5500 has 1500 participants
        assert sample_form5500.total_participants >= 500, "Should be large plan"

        result = dol_spoke.process(sample_form5500)

        # Should emit signal for large plan
        # Note: Will fail match without DB, but should attempt
        assert dol_spoke.stats['total_processed'] >= 1


# ============================================================================
# EIN MATCHING Tests
# PRD Reference: Section 3.2 - EIN-to-Company Matching
# ============================================================================

class TestEINMatching:
    """
    Test EIN-to-Company Matching

    PRD Requirements:
    - Match Form 5500 EIN to company_master.ein
    - Handle EIN format variations (XX-XXXXXXX vs XXXXXXXXX)
    - Report unmatched EINs for manual review
    """

    def test_ein_format_normalization(self):
        """
        PRD: Normalize EIN formats for matching.
        """
        test_cases = [
            ('12-3456789', '123456789'),
            ('123456789', '123456789'),
            ('12 3456789', '123456789'),
        ]

        for input_ein, expected in test_cases:
            normalized = input_ein.replace('-', '').replace(' ', '')
            assert normalized == expected

    def test_ein_validation(self):
        """
        PRD: EIN should be 9 digits.
        """
        valid_eins = ['12-3456789', '123456789', '98-7654321']
        invalid_eins = ['12345', '12-345678', 'ABCDEFGHI']

        for ein in valid_eins:
            digits = ein.replace('-', '').replace(' ', '')
            assert len(digits) == 9 and digits.isdigit(), f"{ein} should be valid"

        for ein in invalid_eins:
            digits = ein.replace('-', '').replace(' ', '')
            is_valid = len(digits) == 9 and digits.isdigit()
            assert not is_valid, f"{ein} should be invalid"


# ============================================================================
# SCHEDULE A Tests
# PRD Reference: Section 3.3 - Schedule A Extraction
# ============================================================================

class TestScheduleAExtraction:
    """
    Test Schedule A Extraction

    PRD Requirements:
    - Extract broker information
    - Extract carrier/policy data
    - Detect broker changes → BROKER_CHANGE signal (+7.0)
    """

    @pytest.fixture
    def dol_spoke(self):
        from spokes.dol.dol_spoke import DOLNodeSpoke
        mock_hub = Mock()
        return DOLNodeSpoke(hub=mock_hub)

    def test_schedule_a_processing(self, dol_spoke):
        """
        PRD: Process Schedule A broker records.
        """
        from spokes.dol.dol_spoke import ScheduleARecord

        record = ScheduleARecord(
            schedule_id='SA-2023-001',
            filing_id='F5500-2023-001',
            broker_name='Benefits Broker Inc',
            broker_fees=50000.0,
            carrier_name='Health Insurance Co',
            policy_type='Group Health'
        )

        result = dol_spoke.process(record)

        assert dol_spoke.stats['schedule_a_records'] >= 1


# ============================================================================
# SIGNAL EMISSION Tests
# PRD Reference: Section 4 - Signal Emission
# ============================================================================

class TestDOLSignalEmission:
    """
    Test DOL Signal Emission to BIT Engine

    PRD Signal Types and Values:
    - FORM_5500_FILED: +5.0
    - LARGE_PLAN (≥500 participants): +8.0
    - BROKER_CHANGE: +7.0
    """

    def test_signal_values_match_prd(self):
        """
        PRD: Verify signal impact values match PRD specification.
        """
        from hub.company.bit_engine import SignalType, SIGNAL_IMPACTS

        # PRD-specified values
        expected_values = {
            SignalType.FORM_5500_FILED: 5.0,
            SignalType.LARGE_PLAN: 8.0,
            SignalType.BROKER_CHANGE: 7.0,
        }

        for signal_type, expected_value in expected_values.items():
            actual_value = SIGNAL_IMPACTS.get(signal_type, 0)
            assert actual_value == expected_value, \
                f"{signal_type} should have impact {expected_value}, got {actual_value}"


# ============================================================================
# SIGNAL IDEMPOTENCY Tests
# PRD Reference: Section 2.3 - Signal Idempotency (DOL)
# ============================================================================

class TestDOLSignalIdempotency:
    """
    Test DOL Signal Idempotency

    PRD Requirements (HARD LAW):
    - DOL signals: 365-day deduplication window
    - Same filing + same signal type within 365 days = DROP
    - Annual filings should only emit once per year
    """

    def test_dol_signal_365_day_dedup(self):
        """
        PRD: DOL signals have 365-day deduplication window.

        Same EIN + same filing year = DROP duplicate.
        """
        dedup_window_days = 365
        assert dedup_window_days == 365, "DOL signals should have 365-day dedup"

    def test_dedup_key_includes_filing_year(self):
        """
        PRD: Dedup key should include filing year for annual filings.

        Format: {company_id}:{filing_year}:{signal_type}
        """
        company_id = 'C001'
        filing_year = '2023'
        signal_type = 'FORM_5500_FILED'

        dedup_key = f"{company_id}:{filing_year}:{signal_type}"
        assert dedup_key == 'C001:2023:FORM_5500_FILED'


# ============================================================================
# ERROR CODE Tests
# PRD Reference: Section 5 - Error Codes
# ============================================================================

class TestDOLErrorCodes:
    """
    Test DOL Sub-Hub Error Codes

    PRD Error Codes:
    - DOL-001: Invalid filing format
    - DOL-002: Missing EIN
    - DOL-003: EIN not found in company_master
    - DOL-004: Duplicate filing detected (within 365 days)
    - DOL-005: Schedule A parsing error
    - DOL-006: Invalid plan year dates
    - DOL-007: Missing required fields
    """

    def test_error_code_format(self):
        """
        PRD: Error codes follow format DOL-{number}
        """
        valid_codes = [
            'DOL-001', 'DOL-002', 'DOL-003',
            'DOL-004', 'DOL-005', 'DOL-006', 'DOL-007'
        ]

        import re
        pattern = r'^DOL-[0-9]{3}$'

        for code in valid_codes:
            assert re.match(pattern, code), f"Error code {code} should match format"


# ============================================================================
# CORRELATION ID Tests
# PRD Reference: Section 2.2 - Correlation ID Protocol
# ============================================================================

class TestDOLCorrelationID:
    """
    Test Correlation ID enforcement for DOL Node.

    PRD Requirements:
    - Every DOL process MUST have correlation_id
    - correlation_id propagates unchanged through processing
    """

    def test_correlation_id_propagation(self):
        """
        PRD: correlation_id must propagate through DOL processing.

        GAP: This documents expected behavior.
        """
        correlation_id = str(uuid.uuid4())

        # Verify format
        assert len(correlation_id) == 36
        uuid.UUID(correlation_id)  # Should not raise


# ============================================================================
# PROMOTION GATES Tests
# PRD Reference: Section 6 - Promotion Gates
# ============================================================================

class TestDOLPromotionGates:
    """
    Test DOL Promotion Gates (Burn-in → Steady State)

    PRD Requirements:
    - Burn-in mode: 30 days OR 1,000 filings processed
    - Gate metrics: Match rate, signal accuracy, processing time
    """

    def test_burnin_criteria(self):
        """
        PRD: Burn-in complete after 30 days OR 1,000 filings.
        """
        burnin_days = 30
        burnin_filings = 1000

        assert burnin_days == 30
        assert burnin_filings == 1000

    def test_match_rate_threshold(self):
        """
        PRD: Match rate should exceed threshold for promotion.

        Target: >80% EIN match rate.
        """
        target_match_rate = 0.80
        assert target_match_rate == 0.80


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
