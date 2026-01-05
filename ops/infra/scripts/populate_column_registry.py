#!/usr/bin/env python3
"""Populate outreach.column_registry with column metadata."""

import psycopg2

conn = psycopg2.connect(
    host='ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    database='Marketing DB',
    user='Marketing DB_owner',
    password='npg_OsE4Z2oPCpiT',
    sslmode='require'
)
conn.autocommit = True
cur = conn.cursor()

print('=== POPULATING COLUMN REGISTRY ===')
print()

# Clear existing entries first
cur.execute('DELETE FROM outreach.column_registry')

# All columns for registration
columns = [
    # company_target
    ('outreach', 'company_target', 'target_id', 'UUID primary key for outreach company target record', 'UUID', False, 'gen_random_uuid()', None),
    ('outreach', 'company_target', 'company_unique_id', 'FK to cl.company_identity - parent hub identity', 'TEXT', False, None, 'cl.company_identity.company_unique_id'),
    ('outreach', 'company_target', 'outreach_status', 'Current outreach status', 'TEXT', False, 'not_started', None),
    ('outreach', 'company_target', 'bit_score_snapshot', 'Cached BIT score at targeting (0-100)', 'INTEGER', True, None, None),
    ('outreach', 'company_target', 'first_targeted_at', 'First targeting timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'company_target', 'last_targeted_at', 'Most recent outreach timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'company_target', 'sequence_count', 'Number of sequences completed', 'INTEGER', False, '0', None),
    ('outreach', 'company_target', 'active_sequence_id', 'Current sequence ID', 'TEXT', True, None, None),
    ('outreach', 'company_target', 'source', 'Record origin', 'TEXT', True, None, None),
    ('outreach', 'company_target', 'created_at', 'Creation timestamp', 'TIMESTAMPTZ', False, 'now()', None),
    ('outreach', 'company_target', 'updated_at', 'Last update timestamp', 'TIMESTAMPTZ', False, 'now()', None),

    # people
    ('outreach', 'people', 'person_id', 'UUID primary key for person record', 'UUID', False, 'gen_random_uuid()', None),
    ('outreach', 'people', 'target_id', 'FK to outreach.company_target', 'UUID', False, None, 'outreach.company_target.target_id'),
    ('outreach', 'people', 'company_unique_id', 'Denormalized FK to cl.company_identity', 'TEXT', False, None, 'cl.company_identity.company_unique_id'),
    ('outreach', 'people', 'slot_type', 'Executive slot: CHRO, HR, Benefits, CFO, CEO', 'TEXT', True, None, None),
    ('outreach', 'people', 'email', 'Primary email address', 'TEXT', False, None, None),
    ('outreach', 'people', 'email_verified', 'Email verification status', 'BOOLEAN', False, 'false', None),
    ('outreach', 'people', 'email_verified_at', 'Verification timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'people', 'contact_status', 'Contact status', 'TEXT', False, 'active', None),
    ('outreach', 'people', 'lifecycle_state', 'Lifecycle stage', 'outreach.lifecycle_state', False, 'suspect', None),
    ('outreach', 'people', 'funnel_membership', 'Funnel position', 'outreach.funnel_membership', False, 'top', None),
    ('outreach', 'people', 'email_open_count', 'Email open count', 'INTEGER', False, '0', None),
    ('outreach', 'people', 'email_click_count', 'Email click count', 'INTEGER', False, '0', None),
    ('outreach', 'people', 'email_reply_count', 'Email reply count', 'INTEGER', False, '0', None),
    ('outreach', 'people', 'current_bit_score', 'Current BIT score (0-100)', 'INTEGER', False, '0', None),
    ('outreach', 'people', 'last_event_ts', 'Last event timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'people', 'last_state_change_ts', 'Last state change timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'people', 'source', 'Record origin', 'TEXT', True, None, None),
    ('outreach', 'people', 'created_at', 'Creation timestamp', 'TIMESTAMPTZ', False, 'now()', None),
    ('outreach', 'people', 'updated_at', 'Last update timestamp', 'TIMESTAMPTZ', False, 'now()', None),

    # engagement_events
    ('outreach', 'engagement_events', 'event_id', 'UUID primary key', 'UUID', False, 'gen_random_uuid()', None),
    ('outreach', 'engagement_events', 'person_id', 'FK to outreach.people', 'UUID', False, None, 'outreach.people.person_id'),
    ('outreach', 'engagement_events', 'target_id', 'FK to outreach.company_target', 'UUID', False, None, 'outreach.company_target.target_id'),
    ('outreach', 'engagement_events', 'company_unique_id', 'Denormalized FK to cl', 'TEXT', False, None, 'cl.company_identity.company_unique_id'),
    ('outreach', 'engagement_events', 'event_type', 'Event type enum', 'outreach.event_type', False, None, None),
    ('outreach', 'engagement_events', 'event_subtype', 'Event subtype', 'TEXT', True, None, None),
    ('outreach', 'engagement_events', 'event_ts', 'Event timestamp', 'TIMESTAMPTZ', False, None, None),
    ('outreach', 'engagement_events', 'source_system', 'Source system', 'TEXT', True, None, None),
    ('outreach', 'engagement_events', 'source_campaign_id', 'Source campaign ID', 'TEXT', True, None, None),
    ('outreach', 'engagement_events', 'source_email_id', 'Source email ID', 'TEXT', True, None, None),
    ('outreach', 'engagement_events', 'metadata', 'Event metadata', 'JSONB', False, '{}', None),
    ('outreach', 'engagement_events', 'is_processed', 'Processing flag', 'BOOLEAN', False, 'false', None),
    ('outreach', 'engagement_events', 'processed_at', 'Processing timestamp', 'TIMESTAMPTZ', True, None, None),
    ('outreach', 'engagement_events', 'triggered_transition', 'Transition flag', 'BOOLEAN', False, 'false', None),
    ('outreach', 'engagement_events', 'transition_to_state', 'New lifecycle state', 'outreach.lifecycle_state', True, None, None),
    ('outreach', 'engagement_events', 'event_hash', 'Deduplication hash', 'VARCHAR(64)', True, None, None),
    ('outreach', 'engagement_events', 'is_duplicate', 'Duplicate flag', 'BOOLEAN', False, 'false', None),
    ('outreach', 'engagement_events', 'created_at', 'Creation timestamp', 'TIMESTAMPTZ', False, 'now()', None),
]

print(f'Inserting {len(columns)} column definitions...')

for schema, table, column, desc, fmt, nullable, default, fk in columns:
    unique_id = f'{schema}.{table}.{column}'
    cur.execute('''
        INSERT INTO outreach.column_registry
        (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (schema, table, column, unique_id, desc, fmt, nullable, default, fk))

print('  [OK] Column registry populated')

# Verify count
cur.execute('SELECT COUNT(*) FROM outreach.column_registry')
count = cur.fetchone()[0]
print(f'  [OK] Total columns registered: {count}')

cur.close()
conn.close()
