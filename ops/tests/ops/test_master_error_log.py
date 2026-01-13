"""
Test Suite: ops/master_error_log/ - Master Error Log System
=============================================================
PRD Reference: PRD_MASTER_ERROR_LOG.md

Tests Master Error Log functionality:
- Error event emission
- Correlation ID enforcement (FAIL HARD)
- Process ID validation (FAIL HARD)
- Append-only immutability
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch


# ============================================================================
# MASTER ERROR EMITTER Tests
# PRD Reference: Section 3 - Master Error Emitter
# ============================================================================

class TestMasterErrorEmitter:
    """
    Test Master Error Emitter

    PRD Requirements (DOCTRINE - FAIL HARD):
    - Local First: Write to local table BEFORE calling emitter
    - Correlation Required: All errors MUST have correlation_id
    - Process ID Required: All errors MUST have process_id
    - Append-Only: No updates or deletes
    """

    @pytest.fixture
    def emitter(self):
        from ops.master_error_log.master_error_emitter import (
            MasterErrorEmitter, OperatingMode
        )
        mock_db = Mock()
        return MasterErrorEmitter(mock_db, OperatingMode.STEADY_STATE)

    @pytest.fixture
    def valid_params(self):
        from ops.master_error_log.master_error_emitter import (
            Hub, Severity, EntityType
        )
        return {
            'correlation_id': str(uuid.uuid4()),
            'hub': Hub.PEOPLE,
            'sub_hub': 'lifecycle',
            'process_id': 'people.lifecycle.email.phase5',
            'pipeline_phase': 'phase5',
            'entity_type': EntityType.PERSON,
            'entity_id': '04.04.02.04.20000.042',
            'severity': Severity.MEDIUM,
            'error_code': 'PSH-P5-001',
            'error_message': 'Cannot generate email - missing first_name',
            'source_tool': 'pattern_template',
            'retryable': False
        }

    def test_emit_success(self, emitter, valid_params):
        """
        PRD: Successfully emit error with valid parameters.
        """
        error_id = emitter.emit(**valid_params)

        # Should return UUID
        assert error_id is not None
        uuid.UUID(error_id)  # Should not raise

    def test_emit_missing_correlation_id_fails_hard(self, emitter, valid_params):
        """
        PRD DOCTRINE: Missing correlation_id → FAIL HARD.

        ValidationError should be raised, not silent failure.
        """
        from ops.master_error_log.master_error_emitter import ValidationError

        valid_params['correlation_id'] = None

        with pytest.raises(ValidationError) as exc_info:
            emitter.emit(**valid_params)

        assert 'correlation_id' in str(exc_info.value).lower()
        assert 'required' in str(exc_info.value).lower()

    def test_emit_empty_correlation_id_fails_hard(self, emitter, valid_params):
        """
        PRD DOCTRINE: Empty correlation_id → FAIL HARD.
        """
        from ops.master_error_log.master_error_emitter import ValidationError

        valid_params['correlation_id'] = ''

        with pytest.raises(ValidationError):
            emitter.emit(**valid_params)

    def test_emit_invalid_correlation_id_fails_hard(self, emitter, valid_params):
        """
        PRD DOCTRINE: Invalid UUID correlation_id → FAIL HARD.
        """
        from ops.master_error_log.master_error_emitter import ValidationError

        valid_params['correlation_id'] = 'not-a-valid-uuid'

        with pytest.raises(ValidationError):
            emitter.emit(**valid_params)


# ============================================================================
# PROCESS ID VALIDATION Tests
# PRD Reference: Section 3.2 - Process ID Format
# ============================================================================

class TestProcessIDValidation:
    """
    Test Process ID Validation

    PRD Requirements (FAIL HARD):
    - Format: hub.subhub.pipeline.phase
    - Exactly 4 dot-separated components
    - All lowercase, underscores allowed
    - Max length: 100 characters
    """

    def test_valid_process_ids(self):
        """
        PRD: Valid process_id formats should pass validation.
        """
        from ops.master_error_log.master_error_emitter import validate_process_id

        valid_ids = [
            'company.identity.matching.phase1',
            'people.lifecycle.email.phase5',
            'dol.form5500.ingest.parse',
            'blog_news.news.extract.entity',
        ]

        for process_id in valid_ids:
            validate_process_id(process_id)  # Should not raise

    def test_invalid_process_id_missing_fails_hard(self):
        """
        PRD DOCTRINE: Missing process_id → FAIL HARD.
        """
        from ops.master_error_log.master_error_emitter import (
            validate_process_id, ValidationError
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_process_id(None)

        assert 'mandatory' in str(exc_info.value).lower()

    def test_invalid_process_id_empty_fails_hard(self):
        """
        PRD DOCTRINE: Empty process_id → FAIL HARD.
        """
        from ops.master_error_log.master_error_emitter import (
            validate_process_id, ValidationError
        )

        with pytest.raises(ValidationError):
            validate_process_id('')

        with pytest.raises(ValidationError):
            validate_process_id('   ')  # Whitespace only

    def test_invalid_process_id_wrong_components(self):
        """
        PRD: process_id must have exactly 4 components.
        """
        from ops.master_error_log.master_error_emitter import (
            validate_process_id, ValidationError
        )

        invalid_ids = [
            'company.identity.matching',       # Only 3 components
            'company',                          # Only 1 component
            'company.identity.matching.phase1.extra',  # 5 components
        ]

        for process_id in invalid_ids:
            with pytest.raises(ValidationError) as exc_info:
                validate_process_id(process_id)
            assert '4 components' in str(exc_info.value)

    def test_invalid_process_id_bad_format(self):
        """
        PRD: process_id must be lowercase with underscores only.
        """
        from ops.master_error_log.master_error_emitter import (
            validate_process_id, ValidationError
        )

        invalid_ids = [
            'Company.identity.matching.phase1',  # Uppercase
            'company.identity.matching.phase-1', # Hyphen instead of underscore
        ]

        for process_id in invalid_ids:
            with pytest.raises(ValidationError):
                validate_process_id(process_id)


# ============================================================================
# ERROR CODE VALIDATION Tests
# PRD Reference: Section 3.3 - Error Code Format
# ============================================================================

class TestErrorCodeValidation:
    """
    Test Error Code Validation

    PRD Requirements:
    - Format: PREFIX-CATEGORY-NUMBER
    - Examples: PSH-P5-001, DOL-002, PIPE-301
    """

    def test_valid_error_codes(self):
        """
        PRD: Valid error codes should pass validation.
        """
        from ops.master_error_log.master_error_emitter import validate_error_code

        valid_codes = [
            'PSH-P0-001',
            'PSH-P5-002',
            'DOL-001',
            'PIPE-301',
            'BLOG-101',
        ]

        for code in valid_codes:
            validate_error_code(code)  # Should not raise

    def test_invalid_error_code_missing(self):
        """
        PRD: Missing error_code → ValidationError.
        """
        from ops.master_error_log.master_error_emitter import (
            validate_error_code, ValidationError
        )

        with pytest.raises(ValidationError):
            validate_error_code('')


# ============================================================================
# PROCESS ID REGISTRY Tests
# PRD Reference: Section 4 - Process ID Registry
# ============================================================================

class TestProcessIDRegistry:
    """
    Test Process ID Registry

    PRD Requirements:
    - Pre-defined process IDs for all hub/spoke operations
    - Registry should include descriptions
    """

    def test_registry_contains_company_hub(self):
        """
        PRD: Registry should contain Company Hub process IDs.
        """
        from ops.master_error_log.master_error_emitter import PROCESS_IDS

        company_ids = [
            'company.identity.matching.phase1',
            'company.identity.domain.phase2',
            'company.identity.pattern.phase3',
            'company.identity.verification.phase4',
        ]

        for pid in company_ids:
            assert pid in PROCESS_IDS, f"Registry should contain {pid}"

    def test_registry_contains_people_subhub(self):
        """
        PRD: Registry should contain People Sub-Hub process IDs.
        """
        from ops.master_error_log.master_error_emitter import PROCESS_IDS

        people_ids = [
            'people.lifecycle.ingest.phase0',
            'people.lifecycle.email.phase5',
            'people.lifecycle.slot.phase6',
        ]

        for pid in people_ids:
            assert pid in PROCESS_IDS, f"Registry should contain {pid}"

    def test_registry_contains_dol_subhub(self):
        """
        PRD: Registry should contain DOL Sub-Hub process IDs.
        """
        from ops.master_error_log.master_error_emitter import PROCESS_IDS

        dol_ids = [
            'dol.form5500.ingest.parse',
            'dol.form5500.match.ein',
        ]

        for pid in dol_ids:
            assert pid in PROCESS_IDS, f"Registry should contain {pid}"


# ============================================================================
# CREATE PROCESS ID Tests
# PRD Reference: Section 3.4 - Process ID Creation
# ============================================================================

class TestCreateProcessID:
    """
    Test Process ID Creation Helper
    """

    def test_create_process_id_valid(self):
        """
        PRD: create_process_id should generate valid format.
        """
        from ops.master_error_log.master_error_emitter import create_process_id

        process_id = create_process_id(
            hub='people',
            sub_hub='lifecycle',
            pipeline='email',
            phase='phase5'
        )

        assert process_id == 'people.lifecycle.email.phase5'

    def test_create_process_id_lowercases(self):
        """
        PRD: create_process_id should lowercase all components.
        """
        from ops.master_error_log.master_error_emitter import create_process_id

        process_id = create_process_id(
            hub='PEOPLE',
            sub_hub='Lifecycle',
            pipeline='EMAIL',
            phase='Phase5'
        )

        assert process_id == 'people.lifecycle.email.phase5'


# ============================================================================
# OPERATING MODE Tests
# PRD Reference: Section 5 - Operating Modes
# ============================================================================

class TestOperatingMode:
    """
    Test Operating Mode (BURN_IN vs STEADY_STATE)

    PRD Requirements:
    - BURN_IN: Higher alerting thresholds
    - STEADY_STATE: Standard alerting thresholds
    """

    def test_operating_modes_exist(self):
        """
        PRD: Both operating modes should be defined.
        """
        from ops.master_error_log.master_error_emitter import OperatingMode

        assert hasattr(OperatingMode, 'BURN_IN')
        assert hasattr(OperatingMode, 'STEADY_STATE')

    def test_operating_mode_in_error_event(self):
        """
        PRD: Error events should include operating_mode.
        """
        from ops.master_error_log.master_error_emitter import (
            MasterErrorEmitter, OperatingMode, Hub, Severity, EntityType
        )

        mock_db = Mock()
        emitter = MasterErrorEmitter(mock_db, OperatingMode.BURN_IN)

        assert emitter.operating_mode == OperatingMode.BURN_IN


# ============================================================================
# MASTER ERROR EVENT Tests
# PRD Reference: Section 6 - Error Event Schema
# ============================================================================

class TestMasterErrorEvent:
    """
    Test Master Error Event dataclass
    """

    def test_error_event_to_dict(self):
        """
        PRD: Error event should serialize to dict correctly.
        """
        from ops.master_error_log.master_error_emitter import (
            MasterErrorEvent, Hub, Severity, EntityType, OperatingMode
        )

        event = MasterErrorEvent(
            correlation_id=str(uuid.uuid4()),
            hub=Hub.PEOPLE,
            process_id='people.lifecycle.email.phase5',
            pipeline_phase='phase5',
            entity_type=EntityType.PERSON,
            severity=Severity.MEDIUM,
            error_code='PSH-P5-001',
            error_message='Test error',
            operating_mode=OperatingMode.STEADY_STATE,
            retryable=False
        )

        event_dict = event.to_dict()

        assert 'correlation_id' in event_dict
        assert event_dict['hub'] == 'people'
        assert event_dict['severity'] == 'MEDIUM'


# ============================================================================
# IMMUTABILITY Tests
# PRD Reference: Section 7 - Append-Only Enforcement
# ============================================================================

class TestAppendOnlyImmutability:
    """
    Test Append-Only Immutability

    PRD Requirements (DOCTRINE):
    - No UPDATE operations allowed
    - No DELETE operations allowed
    - Corrections are NEW records, never edits
    """

    def test_emitter_only_inserts(self):
        """
        PRD: Emitter should only INSERT, never UPDATE or DELETE.
        """
        from ops.master_error_log.master_error_emitter import (
            MasterErrorEmitter, OperatingMode, Hub, Severity, EntityType
        )

        mock_db = Mock()
        emitter = MasterErrorEmitter(mock_db, OperatingMode.STEADY_STATE)

        emitter.emit(
            correlation_id=str(uuid.uuid4()),
            hub=Hub.PEOPLE,
            process_id='people.lifecycle.email.phase5',
            pipeline_phase='phase5',
            entity_type=EntityType.PERSON,
            severity=Severity.MEDIUM,
            error_code='PSH-P5-001',
            error_message='Test error',
            retryable=False
        )

        # Verify only INSERT was called
        call_args = mock_db.execute.call_args[0][0]
        assert 'INSERT INTO' in call_args
        assert 'UPDATE' not in call_args
        assert 'DELETE' not in call_args


# ============================================================================
# HUB ENUM Tests
# PRD Reference: Section 2 - Hub Enumeration
# ============================================================================

class TestHubEnum:
    """
    Test Hub Enumeration
    """

    def test_all_hubs_defined(self):
        """
        PRD: All hubs should be defined in enum.
        """
        from ops.master_error_log.master_error_emitter import Hub

        expected_hubs = ['COMPANY', 'PEOPLE', 'DOL', 'BLOG_NEWS', 'OUTREACH', 'PLATFORM']

        for hub_name in expected_hubs:
            assert hasattr(Hub, hub_name), f"Hub should have {hub_name}"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
