"""
Agent Utilities - Shared functions for Garage 2.0 enrichment agents

Common functionality:
- Database connections
- Validation logic (same as state_duckdb_pipeline)
- Logging to agent_routing_log
- Cost tracking
- Record tagging

Date: 2025-11-18
"""

import os
import re
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neon PostgreSQL credentials
NEON_HOST = os.getenv('NEON_HOST')
NEON_USER = os.getenv('NEON_USER')
NEON_PASSWORD = os.getenv('NEON_PASSWORD')
NEON_DATABASE = os.getenv('NEON_DATABASE')
NEON_CONNECTION_STRING = f"postgresql://{NEON_USER}:{NEON_PASSWORD}@{NEON_HOST}/{NEON_DATABASE}"

# Agent costs (USD per record)
AGENT_COSTS = {
    'firecrawl': 0.05,
    'apify': 0.10,
    'abacus': 0.50,
    'claude': 1.00
}

def get_neon_connection():
    """Get Neon PostgreSQL connection."""
    return psycopg2.connect(NEON_CONNECTION_STRING)

def validate_company(company_record):
    """
    Validate company record using same logic as state_duckdb_pipeline.

    Good criteria:
    - company_name IS NOT NULL
    - website_url IS NOT NULL
    - website_url contains domain (has '.')

    Returns: (is_valid: bool, validation_errors: list)
    """
    errors = []

    company_name = company_record.get('company_name')
    website_url = company_record.get('website_url')

    if not company_name or company_name == '':
        errors.append('company_name_missing')

    if not website_url or website_url == '':
        errors.append('website_url_missing')
    elif '.' not in website_url:
        errors.append('website_url_invalid')

    return len(errors) == 0, errors

def validate_person(person_record):
    """
    Validate person record using same logic as state_duckdb_pipeline.

    Good criteria:
    - email matches regex: ^[^@]+@[^@]+\.[^@]+
    - title IS NOT NULL

    Returns: (is_valid: bool, validation_errors: list)
    """
    errors = []

    email = person_record.get('email')
    title = person_record.get('title')

    # Email validation
    email_regex = r'^[^@]+@[^@]+\.[^@]+'
    if not email or email == '' or not re.match(email_regex, email):
        errors.append('email_invalid')

    # Title validation
    if not title or title == '':
        errors.append('title_missing')

    return len(errors) == 0, errors

def log_agent_routing(
    garage_run_id,
    record_type,
    record_id,
    garage_bay,
    agent_name,
    routing_reason,
    missing_fields,
    contradictions,
    repair_attempt_number,
    is_chronic_bad,
    agent_status,
    agent_cost,
    fields_repaired=None,
    agent_started_at=None,
    agent_completed_at=None
):
    """
    Log agent routing decision to public.agent_routing_log.

    Args:
        garage_run_id: FK to garage_runs table
        record_type: 'person' or 'company'
        record_id: unique_id or company_unique_id
        garage_bay: 'bay_a' or 'bay_b'
        agent_name: 'firecrawl', 'apify', 'abacus', 'claude'
        routing_reason: Why this agent was chosen
        missing_fields: List of missing fields
        contradictions: List of contradictions
        repair_attempt_number: Current repair attempt
        is_chronic_bad: Boolean
        agent_status: 'pending', 'running', 'success', 'failed'
        agent_cost: Cost in USD
        fields_repaired: List of fields that were repaired (optional)
        agent_started_at: Timestamp when agent started (optional)
        agent_completed_at: Timestamp when agent completed (optional)

    Returns: routing_id
    """
    conn = get_neon_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute("""
            INSERT INTO public.agent_routing_log (
                garage_run_id,
                record_type,
                record_id,
                garage_bay,
                agent_assigned,
                routing_reason,
                missing_fields,
                contradictions,
                repair_attempt_number,
                is_chronic_bad,
                agent_started_at,
                agent_completed_at,
                agent_status,
                agent_cost,
                fields_repaired,
                routed_at,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
            ) RETURNING routing_id;
        """, (
            garage_run_id,
            record_type,
            record_id,
            garage_bay,
            agent_name,
            routing_reason,
            missing_fields if missing_fields else [],
            contradictions if contradictions else [],
            repair_attempt_number,
            is_chronic_bad,
            agent_started_at if agent_started_at else None,
            agent_completed_at if agent_completed_at else None,
            agent_status,
            agent_cost,
            fields_repaired if fields_repaired else []
        ))

        routing_id = cursor.fetchone()['routing_id']
        conn.commit()

        return routing_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def tag_record(record, agent_name, repair_status, cost):
    """
    Tag record with agent metadata.

    Args:
        record: Record dict
        agent_name: Name of agent
        repair_status: 'success', 'failed', 'partial'
        cost: Cost in USD

    Returns: Tagged record
    """
    record['_agent_metadata'] = {
        'agent_name': agent_name,
        'repair_status': repair_status,
        'cost': cost,
        'timestamp_repaired': datetime.now().isoformat()
    }

    return record

def setup_logging(agent_name, run_id):
    """
    Setup logging to file and stdout.

    Args:
        agent_name: Name of agent
        run_id: Run ID for this execution

    Returns: log file path
    """
    log_dir = Path(__file__).parent.parent.parent / "logs" / "agents"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{agent_name}_{run_id}.log"

    return log_file

def write_log(log_file, message, also_print=True):
    """
    Write message to log file and optionally print.

    Args:
        log_file: Path to log file
        message: Message to write
        also_print: Also print to stdout
    """
    timestamp = datetime.now().isoformat()
    log_message = f"[{timestamp}] {message}"

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')

    if also_print:
        print(log_message)

def compute_repair_confidence(original_record, repaired_record, agent_name):
    """
    Compute repair confidence score (0-100).

    Based on:
    - Number of fields repaired
    - Quality of enrichment
    - Agent type

    Returns: confidence score (0-100)
    """
    # Count fields repaired
    fields_repaired = 0

    for key in repaired_record.keys():
        if key.startswith('_'):
            continue  # Skip metadata fields

        original_value = original_record.get(key)
        repaired_value = repaired_record.get(key)

        # Field was added or changed
        if original_value != repaired_value:
            if repaired_value and repaired_value != '':
                fields_repaired += 1

    # Base confidence on fields repaired
    if fields_repaired == 0:
        return 0

    # Agent-specific confidence modifiers
    agent_confidence_multipliers = {
        'firecrawl': 0.85,  # 85% base confidence
        'apify': 0.80,      # 80% base confidence
        'abacus': 0.95,     # 95% base confidence (AI-powered)
        'claude': 0.98      # 98% base confidence (highest reasoning)
    }

    multiplier = agent_confidence_multipliers.get(agent_name, 0.75)

    # Calculate score
    # More fields repaired = higher confidence
    # But cap at 100
    raw_score = min(fields_repaired * 20, 100)
    final_score = int(raw_score * multiplier)

    return max(0, min(100, final_score))
