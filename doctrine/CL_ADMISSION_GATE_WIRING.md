# CL Admission Gate Wiring (Minimal)

**Status**: LOCKED
**Complexity**: MINIMAL — One rule, no abstractions

---

## The Rule (This Is the Whole Game)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   CL creates a company_unique_id ONLY IF:                                   │
│                                                                             │
│       domain IS NOT NULL                                                    │
│       OR                                                                    │
│       linkedin_url IS NOT NULL                                              │
│                                                                             │
│   Otherwise: REJECT. Do nothing. Stop.                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What CL Records (On Admit)

| Field | Description |
|-------|-------------|
| `company_unique_id` | Generated UUID |
| `name` | Company name |
| `domain` | If present |
| `linkedin_url` | If present |
| `source` | Where it came from |
| `created_at` | Timestamp |

That's it.

---

## What CL Does NOT Do

- No fuzzy matching
- No cleanup
- No retries
- No confidence scoring
- No remediation
- No execution
- No enrichment
- No "maybe later"
- No "pending"
- No "temporary"

If the data isn't there → **reject and stop**.

---

## Schema (Conceptual)

### CL Identity Table

```
cl.company_identity
├── company_unique_id   UUID PRIMARY KEY (generated on admit)
├── name                TEXT NOT NULL
├── domain              TEXT (nullable)
├── linkedin_url        TEXT (nullable)
├── source              TEXT NOT NULL
├── created_at          TIMESTAMPTZ DEFAULT now()
└── CONSTRAINT chk_admission_gate
    CHECK (domain IS NOT NULL OR linkedin_url IS NOT NULL)
```

The `CHECK` constraint IS the admission gate.
No application logic needed. The database enforces it.

### Outreach FK (Fail-Closed)

```
outreach.company_target
├── target_id           UUID PRIMARY KEY
├── company_unique_id   UUID REFERENCES cl.company_identity(company_unique_id)
│                       ↑ Can only reference ADMITTED identities
│                       ↑ If CL rejected, this FK cannot exist
└── ...
```

If CL didn't mint an ID, Outreach cannot reference it. Period.

---

## CI Guard

**File**: `.github/workflows/constitutional-hub-guard.yml`

Add one check:

```yaml
- name: CL Admission Gate Constraint Check
  run: |
    # Verify CHECK constraint exists on cl.company_identity
    # Verify constraint enforces: domain IS NOT NULL OR linkedin_url IS NOT NULL
    # FAIL if constraint is missing or weakened
```

---

## Rejection Handling

### What Happens on Reject

Nothing.

- No CL record created
- No `company_unique_id` minted
- No tombstone (unnecessary complexity)
- No retry queue (Outreach's problem)

The record stays in Outreach. Outreach decides what to do with it.

### Why No Tombstone

Tombstones add:
- State to track
- Logic to check
- Complexity to maintain

The CHECK constraint already prevents bad data.
If Outreach resubmits the same junk, the CHECK fails again.
No tombstone needed.

---

## Guard Rail Summary

| Layer | Mechanism | Enforces |
|-------|-----------|----------|
| Database | CHECK constraint | Domain OR LinkedIn required |
| Database | FK constraint | Only admitted IDs referenceable |
| CI | Guard workflow | Constraint exists and is correct |

Three lines of defense. All fail-closed. No application logic.

---

## Validation

Confirm:

- [ ] CHECK constraint on `cl.company_identity` enforces domain OR linkedin_url
- [ ] Outreach FK references only admitted CL identities
- [ ] CI guard verifies constraint exists
- [ ] No fuzzy matching anywhere
- [ ] No retry/remediation logic in CL
- [ ] No tombstones (simplicity preserved)

---

## Doctrine Confirmation

> **"CL creates a company_unique_id only if domain OR linkedin_url exists. Otherwise, nothing happens."**

```
IF domain IS NULL AND linkedin_url IS NULL:
    REJECT
    STOP
    DO NOTHING
ELSE:
    MINT company_unique_id
    RECORD identity
```

No exceptions. No workarounds. No "temporary" solutions.

---

**END OF WIRING**
