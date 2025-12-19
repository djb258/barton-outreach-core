"""
Phase 5: Email Generation
=========================
Generates emails using verified patterns from Phase 4.
Links emails to company_id (Company Hub anchor).

Requirements:
- company_id must be present (Company-First doctrine)
- Pattern must exist from Phase 4
- No per-email API cost - uses verified pattern

Email Confidence Levels:
- verified: Pattern was verified in Phase 4
- derived: Pattern derived from known emails
- low_confidence: Fallback pattern used
- waterfall: Pattern discovered via on-demand waterfall

Waterfall Integration:
- When enable_waterfall=True, triggers pattern discovery for missing patterns
- Tier 0 (free) → Tier 1 (low cost) → Tier 2 (premium)
- Results cached to avoid duplicate API calls

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
- hub_gate validation - company_id REQUIRED (FAIL HARD)
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError
from ops.enforcement.hub_gate import validate_company_anchor_batch, GateLevel

# Waterfall integration (optional - enabled via config)
try:
    from .waterfall_integration import Phase5WaterfallAdapter, WaterfallStatus
    WATERFALL_AVAILABLE = True
except ImportError:
    WATERFALL_AVAILABLE = False

# Provider Benchmark Engine (System-Level) - Optional import
try:
    from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine
    _PBE_AVAILABLE = True
except ImportError:
    _PBE_AVAILABLE = False


class EmailConfidence(Enum):
    """Confidence level of generated email."""
    VERIFIED = "verified"           # Pattern verified in Phase 4
    DERIVED = "derived"             # Pattern derived from known emails
    LOW_CONFIDENCE = "low_confidence"  # Fallback pattern, unverified
    WATERFALL = "waterfall"         # Pattern discovered via on-demand waterfall


@dataclass
class GeneratedEmail:
    """A generated email record."""
    person_id: str
    company_id: str
    first_name: str
    last_name: str
    pattern: str
    domain: str
    generated_email: str
    confidence: EmailConfidence
    pattern_confidence: float = 0.0
    candidates: List[str] = field(default_factory=list)


@dataclass
class Phase5Stats:
    """Statistics for Phase 5 execution."""
    total_input: int = 0
    emails_generated: int = 0
    verified_emails: int = 0
    derived_emails: int = 0
    low_confidence_emails: int = 0
    waterfall_emails: int = 0           # Emails from waterfall-discovered patterns
    waterfall_patterns_discovered: int = 0  # Patterns found via on-demand waterfall
    waterfall_api_calls: int = 0        # Total API calls made by waterfall
    missing_pattern: int = 0
    missing_name: int = 0
    hub_gate_failures: int = 0          # Records rejected by hub_gate
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase5EmailGeneration:
    """
    Phase 5: Generate emails using verified patterns.

    Benefits:
    - No per-email API cost
    - Fast batch generation
    - Links to person_id and company_id

    Movement Engine Integration:
    - Triggers warm-engagement events for email generation
    - Reports EventType.MOVEMENT_WARM_ENGAGEMENT for verified email generation

    REQUIRES: company_id anchor (Company-First doctrine)
    """

    def __init__(self, config: Dict[str, Any] = None, movement_engine=None):
        """
        Initialize Phase 5.

        Args:
            config: Configuration dictionary
                - enable_waterfall: bool - Enable on-demand waterfall for missing patterns
                - waterfall_mode: int - 0=Tier0 only, 1=Tier0+1, 2=Full (default)
                - waterfall_config: dict - Config passed to waterfall adapter
            movement_engine: Optional MovementEngine instance for event reporting
        """
        self.config = config or {}
        self.movement_engine = movement_engine

        # Waterfall integration (optional)
        self.enable_waterfall = self.config.get('enable_waterfall', False)
        self.waterfall_adapter = None
        if self.enable_waterfall and WATERFALL_AVAILABLE:
            waterfall_config = self.config.get('waterfall_config', {})
            waterfall_config['mode'] = self.config.get('waterfall_mode', 2)  # Default: full
            self.waterfall_adapter = Phase5WaterfallAdapter(config=waterfall_config)

        # Provider Benchmark Engine reference
        self._pbe = None
        if _PBE_AVAILABLE:
            try:
                self._pbe = ProviderBenchmarkEngine.get_instance()
            except Exception:
                pass

        # Email pattern templates
        self.pattern_templates = {
            '{first}.{last}': lambda f, l: f"{f}.{l}",
            '{first}{last}': lambda f, l: f"{f}{l}",
            '{f}.{last}': lambda f, l: f"{f[0]}.{l}" if f else None,
            '{first}.{l}': lambda f, l: f"{f}.{l[0]}" if l else None,
            '{f}{last}': lambda f, l: f"{f[0]}{l}" if f else None,
            '{first}_{last}': lambda f, l: f"{f}_{l}",
            '{last}.{first}': lambda f, l: f"{l}.{f}",
            '{last}{first}': lambda f, l: f"{l}{f}",
            '{first}': lambda f, l: f,
            '{last}': lambda f, l: l,
        }

    def run(self, matched_people_df: pd.DataFrame,
            pattern_df: pd.DataFrame,
            correlation_id: str) -> Tuple[pd.DataFrame, pd.DataFrame, Phase5Stats]:
        """
        Run email generation phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.
        HUB GATE: Records without company_id are rejected.

        Args:
            matched_people_df: DataFrame with matched people from Company Pipeline
                Required columns: person_id, company_id, first_name, last_name
            pattern_df: DataFrame with verified patterns from Phase 4
                Required columns: company_id, email_pattern, resolved_domain, pattern_confidence
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            Tuple of (people_with_emails_df, people_missing_pattern_df, Phase5Stats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "people.lifecycle.email.phase5"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 5")

        start_time = time.time()
        stats = Phase5Stats(total_input=len(matched_people_df), correlation_id=correlation_id)

        # HUB GATE: Pre-filter records without company_id
        records_list = matched_people_df.to_dict('records')
        valid_records, invalid_records = validate_company_anchor_batch(
            records=records_list,
            level=GateLevel.COMPANY_ID_ONLY,
            process_id=process_id,
            correlation_id=correlation_id
        )
        stats.hub_gate_failures = len(invalid_records)

        # Build pattern lookup by company_id
        pattern_map = self._build_pattern_map(pattern_df)

        people_with_emails = []
        people_missing_pattern = []

        # Add hub_gate failures to missing_pattern list
        for invalid in invalid_records:
            people_missing_pattern.append({
                **invalid['record'],
                'missing_reason': 'hub_gate_failed_no_company_id'
            })

        for record in valid_records:
            person_id = str(record.get('person_id', ''))
            company_id = str(record.get('company_id', '') or record.get('matched_company_id', ''))
            first_name = str(record.get('first_name', '') or '').strip()
            last_name = str(record.get('last_name', '') or '').strip()

            # Check for name
            if not first_name or not last_name:
                stats.missing_name += 1
                people_missing_pattern.append({
                    **row.to_dict(),
                    'missing_reason': 'missing_name'
                })
                continue

            # Get pattern for company
            pattern_info = pattern_map.get(company_id)

            # If no pattern, try waterfall discovery (if enabled)
            waterfall_discovered = False
            if not pattern_info or not pattern_info.get('pattern') or not pattern_info.get('domain'):
                if self.waterfall_adapter:
                    # Try to discover pattern via waterfall
                    domain = str(row.get('domain', '') or row.get('company_domain', '')).strip()
                    company_name = str(row.get('company_name', '') or row.get('matched_company_name', '')).strip()

                    if domain:
                        waterfall_result = self.waterfall_adapter.discover_missing_pattern(
                            domain=domain,
                            company_id=company_id,
                            company_name=company_name
                        )
                        if waterfall_result:
                            pattern_info = waterfall_result
                            waterfall_discovered = True
                            stats.waterfall_patterns_discovered += 1
                            # Cache the discovered pattern for other people at same company
                            pattern_map[company_id] = pattern_info

                # Still no pattern after waterfall attempt
                if not pattern_info or not pattern_info.get('pattern') or not pattern_info.get('domain'):
                    stats.missing_pattern += 1
                    people_missing_pattern.append({
                        **row.to_dict(),
                        'missing_reason': 'no_pattern_for_company'
                    })
                    continue

            # Generate email
            # Override verification status if pattern came from waterfall
            verification_status = pattern_info.get('status', 'unknown')
            if waterfall_discovered:
                verification_status = 'waterfall'

            result = self._generate_email_for_person(
                person_id=person_id,
                company_id=company_id,
                first_name=first_name,
                last_name=last_name,
                pattern=pattern_info['pattern'],
                domain=pattern_info['domain'],
                pattern_confidence=pattern_info.get('confidence', 0.0),
                verification_status=verification_status
            )

            if result:
                stats.emails_generated += 1

                # Track confidence levels
                if waterfall_discovered:
                    # Waterfall-discovered patterns get their own confidence level
                    result.confidence = EmailConfidence.WATERFALL
                    stats.waterfall_emails += 1
                elif result.confidence == EmailConfidence.VERIFIED:
                    stats.verified_emails += 1
                elif result.confidence == EmailConfidence.DERIVED:
                    stats.derived_emails += 1
                else:
                    stats.low_confidence_emails += 1

                people_with_emails.append({
                    **row.to_dict(),
                    'generated_email': result.generated_email,
                    'email_confidence': result.confidence.value,
                    'pattern_used': result.pattern,
                    'email_domain': result.domain,
                    'pattern_confidence': result.pattern_confidence,
                    'email_candidates': ','.join(result.candidates[:3]),  # Top 3 candidates
                    'waterfall_discovered': waterfall_discovered
                })

                # Report movement event for verified emails
                # Phase 5 triggers warm-engagement events for email generation
                if self.movement_engine and company_id:
                    self._report_email_generation_event(
                        company_id=company_id,
                        person_id=person_id,
                        confidence=result.confidence,
                        waterfall_discovered=waterfall_discovered
                    )
            else:
                people_missing_pattern.append({
                    **row.to_dict(),
                    'missing_reason': 'generation_failed'
                })

        # Build output DataFrames
        people_with_emails_df = pd.DataFrame(people_with_emails) if people_with_emails else pd.DataFrame()
        people_missing_pattern_df = pd.DataFrame(people_missing_pattern) if people_missing_pattern else pd.DataFrame()

        stats.duration_seconds = time.time() - start_time

        return people_with_emails_df, people_missing_pattern_df, stats

    def _build_pattern_map(self, pattern_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Build lookup map from company_id to pattern info.

        Args:
            pattern_df: DataFrame with patterns

        Returns:
            Dict mapping company_id to pattern info
        """
        pattern_map = {}

        if pattern_df is None or len(pattern_df) == 0:
            return pattern_map

        for idx, row in pattern_df.iterrows():
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            if not company_id:
                continue

            pattern = row.get('email_pattern', '') or row.get('verified_pattern', '') or row.get('pattern', '')
            domain = row.get('resolved_domain', '') or row.get('domain', '')
            confidence = row.get('pattern_confidence', 0.0) or row.get('verification_confidence', 0.0)
            status = row.get('verification_status', '') or row.get('pattern_status', '')

            if pattern and domain:
                pattern_map[company_id] = {
                    'pattern': pattern,
                    'domain': domain,
                    'confidence': float(confidence) if confidence else 0.0,
                    'status': status
                }

        return pattern_map

    def _generate_email_for_person(
        self,
        person_id: str,
        company_id: str,
        first_name: str,
        last_name: str,
        pattern: str,
        domain: str,
        pattern_confidence: float,
        verification_status: str
    ) -> Optional[GeneratedEmail]:
        """
        Generate email for a single person.

        Args:
            person_id: Person unique ID
            company_id: Company unique ID (anchor)
            first_name: First name
            last_name: Last name
            pattern: Email pattern template
            domain: Company domain
            pattern_confidence: Confidence of pattern
            verification_status: Status from Phase 4

        Returns:
            GeneratedEmail or None
        """
        # Normalize names
        first_normalized = self.normalize_name(first_name)
        last_normalized = self.normalize_name(last_name)

        if not first_normalized or not last_normalized:
            return None

        # Generate primary email using pattern
        generated = self.generate_email(first_normalized, last_normalized, pattern, domain)

        if not generated:
            return None

        # Generate candidate emails for fallback
        candidates = self._generate_candidates(first_normalized, last_normalized, domain)

        # Determine confidence level
        if verification_status in ['verified', 'confirmed']:
            confidence = EmailConfidence.VERIFIED
        elif verification_status in ['derived', 'extracted']:
            confidence = EmailConfidence.DERIVED
        else:
            confidence = EmailConfidence.LOW_CONFIDENCE

        return GeneratedEmail(
            person_id=person_id,
            company_id=company_id,
            first_name=first_name,
            last_name=last_name,
            pattern=pattern,
            domain=domain,
            generated_email=generated,
            confidence=confidence,
            pattern_confidence=pattern_confidence,
            candidates=candidates
        )

    def generate_email(self, first_name: str, last_name: str,
                       pattern: str, domain: str) -> Optional[str]:
        """
        Generate email using pattern.

        Pattern placeholders:
        - {first} - Full first name
        - {last} - Full last name
        - {f} - First initial
        - {l} - Last initial
        - {first_2} - First 2 chars of first name

        Args:
            first_name: Normalized first name
            last_name: Normalized last name
            pattern: Email pattern
            domain: Company domain

        Returns:
            Generated email address
        """
        if not first_name or not last_name or not pattern or not domain:
            return None

        # Clean domain
        domain = domain.lower().strip()
        if domain.startswith('http'):
            domain = domain.replace('https://', '').replace('http://', '')
        if domain.startswith('www.'):
            domain = domain[4:]
        domain = domain.split('/')[0]

        # Apply pattern replacements
        email_local = pattern.lower()

        # Replace placeholders
        replacements = {
            '{first}': first_name,
            '{last}': last_name,
            '{f}': first_name[0] if first_name else '',
            '{l}': last_name[0] if last_name else '',
            '{first_initial}': first_name[0] if first_name else '',
            '{last_initial}': last_name[0] if last_name else '',
            '{first_2}': first_name[:2] if len(first_name) >= 2 else first_name,
        }

        for placeholder, value in replacements.items():
            email_local = email_local.replace(placeholder, value)

        # If pattern still has braces, it's invalid
        if '{' in email_local or '}' in email_local:
            return None

        # Build final email
        email = f"{email_local}@{domain}"

        # Validate email format
        if not self._is_valid_email(email):
            return None

        return email

    def normalize_name(self, name: str) -> str:
        """
        Normalize name for email generation.

        - Remove special characters
        - Handle hyphenated names (use first part)
        - Lowercase

        Args:
            name: Name to normalize

        Returns:
            Normalized name
        """
        if not name:
            return ''

        # Lowercase
        name = name.lower().strip()

        # Handle hyphenated names - use first part
        if '-' in name:
            name = name.split('-')[0]

        # Handle spaces - use first part
        if ' ' in name:
            name = name.split()[0]

        # Remove special characters except alphanumeric
        name = re.sub(r'[^a-z0-9]', '', name)

        return name

    def _generate_candidates(self, first: str, last: str, domain: str) -> List[str]:
        """
        Generate candidate email formats.

        Args:
            first: Normalized first name
            last: Normalized last name
            domain: Company domain

        Returns:
            List of candidate emails
        """
        candidates = []

        patterns = [
            f"{first}.{last}",
            f"{first}{last}",
            f"{first[0]}.{last}" if first else None,
            f"{first}.{last[0]}" if last else None,
            f"{first[0]}{last}" if first else None,
            f"{first}_{last}",
            f"{last}.{first}",
        ]

        for p in patterns:
            if p:
                email = f"{p}@{domain}"
                if self._is_valid_email(email):
                    candidates.append(email)

        return candidates

    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email to validate

        Returns:
            True if valid format
        """
        if not email:
            return False

        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def batch_generate(self, people_df: pd.DataFrame,
                       pattern_map: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """
        Batch generate emails for multiple people.

        Args:
            people_df: DataFrame with people records
            pattern_map: Dict mapping company_id to pattern info

        Returns:
            DataFrame with generated emails
        """
        results = []

        for idx, row in people_df.iterrows():
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            pattern_info = pattern_map.get(company_id, {})

            if not pattern_info:
                continue

            result = self._generate_email_for_person(
                person_id=str(row.get('person_id', idx)),
                company_id=company_id,
                first_name=str(row.get('first_name', '')),
                last_name=str(row.get('last_name', '')),
                pattern=pattern_info.get('pattern', ''),
                domain=pattern_info.get('domain', ''),
                pattern_confidence=pattern_info.get('confidence', 0.0),
                verification_status=pattern_info.get('status', '')
            )

            if result:
                results.append({
                    **row.to_dict(),
                    'generated_email': result.generated_email,
                    'email_confidence': result.confidence.value,
                    'pattern_used': result.pattern,
                    'email_domain': result.domain
                })

        return pd.DataFrame(results) if results else pd.DataFrame()

    def _report_email_generation_event(
        self,
        company_id: str,
        person_id: str,
        confidence: EmailConfidence,
        waterfall_discovered: bool = False
    ) -> None:
        """
        Report movement event for email generation.

        Phase 5 triggers warm-engagement events when verified emails are generated.
        This signals to the Movement Engine that the person has been enriched
        and may qualify for state advancement.

        Args:
            company_id: Company anchor ID
            person_id: Person unique ID
            confidence: Email confidence level
            waterfall_discovered: Whether email was discovered via waterfall
        """
        if not self.movement_engine:
            return

        try:
            # Only report for verified/waterfall emails (high confidence)
            if confidence in [EmailConfidence.VERIFIED, EmailConfidence.WATERFALL]:
                self.movement_engine.detect_event(
                    company_id=company_id,
                    person_id=person_id,
                    event_type='email_enriched',
                    metadata={
                        'phase': 5,
                        'email_confidence': confidence.value,
                        'waterfall_discovered': waterfall_discovered,
                        'event_category': 'MOVEMENT_WARM_ENGAGEMENT'
                    }
                )
        except Exception:
            # Don't fail email generation due to movement event errors
            pass


def generate_emails(matched_people_df: pd.DataFrame,
                   pattern_df: pd.DataFrame,
                   config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, pd.DataFrame, Phase5Stats]:
    """
    Convenience function to run email generation.

    Args:
        matched_people_df: DataFrame with matched people
        pattern_df: DataFrame with verified patterns
        config: Optional configuration

    Returns:
        Tuple of (people_with_emails_df, people_missing_pattern_df, Phase5Stats)
    """
    phase5 = Phase5EmailGeneration(config=config)
    return phase5.run(matched_people_df, pattern_df)
