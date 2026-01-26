# Bicycle Wheel Doctrine utilities
# Implements the hub-and-spoke pattern utilities

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class HubType(Enum):
    """Hub types in the CL Parent-Child architecture."""
    SUB_HUB = "sub_hub"  # Child hub (e.g., Company Target, People, DOL)
    SPOKE = "spoke"  # I/O connectors between hubs (no logic, no state)


class SpokeDirection(Enum):
    """Direction of spoke data flow."""
    INGRESS = "ingress"  # Data flowing INTO a hub
    EGRESS = "egress"    # Data flowing OUT of a hub


@dataclass
class SpokePayload:
    """Base class for spoke payloads.

    All spoke payloads must include company_unique_id to anchor to CL identity.
    """
    company_id: str
    payload_type: str
    data: Dict[str, Any]

    def validate(self) -> bool:
        """Validate the payload has required fields."""
        if not self.company_id:
            raise ValueError("company_id is required - all data anchors to company")
        return True


@dataclass
class HubManifest:
    """Hub manifest defining hub identity and ownership."""
    hub_id: str
    doctrine_id: str
    core_metric: str
    entities_owned: list
    hub_type: HubType

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'HubManifest':
        """Load hub manifest from YAML file."""
        import yaml
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(
            hub_id=data['hub_id'],
            doctrine_id=data['doctrine_id'],
            core_metric=data['core_metric'],
            entities_owned=data.get('entities_owned', []),
            hub_type=HubType(data.get('hub_type', 'spoke'))
        )


def validate_company_anchor(company_unique_id: Optional[str]) -> bool:
    """Validate that company anchor exists.

    Implements the Golden Rule:
    IF company_unique_id IS NULL: STOP. DO NOT PROCEED.
    Request identity from Company Lifecycle (CL) parent hub first.

    Args:
        company_unique_id: The CL-minted company ID to validate

    Returns:
        True if valid

    Raises:
        ValueError: If company_unique_id is None or empty
    """
    if not company_unique_id:
        raise ValueError(
            "Golden Rule Violation: company_unique_id is required. "
            "CL must mint identity before Outreach can proceed. "
            "This hub does NOT mint identity - it consumes from CL."
        )
    return True


__all__ = [
    'HubType',
    'SpokeDirection',
    'SpokePayload',
    'HubManifest',
    'validate_company_anchor'
]
