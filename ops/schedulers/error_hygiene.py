#!/usr/bin/env python3
"""
Error Hygiene & Auto-Resolution Scheduler
==========================================

DOCTRINE: Errors must be actively managed, not left to rot.

This scheduler handles:
1. Auto-tombstone permanent errors >30 days old
2. Enforce retry guard (max 3 requeue attempts)
3. Alert on >5 actionable errors in 1 hour
4. Escalate UNKNOWN errors after 24h
5. All actions logged to audit_log

THRESHOLDS (configurable):
- TOMBSTONE_DAYS = 30 (errors older than this are auto-tombstoned)
- MAX_REQUEUE_ATTEMPTS = 3 (prevent infinite retries)
- ALERT_THRESHOLD = 5 (errors in 1 hour triggers alert)
- UNKNOWN_ESCALATION_HOURS = 24 (UNKNOWN errors escalated after this)

Usage:
    python ops/schedulers/error_hygiene.py [--dry-run]
"""

import argparse
import logging
import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('error_hygiene')

# ============================================================================
# THRESHOLDS (all configurable)
# ============================================================================

# Auto-tombstone errors older than this (days)
TOMBSTONE_DAYS = 30

# Maximum requeue attempts before permanent failure
MAX_REQUEUE_ATTEMPTS = 3

# Alert if more than this many actionable errors in 1 hour
ALERT_THRESHOLD = 5

# Escalate UNKNOWN errors after this many hours
UNKNOWN_ESCALATION_HOURS = 24

# Error tables to process
ERROR_TABLES = [
    'outreach.company_target_errors',
    'outreach.dol_errors',
    'outreach.people_errors',
    'outreach.blog_errors',
    'outreach.bit_errors',
    'outreach.outreach_errors',
]


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=5432,
        database=os.getenv('NEON_DATABASE', 'Marketing DB'),
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def log_to_audit(
    cur, 
    component: str, 
    event_type: str, 
    event_data: Dict[str, Any]
) -> None:
    """
    Log action to shq.audit_log.
    
    All error hygiene actions MUST be logged.
    
    Schema: id, event_type, event_source, details, created_at
    """
    try:
        cur.execute("""
            INSERT INTO shq.audit_log (event_type, event_source, details, created_at)
            VALUES (%s, %s, %s::jsonb, NOW())
        """, (event_type, component, json.dumps(event_data, default=str)))
    except Exception as e:
        # Log failure but don't crash
        logger.warning(f"Failed to log to audit: {e}")


def task_1_tombstone_old_errors(cur, dry_run: bool) -> Dict[str, Any]:
    """
    Task 1: Auto-tombstone permanent errors >30 days old.
    
    Permanent errors = retry_allowed = false AND resolved_at IS NULL
    These errors will never be retried, so tombstone them after 30 days.
    
    Tombstoning = setting resolved_at and resolution_note to indicate auto-cleanup.
    
    Note: Only processes tables with both retry_allowed and resolved_at columns.
    """
    logger.info(f"Task 1: Tombstoning errors older than {TOMBSTONE_DAYS} days...")
    
    cutoff_date = datetime.now() - timedelta(days=TOMBSTONE_DAYS)
    stats = {'tables': {}, 'total_tombstoned': 0}
    
    for table in ERROR_TABLES:
        try:
            # Check if table has required columns
            schema, table_name = table.split('.')
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table_name))
            columns = [r['column_name'] for r in cur.fetchall()]
            
            # Skip tables without required columns
            if 'retry_allowed' not in columns or 'resolved_at' not in columns:
                logger.debug(f"  Skipping {table} - missing retry_allowed or resolved_at")
                continue
            
            # Count eligible errors
            cur.execute(f"""
                SELECT COUNT(*) as cnt FROM {table}
                WHERE retry_allowed = false
                AND resolved_at IS NULL
                AND created_at < %s
            """, (cutoff_date,))
            count = cur.fetchone()['cnt']
            
            if count > 0:
                if not dry_run:
                    # Tombstone old permanent errors
                    cur.execute(f"""
                        UPDATE {table}
                        SET resolved_at = NOW(),
                            resolution_note = 'Auto-tombstoned by error_hygiene after {TOMBSTONE_DAYS} days'
                        WHERE retry_allowed = false
                        AND resolved_at IS NULL
                        AND created_at < %s
                    """, (cutoff_date,))
                
                stats['tables'][table] = count
                stats['total_tombstoned'] += count
                logger.info(f"  {table}: {count} errors tombstoned")
                
                # Audit log
                if not dry_run:
                    log_to_audit(cur, 'error_hygiene', 'tombstone_old_errors', {
                        'table': table,
                        'count': count,
                        'cutoff_date': cutoff_date.isoformat(),
                        'threshold_days': TOMBSTONE_DAYS,
                    })
            else:
                logger.debug(f"  {table}: 0 errors to tombstone")
                
        except Exception as e:
            logger.warning(f"  {table}: Error - {e}")
            # Rollback for this table's transaction issue
            try:
                cur.connection.rollback()
            except:
                pass
    
    return stats


def task_2_enforce_retry_guard(cur, dry_run: bool) -> Dict[str, Any]:
    """
    Task 2: Enforce retry guard (max 3 requeue attempts).
    
    If an error has been requeued more than MAX_REQUEUE_ATTEMPTS times,
    mark it as permanent failure (retry_allowed = false).
    
    Note: This requires tracking requeue_attempts. If the column doesn't exist,
    we add it. Tables without retry_allowed or resolved_at are skipped.
    """
    logger.info(f"Task 2: Enforcing retry guard (max {MAX_REQUEUE_ATTEMPTS} attempts)...")
    
    stats = {'tables': {}, 'total_blocked': 0}
    
    for table in ERROR_TABLES:
        try:
            schema, table_name = table.split('.')
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table_name))
            columns = [r['column_name'] for r in cur.fetchall()]
            
            # Skip tables without retry_allowed or resolved_at
            if 'retry_allowed' not in columns or 'resolved_at' not in columns:
                logger.debug(f"  Skipping {table} - missing retry_allowed or resolved_at")
                continue
            
            # Add requeue_attempts column if it doesn't exist
            if 'requeue_attempts' not in columns:
                if not dry_run:
                    try:
                        cur.execute(f"""
                            ALTER TABLE {table}
                            ADD COLUMN IF NOT EXISTS requeue_attempts INTEGER DEFAULT 0
                        """)
                        cur.connection.commit()
                        logger.info(f"  {table}: Added requeue_attempts column")
                    except Exception as e:
                        logger.warning(f"  {table}: Could not add column - {e}")
                        cur.connection.rollback()
                        continue
                else:
                    logger.info(f"  {table}: Would add requeue_attempts column")
                    continue
            
            # Find errors exceeding retry limit
            cur.execute(f"""
                SELECT COUNT(*) as cnt FROM {table}
                WHERE requeue_attempts >= %s
                AND retry_allowed = true
                AND resolved_at IS NULL
            """, (MAX_REQUEUE_ATTEMPTS,))
            count = cur.fetchone()['cnt']
            
            if count > 0:
                if not dry_run:
                    # Block further retries
                    cur.execute(f"""
                        UPDATE {table}
                        SET retry_allowed = false,
                            resolution_note = COALESCE(resolution_note || ' | ', '') || 
                                'Retry guard: exceeded {MAX_REQUEUE_ATTEMPTS} attempts'
                        WHERE requeue_attempts >= %s
                        AND retry_allowed = true
                        AND resolved_at IS NULL
                    """, (MAX_REQUEUE_ATTEMPTS,))
                
                stats['tables'][table] = count
                stats['total_blocked'] += count
                logger.info(f"  {table}: {count} errors blocked (exceeded retry limit)")
                
                # Audit log
                if not dry_run:
                    log_to_audit(cur, 'error_hygiene', 'retry_guard_block', {
                        'table': table,
                        'count': count,
                        'max_attempts': MAX_REQUEUE_ATTEMPTS,
                    })
            else:
                logger.debug(f"  {table}: 0 errors exceeding retry limit")
                
        except Exception as e:
            logger.warning(f"  {table}: Error - {e}")
            try:
                cur.connection.rollback()
            except:
                pass
    
    return stats


def task_3_alert_on_error_spike(cur, dry_run: bool) -> Dict[str, Any]:
    """
    Task 3: Alert if >5 actionable errors in 1 hour.
    
    Actionable errors = unresolved AND retry_allowed = true
    This indicates a systemic issue that needs attention.
    
    Note: Tables without resolved_at just check retry_allowed.
    """
    logger.info(f"Task 3: Checking for error spikes (>{ALERT_THRESHOLD} in 1 hour)...")
    
    one_hour_ago = datetime.now() - timedelta(hours=1)
    stats = {'alerts': [], 'total_actionable': 0}
    
    for table in ERROR_TABLES:
        try:
            schema, table_name = table.split('.')
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table_name))
            columns = [r['column_name'] for r in cur.fetchall()]
            
            if 'created_at' not in columns:
                continue
            
            # Build query based on available columns
            has_retry = 'retry_allowed' in columns
            has_resolved = 'resolved_at' in columns
            
            if has_retry and has_resolved:
                query = f"""
                    SELECT COUNT(*) as cnt FROM {table}
                    WHERE retry_allowed = true
                    AND resolved_at IS NULL
                    AND created_at >= %s
                """
            elif has_retry:
                query = f"""
                    SELECT COUNT(*) as cnt FROM {table}
                    WHERE retry_allowed = true
                    AND created_at >= %s
                """
            else:
                # Just count errors in time window
                query = f"""
                    SELECT COUNT(*) as cnt FROM {table}
                    WHERE created_at >= %s
                """
            
            cur.execute(query, (one_hour_ago,))
            count = cur.fetchone()['cnt']
            
            stats['total_actionable'] += count
            
            if count > ALERT_THRESHOLD:
                alert = {
                    'table': table,
                    'count': count,
                    'threshold': ALERT_THRESHOLD,
                    'time_window': '1 hour',
                    'severity': 'HIGH' if count > ALERT_THRESHOLD * 2 else 'MEDIUM',
                }
                stats['alerts'].append(alert)
                logger.warning(f"  🚨 ALERT: {table} has {count} actionable errors in last hour!")
                
                # Audit log
                if not dry_run:
                    log_to_audit(cur, 'error_hygiene', 'error_spike_alert', alert)
            else:
                logger.debug(f"  {table}: {count} actionable errors (under threshold)")
                
        except Exception as e:
            logger.warning(f"  {table}: Error - {e}")
            try:
                cur.connection.rollback()
            except:
                pass
    
    if stats['alerts']:
        logger.warning(f"  TOTAL ALERTS: {len(stats['alerts'])}")
    else:
        logger.info("  No error spikes detected")
    
    return stats


def task_4_escalate_unknown_errors(cur, dry_run: bool) -> Dict[str, Any]:
    """
    Task 4: Escalate UNKNOWN errors after 24h.
    
    UNKNOWN errors should not persist. If they exist after 24h,
    escalate them by logging to audit and marking for review.
    
    Note: Tables without resolved_at just check created_at age.
    """
    logger.info(f"Task 4: Checking for stale UNKNOWN errors (>{UNKNOWN_ESCALATION_HOURS}h)...")
    
    escalation_cutoff = datetime.now() - timedelta(hours=UNKNOWN_ESCALATION_HOURS)
    stats = {'tables': {}, 'total_escalated': 0}
    
    for table in ERROR_TABLES:
        try:
            schema, table_name = table.split('.')
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s
            """, (schema, table_name))
            columns = [r['column_name'] for r in cur.fetchall()]
            
            # Determine code column
            if 'failure_code' in columns:
                code_column = 'failure_code'
            elif 'error_type' in columns:
                code_column = 'error_type'
            else:
                logger.debug(f"  Skipping {table} - no failure_code or error_type")
                continue
            
            has_resolved = 'resolved_at' in columns
            has_resolution_note = 'resolution_note' in columns
            
            # Build query based on available columns
            if has_resolved:
                query = f"""
                    SELECT error_id, {code_column}, created_at
                    FROM {table}
                    WHERE ({code_column} LIKE '%%UNKNOWN%%' OR {code_column} = 'UNKNOWN')
                    AND resolved_at IS NULL
                    AND created_at < %s
                    LIMIT 100
                """
            else:
                query = f"""
                    SELECT error_id, {code_column}, created_at
                    FROM {table}
                    WHERE ({code_column} LIKE '%%UNKNOWN%%' OR {code_column} = 'UNKNOWN')
                    AND created_at < %s
                    LIMIT 100
                """
            
            cur.execute(query, (escalation_cutoff,))
            unknown_errors = cur.fetchall()
            
            count = len(unknown_errors)
            if count > 0:
                stats['tables'][table] = count
                stats['total_escalated'] += count
                logger.warning(f"  ⚠️  {table}: {count} UNKNOWN errors need review")
                
                # Mark for escalation (if resolution_note exists)
                if not dry_run and has_resolution_note:
                    error_ids = [r['error_id'] for r in unknown_errors]
                    cur.execute(f"""
                        UPDATE {table}
                        SET resolution_note = COALESCE(resolution_note || ' | ', '') || 
                            'ESCALATED: UNKNOWN error persisted >{UNKNOWN_ESCALATION_HOURS}h - requires manual review'
                        WHERE error_id = ANY(%s)
                    """, (error_ids,))
                    
                    # Audit log
                    log_to_audit(cur, 'error_hygiene', 'unknown_error_escalation', {
                        'table': table,
                        'count': count,
                        'error_ids': [str(e) for e in error_ids[:10]],  # First 10 for audit
                        'threshold_hours': UNKNOWN_ESCALATION_HOURS,
                    })
                elif not dry_run:
                    # Audit log even if no update possible
                    log_to_audit(cur, 'error_hygiene', 'unknown_error_escalation', {
                        'table': table,
                        'count': count,
                        'threshold_hours': UNKNOWN_ESCALATION_HOURS,
                        'note': 'Table lacks resolution_note column - audit only',
                    })
            else:
                logger.debug(f"  {table}: No stale UNKNOWN errors")
                
        except Exception as e:
            logger.warning(f"  {table}: Error - {e}")
            try:
                cur.connection.rollback()
            except:
                pass
    
    if stats['total_escalated'] > 0:
        logger.warning(f"  TOTAL ESCALATED: {stats['total_escalated']}")
    else:
        logger.info("  No UNKNOWN errors requiring escalation")
    
    return stats


def run_error_hygiene(dry_run: bool = False) -> Dict[str, Any]:
    """
    Run all error hygiene tasks.
    
    All actions are logged to shq.audit_log.
    """
    results = {
        'run_id': str(uuid4()),
        'timestamp': datetime.now().isoformat(),
        'dry_run': dry_run,
        'tasks': {},
    }
    
    # Task 1: Tombstone old errors (fresh connection)
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        results['tasks']['tombstone'] = task_1_tombstone_old_errors(cur, dry_run)
        if not dry_run:
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Task 1 failed: {e}")
        results['tasks']['tombstone'] = {'error': str(e), 'total_tombstoned': 0, 'tables': {}}
    
    # Task 2: Enforce retry guard (fresh connection)
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        results['tasks']['retry_guard'] = task_2_enforce_retry_guard(cur, dry_run)
        if not dry_run:
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Task 2 failed: {e}")
        results['tasks']['retry_guard'] = {'error': str(e), 'total_blocked': 0, 'tables': {}}
    
    # Task 3: Alert on error spikes (fresh connection)
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        results['tasks']['alert'] = task_3_alert_on_error_spike(cur, dry_run)
        if not dry_run:
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Task 3 failed: {e}")
        results['tasks']['alert'] = {'error': str(e), 'alerts': [], 'alert_triggered': False}
    
    # Task 4: Escalate UNKNOWN errors (fresh connection)
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        results['tasks']['unknown_escalation'] = task_4_escalate_unknown_errors(cur, dry_run)
        if not dry_run:
            conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Task 4 failed: {e}")
        results['tasks']['unknown_escalation'] = {'error': str(e), 'total_escalated': 0, 'tables': {}}
    
    # Log run completion to audit (fresh connection)
    if not dry_run:
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            log_to_audit(cur, 'error_hygiene', 'run_complete', {
                'run_id': results['run_id'],
                'tombstoned': results['tasks']['tombstone'].get('total_tombstoned', 0),
                'retry_blocked': results['tasks']['retry_guard'].get('total_blocked', 0),
                'alerts': len(results['tasks']['alert'].get('alerts', [])),
                'escalated': results['tasks']['unknown_escalation'].get('total_escalated', 0),
            })
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log run completion: {e}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Error Hygiene & Auto-Resolution')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ERROR HYGIENE & AUTO-RESOLUTION")
    logger.info("=" * 60)
    logger.info(f"Thresholds:")
    logger.info(f"  TOMBSTONE_DAYS: {TOMBSTONE_DAYS}")
    logger.info(f"  MAX_REQUEUE_ATTEMPTS: {MAX_REQUEUE_ATTEMPTS}")
    logger.info(f"  ALERT_THRESHOLD: {ALERT_THRESHOLD} errors/hour")
    logger.info(f"  UNKNOWN_ESCALATION_HOURS: {UNKNOWN_ESCALATION_HOURS}")
    logger.info("")
    
    if args.dry_run:
        logger.info("*** DRY RUN MODE - No changes will be committed ***")
        logger.info("")
    
    try:
        results = run_error_hygiene(dry_run=args.dry_run)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Run ID: {results['run_id']}")
        logger.info(f"Errors tombstoned: {results['tasks']['tombstone']['total_tombstoned']}")
        logger.info(f"Errors blocked (retry limit): {results['tasks']['retry_guard']['total_blocked']}")
        logger.info(f"Alerts triggered: {len(results['tasks']['alert']['alerts'])}")
        logger.info(f"UNKNOWN errors escalated: {results['tasks']['unknown_escalation']['total_escalated']}")
        
        # Return error code if alerts were triggered
        if results['tasks']['alert']['alerts']:
            return 1
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
