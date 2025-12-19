"""
Tool 3: Fuzzy Arbitration (Abacus.ai LLM)
=========================================
LLM-based collision resolution for ambiguous fuzzy matches.

Per Pipeline Tool Doctrine:
- LLM is ONLY allowed here for collision resolution
- Must be triggered ONLY when top 2 candidates are within 0.03 score
- LLM may REJECT if uncertain (reject is valid)
- Uses Abacus.ai as the only approved LLM provider

Principle: Deterministic → Fuzzy → LLM (last resort only)
"""

import os
import json
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ArbitrationResult(Enum):
    """Result of LLM arbitration."""
    SELECTED = "selected"          # LLM selected one candidate
    REJECTED_BOTH = "rejected"     # LLM couldn't decide, rejected both
    NEEDS_REVIEW = "needs_review"  # LLM uncertain, needs human review
    ERROR = "error"                # Arbitration failed
    SKIPPED = "skipped"            # Arbitration was skipped (not a collision)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CollisionCandidate:
    """A candidate in a collision."""
    company_id: str
    company_name: str
    score: float
    domain: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArbitrationResponse:
    """Response from fuzzy arbitration."""
    result: ArbitrationResult
    selected_company_id: Optional[str] = None
    selected_company_name: Optional[str] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None
    input_company_name: str = ""
    candidates: List[CollisionCandidate] = field(default_factory=list)
    llm_response: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# ABACUS.AI ARBITRATOR
# =============================================================================

class AbacusFuzzyArbitrator:
    """
    Tool 3: Fuzzy Arbitration using Abacus.ai LLM.

    This is the ONLY place in the pipeline where LLM is allowed for matching.
    Used exclusively for resolving collisions when top candidates are within
    the collision threshold (0.03 score difference).
    """

    def __init__(
        self,
        api_key: str = None,
        api_url: str = "https://api.abacus.ai",
        collision_threshold: float = 0.03,
        confidence_threshold: float = 0.7,
        timeout: int = 30
    ):
        """
        Initialize Abacus arbitrator.

        Args:
            api_key: Abacus.ai API key (from env ABACUS_API_KEY if not provided)
            api_url: Abacus.ai API URL
            collision_threshold: Score difference to trigger arbitration
            confidence_threshold: Minimum LLM confidence to accept decision
            timeout: API timeout in seconds
        """
        self.api_key = api_key or os.getenv('ABACUS_API_KEY', '')
        self.api_url = api_url
        self.collision_threshold = collision_threshold
        self.confidence_threshold = confidence_threshold
        self.timeout = timeout

        if not self.api_key:
            logger.warning("ABACUS_API_KEY not set - arbitration will use fallback logic")

    def is_collision(self, candidates: List[CollisionCandidate]) -> bool:
        """
        Check if candidates constitute a collision requiring arbitration.

        Args:
            candidates: List of match candidates

        Returns:
            True if top 2 candidates are within collision threshold
        """
        if len(candidates) < 2:
            return False

        # Sort by score descending
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        top_score = sorted_candidates[0].score
        second_score = sorted_candidates[1].score

        # Collision if within threshold
        return (top_score - second_score) <= self.collision_threshold

    def arbitrate(
        self,
        input_company_name: str,
        candidates: List[CollisionCandidate],
        input_city: str = None,
        input_state: str = None,
        input_domain: str = None
    ) -> ArbitrationResponse:
        """
        Arbitrate between collision candidates using LLM.

        Args:
            input_company_name: The company name from input
            candidates: List of collision candidates
            input_city: Optional city for context
            input_state: Optional state for context
            input_domain: Optional domain for context

        Returns:
            ArbitrationResponse with decision
        """
        # Validate candidates
        if not candidates:
            return ArbitrationResponse(
                result=ArbitrationResult.SKIPPED,
                input_company_name=input_company_name,
                reasoning="No candidates provided"
            )

        if len(candidates) < 2:
            # Only one candidate - not a collision
            candidate = candidates[0]
            return ArbitrationResponse(
                result=ArbitrationResult.SELECTED,
                selected_company_id=candidate.company_id,
                selected_company_name=candidate.company_name,
                confidence=candidate.score,
                input_company_name=input_company_name,
                candidates=candidates,
                reasoning="Single candidate - no arbitration needed"
            )

        if not self.is_collision(candidates):
            # Not a collision - return top candidate
            top = max(candidates, key=lambda c: c.score)
            return ArbitrationResponse(
                result=ArbitrationResult.SELECTED,
                selected_company_id=top.company_id,
                selected_company_name=top.company_name,
                confidence=top.score,
                input_company_name=input_company_name,
                candidates=candidates,
                reasoning="Clear winner - no arbitration needed"
            )

        # This IS a collision - need LLM arbitration
        if not self.api_key:
            # No API key - use fallback logic
            return self._fallback_arbitration(input_company_name, candidates,
                                               input_city, input_state, input_domain)

        # Call Abacus.ai for arbitration
        try:
            return self._call_abacus_arbitration(
                input_company_name, candidates,
                input_city, input_state, input_domain
            )
        except Exception as e:
            logger.error(f"Abacus arbitration failed: {e}")
            return ArbitrationResponse(
                result=ArbitrationResult.ERROR,
                input_company_name=input_company_name,
                candidates=candidates,
                error_message=str(e)
            )

    def _call_abacus_arbitration(
        self,
        input_company_name: str,
        candidates: List[CollisionCandidate],
        input_city: str = None,
        input_state: str = None,
        input_domain: str = None
    ) -> ArbitrationResponse:
        """
        Call Abacus.ai API for arbitration.
        """
        import requests

        # Build prompt
        prompt = self._build_arbitration_prompt(
            input_company_name, candidates,
            input_city, input_state, input_domain
        )

        # Build request
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.1,  # Low temperature for consistency
            "response_format": "json"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.api_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"Abacus API error: {response.status_code} - {response.text}")
                return ArbitrationResponse(
                    result=ArbitrationResult.ERROR,
                    input_company_name=input_company_name,
                    candidates=candidates,
                    error_message=f"API error: {response.status_code}"
                )

            # Parse response
            result = response.json()
            return self._parse_abacus_response(
                result, input_company_name, candidates
            )

        except requests.Timeout:
            return ArbitrationResponse(
                result=ArbitrationResult.ERROR,
                input_company_name=input_company_name,
                candidates=candidates,
                error_message="API timeout"
            )

    def _build_arbitration_prompt(
        self,
        input_company_name: str,
        candidates: List[CollisionCandidate],
        input_city: str = None,
        input_state: str = None,
        input_domain: str = None
    ) -> str:
        """Build the arbitration prompt for the LLM."""
        context_parts = [f"Input company name: {input_company_name}"]

        if input_city:
            context_parts.append(f"Input city: {input_city}")
        if input_state:
            context_parts.append(f"Input state: {input_state}")
        if input_domain:
            context_parts.append(f"Input domain: {input_domain}")

        context = "\n".join(context_parts)

        candidates_text = "\n".join([
            f"Candidate {i+1}: {c.company_name} (ID: {c.company_id}, Score: {c.score:.3f}, "
            f"City: {c.city or 'N/A'}, State: {c.state or 'N/A'}, Domain: {c.domain or 'N/A'})"
            for i, c in enumerate(candidates)
        ])

        prompt = f"""You are a company matching expert. Your task is to determine which candidate company best matches the input company name, or reject both if uncertain.

{context}

Candidates:
{candidates_text}

Instructions:
1. Compare the input company name to each candidate
2. Consider location (city/state) as supporting evidence
3. Consider domain as strong evidence if available
4. Select the BEST match, or REJECT if you cannot determine with high confidence

IMPORTANT: It is acceptable to REJECT both candidates if:
- The input name could reasonably match multiple candidates
- You are not confident in the match
- There is not enough distinguishing information

Respond in JSON format:
{{
    "decision": "SELECT" or "REJECT",
    "selected_candidate": 1 or 2 or null (if REJECT),
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation"
}}
"""
        return prompt

    def _parse_abacus_response(
        self,
        api_response: Dict[str, Any],
        input_company_name: str,
        candidates: List[CollisionCandidate]
    ) -> ArbitrationResponse:
        """Parse the Abacus API response."""
        try:
            # Extract the LLM output
            content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Parse JSON from content
            llm_result = json.loads(content)

            decision = llm_result.get('decision', 'REJECT')
            selected_idx = llm_result.get('selected_candidate')
            confidence = float(llm_result.get('confidence', 0.0))
            reasoning = llm_result.get('reasoning', '')

            if decision == 'SELECT' and selected_idx is not None:
                # LLM selected a candidate
                if confidence < self.confidence_threshold:
                    # Confidence too low - needs review
                    return ArbitrationResponse(
                        result=ArbitrationResult.NEEDS_REVIEW,
                        input_company_name=input_company_name,
                        candidates=candidates,
                        confidence=confidence,
                        reasoning=f"LLM confidence ({confidence:.2f}) below threshold ({self.confidence_threshold})",
                        llm_response=content
                    )

                # Valid selection
                idx = int(selected_idx) - 1  # Convert to 0-based
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
                    return ArbitrationResponse(
                        result=ArbitrationResult.SELECTED,
                        selected_company_id=selected.company_id,
                        selected_company_name=selected.company_name,
                        confidence=confidence,
                        input_company_name=input_company_name,
                        candidates=candidates,
                        reasoning=reasoning,
                        llm_response=content
                    )

            # LLM rejected or invalid selection
            return ArbitrationResponse(
                result=ArbitrationResult.REJECTED_BOTH,
                input_company_name=input_company_name,
                candidates=candidates,
                confidence=confidence,
                reasoning=reasoning or "LLM could not determine best match",
                llm_response=content
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return ArbitrationResponse(
                result=ArbitrationResult.ERROR,
                input_company_name=input_company_name,
                candidates=candidates,
                error_message=f"Failed to parse LLM response: {e}",
                llm_response=str(api_response)
            )

    def _fallback_arbitration(
        self,
        input_company_name: str,
        candidates: List[CollisionCandidate],
        input_city: str = None,
        input_state: str = None,
        input_domain: str = None
    ) -> ArbitrationResponse:
        """
        Fallback arbitration when API is not available.

        Uses deterministic rules:
        1. If domain matches one candidate, select it
        2. If city+state matches one candidate better, select it
        3. Otherwise, reject both (needs manual review)
        """
        # Sort by score
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)

        # Check domain match
        if input_domain:
            for candidate in sorted_candidates:
                if candidate.domain and candidate.domain.lower() == input_domain.lower():
                    return ArbitrationResponse(
                        result=ArbitrationResult.SELECTED,
                        selected_company_id=candidate.company_id,
                        selected_company_name=candidate.company_name,
                        confidence=0.9,  # High confidence for domain match
                        input_company_name=input_company_name,
                        candidates=candidates,
                        reasoning="Domain match resolved collision (fallback)"
                    )

        # Check location match
        location_matches = []
        for candidate in sorted_candidates:
            city_match = (input_city and candidate.city and
                         input_city.lower() == candidate.city.lower())
            state_match = (input_state and candidate.state and
                          input_state.lower() == candidate.state.lower())
            if city_match and state_match:
                location_matches.append(candidate)

        if len(location_matches) == 1:
            # Only one candidate matches location
            selected = location_matches[0]
            return ArbitrationResponse(
                result=ArbitrationResult.SELECTED,
                selected_company_id=selected.company_id,
                selected_company_name=selected.company_name,
                confidence=0.75,
                input_company_name=input_company_name,
                candidates=candidates,
                reasoning="Location match resolved collision (fallback)"
            )

        # Cannot resolve - reject both
        return ArbitrationResponse(
            result=ArbitrationResult.REJECTED_BOTH,
            input_company_name=input_company_name,
            candidates=candidates,
            confidence=0.0,
            reasoning="Could not resolve collision (fallback) - candidates too similar"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_arbitrator(api_key: str = None) -> AbacusFuzzyArbitrator:
    """
    Create an arbitrator instance with configuration from environment.

    Args:
        api_key: Optional API key (uses ABACUS_API_KEY env var if not provided)

    Returns:
        Configured AbacusFuzzyArbitrator instance
    """
    return AbacusFuzzyArbitrator(
        api_key=api_key,
        collision_threshold=float(os.getenv('COLLISION_THRESHOLD', '0.03')),
        confidence_threshold=float(os.getenv('LLM_CONFIDENCE_THRESHOLD', '0.7'))
    )


def arbitrate_collision(
    input_company_name: str,
    candidates: List[Dict[str, Any]],
    input_city: str = None,
    input_state: str = None,
    input_domain: str = None
) -> ArbitrationResponse:
    """
    Convenience function to arbitrate a collision.

    Args:
        input_company_name: The input company name
        candidates: List of candidate dicts with keys:
            company_id, company_name, score, domain, city, state
        input_city: Optional input city
        input_state: Optional input state
        input_domain: Optional input domain

    Returns:
        ArbitrationResponse with decision
    """
    arbitrator = create_arbitrator()

    # Convert dicts to CollisionCandidate objects
    collision_candidates = [
        CollisionCandidate(
            company_id=c.get('company_id', ''),
            company_name=c.get('company_name', ''),
            score=float(c.get('score', 0)),
            domain=c.get('domain'),
            city=c.get('city'),
            state=c.get('state'),
            metadata=c.get('metadata', {})
        )
        for c in candidates
    ]

    return arbitrator.arbitrate(
        input_company_name,
        collision_candidates,
        input_city,
        input_state,
        input_domain
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ArbitrationResult",
    # Data classes
    "CollisionCandidate",
    "ArbitrationResponse",
    # Main class
    "AbacusFuzzyArbitrator",
    # Convenience functions
    "create_arbitrator",
    "arbitrate_collision",
]
