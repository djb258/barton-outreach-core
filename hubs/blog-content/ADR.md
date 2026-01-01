# ADR: Blog Content — Signals Only, No Authority

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-BLOG-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |

---

## Context

Content signals (funding, acquisitions, leadership changes) provide valuable
timing information, but should not create authority over company existence.

---

## Decision

Blog Content is a **signal-only hub**:
- Emits BIT signals for timing optimization
- Cannot mint or revive companies
- Cannot trigger enrichment
- Lifecycle read-only

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Allow company creation from news | Would violate single-authority |
| Trigger enrichment on signals | Would bypass cost controls |
| Do Nothing | Would miss timing opportunities |

---

## Consequences

### Enables

- Timing optimization via BIT signals
- Clean separation of signal vs authority
- Safe integration of news sources

### Prevents

- Duplicate company creation
- Uncontrolled enrichment
- Authority conflicts

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |
