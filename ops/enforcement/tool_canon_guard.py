"""
Tool Canon Guard - Pre-Invocation Validation

Authority: TOOL_CANON_ENFORCEMENT.md v1.0.0
Doctrine: "Snap-on - One tool, many jobs, config is the variable"

This module enforces the Tool Canon rules:
1. Tool must be in SNAP_ON_TOOLBOX.yaml
2. Tool must be allowed for the invoking hub
3. Tier 2 tools require gate conditions
4. Banned tools/vendors/libraries are rejected
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ToolTier(Enum):
    """Tool tier classification"""
    TIER_0 = "FREE"       # No gate required
    TIER_1 = "CHEAP"      # Budget-capped
    TIER_2 = "SURGICAL"   # Gate required


class InteractionType(Enum):
    """Tool interaction types"""
    READ = "READ"         # Fetch data from external source without mutation
    WRITE = "WRITE"       # Persist data to internal storage
    ENRICH = "ENRICH"     # Augment existing record with external data
    VALIDATE = "VALIDATE" # Verify correctness of existing data


class ViolationSeverity(Enum):
    """Violation severity levels"""
    CRITICAL = "CRITICAL"  # PARK immediately
    HIGH = "HIGH"          # RETRY, blocks promotion
    MEDIUM = "MEDIUM"      # RETRY, no block
    LOW = "LOW"            # IGNORE


class ViolationDisposition(Enum):
    """What to do with a violation"""
    PARK = "PARK"       # Hold for manual review
    RETRY = "RETRY"     # Queue for retry
    ARCHIVE = "ARCHIVE" # Move to archive
    IGNORE = "IGNORE"   # Log only


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ToolDefinition:
    """Definition of a tool in the canon"""
    tool_id: str
    tool_name: str
    software: str
    purpose: str
    tier: ToolTier
    allowed_hubs: List[str]
    interaction_types: List[InteractionType]
    gate_conditions: Optional[Dict[str, Any]] = None
    monthly_budget: Optional[str] = None


@dataclass
class GateCondition:
    """Gate condition for Tier 2 tools"""
    condition_name: str
    required_state: Any
    hub: str


@dataclass
class ToolViolation:
    """A tool canon violation"""
    violation_code: str
    tool_id: str
    hub_id: str
    severity: ViolationSeverity
    disposition: ViolationDisposition
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# TOOL CANON REGISTRY
# =============================================================================

# Hub ID constants
HUB_COMPANY_LIFECYCLE = "HUB-COMPANY-LIFECYCLE"
HUB_COMPANY_TARGET = "HUB-COMPANY-TARGET"
HUB_DOL = "HUB-DOL"
HUB_PEOPLE = "HUB-PEOPLE"
HUB_TALENT_FLOW = "HUB-TALENT-FLOW"
HUB_BLOG = "HUB-BLOG-001"
HUB_OUTREACH = "HUB-OUTREACH"

# Tier 0: Free Tools
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "TOOL-001": ToolDefinition(
        tool_id="TOOL-001",
        tool_name="MXLookup",
        software="dnspython",
        purpose="DNS MX record validation",
        tier=ToolTier.TIER_0,
        allowed_hubs=[HUB_COMPANY_TARGET, HUB_PEOPLE],
        interaction_types=[InteractionType.VALIDATE],
    ),
    "TOOL-002": ToolDefinition(
        tool_id="TOOL-002",
        tool_name="SMTPCheck",
        software="smtplib (stdlib)",
        purpose="SMTP deliverability validation",
        tier=ToolTier.TIER_0,
        allowed_hubs=[HUB_PEOPLE],
        interaction_types=[InteractionType.VALIDATE],
    ),
    "TOOL-003": ToolDefinition(
        tool_id="TOOL-003",
        tool_name="LinkedInCheck",
        software="httpx",
        purpose="LinkedIn URL existence check",
        tier=ToolTier.TIER_0,
        allowed_hubs=[HUB_COMPANY_TARGET, HUB_PEOPLE, HUB_TALENT_FLOW],
        interaction_types=[InteractionType.VALIDATE],
    ),
    # Tier 1: Cheap Tools
    "TOOL-004": ToolDefinition(
        tool_id="TOOL-004",
        tool_name="Firecrawl",
        software="Firecrawl API",
        purpose="JS-rendered page scraping",
        tier=ToolTier.TIER_1,
        allowed_hubs=[HUB_BLOG],
        interaction_types=[InteractionType.READ],
        monthly_budget="500/mo free",
    ),
    "TOOL-005": ToolDefinition(
        tool_id="TOOL-005",
        tool_name="ScraperAPI",
        software="ScraperAPI",
        purpose="Anti-bot proxy",
        tier=ToolTier.TIER_1,
        allowed_hubs=[HUB_BLOG],
        interaction_types=[InteractionType.READ],
        monthly_budget="$100/mo",
    ),
    "TOOL-006": ToolDefinition(
        tool_id="TOOL-006",
        tool_name="GooglePlaces",
        software="Google Places API",
        purpose="Business/address validation",
        tier=ToolTier.TIER_1,
        allowed_hubs=[HUB_COMPANY_TARGET],
        interaction_types=[InteractionType.VALIDATE],
        monthly_budget="$50/mo",
    ),
    "TOOL-007": ToolDefinition(
        tool_id="TOOL-007",
        tool_name="ComposioRouter",
        software="Composio",
        purpose="Integration router (500+ apps)",
        tier=ToolTier.TIER_1,
        allowed_hubs=[HUB_OUTREACH],
        interaction_types=[InteractionType.WRITE],
        monthly_budget="$30/mo fixed",
    ),
    # Tier 2: Surgical Tools (Gate Required)
    "TOOL-008": ToolDefinition(
        tool_id="TOOL-008",
        tool_name="HunterEnricher",
        software="Hunter.io API",
        purpose="Email finder, domain search",
        tier=ToolTier.TIER_2,
        allowed_hubs=[HUB_COMPANY_TARGET, HUB_PEOPLE],
        interaction_types=[InteractionType.ENRICH],
        gate_conditions={
            "domain_verified": True,
            "mx_present": True,
            "pattern_attempts": {"max": 1},
        },
    ),
    "TOOL-009": ToolDefinition(
        tool_id="TOOL-009",
        tool_name="ApolloEnricher",
        software="Apollo.io API",
        purpose="Contact/company enrichment",
        tier=ToolTier.TIER_2,
        allowed_hubs=[HUB_PEOPLE],
        interaction_types=[InteractionType.ENRICH],
        gate_conditions={
            "slot_unfilled": True,
            "company_target_pass": True,
            "enrichment_attempts": {"max": 1},
        },
    ),
    "TOOL-010": ToolDefinition(
        tool_id="TOOL-010",
        tool_name="EmailVerifier",
        software="MillionVerifier API",
        purpose="Pre-send email verification",
        tier=ToolTier.TIER_2,
        allowed_hubs=[HUB_PEOPLE],
        interaction_types=[InteractionType.VALIDATE],
        gate_conditions={
            "email_generated": True,
            "email_format_valid": True,
            "verification_attempts": {"max": 1},
        },
    ),
    "TOOL-011": ToolDefinition(
        tool_id="TOOL-011",
        tool_name="RetellCaller",
        software="Retell AI API",
        purpose="AI voice calling",
        tier=ToolTier.TIER_2,
        allowed_hubs=[HUB_OUTREACH],
        interaction_types=[InteractionType.WRITE],
        gate_conditions={
            "human_approval": True,
            "bit_score": {"min": 75},
            "contact_verified": True,
            "dnc_checked": True,
            "calling_hours": "9am-8pm local",
        },
    ),
}

# Banned vendors
BANNED_VENDORS = {
    "ZoomInfo": "Cost prohibitive",
    "Lusha": "Cost prohibitive",
    "Seamless.AI": "Cost prohibitive",
    "LinkedIn Sales Navigator": "ToS violation + cost",
    "Diffbot": "Per-page pricing",
    "Clearbit": "Pricing changed",
    "Clay": "Margin markup",
    "Prospeo": "Redundant",
    "Snov": "Redundant",
}

# Banned libraries
BANNED_LIBRARIES = {
    "selenium": "Overhead",
    "requests": "Legacy",
    "lxml": "Performance",
    "scrapy": "Overkill",
    "beautifulsoup4": "Performance",
}

# Banned patterns
BANNED_PATTERNS = {
    "bulk_enrichment": "Violates surgical doctrine",
    "llm_as_spine": "LLM is tail arbitration only",
    "recursive_crawling": "Cost explosion",
    "scraping_linkedin_profiles": "ToS violation",
}


# =============================================================================
# TOOL CANON GUARD
# =============================================================================

class ToolCanonGuard:
    """
    Enforces tool canon rules before any tool invocation.

    Usage:
        guard = ToolCanonGuard()
        result = guard.validate(
            tool_id="TOOL-008",
            hub_id="HUB-COMPANY-TARGET",
            interaction_type=InteractionType.ENRICH,
            gate_state={"domain_verified": True, "mx_present": True}
        )
        if not result.is_valid:
            # Handle violation
            raise ToolCanonViolationError(result.violation)
    """

    def __init__(self):
        self.tool_registry = TOOL_REGISTRY
        self.banned_vendors = BANNED_VENDORS
        self.banned_libraries = BANNED_LIBRARIES
        self.banned_patterns = BANNED_PATTERNS

    def validate(
        self,
        tool_id: str,
        hub_id: str,
        interaction_type: Optional[InteractionType] = None,
        gate_state: Optional[Dict[str, Any]] = None,
    ) -> "ValidationResult":
        """
        Validate a tool invocation against the canon.

        Args:
            tool_id: The tool ID (e.g., "TOOL-008")
            hub_id: The invoking hub ID (e.g., "HUB-COMPANY-TARGET")
            interaction_type: The intended interaction type
            gate_state: Current state for gate condition evaluation (Tier 2 only)

        Returns:
            ValidationResult with is_valid flag and optional violation
        """
        # Step 1: Check banned list (not applicable to tool_id, but good practice)
        # Banned checks are for vendor/library names, not tool IDs

        # Step 2: Check tool registry
        if tool_id not in self.tool_registry:
            return ValidationResult(
                is_valid=False,
                violation=ToolViolation(
                    violation_code="V-TOOL-001",
                    tool_id=tool_id,
                    hub_id=hub_id,
                    severity=ViolationSeverity.CRITICAL,
                    disposition=ViolationDisposition.PARK,
                    message=f"Tool {tool_id} not in SNAP_ON_TOOLBOX.yaml (absence = banned)",
                    context={"attempted_tool": tool_id},
                ),
            )

        tool = self.tool_registry[tool_id]

        # Step 3: Check hub scope
        if hub_id not in tool.allowed_hubs:
            return ValidationResult(
                is_valid=False,
                violation=ToolViolation(
                    violation_code="V-SCOPE-001",
                    tool_id=tool_id,
                    hub_id=hub_id,
                    severity=ViolationSeverity.CRITICAL,
                    disposition=ViolationDisposition.PARK,
                    message=f"Tool {tool_id} not allowed for hub {hub_id}. Allowed: {tool.allowed_hubs}",
                    context={"allowed_hubs": tool.allowed_hubs},
                ),
            )

        # Step 4: Check interaction type (if provided)
        if interaction_type and interaction_type not in tool.interaction_types:
            return ValidationResult(
                is_valid=False,
                violation=ToolViolation(
                    violation_code="V-TYPE-001",
                    tool_id=tool_id,
                    hub_id=hub_id,
                    severity=ViolationSeverity.HIGH,
                    disposition=ViolationDisposition.PARK,
                    message=f"Interaction type {interaction_type.value} not permitted for tool {tool_id}",
                    context={
                        "attempted_interaction": interaction_type.value,
                        "allowed_interactions": [t.value for t in tool.interaction_types],
                    },
                ),
            )

        # Step 5: Check tier and gate conditions
        if tool.tier == ToolTier.TIER_2:
            if not tool.gate_conditions:
                # Tier 2 tool without defined gates - should not happen
                logger.warning(f"Tier 2 tool {tool_id} has no gate conditions defined")
            else:
                gate_result = self._check_gate_conditions(tool, gate_state or {})
                if not gate_result.is_valid:
                    return gate_result

        # All checks passed
        return ValidationResult(is_valid=True)

    def _check_gate_conditions(
        self,
        tool: ToolDefinition,
        gate_state: Dict[str, Any],
    ) -> "ValidationResult":
        """Check gate conditions for Tier 2 tools."""
        if not tool.gate_conditions:
            return ValidationResult(is_valid=True)

        failed_conditions = []

        for condition_name, required_value in tool.gate_conditions.items():
            actual_value = gate_state.get(condition_name)

            # Handle different condition types
            if isinstance(required_value, dict):
                # Complex condition (e.g., {"max": 1} or {"min": 75})
                if "max" in required_value:
                    if actual_value is None or actual_value >= required_value["max"]:
                        failed_conditions.append(
                            f"{condition_name}: expected < {required_value['max']}, got {actual_value}"
                        )
                elif "min" in required_value:
                    if actual_value is None or actual_value < required_value["min"]:
                        failed_conditions.append(
                            f"{condition_name}: expected >= {required_value['min']}, got {actual_value}"
                        )
            elif isinstance(required_value, bool):
                if actual_value != required_value:
                    failed_conditions.append(
                        f"{condition_name}: expected {required_value}, got {actual_value}"
                    )
            elif isinstance(required_value, str):
                # String conditions are informational (e.g., "9am-8pm local")
                # Caller is responsible for checking these
                pass
            else:
                if actual_value != required_value:
                    failed_conditions.append(
                        f"{condition_name}: expected {required_value}, got {actual_value}"
                    )

        if failed_conditions:
            return ValidationResult(
                is_valid=False,
                violation=ToolViolation(
                    violation_code="V-GATE-001",
                    tool_id=tool.tool_id,
                    hub_id="",  # Will be set by caller
                    severity=ViolationSeverity.CRITICAL,
                    disposition=ViolationDisposition.PARK,
                    message=f"Gate conditions not met for {tool.tool_id}: {'; '.join(failed_conditions)}",
                    context={
                        "failed_conditions": failed_conditions,
                        "provided_state": gate_state,
                    },
                ),
            )

        return ValidationResult(is_valid=True)

    def check_vendor(self, vendor_name: str) -> Optional[ToolViolation]:
        """Check if a vendor is banned."""
        if vendor_name in self.banned_vendors:
            return ToolViolation(
                violation_code="V-TOOL-002",
                tool_id="",
                hub_id="",
                severity=ViolationSeverity.CRITICAL,
                disposition=ViolationDisposition.PARK,
                message=f"Banned vendor: {vendor_name}. Reason: {self.banned_vendors[vendor_name]}",
                context={"vendor": vendor_name},
            )
        return None

    def check_library(self, library_name: str) -> Optional[ToolViolation]:
        """Check if a library is banned."""
        if library_name in self.banned_libraries:
            return ToolViolation(
                violation_code="V-TOOL-002",
                tool_id="",
                hub_id="",
                severity=ViolationSeverity.CRITICAL,
                disposition=ViolationDisposition.PARK,
                message=f"Banned library: {library_name}. Reason: {self.banned_libraries[library_name]}",
                context={"library": library_name},
            )
        return None

    def check_pattern(self, pattern_name: str) -> Optional[ToolViolation]:
        """Check if a pattern is banned."""
        if pattern_name in self.banned_patterns:
            return ToolViolation(
                violation_code="V-TOOL-002",
                tool_id="",
                hub_id="",
                severity=ViolationSeverity.CRITICAL,
                disposition=ViolationDisposition.PARK,
                message=f"Banned pattern: {pattern_name}. Reason: {self.banned_patterns[pattern_name]}",
                context={"pattern": pattern_name},
            )
        return None


@dataclass
class ValidationResult:
    """Result of a tool canon validation"""
    is_valid: bool
    violation: Optional[ToolViolation] = None


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ToolCanonViolationError(Exception):
    """Raised when a tool canon violation is detected"""

    def __init__(self, violation: ToolViolation):
        self.violation = violation
        super().__init__(
            f"[{violation.violation_code}] {violation.message} "
            f"(severity={violation.severity.value}, disposition={violation.disposition.value})"
        )


# =============================================================================
# DECORATOR FOR TOOL INVOCATIONS
# =============================================================================

def enforce_tool_canon(tool_id: str, hub_id: str, interaction_type: Optional[InteractionType] = None):
    """
    Decorator to enforce tool canon on a function that invokes a tool.

    Usage:
        @enforce_tool_canon("TOOL-008", "HUB-COMPANY-TARGET", InteractionType.ENRICH)
        def call_hunter_api(domain: str, gate_state: dict):
            # The gate_state dict should be passed as kwarg
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            guard = ToolCanonGuard()
            gate_state = kwargs.get("gate_state", {})

            result = guard.validate(
                tool_id=tool_id,
                hub_id=hub_id,
                interaction_type=interaction_type,
                gate_state=gate_state,
            )

            if not result.is_valid:
                raise ToolCanonViolationError(result.violation)

            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Example: Validate a tool invocation
    guard = ToolCanonGuard()

    # Valid Tier 0 tool
    result = guard.validate(
        tool_id="TOOL-001",
        hub_id=HUB_COMPANY_TARGET,
        interaction_type=InteractionType.VALIDATE,
    )
    print(f"MXLookup from Company Target: valid={result.is_valid}")

    # Invalid: Tool not allowed for hub
    result = guard.validate(
        tool_id="TOOL-004",  # Firecrawl
        hub_id=HUB_COMPANY_TARGET,  # Not allowed
    )
    print(f"Firecrawl from Company Target: valid={result.is_valid}")
    if not result.is_valid:
        print(f"  Violation: {result.violation.violation_code} - {result.violation.message}")

    # Tier 2 with gate conditions
    result = guard.validate(
        tool_id="TOOL-008",  # HunterEnricher
        hub_id=HUB_COMPANY_TARGET,
        interaction_type=InteractionType.ENRICH,
        gate_state={
            "domain_verified": True,
            "mx_present": True,
            "pattern_attempts": 0,
        },
    )
    print(f"HunterEnricher with valid gates: valid={result.is_valid}")

    # Tier 2 with failed gate
    result = guard.validate(
        tool_id="TOOL-008",
        hub_id=HUB_COMPANY_TARGET,
        gate_state={
            "domain_verified": False,  # Gate fail
            "mx_present": True,
        },
    )
    print(f"HunterEnricher with failed gate: valid={result.is_valid}")
    if not result.is_valid:
        print(f"  Violation: {result.violation.violation_code} - {result.violation.message}")
