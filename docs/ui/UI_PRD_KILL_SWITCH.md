# UI PRD — Kill Switch System

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_KILL_SWITCH_SYSTEM.md
**Generated**: 2026-01-29

---

## UI Identity

| Field | Value |
|-------|-------|
| **UI Name** | Kill Switch Console |
| **Owning Hub** | HUB-OUTREACH-001 (Kill Switch component) |
| **Canonical PRD** | docs/prd/PRD_KILL_SWITCH_SYSTEM.md |
| **Type** | Event-emitting (CRITICAL) |

---

## Explicit Exclusions

This UI does NOT:

- Directly modify manual_overrides table
- Bypass audit logging
- Execute marketing actions
- Determine override validity

---

## Screens / Views

| Screen | Type | Description |
|--------|------|-------------|
| Override List | Read-only | Current active overrides |
| Override Form | Event-emitting | Form to request override |
| Audit Log | Read-only | override_audit_log history |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| Active overrides | outreach.manual_overrides | SELECT |
| Audit history | outreach.override_audit_log | SELECT |
| Company context | outreach.company_target | SELECT |

---

## Events Emitted

| Event | Trigger | Destination |
|-------|---------|-------------|
| `request_override` | User submits form | Backend API (audited) |
| `remove_override` | User clicks remove | Backend API (audited) |

**CRITICAL**: All override events MUST be audited. UI emits event; backend enforces audit.

---

## Failure States

| Failure | Display |
|---------|---------|
| Override rejected | "Override request denied: [reason]" |
| Audit failure | "Cannot proceed without audit. Contact admin." |
| Company not found | "Company not found" message |

---

## Forbidden Behaviors

- Directly writing to manual_overrides
- Bypassing audit logging
- Approving own override requests
- Modifying audit log
