#!/usr/bin/env python3
"""
Completeness Evaluator Script
=============================

Evaluates entity completeness across all sub-hubs based on TAS_COMPLETENESS_CONTRACT.md rules.

IMPORTANT:
- This script is READ-HEAVY, WRITE-MINIMAL
- Only writes to outreach.company_hub_status (status tracking table)
- NEVER mutates source data tables
- Idempotent: safe to re-run

Usage:
    python evaluate_completeness.py [--dry-run] [--entity-id <id>] [--hub <hub_id>]

Output:
    Structured JSON logs to stdout
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# Attempt psycopg2 import - graceful fallback for dry-run
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


# =============================================================================
# ENUM DEFINITIONS (Must match database blocker_type_enum)
# =============================================================================

class BlockerType(Enum):
    DATA_MISSING = "DATA_MISSING"
    DATA_UNDISCOVERABLE = "DATA_UNDISCOVERABLE"
    DATA_CONFLICT = "DATA_CONFLICT"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    UPSTREAM_BLOCKED = "UPSTREAM_BLOCKED"
    THRESHOLD_NOT_MET = "THRESHOLD_NOT_MET"
    EXPIRED = "EXPIRED"


class HubStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


# =============================================================================
# HUB DEFINITIONS (From TAS_COMPLETENESS_CONTRACT.md)
# =============================================================================

HUB_DEFINITIONS = {
    "company-target": {
        "waterfall_order": 1,
        "gates_completion": True,
        "upstream_hub": None,
        "evaluate": lambda data: evaluate_company_target(data),
    },
    "dol-filings": {
        "waterfall_order": 2,
        "gates_completion": True,
        "upstream_hub": "company-target",
        "evaluate": lambda data: evaluate_dol_filings(data),
    },
    "people-intelligence": {
        "waterfall_order": 3,
        "gates_completion": True,
        "upstream_hub": "dol-filings",
        "evaluate": lambda data: evaluate_people_intelligence(data),
    },
    "talent-flow": {
        "waterfall_order": 4,
        "gates_completion": True,
        "upstream_hub": "people-intelligence",
        "evaluate": lambda data: evaluate_talent_flow(data),
    },
    "blog-content": {
        "waterfall_order": 5,
        "gates_completion": False,
        "upstream_hub": "talent-flow",
        "evaluate": lambda data: evaluate_blog_content(data),
    },
    "outreach-execution": {
        "waterfall_order": 6,
        "gates_completion": False,
        "upstream_hub": "talent-flow",
        "evaluate": lambda data: evaluate_outreach_execution(data),
    },
}


# =============================================================================
# EVALUATION RESULT
# =============================================================================

@dataclass
class EvaluationResult:
    entity_id: str
    hub_id: str
    status: HubStatus
    blocker_type: Optional[BlockerType]
    blocker_evidence: Optional[Dict[str, Any]]
    metric_value: Optional[float]
    evaluated_at: str

    def to_log(self) -> Dict[str, Any]:
        return {
            "timestamp": self.evaluated_at,
            "entity_id": self.entity_id,
            "hub_id": self.hub_id,
            "status": self.status.value,
            "blocker_type": self.blocker_type.value if self.blocker_type else None,
            "blocker_evidence": self.blocker_evidence,
            "metric_value": self.metric_value,
        }


# =============================================================================
# HUB EVALUATION FUNCTIONS
# Per TAS_COMPLETENESS_CONTRACT.md Section: Per-Hub Completeness Rules
# =============================================================================

def evaluate_company_target(data: Dict[str, Any]) -> EvaluationResult:
    """
    Company Target (04.04.01): Complete when email_method IS NOT NULL AND confidence_score >= 0.5
    """
    entity_id = data.get("outreach_id")
    email_method = data.get("email_method")
    confidence_score = data.get("confidence_score", 0)

    if email_method is None:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="company-target",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.DATA_MISSING,
            blocker_evidence={"missing_fields": ["email_method"]},
            metric_value=confidence_score,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    if confidence_score is None or confidence_score < 0.5:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="company-target",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.THRESHOLD_NOT_MET,
            blocker_evidence={
                "metric_name": "confidence_score",
                "actual_value": confidence_score,
                "required_value": 0.5,
            },
            metric_value=confidence_score,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="company-target",
        status=HubStatus.PASS,
        blocker_type=None,
        blocker_evidence=None,
        metric_value=confidence_score,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_dol_filings(data: Dict[str, Any]) -> EvaluationResult:
    """
    DOL Filings (04.04.03): Complete when form_5500_matched = true OR NOT_APPLICABLE
    """
    entity_id = data.get("outreach_id")
    form_5500_matched = data.get("form_5500_matched", False)
    ein_resolved = data.get("ein_resolved", False)
    employee_count = data.get("employee_count", 0)

    # Companies with < 100 employees typically don't file Form 5500
    if employee_count and employee_count < 100:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="dol-filings",
            status=HubStatus.BLOCKED,
            blocker_type=BlockerType.NOT_APPLICABLE,
            blocker_evidence={"reason": "Company has < 100 employees, Form 5500 not required"},
            metric_value=None,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    if not ein_resolved:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="dol-filings",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.DATA_MISSING,
            blocker_evidence={"missing_fields": ["ein"]},
            metric_value=None,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    if not form_5500_matched:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="dol-filings",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.DATA_UNDISCOVERABLE,
            blocker_evidence={
                "checked_sources": ["dol_form_5500_database"],
                "last_attempt_at": datetime.now(timezone.utc).isoformat(),
            },
            metric_value=0,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="dol-filings",
        status=HubStatus.PASS,
        blocker_type=None,
        blocker_evidence=None,
        metric_value=1.0,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_people_intelligence(data: Dict[str, Any]) -> EvaluationResult:
    """
    People Intelligence (04.04.02): Complete when slot_fill_rate >= metric_critical_threshold
    """
    entity_id = data.get("outreach_id")
    slot_fill_rate = data.get("slot_fill_rate", 0)
    threshold = data.get("metric_critical_threshold", 0.5)

    if slot_fill_rate is None:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="people-intelligence",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.DATA_MISSING,
            blocker_evidence={"missing_fields": ["slot_assignments"]},
            metric_value=0,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    if slot_fill_rate < threshold:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="people-intelligence",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.THRESHOLD_NOT_MET,
            blocker_evidence={
                "metric_name": "slot_fill_rate",
                "actual_value": slot_fill_rate,
                "required_value": threshold,
            },
            metric_value=slot_fill_rate,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="people-intelligence",
        status=HubStatus.PASS,
        blocker_type=None,
        blocker_evidence=None,
        metric_value=slot_fill_rate,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_talent_flow(data: Dict[str, Any]) -> EvaluationResult:
    """
    Talent Flow: Complete when movement_detection_rate >= threshold OR age < 90 days
    """
    entity_id = data.get("outreach_id")
    movement_detection_rate = data.get("movement_detection_rate", 0)
    data_age_days = data.get("data_age_days", 0)
    threshold = data.get("metric_critical_threshold", 0.1)

    # Fresh data passes
    if data_age_days and data_age_days < 90:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="talent-flow",
            status=HubStatus.PASS,
            blocker_type=None,
            blocker_evidence=None,
            metric_value=movement_detection_rate,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    if movement_detection_rate >= threshold:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="talent-flow",
            status=HubStatus.PASS,
            blocker_type=None,
            blocker_evidence=None,
            metric_value=movement_detection_rate,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    # Stale data with no movements
    if data_age_days and data_age_days >= 90:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="talent-flow",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.EXPIRED,
            blocker_evidence={
                "data_timestamp": data.get("last_enriched_at"),
                "freshness_window_days": 90,
            },
            metric_value=movement_detection_rate,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="talent-flow",
        status=HubStatus.FAIL,
        blocker_type=BlockerType.THRESHOLD_NOT_MET,
        blocker_evidence={
            "metric_name": "movement_detection_rate",
            "actual_value": movement_detection_rate,
            "required_value": threshold,
        },
        metric_value=movement_detection_rate,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_blog_content(data: Dict[str, Any]) -> EvaluationResult:
    """
    Blog Content (04.04.05): Complete when signal_count >= 1
    """
    entity_id = data.get("outreach_id")
    signal_count = data.get("signal_count", 0)

    if signal_count is None or signal_count < 1:
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="blog-content",
            status=HubStatus.FAIL,
            blocker_type=BlockerType.DATA_UNDISCOVERABLE,
            blocker_evidence={
                "checked_sources": ["blog_discovery", "news_api"],
                "last_attempt_at": datetime.now(timezone.utc).isoformat(),
            },
            metric_value=signal_count or 0,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="blog-content",
        status=HubStatus.PASS,
        blocker_type=None,
        blocker_evidence=None,
        metric_value=signal_count,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_outreach_execution(data: Dict[str, Any]) -> EvaluationResult:
    """
    Outreach Execution (04.04.04): Complete when campaign_status IN ('active', 'completed')
    """
    entity_id = data.get("outreach_id")
    campaign_status = data.get("campaign_status")

    if campaign_status in ("active", "completed"):
        return EvaluationResult(
            entity_id=entity_id,
            hub_id="outreach-execution",
            status=HubStatus.PASS,
            blocker_type=None,
            blocker_evidence=None,
            metric_value=1.0,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return EvaluationResult(
        entity_id=entity_id,
        hub_id="outreach-execution",
        status=HubStatus.FAIL,
        blocker_type=BlockerType.DATA_MISSING,
        blocker_evidence={"missing_fields": ["campaign_status"], "current_value": campaign_status},
        metric_value=0,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


# =============================================================================
# WATERFALL EVALUATION
# =============================================================================

def check_upstream_status(conn, entity_id: str, hub_id: str) -> Optional[EvaluationResult]:
    """
    Check if upstream hub is PASS. If not, return UPSTREAM_BLOCKED result.
    """
    hub_def = HUB_DEFINITIONS.get(hub_id)
    if not hub_def or not hub_def["upstream_hub"]:
        return None  # No upstream dependency

    upstream_hub = hub_def["upstream_hub"]

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT status FROM outreach.company_hub_status
            WHERE company_unique_id = %s AND hub_id = %s
        """, (entity_id, upstream_hub))
        row = cur.fetchone()

    if not row or row["status"] != "PASS":
        upstream_status = row["status"] if row else "NOT_EVALUATED"
        return EvaluationResult(
            entity_id=entity_id,
            hub_id=hub_id,
            status=HubStatus.BLOCKED,
            blocker_type=BlockerType.UPSTREAM_BLOCKED,
            blocker_evidence={
                "blocking_hub": upstream_hub,
                "blocking_status": upstream_status,
            },
            metric_value=None,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    return None  # Upstream is PASS, proceed with evaluation


# =============================================================================
# DATA FETCHING
# =============================================================================

def fetch_entity_data(conn, entity_id: str, hub_id: str) -> Dict[str, Any]:
    """
    Fetch required data for evaluation from source tables.
    Uses outreach_id as the unifying key.
    """
    data = {"outreach_id": entity_id}

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if hub_id == "company-target":
            cur.execute("""
                SELECT email_method, confidence_score
                FROM outreach.company_target
                WHERE outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

        elif hub_id == "dol-filings":
            cur.execute("""
                SELECT
                    CASE WHEN dol.form_5500_id IS NOT NULL THEN true ELSE false END as form_5500_matched,
                    CASE WHEN dol.ein IS NOT NULL THEN true ELSE false END as ein_resolved,
                    ct.employee_count
                FROM outreach.outreach o
                LEFT JOIN outreach.dol dol ON dol.outreach_id = o.outreach_id
                LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
                WHERE o.outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

        elif hub_id == "people-intelligence":
            cur.execute("""
                SELECT
                    COALESCE(p.slot_fill_rate, 0) as slot_fill_rate,
                    hr.metric_critical_threshold
                FROM outreach.outreach o
                LEFT JOIN outreach.people p ON p.outreach_id = o.outreach_id
                LEFT JOIN outreach.hub_registry hr ON hr.hub_id = 'people-intelligence'
                WHERE o.outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

        elif hub_id == "talent-flow":
            cur.execute("""
                SELECT
                    COALESCE(movement_detection_rate, 0) as movement_detection_rate,
                    EXTRACT(DAY FROM NOW() - last_enriched_at) as data_age_days,
                    last_enriched_at
                FROM outreach.outreach o
                LEFT JOIN outreach.people p ON p.outreach_id = o.outreach_id
                WHERE o.outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

        elif hub_id == "blog-content":
            cur.execute("""
                SELECT COALESCE(signal_count, 0) as signal_count
                FROM outreach.blog
                WHERE outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

        elif hub_id == "outreach-execution":
            cur.execute("""
                SELECT campaign_status
                FROM outreach.outreach
                WHERE outreach_id = %s
            """, (entity_id,))
            row = cur.fetchone()
            if row:
                data.update(row)

    return data


# =============================================================================
# STATUS WRITER
# =============================================================================

def write_status(conn, result: EvaluationResult, dry_run: bool = False) -> None:
    """
    Write evaluation result to outreach.company_hub_status.
    ONLY writes to status tracking table - never to source data.
    """
    if dry_run:
        log_output("dry_run_skip", {"action": "write_status", "result": result.to_log()})
        return

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO outreach.company_hub_status (
                company_unique_id, hub_id, status, blocker_type,
                blocker_evidence, metric_value, last_processed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (company_unique_id, hub_id) DO UPDATE SET
                status = EXCLUDED.status,
                blocker_type = EXCLUDED.blocker_type,
                blocker_evidence = EXCLUDED.blocker_evidence,
                metric_value = EXCLUDED.metric_value,
                last_processed_at = EXCLUDED.last_processed_at,
                updated_at = NOW()
        """, (
            result.entity_id,
            result.hub_id,
            result.status.value,
            result.blocker_type.value if result.blocker_type else None,
            json.dumps(result.blocker_evidence) if result.blocker_evidence else None,
            result.metric_value,
            result.evaluated_at,
        ))
    conn.commit()


# =============================================================================
# LOGGING
# =============================================================================

def log_output(event: str, data: Dict[str, Any]) -> None:
    """Emit structured JSON log to stdout."""
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **data,
    }
    print(json.dumps(output))


# =============================================================================
# MAIN EVALUATION LOOP
# =============================================================================

def evaluate_entity(conn, entity_id: str, hub_id: Optional[str], dry_run: bool) -> List[EvaluationResult]:
    """
    Evaluate one entity across specified hub(s).
    Returns list of evaluation results.
    """
    results = []
    hubs_to_evaluate = [hub_id] if hub_id else list(HUB_DEFINITIONS.keys())

    # Sort by waterfall order
    hubs_to_evaluate.sort(key=lambda h: HUB_DEFINITIONS[h]["waterfall_order"])

    for hub in hubs_to_evaluate:
        log_output("evaluating", {"entity_id": entity_id, "hub_id": hub})

        # Check upstream dependency first
        upstream_block = check_upstream_status(conn, entity_id, hub) if conn else None
        if upstream_block:
            results.append(upstream_block)
            write_status(conn, upstream_block, dry_run) if conn else None
            log_output("result", upstream_block.to_log())
            continue

        # Fetch data and evaluate
        data = fetch_entity_data(conn, entity_id, hub) if conn else {"outreach_id": entity_id}
        evaluator = HUB_DEFINITIONS[hub]["evaluate"]
        result = evaluator(data)

        results.append(result)
        if conn:
            write_status(conn, result, dry_run)
        log_output("result", result.to_log())

    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate entity completeness")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to database")
    parser.add_argument("--entity-id", help="Evaluate specific entity")
    parser.add_argument("--hub", help="Evaluate specific hub only")
    parser.add_argument("--limit", type=int, default=100, help="Limit entities to process")
    args = parser.parse_args()

    log_output("start", {
        "dry_run": args.dry_run,
        "entity_id": args.entity_id,
        "hub": args.hub,
        "limit": args.limit,
    })

    # Connect to database
    conn = None
    if HAS_PSYCOPG2 and not args.dry_run:
        try:
            conn = psycopg2.connect(
                host=os.environ.get("NEON_HOST"),
                database=os.environ.get("NEON_DATABASE"),
                user=os.environ.get("NEON_USER"),
                password=os.environ.get("NEON_PASSWORD"),
                sslmode="require",
            )
            log_output("connected", {"database": os.environ.get("NEON_DATABASE")})
        except Exception as e:
            log_output("connection_error", {"error": str(e)})
            sys.exit(1)
    else:
        log_output("no_database", {"reason": "dry_run or psycopg2 not available"})

    try:
        if args.entity_id:
            # Evaluate single entity
            evaluate_entity(conn, args.entity_id, args.hub, args.dry_run)
        elif conn:
            # Evaluate all entities
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT outreach_id FROM outreach.outreach
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (args.limit,))
                entities = [row["outreach_id"] for row in cur.fetchall()]

            log_output("entities_found", {"count": len(entities)})

            for entity_id in entities:
                evaluate_entity(conn, entity_id, args.hub, args.dry_run)
        else:
            log_output("error", {"message": "No entity_id provided and no database connection"})
            sys.exit(1)

    finally:
        if conn:
            conn.close()

    log_output("complete", {"status": "success"})


if __name__ == "__main__":
    main()
