"""
Email Verification Sub-Wheel
============================
A complete wheel for email verification within the People Node.

Hub: MillionVerifier API
Spokes: pattern_guesser, bulk_verifier, pattern_saver
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

# TODO: ctb/ was archived — bicycle_wheel module does not exist. Need to implement in src/sys/wheel/ or remove.
# from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Hub, SubWheel, Spoke
# from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import WheelResult, SpokeResult, FailureResult, ResultStatus, FailureType


logger = logging.getLogger(__name__)


@dataclass
class EmailCandidate:
    """An email candidate for verification"""
    person_id: str
    first_name: str
    last_name: str
    domain: str
    pattern: Optional[str] = None
    generated_email: Optional[str] = None
    is_verified: bool = False
    verification_result: Optional[str] = None
    verification_timestamp: Optional[datetime] = None


class EmailVerificationSubWheel(SubWheel):
    """
    Email Verification - Sub-wheel of People Node.

    This wheel has:
    - Hub: MillionVerifier API (the central verification service)
    - Spokes: pattern_guesser (FREE), bulk_verifier (CHEAP)
    - Failure Spokes: invalid_email, timeout_error, rate_limited
    """

    def __init__(self, millionverifier_api_key: Optional[str] = None):
        super().__init__(name="email_verification", hub_name="millionverifier")
        self.api_key = millionverifier_api_key

        # Configure hub for MillionVerifier
        self.hub.core_metric_name = "verification_success_rate"
        self.hub.core_metric_value = 0.0
        self.hub.anchor_fields = {
            'api_key_set': bool(millionverifier_api_key),
            'total_verified': 0,
            'total_valid': 0,
            'credits_used': 0
        }

        # Track stats
        self.stats = {
            'patterns_generated': 0,
            'emails_verified': 0,
            'valid': 0,
            'invalid': 0,
            'risky': 0,
            'unknown': 0
        }

    def rotate(self, data: EmailCandidate) -> WheelResult:
        """
        Process an email candidate through the verification wheel.

        Flow:
        1. Pattern Guesser generates email from pattern
        2. Bulk Verifier checks with MillionVerifier
        3. Route to success or failure spoke
        """
        result = WheelResult(wheel_name=self.name, started_at=datetime.now())

        # SPOKE 1: Pattern Guesser
        if not data.generated_email:
            generated = self.generate_email(data)
            if not generated:
                failure = FailureResult(
                    failure_type=FailureType.NO_PATTERN,
                    record_id=data.person_id,
                    original_data=data,
                    failure_reason="Could not generate email - missing pattern or domain",
                    resolution_path="manual_pattern_entry"
                )
                result.add_failure(failure)
                result.complete()
                return result

            data.generated_email = generated
            self.stats['patterns_generated'] += 1

        # SPOKE 2: Bulk Verifier
        verification = self.verify_email(data.generated_email)
        data.is_verified = verification['valid']
        data.verification_result = verification['result']
        data.verification_timestamp = datetime.now()

        self.stats['emails_verified'] += 1

        if verification['result'] == 'ok':
            self.stats['valid'] += 1
            result.add_success(SpokeResult(
                status=ResultStatus.SUCCESS,
                data=data,
                hub_signal={
                    'signal_type': 'email_verified',
                    'impact': 3.0,
                    'source': self.name
                }
            ))
        elif verification['result'] in ['invalid', 'disposable']:
            self.stats['invalid'] += 1
            result.add_failure(FailureResult(
                failure_type=FailureType.EMAIL_INVALID,
                record_id=data.person_id,
                original_data=data,
                failure_reason=f"Email invalid: {verification['result']}",
                resolution_path="try_alternate_pattern"
            ))
        elif verification['result'] == 'risky':
            self.stats['risky'] += 1
            # Risky emails can be used but flagged
            data.is_verified = True  # Accept with caution
            result.add_success(SpokeResult(
                status=ResultStatus.SUCCESS,
                data=data,
                metrics={'risky': True}
            ))
        else:
            self.stats['unknown'] += 1
            result.add_failure(FailureResult(
                failure_type=FailureType.EMAIL_INVALID,
                record_id=data.person_id,
                original_data=data,
                failure_reason=f"Verification unknown: {verification['result']}",
                resolution_path="manual_review"
            ))

        # Update hub metrics
        total = self.stats['valid'] + self.stats['invalid'] + self.stats['risky'] + self.stats['unknown']
        if total > 0:
            self.hub.core_metric_value = (self.stats['valid'] + self.stats['risky']) / total * 100
            self.hub.set_anchor('total_verified', total)
            self.hub.set_anchor('total_valid', self.stats['valid'] + self.stats['risky'])

        result.complete()
        return result

    def generate_email(self, data: EmailCandidate) -> Optional[str]:
        """
        Generate email from pattern.

        This wraps the existing pattern_guesser module.
        """
        if not data.domain or not data.pattern:
            return None

        if not data.first_name or not data.last_name:
            return None

        # Pattern substitution
        pattern = data.pattern.lower()
        first = data.first_name.lower()
        last = data.last_name.lower()

        # Common patterns
        pattern_map = {
            '{first}.{last}': f"{first}.{last}@{data.domain}",
            '{first}{last}': f"{first}{last}@{data.domain}",
            '{f}{last}': f"{first[0]}{last}@{data.domain}",
            '{first}_{last}': f"{first}_{last}@{data.domain}",
            '{first}': f"{first}@{data.domain}",
            '{last}': f"{last}@{data.domain}",
            '{f}.{last}': f"{first[0]}.{last}@{data.domain}",
            '{first}.{l}': f"{first}.{last[0]}@{data.domain}",
        }

        return pattern_map.get(pattern, f"{first}.{last}@{data.domain}")

    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify email with MillionVerifier.

        This wraps the existing bulk_verifier module.
        In test mode (no API key), returns mock results.
        """
        if not self.api_key:
            # Mock verification for testing
            logger.warning("No MillionVerifier API key - using mock verification")
            return {'valid': True, 'result': 'ok', 'mock': True}

        # Real verification would call the API here
        # For now, delegate to existing bulk_verifier
        try:
            # Import existing verifier
            from .....email.bulk_verifier import verify_single_email
            result = verify_single_email(email, self.api_key)
            return result
        except ImportError:
            logger.warning("bulk_verifier not available - using mock")
            return {'valid': True, 'result': 'ok', 'mock': True}

    def get_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        return {
            'patterns_generated': self.stats['patterns_generated'],
            'emails_verified': self.stats['emails_verified'],
            'valid': self.stats['valid'],
            'invalid': self.stats['invalid'],
            'risky': self.stats['risky'],
            'unknown': self.stats['unknown'],
            'success_rate': self.hub.core_metric_value
        }
