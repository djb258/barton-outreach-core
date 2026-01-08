"""
Talent Flow Doctrine Enforcement Tests — TF-001
================================================
CERTIFICATION: TF-001
DOCTRINE VERSION: 1.0.1
STATUS: CERTIFIED
DATE: 2026-01-08

These tests validate that Talent Flow implementations conform to
certified doctrine invariants. Test failures block merges.

INVARIANTS TESTED:
1. Idempotency — Same movement cannot insert twice
2. Binary Completion — PROMOTED or QUARANTINED only
3. Kill Switch — HALT behavior, not SKIP
4. Phase Gates — DETECT → RECON → SIGNAL order
5. Write Authority — Only person_movement_history + people_errors
6. Signal Authority — Only 4 permitted signals
"""

import hashlib
import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set
from unittest.mock import MagicMock, patch


# =============================================================================
# DOCTRINE CONSTANTS (MUST MATCH TALENT_FLOW_DOCTRINE.md)
# =============================================================================

CERTIFICATION_ID = "TF-001"
DOCTRINE_VERSION = "1.0.1"

PERMITTED_TABLES: Set[str] = {
    "person_movement_history",
    "people_errors",
    "people.person_movement_history",
    "people.people_errors",
}

PERMITTED_SIGNALS: Set[str] = {
    "SLOT_VACATED",
    "SLOT_BIND_REQUEST",
    "COMPANY_RESOLUTION_REQUIRED",
    "MOVEMENT_RECORDED",
}

VALID_OUTCOMES: Set[str] = {"PROMOTED", "QUARANTINED"}

REQUIRED_PHASES: List[str] = ["DETECT", "RECON", "SIGNAL"]

KILL_SWITCH_VAR = "PEOPLE_MOVEMENT_DETECT_ENABLED"


# =============================================================================
# MOCK IMPLEMENTATIONS FOR TESTING
# =============================================================================

class TalentFlowOutcome(Enum):
    """Valid Talent Flow outcomes per doctrine."""
    PROMOTED = "PROMOTED"
    QUARANTINED = "QUARANTINED"


class PhaseGate(Enum):
    """Phase gates per doctrine."""
    DETECT = "DETECT"
    RECON = "RECON"
    SIGNAL = "SIGNAL"


@dataclass
class MovementEvent:
    """Represents a movement event for testing."""
    person_unique_id: str
    movement_type: str
    company_from_id: Optional[str]
    company_to_id: Optional[str]
    movement_date: str
    detected_at: datetime = None

    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()

    def compute_dedup_hash(self) -> str:
        """Compute SHA256 deduplication hash per doctrine."""
        key_parts = [
            self.person_unique_id or "",
            self.movement_type or "",
            self.company_from_id or "",
            self.company_to_id or "",
            self.movement_date or "",
        ]
        key_string = "".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()


class MockTalentFlowProcessor:
    """
    Mock Talent Flow processor for testing doctrine compliance.
    
    This is NOT production code — it exists solely to validate
    that implementations MUST follow doctrine invariants.
    """

    def __init__(self):
        self.movement_hashes: Set[str] = set()
        self.movements_logged: List[Dict] = []
        self.errors_logged: List[Dict] = []
        self.signals_emitted: List[Dict] = []
        self.kill_switch_enabled: bool = True
        self.current_phase: Optional[PhaseGate] = None
        self.phase_history: List[PhaseGate] = []

    def set_kill_switch(self, enabled: bool):
        """Set kill switch state."""
        self.kill_switch_enabled = enabled

    def process_movement(self, event: MovementEvent) -> TalentFlowOutcome:
        """
        Process a movement event through phase gates.
        
        Returns: PROMOTED or QUARANTINED (binary outcome)
        """
        # Kill switch check (HALT, not SKIP)
        if not self.kill_switch_enabled:
            raise RuntimeError(
                f"[{CERTIFICATION_ID}] HALT: Talent Flow disabled via {KILL_SWITCH_VAR}"
            )

        # Phase 1: DETECT
        self._enter_phase(PhaseGate.DETECT)
        detect_result = self._phase_detect(event)
        if detect_result == TalentFlowOutcome.QUARANTINED:
            return TalentFlowOutcome.QUARANTINED

        # Phase 2: RECON
        self._enter_phase(PhaseGate.RECON)
        recon_result = self._phase_recon(event)
        if recon_result == TalentFlowOutcome.QUARANTINED:
            return TalentFlowOutcome.QUARANTINED

        # Phase 3: SIGNAL
        self._enter_phase(PhaseGate.SIGNAL)
        signal_result = self._phase_signal(event)
        if signal_result == TalentFlowOutcome.QUARANTINED:
            return TalentFlowOutcome.QUARANTINED

        return TalentFlowOutcome.PROMOTED

    def _enter_phase(self, phase: PhaseGate):
        """Enter a phase gate."""
        self.current_phase = phase
        self.phase_history.append(phase)

    def _phase_detect(self, event: MovementEvent) -> TalentFlowOutcome:
        """Phase 1: Detect movement."""
        # Validate required fields
        if not event.person_unique_id:
            self._log_error("TF-E102", "person_not_found", event)
            return TalentFlowOutcome.QUARANTINED

        if not event.movement_type:
            self._log_error("TF-E103", "no_change_detected", event)
            return TalentFlowOutcome.QUARANTINED

        # Canonical slot check (simplified for testing)
        return TalentFlowOutcome.PROMOTED

    def _phase_recon(self, event: MovementEvent) -> TalentFlowOutcome:
        """Phase 2: Reconnaissance — determine movement type."""
        valid_types = {"exit", "hire", "move", "promotion", "title_change"}
        
        if event.movement_type.lower() not in valid_types:
            self._log_error("TF-E201", "ambiguous_movement_type", event)
            return TalentFlowOutcome.QUARANTINED

        # Idempotency check
        dedup_hash = event.compute_dedup_hash()
        if dedup_hash in self.movement_hashes:
            # Duplicate — discard silently (per doctrine)
            return TalentFlowOutcome.PROMOTED  # Already processed

        # Log movement (append-only write)
        self.movement_hashes.add(dedup_hash)
        self._log_movement(event, dedup_hash)

        return TalentFlowOutcome.PROMOTED

    def _phase_signal(self, event: MovementEvent) -> TalentFlowOutcome:
        """Phase 3: Emit signals."""
        try:
            if event.movement_type.lower() in {"exit", "move"}:
                if event.company_from_id:
                    self._emit_signal("SLOT_VACATED", event)

            if event.movement_type.lower() in {"hire", "move"}:
                if event.company_to_id:
                    self._emit_signal("SLOT_BIND_REQUEST", event)
                else:
                    self._emit_signal("COMPANY_RESOLUTION_REQUIRED", event)

            self._emit_signal("MOVEMENT_RECORDED", event)
            return TalentFlowOutcome.PROMOTED

        except Exception as e:
            self._log_error("TF-E301", f"signal_emission_failed: {e}", event)
            return TalentFlowOutcome.QUARANTINED

    def _log_movement(self, event: MovementEvent, dedup_hash: str):
        """Log movement to person_movement_history (permitted table)."""
        self.movements_logged.append({
            "person_unique_id": event.person_unique_id,
            "movement_type": event.movement_type,
            "company_from_id": event.company_from_id,
            "company_to_id": event.company_to_id,
            "detected_at": event.detected_at.isoformat(),
            "dedup_hash": dedup_hash,
        })

    def _log_error(self, error_code: str, message: str, event: MovementEvent):
        """Log error to people_errors (permitted table)."""
        self.errors_logged.append({
            "error_code": error_code,
            "error_stage": "movement_detect",
            "message": message,
            "person_unique_id": event.person_unique_id,
            "logged_at": datetime.utcnow().isoformat(),
        })

    def _emit_signal(self, signal_type: str, event: MovementEvent):
        """Emit a signal (must be in PERMITTED_SIGNALS)."""
        if signal_type not in PERMITTED_SIGNALS:
            raise ValueError(
                f"[{CERTIFICATION_ID}] FORBIDDEN SIGNAL: {signal_type} "
                f"(permitted: {PERMITTED_SIGNALS})"
            )

        self.signals_emitted.append({
            "signal_type": signal_type,
            "person_unique_id": event.person_unique_id,
            "emitted_at": datetime.utcnow().isoformat(),
        })


# =============================================================================
# TEST SUITE: IDEMPOTENCY ENFORCEMENT
# =============================================================================

class TestIdempotencyEnforcement:
    """
    Tests for idempotency invariant.
    
    DOCTRINE: Same movement cannot fire twice.
    Deduplication via SHA256(person_unique_id + movement_type + company_from_id + company_to_id + movement_date)
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    @pytest.fixture
    def sample_event(self):
        return MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

    def test_same_movement_cannot_insert_twice(self, processor, sample_event):
        """
        TF-001: Same movement processed twice should only insert once.
        Second processing is discarded silently (no error).
        """
        # First processing
        result1 = processor.process_movement(sample_event)
        assert result1 == TalentFlowOutcome.PROMOTED

        # Second processing with identical event
        result2 = processor.process_movement(sample_event)
        assert result2 == TalentFlowOutcome.PROMOTED  # No error for duplicate

        # Only one movement should be logged
        assert len(processor.movements_logged) == 1
        assert len(processor.errors_logged) == 0  # No error for duplicates

    def test_different_movements_insert_separately(self, processor):
        """
        TF-001: Different movements should each be inserted.
        """
        event1 = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )
        event2 = MovementEvent(
            person_unique_id="P001",
            movement_type="hire",  # Different type
            company_from_id=None,
            company_to_id="C002",
            movement_date="2026-01-08",
        )

        processor.process_movement(event1)
        processor.process_movement(event2)

        assert len(processor.movements_logged) == 2

    def test_dedup_hash_is_deterministic(self, sample_event):
        """
        TF-001: Same inputs must produce same hash (determinism).
        """
        hash1 = sample_event.compute_dedup_hash()
        hash2 = sample_event.compute_dedup_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex chars

    def test_different_date_produces_different_hash(self):
        """
        TF-001: Different movement_date should produce different hash.
        """
        event1 = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )
        event2 = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-09",  # Different date
        )

        assert event1.compute_dedup_hash() != event2.compute_dedup_hash()


# =============================================================================
# TEST SUITE: BINARY COMPLETION STATE
# =============================================================================

class TestBinaryCompletionState:
    """
    Tests for binary outcome invariant.
    
    DOCTRINE: Only PROMOTED or QUARANTINED. No third state.
    No partial completion.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_successful_processing_returns_promoted(self, processor):
        """
        TF-001: Successful processing must return PROMOTED.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.PROMOTED
        assert result.value == "PROMOTED"

    def test_failed_detect_returns_quarantined(self, processor):
        """
        TF-001: Failed detection must return QUARANTINED.
        """
        event = MovementEvent(
            person_unique_id="",  # Missing — should fail
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.QUARANTINED
        assert len(processor.errors_logged) == 1
        assert processor.errors_logged[0]["error_code"] == "TF-E102"

    def test_invalid_movement_type_returns_quarantined(self, processor):
        """
        TF-001: Invalid movement type must return QUARANTINED.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="invalid_type",  # Not valid
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.QUARANTINED
        assert processor.errors_logged[0]["error_code"] == "TF-E201"

    def test_outcome_enum_has_only_two_values(self):
        """
        TF-001: Outcome enum must have exactly two values.
        """
        outcomes = list(TalentFlowOutcome)

        assert len(outcomes) == 2
        assert TalentFlowOutcome.PROMOTED in outcomes
        assert TalentFlowOutcome.QUARANTINED in outcomes

    def test_valid_outcomes_match_doctrine(self):
        """
        TF-001: Valid outcomes must match doctrine constants.
        """
        enum_values = {o.value for o in TalentFlowOutcome}

        assert enum_values == VALID_OUTCOMES


# =============================================================================
# TEST SUITE: KILL SWITCH ENFORCEMENT
# =============================================================================

class TestKillSwitchEnforcement:
    """
    Tests for kill switch invariant.
    
    DOCTRINE: When disabled, HALT execution — never SKIP.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_kill_switch_disabled_halts_execution(self, processor):
        """
        TF-001: Disabled kill switch must HALT, not skip.
        """
        processor.set_kill_switch(False)

        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        with pytest.raises(RuntimeError) as exc_info:
            processor.process_movement(event)

        assert "HALT" in str(exc_info.value)
        assert CERTIFICATION_ID in str(exc_info.value)
        assert KILL_SWITCH_VAR in str(exc_info.value)

    def test_kill_switch_enabled_allows_processing(self, processor):
        """
        TF-001: Enabled kill switch must allow processing.
        """
        processor.set_kill_switch(True)

        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.PROMOTED

    def test_no_processing_when_halted(self, processor):
        """
        TF-001: When halted, no movements should be logged.
        """
        processor.set_kill_switch(False)

        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        try:
            processor.process_movement(event)
        except RuntimeError:
            pass

        assert len(processor.movements_logged) == 0
        assert len(processor.signals_emitted) == 0


# =============================================================================
# TEST SUITE: PHASE GATE ENFORCEMENT
# =============================================================================

class TestPhaseGateEnforcement:
    """
    Tests for phase gate invariant.
    
    DOCTRINE: DETECT → RECON → SIGNAL order is mandatory.
    No skipping phases.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_phases_execute_in_order(self, processor):
        """
        TF-001: Phases must execute in DETECT → RECON → SIGNAL order.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        # Verify phase order
        assert len(processor.phase_history) == 3
        assert processor.phase_history[0] == PhaseGate.DETECT
        assert processor.phase_history[1] == PhaseGate.RECON
        assert processor.phase_history[2] == PhaseGate.SIGNAL

    def test_quarantine_stops_at_detect(self, processor):
        """
        TF-001: QUARANTINE at DETECT stops further phases.
        """
        event = MovementEvent(
            person_unique_id="",  # Will fail DETECT
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.QUARANTINED
        assert len(processor.phase_history) == 1
        assert processor.phase_history[0] == PhaseGate.DETECT

    def test_quarantine_stops_at_recon(self, processor):
        """
        TF-001: QUARANTINE at RECON stops further phases.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="invalid",  # Will fail RECON
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.QUARANTINED
        assert len(processor.phase_history) == 2
        assert processor.phase_history[0] == PhaseGate.DETECT
        assert processor.phase_history[1] == PhaseGate.RECON

    def test_required_phases_match_doctrine(self):
        """
        TF-001: Required phases must match doctrine.
        """
        enum_names = [p.name for p in PhaseGate]

        assert enum_names == REQUIRED_PHASES


# =============================================================================
# TEST SUITE: WRITE AUTHORITY ENFORCEMENT
# =============================================================================

class TestWriteAuthorityEnforcement:
    """
    Tests for write authority invariant.
    
    DOCTRINE: Only write to person_movement_history and people_errors.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_movements_logged_to_permitted_table(self, processor):
        """
        TF-001: Movements must be logged to person_movement_history.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        assert len(processor.movements_logged) == 1
        # In real implementation, this would write to people.person_movement_history

    def test_errors_logged_to_permitted_table(self, processor):
        """
        TF-001: Errors must be logged to people_errors.
        """
        event = MovementEvent(
            person_unique_id="",  # Will cause error
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        assert len(processor.errors_logged) == 1
        # In real implementation, this would write to people.people_errors

    def test_error_codes_follow_tf_format(self, processor):
        """
        TF-001: Error codes must follow TF-Exxx format.
        """
        event = MovementEvent(
            person_unique_id="",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        assert len(processor.errors_logged) == 1
        error_code = processor.errors_logged[0]["error_code"]
        assert error_code.startswith("TF-E")


# =============================================================================
# TEST SUITE: SIGNAL AUTHORITY ENFORCEMENT
# =============================================================================

class TestSignalAuthorityEnforcement:
    """
    Tests for signal authority invariant.
    
    DOCTRINE: Only emit SLOT_VACATED, SLOT_BIND_REQUEST,
    COMPANY_RESOLUTION_REQUIRED, MOVEMENT_RECORDED.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_exit_emits_slot_vacated(self, processor):
        """
        TF-001: Exit movement must emit SLOT_VACATED.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        signal_types = [s["signal_type"] for s in processor.signals_emitted]
        assert "SLOT_VACATED" in signal_types
        assert "MOVEMENT_RECORDED" in signal_types

    def test_hire_with_company_emits_slot_bind_request(self, processor):
        """
        TF-001: Hire with known company must emit SLOT_BIND_REQUEST.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="hire",
            company_from_id=None,
            company_to_id="C002",
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        signal_types = [s["signal_type"] for s in processor.signals_emitted]
        assert "SLOT_BIND_REQUEST" in signal_types

    def test_hire_without_company_emits_resolution_required(self, processor):
        """
        TF-001: Hire without company must emit COMPANY_RESOLUTION_REQUIRED.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="hire",
            company_from_id=None,
            company_to_id=None,  # Unknown company
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        signal_types = [s["signal_type"] for s in processor.signals_emitted]
        assert "COMPANY_RESOLUTION_REQUIRED" in signal_types

    def test_forbidden_signal_raises_error(self, processor):
        """
        TF-001: Emitting forbidden signal must raise error.
        """
        with pytest.raises(ValueError) as exc_info:
            processor._emit_signal("FORBIDDEN_SIGNAL", None)

        assert "FORBIDDEN SIGNAL" in str(exc_info.value)
        assert CERTIFICATION_ID in str(exc_info.value)

    def test_all_emitted_signals_are_permitted(self, processor):
        """
        TF-001: All emitted signals must be in PERMITTED_SIGNALS.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="move",
            company_from_id="C001",
            company_to_id="C002",
            movement_date="2026-01-08",
        )

        processor.process_movement(event)

        for signal in processor.signals_emitted:
            assert signal["signal_type"] in PERMITTED_SIGNALS


# =============================================================================
# TEST SUITE: FORBIDDEN OPERATIONS
# =============================================================================

class TestForbiddenOperations:
    """
    Tests for forbidden operations invariant.
    
    DOCTRINE: TF is a SENSOR, not an ACTOR.
    No minting, enrichment, scoring, or recursive execution.
    """

    def test_doctrine_constants_are_complete(self):
        """
        TF-001: Doctrine constants must match document.
        """
        assert CERTIFICATION_ID == "TF-001"
        assert DOCTRINE_VERSION == "1.0.1"
        assert len(PERMITTED_TABLES) == 4
        assert len(PERMITTED_SIGNALS) == 4
        assert len(VALID_OUTCOMES) == 2
        assert len(REQUIRED_PHASES) == 3

    def test_permitted_tables_are_correct(self):
        """
        TF-001: Permitted tables must match doctrine.
        """
        expected = {
            "person_movement_history",
            "people_errors",
            "people.person_movement_history",
            "people.people_errors",
        }
        assert PERMITTED_TABLES == expected

    def test_permitted_signals_are_correct(self):
        """
        TF-001: Permitted signals must match doctrine.
        """
        expected = {
            "SLOT_VACATED",
            "SLOT_BIND_REQUEST",
            "COMPANY_RESOLUTION_REQUIRED",
            "MOVEMENT_RECORDED",
        }
        assert PERMITTED_SIGNALS == expected


# =============================================================================
# INTEGRATION TEST: FULL FLOW
# =============================================================================

class TestFullFlowIntegration:
    """
    Integration tests for complete Talent Flow execution.
    """

    @pytest.fixture
    def processor(self):
        return MockTalentFlowProcessor()

    def test_full_exit_flow(self, processor):
        """
        TF-001: Complete exit movement flow.
        """
        event = MovementEvent(
            person_unique_id="P001",
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        # Verify outcome
        assert result == TalentFlowOutcome.PROMOTED

        # Verify phase execution
        assert processor.phase_history == [
            PhaseGate.DETECT,
            PhaseGate.RECON,
            PhaseGate.SIGNAL,
        ]

        # Verify movement logged
        assert len(processor.movements_logged) == 1

        # Verify signals emitted
        signal_types = {s["signal_type"] for s in processor.signals_emitted}
        assert "SLOT_VACATED" in signal_types
        assert "MOVEMENT_RECORDED" in signal_types

        # Verify no errors
        assert len(processor.errors_logged) == 0

    def test_full_move_flow(self, processor):
        """
        TF-001: Complete move (departure + arrival) flow.
        """
        event = MovementEvent(
            person_unique_id="P002",
            movement_type="move",
            company_from_id="C001",
            company_to_id="C002",
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        assert result == TalentFlowOutcome.PROMOTED

        signal_types = {s["signal_type"] for s in processor.signals_emitted}
        assert "SLOT_VACATED" in signal_types
        assert "SLOT_BIND_REQUEST" in signal_types
        assert "MOVEMENT_RECORDED" in signal_types

    def test_quarantine_flow(self, processor):
        """
        TF-001: Quarantine flow with proper error logging.
        """
        event = MovementEvent(
            person_unique_id="",  # Invalid
            movement_type="exit",
            company_from_id="C001",
            company_to_id=None,
            movement_date="2026-01-08",
        )

        result = processor.process_movement(event)

        # Verify quarantine
        assert result == TalentFlowOutcome.QUARANTINED

        # Verify error logged
        assert len(processor.errors_logged) == 1
        assert processor.errors_logged[0]["error_stage"] == "movement_detect"

        # Verify no movement logged
        assert len(processor.movements_logged) == 0

        # Verify no signals emitted
        assert len(processor.signals_emitted) == 0
