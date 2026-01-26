# Implementation Plan: BIT Authorization System v2.0

**Authority:** ADR-017
**Status:** PLANNING
**Target Completion:** TBD

---

## Overview

This plan migrates BIT from a scoring system to an authorization system per ADR-017. Each phase is independently deployable and reversible.

---

## Phase 1: Schema Additions

**Goal:** Add new infrastructure without modifying existing behavior
**Risk:** None (purely additive)
**Reversibility:** Drop new tables

### 1.1 New Tables

```sql
-- Movement event storage
CREATE TABLE bit.movement_events (
    movement_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id   TEXT NOT NULL,

    -- Source
    source_hub          TEXT NOT NULL,
    source_table        TEXT NOT NULL,
    source_fields       TEXT[] NOT NULL,

    -- Classification
    movement_class      TEXT NOT NULL,
    pressure_class      TEXT NOT NULL,
    domain              TEXT NOT NULL CHECK (domain IN (
        'STRUCTURAL_PRESSURE',
        'DECISION_SURFACE',
        'NARRATIVE_VOLATILITY'
    )),

    -- Measurement
    direction           TEXT NOT NULL CHECK (direction IN (
        'INCREASING', 'DECREASING', 'REVERTING', 'STABLE'
    )),
    magnitude           NUMERIC(5,2) NOT NULL,

    -- Temporal
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ NOT NULL,
    comparison_period   TEXT,  -- 'YOY', '3YR', etc.

    -- Evidence
    evidence            JSONB NOT NULL,
    source_record_ids   JSONB NOT NULL,  -- Traceability

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_movement_company ON bit.movement_events(company_unique_id);
CREATE INDEX idx_movement_domain ON bit.movement_events(domain);
CREATE INDEX idx_movement_pressure ON bit.movement_events(pressure_class);
CREATE INDEX idx_movement_valid ON bit.movement_events(valid_until);

-- Proof line storage
CREATE TABLE bit.proof_lines (
    proof_id            TEXT PRIMARY KEY,
    company_unique_id   TEXT NOT NULL,

    -- Authorization
    band                INTEGER NOT NULL CHECK (band BETWEEN 0 AND 5),
    pressure_class      TEXT NOT NULL,

    -- Evidence chain
    sources             TEXT[] NOT NULL,
    evidence            JSONB NOT NULL,
    movement_ids        UUID[] NOT NULL,  -- Links to movement_events

    -- Human readable
    human_readable      TEXT NOT NULL,

    -- Validity
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until         TIMESTAMPTZ NOT NULL,

    -- Audit
    generated_by        TEXT NOT NULL,  -- system/agent/human

    CONSTRAINT valid_window CHECK (valid_until > generated_at)
);

CREATE INDEX idx_proof_company ON bit.proof_lines(company_unique_id);
CREATE INDEX idx_proof_valid ON bit.proof_lines(valid_until);

-- Phase state per company
CREATE TABLE bit.phase_state (
    company_unique_id   TEXT PRIMARY KEY,

    -- Current state
    current_band        INTEGER NOT NULL DEFAULT 0,
    phase_status        TEXT NOT NULL DEFAULT 'SILENT' CHECK (phase_status IN (
        'SILENT', 'WATCH', 'EXPLORATORY', 'TARGETED', 'ENGAGED', 'DIRECT'
    )),

    -- Domain activation
    dol_active          BOOLEAN NOT NULL DEFAULT FALSE,
    people_active       BOOLEAN NOT NULL DEFAULT FALSE,
    blog_active         BOOLEAN NOT NULL DEFAULT FALSE,

    -- Pressure alignment
    primary_pressure    TEXT,
    aligned_domains     INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    last_movement_at    TIMESTAMPTZ,
    last_band_change_at TIMESTAMPTZ,
    phase_entered_at    TIMESTAMPTZ,

    -- Stasis tracking
    stasis_start        TIMESTAMPTZ,
    stasis_years        NUMERIC(3,1) DEFAULT 0,

    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Authorization audit log
CREATE TABLE bit.authorization_log (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id   TEXT NOT NULL,

    -- Request
    requested_action    TEXT NOT NULL,
    requested_band      INTEGER NOT NULL,

    -- Decision
    authorized          BOOLEAN NOT NULL,
    actual_band         INTEGER NOT NULL,
    denial_reason       TEXT,

    -- Proof (if required)
    proof_id            TEXT,
    proof_valid         BOOLEAN,

    -- Context
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_by        TEXT NOT NULL
);

CREATE INDEX idx_authlog_company ON bit.authorization_log(company_unique_id);
CREATE INDEX idx_authlog_time ON bit.authorization_log(requested_at);
```

### 1.2 New Columns on Existing Tables

```sql
-- Classify existing signals
ALTER TABLE bit.bit_signal
    ADD COLUMN IF NOT EXISTS movement_class TEXT,
    ADD COLUMN IF NOT EXISTS pressure_class TEXT,
    ADD COLUMN IF NOT EXISTS domain TEXT;

-- Shadow band on company
ALTER TABLE marketing.company_master
    ADD COLUMN IF NOT EXISTS bit_band INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS bit_phase TEXT DEFAULT 'SILENT';
```

### 1.3 Enum Types

```sql
CREATE TYPE bit.authorization_band AS ENUM (
    'SILENT',
    'WATCH',
    'EXPLORATORY',
    'TARGETED',
    'ENGAGED',
    'DIRECT'
);

CREATE TYPE bit.pressure_class AS ENUM (
    'COST_PRESSURE',
    'VENDOR_DISSATISFACTION',
    'DEADLINE_PROXIMITY',
    'ORGANIZATIONAL_RECONFIGURATION',
    'OPERATIONAL_CHAOS'
);

CREATE TYPE bit.movement_domain AS ENUM (
    'STRUCTURAL_PRESSURE',
    'DECISION_SURFACE',
    'NARRATIVE_VOLATILITY'
);
```

### 1.4 Validation

- [ ] All tables created successfully
- [ ] Indexes operational
- [ ] No existing queries broken
- [ ] Existing BIT scoring unchanged

---

## Phase 2: Movement Emission

**Goal:** Hubs emit movement events; shadow band calculation runs parallel
**Risk:** Low (additive behavior)
**Reversibility:** Disable emitters; old scoring continues

### 2.1 DOL Hub Movement Emitter

Create `hubs/dol-filings/imo/middle/movement_emitter.py`:

```python
"""
DOL Movement Emitter - STRUCTURAL_PRESSURE Domain

Emits movement events from DOL filings by comparing current year
to prior year(s) to detect organizational pressure signals.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class PressureClass(Enum):
    COST_PRESSURE = "COST_PRESSURE"
    VENDOR_DISSATISFACTION = "VENDOR_DISSATISFACTION"
    DEADLINE_PROXIMITY = "DEADLINE_PROXIMITY"
    ORGANIZATIONAL_RECONFIGURATION = "ORGANIZATIONAL_RECONFIGURATION"
    OPERATIONAL_CHAOS = "OPERATIONAL_CHAOS"


class MovementDirection(Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    REVERTING = "REVERTING"
    STABLE = "STABLE"


@dataclass
class MovementEvent:
    movement_id: str
    company_unique_id: str
    source_hub: str
    source_table: str
    source_fields: List[str]
    movement_class: str
    pressure_class: str
    domain: str
    direction: str
    magnitude: float
    detected_at: datetime
    valid_from: datetime
    valid_until: datetime
    comparison_period: str
    evidence: Dict[str, Any]
    source_record_ids: Dict[str, Any]


class DOLMovementEmitter:
    """
    Emits STRUCTURAL_PRESSURE movement events from DOL filings.
    Compares current year to prior year(s) to detect movement.
    """

    DOMAIN = "STRUCTURAL_PRESSURE"
    SOURCE_HUB = "dol-filings"

    # Movement definitions with detection rules
    MOVEMENT_DEFINITIONS = {
        'CARRIER_CHANGE': {
            'fields': ['ins_carrier_ein'],
            'comparison': 'YOY_DIFF',
            'pressure_class': PressureClass.VENDOR_DISSATISFACTION,
            'base_magnitude': 20,
            'validity_days': 365,
            'description': 'Insurance carrier changed year-over-year'
        },
        'BROKER_CHANGE': {
            'fields': ['ins_broker_ein', 'ins_broker_name'],
            'comparison': 'YOY_DIFF',
            'pressure_class': PressureClass.VENDOR_DISSATISFACTION,
            'base_magnitude': 25,
            'validity_days': 365,
            'description': 'Broker of record changed year-over-year'
        },
        'BROKER_COST_SPIKE': {
            'fields': ['ins_broker_comm_tot_amt', 'ins_broker_fees_tot_amt'],
            'comparison': 'YOY_DELTA_PCT',
            'threshold': 0.15,  # 15% increase
            'pressure_class': PressureClass.COST_PRESSURE,
            'base_magnitude': 12,
            'validity_days': 365,
            'description': 'Broker costs increased >15% YoY'
        },
        'EMPLOYER_COST_RISING': {
            'fields': ['tot_contrib_employer_amt'],
            'comparison': 'YOY_DELTA_PCT',
            'threshold': 0.10,  # 10% increase
            'pressure_class': PressureClass.COST_PRESSURE,
            'base_magnitude': 15,
            'validity_days': 365,
            'description': 'Employer contribution increased >10% YoY'
        },
        'RENEWAL_IMMINENT': {
            'fields': ['ins_policy_to_date'],
            'comparison': 'DAYS_UNTIL',
            'threshold': 90,  # Within 90 days
            'pressure_class': PressureClass.DEADLINE_PROXIMITY,
            'base_magnitude': 25,
            'validity_days': 90,
            'description': 'Policy renewal within 90 days'
        },
        'RENEWAL_CRITICAL': {
            'fields': ['ins_policy_to_date'],
            'comparison': 'DAYS_UNTIL',
            'threshold': 30,  # Within 30 days
            'pressure_class': PressureClass.DEADLINE_PROXIMITY,
            'base_magnitude': 40,
            'validity_days': 30,
            'description': 'Policy renewal within 30 days'
        },
        'PLAN_SIZE_GROWTH': {
            'fields': ['tot_act_prtcp_cnt'],
            'comparison': 'YOY_DELTA_PCT',
            'threshold': 0.20,  # 20% growth
            'pressure_class': PressureClass.ORGANIZATIONAL_RECONFIGURATION,
            'base_magnitude': 10,
            'validity_days': 365,
            'description': 'Plan participants grew >20% YoY'
        },
        'FILING_IRREGULARITY': {
            'fields': ['ack_id', 'plan_year_end_date'],
            'comparison': 'LATE_FILING',
            'threshold': 30,  # Days late
            'pressure_class': PressureClass.OPERATIONAL_CHAOS,
            'base_magnitude': 8,
            'validity_days': 365,
            'description': 'Filing submitted late'
        },
        'MULTI_CARRIER': {
            'fields': ['schedule_a_count'],
            'comparison': 'THRESHOLD_EXCEEDED',
            'threshold': 3,  # 3+ carriers
            'pressure_class': PressureClass.OPERATIONAL_CHAOS,
            'base_magnitude': 6,
            'validity_days': 365,
            'description': 'Complex multi-carrier arrangement'
        }
    }

    def __init__(self, db_connection):
        self.db = db_connection

    def emit_movements(self, company_id: str) -> List[MovementEvent]:
        """
        Analyze DOL filings for a company and emit movement events.
        """
        current = self._get_current_filing(company_id)
        prior = self._get_prior_filing(company_id)

        if not current:
            return []

        movements = []

        for movement_class, definition in self.MOVEMENT_DEFINITIONS.items():
            detected = self._detect_movement(current, prior, definition)

            if detected:
                event = self._create_movement_event(
                    company_id=company_id,
                    movement_class=movement_class,
                    definition=definition,
                    current=current,
                    prior=prior,
                    detection_result=detected
                )
                movements.append(event)
                self._persist_movement(event)

        return movements

    def _detect_movement(
        self,
        current: Dict,
        prior: Optional[Dict],
        definition: Dict
    ) -> Optional[Dict]:
        """
        Detect if movement occurred based on definition rules.
        Returns detection details if movement found, None otherwise.
        """
        comparison = definition['comparison']
        fields = definition['fields']

        if comparison == 'YOY_DIFF':
            return self._detect_yoy_diff(current, prior, fields)

        elif comparison == 'YOY_DELTA_PCT':
            threshold = definition['threshold']
            return self._detect_yoy_delta_pct(current, prior, fields, threshold)

        elif comparison == 'DAYS_UNTIL':
            threshold = definition['threshold']
            return self._detect_days_until(current, fields, threshold)

        elif comparison == 'LATE_FILING':
            threshold = definition['threshold']
            return self._detect_late_filing(current, threshold)

        elif comparison == 'THRESHOLD_EXCEEDED':
            threshold = definition['threshold']
            return self._detect_threshold_exceeded(current, fields, threshold)

        return None

    def _detect_yoy_diff(
        self,
        current: Dict,
        prior: Optional[Dict],
        fields: List[str]
    ) -> Optional[Dict]:
        """Detect if field value changed between years."""
        if not prior:
            return None

        for field in fields:
            current_val = current.get(field)
            prior_val = prior.get(field)

            if current_val and prior_val and current_val != prior_val:
                return {
                    'field': field,
                    'current_value': current_val,
                    'prior_value': prior_val,
                    'direction': MovementDirection.REVERTING.value
                }

        return None

    def _detect_yoy_delta_pct(
        self,
        current: Dict,
        prior: Optional[Dict],
        fields: List[str],
        threshold: float
    ) -> Optional[Dict]:
        """Detect if field value changed by more than threshold percentage."""
        if not prior:
            return None

        for field in fields:
            current_val = current.get(field, 0) or 0
            prior_val = prior.get(field, 0) or 0

            if prior_val > 0:
                delta_pct = (current_val - prior_val) / prior_val

                if abs(delta_pct) >= threshold:
                    direction = (
                        MovementDirection.INCREASING.value
                        if delta_pct > 0
                        else MovementDirection.DECREASING.value
                    )
                    return {
                        'field': field,
                        'current_value': current_val,
                        'prior_value': prior_val,
                        'delta_pct': round(delta_pct * 100, 1),
                        'direction': direction
                    }

        return None

    def _detect_days_until(
        self,
        current: Dict,
        fields: List[str],
        threshold: int
    ) -> Optional[Dict]:
        """Detect if date field is within threshold days from now."""
        for field in fields:
            date_val = current.get(field)
            if date_val:
                if isinstance(date_val, str):
                    date_val = datetime.fromisoformat(date_val)

                days_until = (date_val - datetime.now()).days

                if 0 < days_until <= threshold:
                    return {
                        'field': field,
                        'target_date': date_val.isoformat(),
                        'days_until': days_until,
                        'direction': MovementDirection.INCREASING.value
                    }

        return None

    def _detect_late_filing(self, current: Dict, threshold: int) -> Optional[Dict]:
        """Detect if filing was submitted late."""
        plan_year_end = current.get('plan_year_end_date')
        received_date = current.get('received_date')

        if plan_year_end and received_date:
            # Form 5500 due 7 months after plan year end
            due_date = plan_year_end + timedelta(days=210)
            days_late = (received_date - due_date).days

            if days_late > threshold:
                return {
                    'due_date': due_date.isoformat(),
                    'received_date': received_date.isoformat(),
                    'days_late': days_late,
                    'direction': MovementDirection.STABLE.value
                }

        return None

    def _detect_threshold_exceeded(
        self,
        current: Dict,
        fields: List[str],
        threshold: int
    ) -> Optional[Dict]:
        """Detect if field value exceeds threshold."""
        for field in fields:
            val = current.get(field, 0) or 0
            if val >= threshold:
                return {
                    'field': field,
                    'value': val,
                    'threshold': threshold,
                    'direction': MovementDirection.STABLE.value
                }

        return None

    def _create_movement_event(
        self,
        company_id: str,
        movement_class: str,
        definition: Dict,
        current: Dict,
        prior: Optional[Dict],
        detection_result: Dict
    ) -> MovementEvent:
        """Create a MovementEvent from detection results."""
        now = datetime.now()
        validity_days = definition.get('validity_days', 365)

        return MovementEvent(
            movement_id=str(uuid.uuid4()),
            company_unique_id=company_id,
            source_hub=self.SOURCE_HUB,
            source_table='dol.form_5500',
            source_fields=definition['fields'],
            movement_class=movement_class,
            pressure_class=definition['pressure_class'].value,
            domain=self.DOMAIN,
            direction=detection_result.get('direction', 'STABLE'),
            magnitude=definition['base_magnitude'],
            detected_at=now,
            valid_from=now,
            valid_until=now + timedelta(days=validity_days),
            comparison_period='YOY' if prior else 'CURRENT',
            evidence=detection_result,
            source_record_ids={
                'current_ack_id': current.get('ack_id'),
                'prior_ack_id': prior.get('ack_id') if prior else None
            }
        )

    def _get_current_filing(self, company_id: str) -> Optional[Dict]:
        """Get most recent DOL filing for company."""
        # Implementation depends on DB schema
        pass

    def _get_prior_filing(self, company_id: str) -> Optional[Dict]:
        """Get prior year DOL filing for company."""
        # Implementation depends on DB schema
        pass

    def _persist_movement(self, event: MovementEvent) -> None:
        """Persist movement event to bit.movement_events table."""
        # Implementation depends on DB schema
        pass
```

### 2.2 People Hub Movement Emitter

Create `hubs/people-intelligence/imo/middle/movement_emitter.py`:

```python
"""
People Movement Emitter - DECISION_SURFACE Domain

Emits movement events from people/slot changes that indicate
organizational decision-making capacity shifts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class PressureClass(Enum):
    ORGANIZATIONAL_RECONFIGURATION = "ORGANIZATIONAL_RECONFIGURATION"
    VENDOR_DISSATISFACTION = "VENDOR_DISSATISFACTION"


@dataclass
class MovementEvent:
    movement_id: str
    company_unique_id: str
    source_hub: str
    source_table: str
    source_fields: List[str]
    movement_class: str
    pressure_class: str
    domain: str
    direction: str
    magnitude: float
    detected_at: datetime
    valid_from: datetime
    valid_until: datetime
    comparison_period: str
    evidence: Dict[str, Any]
    source_record_ids: Dict[str, Any]


class PeopleMovementEmitter:
    """
    Emits DECISION_SURFACE movement events from people/slot changes.
    """

    DOMAIN = "DECISION_SURFACE"
    SOURCE_HUB = "people-intelligence"

    MOVEMENT_DEFINITIONS = {
        'SLOT_VACATED': {
            'source_table': 'people.company_slot',
            'fields': ['slot_type', 'vacated_at'],
            'pressure_class': PressureClass.ORGANIZATIONAL_RECONFIGURATION,
            'base_magnitude': 12,
            'validity_days': 180,
            'description': 'Executive slot became vacant'
        },
        'NEW_HR_LEADER': {
            'source_table': 'people.company_slot',
            'fields': ['slot_type', 'filled_at', 'person_id'],
            'condition': 'slot_type IN (CHRO, HR_MANAGER) AND tenure < 180 days',
            'pressure_class': PressureClass.ORGANIZATIONAL_RECONFIGURATION,
            'base_magnitude': 20,
            'validity_days': 180,
            'description': 'New HR leader within last 6 months'
        },
        'AUTHORITY_VACUUM': {
            'source_table': 'people.company_slot',
            'fields': ['slot_type', 'is_filled', 'vacated_at'],
            'condition': 'HR slots unfilled > 30 days',
            'pressure_class': PressureClass.ORGANIZATIONAL_RECONFIGURATION,
            'base_magnitude': 15,
            'validity_days': 90,
            'description': 'HR authority vacuum (unfilled > 30 days)'
        },
        'DECISION_MAKER_CHURN': {
            'source_table': 'people.company_slot',
            'fields': ['slot_type', 'person_id', 'filled_at'],
            'condition': '2+ HR slot changes in 12 months',
            'pressure_class': PressureClass.VENDOR_DISSATISFACTION,
            'base_magnitude': 18,
            'validity_days': 365,
            'description': 'Multiple HR leadership changes in 12 months'
        },
        'BENEFITS_LEAD_NEW': {
            'source_table': 'people.company_slot',
            'fields': ['slot_type', 'filled_at', 'person_id'],
            'condition': 'slot_type = BENEFITS_LEAD AND tenure < 90 days',
            'pressure_class': PressureClass.ORGANIZATIONAL_RECONFIGURATION,
            'base_magnitude': 15,
            'validity_days': 90,
            'description': 'New benefits lead within last 90 days'
        }
    }

    def __init__(self, db_connection):
        self.db = db_connection

    def emit_movements(self, company_id: str) -> List[MovementEvent]:
        """
        Analyze people/slot data for a company and emit movement events.
        """
        slots = self._get_company_slots(company_id)
        slot_history = self._get_slot_history(company_id)

        movements = []

        for movement_class, definition in self.MOVEMENT_DEFINITIONS.items():
            detected = self._detect_movement(
                company_id, slots, slot_history, definition
            )

            if detected:
                event = self._create_movement_event(
                    company_id=company_id,
                    movement_class=movement_class,
                    definition=definition,
                    detection_result=detected
                )
                movements.append(event)
                self._persist_movement(event)

        return movements

    def _detect_movement(
        self,
        company_id: str,
        slots: List[Dict],
        slot_history: List[Dict],
        definition: Dict
    ) -> Optional[Dict]:
        """Detect if movement occurred based on definition."""
        movement_class = definition.get('description', '')

        if 'VACATED' in movement_class.upper():
            return self._detect_slot_vacated(slots)

        elif 'NEW_HR_LEADER' in movement_class.upper() or 'NEW' in movement_class.upper():
            return self._detect_new_leader(slots, definition)

        elif 'VACUUM' in movement_class.upper():
            return self._detect_authority_vacuum(slots)

        elif 'CHURN' in movement_class.upper():
            return self._detect_decision_maker_churn(slot_history)

        return None

    def _detect_slot_vacated(self, slots: List[Dict]) -> Optional[Dict]:
        """Detect recently vacated HR slots."""
        hr_slots = ['CHRO', 'HR_MANAGER', 'BENEFITS_LEAD']

        for slot in slots:
            if (slot.get('slot_type') in hr_slots and
                not slot.get('is_filled') and
                slot.get('vacated_at')):

                vacated_at = slot['vacated_at']
                days_vacant = (datetime.now() - vacated_at).days

                if days_vacant <= 90:
                    return {
                        'slot_type': slot['slot_type'],
                        'vacated_at': vacated_at.isoformat(),
                        'days_vacant': days_vacant,
                        'direction': 'DECREASING'
                    }

        return None

    def _detect_new_leader(
        self,
        slots: List[Dict],
        definition: Dict
    ) -> Optional[Dict]:
        """Detect new HR leadership within tenure threshold."""
        target_slots = ['CHRO', 'HR_MANAGER', 'BENEFITS_LEAD']
        tenure_threshold = 180  # days

        for slot in slots:
            if (slot.get('slot_type') in target_slots and
                slot.get('is_filled') and
                slot.get('filled_at')):

                filled_at = slot['filled_at']
                tenure_days = (datetime.now() - filled_at).days

                if tenure_days <= tenure_threshold:
                    return {
                        'slot_type': slot['slot_type'],
                        'person_id': slot.get('person_id'),
                        'filled_at': filled_at.isoformat(),
                        'tenure_days': tenure_days,
                        'direction': 'REVERTING'
                    }

        return None

    def _detect_authority_vacuum(self, slots: List[Dict]) -> Optional[Dict]:
        """Detect HR authority vacuum (unfilled slots > 30 days)."""
        hr_slots = ['CHRO', 'HR_MANAGER']

        for slot in slots:
            if (slot.get('slot_type') in hr_slots and
                not slot.get('is_filled') and
                slot.get('vacated_at')):

                days_vacant = (datetime.now() - slot['vacated_at']).days

                if days_vacant > 30:
                    return {
                        'slot_type': slot['slot_type'],
                        'days_vacant': days_vacant,
                        'vacated_at': slot['vacated_at'].isoformat(),
                        'direction': 'STABLE'
                    }

        return None

    def _detect_decision_maker_churn(
        self,
        slot_history: List[Dict]
    ) -> Optional[Dict]:
        """Detect multiple HR leadership changes in 12 months."""
        one_year_ago = datetime.now() - timedelta(days=365)
        hr_slots = ['CHRO', 'HR_MANAGER', 'BENEFITS_LEAD']

        changes = [
            h for h in slot_history
            if h.get('slot_type') in hr_slots and
               h.get('changed_at', datetime.min) > one_year_ago
        ]

        if len(changes) >= 2:
            return {
                'change_count': len(changes),
                'period': '12_months',
                'slot_types': list(set(h['slot_type'] for h in changes)),
                'direction': 'INCREASING'
            }

        return None

    def _create_movement_event(
        self,
        company_id: str,
        movement_class: str,
        definition: Dict,
        detection_result: Dict
    ) -> MovementEvent:
        """Create a MovementEvent from detection results."""
        now = datetime.now()
        validity_days = definition.get('validity_days', 180)

        return MovementEvent(
            movement_id=str(uuid.uuid4()),
            company_unique_id=company_id,
            source_hub=self.SOURCE_HUB,
            source_table=definition.get('source_table', 'people.company_slot'),
            source_fields=definition['fields'],
            movement_class=movement_class,
            pressure_class=definition['pressure_class'].value,
            domain=self.DOMAIN,
            direction=detection_result.get('direction', 'STABLE'),
            magnitude=definition['base_magnitude'],
            detected_at=now,
            valid_from=now,
            valid_until=now + timedelta(days=validity_days),
            comparison_period='CURRENT',
            evidence=detection_result,
            source_record_ids=detection_result
        )

    def _get_company_slots(self, company_id: str) -> List[Dict]:
        """Get current slot state for company."""
        pass

    def _get_slot_history(self, company_id: str) -> List[Dict]:
        """Get slot change history for company."""
        pass

    def _persist_movement(self, event: MovementEvent) -> None:
        """Persist movement event to database."""
        pass
```

### 2.3 Blog Hub Trust Cap Enforcement

Modify `hubs/blog-content/imo/output/emit_bit_signal.py`:

```python
"""
Blog Signal Emitter with Trust Cap Enforcement

CRITICAL: Blog signals are NARRATIVE_VOLATILITY domain.
Blog alone can NEVER exceed Band 1.
"""

class BlogSignalEmitter:
    """
    Emits NARRATIVE_VOLATILITY events.
    CRITICAL: Blog alone can NEVER exceed Band 1.
    """

    DOMAIN = "NARRATIVE_VOLATILITY"
    TRUST_CAP = 1  # Max band contribution from Blog alone

    def emit_movement(self, company_id: str, signal: BlogSignal) -> MovementEvent:
        """
        Emit blog signal as movement event with trust cap metadata.
        """
        event = MovementEvent(
            movement_id=str(uuid.uuid4()),
            company_unique_id=company_id,
            source_hub='blog-content',
            source_table='outreach.blog',
            source_fields=['article_id', 'event_type'],
            movement_class=signal.event_type,
            pressure_class=self._map_to_pressure_class(signal.event_type),
            domain=self.DOMAIN,
            direction=self._get_direction(signal),
            magnitude=signal.bit_impact,
            detected_at=datetime.now(),
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=30),  # Short validity
            comparison_period='CURRENT',
            evidence={
                'article_id': signal.article_id,
                'event_type': signal.event_type,
                'confidence': signal.confidence,
                'trust_capped': True,
                'max_solo_band': self.TRUST_CAP
            },
            source_record_ids={'article_id': signal.article_id}
        )

        self._persist_movement(event)
        return event

    def _map_to_pressure_class(self, event_type: str) -> str:
        """Map blog event types to pressure classes."""
        mapping = {
            'FUNDING_EVENT': 'ORGANIZATIONAL_RECONFIGURATION',
            'ACQUISITION': 'ORGANIZATIONAL_RECONFIGURATION',
            'LEADERSHIP_CHANGE': 'ORGANIZATIONAL_RECONFIGURATION',
            'EXPANSION': 'ORGANIZATIONAL_RECONFIGURATION',
            'LAYOFF': 'COST_PRESSURE',
            'PRODUCT_LAUNCH': None,  # No pressure class
            'PARTNERSHIP': None,
        }
        return mapping.get(event_type, None)
```

### 2.4 Shadow Band Calculator

Create `ops/bit/band_calculator.py`:

```python
"""
Band Calculator - Authorization Band Computation

Calculates authorization band from movement events using
convergence detection across domains.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class Band(Enum):
    SILENT = 0
    WATCH = 1
    EXPLORATORY = 2
    TARGETED = 3
    ENGAGED = 4
    DIRECT = 5


@dataclass
class BandResult:
    band: int
    phase_status: str
    dol_active: bool
    people_active: bool
    blog_active: bool
    primary_pressure: Optional[str]
    aligned_domains: int
    movement_count: int
    magnitude_sum: float


class BandCalculator:
    """
    Calculates authorization band from movement events.

    Key Rules:
    - Blog alone = max Band 1
    - No DOL = max Band 2
    - Convergence (2+ domains aligned) = bonus
    - 3 domains aligned = strong phase
    """

    BAND_NAMES = {
        0: 'SILENT',
        1: 'WATCH',
        2: 'EXPLORATORY',
        3: 'TARGETED',
        4: 'ENGAGED',
        5: 'DIRECT'
    }

    def __init__(self, db_connection):
        self.db = db_connection

    def calculate_band(self, company_id: str) -> BandResult:
        """
        Calculate current authorization band for a company.
        """
        movements = self._get_active_movements(company_id)

        # Domain activation
        dol_active = any(
            m['domain'] == 'STRUCTURAL_PRESSURE'
            for m in movements
        )
        people_active = any(
            m['domain'] == 'DECISION_SURFACE'
            for m in movements
        )
        blog_active = any(
            m['domain'] == 'NARRATIVE_VOLATILITY'
            for m in movements
        )

        # Count active domains
        active_domains = sum([dol_active, people_active, blog_active])

        # Find aligned pressure class
        pressure_classes = [m['pressure_class'] for m in movements if m.get('pressure_class')]
        aligned_pressure = self._find_aligned_pressure(pressure_classes)
        aligned_count = sum([dol_active, people_active, blog_active]) if aligned_pressure else 0

        # Calculate base magnitude
        magnitude_sum = sum(m.get('magnitude', 0) for m in movements)

        # Determine band
        band = self._determine_band(
            active_domains=active_domains,
            dol_present=dol_active,
            blog_only=(blog_active and not dol_active and not people_active),
            aligned_pressure=aligned_pressure,
            magnitude_sum=magnitude_sum
        )

        return BandResult(
            band=band,
            phase_status=self.BAND_NAMES[band],
            dol_active=dol_active,
            people_active=people_active,
            blog_active=blog_active,
            primary_pressure=aligned_pressure,
            aligned_domains=aligned_count,
            movement_count=len(movements),
            magnitude_sum=magnitude_sum
        )

    def _determine_band(
        self,
        active_domains: int,
        dol_present: bool,
        blog_only: bool,
        aligned_pressure: Optional[str],
        magnitude_sum: float
    ) -> int:
        """
        Determine authorization band based on movement state.

        Rules:
        1. Blog alone = max Band 1
        2. No DOL = max Band 2
        3. Base band from magnitude
        4. Convergence bonus for alignment
        """

        # Rule 1: Blog alone caps at Band 1
        if blog_only:
            return min(1, self._band_from_magnitude(magnitude_sum))

        # Calculate base band from magnitude
        base_band = self._band_from_magnitude(magnitude_sum)

        # Rule 2: No DOL caps at Band 2
        if not dol_present:
            return min(2, base_band)

        # Convergence bonus (2+ domains pointing to same pressure)
        if aligned_pressure and active_domains >= 2:
            convergence_bonus = (active_domains - 1)  # +1 per additional domain
            base_band = min(5, base_band + convergence_bonus)

        return base_band

    def _band_from_magnitude(self, magnitude: float) -> int:
        """Convert magnitude sum to base band."""
        if magnitude < 10:
            return 0  # SILENT
        elif magnitude < 25:
            return 1  # WATCH
        elif magnitude < 40:
            return 2  # EXPLORATORY
        elif magnitude < 60:
            return 3  # TARGETED
        elif magnitude < 80:
            return 4  # ENGAGED
        else:
            return 5  # DIRECT

    def _find_aligned_pressure(self, pressure_classes: List[str]) -> Optional[str]:
        """
        Find pressure class that appears in multiple domains.
        Returns the most common pressure class if multiple qualify.
        """
        if not pressure_classes:
            return None

        from collections import Counter
        counts = Counter(pressure_classes)

        # Need at least 2 occurrences for alignment
        aligned = [(p, c) for p, c in counts.items() if c >= 2]

        if not aligned:
            return None

        # Return most common
        return max(aligned, key=lambda x: x[1])[0]

    def _get_active_movements(self, company_id: str) -> List[Dict]:
        """Get active (non-expired) movement events for company."""
        # Query bit.movement_events where valid_until > NOW()
        pass

    def get_current_band(self, company_id: str) -> int:
        """Convenience method to get just the band number."""
        return self.calculate_band(company_id).band
```

### 2.5 Shadow Mode Comparator

Create `ops/bit/shadow_mode.py`:

```python
"""
Shadow Mode Comparator

Runs both old scoring and new band calculation in parallel.
Logs discrepancies for analysis during Phase 2.
"""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Comparison:
    company_id: str
    old_score: int
    old_tier: str
    new_band: int
    new_phase: str
    discrepancy: int
    discrepancy_type: str
    timestamp: datetime


class ShadowModeComparator:
    """
    Runs both old scoring and new band calculation.
    Logs discrepancies for analysis.
    """

    # Map old tiers to approximate band equivalents
    TIER_TO_BAND = {
        'COLD': 0,
        'WARM': 2,
        'HOT': 3,
        'BURNING': 5
    }

    def __init__(self, old_bit_engine, band_calculator, db_connection):
        self.old_bit_engine = old_bit_engine
        self.band_calculator = band_calculator
        self.db = db_connection
        self.discrepancy_threshold = 1  # Allow 1 band difference

    def compare(self, company_id: str) -> Comparison:
        """
        Compare old scoring with new band calculation.
        """
        # Old system
        old_score = self.old_bit_engine.calculate_score(company_id)
        old_tier = self.old_bit_engine.get_tier(old_score)

        # New system
        new_result = self.band_calculator.calculate_band(company_id)
        new_band = new_result.band
        new_phase = new_result.phase_status

        # Compare
        expected_band = self.TIER_TO_BAND.get(old_tier, 0)
        discrepancy = abs(new_band - expected_band)

        # Classify discrepancy type
        discrepancy_type = self._classify_discrepancy(
            old_tier, old_score, new_band, new_result
        )

        comparison = Comparison(
            company_id=company_id,
            old_score=old_score,
            old_tier=old_tier,
            new_band=new_band,
            new_phase=new_phase,
            discrepancy=discrepancy,
            discrepancy_type=discrepancy_type,
            timestamp=datetime.now()
        )

        # Log significant discrepancies
        if discrepancy > self.discrepancy_threshold:
            self._log_discrepancy(comparison, new_result)

        return comparison

    def _classify_discrepancy(
        self,
        old_tier: str,
        old_score: int,
        new_band: int,
        new_result
    ) -> str:
        """Classify the type of discrepancy for analysis."""

        # Blog inflation: old was high due to blog, new capped
        if old_tier in ('HOT', 'BURNING') and new_band <= 1 and new_result.blog_active and not new_result.dol_active:
            return 'BLOG_INFLATION_CORRECTED'

        # DOL gravity: new is higher due to DOL presence
        if new_band > self.TIER_TO_BAND.get(old_tier, 0) and new_result.dol_active:
            return 'DOL_GRAVITY_APPLIED'

        # Convergence bonus: new is higher due to alignment
        if new_result.aligned_domains >= 2 and new_band > self.TIER_TO_BAND.get(old_tier, 0):
            return 'CONVERGENCE_BONUS'

        # Missing DOL: new is capped due to no DOL
        if not new_result.dol_active and new_band < self.TIER_TO_BAND.get(old_tier, 0):
            return 'DOL_ABSENCE_CAP'

        return 'UNCLASSIFIED'

    def _log_discrepancy(self, comparison: Comparison, new_result) -> None:
        """Log discrepancy for analysis."""
        logger.warning(
            f"BIT Discrepancy: company={comparison.company_id} "
            f"old={comparison.old_tier}({comparison.old_score}) "
            f"new=Band{comparison.new_band}({comparison.new_phase}) "
            f"type={comparison.discrepancy_type} "
            f"dol={new_result.dol_active} "
            f"aligned={new_result.aligned_domains}"
        )

        # Persist to database for batch analysis
        self._persist_discrepancy(comparison, new_result)

    def _persist_discrepancy(self, comparison: Comparison, new_result) -> None:
        """Persist discrepancy to analysis table."""
        pass

    def run_batch_comparison(self, company_ids: List[str]) -> Dict:
        """
        Run comparison on batch of companies.
        Returns summary statistics.
        """
        results = {
            'total': len(company_ids),
            'aligned': 0,
            'discrepant': 0,
            'by_type': {}
        }

        for company_id in company_ids:
            comparison = self.compare(company_id)

            if comparison.discrepancy <= self.discrepancy_threshold:
                results['aligned'] += 1
            else:
                results['discrepant'] += 1
                dtype = comparison.discrepancy_type
                results['by_type'][dtype] = results['by_type'].get(dtype, 0) + 1

        results['alignment_rate'] = results['aligned'] / results['total']
        return results
```

### 2.6 Validation Checklist

- [ ] DOL emitting movement events for all movement classes
- [ ] People emitting movement events for slot changes
- [ ] Blog emitting with trust_capped=True metadata
- [ ] Shadow calculator producing bands for all companies
- [ ] Shadow comparator logging discrepancies
- [ ] Discrepancy rate < 5% on test set (or discrepancies are explainable)
- [ ] Old scoring still functional and unchanged
- [ ] No performance regression

---

## Phase 3: Proof Line Infrastructure

**Goal:** Generate and validate proof lines for Band 3+ outreach
**Risk:** Medium (new validation gate)
**Reversibility:** Bypass proof validation with feature flag

### 3.1 Proof Generator

Create `ops/bit/proof_generator.py`:

```python
"""
Proof Line Generator

Generates human-readable and machine-readable proof lines
from movement events. Proof must exist BEFORE message drafting.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib
import json


@dataclass
class ProofLine:
    proof_id: str
    company_unique_id: str
    band: int
    pressure_class: str
    sources: List[str]
    evidence: Dict
    movement_ids: List[str]
    human_readable: str
    generated_at: datetime
    valid_until: datetime
    generated_by: str


class ProofGenerator:
    """
    Generates proof lines from movement events.
    Proof must exist BEFORE message drafting.
    """

    def __init__(self, db_connection):
        self.db = db_connection

    def generate_proof(
        self,
        company_id: str,
        band: int,
        generated_by: str = 'system'
    ) -> ProofLine:
        """
        Generate proof line for a company at specified band.

        Raises InsufficientEvidenceError if movements don't support band.
        """
        movements = self._get_aligned_movements(company_id)

        # Validate sufficient evidence
        if band >= 3 and not movements:
            raise InsufficientEvidenceError(
                f"Band {band} requires movement evidence, none found"
            )

        # Identify primary pressure
        pressure = self._identify_primary_pressure(movements)

        if band >= 3 and not pressure:
            raise InsufficientEvidenceError(
                f"Band {band} requires identifiable pressure class"
            )

        # Extract evidence
        evidence = self._extract_evidence(movements, band)

        # Format human readable
        human_readable = self._format_human_readable(band, pressure, evidence)

        # Calculate validity
        valid_until = self._calculate_validity(movements)

        # Generate proof ID
        proof_id = self._generate_proof_id(company_id, pressure, evidence)

        proof = ProofLine(
            proof_id=proof_id,
            company_unique_id=company_id,
            band=band,
            pressure_class=pressure,
            sources=[m['source_hub'] for m in movements],
            evidence=evidence,
            movement_ids=[m['movement_id'] for m in movements],
            human_readable=human_readable,
            generated_at=datetime.now(),
            valid_until=valid_until,
            generated_by=generated_by
        )

        self._persist_proof(proof)
        return proof

    def _format_human_readable(
        self,
        band: int,
        pressure: str,
        evidence: Dict
    ) -> str:
        """
        Format human-readable proof line based on band.

        Band 3: [PRESSURE] detected via [SOURCE]: [EVIDENCE]
        Band 4: [PRESSURE] convergence: [DOL] + [PEOPLE] + [BLOG?]
        Band 5: PHASE TRANSITION: [PRESSURE] — [ALL] — Window: [X] days
        """
        if band == 3:
            source = evidence.get('primary_source', 'unknown')
            summary = evidence.get('summary', 'movement detected')
            return f"{pressure} detected via {source}: {summary}"

        elif band == 4:
            sources = evidence.get('sources', [])
            source_str = ' + '.join(sources)
            return f"{pressure} convergence: {source_str}"

        elif band == 5:
            sources = evidence.get('sources', [])
            source_str = ' + '.join(sources)
            days = evidence.get('decision_window_days', 'unknown')
            return f"PHASE TRANSITION: {pressure} — {source_str} — Decision window: {days} days"

        return f"{pressure} detected"

    def _extract_evidence(self, movements: List[Dict], band: int) -> Dict:
        """Extract structured evidence from movements."""
        evidence = {
            'sources': list(set(m['source_hub'] for m in movements)),
            'movement_count': len(movements),
            'domains': list(set(m['domain'] for m in movements)),
        }

        # Primary source (highest magnitude)
        if movements:
            primary = max(movements, key=lambda m: m.get('magnitude', 0))
            evidence['primary_source'] = primary['source_hub']
            evidence['primary_movement'] = primary['movement_class']

            # Summary from primary evidence
            primary_evidence = primary.get('evidence', {})
            evidence['summary'] = self._summarize_evidence(primary_evidence)

        # Decision window (shortest validity)
        if movements:
            earliest_expiry = min(m['valid_until'] for m in movements)
            evidence['decision_window_days'] = (earliest_expiry - datetime.now()).days

        # Domain-specific evidence
        for m in movements:
            domain = m['domain'].lower().replace('_', '')
            evidence[f'{domain}_evidence'] = m.get('evidence', {})

        return evidence

    def _summarize_evidence(self, evidence: Dict) -> str:
        """Create human-readable summary from evidence dict."""
        summaries = []

        if 'delta_pct' in evidence:
            summaries.append(f"{evidence.get('field', 'value')} {evidence['delta_pct']:+.1f}% YoY")

        if 'days_until' in evidence:
            summaries.append(f"renewal in {evidence['days_until']} days")

        if 'days_vacant' in evidence:
            summaries.append(f"{evidence.get('slot_type', 'slot')} vacant {evidence['days_vacant']} days")

        if 'tenure_days' in evidence:
            summaries.append(f"new {evidence.get('slot_type', 'leader')} ({evidence['tenure_days']} days)")

        if 'current_value' in evidence and 'prior_value' in evidence:
            summaries.append(f"{evidence.get('field', 'value')} changed")

        return ', '.join(summaries) if summaries else 'movement detected'

    def _identify_primary_pressure(self, movements: List[Dict]) -> Optional[str]:
        """Identify the primary pressure class from movements."""
        if not movements:
            return None

        from collections import Counter
        pressures = [m['pressure_class'] for m in movements if m.get('pressure_class')]

        if not pressures:
            return None

        counts = Counter(pressures)
        return counts.most_common(1)[0][0]

    def _calculate_validity(self, movements: List[Dict]) -> datetime:
        """Calculate proof validity from movement validity windows."""
        if not movements:
            return datetime.now() + timedelta(days=90)

        # Proof valid until earliest movement expires
        earliest = min(m['valid_until'] for m in movements)

        # Cap at 90 days
        max_validity = datetime.now() + timedelta(days=90)
        return min(earliest, max_validity)

    def _generate_proof_id(
        self,
        company_id: str,
        pressure: str,
        evidence: Dict
    ) -> str:
        """Generate unique proof ID."""
        content = f"{company_id}:{pressure}:{json.dumps(evidence, sort_keys=True, default=str)}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"prf_{hash_val}"

    def _get_aligned_movements(self, company_id: str) -> List[Dict]:
        """Get active movements that share a pressure class."""
        # Query movements and filter to aligned ones
        pass

    def _persist_proof(self, proof: ProofLine) -> None:
        """Persist proof to bit.proof_lines table."""
        pass

    def get_or_create(self, company_id: str, band: int) -> ProofLine:
        """Get existing valid proof or create new one."""
        existing = self._get_valid_proof(company_id, band)
        if existing:
            return existing
        return self.generate_proof(company_id, band)

    def _get_valid_proof(self, company_id: str, band: int) -> Optional[ProofLine]:
        """Get existing proof that is still valid."""
        pass


class InsufficientEvidenceError(Exception):
    """Raised when movements don't support requested band."""
    pass
```

### 3.2 Proof Validator

Create `ops/bit/proof_validator.py`:

```python
"""
Proof Validator

Validates proof lines before message send.
Invalid proof = blocked send.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    valid: bool
    reason: Optional[str] = None
    proof: Optional[dict] = None
    expired_at: Optional[datetime] = None
    proof_band: Optional[int] = None
    requested_band: Optional[int] = None


class ProofValidator:
    """
    Validates proof before message send.
    Invalid proof = blocked send.
    """

    def __init__(self, db_connection):
        self.db = db_connection

    def validate_for_send(
        self,
        proof_id: str,
        requested_band: int
    ) -> ValidationResult:
        """
        Validate proof is sufficient for requested band.

        Checks:
        1. Proof exists
        2. Proof not expired
        3. Proof band >= requested band
        4. Evidence chain intact
        """
        proof = self._get_proof(proof_id)

        # Check 1: Proof exists
        if not proof:
            return ValidationResult(
                valid=False,
                reason="PROOF_NOT_FOUND"
            )

        # Check 2: Proof not expired
        if proof['valid_until'] < datetime.now():
            return ValidationResult(
                valid=False,
                reason="PROOF_EXPIRED",
                expired_at=proof['valid_until']
            )

        # Check 3: Proof band sufficient
        if proof['band'] < requested_band:
            return ValidationResult(
                valid=False,
                reason="PROOF_INSUFFICIENT",
                proof_band=proof['band'],
                requested_band=requested_band
            )

        # Check 4: Evidence chain intact
        if not self._verify_evidence_chain(proof):
            return ValidationResult(
                valid=False,
                reason="EVIDENCE_CHAIN_BROKEN"
            )

        return ValidationResult(valid=True, proof=proof)

    def _verify_evidence_chain(self, proof: dict) -> bool:
        """
        Verify that proof's movement_ids still exist and are valid.
        """
        movement_ids = proof.get('movement_ids', [])

        if not movement_ids:
            return False

        # Check each movement still exists and is valid
        for mid in movement_ids:
            movement = self._get_movement(mid)
            if not movement:
                logger.warning(f"Movement {mid} no longer exists")
                return False
            if movement['valid_until'] < datetime.now():
                logger.warning(f"Movement {mid} has expired")
                return False

        return True

    def _get_proof(self, proof_id: str) -> Optional[dict]:
        """Get proof by ID."""
        pass

    def _get_movement(self, movement_id: str) -> Optional[dict]:
        """Get movement by ID."""
        pass
```

### 3.3 Message Gate Integration

Create `ops/bit/message_gate.py`:

```python
"""
Message Gate

Validates band authorization and proof before message send.
Integrates with existing MarketingSafetyGate.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationResult:
    authorized: bool
    band: int
    reason: Optional[str] = None
    proof_id: Optional[str] = None


class MessageGate:
    """
    Gate that validates band authorization and proof before message send.

    Flow:
    1. Get current band
    2. Check action permitted at band
    3. If Band 3+, require valid proof
    4. Log authorization decision
    """

    # Actions permitted at each band
    BAND_PERMISSIONS = {
        0: [],  # SILENT - nothing
        1: ['internal_flag'],  # WATCH - internal only
        2: ['educational_content'],  # EXPLORATORY - educational
        3: ['persona_email'],  # TARGETED - persona-specific
        4: ['persona_email', 'phone_warm'],  # ENGAGED - phone allowed
        5: ['persona_email', 'phone_warm', 'phone_cold', 'meeting_request'],  # DIRECT
    }

    def __init__(self, band_calculator, proof_validator, db_connection):
        self.band_calculator = band_calculator
        self.proof_validator = proof_validator
        self.db = db_connection

    def authorize_send(
        self,
        company_id: str,
        action_type: str,
        proof_id: Optional[str] = None
    ) -> AuthorizationResult:
        """
        Authorize a send action for a company.
        """
        # Get current band
        band_result = self.band_calculator.calculate_band(company_id)
        band = band_result.band

        # Check action permitted
        permitted_actions = self.BAND_PERMISSIONS.get(band, [])
        if action_type not in permitted_actions:
            self._log_authorization(
                company_id, action_type, band,
                authorized=False, reason=f"Action '{action_type}' not permitted at Band {band}"
            )
            return AuthorizationResult(
                authorized=False,
                band=band,
                reason=f"Band {band} does not permit '{action_type}'"
            )

        # Check proof if Band 3+
        if band >= 3:
            if not proof_id:
                self._log_authorization(
                    company_id, action_type, band,
                    authorized=False, reason="Band 3+ requires proof line"
                )
                return AuthorizationResult(
                    authorized=False,
                    band=band,
                    reason="Band 3+ requires proof line"
                )

            proof_result = self.proof_validator.validate_for_send(proof_id, band)

            if not proof_result.valid:
                self._log_authorization(
                    company_id, action_type, band,
                    authorized=False, reason=f"Proof invalid: {proof_result.reason}",
                    proof_id=proof_id
                )
                return AuthorizationResult(
                    authorized=False,
                    band=band,
                    reason=f"Proof invalid: {proof_result.reason}",
                    proof_id=proof_id
                )

        # Authorized
        self._log_authorization(
            company_id, action_type, band,
            authorized=True, proof_id=proof_id
        )

        return AuthorizationResult(
            authorized=True,
            band=band,
            proof_id=proof_id
        )

    def _log_authorization(
        self,
        company_id: str,
        action_type: str,
        band: int,
        authorized: bool,
        reason: Optional[str] = None,
        proof_id: Optional[str] = None
    ) -> None:
        """Log authorization decision to bit.authorization_log."""
        pass
```

### 3.4 Validation Checklist

- [ ] Proof generator creates valid proofs from movements
- [ ] Proof validator catches expired proofs
- [ ] Proof validator catches insufficient band proofs
- [ ] Proof validator detects broken evidence chains
- [ ] Message gate blocks sends without valid proof at Band 3+
- [ ] All authorizations logged to bit.authorization_log
- [ ] Feature flag allows bypassing proof validation (for rollback)

---

## Phase 4: Cutover

**Goal:** Replace scoring with authorization as primary system
**Risk:** High (behavioral change)
**Reversibility:** Re-enable score-based gates via feature flag

### 4.1 Feature Flags

```python
# Feature flags for controlled rollout
BIT_V2_ENABLED = True  # Master switch
BIT_V2_SHADOW_MODE = False  # If True, calculate but don't enforce
BIT_V2_PROOF_REQUIRED = True  # If False, allow sends without proof
BIT_V2_OLD_SCORING_ENABLED = False  # If True, old scoring still runs
```

### 4.2 Deprecation Markers

```python
import warnings

@deprecated(version="2.0", reason="Use BandCalculator.calculate_band() instead")
def calculate_bit_score(company_id: str) -> int:
    warnings.warn(
        "calculate_bit_score is deprecated. Use BandCalculator.calculate_band()",
        DeprecationWarning
    )
    # ... legacy implementation

@deprecated(version="2.0", reason="Use band-based authorization instead")
def get_bit_tier(score: int) -> str:
    warnings.warn(
        "get_bit_tier is deprecated. Use BandCalculator for band-based authorization.",
        DeprecationWarning
    )
    # ... legacy implementation
```

### 4.3 Terminology Migration

| Old Term | New Term | Notes |
|----------|----------|-------|
| COLD | SILENT (Band 0) | No action permitted |
| WARM | WATCH/EXPLORATORY (Band 1-2) | Internal or educational only |
| HOT | TARGETED (Band 3) | Persona email, proof required |
| BURNING | ENGAGED/DIRECT (Band 4-5) | Phone + full contact |
| BIT Score | BIT Index | Still 0-100, different meaning |
| Tier | Band | Authorization level |
| Buyer Intent | Phase Detection | Movement-based, not scoring |

### 4.4 Monitoring Dashboard

Track these metrics post-cutover:

| Metric | Expected | Alert Threshold |
|--------|----------|-----------------|
| Band distribution | Shift toward lower bands | >50% in Band 0-1 |
| Proof generation rate | >95% success at Band 3+ | <90% |
| Authorization denial rate | <10% | >15% |
| Send volume | -30% to +10% vs baseline | >40% change |
| Discrepancy rate | <5% | >10% |

### 4.5 Validation Checklist

- [ ] All outreach paths use band authorization
- [ ] All Band 3+ messages have valid proof attached
- [ ] No messages sent with expired proofs
- [ ] Feature flags allow instant rollback
- [ ] Monitoring dashboards operational
- [ ] Volume change within expected range
- [ ] No regression in engagement metrics

---

## Rollback Procedures

### Emergency Rollback (Any Phase)

```python
# Set feature flags
BIT_V2_ENABLED = False
BIT_V2_OLD_SCORING_ENABLED = True
BIT_V2_PROOF_REQUIRED = False

# Old scoring resumes immediately
# New band calculation stops
# Proof validation bypassed
```

### Phase-Specific Rollback

**Phase 1 Rollback:**
```sql
-- Drop new tables (no functional impact)
DROP TABLE IF EXISTS bit.movement_events CASCADE;
DROP TABLE IF EXISTS bit.proof_lines CASCADE;
DROP TABLE IF EXISTS bit.phase_state CASCADE;
DROP TABLE IF EXISTS bit.authorization_log CASCADE;
DROP TYPE IF EXISTS bit.authorization_band CASCADE;
DROP TYPE IF EXISTS bit.pressure_class CASCADE;
DROP TYPE IF EXISTS bit.movement_domain CASCADE;
```

**Phase 2 Rollback:**
- Disable movement emitters in hub configs
- Shadow calculator stops running
- Old scoring continues unchanged

**Phase 3 Rollback:**
- Set `BIT_V2_PROOF_REQUIRED = False`
- Message gate bypasses proof validation
- Log warning on each bypassed check

**Phase 4 Rollback:**
- Set `BIT_V2_ENABLED = False`
- Set `BIT_V2_OLD_SCORING_ENABLED = True`
- Old tier-based gates re-enabled

---

## Timeline

| Phase | Duration | Dependencies | Exit Criteria |
|-------|----------|--------------|---------------|
| Phase 1 | 1 week | None | Tables created, no breaks |
| Phase 2 | 2 weeks | Phase 1 | <5% discrepancy rate |
| Phase 3 | 2 weeks | Phase 2 | Proof system working |
| Phase 4 | 1 week | Phase 3 | Cutover complete |

**Total:** 6 weeks (conservative estimate)

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Movement coverage | 100% DOL signals | Distinct movement classes |
| Proof success rate | >95% at Band 3+ | Proofs / proof requests |
| Authorization denial rate | <10% | Denials / requests |
| Message traceability | 100% | Messages with valid proof |
| Volume change | -30% to +10% | Send count vs baseline |
| Engagement rate | No regression | Open/click/reply rates |

---

**Document Control:**

| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Authority | ADR-017 |
| Status | PLANNING |
| Owner | System Architect |
