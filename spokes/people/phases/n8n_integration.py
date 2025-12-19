"""
n8n Queue Integration for Phase 7
=================================
Sends enrichment queue items to n8n for processing.
n8n handles the actual enrichment workflow.

Environment Variables:
- N8N_WEBHOOK_URL: Base URL for n8n webhooks
- N8N_API_KEY: API key for authentication (optional)
- N8N_HOSTINGER_URL: Alternative Hostinger-hosted n8n URL
"""

import os
import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class N8NConfig:
    """n8n integration configuration."""
    webhook_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 50
    enabled: bool = True


def load_n8n_config() -> N8NConfig:
    """Load n8n configuration from environment."""
    # Try multiple URL sources
    webhook_url = (
        os.getenv("N8N_WEBHOOK_URL") or
        os.getenv("N8N_HOSTINGER_URL") or
        "https://srv1153077.hstgr.cloud:5678"
    )

    return N8NConfig(
        webhook_url=webhook_url,
        api_key=os.getenv("N8N_API_KEY"),
        timeout=int(os.getenv("N8N_TIMEOUT", "30")),
        max_retries=int(os.getenv("N8N_MAX_RETRIES", "3")),
        batch_size=int(os.getenv("N8N_BATCH_SIZE", "50")),
        enabled=os.getenv("N8N_ENABLED", "true").lower() == "true"
    )


# =============================================================================
# N8N QUEUE TRIGGER
# =============================================================================

class N8NQueueTrigger:
    """
    Triggers n8n workflows for enrichment queue items.

    Workflow Types:
    - pattern_discovery: Find email patterns for companies
    - slot_enrichment: Find people for empty slots
    - email_verification: Verify generated emails
    - data_quality: Fix missing/invalid data
    """

    # Webhook paths for different queue types
    WEBHOOK_PATHS = {
        'pattern_missing': '/webhook/enrichment/pattern-discovery',
        'pattern_low_confidence': '/webhook/enrichment/pattern-verify',
        'slot_empty_chro': '/webhook/enrichment/slot-fill',
        'slot_empty_hr_manager': '/webhook/enrichment/slot-fill',
        'slot_empty_benefits': '/webhook/enrichment/slot-fill',
        'slot_empty_payroll': '/webhook/enrichment/slot-fill',
        'slot_empty_hr_support': '/webhook/enrichment/slot-fill',
        'slot_collision': '/webhook/enrichment/slot-resolve',
        'email_generation_failed': '/webhook/enrichment/email-verify',
        'email_low_confidence': '/webhook/enrichment/email-verify',
        'missing_company_id': '/webhook/enrichment/company-match',
        'missing_name': '/webhook/enrichment/data-quality',
        'missing_title': '/webhook/enrichment/data-quality',
    }

    def __init__(self, config: N8NConfig = None):
        """Initialize n8n queue trigger."""
        self.config = config or load_n8n_config()
        self._stats = {
            'total_triggered': 0,
            'successful': 0,
            'failed': 0,
            'retried': 0,
            'batches_sent': 0
        }

    def trigger_queue_items(
        self,
        queue_items: List[Dict[str, Any]],
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Send queue items to n8n for processing.

        Args:
            queue_items: List of queue item dicts
            correlation_id: Correlation ID for tracing

        Returns:
            Dict with trigger results
        """
        if not self.config.enabled:
            logger.info("n8n integration disabled - skipping")
            return {'triggered': 0, 'skipped': len(queue_items), 'reason': 'disabled'}

        if not queue_items:
            return {'triggered': 0, 'skipped': 0}

        try:
            import requests
        except ImportError:
            logger.error("requests library not installed")
            return {'triggered': 0, 'skipped': len(queue_items), 'reason': 'no_requests_lib'}

        results = {
            'triggered': 0,
            'failed': 0,
            'errors': [],
            'batches': []
        }

        # Group items by reason (different workflows)
        grouped = {}
        for item in queue_items:
            reason = item.get('reason', 'pattern_missing')
            if reason not in grouped:
                grouped[reason] = []
            grouped[reason].append(item)

        # Process each group
        for reason, items in grouped.items():
            webhook_path = self.WEBHOOK_PATHS.get(reason, '/webhook/enrichment/generic')
            webhook_url = f"{self.config.webhook_url.rstrip('/')}{webhook_path}"

            # Process in batches
            for i in range(0, len(items), self.config.batch_size):
                batch = items[i:i + self.config.batch_size]
                batch_result = self._send_batch(
                    webhook_url=webhook_url,
                    batch=batch,
                    reason=reason,
                    correlation_id=correlation_id
                )

                results['batches'].append(batch_result)

                if batch_result['success']:
                    results['triggered'] += len(batch)
                else:
                    results['failed'] += len(batch)
                    results['errors'].append(batch_result.get('error', 'Unknown error'))

        self._stats['total_triggered'] += results['triggered']
        self._stats['successful'] += results['triggered']
        self._stats['failed'] += results['failed']
        self._stats['batches_sent'] += len(results['batches'])

        return results

    def _send_batch(
        self,
        webhook_url: str,
        batch: List[Dict[str, Any]],
        reason: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Send a batch of items to n8n webhook.

        Args:
            webhook_url: Full webhook URL
            batch: List of queue items
            reason: Queue reason
            correlation_id: Correlation ID

        Returns:
            Dict with batch result
        """
        try:
            import requests
        except ImportError:
            return {'success': False, 'error': 'requests not installed'}

        payload = {
            'correlation_id': correlation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'reason': reason,
            'item_count': len(batch),
            'items': batch
        }

        headers = {
            'Content-Type': 'application/json',
            'X-Correlation-ID': correlation_id
        }

        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'

        attempt = 0
        last_error = None

        while attempt < self.config.max_retries:
            try:
                response = requests.post(
                    webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout
                )

                if response.status_code in (200, 201, 202):
                    logger.info(
                        f"n8n trigger successful: {len(batch)} items to {webhook_url}"
                    )
                    return {
                        'success': True,
                        'status_code': response.status_code,
                        'item_count': len(batch),
                        'webhook_url': webhook_url
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"n8n trigger failed: {last_error}")

            except requests.Timeout:
                last_error = "Request timeout"
                logger.warning(f"n8n trigger timeout: {webhook_url}")
                self._stats['retried'] += 1

            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"n8n trigger error: {e}")
                self._stats['retried'] += 1

            attempt += 1
            if attempt < self.config.max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff

        return {
            'success': False,
            'error': last_error,
            'item_count': len(batch),
            'webhook_url': webhook_url,
            'attempts': attempt
        }

    def trigger_single(
        self,
        queue_item: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """
        Trigger a single queue item.

        Args:
            queue_item: Queue item dict
            correlation_id: Correlation ID

        Returns:
            Trigger result
        """
        return self.trigger_queue_items([queue_item], correlation_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get trigger statistics."""
        return {
            **self._stats,
            'config': {
                'webhook_url': self.config.webhook_url,
                'enabled': self.config.enabled,
                'batch_size': self.config.batch_size
            }
        }


# =============================================================================
# N8N CALLBACK HANDLER
# =============================================================================

class N8NCallbackHandler:
    """
    Handles callbacks from n8n after enrichment processing.

    Expected callback payload:
    {
        "correlation_id": "...",
        "queue_id": "...",
        "status": "completed" | "failed" | "partial",
        "result": { ... enrichment data ... },
        "error": "..." (if failed)
    }
    """

    def __init__(self):
        """Initialize callback handler."""
        self._processed = []

    def handle_callback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process callback from n8n.

        Args:
            payload: Callback payload from n8n

        Returns:
            Processing result
        """
        correlation_id = payload.get('correlation_id', 'unknown')
        queue_id = payload.get('queue_id')
        status = payload.get('status', 'unknown')
        result_data = payload.get('result', {})
        error = payload.get('error')

        logger.info(
            f"n8n callback received: queue_id={queue_id}, status={status}, "
            f"correlation_id={correlation_id}"
        )

        self._processed.append({
            'queue_id': queue_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        })

        if status == 'completed':
            return self._handle_completed(queue_id, result_data, correlation_id)
        elif status == 'failed':
            return self._handle_failed(queue_id, error, correlation_id)
        elif status == 'partial':
            return self._handle_partial(queue_id, result_data, correlation_id)
        else:
            return {'processed': False, 'reason': f'Unknown status: {status}'}

    def _handle_completed(
        self,
        queue_id: str,
        result_data: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """Handle completed enrichment."""
        # Extract result type
        result_type = result_data.get('type', 'unknown')

        if result_type == 'pattern':
            # Pattern discovered
            pattern = result_data.get('pattern')
            domain = result_data.get('domain')
            confidence = result_data.get('confidence', 0.0)

            logger.info(
                f"Pattern discovered via n8n: {domain} → {pattern} "
                f"(confidence: {confidence})"
            )

            return {
                'processed': True,
                'result_type': 'pattern',
                'pattern': pattern,
                'domain': domain,
                'confidence': confidence
            }

        elif result_type == 'person':
            # Person found for slot
            person_data = result_data.get('person', {})

            logger.info(
                f"Person found via n8n: {person_data.get('full_name', 'unknown')}"
            )

            return {
                'processed': True,
                'result_type': 'person',
                'person': person_data
            }

        else:
            return {
                'processed': True,
                'result_type': result_type,
                'data': result_data
            }

    def _handle_failed(
        self,
        queue_id: str,
        error: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Handle failed enrichment."""
        logger.warning(f"n8n enrichment failed: queue_id={queue_id}, error={error}")

        return {
            'processed': False,
            'error': error,
            'should_retry': True
        }

    def _handle_partial(
        self,
        queue_id: str,
        result_data: Dict[str, Any],
        correlation_id: str
    ) -> Dict[str, Any]:
        """Handle partial enrichment (some items succeeded, some failed)."""
        succeeded = result_data.get('succeeded', [])
        failed = result_data.get('failed', [])

        logger.info(
            f"n8n partial result: {len(succeeded)} succeeded, {len(failed)} failed"
        )

        return {
            'processed': True,
            'partial': True,
            'succeeded_count': len(succeeded),
            'failed_count': len(failed),
            'succeeded': succeeded,
            'failed': failed
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def trigger_enrichment_queue(
    queue_items: List[Dict[str, Any]],
    correlation_id: str,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function to trigger n8n enrichment queue.

    Args:
        queue_items: List of queue item dicts
        correlation_id: Correlation ID
        config: Optional configuration overrides

    Returns:
        Trigger results
    """
    n8n_config = load_n8n_config()

    if config:
        if 'webhook_url' in config:
            n8n_config.webhook_url = config['webhook_url']
        if 'enabled' in config:
            n8n_config.enabled = config['enabled']
        if 'batch_size' in config:
            n8n_config.batch_size = config['batch_size']

    trigger = N8NQueueTrigger(config=n8n_config)
    return trigger.trigger_queue_items(queue_items, correlation_id)


def handle_n8n_callback(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to handle n8n callback.

    Args:
        payload: Callback payload from n8n

    Returns:
        Processing result
    """
    handler = N8NCallbackHandler()
    return handler.handle_callback(payload)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "N8NConfig",
    "load_n8n_config",
    # Trigger
    "N8NQueueTrigger",
    "trigger_enrichment_queue",
    # Callback
    "N8NCallbackHandler",
    "handle_n8n_callback",
]
