"""
Pattern Guesser Spoke - FREE Email Generation
==============================================
Generates email candidates from name + domain + pattern.

Cost: FREE (no API calls)

Wraps existing email/pattern_guesser.py with spoke interface.
"""

from typing import Any, Dict, List, Optional
import logging

from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType


logger = logging.getLogger(__name__)


# Standard email patterns
PATTERN_PRIORITY = [
    '{first}.{last}',      # john.smith@company.com
    '{first}{last}',       # johnsmith@company.com
    '{f}{last}',           # jsmith@company.com
    '{first}_{last}',      # john_smith@company.com
    '{first}',             # john@company.com
    '{last}',              # smith@company.com
    '{f}.{last}',          # j.smith@company.com
    '{first}.{l}',         # john.s@company.com
    '{l}{first}',          # sjohn@company.com
    '{last}.{first}',      # smith.john@company.com
]


class PatternGuesserSpoke(Spoke):
    """
    Pattern Guesser - FREE email generation.

    Generates email candidates from:
    - First name
    - Last name
    - Domain
    - Pattern (optional - will try all patterns if not provided)
    """

    def __init__(self, hub: Hub):
        super().__init__(name="pattern_guesser", hub=hub)
        self.stats = {
            'total_processed': 0,
            'patterns_applied': 0,
            'generated': 0,
            'failed': 0
        }

    def process(self, data: Any) -> SpokeResult:
        """
        Generate email from pattern.

        Expects data with: first_name, last_name, domain, pattern (optional)
        """
        self.stats['total_processed'] += 1

        # Validate inputs
        if not hasattr(data, 'first_name') or not data.first_name:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Missing first_name"
            )

        if not hasattr(data, 'last_name') or not data.last_name:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Missing last_name"
            )

        if not hasattr(data, 'domain') or not data.domain:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_PATTERN,
                failure_reason="Missing domain - cannot generate email"
            )

        # Get pattern or use first in priority list
        pattern = getattr(data, 'pattern', None) or PATTERN_PRIORITY[0]

        # Generate email
        email = self.generate_email(
            first_name=data.first_name,
            last_name=data.last_name,
            domain=data.domain,
            pattern=pattern
        )

        if not email:
            self.stats['failed'] += 1
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_PATTERN,
                failure_reason="Failed to generate email from pattern"
            )

        self.stats['generated'] += 1
        self.stats['patterns_applied'] += 1

        # Update data
        data.generated_email = email

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=data,
            metrics={
                'pattern_used': pattern,
                'generated_email': email
            }
        )

    def generate_email(
        self,
        first_name: str,
        last_name: str,
        domain: str,
        pattern: str
    ) -> Optional[str]:
        """
        Generate a single email from pattern.

        Pattern placeholders:
        - {first}: Full first name
        - {last}: Full last name
        - {f}: First initial
        - {l}: Last initial
        """
        if not all([first_name, last_name, domain]):
            return None

        # Normalize inputs
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        domain = domain.lower().strip()

        # Remove any non-alphanumeric from names (except common patterns)
        first = ''.join(c for c in first if c.isalnum())
        last = ''.join(c for c in last if c.isalnum())

        if not first or not last:
            return None

        # Pattern replacement
        email_local = pattern.lower()
        email_local = email_local.replace('{first}', first)
        email_local = email_local.replace('{last}', last)
        email_local = email_local.replace('{f}', first[0])
        email_local = email_local.replace('{l}', last[0])

        return f"{email_local}@{domain}"

    def generate_all_candidates(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> List[str]:
        """
        Generate all possible email candidates for a person.

        Useful when pattern is unknown - try all patterns.
        """
        candidates = []
        for pattern in PATTERN_PRIORITY:
            email = self.generate_email(first_name, last_name, domain, pattern)
            if email and email not in candidates:
                candidates.append(email)
        return candidates

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            'total_processed': self.stats['total_processed'],
            'generated': self.stats['generated'],
            'failed': self.stats['failed'],
            'success_rate': (
                self.stats['generated'] / max(self.stats['total_processed'], 1) * 100
            )
        }
