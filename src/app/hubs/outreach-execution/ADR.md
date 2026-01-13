# ADR: Outreach Golden Rule

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-OE-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OE-001 |

---

## Context

Outreach without proper anchors (company identity, domain, email pattern)
results in bounces, spam complaints, and wasted effort.

---

## Decision

The **Golden Rule** enforced at Outreach Execution:

```
IF company_sov_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
```

No exceptions. No overrides. No workarounds.

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Soft validation | Would allow bad outreach |
| Warning only | Would be ignored |
| Do Nothing | Would cause deliverability issues |

---

## Consequences

### Enables

- High deliverability
- Clean sender reputation
- Zero wasted sends

### Prevents

- Bounces from bad emails
- Spam complaints
- Reputation damage

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |
