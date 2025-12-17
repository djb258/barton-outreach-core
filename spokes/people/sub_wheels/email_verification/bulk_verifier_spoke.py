"""
Bulk Verifier Spoke - MillionVerifier Integration
=================================================
Verifies emails with MillionVerifier API.

Cost: $37/10,000 verifications (batch)
      $0.001/email (real-time)

Wraps existing email/bulk_verifier.py with spoke interface.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
import os

from .....wheel.bicycle_wheel import Spoke, Hub
from .....wheel.wheel_result import SpokeResult, ResultStatus, FailureType


logger = logging.getLogger(__name__)


# MillionVerifier result codes
MV_RESULT_CODES = {
    'ok': {'valid': True, 'description': 'Valid email'},
    'catch_all': {'valid': True, 'description': 'Catch-all domain (risky)'},
    'unknown': {'valid': False, 'description': 'Unable to verify'},
    'invalid': {'valid': False, 'description': 'Invalid email'},
    'disposable': {'valid': False, 'description': 'Disposable email'},
    'role': {'valid': True, 'description': 'Role-based email (info@, support@)'},
    'risky': {'valid': True, 'description': 'Risky but deliverable'},
}


class BulkVerifierSpoke(Spoke):
    """
    Bulk Verifier - MillionVerifier email verification.

    Modes:
    - Single: Real-time verification ($0.001/email)
    - Batch: Upload CSV for batch processing ($37/10K)
    """

    def __init__(self, hub: Hub, api_key: Optional[str] = None):
        super().__init__(name="bulk_verifier", hub=hub)
        self.api_key = api_key or os.getenv('MILLIONVERIFIER_API_KEY')

        self.stats = {
            'total_verified': 0,
            'ok': 0,
            'catch_all': 0,
            'risky': 0,
            'invalid': 0,
            'disposable': 0,
            'unknown': 0,
            'api_errors': 0
        }

    def process(self, data: Any) -> SpokeResult:
        """
        Verify an email address.

        Expects data with: generated_email
        """
        if not hasattr(data, 'generated_email') or not data.generated_email:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Missing generated_email to verify"
            )

        email = data.generated_email

        # Verify the email
        result = self.verify_email(email)

        self.stats['total_verified'] += 1
        self.stats[result['result_code']] = self.stats.get(result['result_code'], 0) + 1

        # Update data
        data.is_verified = result['valid']
        data.verification_result = result['result_code']
        data.verification_timestamp = datetime.now()

        if result['valid']:
            return SpokeResult(
                status=ResultStatus.SUCCESS,
                data=data,
                hub_signal={
                    'signal_type': 'email_verified',
                    'impact': 3.0,
                    'source': self.name
                },
                metrics={
                    'result_code': result['result_code'],
                    'subresult': result.get('subresult')
                }
            )
        else:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.EMAIL_INVALID,
                failure_reason=f"Email verification failed: {result['result_code']}",
                data=data,
                metrics=result
            )

    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify a single email with MillionVerifier.

        Returns:
            {
                'valid': bool,
                'result_code': str (ok, invalid, etc.),
                'subresult': str (optional additional info),
                'quality': float (0-100),
                'free': bool (is free email provider)
            }
        """
        if not self.api_key:
            logger.warning("No MillionVerifier API key - returning mock result")
            return {
                'valid': True,
                'result_code': 'ok',
                'subresult': 'mock_verification',
                'quality': 100.0,
                'free': False,
                'mock': True
            }

        try:
            import aiohttp
            import asyncio

            async def _verify():
                url = f"https://api.millionverifier.com/api/v3/?api={self.api_key}&email={email}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            result_code = data.get('result', 'unknown')
                            result_info = MV_RESULT_CODES.get(result_code, {'valid': False})

                            return {
                                'valid': result_info['valid'],
                                'result_code': result_code,
                                'subresult': data.get('subresult'),
                                'quality': data.get('quality', 0),
                                'free': data.get('free', False)
                            }
                        else:
                            self.stats['api_errors'] += 1
                            return {
                                'valid': False,
                                'result_code': 'api_error',
                                'subresult': f"HTTP {response.status}"
                            }

            # Run async verification
            return asyncio.run(_verify())

        except Exception as e:
            self.stats['api_errors'] += 1
            logger.error(f"MillionVerifier error: {e}")
            return {
                'valid': False,
                'result_code': 'api_error',
                'subresult': str(e)
            }

    def verify_batch(self, emails: List[str]) -> List[Dict[str, Any]]:
        """
        Verify multiple emails in batch.

        More cost-effective for large volumes.
        """
        results = []
        for email in emails:
            result = self.verify_email(email)
            result['email'] = email
            results.append(result)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        total = self.stats['total_verified']
        valid = self.stats['ok'] + self.stats['catch_all'] + self.stats['risky']

        return {
            'total_verified': total,
            'valid': valid,
            'valid_rate': f"{valid / max(total, 1) * 100:.1f}%",
            'breakdown': {
                'ok': self.stats['ok'],
                'catch_all': self.stats['catch_all'],
                'risky': self.stats['risky'],
                'invalid': self.stats['invalid'],
                'disposable': self.stats['disposable'],
                'unknown': self.stats['unknown']
            },
            'api_errors': self.stats['api_errors']
        }
