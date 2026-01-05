# Contracts Directory — CC-03

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-03 (Context)
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Definition

Contracts define bounded configuration for spoke interfaces.
They operate at CC-03 as they scope the operational slice between hubs.

## Contained Contracts

| Contract | Hubs Connected | Direction |
|----------|----------------|-----------|
| company-people.contract.yaml | CT ↔ People | Bidirectional |
| company-dol.contract.yaml | CT ↔ DOL | Bidirectional |
| company-outreach.contract.yaml | CT ↔ Outreach | Bidirectional |
| people-outreach.contract.yaml | People ↔ Outreach | Bidirectional |
| signal-company.contract.yaml | External → CT | Ingress |

## Rules

1. **YAML format** — Contracts defined in YAML
2. **Schema locked** — Changes require ADR approval
3. **Version tracked** — Contract versions must match
4. **Bidirectional symmetry** — Both sides must agree

## Contract Schema

```yaml
contract:
  name: spoke-name
  version: "1.0.0"
  from_hub: source-hub
  to_hub: target-hub

ingress:
  payload:
    - field: type  # required/optional

egress:
  payload:
    - field: type
```
