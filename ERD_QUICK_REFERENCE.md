# ERD Quick Reference Card

**Purpose**: Fast lookup for ERD diagram updates
**Generated**: 2026-02-02

---

## CRITICAL PRIMARY KEY CHANGE

```
❌ OLD: cl.company_identity.company_unique_id (PK)
✅ NEW: cl.company_identity.sovereign_company_id (PK)

company_unique_id is LEGACY - still present but not authoritative
```

---

## CRITICAL FOREIGN KEY CHANGE

```
❌ OLD: outreach.outreach.sovereign_company_id → cl.company_identity.sovereign_company_id
✅ NEW: outreach.outreach.sovereign_id → cl.company_identity.sovereign_company_id

Column name in outreach.outreach is "sovereign_id" not "sovereign_company_id"
```

---

## TABLE: cl.company_identity (33 columns)

**PK**: sovereign_company_id (uuid)
**Legacy PK**: company_unique_id (uuid) - keep for reference

**Key Columns**:
- sovereign_company_id (uuid, PK) - Minted by CL
- outreach_id (uuid, NULLABLE) - Minted by Outreach, WRITE-ONCE
- sales_process_id (uuid, NULLABLE) - Minted by Sales, WRITE-ONCE
- client_id (uuid, NULLABLE) - Minted by Client, WRITE-ONCE
- company_name (text, NOT NULL)
- company_domain (text, NULLABLE)
- lifecycle_state (text, NULLABLE) - Uses lifecycle_state ENUM
- created_at (timestamptz, NOT NULL, DEFAULT now())

---

## TABLE: outreach.outreach (5 columns)

**PK**: outreach_id (uuid)
**FK**: sovereign_id → cl.company_identity.sovereign_company_id

**All Columns**:
- outreach_id (uuid, NOT NULL, PK, DEFAULT gen_random_uuid())
- sovereign_id (uuid, NOT NULL, FK)
- domain (varchar(255), NULLABLE)
- created_at (timestamptz, NOT NULL, DEFAULT now())
- updated_at (timestamptz, NOT NULL, DEFAULT now())

---

## TABLE: outreach.manual_overrides (12 columns)

**PK**: override_id (uuid)
**Purpose**: Kill switch system

**Key Columns**:
- override_id (uuid, NOT NULL, PK)
- company_unique_id (text, NOT NULL)
- override_type (USER-DEFINED, NOT NULL) - ENUM: marketing_disabled, tier_cap, hub_bypass, cooldown, legal_hold, customer_requested
- reason (text, NOT NULL)
- is_active (boolean, NOT NULL, DEFAULT true)
- created_at (timestamptz, NOT NULL, DEFAULT now())
- created_by (text, NOT NULL, DEFAULT CURRENT_USER)
- expires_at (timestamptz, NULLABLE)

---

## TABLE: outreach.override_audit_log (9 columns)

**PK**: audit_id (uuid)
**FK**: override_id → outreach.manual_overrides.override_id

**Key Columns**:
- audit_id (uuid, NOT NULL, PK)
- company_unique_id (text, NOT NULL)
- override_id (uuid, NULLABLE, FK)
- action (text, NOT NULL) - CREATED, DEACTIVATED, etc.
- old_value (jsonb, NULLABLE)
- new_value (jsonb, NULLABLE)
- performed_by (text, NOT NULL, DEFAULT CURRENT_USER)
- performed_at (timestamptz, NOT NULL, DEFAULT now())

---

## TABLE: cl.company_domains (7 columns)

**PK**: domain_id (uuid)
**FK**: company_unique_id → cl.company_identity.company_unique_id

**Key Columns**:
- domain_id (uuid, NOT NULL, PK)
- company_unique_id (uuid, NOT NULL, FK)
- domain (text, NOT NULL)
- domain_health (text, NULLABLE)
- mx_present (boolean, NULLABLE)
- checked_at (timestamptz, NULLABLE, DEFAULT now())

**Relationship**: 1:N from cl.company_identity

---

## TABLE: outreach.hub_registry (12 columns)

**PK**: hub_id (varchar(50))

**Waterfall Order** (as of v1.0):
1. Company Lifecycle (CL) - PARENT
2. Company Target (04.04.01) - ANCHOR, gates_completion = true
3. DOL Filings (04.04.03) - SUB-HUB, gates_completion = true
4. People Intelligence (04.04.02) - SUB-HUB, gates_completion = true
5. Blog Content (04.04.05) - SUB-HUB, gates_completion = false

**Key Columns**:
- hub_id (varchar(50), NOT NULL, PK)
- hub_name (varchar(100), NOT NULL)
- doctrine_id (varchar(20), NOT NULL)
- waterfall_order (integer, NOT NULL)
- gates_completion (boolean, NOT NULL, DEFAULT false)
- core_metric (varchar(50), NOT NULL)

---

## TABLE: outreach.blog (8 columns)

**PK**: blog_id (uuid)
**FK**: outreach_id → outreach.outreach.outreach_id

**Key Columns**:
- blog_id (uuid, NOT NULL, PK)
- outreach_id (uuid, NOT NULL, FK)
- source_type (text, NULLABLE) - LEGACY
- source_type_enum (USER-DEFINED, NULLABLE) - NEW: website, blog, press, news, social, filing, careers
- context_summary (text, NULLABLE)
- source_url (text, NULLABLE)
- context_timestamp (timestamptz, NULLABLE)
- created_at (timestamptz, NULLABLE, DEFAULT now())

**Migration**: source_type (text) → source_type_enum (ENUM)

---

## BIT TABLES

### bit.authorization_log
**PK**: log_id (uuid)
**Key**: company_unique_id (text, NOT NULL)

### bit.movement_events
**PK**: movement_id (uuid)
**Key**: company_unique_id (text, NOT NULL)

### bit.phase_state
**PK**: company_unique_id (text) - PK is also FK
**Pattern**: 1:1 with company

### bit.proof_lines
**PK**: proof_id (text)
**Key**: company_unique_id (text, NOT NULL)
**Link**: movement_ids (ARRAY) → bit.movement_events.movement_id

---

## KEY ENUMS FOR LEGEND

### bit.authorization_band (6 values)
```
0. SILENT (light gray)
1. WATCH (light red)
2. EXPLORATORY (medium red)
3. TARGETED (dark red)
4. ENGAGED (bright red)
5. DIRECT (deep red)
```

### outreach.lifecycle_state (8 values)
```
SUSPECT (light blue)
WARM (medium blue)
TALENTFLOW_WARM (teal)
REENGAGEMENT (orange)
APPOINTMENT (green) ← Handoff to Sales
CLIENT (gold)
DISQUALIFIED (gray)
UNSUBSCRIBED (black)
```

### outreach.hub_status_enum (4 values)
```
PASS (green)
IN_PROGRESS (yellow)
FAIL (red)
BLOCKED (orange)
```

### people.email_status_t (4 values)
```
green (green)
yellow (yellow)
red (red)
gray (gray)
```

### outreach.override_type_enum (6 values)
```
marketing_disabled
tier_cap
hub_bypass
cooldown
legal_hold
customer_requested
```

---

## RELATIONSHIPS DIAGRAM

```
cl.company_identity (sovereign_company_id)
    ↓ 1:1
outreach.outreach (sovereign_id) [PK: outreach_id]
    ↓ 1:N
    ├─ outreach.company_target (outreach_id)
    ├─ outreach.people (outreach_id)
    ├─ outreach.dol (outreach_id)
    └─ outreach.blog (outreach_id)

cl.company_identity (company_unique_id)
    ↓ 1:N
cl.company_domains (company_unique_id)

Any company_unique_id
    ← N:1
outreach.manual_overrides (company_unique_id)
    ↓ 1:N
outreach.override_audit_log (override_id)

Any company_unique_id
    ← 1:1
bit.phase_state (company_unique_id)

Any company_unique_id
    ← N:1
bit.movement_events (movement_id)
    ↓ N:N (via movement_ids[])
bit.proof_lines (movement_ids[])
```

---

## v1.0 ALIGNMENT RULE (FROZEN)

```sql
-- MUST ALWAYS BE EQUAL
SELECT COUNT(*) FROM outreach.outreach;
-- Result: 51,148

SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL;
-- Result: 51,148

-- If not equal → HARD_FAIL (sovereignty violation)
```

---

## DOCTRINE REMINDERS

1. **CL mints sovereign_company_id** (IMMUTABLE)
2. **Outreach mints outreach_id** (writes to CL ONCE)
3. **CL stores identity pointers ONLY** (never workflow state)
4. **outreach.outreach is operational spine** (workflow state lives here)
5. **All sub-hubs FK to outreach_id** (not sovereign_company_id)
6. **Kill switch via manual_overrides** (HARD_FAIL enforcement)
7. **Waterfall order enforced by hub_registry** (gates_completion blocks downstream)

---

**Full Details**: See NEON_SCHEMA_REFERENCE_FOR_ERD.md
**Corrections**: See ERD_SCHEMA_AUDIT_FINDINGS.md
**ENUMs**: See NEON_ENUM_TYPES_REFERENCE.md
**Summary**: See SCHEMA_INTROSPECTION_SUMMARY.md
