# Contexts Directory — CC-03

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-03 (Context)
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Definition

Contexts represent bounded execution contexts within the Outreach program.
The primary context is `outreach_context_id` which binds all hub operations.

## Context Authority

```
outreach_context_id
├── Minted by: Outreach Orchestration (CC-02)
├── Bound to: company_unique_id (CC-01, external)
├── Scope: Single Outreach program run
└── Immutable: Once created, cannot change binding
```

## Rules

1. **One context per run** — outreach_context_id is unique per execution
2. **Bound to sovereign** — Must reference valid company_unique_id
3. **Auditable** — All operations traceable to context
4. **Lifecycle managed** — DRAFT → ACTIVE → SUSPENDED → TERMINATED

## Context Table

```sql
-- outreach.outreach_context
outreach_context_id UUID PRIMARY KEY,
company_unique_id   UUID NOT NULL REFERENCES cl.company_identity,
created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
status              TEXT NOT NULL DEFAULT 'ACTIVE',
```

## Write Permissions

| Source | Can Write? | Notes |
|--------|------------|-------|
| CC-01 | No | External |
| CC-02 | Yes | Context creation |
| CC-03 | Yes | Self (within context) |
| CC-04 | No | Read only |
