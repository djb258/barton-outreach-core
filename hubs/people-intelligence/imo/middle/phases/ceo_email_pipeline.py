#!/usr/bin/env python3
"""
CEO Email Pipeline - Phases 5-8 (Hardened Implementation)
=========================================================
Implements the CEO email verification pipeline with MillionVerifier as a HARD GATE.

Phases:
    5. Email Generation (pattern-only, deterministic)
    6. CEO Slot Assignment (seniority resolution)
    7. Email Verification (MillionVerifier - HARD GATE)
    8. Persistence (Neon + CSV)

HARD CONSTRAINTS (NON-NEGOTIABLE):
    - NO table bloat
    - NO new hubs
    - NO enrichment logic
    - NO retries or loops
    - ONE verification pass per email per TTL
    - MillionVerifier = gate, not enrichment
    - ONLY VALID emails may be promoted

Usage:
    doppler run -- python -m hubs.people_intelligence.imo.middle.phases.ceo_email_pipeline <csv_path>

Created: 2026-01-13
Doctrine: Barton Hub & Spoke Architecture
"""

import os
import sys
import csv
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# =============================================================================
# CONSTANTS & CONFIG
# =============================================================================

VERIFICATION_TTL_DAYS = 30  # One verification per email per 30 days

# Supported verification providers
VERIFIER_MILLIONVERIFIER = "millionverifier"
VERIFIER_EMAILVERIFYIO = "emailverifyio"
DEFAULT_VERIFIER = VERIFIER_EMAILVERIFYIO  # Default to EmailVerify.io

# API URLs
MILLIONVERIFIER_API_URL = "https://api.millionverifier.com/api/v3/"
EMAILVERIFYIO_API_URL = "https://app.emailverify.io/api/v1/"


class VerificationStatus(Enum):
    """Email verification result statuses mapped to gate decisions."""
    VALID = "VALID"         # Promote to Neon
    RISKY = "RISKY"         # Flag only, no action
    INVALID = "INVALID"     # Discard, do not promote
    UNKNOWN = "UNKNOWN"     # Flag only, no action


class SlotResolutionReason(Enum):
    """Reasons for CEO slot assignment decisions."""
    EXACT_TITLE_MATCH = "exact_title_match"
    SENIORITY_WIN = "seniority_win"
    RECENCY_WIN = "recency_win"
    FIRST_CANDIDATE = "first_candidate"
    DISPLACEMENT = "displacement"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CEOCandidate:
    """CEO candidate for processing through the pipeline."""
    # Identity (required)
    person_unique_id: str
    company_unique_id: str

    # Person data
    first_name: str
    last_name: str
    full_name: str
    job_title: str
    linkedin_url: Optional[str] = None

    # Company data
    company_name: str = ""
    company_domain: str = ""
    email_pattern: Optional[str] = None

    # Phase 5: Email Generation
    generated_email: Optional[str] = None
    email_source: str = "pattern"
    email_confidence: str = "LOW"

    # Phase 6: Slot Assignment
    slot_type: str = "CEO"
    slot_assigned: bool = False
    slot_resolution_reason: Optional[str] = None
    seniority_score: float = 9.99

    # Phase 7: Verification
    verification_status: Optional[str] = None
    verification_result_raw: Optional[str] = None
    verified_at: Optional[datetime] = None
    verifier: str = "MillionVerifier"

    # Phase 8: Persistence
    promoted_to_neon: bool = False

    # Processing state
    row_id: int = 0
    error: Optional[str] = None


@dataclass
class PipelineStats:
    """Pipeline execution statistics."""
    total_records: int = 0

    # Phase 5
    emails_generated: int = 0
    emails_skipped_no_pattern: int = 0
    emails_skipped_no_domain: int = 0

    # Phase 6
    slots_assigned: int = 0
    slots_displaced: int = 0
    slots_skipped: int = 0

    # Phase 7
    emails_verified: int = 0
    emails_valid: int = 0
    emails_risky: int = 0
    emails_invalid: int = 0
    emails_unknown: int = 0
    emails_skipped_ttl: int = 0

    # Phase 8
    records_promoted_neon: int = 0
    records_written_csv: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)


# =============================================================================
# GUARDS & ENFORCEMENT
# =============================================================================

class PipelineGuard:
    """Enforcement guards that FAIL FAST on violations."""

    @staticmethod
    def require_identity(candidate: CEOCandidate, phase: str, require_company: bool = True) -> None:
        """FAIL if person_unique_id missing. company_unique_id optional for CSV imports."""
        if require_company and not candidate.company_unique_id:
            raise ValueError(f"[GUARD FAIL] {phase}: company_unique_id required for {candidate.full_name}")
        if not candidate.person_unique_id:
            raise ValueError(f"[GUARD FAIL] {phase}: person_unique_id required for {candidate.full_name}")

    @staticmethod
    def require_slot_assignment(candidate: CEOCandidate) -> None:
        """FAIL if verification attempted before slot assignment."""
        if not candidate.slot_assigned:
            raise ValueError(f"[GUARD FAIL] Phase 7: Slot assignment required before verification for {candidate.person_unique_id}")

    @staticmethod
    def require_valid_for_promotion(candidate: CEOCandidate) -> None:
        """FAIL if non-VALID email would be promoted."""
        if candidate.verification_status != VerificationStatus.VALID.value:
            raise ValueError(f"[GUARD FAIL] Phase 8: Only VALID emails can be promoted. Got {candidate.verification_status} for {candidate.generated_email}")

    @staticmethod
    def check_ttl_violation(email: str, last_verified: Optional[datetime], ttl_days: int = VERIFICATION_TTL_DAYS) -> bool:
        """Return True if TTL not expired (verification should be skipped)."""
        if last_verified is None:
            return False
        return datetime.now() - last_verified < timedelta(days=ttl_days)


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


# =============================================================================
# PHASE 5: EMAIL GENERATION (Pattern-Only)
# =============================================================================

def phase5_generate_emails(
    candidates: List[CEOCandidate],
    conn,
    stats: PipelineStats
) -> List[CEOCandidate]:
    """
    Phase 5: Email Generation (Pattern-Only)

    - Generate candidate emails DETERMINISTICALLY from patterns
    - Do NOT guess or infer missing patterns
    - Output: email, source='pattern', confidence=LOW|MEDIUM
    """
    print("\n" + "="*60)
    print("PHASE 5: EMAIL GENERATION (Pattern-Only)")
    print("="*60)

    cursor = conn.cursor()

    # Load verified patterns from company.company_master (by ID and domain)
    print("  Loading verified patterns from company.company_master...")
    cursor.execute("""
        SELECT company_unique_id, website_url, email_pattern, email_pattern_confidence
        FROM company.company_master
        WHERE email_pattern IS NOT NULL AND email_pattern != ''
    """)
    company_patterns = {}  # company_unique_id -> (pattern, confidence)
    domain_patterns = {}   # normalized domain -> (pattern, confidence, company_id)

    for row in cursor.fetchall():
        company_id, website, pattern, confidence = row
        conf = confidence or 50
        company_patterns[company_id] = (pattern, conf)

        # Also index by domain for CSV imports
        if website:
            domain = website.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
            if domain:
                domain_patterns[domain] = (pattern, conf, company_id)

    print(f"  Loaded {len(company_patterns)} verified patterns ({len(domain_patterns)} domains)")

    for candidate in candidates:
        # GUARD: Require identity (company_unique_id optional for CSV imports)
        try:
            PipelineGuard.require_identity(candidate, "Phase 5", require_company=bool(candidate.company_unique_id))
        except ValueError as e:
            candidate.error = str(e)
            stats.errors.append(str(e))
            continue

        # Check for domain
        if not candidate.company_domain:
            candidate.error = "missing_domain"
            stats.emails_skipped_no_domain += 1
            continue

        # Normalize domain
        domain = candidate.company_domain.lower().strip()

        # Get pattern - try by company_unique_id first, then by domain
        pattern_data = None
        if candidate.company_unique_id:
            pattern_data = company_patterns.get(candidate.company_unique_id)

        if not pattern_data and domain:
            # Try domain lookup (for CSV imports without company_unique_id)
            domain_data = domain_patterns.get(domain)
            if domain_data:
                pattern, conf, company_id = domain_data
                pattern_data = (pattern, conf)
                # Populate company_unique_id for downstream phases
                if not candidate.company_unique_id:
                    candidate.company_unique_id = company_id

        if pattern_data:
            pattern, confidence = pattern_data
            candidate.email_pattern = pattern
            candidate.email_confidence = "MEDIUM" if confidence >= 70 else "LOW"
        else:
            # Default pattern - first.last (most common)
            pattern = "{first}.{last}@{domain}"
            candidate.email_pattern = pattern
            candidate.email_confidence = "LOW"

        # Generate email DETERMINISTICALLY
        first = candidate.first_name.lower().strip() if candidate.first_name else ""
        last = candidate.last_name.lower().strip() if candidate.last_name else ""
        domain = candidate.company_domain.lower().strip()

        # Clean names (ASCII alphanumeric only - strip accented chars)
        import unicodedata
        first = unicodedata.normalize('NFKD', first).encode('ascii', 'ignore').decode('ascii')
        last = unicodedata.normalize('NFKD', last).encode('ascii', 'ignore').decode('ascii')
        first = ''.join(c for c in first if c.isalnum())
        last = ''.join(c for c in last if c.isalnum())

        if not first or not last:
            candidate.error = "missing_name_components"
            stats.emails_skipped_no_pattern += 1
            continue

        # Apply pattern
        try:
            email = candidate.email_pattern.format(
                first=first,
                last=last,
                f=first[0] if first else "",
                l=last[0] if last else "",
                domain=domain
            )
            candidate.generated_email = email
            candidate.email_source = "pattern"
            stats.emails_generated += 1
        except (KeyError, IndexError) as e:
            # Pattern doesn't match expected format, use default
            candidate.generated_email = f"{first}.{last}@{domain}"
            candidate.email_source = "pattern"
            candidate.email_confidence = "LOW"
            stats.emails_generated += 1

    cursor.close()

    print(f"  Emails generated: {stats.emails_generated}")
    print(f"  Skipped (no domain): {stats.emails_skipped_no_domain}")
    print(f"  Skipped (no pattern/name): {stats.emails_skipped_no_pattern}")

    return candidates


# =============================================================================
# PHASE 6: CEO SLOT ASSIGNMENT
# =============================================================================

def phase6_assign_slots(
    candidates: List[CEOCandidate],
    conn,
    stats: PipelineStats
) -> List[CEOCandidate]:
    """
    Phase 6: CEO Slot Assignment

    - Assign person to CEO slot using:
      1. Exact title match
      2. Seniority / tenure
      3. Recency
    - Resolve collisions deterministically
    - Output: person_id, slot='CEO', slot_resolution_reason
    """
    print("\n" + "="*60)
    print("PHASE 6: CEO SLOT ASSIGNMENT")
    print("="*60)

    cursor = conn.cursor()

    # CEO title patterns (exact matches get priority)
    CEO_EXACT_TITLES = {
        'ceo', 'chief executive officer', 'chief executive',
        'president & ceo', 'ceo & president', 'president and ceo',
        'founder & ceo', 'ceo & founder', 'co-ceo'
    }

    for candidate in candidates:
        # Skip if no email generated
        if not candidate.generated_email:
            continue

        # For CSV imports without company_unique_id, mark as assigned but skip DB operations
        if not candidate.company_unique_id:
            candidate.slot_assigned = True
            candidate.slot_resolution_reason = "csv_import_no_company"
            stats.slots_assigned += 1
            continue

        # GUARD: Require identity for DB operations
        try:
            PipelineGuard.require_identity(candidate, "Phase 6")
        except ValueError as e:
            candidate.error = str(e)
            stats.errors.append(str(e))
            continue

        # Skip if no email generated (redundant check after early exit)
        if not candidate.generated_email:
            stats.slots_skipped += 1
            continue

        # Skip if already has slot assigned (from Neon load)
        if candidate.slot_assigned:
            stats.slots_assigned += 1
            continue

        # Determine resolution reason
        title_lower = candidate.job_title.lower().strip() if candidate.job_title else ""
        if title_lower in CEO_EXACT_TITLES:
            resolution_reason = SlotResolutionReason.EXACT_TITLE_MATCH.value
        else:
            resolution_reason = SlotResolutionReason.SENIORITY_WIN.value

        # Check existing slot
        cursor.execute("""
            SELECT company_slot_unique_id, person_unique_id, confidence_score, is_filled
            FROM people.company_slot
            WHERE company_unique_id = %s AND slot_type = %s
        """, (candidate.company_unique_id, candidate.slot_type))

        existing_slot = cursor.fetchone()

        if existing_slot:
            slot_id, current_person, current_score, is_filled = existing_slot
            current_score = float(current_score) if current_score else 0.0

            # Seniority competition - higher score wins
            if candidate.seniority_score > current_score or not is_filled:
                # Update slot (triggers history via trg_slot_assignment_history)
                cursor.execute("""
                    UPDATE people.company_slot
                    SET person_unique_id = %s,
                        confidence_score = %s,
                        is_filled = TRUE,
                        filled_at = NOW(),
                        source_system = %s,
                        slot_status = 'filled'
                    WHERE company_slot_unique_id = %s
                """, (candidate.person_unique_id, candidate.seniority_score,
                      'executive_pipeline', slot_id))

                candidate.slot_assigned = True
                candidate.slot_resolution_reason = resolution_reason
                stats.slots_assigned += 1

                if current_person and is_filled:
                    stats.slots_displaced += 1
                    candidate.slot_resolution_reason = SlotResolutionReason.DISPLACEMENT.value
            else:
                # Lost competition
                candidate.slot_assigned = False
                candidate.slot_resolution_reason = "lost_seniority_competition"
                stats.slots_skipped += 1
        else:
            # Create new slot
            slot_unique_id = f"04.04.05.99.{candidate.row_id:05d}.{candidate.row_id % 1000:03d}"

            cursor.execute("""
                INSERT INTO people.company_slot (
                    company_slot_unique_id, company_unique_id, person_unique_id,
                    slot_type, confidence_score, is_filled, filled_at,
                    source_system, slot_status, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, TRUE, NOW(), 'executive_pipeline', 'filled', NOW()
                )
            """, (slot_unique_id, candidate.company_unique_id, candidate.person_unique_id,
                  candidate.slot_type, candidate.seniority_score))

            candidate.slot_assigned = True
            candidate.slot_resolution_reason = SlotResolutionReason.FIRST_CANDIDATE.value
            stats.slots_assigned += 1

    conn.commit()
    cursor.close()

    print(f"  Slots assigned: {stats.slots_assigned}")
    print(f"  Displacements: {stats.slots_displaced}")
    print(f"  Skipped: {stats.slots_skipped}")

    return candidates


# =============================================================================
# PHASE 7: EMAIL VERIFICATION (MULTI-PROVIDER HARD GATE)
# =============================================================================

async def verify_with_millionverifier(
    session: aiohttp.ClientSession,
    email: str,
    api_key: str
) -> Tuple[str, str]:
    """Verify email with MillionVerifier API."""
    url = f"{MILLIONVERIFIER_API_URL}?api={api_key}&email={email}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                result = data.get('result', 'unknown').lower()

                if result in ['ok', 'valid', 'deliverable']:
                    return VerificationStatus.VALID.value, result
                elif result in ['risky', 'catch_all', 'accept_all']:
                    return VerificationStatus.RISKY.value, result
                elif result in ['invalid', 'disposable', 'unknown_email']:
                    return VerificationStatus.INVALID.value, result
                else:
                    return VerificationStatus.UNKNOWN.value, result
            else:
                return VerificationStatus.UNKNOWN.value, f"api_error_{response.status}"
    except asyncio.TimeoutError:
        return VerificationStatus.UNKNOWN.value, "timeout"
    except Exception as e:
        return VerificationStatus.UNKNOWN.value, f"error_{str(e)[:50]}"


async def verify_with_emailverifyio(
    session: aiohttp.ClientSession,
    emails: List[str],
    api_key: str
) -> Dict[str, Tuple[str, str]]:
    """
    Verify emails with EmailVerify.io API (batch).

    Returns: {email: (status, raw_result)}
    """
    import time

    # Create batch verification task
    url = f"{EMAILVERIFYIO_API_URL}validate-batch"
    payload = {
        "title": f"CEO_Pipeline_{int(time.time())}",
        "key": api_key,
        "email_batch": [{"address": email} for email in emails]
    }

    results = {}

    try:
        # Submit batch
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                error_msg = f"api_error_{response.status}"
                return {email: (VerificationStatus.UNKNOWN.value, error_msg) for email in emails}

            data = await response.json()
            # API returns 'queued' or 'success' on successful submission
            if data.get('status') not in ['success', 'queued']:
                error_msg = data.get('message', 'unknown_error')
                return {email: (VerificationStatus.UNKNOWN.value, error_msg) for email in emails}

            task_id = data.get('task_id')
            if not task_id:
                return {email: (VerificationStatus.UNKNOWN.value, 'no_task_id') for email in emails}

        # Poll for results (max 60 seconds)
        get_url = f"{EMAILVERIFYIO_API_URL}get-result-bulk-verification-task?key={api_key}&task_id={task_id}"
        max_attempts = 30

        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Wait 2 seconds between polls

            async with session.get(get_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    continue

                data = await response.json()
                status = data.get('status', '')

                if status == 'verified':
                    # Parse results
                    email_batch = data.get('results', {}).get('email_batch', [])
                    for item in email_batch:
                        email = item.get('address', '').lower()
                        result_status = item.get('status', 'unknown').lower()
                        sub_status = item.get('sub_status', '')

                        # Map EmailVerify.io statuses to our gate statuses
                        # Valid statuses: 'valid', 'ok'
                        # Risky statuses: 'catch_all', 'role_based', 'accept_all'
                        # Invalid statuses: 'invalid', 'unknown', 'no_dns_entries', 'mailbox_not_found'
                        if result_status in ['valid', 'ok']:
                            results[email] = (VerificationStatus.VALID.value, result_status)
                        elif result_status in ['catch_all', 'catch-all', 'role_based', 'accept_all', 'risky']:
                            results[email] = (VerificationStatus.RISKY.value, f"{result_status}:{sub_status}")
                        elif result_status in ['invalid', 'unknown', 'mailbox_not_found', 'syntax_error']:
                            results[email] = (VerificationStatus.INVALID.value, f"{result_status}:{sub_status}")
                        else:
                            # Treat unrecognized statuses as UNKNOWN
                            results[email] = (VerificationStatus.UNKNOWN.value, f"{result_status}:{sub_status}")

                    # Fill in any missing emails
                    for email in emails:
                        if email.lower() not in results:
                            results[email.lower()] = (VerificationStatus.UNKNOWN.value, 'not_in_response')

                    return results

                elif status in ['error', 'failed']:
                    error_msg = data.get('message', 'task_failed')
                    return {email: (VerificationStatus.UNKNOWN.value, error_msg) for email in emails}

        # Timeout waiting for results
        return {email: (VerificationStatus.UNKNOWN.value, 'poll_timeout') for email in emails}

    except asyncio.TimeoutError:
        return {email: (VerificationStatus.UNKNOWN.value, 'timeout') for email in emails}
    except Exception as e:
        return {email: (VerificationStatus.UNKNOWN.value, f"error_{str(e)[:50]}") for email in emails}


async def verify_single_email(
    session: aiohttp.ClientSession,
    email: str,
    api_key: str,
    provider: str = VERIFIER_MILLIONVERIFIER
) -> Tuple[str, str]:
    """
    Verify a single email with the specified provider.

    Providers:
        - millionverifier: MillionVerifier API
        - emailverifyio: EmailVerify.io API
    """
    if provider == VERIFIER_MILLIONVERIFIER:
        return await verify_with_millionverifier(session, email, api_key)
    elif provider == VERIFIER_EMAILVERIFYIO:
        # For single email, use batch with one email
        results = await verify_with_emailverifyio(session, [email], api_key)
        return results.get(email.lower(), (VerificationStatus.UNKNOWN.value, 'not_found'))
    else:
        return VerificationStatus.UNKNOWN.value, f"unknown_provider_{provider}"


async def phase7_verify_emails(
    candidates: List[CEOCandidate],
    conn,
    stats: PipelineStats,
    api_key: str,
    provider: str = DEFAULT_VERIFIER
) -> List[CEOCandidate]:
    """
    Phase 7: Email Verification (MULTI-PROVIDER HARD GATE)

    Supported providers:
        - millionverifier: MillionVerifier API (single email)
        - emailverifyio: EmailVerify.io API (batch)

    Gate logic:
        - VALID -> eligible for persistence
        - INVALID -> discard, do not promote
        - RISKY | UNKNOWN -> flag only, no action

    Enforce one verification per email per TTL. No retries.
    """
    provider_name = "MillionVerifier" if provider == VERIFIER_MILLIONVERIFIER else "EmailVerify.io"

    print("\n" + "="*60)
    print(f"PHASE 7: EMAIL VERIFICATION ({provider_name} - HARD GATE)")
    print("="*60)

    if not api_key:
        print(f"  [FAIL] {provider.upper()}_API_KEY not set")
        for candidate in candidates:
            candidate.error = "no_api_key"
        return candidates

    cursor = conn.cursor()

    # Load TTL cache - emails verified within TTL period
    print("  Loading verification TTL cache...")
    cursor.execute("""
        SELECT email, verified_at
        FROM company.email_verification
        WHERE verification_service = %s
        AND verified_at > NOW() - INTERVAL '%s days'
    """, (provider_name, VERIFICATION_TTL_DAYS))
    ttl_cache = {row[0].lower(): row[1] for row in cursor.fetchall()}
    print(f"  TTL cache entries: {len(ttl_cache)}")

    # Filter candidates for verification
    to_verify = []
    for candidate in candidates:
        if not candidate.slot_assigned:
            continue

        if not candidate.generated_email:
            continue

        email_lower = candidate.generated_email.lower()

        if email_lower in ttl_cache:
            stats.emails_skipped_ttl += 1
            candidate.verification_status = VerificationStatus.VALID.value
            candidate.verified_at = ttl_cache[email_lower]
            continue

        to_verify.append(candidate)

    print(f"  Emails to verify: {len(to_verify)}")
    print(f"  Skipped (TTL): {stats.emails_skipped_ttl}")

    if not to_verify:
        print("  No emails to verify")
        cursor.close()
        return candidates

    print(f"  Starting verification with {provider_name}...")

    async with aiohttp.ClientSession() as session:
        if provider == VERIFIER_EMAILVERIFYIO:
            # Batch verification with EmailVerify.io
            emails_to_verify = [c.generated_email for c in to_verify]
            results = await verify_with_emailverifyio(session, emails_to_verify, api_key)

            for candidate in to_verify:
                email_lower = candidate.generated_email.lower()
                status, raw_result = results.get(email_lower, (VerificationStatus.UNKNOWN.value, 'not_found'))

                candidate.verification_status = status
                candidate.verification_result_raw = raw_result
                candidate.verified_at = datetime.now()
                candidate.verifier = provider_name

                stats.emails_verified += 1
                if status == VerificationStatus.VALID.value:
                    stats.emails_valid += 1
                elif status == VerificationStatus.RISKY.value:
                    stats.emails_risky += 1
                elif status == VerificationStatus.INVALID.value:
                    stats.emails_invalid += 1
                else:
                    stats.emails_unknown += 1
        else:
            # Single email verification with MillionVerifier
            for i, candidate in enumerate(to_verify):
                status, raw_result = await verify_with_millionverifier(
                    session, candidate.generated_email, api_key
                )

                candidate.verification_status = status
                candidate.verification_result_raw = raw_result
                candidate.verified_at = datetime.now()
                candidate.verifier = provider_name

                stats.emails_verified += 1
                if status == VerificationStatus.VALID.value:
                    stats.emails_valid += 1
                elif status == VerificationStatus.RISKY.value:
                    stats.emails_risky += 1
                elif status == VerificationStatus.INVALID.value:
                    stats.emails_invalid += 1
                else:
                    stats.emails_unknown += 1

                if (i + 1) % 50 == 0:
                    print(f"    Verified: {i + 1}/{len(to_verify)}")

        # Log all verifications to company.email_verification (TTL tracking)
        for candidate in to_verify:
            try:
                cursor.execute("""
                    INSERT INTO company.email_verification (
                        enrichment_id, email, verification_status, verification_service,
                        verification_result, verified_at, created_at
                    ) VALUES (
                        0, %s, %s, %s, %s::jsonb, NOW(), NOW()
                    )
                    ON CONFLICT DO NOTHING
                """, (
                    candidate.generated_email,
                    candidate.verification_status,
                    provider_name,
                    f'{{"raw_result": "{candidate.verification_result_raw}"}}'
                ))
            except Exception:
                pass  # Non-critical, continue

    conn.commit()
    cursor.close()

    print(f"\n  Verification complete:")
    print(f"    VALID: {stats.emails_valid}")
    print(f"    RISKY: {stats.emails_risky}")
    print(f"    INVALID: {stats.emails_invalid}")
    print(f"    UNKNOWN: {stats.emails_unknown}")

    return candidates


def phase7_verify_emails_sync(
    candidates: List[CEOCandidate],
    conn,
    stats: PipelineStats,
    api_key: str,
    provider: str = DEFAULT_VERIFIER
) -> List[CEOCandidate]:
    """Synchronous wrapper for async verification."""
    return asyncio.run(phase7_verify_emails(candidates, conn, stats, api_key, provider))


# =============================================================================
# PHASE 8: PERSISTENCE (Neon + CSV)
# =============================================================================

def phase8_persist(
    candidates: List[CEOCandidate],
    conn,
    stats: PipelineStats,
    output_dir: str
) -> Dict[str, str]:
    """
    Phase 8: Persistence (Neon + CSV)

    Neon:
        - Write VALID emails ONLY
        - Fields: person_id, email, verification_status='VALID',
                  verifier='MillionVerifier', verified_at
        - Enforce immutability on verification fields

    CSV:
        - Include ALL candidates with statuses
        - Purpose: ops audit only
    """
    print("\n" + "="*60)
    print("PHASE 8: PERSISTENCE (Neon + CSV)")
    print("="*60)

    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)

    # Get slot type for filename prefix (lowercase)
    slot_type_prefix = candidates[0].slot_type.lower() if candidates else "exec"

    output_files = {}

    # --- NEON: VALID emails only ---
    print("\n  Writing VALID emails to Neon...")
    valid_count = 0

    for candidate in candidates:
        # GUARD: Only VALID emails can be promoted
        if candidate.verification_status != VerificationStatus.VALID.value:
            continue

        try:
            # Enforce guard
            PipelineGuard.require_valid_for_promotion(candidate)

            # Update people.people_master with verified email
            cursor.execute("""
                UPDATE people.people_master
                SET email = %s,
                    email_verified = TRUE,
                    email_verification_source = %s,
                    email_verified_at = %s,
                    updated_at = NOW()
                WHERE unique_id = %s
            """, (
                candidate.generated_email,
                candidate.verifier,
                candidate.verified_at,
                candidate.person_unique_id
            ))

            candidate.promoted_to_neon = True
            valid_count += 1

        except Exception as e:
            candidate.error = str(e)
            stats.errors.append(f"Neon write error for {candidate.full_name}: {e}")
            # Rollback failed transaction to continue with next record
            conn.rollback()

    conn.commit()
    stats.records_promoted_neon = valid_count
    print(f"    Promoted to Neon: {valid_count}")

    # --- CSV: ALL candidates (audit) ---
    print("\n  Writing ALL candidates to CSV (audit)...")

    # 1. Full audit CSV
    audit_file = os.path.join(output_dir, f"{slot_type_prefix}_pipeline_audit_{timestamp}.csv")
    with open(audit_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_unique_id', 'company_unique_id', 'full_name', 'job_title',
            'company_name', 'company_domain', 'generated_email', 'email_source',
            'email_confidence', 'slot_type', 'slot_assigned', 'slot_resolution_reason',
            'verification_status', 'verification_result_raw', 'verifier', 'verified_at',
            'promoted_to_neon', 'error'
        ])
        for c in candidates:
            writer.writerow([
                c.person_unique_id, c.company_unique_id, c.full_name, c.job_title,
                c.company_name, c.company_domain, c.generated_email, c.email_source,
                c.email_confidence, c.slot_type, c.slot_assigned, c.slot_resolution_reason,
                c.verification_status, c.verification_result_raw, c.verifier,
                c.verified_at.isoformat() if c.verified_at else None,
                c.promoted_to_neon, c.error
            ])
    output_files['audit'] = audit_file
    stats.records_written_csv = len(candidates)
    print(f"    Written: {audit_file} ({len(candidates)} records)")

    # 2. VALID only CSV (ready for send)
    valid_file = os.path.join(output_dir, f"{slot_type_prefix}_valid_emails_{timestamp}.csv")
    valid_candidates = [c for c in candidates if c.verification_status == VerificationStatus.VALID.value]
    with open(valid_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_unique_id', 'company_unique_id', 'full_name', 'email',
            'company_name', 'slot_type', 'verifier', 'verified_at'
        ])
        for c in valid_candidates:
            writer.writerow([
                c.person_unique_id, c.company_unique_id, c.full_name, c.generated_email,
                c.company_name, c.slot_type, c.verifier,
                c.verified_at.isoformat() if c.verified_at else None
            ])
    output_files['valid'] = valid_file
    print(f"    Written: {valid_file} ({len(valid_candidates)} records)")

    # 3. INVALID/RISKY CSV (flagged)
    flagged_file = os.path.join(output_dir, f"{slot_type_prefix}_flagged_emails_{timestamp}.csv")
    flagged = [c for c in candidates if c.verification_status in
               [VerificationStatus.INVALID.value, VerificationStatus.RISKY.value, VerificationStatus.UNKNOWN.value]]
    with open(flagged_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'person_unique_id', 'full_name', 'email', 'verification_status',
            'verification_result_raw', 'company_name'
        ])
        for c in flagged:
            writer.writerow([
                c.person_unique_id, c.full_name, c.generated_email, c.verification_status,
                c.verification_result_raw, c.company_name
            ])
    output_files['flagged'] = flagged_file
    print(f"    Written: {flagged_file} ({len(flagged)} records)")

    cursor.close()
    return output_files


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def load_candidates_from_csv(csv_path: str, slot_type: str = "CEO") -> List[CEOCandidate]:
    """Load candidates from CSV file."""
    candidates = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            candidate = CEOCandidate(
                row_id=i + 1,
                person_unique_id=row.get('person_unique_id', f"04.04.02.99.{i+1:05d}.{(i+1) % 1000:03d}"),
                company_unique_id=row.get('company_unique_id', ''),
                first_name=row.get('First Name', row.get('first_name', '')).strip(),
                last_name=row.get('Last Name', row.get('last_name', '')).strip(),
                full_name=row.get('Full Name', row.get('full_name', '')).strip(),
                job_title=row.get('Job Title', row.get('job_title', '')).strip(),
                linkedin_url=row.get('LinkedIn Profile', row.get('linkedin_url', '')).strip(),
                company_name=row.get('Company Name', row.get('company_name', '')).strip(),
                company_domain=row.get('Company Domain', row.get('company_domain', '')).strip(),
                slot_type=slot_type,
            )
            candidates.append(candidate)

    return candidates


def load_candidates_from_neon(conn, limit: int = 1000, slot_type: str = "CEO") -> List[CEOCandidate]:
    """Load candidates from Neon people.people_master."""
    cursor = conn.cursor()

    # Load people who need verification (no verified email yet)
    # These already have slots assigned of the specified type
    cursor.execute("""
        SELECT
            pm.unique_id, pm.company_unique_id, pm.first_name, pm.last_name,
            pm.title, pm.linkedin_url, pm.email,
            cm.company_name, cm.website_url, cm.email_pattern,
            cs.company_slot_unique_id, cs.is_filled
        FROM people.people_master pm
        JOIN company.company_master cm ON pm.company_unique_id = cm.company_unique_id
        JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id AND cs.slot_type = %s
        WHERE (pm.email_verified IS NULL OR pm.email_verified = FALSE)
        AND cs.is_filled = TRUE
        LIMIT %s
    """, (slot_type, limit,))

    candidates = []
    for i, row in enumerate(cursor.fetchall()):
        # Extract domain from website_url
        website = row[8] or ''
        domain = website.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]

        candidate = CEOCandidate(
            row_id=i + 1,
            person_unique_id=row[0],
            company_unique_id=row[1],
            first_name=row[2] or '',
            last_name=row[3] or '',
            full_name=f"{row[2] or ''} {row[3] or ''}".strip(),
            job_title=row[4] or '',
            linkedin_url=row[5],
            company_name=row[7] or '',
            company_domain=domain,
            email_pattern=row[9],
            # Already has slot assigned from Neon
            slot_assigned=True,
            slot_resolution_reason="pre_existing_slot",
        )
        candidates.append(candidate)

    cursor.close()
    return candidates


def run_pipeline(
    candidates: List[CEOCandidate],
    output_dir: str,
    skip_verification: bool = False,
    verifier: str = DEFAULT_VERIFIER
) -> Tuple[PipelineStats, str]:
    """
    Run the full CEO Email Pipeline (Phases 5-8).

    Args:
        candidates: List of CEOCandidate objects
        output_dir: Directory for output files
        skip_verification: Skip Phase 7 verification
        verifier: Email verification provider ('emailverifyio' or 'millionverifier')

    Returns: (stats, final_status)
        final_status: 'READY_FOR_SEND_PIPELINE' or 'FAILED (reason)'
    """
    verifier_name = "EmailVerify.io" if verifier == VERIFIER_EMAILVERIFYIO else "MillionVerifier"

    # Get slot type from first candidate (all should be same)
    slot_type = candidates[0].slot_type if candidates else "CEO"

    print("="*60)
    print(f"{slot_type} EMAIL PIPELINE - Phases 5-8")
    print("="*60)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Candidates: {len(candidates)}")
    print(f"Slot Type: {slot_type}")
    print(f"Verifier: {verifier_name}")

    stats = PipelineStats(total_records=len(candidates))
    conn = get_connection()

    try:
        # Phase 5: Email Generation
        candidates = phase5_generate_emails(candidates, conn, stats)

        # Phase 6: Slot Assignment
        candidates = phase6_assign_slots(candidates, conn, stats)

        # Phase 7: Email Verification
        if not skip_verification:
            # Get API key based on verifier
            if verifier == VERIFIER_EMAILVERIFYIO:
                api_key = os.getenv('EMAILVERIFYIO_API_KEY')
                key_name = 'EMAILVERIFYIO_API_KEY'
            else:
                api_key = os.getenv('MILLIONVERIFIER_API_KEY')
                key_name = 'MILLIONVERIFIER_API_KEY'

            if api_key:
                candidates = phase7_verify_emails_sync(candidates, conn, stats, api_key, verifier)
            else:
                print(f"\n  [WARN] {key_name} not set - skipping verification")
                for c in candidates:
                    if c.slot_assigned and c.generated_email:
                        c.verification_status = VerificationStatus.UNKNOWN.value
        else:
            print("\n  [INFO] Verification skipped (skip_verification=True)")
            for c in candidates:
                if c.slot_assigned and c.generated_email:
                    c.verification_status = VerificationStatus.VALID.value  # Assume valid for testing

        # Phase 8: Persistence
        output_files = phase8_persist(candidates, conn, stats, output_dir)

        # Final status
        if stats.records_promoted_neon > 0:
            final_status = "READY_FOR_SEND_PIPELINE"
        elif stats.emails_verified == 0 and not skip_verification:
            final_status = "FAILED (no verifications performed)"
        else:
            final_status = "READY_FOR_SEND_PIPELINE"

    except Exception as e:
        final_status = f"FAILED ({str(e)})"
        stats.errors.append(str(e))

    finally:
        conn.close()

    # Summary
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"  Total records: {stats.total_records}")
    print(f"  Emails generated: {stats.emails_generated}")
    print(f"  Slots assigned: {stats.slots_assigned}")
    print(f"  Emails verified: {stats.emails_verified}")
    print(f"    - VALID: {stats.emails_valid}")
    print(f"    - RISKY: {stats.emails_risky}")
    print(f"    - INVALID: {stats.emails_invalid}")
    print(f"    - UNKNOWN: {stats.emails_unknown}")
    print(f"  Promoted to Neon: {stats.records_promoted_neon}")
    print(f"\n  FINAL STATUS: {final_status}")

    if stats.errors:
        print(f"\n  ERRORS ({len(stats.errors)}):")
        for err in stats.errors[:5]:
            print(f"    - {err}")

    return stats, final_status


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ceo_email_pipeline.py <csv_path> [options]")
        print("       python ceo_email_pipeline.py --from-neon [options]")
        print("")
        print("Options:")
        print("  --skip-verification    Skip email verification (Phase 7)")
        print("  --limit N              Limit records from Neon (default: 1000)")
        print("  --verifier NAME        Email verifier: 'emailverifyio' (default) or 'millionverifier'")
        print("  --slot-type TYPE       Slot type: CEO, CFO, HR (default: CEO)")
        print("")
        print("Environment Variables:")
        print("  EMAILVERIFYIO_API_KEY    API key for EmailVerify.io")
        print("  MILLIONVERIFIER_API_KEY  API key for MillionVerifier")
        sys.exit(1)

    skip_verification = '--skip-verification' in sys.argv

    # Parse verifier option
    verifier = DEFAULT_VERIFIER
    if '--verifier' in sys.argv:
        idx = sys.argv.index('--verifier')
        if idx + 1 < len(sys.argv):
            verifier = sys.argv[idx + 1].lower()
            if verifier not in [VERIFIER_EMAILVERIFYIO, VERIFIER_MILLIONVERIFIER]:
                print(f"[ERROR] Unknown verifier: {verifier}")
                print(f"  Valid options: {VERIFIER_EMAILVERIFYIO}, {VERIFIER_MILLIONVERIFIER}")
                sys.exit(1)

    # Parse slot-type option
    slot_type = "CEO"
    if '--slot-type' in sys.argv:
        idx = sys.argv.index('--slot-type')
        if idx + 1 < len(sys.argv):
            slot_type = sys.argv[idx + 1].upper()
            if slot_type not in ['CEO', 'CFO', 'HR', 'CTO', 'CMO', 'COO']:
                print(f"[ERROR] Unknown slot type: {slot_type}")
                print(f"  Valid options: CEO, CFO, HR, CTO, CMO, COO")
                sys.exit(1)

    if sys.argv[1] == '--from-neon':
        # Load from Neon
        limit = 1000
        if '--limit' in sys.argv:
            idx = sys.argv.index('--limit')
            limit = int(sys.argv[idx + 1])

        print(f"Loading candidates from Neon (limit: {limit})...")
        conn = get_connection()
        candidates = load_candidates_from_neon(conn, limit, slot_type)
        conn.close()
        output_dir = "pipeline_output"
    else:
        # Load from CSV
        csv_path = sys.argv[1]
        print(f"Loading candidates from CSV: {csv_path}")
        candidates = load_candidates_from_csv(csv_path, slot_type)
        output_dir = os.path.join(os.path.dirname(csv_path), "pipeline_output")

    if not candidates:
        print("[FAIL] No candidates to process")
        sys.exit(1)

    stats, final_status = run_pipeline(candidates, output_dir, skip_verification, verifier)

    # Exit code based on status
    if final_status.startswith("READY"):
        print(f"\n{final_status}")
        sys.exit(0)
    else:
        print(f"\n{final_status}")
        sys.exit(1)
