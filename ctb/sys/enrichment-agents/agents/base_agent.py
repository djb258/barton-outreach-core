"""
Base Agent Class - Universal Enrichment Agent Interface
Barton Doctrine ID: 04.04.02.04.50000.000

All enrichment agents (Apify, Abacus, Firecrawl) inherit from this.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from datetime import datetime
import os


class AgentTimeout(Exception):
    """Raised when agent exceeds timeout"""
    pass


class AgentRateLimitExceeded(Exception):
    """Raised when agent hits rate limit"""
    pass


class BaseEnrichmentAgent(ABC):
    """
    Base class for all enrichment agents

    All agents must implement:
    - enrich() - Main enrichment method
    - get_capabilities() - List of what this agent can enrich
    - estimate_cost() - Cost estimate for operation
    """

    def __init__(self, config: Dict, api_key: Optional[str] = None):
        """
        Initialize agent with configuration

        Args:
            config: Agent configuration from agent_config.json
            api_key: Optional API key override (defaults to env var)
        """
        self.config = config
        self.agent_name = self.__class__.__name__.replace('Agent', '').lower()

        # Get API key from env or parameter
        api_key_env = config.get('api_key_env')
        self.api_key = api_key or (os.getenv(api_key_env) if api_key_env else None)

        if not self.api_key:
            raise ValueError(f"API key not found for {self.agent_name} (env: {api_key_env})")

        # Rate limiting
        self.rate_limit = config.get('rate_limit', {})
        self.call_history = []  # Track calls for rate limiting

        # Timeouts
        self.default_timeout = config.get('timeout_seconds', 60)
        self.max_retries = config.get('max_retries', 2)

        # Cost tracking
        self.cost_per_request = config.get('cost_per_request', 0.0)
        self.total_cost = 0.0

    @abstractmethod
    async def enrich(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main enrichment method - MUST be implemented by subclass

        Args:
            capability: Which capability to use (e.g., 'linkedin_company_scraper')
            input_data: Input data for enrichment
            timeout_override: Override default timeout

        Returns:
            {
                'success': True/False,
                'data': {...enriched fields...},
                'cost': 0.01,
                'duration_seconds': 12.5,
                'error': None or error message
            }
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides

        Returns:
            ['linkedin_company_scraper', 'linkedin_profile_scraper', ...]
        """
        pass

    def estimate_cost(self, capability: str) -> float:
        """
        Estimate cost for this operation

        Args:
            capability: Capability name

        Returns:
            Estimated cost in USD
        """
        capabilities = self.config.get('capabilities', {})
        if capability in capabilities:
            return capabilities[capability].get('cost', self.cost_per_request)
        return self.cost_per_request

    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits

        Returns:
            True if OK to proceed, False if rate limited
        """
        now = time.time()

        # Remove old calls (older than 1 hour)
        self.call_history = [t for t in self.call_history if now - t < 3600]

        # Check per-minute limit
        calls_per_minute = self.rate_limit.get('calls_per_minute', float('inf'))
        recent_calls = [t for t in self.call_history if now - t < 60]
        if len(recent_calls) >= calls_per_minute:
            return False

        # Check per-hour limit
        calls_per_hour = self.rate_limit.get('calls_per_hour', float('inf'))
        if len(self.call_history) >= calls_per_hour:
            return False

        return True

    def record_call(self):
        """Record a call for rate limiting"""
        self.call_history.append(time.time())

    async def enrich_with_timeout(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich with timeout and rate limit checks

        This is the main entry point - it wraps enrich() with safety checks
        """
        # Check rate limit
        if not self.check_rate_limit():
            raise AgentRateLimitExceeded(
                f"{self.agent_name} rate limit exceeded"
            )

        # Get timeout
        timeout = timeout_seconds or self.default_timeout
        capability_config = self.config.get('capabilities', {}).get(capability, {})
        timeout = capability_config.get('timeout_seconds', timeout)

        # Record call
        self.record_call()

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self.enrich(capability, input_data, timeout),
                timeout=timeout
            )

            # Track cost
            cost = result.get('cost', 0.0)
            self.total_cost += cost

            return result

        except asyncio.TimeoutError:
            raise AgentTimeout(
                f"{self.agent_name}.{capability} exceeded timeout of {timeout}s"
            )

    async def enrich_with_retry(
        self,
        capability: str,
        input_data: Dict[str, Any],
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich with retry logic
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.enrich_with_timeout(
                    capability,
                    input_data,
                    timeout_seconds
                )

                # Success!
                if result.get('success'):
                    return result

                # Failed but no exception - store error and retry
                last_error = result.get('error', 'Unknown error')

            except (AgentTimeout, AgentRateLimitExceeded) as e:
                last_error = str(e)

                # Don't retry on rate limit or timeout
                if isinstance(e, AgentRateLimitExceeded):
                    break

            except Exception as e:
                last_error = str(e)

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** attempt)

        # All retries failed
        return {
            'success': False,
            'data': {},
            'cost': 0.0,
            'duration_seconds': 0.0,
            'error': f"Failed after {self.max_retries + 1} attempts: {last_error}"
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics

        Returns:
            {
                'agent_name': 'apify',
                'total_calls': 150,
                'total_cost': 1.50,
                'rate_limit_status': 'OK'
            }
        """
        return {
            'agent_name': self.agent_name,
            'total_calls': len(self.call_history),
            'total_cost': round(self.total_cost, 4),
            'rate_limit_status': 'OK' if self.check_rate_limit() else 'LIMITED'
        }
