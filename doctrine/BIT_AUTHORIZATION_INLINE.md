# BIT Authorization — Abbreviated Inline Context

> Drop this in context when full CLAUDE.md is too heavy.

---

## The One Rule

BIT is an **authorization index**, not a lead score. It determines what actions are **PERMITTED**.

---

## Three Domains

| Domain | Hub | Trust | Role |
|--------|-----|-------|------|
| STRUCTURAL_PRESSURE | DOL | Highest | Gravity (required) |
| DECISION_SURFACE | People | Medium | Direction |
| NARRATIVE_VOLATILITY | Blog | Lowest | Amplifier only |

---

## Convergence

- 1 domain moving = noise
- 2 domains moving = watch
- 3 domains aligned = act
- **Blog alone = max Band 1**
- **No DOL = max Band 2**

---

## Bands

| Band | Range | Name | Permitted | Proof |
|------|-------|------|-----------|-------|
| 0 | 0-9 | SILENT | Nothing | No |
| 1 | 10-24 | WATCH | Internal only | No |
| 2 | 25-39 | EXPLORATORY | 1 educational / 60d | No |
| 3 | 40-59 | TARGETED | Persona email, 3-touch | Single |
| 4 | 60-79 | ENGAGED | Phone + 5-touch | Multi |
| 5 | 80+ | DIRECT | Full contact | Full-chain |

---

## Proof Format

**Band 3:** `[PRESSURE] via [SOURCE]: [EVIDENCE]`
**Band 4:** `[PRESSURE] convergence: [DOL] + [PEOPLE] + [BLOG?]`
**Band 5:** `PHASE TRANSITION: [PRESSURE] — [ALL] — Window: [X] days`

---

## Pressure Classes

- **COST_PRESSURE** — cost visibility gap
- **VENDOR_DISSATISFACTION** — broker churn, knowledge reset
- **DEADLINE_PROXIMITY** — compressed decisions
- **ORGANIZATIONAL_RECONFIGURATION** — knowledge loss
- **OPERATIONAL_CHAOS** — compliance gaps

---

## Hard Rules

1. No message without band authorization
2. No message exceeding band permissions
3. No Band 3+ without proof line
4. Lead with **system failure**, not product
5. Never use Blog alone to justify contact

---

## Code Pattern

```python
band = bit.get_current_band(company_id)
if band < required_band:
    raise UnauthorizedOutreachError()
if band >= 3:
    proof = bit.get_valid_proof(company_id, band)
    if not proof:
        raise MissingProofLineError()
```

---

## Never Do

- Create outreach without checking band
- Fabricate or backfill proof lines
- Use Blog alone to justify contact
- Escalate band without new movement
- Send with expired proof
- Copy proof between companies
- Use urgency language below Band 5
- Mention pricing without discovery
- Frame insurance as the product

---

**Ref:** ADR-017, `doctrine/ple/BIT_AUTHORIZATION_BANDS.md`, `doctrine/ple/PROOF_LINE_RULE.md`
