# Neon ENUM Types Reference

**Generated**: 2026-02-02
**Purpose**: Complete enumeration of all PostgreSQL ENUM types for ERD documentation
**Total ENUM Types**: 13
**Total ENUM Values**: 69

---

## SCHEMA: bit (BIT Intent Tracking)

### 1. authorization_band

**Purpose**: BIT tier levels for buyer intent classification

**Values** (6):
1. SILENT - No detectable buyer intent
2. WATCH - Minimal signals detected
3. EXPLORATORY - Early exploration signals
4. TARGETED - Clear research signals
5. ENGAGED - Active engagement signals
6. DIRECT - Direct inquiry/contact

**Used In**:
- bit.authorization_log (requested_band, actual_band)
- bit.proof_lines (band)
- bit.phase_state (current_band - stored as integer)

**Doctrine**: Band 0 = SILENT, Band 1 = WATCH, etc.

---

### 2. movement_direction

**Purpose**: Direction of buyer intent movement

**Values** (4):
1. INCREASING - Intent signals growing
2. DECREASING - Intent signals declining
3. REVERTING - Returning to previous state
4. STABLE - No significant change

**Used In**:
- bit.movement_events (direction)

---

### 3. movement_domain

**Purpose**: Categories of buyer intent signals

**Values** (3):
1. STRUCTURAL_PRESSURE - Cost/operational forces
2. DECISION_SURFACE - Decision-making activity
3. NARRATIVE_VOLATILITY - Communication/messaging changes

**Used In**:
- bit.movement_events (domain)

**Doctrine**: Aligned with pressure classes for multi-domain signal correlation

---

### 4. pressure_class

**Purpose**: Specific types of pressure driving buyer intent

**Values** (5):
1. COST_PRESSURE - Financial constraints
2. VENDOR_DISSATISFACTION - Current solution issues
3. DEADLINE_PROXIMITY - Time-sensitive needs
4. ORGANIZATIONAL_RECONFIGURATION - Structural changes
5. OPERATIONAL_CHAOS - Process breakdowns

**Used In**:
- bit.movement_events (pressure_class)
- bit.proof_lines (pressure_class)
- bit.phase_state (primary_pressure)

**Doctrine**: Maps to movement_domain for signal classification

---

## SCHEMA: outreach (Marketing Operations)

### 5. blog_source_type

**Purpose**: Content signal source classification

**Values** (7):
1. website - Company website content
2. blog - Blog posts
3. press - Press releases
4. news - News mentions
5. social - Social media
6. filing - Public filings (SEC, DOL, etc.)
7. careers - Careers page changes

**Used In**:
- outreach.blog (source_type_enum)

**Migration Note**: Replaces text field `source_type`

---

### 6. event_type

**Purpose**: Outreach engagement event types

**Values** (10):
1. EVENT_OPEN - Email opened
2. EVENT_CLICK - Link clicked
3. EVENT_REPLY - Email reply received
4. EVENT_OPENS_X3 - 3+ opens detected
5. EVENT_CLICKS_X2 - 2+ clicks detected
6. EVENT_TALENTFLOW_MOVE - TalentFlow signal detected
7. EVENT_BIT_THRESHOLD - BIT threshold crossed
8. EVENT_MANUAL_OVERRIDE - Manual intervention
9. EVENT_BOUNCE - Email bounced
10. EVENT_UNSUBSCRIBE - Unsubscribe event

**Used In**:
- outreach.engagement_events (likely table)
- outreach.attempt_log (likely table)

**Doctrine**: Drives lifecycle state transitions

---

### 7. funnel_membership

**Purpose**: Marketing funnel classification

**Values** (4):
1. COLD_UNIVERSE - No prior engagement
2. TALENTFLOW_UNIVERSE - TalentFlow signal detected
3. WARM_UNIVERSE - Prior engagement
4. REENGAGEMENT_UNIVERSE - Re-engagement campaign

**Used In**:
- outreach.outreach (likely column: funnel_status)
- cl.company_identity (likely column: funnel_classification)

**Doctrine**: Determines campaign eligibility and messaging

---

### 8. hub_status_enum

**Purpose**: Hub execution status in waterfall

**Values** (4):
1. PASS - Hub completed successfully
2. IN_PROGRESS - Hub currently executing
3. FAIL - Hub failed validation
4. BLOCKED - Hub blocked by upstream failure

**Used In**:
- outreach.hub_execution_log (likely table)
- outreach.company_target (likely column: hub_status)
- outreach.people (likely column: hub_status)
- outreach.dol (likely column: hub_status)

**Doctrine**: Enforces waterfall gate logic

---

### 9. lifecycle_state

**Purpose**: Company lifecycle stage

**Values** (8):
1. SUSPECT - Initial identification
2. WARM - Engaged in marketing
3. TALENTFLOW_WARM - TalentFlow + marketing engaged
4. REENGAGEMENT - Re-engagement campaign
5. APPOINTMENT - Meeting booked
6. CLIENT - Active client
7. DISQUALIFIED - Not eligible
8. UNSUBSCRIBED - Opted out

**Used In**:
- cl.company_identity (likely column: lifecycle_state)
- outreach.outreach (likely column: lifecycle_state)

**Doctrine**: Drives hub-to-hub handoff (APPOINTMENT → Sales)

---

### 10. override_type_enum

**Purpose**: Kill switch override types

**Values** (6):
1. marketing_disabled - Complete marketing stop
2. tier_cap - Cap max BIT tier
3. hub_bypass - Skip specific hub execution
4. cooldown - Temporary pause
5. legal_hold - Legal/compliance hold
6. customer_requested - Customer opt-out

**Used In**:
- outreach.manual_overrides (override_type)
- outreach.override_audit_log (override_type)

**Doctrine**: v1.0 FROZEN - Kill switch enforcement

---

## SCHEMA: people (People Intelligence)

### 11. email_status_t

**Purpose**: Email verification status

**Values** (4):
1. green - Verified deliverable
2. yellow - Risky/catch-all
3. red - Invalid/bounced
4. gray - Unknown/not checked

**Used In**:
- people.people_master (email_status)
- outreach.people (email_status)

**Doctrine**: Email verification sub-wheel classification

---

## SCHEMA: public (Shared/Legacy)

### 12. pressure_class_type

**Purpose**: DUPLICATE of bit.pressure_class (legacy)

**Values** (5):
1. COST_PRESSURE
2. VENDOR_DISSATISFACTION
3. DEADLINE_PROXIMITY
4. ORGANIZATIONAL_RECONFIGURATION
5. OPERATIONAL_CHAOS

**Status**: DUPLICATE - Should migrate to bit.pressure_class

---

### 13. pressure_domain

**Purpose**: DUPLICATE of bit.movement_domain (legacy)

**Values** (3):
1. STRUCTURAL_PRESSURE
2. DECISION_SURFACE
3. NARRATIVE_VOLATILITY

**Status**: DUPLICATE - Should migrate to bit.movement_domain

---

## ENUM USAGE MATRIX

| ENUM Type | Schema | Tables Using | Doctrine Status |
|-----------|--------|--------------|-----------------|
| authorization_band | bit | authorization_log, proof_lines, phase_state | FROZEN |
| movement_direction | bit | movement_events | FROZEN |
| movement_domain | bit | movement_events | FROZEN |
| pressure_class | bit | movement_events, proof_lines, phase_state | FROZEN |
| blog_source_type | outreach | blog | ACTIVE |
| event_type | outreach | engagement_events, attempt_log | ACTIVE |
| funnel_membership | outreach | outreach, cl.company_identity | ACTIVE |
| hub_status_enum | outreach | hub_execution_log, company_target, people, dol | FROZEN |
| lifecycle_state | outreach | outreach, cl.company_identity | FROZEN |
| override_type_enum | outreach | manual_overrides, override_audit_log | FROZEN |
| email_status_t | people | people_master, outreach.people | ACTIVE |
| pressure_class_type | public | LEGACY - migrate to bit.pressure_class | DEPRECATED |
| pressure_domain | public | LEGACY - migrate to bit.movement_domain | DEPRECATED |

---

## CRITICAL RELATIONSHIPS

### BIT Intent Scoring
```
movement_domain (STRUCTURAL_PRESSURE, DECISION_SURFACE, NARRATIVE_VOLATILITY)
    ↓ maps to
pressure_class (COST_PRESSURE, VENDOR_DISSATISFACTION, etc.)
    ↓ aggregates to
authorization_band (SILENT → WATCH → EXPLORATORY → TARGETED → ENGAGED → DIRECT)
```

### Lifecycle Progression
```
lifecycle_state (SUSPECT)
    ↓
funnel_membership (COLD_UNIVERSE)
    ↓ engagement
lifecycle_state (WARM)
    ↓ appointment
lifecycle_state (APPOINTMENT) → HANDOFF TO SALES
```

### Hub Waterfall Execution
```
hub_status_enum (IN_PROGRESS)
    ↓ success
hub_status_enum (PASS) → Next hub starts
    ↓ failure
hub_status_enum (FAIL) → Downstream BLOCKED
```

---

## ERD LEGEND RECOMMENDATIONS

### Color Coding

1. **BIT Intent (Red scale)**
   - SILENT: Light gray
   - WATCH: Light red
   - EXPLORATORY: Medium red
   - TARGETED: Dark red
   - ENGAGED: Bright red
   - DIRECT: Deep red

2. **Lifecycle States (Blue scale)**
   - SUSPECT: Light blue
   - WARM: Medium blue
   - APPOINTMENT: Green (handoff)
   - CLIENT: Gold
   - DISQUALIFIED: Gray
   - UNSUBSCRIBED: Black

3. **Hub Status (Traffic light)**
   - PASS: Green
   - IN_PROGRESS: Yellow
   - FAIL: Red
   - BLOCKED: Orange

4. **Email Status (Traditional)**
   - green: Green
   - yellow: Yellow
   - red: Red
   - gray: Gray

---

## MIGRATION NOTES

### Deprecated ENUMs

1. **public.pressure_class_type** → Migrate to **bit.pressure_class**
2. **public.pressure_domain** → Migrate to **bit.movement_domain**

### In-Progress Migrations

1. **outreach.blog.source_type (text)** → **outreach.blog.source_type_enum**
   - Status: Both columns exist
   - Action: Backfill ENUM, drop text column

---

## ENUM CONSTRAINT QUERIES

To verify ENUM usage in tables:

```sql
-- Find all columns using a specific ENUM
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    a.attname AS column_name,
    t.typname AS enum_type
FROM pg_attribute a
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_type t ON a.atttypid = t.oid
WHERE t.typname = 'override_type_enum'  -- Change to target ENUM
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, c.relname, a.attname;
```

---

**Last Updated**: 2026-02-02
**Status**: COMPLETE ENUM CATALOG
**Next Action**: Update ERD with ENUM legends and color coding
