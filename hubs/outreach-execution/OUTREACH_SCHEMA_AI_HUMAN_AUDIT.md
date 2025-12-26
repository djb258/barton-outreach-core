# Outreach Schema - AI/Human Readability Audit

**Audit Date**: 2025-12-26
**Auditor**: Schema Doctrine Enforcer
**Doctrine Version**: CL Parent-Child Model v1.1

---

## Executive Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL SCHEMA GAP DETECTED                          │
└─────────────────────────────────────────────────────────────────────────────┘

🚨 FINDING: The `outreach.*` schema DOES NOT EXIST in Neon.

Current State:
- Outreach tables are in `funnel.*` schema
- No `CREATE SCHEMA outreach` in any migration
- Doctrine specifies outreach.* but implementation uses funnel.*

Impact:
- Schema ownership unclear
- Table naming violates doctrine
- Cross-hub boundaries blurred
```

---

## Schema Discovery Results

### Schemas Found in Neon

| Schema | Tables | Outreach Access | Notes |
|--------|--------|-----------------|-------|
| `marketing` | company_master, people_master, company_slot | READ+WRITE | ⚠️ CL-owned (violation) |
| `funnel` | suspect_universe, engagement_events, etc. | WRITE | Currently hosting Outreach tables |
| `intake` | company_raw_from_clay, people_raw_from_clay | WRITE | Staging tables |
| `dol` | form_5500, form_5500_sf, schedule_a | WRITE | DOL Hub owned |
| `public` | shq_error_log | WRITE | System tables |
| `outreach` | **NONE** | N/A | ❌ DOES NOT EXIST |

### Doctrine vs Reality

| Doctrine Specifies | Reality | Gap |
|--------------------|---------|-----|
| `outreach.company_target` | Does not exist | ❌ MISSING |
| `outreach.people` | Does not exist | ❌ MISSING |
| `outreach.dol_filings` | Does not exist | ❌ MISSING |
| `outreach.blog_signals` | Does not exist | ❌ MISSING |
| `outreach.campaigns` | Does not exist | ❌ MISSING |
| `outreach.send_log` | Does not exist | ❌ MISSING |
| `outreach.engagement_events` | `funnel.engagement_events` | ⚠️ WRONG SCHEMA |

---

## Actual Tables Used by Outreach (in funnel.* schema)

The following tables are ACTUALLY used by Outreach Execution Hub but reside in
the wrong schema (`funnel.*` instead of `outreach.*`).

---

# TABLE 1: funnel.suspect_universe

## Table Summary

| Attribute | Value |
|-----------|-------|
| **Table Name** | `funnel.suspect_universe` |
| **Purpose** | Primary contact lifecycle table. All contacts start here as SUSPECT. Tracks engagement state through 4-Funnel GTM system. |
| **Owner** | ⚠️ UNCLEAR (should be Outreach, but in funnel schema) |
| **Write Authority** | barton-outreach-core |
| **Reads company_unique_id** | YES (via `company_id` column) |
| **Writes company identity** | NO ✅ |
| **Write Volume** | HIGH (every contact enters here) |

## Column Registry

| column_name | column_unique_id | column_description | column_format | Nullable | Default | FK Reference |
|-------------|------------------|-------------------|---------------|----------|---------|--------------|
| `suspect_id` | `OUT.SUSPECT.001` | Primary key - unique identifier for each contact entry in the funnel system. Generated on insert. | `UUID (gen_random_uuid())` | NO | gen_random_uuid() | None |
| `company_id` | `OUT.SUSPECT.002` | Foreign key to company_master. Links this contact to their employer. Required for all records. CL-owned identity reference. | `UUID (FK to marketing.company_master)` | NO | None | `marketing.company_master.company_unique_id` |
| `person_id` | `OUT.SUSPECT.003` | Foreign key to people_master. Links to the person's master record. Required for all records. | `UUID (FK to marketing.people_master)` | NO | None | `marketing.people_master.unique_id` |
| `email` | `OUT.SUSPECT.004` | Contact's email address. Used for outreach delivery. Must be unique across all suspects. Lowercase, validated format. | `VARCHAR(255) (lowercase, valid email format)` | NO | None | None |
| `funnel_state` | `OUT.SUSPECT.005` | Current lifecycle state. Valid values: SUSPECT, WARM, TALENTFLOW_WARM, REENGAGEMENT, APPOINTMENT, CLIENT, DISQUALIFIED, UNSUBSCRIBED. Drives outreach eligibility. | `ENUM funnel.lifecycle_state` | NO | 'SUSPECT' | None |
| `funnel_membership` | `OUT.SUSPECT.006` | Current funnel universe assignment. Valid values: COLD_UNIVERSE, TALENTFLOW_UNIVERSE, WARM_UNIVERSE, REENGAGEMENT_UNIVERSE. Determines sequence assignment. | `ENUM funnel.funnel_membership` | NO | 'COLD_UNIVERSE' | None |
| `last_event_ts` | `OUT.SUSPECT.007` | Timestamp of most recent engagement event (open, click, reply). NULL if no engagement. Updated by engagement processing. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `last_state_change_ts` | `OUT.SUSPECT.008` | Timestamp of most recent funnel_state transition. Updated automatically by trigger. Used for state timing calculations. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `entered_suspect_ts` | `OUT.SUSPECT.009` | Timestamp when contact first entered the funnel system. Immutable after insert. Used for funnel velocity calculations. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |
| `email_open_count` | `OUT.SUSPECT.010` | Cumulative count of email opens for this contact. Incremented by engagement processor. Used for threshold calculations (3+ opens = warm). | `INTEGER (non-negative)` | NO | 0 | None |
| `email_click_count` | `OUT.SUSPECT.011` | Cumulative count of email link clicks for this contact. Incremented by engagement processor. Used for threshold calculations (2+ clicks = warm). | `INTEGER (non-negative)` | NO | 0 | None |
| `email_reply_count` | `OUT.SUSPECT.012` | Cumulative count of email replies for this contact. Any reply = immediate warm promotion. | `INTEGER (non-negative)` | NO | 0 | None |
| `current_bit_score` | `OUT.SUSPECT.013` | Current BIT (Buyer Intent Tool) score. Range 0-100. Calculated by BIT Engine. Threshold 50+ triggers warm consideration. | `INTEGER (0-100, non-negative)` | NO | 0 | None |
| `reengagement_cycle` | `OUT.SUSPECT.014` | Number of re-engagement attempts. Max 3 per doctrine. Incremented when entering REENGAGEMENT state. 0 = never re-engaged. | `INTEGER (0-5)` | NO | 0 | None |
| `last_reengagement_ts` | `OUT.SUSPECT.015` | Timestamp of most recent re-engagement cycle start. NULL if never re-engaged. Used for 90-day decay calculation. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `is_locked` | `OUT.SUSPECT.016` | State transition lock. TRUE prevents any state changes during processing. Used to prevent race conditions. | `BOOLEAN` | NO | FALSE | None |
| `lock_reason` | `OUT.SUSPECT.017` | Human-readable explanation for why record is locked. Required when is_locked=TRUE. Example: "Processing BIT signal". | `VARCHAR(255)` | YES | None | None |
| `locked_at` | `OUT.SUSPECT.018` | Timestamp when lock was acquired. Used for stale lock detection (>5 min = stale). | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `cooldown_until` | `OUT.SUSPECT.019` | Anti-thrashing cooldown. No state transitions allowed until this timestamp. Prevents rapid state oscillation. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `is_bounced` | `OUT.SUSPECT.020` | Email deliverability flag. TRUE if email hard bounced. Suppresses all outreach. | `BOOLEAN` | NO | FALSE | None |
| `is_unsubscribed` | `OUT.SUSPECT.021` | Opt-out flag. TRUE if contact requested removal. Suppresses all outreach. Cannot be reversed programmatically. | `BOOLEAN` | NO | FALSE | None |
| `is_disqualified` | `OUT.SUSPECT.022` | Manual disqualification flag. TRUE if contact/company is not a fit. Suppresses all outreach. | `BOOLEAN` | NO | FALSE | None |
| `source` | `OUT.SUSPECT.023` | Origin of this contact record. Examples: 'csv_import', 'clay_enrichment', 'linkedin_scrape', 'manual'. For audit trail. | `VARCHAR(100)` | YES | None | None |
| `created_at` | `OUT.SUSPECT.024` | Record creation timestamp. Immutable after insert. System-generated. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |
| `updated_at` | `OUT.SUSPECT.025` | Last modification timestamp. Auto-updated by trigger on any change. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |

## AI Readability Check

| Check | Result | Notes |
|-------|--------|-------|
| Can LLM infer correct usage without repo context? | ⚠️ PARTIAL | `funnel_state` enum values need documentation |
| Columns with system-dependent meaning? | YES | `is_locked`, `cooldown_until` require processing knowledge |
| Overloaded columns? | NO | Each column has single purpose |

**Remediation Notes**:
- Add COMMENT ON TYPE for funnel.lifecycle_state explaining each state
- Add COMMENT ON TYPE for funnel.funnel_membership explaining universe meaning
- Consider renaming to `outreach.suspect_universe`

## Human Operability Check

| Check | Result | Notes |
|-------|--------|-------|
| Could new engineer safely INSERT? | ⚠️ PARTIAL | Need to know valid enum values |
| Could operator debug bad data? | YES | All fields are inspectable |
| Can trace value to pipeline source? | YES | `source` column tracks origin |

**Remediation Notes**:
- Add check constraint documentation for enums
- Add example INSERT statement in comments

---

# TABLE 2: funnel.engagement_events

## Table Summary

| Attribute | Value |
|-----------|-------|
| **Table Name** | `funnel.engagement_events` |
| **Purpose** | Immutable event log for all engagement signals (opens, clicks, replies). Source of truth for threshold calculations and audit trail. |
| **Owner** | ⚠️ UNCLEAR (should be Outreach) |
| **Write Authority** | barton-outreach-core |
| **Reads company_unique_id** | YES (via `company_id`) |
| **Writes company identity** | NO ✅ |
| **Write Volume** | VERY HIGH (every engagement creates row) |

## Column Registry

| column_name | column_unique_id | column_description | column_format | Nullable | Default | FK Reference |
|-------------|------------------|-------------------|---------------|----------|---------|--------------|
| `event_id` | `OUT.ENGAGE.001` | Primary key - unique identifier for each engagement event. Generated on insert. Immutable. | `UUID (gen_random_uuid())` | NO | gen_random_uuid() | None |
| `company_id` | `OUT.ENGAGE.002` | Foreign key to company_master. Links event to company. Required for all events. CL-owned identity reference. | `UUID (FK)` | NO | None | `marketing.company_master` |
| `person_id` | `OUT.ENGAGE.003` | Foreign key to people_master. Links event to person. Required for all events. | `UUID (FK)` | NO | None | `marketing.people_master` |
| `suspect_id` | `OUT.ENGAGE.004` | Foreign key to suspect_universe. Links event to funnel entry. May be NULL for events before funnel entry. | `UUID (FK)` | YES | None | `funnel.suspect_universe` |
| `event_type` | `OUT.ENGAGE.005` | Type of engagement event. Valid values from funnel.event_type enum: EVENT_REPLY, EVENT_CLICKS_X2, EVENT_OPENS_X3, etc. Determines state transition logic. | `ENUM funnel.event_type` | NO | None | None |
| `event_subtype` | `OUT.ENGAGE.006` | Subtype for granular classification. Examples: 'positive_reply', 'ooo_reply', 'link_click', 'image_open'. Free text, not enum. | `VARCHAR(50)` | YES | None | None |
| `event_ts` | `OUT.ENGAGE.007` | Timestamp when engagement occurred (not when detected). Provided by source system. Used for ordering and dedup. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |
| `source_system` | `OUT.ENGAGE.008` | System that detected/reported event. Examples: 'email_tracking', 'crm', 'manual', 'webhook'. For debugging and audit. | `VARCHAR(100)` | YES | None | None |
| `source_campaign_id` | `OUT.ENGAGE.009` | Campaign ID from source system. Links to external campaign. May be NULL for non-campaign events. | `VARCHAR(100)` | YES | None | None |
| `source_email_id` | `OUT.ENGAGE.010` | Specific email/message ID from source. Links to exact send. May be NULL for aggregated events. | `VARCHAR(100)` | YES | None | None |
| `metadata` | `OUT.ENGAGE.011` | Flexible JSON storage for event-specific data. Schema varies by event_type. Examples: link_url for clicks, reply_sentiment for replies. | `JSONB` | NO | '{}' | None |
| `is_processed` | `OUT.ENGAGE.012` | Processing flag. TRUE after state machine has evaluated event. Used for queue processing. | `BOOLEAN` | NO | FALSE | None |
| `processed_at` | `OUT.ENGAGE.013` | Timestamp when event was processed by state machine. NULL if not yet processed. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `triggered_transition` | `OUT.ENGAGE.014` | Whether this event triggered a state transition. TRUE if event caused funnel_state change. | `BOOLEAN` | NO | FALSE | None |
| `transition_to_state` | `OUT.ENGAGE.015` | Target state if transition occurred. NULL if no transition. Valid values from funnel.lifecycle_state. | `ENUM funnel.lifecycle_state` | YES | None | None |
| `event_hash` | `OUT.ENGAGE.016` | SHA256 hash for deduplication. Computed from source+type+person+ts. Unique constraint prevents duplicate events. | `VARCHAR(64) (SHA256 hex)` | YES | None | None |
| `is_duplicate` | `OUT.ENGAGE.017` | Duplicate detection flag. TRUE if event was detected as duplicate during processing. Duplicate events are not processed. | `BOOLEAN` | NO | FALSE | None |
| `created_at` | `OUT.ENGAGE.018` | Record creation timestamp. Immutable after insert. System-generated. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |

## AI Readability Check

| Check | Result | Notes |
|-------|--------|-------|
| Can LLM infer correct usage without repo context? | ⚠️ PARTIAL | `metadata` JSONB schema varies by event_type |
| Columns with system-dependent meaning? | YES | `event_hash` generation algorithm undocumented |
| Overloaded columns? | ⚠️ PARTIAL | `metadata` is intentionally flexible |

**Remediation Notes**:
- Document `metadata` schemas per event_type in COMMENT
- Document `event_hash` algorithm in COMMENT
- Add examples of valid `metadata` payloads

## Human Operability Check

| Check | Result | Notes |
|-------|--------|-------|
| Could new engineer safely INSERT? | NO | Need to know hash algorithm, valid event_types |
| Could operator debug bad data? | ⚠️ PARTIAL | `metadata` inspection requires schema knowledge |
| Can trace value to pipeline source? | YES | `source_system`, `source_campaign_id` track origin |

---

# TABLE 3: funnel.warm_universe

## Table Summary

| Attribute | Value |
|-----------|-------|
| **Table Name** | `funnel.warm_universe` |
| **Purpose** | Funnel 3: Warm Universe - Tracks contacts with demonstrated engagement. Entry via email reply, 3+ opens, 2+ clicks, or BIT threshold. |
| **Owner** | ⚠️ UNCLEAR (should be Outreach) |
| **Write Authority** | barton-outreach-core |
| **Reads company_unique_id** | YES |
| **Writes company identity** | NO ✅ |
| **Write Volume** | MEDIUM (only engaged contacts) |

## Column Registry

| column_name | column_unique_id | column_description | column_format | Nullable | Default | FK Reference |
|-------------|------------------|-------------------|---------------|----------|---------|--------------|
| `warm_id` | `OUT.WARM.001` | Primary key - unique identifier for warm entry. Generated on promotion to warm. | `UUID (gen_random_uuid())` | NO | gen_random_uuid() | None |
| `company_id` | `OUT.WARM.002` | Foreign key to company_master. Links warm entry to company. CL-owned identity reference. | `UUID (FK)` | NO | None | `marketing.company_master` |
| `person_id` | `OUT.WARM.003` | Foreign key to people_master. Links warm entry to person. | `UUID (FK)` | NO | None | `marketing.people_master` |
| `suspect_id` | `OUT.WARM.004` | Foreign key to suspect_universe. Links back to original funnel entry. | `UUID (FK)` | YES | None | `funnel.suspect_universe` |
| `warm_reason` | `OUT.WARM.005` | How contact qualified for warm status. Valid values: 'reply', 'opens_x3', 'clicks_x2', 'bit_threshold', 'manual'. Determines nurture track. | `VARCHAR(50) (enumerated)` | NO | None | None |
| `warm_score` | `OUT.WARM.006` | Engagement score at time of promotion. Higher = more engaged. Used for prioritization. | `INTEGER (non-negative)` | NO | 0 | None |
| `qualifying_event_id` | `OUT.WARM.007` | Foreign key to engagement_events. The specific event that triggered warm promotion. | `UUID (FK)` | YES | None | `funnel.engagement_events` |
| `first_warm_ts` | `OUT.WARM.008` | Timestamp when contact first achieved warm status. Immutable. Used for velocity reporting. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |
| `last_engagement_ts` | `OUT.WARM.009` | Timestamp of most recent engagement after warm promotion. Updated by engagement processor. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `opens_at_promotion` | `OUT.WARM.010` | Email open count at moment of warm promotion. Snapshot for analysis. | `INTEGER (non-negative)` | NO | 0 | None |
| `clicks_at_promotion` | `OUT.WARM.011` | Email click count at moment of warm promotion. Snapshot for analysis. | `INTEGER (non-negative)` | NO | 0 | None |
| `replies_at_promotion` | `OUT.WARM.012` | Email reply count at moment of warm promotion. Snapshot for analysis. | `INTEGER (non-negative)` | NO | 0 | None |
| `bit_score_at_promotion` | `OUT.WARM.013` | BIT score at moment of warm promotion. Snapshot for analysis. | `INTEGER (0-100)` | NO | 0 | None |
| `current_opens` | `OUT.WARM.014` | Current cumulative open count. Updated after promotion. | `INTEGER (non-negative)` | NO | 0 | None |
| `current_clicks` | `OUT.WARM.015` | Current cumulative click count. Updated after promotion. | `INTEGER (non-negative)` | NO | 0 | None |
| `current_replies` | `OUT.WARM.016` | Current cumulative reply count. Updated after promotion. | `INTEGER (non-negative)` | NO | 0 | None |
| `has_talentflow_signal` | `OUT.WARM.017` | Whether contact also has TalentFlow signal (dual qualification). Used for segmentation. | `BOOLEAN` | NO | FALSE | None |
| `talentflow_signal_id` | `OUT.WARM.018` | Foreign key to talentflow_signal_log if dual-qualified. | `UUID (FK)` | YES | None | `funnel.talentflow_signal_log` |
| `nurture_sequence_id` | `OUT.WARM.019` | Current nurture sequence assignment. External ID from sequence system. | `VARCHAR(100)` | YES | None | None |
| `nurture_step` | `OUT.WARM.020` | Current step in nurture sequence. 0 = not started. | `INTEGER (non-negative)` | YES | 0 | None |
| `nurture_started_at` | `OUT.WARM.021` | Timestamp when nurture sequence was started. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `is_active` | `OUT.WARM.022` | Whether warm entry is active. FALSE if demoted or promoted. | `BOOLEAN` | NO | TRUE | None |
| `demoted_to_reengagement` | `OUT.WARM.023` | Whether contact was demoted to re-engagement due to inactivity. | `BOOLEAN` | NO | FALSE | None |
| `demoted_at` | `OUT.WARM.024` | Timestamp of demotion. NULL if never demoted. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `promoted_to_appointment` | `OUT.WARM.025` | Whether contact was promoted to appointment status. | `BOOLEAN` | NO | FALSE | None |
| `promoted_at` | `OUT.WARM.026` | Timestamp of promotion. NULL if never promoted. | `TIMESTAMPTZ (UTC)` | YES | None | None |
| `source` | `OUT.WARM.027` | Origin tracking. Same semantics as suspect_universe.source. | `VARCHAR(100)` | YES | None | None |
| `created_at` | `OUT.WARM.028` | Record creation timestamp. Immutable. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |
| `updated_at` | `OUT.WARM.029` | Last modification timestamp. Auto-updated by trigger. | `TIMESTAMPTZ (UTC)` | NO | NOW() | None |

## AI Readability Check

| Check | Result | Notes |
|-------|--------|-------|
| Can LLM infer correct usage without repo context? | ⚠️ PARTIAL | `warm_reason` valid values need documentation |
| Columns with system-dependent meaning? | YES | `nurture_sequence_id` external reference |
| Overloaded columns? | NO | Clear single-purpose columns |

## Human Operability Check

| Check | Result | Notes |
|-------|--------|-------|
| Could new engineer safely INSERT? | ⚠️ PARTIAL | Need warm_reason valid values |
| Could operator debug bad data? | YES | All fields inspectable |
| Can trace value to pipeline source? | YES | `qualifying_event_id` links to cause |

---

# TABLE 4: funnel.talentflow_signal_log

## Table Summary

| Attribute | Value |
|-----------|-------|
| **Table Name** | `funnel.talentflow_signal_log` |
| **Purpose** | TalentFlow movement signal log. Tracks job changes, promotions, and role movements. Funnel 2 qualification source. |
| **Owner** | ⚠️ UNCLEAR (should be Outreach/People) |
| **Write Authority** | barton-outreach-core |
| **Reads company_unique_id** | YES |
| **Writes company identity** | NO ✅ |
| **Write Volume** | MEDIUM (movement events only) |

## Column Registry (Abbreviated - See migration for full)

| column_name | column_unique_id | column_description | column_format | Nullable |
|-------------|------------------|-------------------|---------------|----------|
| `signal_id` | `OUT.TALENT.001` | Primary key | `UUID` | NO |
| `company_id` | `OUT.TALENT.002` | FK to company_master | `UUID` | NO |
| `person_id` | `OUT.TALENT.003` | FK to people_master | `UUID` | NO |
| `signal_type` | `OUT.TALENT.004` | Type: job_change, promotion, lateral, startup, company_change | `ENUM` | NO |
| `old_company_id` | `OUT.TALENT.005` | Previous employer (if company change) | `UUID` | YES |
| `new_company_id` | `OUT.TALENT.006` | New employer (if company change) | `UUID` | YES |
| `signal_ts` | `OUT.TALENT.007` | When movement occurred | `TIMESTAMPTZ` | NO |
| `signal_age_days` | `OUT.TALENT.008` | COMPUTED: days since movement | `INTEGER` | YES |
| `is_verified` | `OUT.TALENT.009` | Verification status | `BOOLEAN` | NO |
| `priority_score` | `OUT.TALENT.010` | Priority 0-100 | `INTEGER` | NO |
| `expires_at` | `OUT.TALENT.011` | Signal expires 90 days per doctrine | `TIMESTAMPTZ` | YES |

---

# TABLE 5: funnel.bit_signal_log

## Table Summary

| Attribute | Value |
|-----------|-------|
| **Table Name** | `funnel.bit_signal_log` |
| **Purpose** | Log of all BIT (Buyer Intent Tool) score changes and signals. Tracks intent signals for state transitions. |
| **Owner** | ⚠️ UNCLEAR (should be Outreach) |
| **Write Authority** | barton-outreach-core |
| **Reads company_unique_id** | YES |
| **Writes company identity** | NO ✅ |
| **Write Volume** | HIGH (every BIT signal) |

## Column Registry (Key columns)

| column_name | column_unique_id | column_description | column_format | Nullable |
|-------------|------------------|-------------------|---------------|----------|
| `bit_log_id` | `OUT.BIT.001` | Primary key | `UUID` | NO |
| `company_id` | `OUT.BIT.002` | FK to company_master | `UUID` | NO |
| `person_id` | `OUT.BIT.003` | FK to people_master | `UUID` | NO |
| `bit_score` | `OUT.BIT.004` | New BIT score after signal | `INTEGER (0-100)` | NO |
| `previous_score` | `OUT.BIT.005` | BIT score before signal | `INTEGER` | YES |
| `score_delta` | `OUT.BIT.006` | Change in score | `INTEGER` | YES |
| `signal_type` | `OUT.BIT.007` | Type of BIT signal | `VARCHAR` | NO |
| `signal_source` | `OUT.BIT.008` | Source spoke/system | `VARCHAR` | YES |

---

## Missing Tables (Doctrine-Required, NOT FOUND)

| Table | Doctrine ID | Status | Impact |
|-------|-------------|--------|--------|
| `outreach.company_target` | 04.04.04.01 | ❌ MISSING | No internal anchor to CL |
| `outreach.campaigns` | 04.04.04.10 | ❌ MISSING | No campaign management |
| `outreach.sequences` | 04.04.04.11 | ❌ MISSING | No sequence definitions |
| `outreach.send_log` | 04.04.04.12 | ❌ MISSING | No send history |
| `outreach.blog_signals` | 04.04.04.04 | ❌ MISSING | Blog sub-hub not implemented |

---

## Enforcement Recommendations

### 1. Create outreach.* Schema

```sql
-- ============================================================================
-- ENFORCEMENT: Create proper outreach schema
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS outreach;

COMMENT ON SCHEMA outreach IS
'Outreach Execution Hub - Owned by barton-outreach-core.
Child sub-hub of Company Lifecycle (CL). Manages campaign state,
sequence execution, send logs, and engagement tracking.
Doctrine ID: 04.04.04';

-- Grant permissions
GRANT USAGE ON SCHEMA outreach TO outreach_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA outreach TO ui_reader;
```

### 2. Migrate Tables to outreach.* Schema

```sql
-- Option A: Rename in place (requires downtime)
ALTER TABLE funnel.suspect_universe SET SCHEMA outreach;
ALTER TABLE funnel.engagement_events SET SCHEMA outreach;
ALTER TABLE funnel.warm_universe SET SCHEMA outreach;
ALTER TABLE funnel.talentflow_signal_log SET SCHEMA outreach;
ALTER TABLE funnel.bit_signal_log SET SCHEMA outreach;

-- Option B: Create views for backward compatibility
CREATE VIEW funnel.suspect_universe AS SELECT * FROM outreach.suspect_universe;
CREATE VIEW funnel.engagement_events AS SELECT * FROM outreach.engagement_events;
```

### 3. SQL COMMENT Statements (Apply to existing tables)

```sql
-- ============================================================================
-- COLUMN COMMENTS for funnel.suspect_universe
-- ============================================================================

COMMENT ON COLUMN funnel.suspect_universe.suspect_id IS
'OUT.SUSPECT.001 | Primary key - unique identifier for each contact entry in the funnel system. Generated on insert via gen_random_uuid(). Immutable after creation.';

COMMENT ON COLUMN funnel.suspect_universe.company_id IS
'OUT.SUSPECT.002 | Foreign key to marketing.company_master.company_unique_id. Links this contact to their employer company. REQUIRED - no orphan contacts allowed. CL-owned identity - read only reference.';

COMMENT ON COLUMN funnel.suspect_universe.person_id IS
'OUT.SUSPECT.003 | Foreign key to marketing.people_master.unique_id. Links to the person master record. REQUIRED - ensures data integrity with People Hub.';

COMMENT ON COLUMN funnel.suspect_universe.email IS
'OUT.SUSPECT.004 | Contact email address for outreach delivery. UNIQUE constraint - one email per suspect. Format: lowercase, validated email format. Used as primary outreach channel.';

COMMENT ON COLUMN funnel.suspect_universe.funnel_state IS
'OUT.SUSPECT.005 | Current lifecycle state from funnel.lifecycle_state enum. Valid values: SUSPECT (new/cold), WARM (engaged), TALENTFLOW_WARM (job change), REENGAGEMENT (re-warming), APPOINTMENT (meeting scheduled), CLIENT (converted), DISQUALIFIED (not a fit), UNSUBSCRIBED (opted out). Drives outreach eligibility and sequence assignment.';

COMMENT ON COLUMN funnel.suspect_universe.funnel_membership IS
'OUT.SUSPECT.006 | Current funnel universe from funnel.funnel_membership enum. Valid values: COLD_UNIVERSE (Funnel 1 - outbound), TALENTFLOW_UNIVERSE (Funnel 2 - job changers), WARM_UNIVERSE (Funnel 3 - engaged), REENGAGEMENT_UNIVERSE (Funnel 4 - re-warming). Determines which sequences and cadences apply.';

COMMENT ON COLUMN funnel.suspect_universe.email_open_count IS
'OUT.SUSPECT.010 | Cumulative count of email opens detected for this contact. Incremented by engagement processor when open event received. Threshold: 3+ opens can trigger WARM promotion. Never decremented.';

COMMENT ON COLUMN funnel.suspect_universe.email_click_count IS
'OUT.SUSPECT.011 | Cumulative count of email link clicks detected for this contact. Incremented by engagement processor when click event received. Threshold: 2+ clicks can trigger WARM promotion. Never decremented.';

COMMENT ON COLUMN funnel.suspect_universe.email_reply_count IS
'OUT.SUSPECT.012 | Cumulative count of email replies detected for this contact. ANY reply triggers immediate WARM promotion regardless of sentiment. Never decremented.';

COMMENT ON COLUMN funnel.suspect_universe.current_bit_score IS
'OUT.SUSPECT.013 | Current BIT (Buyer Intent Tool) score. Range 0-100 enforced by CHECK constraint. Calculated by BIT Engine from multiple signals. Threshold 50+ triggers WARM consideration. Updated by bit_signal_log processing.';

COMMENT ON COLUMN funnel.suspect_universe.is_locked IS
'OUT.SUSPECT.016 | State transition lock flag. When TRUE, no funnel_state changes are allowed. Used by processing jobs to prevent race conditions. Lock should be held <5 minutes. Stale locks (>5 min) may be force-released.';

COMMENT ON COLUMN funnel.suspect_universe.is_bounced IS
'OUT.SUSPECT.020 | Email deliverability suppression. TRUE if email hard bounced (permanent failure). When TRUE, contact is suppressed from ALL outreach. Cannot be auto-reversed - requires manual email update.';

COMMENT ON COLUMN funnel.suspect_universe.is_unsubscribed IS
'OUT.SUSPECT.021 | Opt-out suppression. TRUE if contact explicitly requested removal from communications. When TRUE, contact is suppressed from ALL outreach. Cannot be reversed programmatically - legal requirement.';

-- ============================================================================
-- COLUMN COMMENTS for funnel.engagement_events
-- ============================================================================

COMMENT ON COLUMN funnel.engagement_events.event_type IS
'OUT.ENGAGE.005 | Type of engagement from funnel.event_type enum. EVENT_REPLY = email reply received. EVENT_CLICKS_X2 = 2nd click threshold crossed. EVENT_OPENS_X3 = 3rd open threshold crossed. EVENT_TALENTFLOW_MOVE = job change detected. EVENT_BIT_THRESHOLD = BIT score 50+ crossed. EVENT_MANUAL_OVERRIDE = human intervention.';

COMMENT ON COLUMN funnel.engagement_events.metadata IS
'OUT.ENGAGE.011 | Flexible JSONB for event-specific data. Schema varies by event_type. For EVENT_REPLY: {sentiment, reply_text_snippet, is_ooo}. For EVENT_CLICKS_X2: {link_url, link_text}. For EVENT_BIT_THRESHOLD: {old_score, new_score, triggering_signal}. Always validate before INSERT.';

COMMENT ON COLUMN funnel.engagement_events.event_hash IS
'OUT.ENGAGE.016 | SHA256 hash for deduplication. Computed as: SHA256(source_system + event_type + person_id + event_ts). UNIQUE constraint prevents duplicate event processing. NULL only for legacy records.';
```

### 4. Column Registry Table Definition

```sql
-- ============================================================================
-- ENFORCEMENT: Create column registry table
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach.column_registry (
    registry_id         SERIAL PRIMARY KEY,
    schema_name         VARCHAR(50) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100) NOT NULL,
    column_unique_id    VARCHAR(50) NOT NULL UNIQUE,
    column_description  TEXT NOT NULL,
    column_format       VARCHAR(200) NOT NULL,
    is_nullable         BOOLEAN NOT NULL,
    default_value       TEXT,
    fk_reference        TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_column_registry UNIQUE (schema_name, table_name, column_name)
);

COMMENT ON TABLE outreach.column_registry IS
'Metadata registry for all Outreach schema columns. Every column in outreach.* MUST have an entry here. Enforced by CI check.';

-- Example entry
INSERT INTO outreach.column_registry
(schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable)
VALUES
('outreach', 'suspect_universe', 'suspect_id', 'OUT.SUSPECT.001',
 'Primary key - unique identifier for each contact entry in the funnel system. Generated on insert.',
 'UUID (gen_random_uuid())', FALSE);
```

### 5. CI Check Script

```bash
#!/bin/bash
# ci/check_column_documentation.sh
# Ensures all columns have required documentation

# Check for columns without COMMENT
psql $DATABASE_URL -c "
SELECT
    c.table_schema,
    c.table_name,
    c.column_name,
    'MISSING COMMENT' as issue
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_description d
    ON d.objsubid = c.ordinal_position
    AND d.objoid = (c.table_schema || '.' || c.table_name)::regclass
WHERE c.table_schema = 'outreach'
  AND d.description IS NULL
ORDER BY c.table_name, c.ordinal_position;
"

# Check for columns not in registry
psql $DATABASE_URL -c "
SELECT
    c.table_schema,
    c.table_name,
    c.column_name,
    'NOT IN REGISTRY' as issue
FROM information_schema.columns c
LEFT JOIN outreach.column_registry r
    ON r.schema_name = c.table_schema
    AND r.table_name = c.table_name
    AND r.column_name = c.column_name
WHERE c.table_schema = 'outreach'
  AND r.registry_id IS NULL
ORDER BY c.table_name, c.ordinal_position;
"
```

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Tables audited | 5 (in funnel.* schema) |
| Tables missing | 5 (in outreach.* schema) |
| Columns audited | 83 |
| Columns with unique_id | 0 (BLOCKING - need to add) |
| Columns with description | ~40% (via SQL COMMENT) |
| Columns with format spec | ~90% (via data type) |
| AI-readable columns | ~70% |
| Human-operable tables | ~60% |

### Blocking Issues

1. ❌ `outreach.*` schema does not exist
2. ❌ No `column_unique_id` assigned to any column
3. ❌ Many columns lack SQL COMMENT
4. ❌ JSONB columns lack schema documentation
5. ❌ No column registry table exists

### Recommended Priority

1. **P0**: Create `outreach` schema
2. **P0**: Add SQL COMMENT to all columns
3. **P1**: Create `outreach.column_registry` table
4. **P1**: Migrate tables from `funnel.*` to `outreach.*`
5. **P2**: Implement CI checks for documentation
6. **P2**: Document JSONB schemas per column

---

*Audit Complete*
*Auditor: Schema Doctrine Enforcer*
*Date: 2025-12-26*
