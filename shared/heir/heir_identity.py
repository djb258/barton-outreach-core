#!/usr/bin/env python3
"""
HEIR Identity System — Hub Environment Identity Record

DOCTRINE: Every operation MUST have a unique_id for traceability.
The unique_id traces operations back to their origin hub and timestamp.

Format Options:
1. Standard: <hub-id>-<timestamp>-<random_hex>
   Example: outreach-core-001-20260205143022-a1b2c3d4

2. Formal HEIR: HEIR-YYYY-MM-SYSTEM-MODE-VN
   Example: HEIR-2026-02-OUTREACH-PROD-V1

Every operation should generate and propagate a unique_id.
This enables:
- End-to-end traceability
- Error correlation
- Audit trails
- Performance tracking
"""

import os
import time
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import threading


# =============================================================================
# CONFIGURATION
# =============================================================================

class HeirMode(Enum):
    """Operating mode for HEIR IDs."""
    PROD = "PROD"
    DEV = "DEV"
    TEST = "TEST"
    STAGING = "STAGING"


class HeirFormat(Enum):
    """HEIR ID format options."""
    STANDARD = "standard"      # hub-id-timestamp-hex
    FORMAL = "formal"          # HEIR-YYYY-MM-SYSTEM-MODE-VN


# Default configuration (loaded from heir.doctrine.yaml if available)
DEFAULT_HUB_ID = "outreach-core-001"
DEFAULT_SYSTEM = "OUTREACH"
DEFAULT_MODE = HeirMode.PROD
DEFAULT_VERSION = "V1"


# =============================================================================
# HEIR ID GENERATOR
# =============================================================================

@dataclass
class HeirId:
    """
    HEIR Identity record.

    Contains both the unique_id and metadata about its generation.
    """
    unique_id: str
    hub_id: str
    timestamp: datetime
    mode: HeirMode
    format: HeirFormat
    random_component: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.unique_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unique_id": self.unique_id,
            "hub_id": self.hub_id,
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode.value,
            "format": self.format.value,
            "random_component": self.random_component,
            "metadata": self.metadata,
        }


class HeirIdentity:
    """
    HEIR Identity generator and manager.

    Usage:
        heir = HeirIdentity()

        # Generate a unique_id
        heir_id = heir.generate()
        print(heir_id.unique_id)  # outreach-core-001-20260205143022-a1b2c3d4

        # Generate formal HEIR ID
        heir_id = heir.generate(format=HeirFormat.FORMAL)
        print(heir_id.unique_id)  # HEIR-2026-02-OUTREACH-PROD-V1-a1b2c3d4

        # Get current unique_id for context
        current_id = heir.current()
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for global HEIR identity manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        hub_id: str = None,
        system: str = None,
        mode: HeirMode = None,
        version: str = None
    ):
        """
        Initialize HEIR identity manager.

        Args:
            hub_id: Hub identifier (default: from config or DEFAULT_HUB_ID)
            system: System name for formal format (default: OUTREACH)
            mode: Operating mode (default: PROD)
            version: Version string (default: V1)
        """
        # Only initialize once (singleton)
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.hub_id = hub_id or self._load_hub_id() or DEFAULT_HUB_ID
        self.system = system or DEFAULT_SYSTEM
        self.mode = mode or self._detect_mode()
        self.version = version or DEFAULT_VERSION

        # Thread-local storage for current context
        self._local = threading.local()
        self._initialized = True

    def _load_hub_id(self) -> Optional[str]:
        """Load hub_id from heir.doctrine.yaml if available."""
        try:
            import yaml
            heir_path = os.path.join(os.getcwd(), "heir.doctrine.yaml")
            if os.path.exists(heir_path):
                with open(heir_path, "r") as f:
                    config = yaml.safe_load(f)
                    return config.get("hub", {}).get("id")
        except Exception:
            pass
        return None

    def _detect_mode(self) -> HeirMode:
        """Detect mode from environment."""
        env = os.getenv("BARTON_ENV", os.getenv("ENV", "prod")).lower()
        mode_map = {
            "prod": HeirMode.PROD,
            "production": HeirMode.PROD,
            "dev": HeirMode.DEV,
            "development": HeirMode.DEV,
            "test": HeirMode.TEST,
            "testing": HeirMode.TEST,
            "staging": HeirMode.STAGING,
            "stage": HeirMode.STAGING,
        }
        return mode_map.get(env, HeirMode.PROD)

    def generate(
        self,
        format: HeirFormat = HeirFormat.STANDARD,
        metadata: Dict[str, Any] = None
    ) -> HeirId:
        """
        Generate a new HEIR unique_id.

        Args:
            format: ID format (STANDARD or FORMAL)
            metadata: Optional metadata to attach

        Returns:
            HeirId with unique_id and metadata
        """
        now = datetime.now()
        random_hex = uuid.uuid4().hex[:8]

        if format == HeirFormat.STANDARD:
            # Format: hub-id-YYYYMMDDHHMMSS-random_hex
            timestamp_str = now.strftime("%Y%m%d%H%M%S")
            unique_id = f"{self.hub_id}-{timestamp_str}-{random_hex}"
        else:
            # Format: HEIR-YYYY-MM-SYSTEM-MODE-VN-random_hex
            unique_id = f"HEIR-{now.year}-{now.month:02d}-{self.system}-{self.mode.value}-{self.version}-{random_hex}"

        heir_id = HeirId(
            unique_id=unique_id,
            hub_id=self.hub_id,
            timestamp=now,
            mode=self.mode,
            format=format,
            random_component=random_hex,
            metadata=metadata or {},
        )

        # Store as current context
        self._local.current = heir_id

        return heir_id

    def current(self) -> Optional[HeirId]:
        """Get the current HEIR ID in this context."""
        return getattr(self._local, 'current', None)

    def set_current(self, heir_id: HeirId) -> None:
        """Set the current HEIR ID (for propagation across operations)."""
        self._local.current = heir_id

    def get_or_generate(
        self,
        format: HeirFormat = HeirFormat.STANDARD,
        metadata: Dict[str, Any] = None
    ) -> HeirId:
        """Get current HEIR ID or generate a new one if none exists."""
        current = self.current()
        if current is None:
            return self.generate(format, metadata)
        return current

    def clear(self) -> None:
        """Clear the current HEIR ID context."""
        self._local.current = None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_heir = None


def get_heir() -> HeirIdentity:
    """Get or create the global HEIR identity manager."""
    global _heir
    if _heir is None:
        _heir = HeirIdentity()
    return _heir


def generate_unique_id(
    format: HeirFormat = HeirFormat.STANDARD,
    metadata: Dict[str, Any] = None
) -> str:
    """
    Generate a new HEIR unique_id.

    This is the primary entry point for code that needs a unique_id.

    Args:
        format: ID format (default: STANDARD)
        metadata: Optional metadata

    Returns:
        The unique_id string

    Example:
        unique_id = generate_unique_id()
        # outreach-core-001-20260205143022-a1b2c3d4
    """
    return get_heir().generate(format, metadata).unique_id


def get_current_unique_id() -> Optional[str]:
    """Get the current unique_id if one exists in this context."""
    heir_id = get_heir().current()
    return heir_id.unique_id if heir_id else None


def require_unique_id() -> str:
    """
    Get the current unique_id or generate one if none exists.

    Use this when you need a unique_id but don't want to fail
    if one wasn't propagated from upstream.
    """
    return get_heir().get_or_generate().unique_id


# =============================================================================
# CONTEXT MANAGER
# =============================================================================

class HeirContext:
    """
    Context manager for HEIR identity scoping.

    Usage:
        with HeirContext() as heir_id:
            # All operations in this block share the same unique_id
            do_something(unique_id=heir_id.unique_id)
            do_something_else(unique_id=heir_id.unique_id)

        # Or with explicit ID
        with HeirContext(unique_id="existing-id-12345"):
            # Use existing ID
            pass
    """

    def __init__(
        self,
        unique_id: str = None,
        format: HeirFormat = HeirFormat.STANDARD,
        metadata: Dict[str, Any] = None
    ):
        self.unique_id = unique_id
        self.format = format
        self.metadata = metadata
        self._heir = get_heir()
        self._previous = None

    def __enter__(self) -> HeirId:
        # Save previous context
        self._previous = self._heir.current()

        if self.unique_id:
            # Use provided ID
            heir_id = HeirId(
                unique_id=self.unique_id,
                hub_id=self._heir.hub_id,
                timestamp=datetime.now(),
                mode=self._heir.mode,
                format=self.format,
                random_component="external",
                metadata=self.metadata or {},
            )
            self._heir.set_current(heir_id)
        else:
            # Generate new ID
            heir_id = self._heir.generate(self.format, self.metadata)

        return heir_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self._previous:
            self._heir.set_current(self._previous)
        else:
            self._heir.clear()
        return False


# =============================================================================
# DECORATOR
# =============================================================================

def with_heir_id(format: HeirFormat = HeirFormat.STANDARD):
    """
    Decorator to automatically generate and propagate HEIR ID.

    Usage:
        @with_heir_id()
        def my_function():
            # unique_id is available via get_current_unique_id()
            unique_id = get_current_unique_id()
            return do_work(unique_id)
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with HeirContext(format=format):
                return func(*args, **kwargs)
        return wrapper

    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes
    "HeirIdentity",
    "HeirId",
    "HeirMode",
    "HeirFormat",
    "HeirContext",
    # Functions
    "get_heir",
    "generate_unique_id",
    "get_current_unique_id",
    "require_unique_id",
    # Decorator
    "with_heir_id",
]
