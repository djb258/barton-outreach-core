# Outreach ↔ EIN Structural Audit

## Document Metadata
| Field | Value |
|-------|-------|
| **Audit Type** | READ-ONLY STRUCTURAL AUDIT |
| **Date** | 2025-01-XX |
| **Scope** | Outreach ↔ Company Target ↔ EIN ↔ DOL |
| **Exclusions** | BIT, AIR, Analytics, Blog, People, Enrichment |
| **Purpose** | State-of-world snapshot - NOT a fix |

---

## A. ERD-Style Logical Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OUTREACH ↔ EIN BINDING CHAIN                              │
│                         (Current State)                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                  COMPANY LIFECYCLE (Sovereign)                        │
    │                     marketing.company_master                          │
    │                                                                       │
    │   company_unique_id  TEXT      PK   SOVEREIGN IDENTITY               │
    │   company_name       TEXT      REQ                                   │
    │   domain             VARCHAR   REQ  ← Anchor (Golden Rule)           │
    │   email_pattern      VARCHAR   REQ  ← Anchor (Golden Rule)           │
    │   ein                VARCHAR        ← MUTABLE! (CL-owned)            │
    │                                                                       │
    └───────────────────────────────┬──────────────────────────────────────┘
                                    │
                    FK: company_unique_id (IMMUTABLE REF)
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────────┐
│   OUTREACH.COMPANY_TARGET       │     │      DOL.EIN_LINKAGE                 │
│   (Outreach Internal Anchor)    │     │      (Append-Only EIN Facts)         │
│                                 │     │                                       │
│ target_id        UUID    PK     │     │ linkage_id         VARCHAR(50)  PK   │
│ company_unique_id TEXT   FK     │     │ company_unique_id  VARCHAR(50)  FK   │
│ outreach_status  TEXT           │     │ ein                VARCHAR(10)  REQ  │
│ bit_score_snap   INT            │     │ source             VARCHAR(50)  REQ  │
│ created_at       TIMESTAMPTZ    │     │ source_url         TEXT         REQ  │
│                                 │     │ filing_year        INTEGER      REQ  │
│ ⚠️ NO EIN COLUMN                │     │ hash_fingerprint   VARCHAR(64)  REQ  │
│ ⚠️ NO outreach_context_id       │     │ outreach_context_id VARCHAR(100) REQ │
│                                 │     │ created_at         TIMESTAMPTZ       │
└────────────────┬────────────────┘     │                                       │
                 │                       │ CONSTRAINTS:                          │
                 │                       │ • UNIQUE (company_unique_id, ein)     │
                 │                       │ • FK → company_master (RESTRICT)      │
                 │                       │ • APPEND-ONLY (trigger blocks UPDATE) │
                 │                       └───────────────────────────────────────┘
                 │                                         │
                 │                                         │
                 │ ┌───────────────────────────────────────┘
                 │ │
                 ▼ ▼
    ┌──────────────────────────────────────────────────────────────────────┐
    │               OUTREACH_CTX.CONTEXT                                    │
    │               (Disposable Execution Context)                          │
    │                                                                       │
    │   outreach_id        UUID      PK   DISPOSABLE (ephemeral)           │
    │   company_sov_id     UUID      REQ  ← SOVEREIGN REF (immutable)      │
    │   context_type       VARCHAR        run | epoch | campaign           │
    │   lifecycle_state_at_creation  VARCHAR                               │
    │   expires_at         TIMESTAMPTZ    TTL-bound                        │
    │   final_state        ENUM           PASS | FAIL | ABORTED            │
    │   total_cost_credits DECIMAL                                         │
    │                                                                       │
    │   ⚠️ company_sov_id ≠ company_unique_id (UUID vs TEXT)              │
    │   ⚠️ NO EIN COLUMN                                                   │
    │                                                                       │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## B. Table Inventory (Minimal, In-Scope Only)

| Schema | Table | Key Columns | EIN Present? | outreach_context_id Present? | Role |
|--------|-------|-------------|--------------|------------------------------|------|
| `marketing` | `company_master` | `company_unique_id` (PK), `ein` | **YES** (mutable) | ❌ NO | Sovereign identity anchor |
| `outreach` | `company_target` | `target_id` (PK), `company_unique_id` (FK) | ❌ NO | ❌ NO | Outreach internal anchor |
| `outreach_ctx` | `context` | `outreach_id` (PK), `company_sov_id` (FK) | ❌ NO | `outreach_id` IS the context | Disposable execution tracking |
| `dol` | `ein_linkage` | `company_unique_id` (FK), `ein` | **YES** (immutable) | **YES** (required) | Append-only EIN-to-company fact |
| `dol` | `violations` | `ein` (FK-ish), `company_unique_id` | **YES** (join key) | **YES** | Violation facts |
| `dol` | `form_5500` | `ein`, `sponsor_dfe_ein` | **YES** (source data) | ❌ NO | Raw DOL filing data |
| `shq` | `error_master` | `company_unique_id`, `outreach_context_id` | ❌ NO | **YES** | Error triage |

---

## C. Current Truth Summary

### C.1 Where EIN Currently Lives

| Location | Nature | Mutability | Notes |
|----------|--------|------------|-------|
| `marketing.company_master.ein` | **Mutable** field on sovereign record | ✏️ MUTABLE | CL-owned, can be updated |
| `dol.ein_linkage.ein` | **Immutable** append-only fact | 🔒 IMMUTABLE | Doctrine-enforced, trigger-protected |
| `dol.violations.ein` | Reference field | READ-ONLY (via join) | Links to `ein_linkage` |
| `dol.form_5500.ein` | Source data | READ-ONLY (source) | Raw DOL import, not normalized |

### C.2 Where `outreach_context_id` Currently Lives

| Location | Purpose | Populated? |
|----------|---------|------------|
| `dol.ein_linkage.outreach_context_id` | Tracks which context triggered EIN resolution | ✅ REQUIRED (NOT NULL) |
| `dol.violations.outreach_context_id` | Tracks which context discovered violation | ✅ REQUIRED |
| `shq.error_master.outreach_context_id` | Error context tracking | ✅ OPTIONAL (nullable) |
| `outreach_ctx.context.outreach_id` | IS the context ID | ✅ PK |

### C.3 Current Binding Status

```
QUESTION: Is there an immutable Outreach ID ↔ EIN binding?

SHORT ANSWER: PARTIAL — via dol.ein_linkage.outreach_context_id
```

#### Binding Chain Analysis

```
outreach_ctx.context.outreach_id
         │
         │ (DISPOSABLE - can expire/kill)
         │
         ▼
dol.ein_linkage.outreach_context_id ──► ein (IMMUTABLE)
         │
         │ (company_unique_id is ALSO on ein_linkage)
         │
         ▼
marketing.company_master.company_unique_id
         │
         │ (SOVEREIGN - immutable identity)
         │
         ▼
outreach.company_target.company_unique_id
```

#### What Exists Today

| Binding | Status | How |
|---------|--------|-----|
| `outreach_context_id` → `ein` | ✅ EXISTS | `dol.ein_linkage.outreach_context_id` + `dol.ein_linkage.ein` |
| `outreach_context_id` → `company_unique_id` | ✅ EXISTS | `dol.ein_linkage.outreach_context_id` + `dol.ein_linkage.company_unique_id` |
| `company_unique_id` → `ein` | ✅ EXISTS | `dol.ein_linkage` UNIQUE constraint |
| `company_target.target_id` → `ein` | ❌ MISSING | No direct path; requires JOIN through `company_unique_id` |
| `outreach_context_id` → `target_id` | ❌ MISSING | No link between context and target |

---

## D. Gaps Identified

### Gap 1: `outreach.company_target` Has No EIN Column

**Current State:**
```sql
CREATE TABLE outreach.company_target (
    target_id           UUID PRIMARY KEY,
    company_unique_id   TEXT NOT NULL,
    outreach_status     TEXT NOT NULL DEFAULT 'queued',
    bit_score_snapshot  INTEGER,
    -- NO ein column
    -- NO outreach_context_id column
);
```

**Impact:**
- To get EIN for a company target, you must JOIN:
  ```sql
  SELECT ct.target_id, el.ein
  FROM outreach.company_target ct
  JOIN dol.ein_linkage el ON ct.company_unique_id = el.company_unique_id;
  ```
- No snapshot of EIN on the outreach record itself

**Is This a Problem?**
- **NO** if doctrine says EIN is NEVER copied (only joined)
- **YES** if you need a "point-in-time" EIN binding at targeting time

---

### Gap 2: `company_sov_id` (UUID) vs `company_unique_id` (TEXT) Type Mismatch

**Current State:**
- `outreach_ctx.context.company_sov_id` is **UUID**
- `marketing.company_master.company_unique_id` is **TEXT**
- `dol.ein_linkage.company_unique_id` is **VARCHAR(50)** (text)

**Impact:**
- Cannot directly JOIN `outreach_ctx.context` to `dol.ein_linkage` without CAST
- Semantic question: Is `company_sov_id` actually `company_unique_id::uuid`?

---

### Gap 3: No Direct `target_id` → `outreach_context_id` Link

**Current State:**
- `outreach.company_target` has no `outreach_context_id` column
- `outreach_ctx.context` has no `target_id` column

**Impact:**
- To find which contexts ran against a target, you must:
  ```sql
  SELECT ct.target_id, oc.outreach_id
  FROM outreach.company_target ct
  JOIN outreach_ctx.context oc ON ct.company_unique_id = oc.company_sov_id::text;
  ```
- No direct FK path

---

### Gap 4: EIN on `company_master` is MUTABLE

**Current State:**
- `marketing.company_master.ein` can be updated
- `dol.ein_linkage.ein` is IMMUTABLE (trigger-protected)

**Impact:**
- Two sources of EIN truth:
  - **CL's view:** `company_master.ein` (current, mutable)
  - **DOL's view:** `ein_linkage.ein` (historical, immutable facts)
- If CL updates EIN, old `ein_linkage` records become stale

**Is This a Problem?**
- **NO** if doctrine says: "DOL captures EIN-at-filing-time, not current EIN"
- **YES** if expectation is single canonical EIN

---

## E. Critical Question: Can We Lock Outreach ID ↔ EIN Today?

### Evidence

1. **`dol.ein_linkage` already captures `outreach_context_id`**
   - Column exists: `outreach_context_id VARCHAR(100) NOT NULL`
   - Populated at linkage creation time

2. **`dol.ein_linkage` is IMMUTABLE**
   - Append-only enforced by trigger
   - UNIQUE constraint on `(company_unique_id, ein)`

3. **The binding exists, but it's CONTEXT → EIN, not TARGET → EIN**

### Answer

**YES, we CAN perform a one-time immutable Outreach ID ↔ EIN lock — BUT:**

| Condition | Status |
|-----------|--------|
| Lock `outreach_context_id` → `ein` | ✅ Already exists in `dol.ein_linkage` |
| Lock `company_target.target_id` → `ein` | ❌ Requires new column OR new junction table |
| Lock without re-running fuzzy | ✅ Possible — data already in `ein_linkage` |

### Options for Target ↔ EIN Lock (If Needed)

1. **Option A: Add `ein` column to `company_target`**
   - Copy from `ein_linkage` at target creation
   - ⚠️ Introduces copy/sync problem

2. **Option B: Add `target_id` column to `ein_linkage`**
   - Captures which target the EIN resolution was for
   - ⚠️ Changes immutable schema

3. **Option C: New junction table `outreach.target_ein_lock`**
   ```sql
   CREATE TABLE outreach.target_ein_lock (
       lock_id UUID PRIMARY KEY,
       target_id UUID NOT NULL REFERENCES outreach.company_target(target_id),
       ein VARCHAR(10) NOT NULL,
       locked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       source_linkage_id VARCHAR(50) REFERENCES dol.ein_linkage(linkage_id),
       UNIQUE (target_id)  -- One EIN per target
   );
   ```
   - ✅ No changes to existing tables
   - ✅ Explicit lock record

4. **Option D: Do nothing — JOIN is sufficient**
   - Use `company_unique_id` as the join key
   - Accept that EIN binding is indirect

---

## F. Summary

### What We Have

| Binding | Exists? | Immutable? |
|---------|---------|------------|
| `company_unique_id` → `ein` (via `ein_linkage`) | ✅ | ✅ |
| `outreach_context_id` → `ein` (via `ein_linkage`) | ✅ | ✅ |
| `target_id` → `ein` | ❌ (JOIN only) | N/A |
| `target_id` → `outreach_context_id` | ❌ | N/A |

### What We're Missing

1. **Direct `target_id` ↔ `ein` binding** — currently requires 2-hop JOIN
2. **Direct `target_id` ↔ `outreach_context_id` binding** — no explicit link
3. **Single EIN source of truth** — CL has mutable copy, DOL has immutable facts

### Recommendation (Descriptive, Not Prescriptive)

The current architecture supports EIN resolution via `company_unique_id` joins. The `dol.ein_linkage` table is the authoritative immutable fact store.

**If a direct `target_id` → `ein` lock is required:**
- Prefer a new junction table (`target_ein_lock`) over modifying existing tables
- Do NOT add `ein` column to `company_target` (violates DRY, introduces sync risk)

---

## G. Appendix: Key Schema Excerpts

### dol.ein_linkage (Immutable)
```sql
CREATE TABLE dol.ein_linkage (
  linkage_id VARCHAR(50) PRIMARY KEY,
  company_unique_id VARCHAR(50) NOT NULL,
  ein VARCHAR(10) NOT NULL,
  source VARCHAR(50) NOT NULL,
  source_url TEXT NOT NULL,
  filing_year INTEGER NOT NULL,
  hash_fingerprint VARCHAR(64) NOT NULL,
  outreach_context_id VARCHAR(100) NOT NULL,  -- ← KEY COLUMN
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  CONSTRAINT uq_company_ein UNIQUE (company_unique_id, ein)
);
```

### outreach.company_target (Mutable)
```sql
CREATE TABLE outreach.company_target (
    target_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_unique_id   TEXT NOT NULL,
    outreach_status     TEXT NOT NULL DEFAULT 'queued',
    bit_score_snapshot  INTEGER,
    first_targeted_at   TIMESTAMPTZ,
    last_targeted_at    TIMESTAMPTZ,
    sequence_count      INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### outreach_ctx.context (Disposable)
```sql
CREATE TABLE outreach_ctx.context (
    outreach_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_sov_id UUID NOT NULL,  -- ⚠️ UUID type, not TEXT
    context_type VARCHAR(50) NOT NULL DEFAULT 'run',
    lifecycle_state_at_creation VARCHAR(50) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    final_state outreach_ctx.final_state_enum,
    total_cost_credits DECIMAL(12, 4) NOT NULL DEFAULT 0
);
```

---

**END OF AUDIT**
