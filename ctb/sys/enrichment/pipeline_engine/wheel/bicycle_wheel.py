"""
Bicycle Wheel Base Classes
==========================
Core architecture classes implementing the Bicycle Wheel Doctrine.

"Everything is a wheel. Wheels have wheels."
-- Bicycle Wheel Doctrine v1.1

Architecture:
    - Hub: Central entity that everything anchors to (contains core metric)
    - Spoke: Major domain/function connected to the hub
    - SubWheel: Smaller wheel at a spoke endpoint (fractal)
    - FailureSpoke: Error handling as first-class citizen
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Callable
import logging

from .wheel_result import (
    WheelResult,
    SpokeResult,
    FailureResult,
    ResultStatus,
    FailureType
)


logger = logging.getLogger(__name__)


@dataclass
class Hub:
    """
    Central Axle - The entity everything anchors to.

    Every hub contains:
    - Core entity identifier
    - Core metric (BIT score, health score, etc.)
    - Anchor fields required for spokes to function
    """
    name: str
    entity_type: str  # company, person, order, etc.

    # Core metric that lives inside the hub
    core_metric_name: str = "score"
    core_metric_value: float = 0.0

    # Anchor fields - required for spokes
    anchor_fields: Dict[str, Any] = field(default_factory=dict)

    # Signals received from spokes
    signals: List[Dict[str, Any]] = field(default_factory=list)

    def receive_signal(self, signal: Dict[str, Any]):
        """
        Receive a signal from a spoke and update core metric.

        Signals should include:
        - signal_type: e.g., 'slot_filled', 'email_verified'
        - impact: numeric value to add to core metric
        - source: which spoke sent the signal
        """
        self.signals.append(signal)
        if 'impact' in signal:
            self.core_metric_value += signal['impact']
            logger.debug(
                f"Hub '{self.name}' received signal: {signal['signal_type']} "
                f"(impact: {signal['impact']:+.1f}, new score: {self.core_metric_value})"
            )

    def get_anchor(self, field_name: str) -> Any:
        """Get an anchor field value"""
        return self.anchor_fields.get(field_name)

    def set_anchor(self, field_name: str, value: Any):
        """Set an anchor field value"""
        self.anchor_fields[field_name] = value

    def validate_anchors(self, required: List[str]) -> bool:
        """Check if all required anchor fields are present"""
        for field_name in required:
            if field_name not in self.anchor_fields or self.anchor_fields[field_name] is None:
                return False
        return True


class Spoke(ABC):
    """
    Major domain/function connected to the hub.

    Spokes:
    - Process data in their domain
    - Route failures to failure spokes
    - Send signals back to the hub
    - May have sub-wheels at their endpoints
    """

    def __init__(self, name: str, hub: Hub):
        self.name = name
        self.hub = hub
        self.sub_wheels: Dict[str, 'BicycleWheel'] = {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def process(self, data: Any) -> SpokeResult:
        """
        Process data through this spoke.

        Returns a SpokeResult indicating success/failure and any hub signals.
        """
        pass

    def add_sub_wheel(self, name: str, wheel: 'BicycleWheel'):
        """Add a sub-wheel to this spoke's endpoint"""
        self.sub_wheels[name] = wheel

    def send_to_hub(self, signal_type: str, impact: float, metadata: Dict = None):
        """Send a signal back to the hub"""
        signal = {
            'signal_type': signal_type,
            'impact': impact,
            'source': self.name,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.hub.receive_signal(signal)
        return signal


class FailureSpoke(ABC):
    """
    Failure handling as a first-class citizen.

    Failure spokes:
    - Have their own database tables
    - Define resolution paths
    - Can trigger auto-repair
    - Report to Master Failure Hub
    """

    def __init__(self, name: str, failure_type: FailureType, table_name: str):
        self.name = name
        self.failure_type = failure_type
        self.table_name = table_name
        self.logger = logging.getLogger(f"{__name__}.failure.{name}")

    @abstractmethod
    def route(self, data: Any, reason: str) -> FailureResult:
        """
        Route a failed record to this failure spoke.

        Returns a FailureResult with resolution path information.
        """
        pass

    def to_master_failure_hub(self, result: FailureResult) -> Dict[str, Any]:
        """
        Format failure for Master Failure Hub (shq_error_log).

        All failures propagate upward to centralized monitoring.
        """
        return {
            'source_hub': 'pipeline_engine',
            'sub_hub': self.name,
            'error_code': self.failure_type.value,
            'error_message': result.failure_reason,
            'severity': result.severity,
            'component': f'failure_spoke.{self.name}',
            'resolution_status': 'open',
            'created_at': datetime.now().isoformat()
        }


class SubWheel:
    """
    A wheel within a spoke - fractal architecture.

    Sub-wheels have their own:
    - Hub (e.g., MillionVerifier for email verification)
    - Spokes (e.g., pattern_guesser, bulk_verifier)
    - Failure spokes
    """

    def __init__(self, name: str, hub_name: str):
        self.name = name
        self.hub = Hub(name=hub_name, entity_type='sub_hub')
        self.spokes: Dict[str, Spoke] = {}
        self.failure_spokes: Dict[FailureType, FailureSpoke] = {}
        self.logger = logging.getLogger(f"{__name__}.subwheel.{name}")

    def add_spoke(self, spoke: Spoke):
        """Add a spoke to this sub-wheel"""
        self.spokes[spoke.name] = spoke

    def add_failure_spoke(self, spoke: FailureSpoke):
        """Add a failure spoke to this sub-wheel"""
        self.failure_spokes[spoke.failure_type] = spoke

    def rotate(self, data: Any) -> WheelResult:
        """Process data through this sub-wheel"""
        result = WheelResult(wheel_name=self.name, started_at=datetime.now())

        for spoke_name, spoke in self.spokes.items():
            spoke_result = spoke.process(data)

            if spoke_result.failed:
                # Route to failure spoke
                if spoke_result.failure_type in self.failure_spokes:
                    failure_spoke = self.failure_spokes[spoke_result.failure_type]
                    failure_result = failure_spoke.route(data, spoke_result.failure_reason)
                    result.add_failure(failure_result)
                else:
                    # No failure spoke defined - create generic failure
                    failure_result = FailureResult(
                        failure_type=spoke_result.failure_type or FailureType.VALIDATION_ERROR,
                        record_id=str(id(data)),
                        original_data=data,
                        failure_reason=spoke_result.failure_reason or "Unknown failure",
                        resolution_path="manual_review"
                    )
                    result.add_failure(failure_result)
                break  # Stop processing on failure

            # Success - continue to next spoke
            data = spoke_result.data if spoke_result.data is not None else data
            result.add_success(spoke_result)

        result.complete()
        return result


class BicycleWheel:
    """
    The Master Wheel - orchestrates all spokes and sub-wheels.

    "Think in wheels. Code in wheels. Diagram in wheels."

    A BicycleWheel:
    - Has a central Hub (axle)
    - Has multiple Spokes radiating out
    - Each spoke may have SubWheels
    - Has FailureSpokes for error handling
    - Rotates (processes data) clockwise through spokes
    """

    def __init__(self, name: str, hub: Hub):
        self.name = name
        self.hub = hub
        self.spokes: Dict[str, Spoke] = {}
        self.spoke_order: List[str] = []  # Execution order
        self.failure_spokes: Dict[FailureType, FailureSpoke] = {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def add_spoke(self, spoke: Spoke, order: Optional[int] = None):
        """
        Add a spoke to the wheel.

        Args:
            spoke: The spoke to add
            order: Optional position in rotation order
        """
        self.spokes[spoke.name] = spoke
        if order is not None and order < len(self.spoke_order):
            self.spoke_order.insert(order, spoke.name)
        else:
            self.spoke_order.append(spoke.name)

    def add_failure_spoke(self, spoke: FailureSpoke):
        """Add a failure spoke to the wheel"""
        self.failure_spokes[spoke.failure_type] = spoke

    def rotate(self, data: Any) -> WheelResult:
        """
        Process data through the wheel (clockwise).

        Data flows through each spoke in order. On failure,
        routes to appropriate failure spoke and stops.
        """
        result = WheelResult(wheel_name=self.name, started_at=datetime.now())

        self.logger.info(f"Starting wheel rotation: {self.name}")

        for spoke_name in self.spoke_order:
            spoke = self.spokes[spoke_name]
            self.logger.debug(f"Processing spoke: {spoke_name}")

            try:
                spoke_result = spoke.process(data)

                if spoke_result.failed:
                    # Route to failure spoke
                    self.logger.warning(
                        f"Spoke '{spoke_name}' failed: {spoke_result.failure_reason}"
                    )

                    if spoke_result.failure_type and spoke_result.failure_type in self.failure_spokes:
                        failure_spoke = self.failure_spokes[spoke_result.failure_type]
                        failure_result = failure_spoke.route(data, spoke_result.failure_reason)
                        result.add_failure(failure_result)
                    else:
                        # Generic failure
                        failure_result = FailureResult(
                            failure_type=spoke_result.failure_type or FailureType.VALIDATION_ERROR,
                            record_id=str(id(data)),
                            original_data=data,
                            failure_reason=spoke_result.failure_reason or "Unknown failure",
                            resolution_path="manual_review"
                        )
                        result.add_failure(failure_result)

                    break  # Stop wheel rotation on failure

                # Success - continue to next spoke
                if spoke_result.data is not None:
                    data = spoke_result.data

                # Process sub-wheels if any
                if spoke.sub_wheels:
                    for sw_name, sub_wheel in spoke.sub_wheels.items():
                        self.logger.debug(f"Processing sub-wheel: {sw_name}")
                        sw_result = sub_wheel.rotate(data)
                        # Merge sub-wheel results
                        result.spoke_results.extend(sw_result.spoke_results)
                        result.failure_results.extend(sw_result.failure_results)
                        if sw_result.failed > 0:
                            break  # Stop if sub-wheel failed

                result.add_success(spoke_result)

            except Exception as e:
                self.logger.error(f"Exception in spoke '{spoke_name}': {e}")
                failure_result = FailureResult(
                    failure_type=FailureType.VALIDATION_ERROR,
                    record_id=str(id(data)),
                    original_data=data,
                    failure_reason=str(e),
                    resolution_path="manual_review",
                    severity="error"
                )
                result.add_failure(failure_result)
                break

        # Feed signals back to hub
        for signal in result.hub_signals:
            self.hub.receive_signal(signal)

        result.complete()
        self.logger.info(f"Wheel rotation complete: {result}")

        return result

    def rotate_batch(self, data_items: List[Any]) -> WheelResult:
        """
        Process multiple items through the wheel.

        Returns aggregate results for the batch.
        """
        batch_result = WheelResult(wheel_name=f"{self.name}_batch", started_at=datetime.now())

        for item in data_items:
            item_result = self.rotate(item)

            # Aggregate results
            batch_result.total_processed += item_result.total_processed
            batch_result.successful += item_result.successful
            batch_result.failed += item_result.failed
            batch_result.skipped += item_result.skipped
            batch_result.spoke_results.extend(item_result.spoke_results)
            batch_result.failure_results.extend(item_result.failure_results)
            batch_result.hub_signals.extend(item_result.hub_signals)
            batch_result.output_data.extend(item_result.output_data)

        batch_result.complete()
        return batch_result

    def get_spoke(self, name: str) -> Optional[Spoke]:
        """Get a spoke by name"""
        return self.spokes.get(name)

    def get_failure_spoke(self, failure_type: FailureType) -> Optional[FailureSpoke]:
        """Get a failure spoke by type"""
        return self.failure_spokes.get(failure_type)

    def summary(self) -> Dict[str, Any]:
        """Get wheel configuration summary"""
        return {
            'wheel_name': self.name,
            'hub': {
                'name': self.hub.name,
                'entity_type': self.hub.entity_type,
                'core_metric': {
                    'name': self.hub.core_metric_name,
                    'value': self.hub.core_metric_value
                },
                'anchor_fields': list(self.hub.anchor_fields.keys())
            },
            'spokes': self.spoke_order,
            'failure_spokes': [ft.value for ft in self.failure_spokes.keys()],
            'sub_wheels': {
                spoke_name: list(spoke.sub_wheels.keys())
                for spoke_name, spoke in self.spokes.items()
                if spoke.sub_wheels
            }
        }


# =============================================================================
# Factory Functions for Common Wheel Patterns
# =============================================================================

def create_company_hub() -> Hub:
    """Create the standard Company Hub (central axle of Barton system)"""
    return Hub(
        name="company_hub",
        entity_type="company",
        core_metric_name="bit_score",
        core_metric_value=0.0,
        anchor_fields={
            'company_id': None,
            'company_name': None,
            'domain': None,
            'email_pattern': None,
            'slots': {'CEO': None, 'CFO': None, 'HR': None}
        }
    )


def create_people_hub() -> Hub:
    """Create the People Node hub"""
    return Hub(
        name="people_hub",
        entity_type="person",
        core_metric_name="verification_score",
        core_metric_value=0.0,
        anchor_fields={
            'person_id': None,
            'full_name': None,
            'email': None,
            'company_id': None,
            'slot_type': None
        }
    )
