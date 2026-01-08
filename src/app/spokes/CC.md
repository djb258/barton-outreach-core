# Spokes Directory — I/O Interface

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: None (Interface only)
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Definition

Spokes are **interfaces**, not components with CC layer assignment.

- Spokes carry data; they contain no logic
- Spokes do not own state
- Spokes are typed as Ingress or Egress

## Contained Spokes

| Spoke | Direction | From → To |
|-------|-----------|-----------|
| company-people | Bidirectional | CT ↔ People |
| company-dol | Bidirectional | CT ↔ DOL |
| company-outreach | Bidirectional | CT ↔ Outreach |
| people-outreach | Bidirectional | People ↔ Outreach |
| signal-company | Ingress | External → CT |

## Rules

1. **No logic** — Pass-through only
2. **No state** — Stateless transport
3. **No spoke-to-spoke** — Route through hub
4. **Typed** — Ingress or Egress, never both in one file

## Structure

```
spoke/
├── __init__.py     # Spoke exports
├── ingress.py      # Incoming data handler
└── egress.py       # Outgoing data handler
```

## Violation

Any spoke containing business logic is a **HUB_SPOKE_VIOLATION**.
