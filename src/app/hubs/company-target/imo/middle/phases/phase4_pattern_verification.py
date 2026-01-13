"""
Phase 4: Pattern Verification
=============================
Validates discovered email patterns:
- Test pattern against known email/name pairs
- Verify sample emails via MX/SMTP checks
- Calculate confidence scores
- Flag patterns needing fallback

This is the final phase of the Company Identity Pipeline.
Verified patterns are passed to the People Pipeline for email generation.

DOCTRINE ENFORCEMENT:
- correlation_id is MANDATORY (FAIL HARD if missing)
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

# Doctrine enforcement imports
from ops.enforcement.correlation_id import validate_correlation_id, CorrelationIDError

from ..utils.patterns import apply_pattern, validate_pattern_format
from ..utils.verification import (
    verify_email,
    verify_email_format,
    verify_mx_records,
    VerificationResult as EmailVerificationResult,
    VerificationStatus
)
from ..utils.logging import (
    PipelineLogger,
    EventType,
    LogLevel,
    log_phase_start,
    log_phase_complete
)


class VerificationMethod(Enum):
    """How the pattern was verified."""
    KNOWN_EMAILS = "known_emails"      # Tested against known email/name pairs
    SMTP_CHECK = "smtp_check"          # SMTP verification of generated email
    MX_ONLY = "mx_only"                # MX record check only
    FORMAT_ONLY = "format_only"        # Format validation only
    UNVERIFIED = "unverified"          # Not verified


class VerificationStatus(Enum):
    """Status of pattern verification."""
    VERIFIED = "verified"              # Pattern confirmed valid
    LIKELY_VALID = "likely_valid"      # Pattern probably valid (MX ok)
    UNVERIFIED = "unverified"          # Could not verify
    FAILED = "failed"                  # Pattern failed verification
    SKIPPED = "skipped"                # Verification skipped


@dataclass
class PatternVerificationResult:
    """Result of pattern verification for a single domain."""
    company_id: str
    domain: str
    pattern: str
    verified: bool = False
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_method: VerificationMethod = VerificationMethod.UNVERIFIED
    confidence_score: float = 0.0
    test_emails_checked: int = 0
    test_emails_valid: int = 0
    sample_email_verified: bool = False
    mx_verified: bool = False
    fallback_required: bool = False
    fallback_pattern: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase4Stats:
    """Statistics for Phase 4 execution."""
    total_input: int = 0
    patterns_verified: int = 0
    patterns_likely_valid: int = 0
    patterns_unverified: int = 0
    patterns_failed: int = 0
    smtp_checks_performed: int = 0
    mx_checks_performed: int = 0
    fallbacks_required: int = 0
    avg_confidence: float = 0.0
    duration_seconds: float = 0.0
    correlation_id: str = ""  # Propagated unchanged


class Phase4PatternVerification:
    """
    Phase 4: Verify discovered email patterns.

    Verification methods:
    1. Test against known valid emails (if available)
    2. Generate sample email and verify via SMTP
    3. Check domain MX records
    4. Calculate confidence score

    Patterns that fail verification are flagged for fallback.
    """

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Phase 4.

        Args:
            config: Configuration with verification settings:
                - enable_smtp_check: Whether to perform SMTP verification
                - smtp_timeout: SMTP check timeout in seconds
                - min_confidence: Minimum confidence to pass verification
                - require_known_match: Require at least one known email match
                - fallback_patterns: List of fallback patterns to try
            logger: Pipeline logger instance
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()

        # Configuration
        self.enable_smtp_check = self.config.get('enable_smtp_check', False)
        self.smtp_timeout = self.config.get('smtp_timeout', 10)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.require_known_match = self.config.get('require_known_match', False)

        # Default fallback patterns (most common patterns)
        self.fallback_patterns = self.config.get('fallback_patterns', [
            '{first}.{last}',
            '{first}{last}',
            '{f}{last}',
            '{first}_{last}',
            '{first}'
        ])

        # Cache for MX verification results
        self._mx_cache: Dict[str, bool] = {}

    def run(self, pattern_df: pd.DataFrame,
            correlation_id: str) -> Tuple[pd.DataFrame, Phase4Stats]:
        """
        Run pattern verification phase.

        DOCTRINE: correlation_id is MANDATORY. FAIL HARD if missing.

        Args:
            pattern_df: DataFrame with patterns from Phase 3
                Expected columns: person_id, resolved_domain, email_pattern,
                                  pattern_confidence, pattern_needs_verification
            correlation_id: MANDATORY - End-to-end trace ID (UUID v4)

        Returns:
            Tuple of (result_df with verification results, Phase4Stats)

        Raises:
            CorrelationIDError: If correlation_id is missing or invalid (FAIL HARD)
        """
        # DOCTRINE ENFORCEMENT: Validate correlation_id (FAIL HARD)
        process_id = "company.identity.verification.phase4"
        correlation_id = validate_correlation_id(correlation_id, process_id, "Phase 4")

        start_time = time.time()
        stats = Phase4Stats(total_input=len(pattern_df), correlation_id=correlation_id)

        log_phase_start(self.logger, 4, "Pattern Verification", len(pattern_df))

        # Group by domain to avoid duplicate verification
        domain_patterns = self._group_by_domain(pattern_df)

        # Verify each unique domain/pattern combination
        verification_results: Dict[str, PatternVerificationResult] = {}
        confidence_scores = []

        for domain, domain_info in domain_patterns.items():
            result = self._verify_domain_pattern(
                domain=domain,
                pattern=domain_info['pattern'],
                company_id=domain_info['company_id'],
                known_emails=domain_info.get('known_emails', []),
                needs_verification=domain_info.get('needs_verification', True)
            )

            verification_results[domain] = result

            # Update stats
            if result.verification_status == VerificationStatus.VERIFIED:
                stats.patterns_verified += 1
            elif result.verification_status == VerificationStatus.LIKELY_VALID:
                stats.patterns_likely_valid += 1
            elif result.verification_status == VerificationStatus.FAILED:
                stats.patterns_failed += 1
            else:
                stats.patterns_unverified += 1

            if result.fallback_required:
                stats.fallbacks_required += 1

            if result.mx_verified:
                stats.mx_checks_performed += 1

            if result.confidence_score > 0:
                confidence_scores.append(result.confidence_score)

        if confidence_scores:
            stats.avg_confidence = sum(confidence_scores) / len(confidence_scores)

        # Build output DataFrame
        result_df = self._build_result_dataframe(pattern_df, verification_results)

        stats.duration_seconds = time.time() - start_time

        log_phase_complete(
            self.logger, 4, "Pattern Verification",
            output_count=len(result_df),
            duration_seconds=stats.duration_seconds,
            stats={
                'verified': stats.patterns_verified,
                'likely_valid': stats.patterns_likely_valid,
                'unverified': stats.patterns_unverified,
                'failed': stats.patterns_failed,
                'fallbacks_required': stats.fallbacks_required,
                'avg_confidence': round(stats.avg_confidence, 3)
            }
        )

        return result_df, stats

    def _group_by_domain(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Group records by domain for verification.

        Args:
            df: Input DataFrame

        Returns:
            Dict mapping domain to pattern info and known emails
        """
        domain_groups = {}

        for idx, row in df.iterrows():
            domain = row.get('resolved_domain', '') or row.get('domain', '')
            if not domain:
                continue

            domain = domain.lower().strip()

            if domain not in domain_groups:
                domain_groups[domain] = {
                    'domain': domain,
                    'pattern': row.get('email_pattern', ''),
                    'company_id': row.get('matched_company_id', ''),
                    'needs_verification': row.get('pattern_needs_verification', True),
                    'known_emails': []
                }

            # Collect known emails for verification
            email = row.get('email', '')
            first_name = row.get('first_name', '')
            last_name = row.get('last_name', '')

            if email and '@' in email and first_name and last_name:
                email_domain = email.split('@')[1].lower()
                if email_domain == domain:
                    domain_groups[domain]['known_emails'].append({
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    })

        return domain_groups

    def _verify_domain_pattern(self, domain: str, pattern: str,
                               company_id: str = '',
                               known_emails: List[Dict[str, str]] = None,
                               needs_verification: bool = True) -> PatternVerificationResult:
        """
        Verify a pattern for a specific domain.

        Verification order:
        1. Test against known emails (if available)
        2. Check MX records
        3. SMTP verify a generated sample (if enabled)
        4. Calculate confidence and determine if fallback needed

        Args:
            domain: Domain the pattern applies to
            pattern: Email pattern to verify (e.g., '{first}.{last}')
            company_id: Associated company ID
            known_emails: List of known email/name pairs for testing
            needs_verification: Whether this pattern needs verification

        Returns:
            PatternVerificationResult
        """
        result = PatternVerificationResult(
            company_id=company_id,
            domain=domain,
            pattern=pattern
        )

        # Skip verification if pattern is empty or not needed
        if not pattern:
            result.verification_status = VerificationStatus.SKIPPED
            result.fallback_required = True
            result.fallback_pattern = self.fallback_patterns[0] if self.fallback_patterns else None
            return result

        if not needs_verification:
            # Already verified pattern from Phase 3
            result.verified = True
            result.verification_status = VerificationStatus.VERIFIED
            result.confidence_score = 0.9
            result.verification_method = VerificationMethod.FORMAT_ONLY
            return result

        # Validate pattern format
        if not validate_pattern_format(pattern):
            self.logger.log_event(
                EventType.PATTERN_FAILED,
                f"Invalid pattern format: {pattern}",
                LogLevel.WARNING,
                entity_type="pattern",
                entity_id=domain
            )
            result.verification_status = VerificationStatus.FAILED
            result.fallback_required = True
            result.fallback_pattern = self.fallback_patterns[0] if self.fallback_patterns else None
            return result

        # 1. Test against known emails
        if known_emails:
            matches = self._test_pattern_against_known_emails(pattern, known_emails, domain)
            result.test_emails_checked = len(known_emails)
            result.test_emails_valid = matches

            if matches > 0:
                result.confidence_score = matches / len(known_emails)
                result.verification_method = VerificationMethod.KNOWN_EMAILS

                if result.confidence_score >= self.min_confidence:
                    result.verified = True
                    result.verification_status = VerificationStatus.VERIFIED

                    self.logger.log_event(
                        EventType.PATTERN_VERIFIED,
                        f"Pattern verified via known emails: {pattern} ({matches}/{len(known_emails)})",
                        entity_type="pattern",
                        entity_id=domain,
                        confidence=result.confidence_score
                    )
                    return result

        # 2. Check MX records
        mx_valid = self._check_mx_records(domain)
        result.mx_verified = mx_valid

        if not mx_valid:
            result.verification_status = VerificationStatus.FAILED
            result.fallback_required = True
            result.metadata['failure_reason'] = 'no_mx_records'
            return result

        # 3. SMTP verification (if enabled)
        if self.enable_smtp_check and known_emails:
            # Generate a sample email and verify
            sample = known_emails[0]
            generated_email = apply_pattern(
                pattern,
                sample['first_name'],
                sample['last_name'],
                domain
            )

            if generated_email:
                smtp_result = self._smtp_verify(generated_email)
                result.sample_email_verified = smtp_result

                if smtp_result:
                    result.verified = True
                    result.verification_status = VerificationStatus.VERIFIED
                    result.verification_method = VerificationMethod.SMTP_CHECK
                    result.confidence_score = max(result.confidence_score, 0.85)

                    self.logger.log_event(
                        EventType.PATTERN_VERIFIED,
                        f"Pattern verified via SMTP: {pattern}",
                        entity_type="pattern",
                        entity_id=domain,
                        confidence=result.confidence_score
                    )
                    return result

        # 4. Determine final status
        if result.mx_verified and not result.verified:
            # MX is valid but couldn't fully verify pattern
            result.verification_status = VerificationStatus.LIKELY_VALID
            result.confidence_score = max(result.confidence_score, 0.6)
            result.verification_method = VerificationMethod.MX_ONLY

            self.logger.log_event(
                EventType.PATTERN_VERIFIED,
                f"Pattern likely valid (MX ok): {pattern}",
                LogLevel.INFO,
                entity_type="pattern",
                entity_id=domain,
                confidence=result.confidence_score
            )

        # Check if fallback needed
        if result.confidence_score < self.min_confidence:
            result.fallback_required = True
            result.fallback_pattern = self._select_fallback_pattern(pattern)

        return result

    def _test_pattern_against_known_emails(self, pattern: str,
                                           known_emails: List[Dict[str, str]],
                                           domain: str) -> int:
        """
        Test pattern against known email/name pairs.

        Args:
            pattern: Pattern to test
            known_emails: List of dicts with email, first_name, last_name
            domain: Expected domain

        Returns:
            Count of emails that match the pattern
        """
        matches = 0

        for email_data in known_emails:
            email = email_data.get('email', '').lower()
            first_name = email_data.get('first_name', '')
            last_name = email_data.get('last_name', '')

            if not all([email, first_name, last_name]):
                continue

            # Generate expected email from pattern
            generated = apply_pattern(pattern, first_name, last_name, domain)

            if generated and generated.lower() == email:
                matches += 1

        return matches

    def _check_mx_records(self, domain: str) -> bool:
        """
        Check if domain has valid MX records.

        Args:
            domain: Domain to check

        Returns:
            True if MX records exist, False otherwise
        """
        # Check cache
        if domain in self._mx_cache:
            return self._mx_cache[domain]

        try:
            mx_records = verify_mx_records(domain, timeout=5.0)
            has_mx = len(mx_records) > 0
            self._mx_cache[domain] = has_mx
            return has_mx
        except Exception:
            self._mx_cache[domain] = False
            return False

    def _smtp_verify(self, email: str) -> bool:
        """
        Verify email via SMTP check.

        Args:
            email: Email to verify

        Returns:
            True if SMTP verification passes, False otherwise
        """
        try:
            result = verify_email(email, check_smtp=True, smtp_timeout=self.smtp_timeout)
            return result.is_valid and result.smtp_valid is not False
        except Exception as e:
            self.logger.debug(
                f"SMTP verification failed for {email}: {e}",
                metadata={'email': email, 'error': str(e)}
            )
            return False

    def _select_fallback_pattern(self, original_pattern: str) -> Optional[str]:
        """
        Select a fallback pattern different from the original.

        Args:
            original_pattern: Pattern that failed

        Returns:
            First fallback pattern that differs from original, or None
        """
        for fallback in self.fallback_patterns:
            if fallback != original_pattern:
                return fallback
        return None

    def _build_result_dataframe(self, pattern_df: pd.DataFrame,
                                verification_results: Dict[str, PatternVerificationResult]) -> pd.DataFrame:
        """Build output DataFrame with verification results appended."""
        result_data = []

        for idx, row in pattern_df.iterrows():
            domain = row.get('resolved_domain', '') or row.get('domain', '')
            domain = domain.lower().strip() if domain else ''

            if domain and domain in verification_results:
                vr = verification_results[domain]
                result_data.append({
                    'person_id': row.get('person_id', idx),
                    'pattern_verified': vr.verified,
                    'verification_status': vr.verification_status.value,
                    'verification_method': vr.verification_method.value,
                    'verification_confidence': vr.confidence_score,
                    'mx_verified': vr.mx_verified,
                    'fallback_required': vr.fallback_required,
                    'fallback_pattern': vr.fallback_pattern,
                    'final_pattern': vr.fallback_pattern if vr.fallback_required else vr.pattern
                })
            else:
                result_data.append({
                    'person_id': row.get('person_id', idx),
                    'pattern_verified': False,
                    'verification_status': VerificationStatus.SKIPPED.value,
                    'verification_method': VerificationMethod.UNVERIFIED.value,
                    'verification_confidence': 0.0,
                    'mx_verified': False,
                    'fallback_required': True,
                    'fallback_pattern': self.fallback_patterns[0] if self.fallback_patterns else None,
                    'final_pattern': self.fallback_patterns[0] if self.fallback_patterns else None
                })

        result_df = pd.DataFrame(result_data)

        # Merge with original pattern_df
        if 'person_id' not in pattern_df.columns:
            pattern_df = pattern_df.reset_index()
            pattern_df = pattern_df.rename(columns={'index': 'person_id'})

        output_df = pattern_df.merge(
            result_df,
            on='person_id',
            how='left'
        )

        return output_df

    def verify_pattern(self, pattern: str, domain: str,
                       sample_emails: List[Dict[str, str]] = None) -> PatternVerificationResult:
        """
        Verify a single email pattern.

        Args:
            pattern: Pattern to verify (e.g., '{first}.{last}')
            domain: Company domain
            sample_emails: Known valid email/name dicts to test against

        Returns:
            PatternVerificationResult with confidence score
        """
        return self._verify_domain_pattern(
            domain=domain,
            pattern=pattern,
            known_emails=sample_emails or [],
            needs_verification=True
        )

    def test_pattern_against_email(self, pattern: str, email: str,
                                   first_name: str, last_name: str) -> bool:
        """
        Test if pattern matches a known email.

        Args:
            pattern: Pattern to test
            email: Known valid email
            first_name: Person's first name
            last_name: Person's last name

        Returns:
            True if pattern matches, False otherwise
        """
        if '@' not in email:
            return False

        domain = email.split('@')[1].lower()
        generated = apply_pattern(pattern, first_name, last_name, domain)

        return generated is not None and generated.lower() == email.lower()

    def calculate_confidence(self, valid_count: int, total_count: int,
                             mx_valid: bool = True,
                             smtp_valid: Optional[bool] = None) -> float:
        """
        Calculate pattern confidence score.

        Args:
            valid_count: Number of emails that match pattern
            total_count: Total emails tested
            mx_valid: Whether domain has MX records
            smtp_valid: Whether SMTP verification passed (None if not checked)

        Returns:
            Confidence score 0.0-1.0
        """
        if total_count == 0:
            base_score = 0.5 if mx_valid else 0.0
        else:
            base_score = valid_count / total_count

        # Adjust for MX status
        if not mx_valid:
            base_score *= 0.5

        # Adjust for SMTP verification
        if smtp_valid is True:
            base_score = min(1.0, base_score + 0.2)
        elif smtp_valid is False:
            base_score *= 0.7

        return round(min(1.0, max(0.0, base_score)), 3)

    def get_verification_statistics(self, result_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about verification results.

        Args:
            result_df: Output from run()

        Returns:
            Dict with verification statistics
        """
        stats = {
            'total': len(result_df),
            'by_status': {},
            'by_method': {},
            'verified_count': 0,
            'fallback_count': 0,
            'avg_confidence': 0.0
        }

        if 'verification_status' in result_df.columns:
            stats['by_status'] = result_df['verification_status'].value_counts().to_dict()

        if 'verification_method' in result_df.columns:
            stats['by_method'] = result_df['verification_method'].value_counts().to_dict()

        if 'pattern_verified' in result_df.columns:
            stats['verified_count'] = result_df['pattern_verified'].sum()

        if 'fallback_required' in result_df.columns:
            stats['fallback_count'] = result_df['fallback_required'].sum()

        if 'verification_confidence' in result_df.columns:
            valid_conf = result_df[result_df['verification_confidence'] > 0]['verification_confidence']
            if len(valid_conf) > 0:
                stats['avg_confidence'] = valid_conf.mean()

        return stats


def verify_patterns(pattern_df: pd.DataFrame,
                    config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Phase4Stats]:
    """
    Convenience function to run pattern verification.

    Args:
        pattern_df: DataFrame with patterns from Phase 3
        config: Optional configuration

    Returns:
        Tuple of (result_df, Phase4Stats)
    """
    phase4 = Phase4PatternVerification(config=config)
    return phase4.run(pattern_df)


def verify_single_pattern(pattern: str, domain: str,
                          sample_emails: List[Dict[str, str]] = None,
                          config: Dict[str, Any] = None) -> PatternVerificationResult:
    """
    Verify a single email pattern.

    Args:
        pattern: Pattern to verify
        domain: Domain to verify for
        sample_emails: Optional known email/name pairs
        config: Optional configuration

    Returns:
        PatternVerificationResult
    """
    phase4 = Phase4PatternVerification(config=config)
    return phase4.verify_pattern(pattern, domain, sample_emails)
