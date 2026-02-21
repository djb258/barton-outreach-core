#!/usr/bin/env python3
"""
BIT Batch Scoring Engine
========================

Batch processes all companies to generate BIT scores from existing signal sources.

Signal Sources:
- DOL: filing_present=True → +5 (form_5500_filed)
- Blog: Each blog record → +5 (content_signal) 
- People: slot_type filled → +10 (slot_filled) [future, currently empty]
- Talent Flow: [future, not implemented]

Tier Mapping (per Doctrine):
- COLD: score < 25
- WARM: 25 <= score < 50  
- HOT: 50 <= score < 75
- BURNING: score >= 75

For Tier 3 eligibility: BIT score >= 50 (HOT or BURNING)

Usage:
    python ops/schedulers/bit_batch_score.py [--dry-run]
"""

import argparse
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bit_batch_score')

# ============================================================================
# SIGNAL IMPACT VALUES (per PRD v2.1)
# ============================================================================
SIGNAL_IMPACTS = {
    # DOL signals
    'form_5500_filed': Decimal('5.0'),
    'large_plan': Decimal('8.0'),
    'broker_change': Decimal('7.0'),
    
    # Blog signals
    'content_signal': Decimal('5.0'),
    'funding_event': Decimal('15.0'),
    'acquisition': Decimal('12.0'),
    'leadership_change': Decimal('8.0'),
    
    # People signals
    'slot_filled': Decimal('10.0'),
    'email_verified': Decimal('3.0'),
    
    # Talent Flow signals  
    'executive_joined': Decimal('10.0'),
    'movement_detected': Decimal('7.0'),
}

# Tier thresholds
TIER_THRESHOLDS = {
    'COLD': Decimal('0'),
    'WARM': Decimal('25'),
    'HOT': Decimal('50'),
    'BURNING': Decimal('75'),
}


def get_tier(score: Decimal) -> str:
    """Determine BIT tier from score."""
    if score >= TIER_THRESHOLDS['BURNING']:
        return 'BURNING'
    elif score >= TIER_THRESHOLDS['HOT']:
        return 'HOT'
    elif score >= TIER_THRESHOLDS['WARM']:
        return 'WARM'
    else:
        return 'COLD'


def get_db_connection():
    """Get database connection.
    
    Uses environment variables if available (for CI/CD), 
    falls back to hardcoded values for local development.
    """
    import os
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=5432,
        database=os.getenv('NEON_DATABASE', 'Marketing DB'),
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )


def batch_score_companies(dry_run: bool = False) -> dict:
    """
    Batch score all companies with signals.
    
    Process:
    1. Aggregate signals from DOL, Blog tables by outreach_id
    2. Calculate total score and component scores
    3. Determine tier
    4. Upsert to bit_scores table
    
    Args:
        dry_run: If True, don't commit changes
        
    Returns:
        Statistics dict
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    stats = {
        'companies_processed': 0,
        'companies_updated': 0,
        'companies_created': 0,
        'signals_counted': 0,
        'tier_distribution': {'COLD': 0, 'WARM': 0, 'HOT': 0, 'BURNING': 0},
        'companies_tier3_eligible': 0,  # BIT >= 50
        'stale_companies': 0,  # No signals in 30+ days
        'errors': [],
    }
    
    logger.info("Starting BIT batch scoring...")
    
    try:
        # ====================================================================
        # STEP 1: Calculate scores from signal sources
        # ====================================================================
        
        # DOL signals: Each filing_present=True → +5 per company
        logger.info("Aggregating DOL signals...")
        cur.execute("""
            SELECT 
                ct.outreach_id,
                ct.company_unique_id,
                COUNT(d.dol_id) as dol_signal_count,
                COALESCE(SUM(CASE WHEN d.filing_present THEN %s ELSE 0 END), 0) as dol_score,
                MAX(d.updated_at) as dol_last_signal_at
            FROM outreach.company_target ct
            LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
            WHERE ct.company_unique_id IS NOT NULL
            GROUP BY ct.outreach_id, ct.company_unique_id
        """, (SIGNAL_IMPACTS['form_5500_filed'],))
        dol_scores = {r['outreach_id']: r for r in cur.fetchall()}
        logger.info(f"  Found {len([d for d in dol_scores.values() if d['dol_score'] > 0])} companies with DOL signals")
        
        # Blog signals: Each blog record → +5 per company
        # Note: Blog uses outreach_id directly
        logger.info("Aggregating Blog signals...")
        cur.execute("""
            SELECT 
                ct.outreach_id,
                COUNT(b.blog_id) as blog_signal_count,
                COALESCE(COUNT(b.blog_id) * %s, 0) as blog_score,
                MAX(COALESCE(b.context_timestamp, b.created_at)) as blog_last_signal_at
            FROM outreach.company_target ct
            LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
            WHERE ct.company_unique_id IS NOT NULL
            GROUP BY ct.outreach_id
        """, (SIGNAL_IMPACTS['content_signal'],))
        blog_scores = {r['outreach_id']: r for r in cur.fetchall()}
        logger.info(f"  Found {len([b for b in blog_scores.values() if b['blog_score'] > 0])} companies with Blog signals")
        
        # People signals (future - currently 0 records)
        logger.info("Aggregating People signals...")
        cur.execute("""
            SELECT 
                ct.outreach_id,
                COUNT(p.person_id) as people_signal_count,
                COALESCE(COUNT(p.person_id) * %s, 0) as people_score,
                MAX(p.updated_at) as people_last_signal_at
            FROM outreach.company_target ct
            LEFT JOIN outreach.people p ON p.outreach_id = ct.outreach_id
            WHERE ct.company_unique_id IS NOT NULL
            GROUP BY ct.outreach_id
        """, (SIGNAL_IMPACTS['slot_filled'],))
        people_scores = {r['outreach_id']: r for r in cur.fetchall()}
        people_with_signals = len([p for p in people_scores.values() if p['people_score'] > 0])
        logger.info(f"  Found {people_with_signals} companies with People signals")
        
        # ====================================================================
        # STEP 2: Combine scores and upsert to bit_scores
        # ====================================================================
        
        logger.info("Calculating combined scores...")
        
        # Get all outreach_ids from company_target
        all_outreach_ids = set(dol_scores.keys()) | set(blog_scores.keys()) | set(people_scores.keys())
        
        # Staleness threshold: 30 days
        from datetime import timedelta
        stale_threshold = datetime.now() - timedelta(days=30)
        
        batch_data = []
        for outreach_id in all_outreach_ids:
            dol_data = dol_scores.get(outreach_id, {'dol_score': Decimal('0'), 'dol_signal_count': 0, 'dol_last_signal_at': None})
            blog_data = blog_scores.get(outreach_id, {'blog_score': Decimal('0'), 'blog_signal_count': 0, 'blog_last_signal_at': None})
            people_data = people_scores.get(outreach_id, {'people_score': Decimal('0'), 'people_signal_count': 0, 'people_last_signal_at': None})
            
            dol_score = Decimal(str(dol_data['dol_score']))
            blog_score = Decimal(str(blog_data['blog_score']))
            people_score = Decimal(str(people_data['people_score']))
            talent_flow_score = Decimal('0')  # Not implemented yet
            
            total_score = dol_score + blog_score + people_score + talent_flow_score
            signal_count = (
                dol_data['dol_signal_count'] + 
                blog_data['blog_signal_count'] + 
                people_data['people_signal_count']
            )
            
            # Determine last signal timestamp (most recent across all sources)
            signal_timestamps = [
                dol_data.get('dol_last_signal_at'),
                blog_data.get('blog_last_signal_at'),
                people_data.get('people_last_signal_at'),
            ]
            valid_timestamps = [t for t in signal_timestamps if t is not None]
            last_signal_at = max(valid_timestamps) if valid_timestamps else None
            
            # Only process companies with at least one signal
            if total_score > 0:
                tier = get_tier(total_score)
                stats['tier_distribution'][tier] += 1
                stats['signals_counted'] += signal_count
                
                if total_score >= TIER_THRESHOLDS['HOT']:
                    stats['companies_tier3_eligible'] += 1
                
                # Track stale companies (no signals in 30+ days)
                if last_signal_at and last_signal_at.replace(tzinfo=None) < stale_threshold:
                    stats['stale_companies'] += 1
                
                batch_data.append({
                    'outreach_id': outreach_id,
                    'score': total_score,
                    'score_tier': tier,
                    'signal_count': signal_count,
                    'people_score': people_score,
                    'dol_score': dol_score,
                    'blog_score': blog_score,
                    'talent_flow_score': talent_flow_score,
                    'last_signal_at': last_signal_at,
                })
        
        stats['companies_processed'] = len(batch_data)
        logger.info(f"Prepared {len(batch_data)} companies for scoring")
        
        # ====================================================================
        # STEP 3: Upsert to bit_scores
        # ====================================================================
        
        if not dry_run and batch_data:
            logger.info("Upserting to outreach.bit_scores...")
            
            upsert_sql = """
                INSERT INTO outreach.bit_scores (
                    outreach_id, score, score_tier, signal_count,
                    people_score, dol_score, blog_score, talent_flow_score,
                    last_signal_at, last_scored_at, created_at, updated_at
                ) VALUES (
                    %(outreach_id)s, %(score)s, %(score_tier)s, %(signal_count)s,
                    %(people_score)s, %(dol_score)s, %(blog_score)s, %(talent_flow_score)s,
                    %(last_signal_at)s, NOW(), NOW(), NOW()
                )
                ON CONFLICT (outreach_id) DO UPDATE SET
                    score = EXCLUDED.score,
                    score_tier = EXCLUDED.score_tier,
                    signal_count = EXCLUDED.signal_count,
                    people_score = EXCLUDED.people_score,
                    dol_score = EXCLUDED.dol_score,
                    blog_score = EXCLUDED.blog_score,
                    talent_flow_score = EXCLUDED.talent_flow_score,
                    last_signal_at = EXCLUDED.last_signal_at,
                    last_scored_at = NOW(),
                    updated_at = NOW()
            """
            
            execute_batch(cur, upsert_sql, batch_data, page_size=1000)
            conn.commit()
            
            stats['companies_updated'] = len(batch_data)
            logger.info(f"Upserted {len(batch_data)} bit_scores")
        
        # ====================================================================
        # STEP 4: Update bit_score_snapshot in company_target
        # ====================================================================
        
        if not dry_run and batch_data:
            logger.info("Updating bit_score_snapshot in company_target...")
            
            update_snapshot_sql = """
                UPDATE outreach.company_target ct
                SET bit_score_snapshot = bs.score::integer
                FROM outreach.bit_scores bs
                WHERE ct.outreach_id = bs.outreach_id
            """
            cur.execute(update_snapshot_sql)
            conn.commit()
            logger.info("Updated bit_score_snapshot values")
        
    except Exception as e:
        logger.error(f"Error during batch scoring: {e}")
        stats['errors'].append(str(e))
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='BIT Batch Scoring Engine')
    parser.add_argument('--dry-run', action='store_true', help='Run without committing changes')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("BIT BATCH SCORING ENGINE")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("*** DRY RUN MODE - No changes will be committed ***")
    
    try:
        stats = batch_score_companies(dry_run=args.dry_run)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Companies processed: {stats['companies_processed']}")
        logger.info(f"Companies updated: {stats['companies_updated']}")
        logger.info(f"Total signals counted: {stats['signals_counted']}")
        logger.info("")
        logger.info("Tier Distribution:")
        for tier, count in stats['tier_distribution'].items():
            logger.info(f"  {tier}: {count}")
        logger.info("")
        logger.info(f"Companies eligible for Tier 3 (BIT >= 50): {stats['companies_tier3_eligible']}")
        logger.info(f"Companies with stale signals (30+ days): {stats['stale_companies']}")
        
        if stats['errors']:
            logger.error(f"Errors encountered: {len(stats['errors'])}")
            for err in stats['errors']:
                logger.error(f"  - {err}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
