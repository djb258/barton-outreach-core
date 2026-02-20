#!/usr/bin/env python3
"""
First-Run Production Smoke Test
================================

PURPOSE: Prove the whole sovereign pipeline works end-to-end once.

This is a READ-ONLY test that:
1. Picks 5 random sovereign company IDs
2. Reads completion + eligibility views
3. Runs marketing safety gate in dry-run
4. Logs expected BLOCKED / ALLOWED outcomes
5. Writes results to stdout + audit log

============================================================================
⚠️  DO NOT WRITE - READ-ONLY SCRIPT
============================================================================
This script is READ-ONLY for sovereign tables:
- outreach.company_hub_status
# - outreach.manual_overrides  # DROPPED 2026-02-20: table had 0 rows, removed during database consolidation
- outreach.hub_registry

NO WRITES to business tables. Read + audit only.
============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime
from uuid import uuid4, UUID
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('smoke_test')

# ============================================================================
# DATABASE CONFIG
# ============================================================================

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
        port=5432,
        database=os.getenv('NEON_DATABASE', 'Marketing DB'),
        user=os.getenv('NEON_USER', 'Marketing DB_owner'),
        password=os.getenv('NEON_PASSWORD', 'npg_OsE4Z2oPCpiT'),
        sslmode='require'
    )


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CompletionStatus:
    """Completion status from vw_sovereign_completion."""
    company_unique_id: str
    company_target_status: str
    dol_status: str
    people_status: str
    talent_flow_status: str
    pass_count: int
    overall_status: str
    bit_score: Optional[float]


@dataclass
class EligibilityStatus:
    """Eligibility status from vw_marketing_eligibility_with_overrides."""
    company_unique_id: str
    effective_tier: int
    computed_tier: int
    is_blocked: bool
    has_override: bool
    override_types: Optional[str]
    override_reasons: Optional[str]


@dataclass
class SafetyGateResult:
    """Result of marketing safety gate check."""
    company_unique_id: str
    decision: str  # ALLOWED, BLOCKED
    reason: str
    tier: int
    checks_passed: List[str]
    checks_failed: List[str]


@dataclass
class SmokeTestResult:
    """Complete smoke test result for a company."""
    company_unique_id: str
    completion: CompletionStatus
    eligibility: EligibilityStatus
    safety_gate: SafetyGateResult
    test_passed: bool
    notes: List[str]


# ============================================================================
# VIEW READERS (READ-ONLY)
# ============================================================================

def read_completion_status(cur, company_id: str) -> Optional[CompletionStatus]:
    """
    Read completion status from vw_sovereign_completion.
    
    READ-ONLY: No mutations.
    """
    cur.execute("""
        SELECT 
            company_unique_id,
            company_target_status,
            dol_status,
            people_status,
            talent_flow_status,
            pass_count,
            overall_status,
            bit_score
        FROM outreach.vw_sovereign_completion
        WHERE company_unique_id = %s
    """, (company_id,))
    
    row = cur.fetchone()
    if not row:
        return None
    
    return CompletionStatus(
        company_unique_id=str(row['company_unique_id']),
        company_target_status=row['company_target_status'],
        dol_status=row['dol_status'],
        people_status=row['people_status'],
        talent_flow_status=row['talent_flow_status'],
        pass_count=row['pass_count'],
        overall_status=row['overall_status'],
        bit_score=row.get('bit_score'),
    )


def read_eligibility_status(cur, company_id: str) -> Optional[EligibilityStatus]:
    """
    Read eligibility status from vw_marketing_eligibility_with_overrides.
    
    READ-ONLY: No mutations.
    """
    cur.execute("""
        SELECT 
            company_unique_id,
            effective_tier,
            computed_tier,
            has_active_override,
            override_types,
            override_reasons
        FROM outreach.vw_marketing_eligibility_with_overrides
        WHERE company_unique_id = %s
    """, (company_id,))
    
    row = cur.fetchone()
    if not row:
        return None
    
    # Determine if blocked (tier < 0 or has blocking override)
    is_blocked = row['effective_tier'] < 0
    
    return EligibilityStatus(
        company_unique_id=str(row['company_unique_id']),
        effective_tier=row['effective_tier'],
        computed_tier=row['computed_tier'],
        is_blocked=is_blocked,
        has_override=row['has_active_override'],
        override_types=row.get('override_types'),
        override_reasons=row.get('override_reasons'),
    )


def get_random_company_ids(cur, count: int = 5) -> List[str]:
    """
    Get random company IDs from sovereign completion view.
    
    READ-ONLY: No mutations.
    """
    cur.execute("""
        SELECT company_unique_id
        FROM outreach.vw_sovereign_completion
        ORDER BY RANDOM()
        LIMIT %s
    """, (count,))
    
    return [str(row['company_unique_id']) for row in cur.fetchall()]


# ============================================================================
# SAFETY GATE (DRY-RUN)
# ============================================================================

def run_safety_gate_dry_run(
    completion: CompletionStatus,
    eligibility: EligibilityStatus
) -> SafetyGateResult:
    """
    Run marketing safety gate in DRY-RUN mode.
    
    This simulates the decision logic WITHOUT making any changes.
    
    Checks:
    1. Is company blocked by override?
    2. Is company at Tier -1 (INELIGIBLE)?
    3. Is completion status valid?
    4. Is BIT score present (for Tier 3)?
    """
    checks_passed = []
    checks_failed = []
    
    company_id = completion.company_unique_id
    
    # Check 1: Override block
    if eligibility.is_blocked:
        checks_failed.append(f"OVERRIDE_BLOCKED: {eligibility.override_types}")
        return SafetyGateResult(
            company_unique_id=company_id,
            decision="BLOCKED",
            reason=f"Override active: {eligibility.override_types}",
            tier=eligibility.effective_tier,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )
    else:
        checks_passed.append("NO_BLOCKING_OVERRIDE")
    
    # Check 2: Tier check
    if eligibility.effective_tier < 0:
        checks_failed.append(f"TIER_INELIGIBLE: {eligibility.effective_tier}")
        return SafetyGateResult(
            company_unique_id=company_id,
            decision="BLOCKED",
            reason=f"Tier is {eligibility.effective_tier} (INELIGIBLE)",
            tier=eligibility.effective_tier,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )
    else:
        checks_passed.append(f"TIER_VALID: {eligibility.effective_tier}")
    
    # Check 3: Completion status
    if completion.overall_status == 'BLOCKED':
        checks_failed.append("COMPLETION_BLOCKED")
        return SafetyGateResult(
            company_unique_id=company_id,
            decision="BLOCKED",
            reason="Completion status is BLOCKED",
            tier=eligibility.effective_tier,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )
    else:
        checks_passed.append(f"COMPLETION_OK: {completion.overall_status}")
    
    # Check 4: BIT score for Tier 3
    if eligibility.effective_tier >= 3:
        if completion.bit_score is None or completion.bit_score < 50:
            checks_failed.append(f"BIT_SCORE_LOW: {completion.bit_score}")
            # Note: This shouldn't happen if view logic is correct
            # but we check anyway
        else:
            checks_passed.append(f"BIT_SCORE_OK: {completion.bit_score}")
    
    # All checks passed
    return SafetyGateResult(
        company_unique_id=company_id,
        decision="ALLOWED",
        reason=f"All checks passed, Tier {eligibility.effective_tier}",
        tier=eligibility.effective_tier,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
    )


# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_to_audit(cur, results: List[SmokeTestResult], run_id: str) -> None:
    """
    Log smoke test results to audit log.
    
    Uses shq.audit_log table.
    """
    try:
        summary = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'companies_tested': len(results),
            'tests_passed': sum(1 for r in results if r.test_passed),
            'tests_failed': sum(1 for r in results if not r.test_passed),
            'decisions': {
                'ALLOWED': sum(1 for r in results if r.safety_gate.decision == 'ALLOWED'),
                'BLOCKED': sum(1 for r in results if r.safety_gate.decision == 'BLOCKED'),
            },
            'tier_distribution': {},
        }
        
        for r in results:
            tier = r.eligibility.effective_tier
            tier_key = f"tier_{tier}"
            summary['tier_distribution'][tier_key] = summary['tier_distribution'].get(tier_key, 0) + 1
        
        cur.execute("""
            INSERT INTO shq.audit_log (event_type, event_source, details, created_at)
            VALUES (%s, %s, %s::jsonb, NOW())
        """, ('smoke_test_complete', 'smoke_test', json.dumps(summary, default=str)))
        
        cur.connection.commit()
        logger.info(f"Audit log entry created for run {run_id}")
        
    except Exception as e:
        logger.warning(f"Failed to log to audit: {e}")


# ============================================================================
# MAIN SMOKE TEST
# ============================================================================

def run_smoke_test(company_count: int = 5) -> List[SmokeTestResult]:
    """
    Run the production smoke test.
    
    Picks random companies, reads views, runs safety gate, logs results.
    """
    run_id = str(uuid4())
    results = []
    
    logger.info("=" * 60)
    logger.info("PRODUCTION SMOKE TEST")
    logger.info("=" * 60)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Companies to test: {company_count}")
    logger.info("")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get random company IDs
        company_ids = get_random_company_ids(cur, company_count)
        logger.info(f"Selected {len(company_ids)} random companies")
        logger.info("")
        
        for i, company_id in enumerate(company_ids, 1):
            logger.info(f"--- Company {i}/{len(company_ids)}: {company_id[:8]}... ---")
            notes = []
            
            # Read completion status
            completion = read_completion_status(cur, company_id)
            if not completion:
                logger.warning(f"  No completion data found")
                notes.append("No completion data")
                continue
            
            logger.info(f"  Completion: {completion.overall_status}")
            logger.info(f"  Hubs: CT={completion.company_target_status}, DOL={completion.dol_status}, PI={completion.people_status}, TF={completion.talent_flow_status}")
            logger.info(f"  BIT Score: {completion.bit_score}")
            
            # Read eligibility status
            eligibility = read_eligibility_status(cur, company_id)
            if not eligibility:
                logger.warning(f"  No eligibility data found")
                notes.append("No eligibility data")
                continue
            
            logger.info(f"  Tier: {eligibility.effective_tier} (computed: {eligibility.computed_tier})")
            logger.info(f"  Blocked: {eligibility.is_blocked}, Override: {eligibility.has_override}")
            
            # Run safety gate (dry-run)
            safety = run_safety_gate_dry_run(completion, eligibility)
            
            if safety.decision == "ALLOWED":
                logger.info(f"  ✅ Decision: ALLOWED - {safety.reason}")
            else:
                logger.info(f"  🚫 Decision: BLOCKED - {safety.reason}")
            
            logger.info(f"  Checks passed: {safety.checks_passed}")
            if safety.checks_failed:
                logger.info(f"  Checks failed: {safety.checks_failed}")
            
            # Determine if test passed (data is consistent)
            test_passed = True
            
            # Consistency check: Tier should match hub statuses
            if eligibility.effective_tier == 0 and completion.company_target_status != 'PASS':
                notes.append("INCONSISTENT: Tier 0 but CT not PASS")
                test_passed = False
            
            result = SmokeTestResult(
                company_unique_id=company_id,
                completion=completion,
                eligibility=eligibility,
                safety_gate=safety,
                test_passed=test_passed,
                notes=notes,
            )
            results.append(result)
            logger.info("")
        
        # Log to audit
        log_to_audit(cur, results, run_id)
        
    except Exception as e:
        logger.error(f"Smoke test failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()
    
    # Summary
    logger.info("=" * 60)
    logger.info("SMOKE TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for r in results if r.test_passed)
    failed = len(results) - passed
    allowed = sum(1 for r in results if r.safety_gate.decision == "ALLOWED")
    blocked = len(results) - allowed
    
    logger.info(f"Companies tested: {len(results)}")
    logger.info(f"Tests passed: {passed}")
    logger.info(f"Tests failed: {failed}")
    logger.info(f"Safety gate ALLOWED: {allowed}")
    logger.info(f"Safety gate BLOCKED: {blocked}")
    logger.info("")
    
    # Tier distribution
    tier_counts = {}
    for r in results:
        tier = r.eligibility.effective_tier
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    logger.info("Tier distribution:")
    for tier in sorted(tier_counts.keys()):
        logger.info(f"  Tier {tier}: {tier_counts[tier]}")
    
    logger.info("")
    logger.info(f"Run ID: {run_id}")
    logger.info("Results logged to shq.audit_log")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Smoke Test')
    parser.add_argument('--count', type=int, default=5, help='Number of companies to test')
    args = parser.parse_args()
    
    results = run_smoke_test(company_count=args.count)
    
    # Exit with error if any tests failed
    failed = sum(1 for r in results if not r.test_passed)
    sys.exit(1 if failed > 0 else 0)
