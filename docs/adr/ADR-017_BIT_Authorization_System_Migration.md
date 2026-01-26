# ADR-017: BIT Authorization System Migration

**Status:** ACCEPTED
**Date:** 2026-01-25
**Deciders:** Dave Barton, System Architect
**Supersedes:** PRD_BIT_ENGINE.md (v2.1)

---

## Context

The current BIT (Buyer Intent Tool) Engine was designed as a **scoring system** that accumulates points from signals to rank companies by "hotness." This model has fundamental limitations:

1. **Scoring ≠ Authorization** — A high score says "this company has good attributes" but doesn't answer "what action is appropriate right now?"

2. **Static facts ≠ Movement** — Current signals reward presence of data, not change over time. A company with stable DOL filings scores the same whether they changed brokers yesterday or five years ago.

3. **Blog inflation** — Blog signals can inflate scores disproportionately, creating false urgency from press releases while ignoring structural pressure.

4. **No convergence detection** — The system sums signals without detecting whether multiple domains are pointing to the same pressure. Three unrelated signals score higher than two aligned ones.

5. **No proof chain** — Messages are generated based on score thresholds, not traceable evidence. This creates compliance risk and allows AI to fabricate justifications.

### Current Architecture

```
Signals → Weighted Sum → Score (0-100) → Tier (COLD/WARM/HOT/BURNING) → Outreach
```

| Tier | Score | Meaning |
|------|-------|---------|
| COLD | 0-24 | No outreach |
| WARM | 25-49 | Watch list |
| HOT | 50-74 | Outreach eligible |
| BURNING | 75+ | Priority outreach |

**Problems:**
- "HOT" means "has lots of signals" not "is in a decision phase"
- Blog headline can push WARM → HOT without structural backing
- No mechanism to ensure DOL authority
- No proof requirement before message send

---

## Decision

**We will migrate BIT from a scoring system to an authorization system.**

### New Mental Model

```
OLD: "Score high enough → send marketing"
NEW: "Detect phase transition → intercept with proof"
```

BIT becomes a **movement-derived authorization index** that:
- Measures convergence across domains, not signal accumulation
- Gates actions by permission bands, not quality tiers
- Requires proof lines for any contact at Band 3+
- Treats DOL as gravity (required for authority)
- Treats Blog as amplifier only (never sufficient alone)

### New Architecture

```
Movement Events → Convergence Detection → BIT Index → Band → Authorized Actions
                                                         ↓
                                              Proof Line Required (Band 3+)
                                                         ↓
                                                    Message Send
```

### Three Domains

| Domain | Source | Velocity | Trust | Role |
|--------|--------|----------|-------|------|
| STRUCTURAL_PRESSURE | DOL | Annual | Highest | Gravity — required for authority |
| DECISION_SURFACE | People | Quarterly | High | Direction — who can act |
| NARRATIVE_VOLATILITY | Blog | Weekly | Lowest | Timing — amplifier only |

### Authorization Bands

| Band | Range | Name | Key Constraint |
|------|-------|------|----------------|
| 0 | 0-9 | SILENT | No action permitted |
| 1 | 10-24 | WATCH | Internal only |
| 2 | 25-39 | EXPLORATORY | Educational, no personalization |
| 3 | 40-59 | TARGETED | Proof line required |
| 4 | 60-79 | ENGAGED | Multi-source proof required |
| 5 | 80+ | DIRECT | Full-chain proof required |

### Convergence Rules

- One domain moving = noise (max Band 1)
- Two domains aligned = watch/act (Band 2-4)
- Three domains aligned = strong phase (Band 4-5)
- Blog alone = max Band 1 (never justifies contact)
- DOL absent = max Band 2 (no authority for targeted outreach)

### Proof Line Requirement

At Band 3+, every message must have:
1. Human-readable proof line citing pressure class and evidence
2. Machine-readable proof object with traceable field values
3. Validity window that includes send time

**Format:** `[PRESSURE_CLASS] detected via [SOURCE]: [SPECIFIC_EVIDENCE]`

---

## Consequences

### Positive

1. **Outreach becomes defensible** — Every message traces to detected pressure, not vibes
2. **AI cannot fabricate urgency** — Proof must exist before message drafting
3. **DOL investment pays off** — Structural signals now carry appropriate weight
4. **Blog noise suppressed** — Press releases can't inflate priority without backing
5. **Movement beats presence** — Companies entering decision phases surface above static "good" companies
6. **Messaging is grounded** — System failure framing comes from evidence, not creativity

### Negative

1. **Volume may decrease** — Fewer companies will qualify for Band 3+ than scored HOT
2. **Complexity increases** — Movement calculation more complex than weighted sum
3. **Migration risk** — Parallel systems during transition
4. **Proof overhead** — Additional infrastructure for proof generation and validation

### Neutral

1. **Score still exists** — BIT index is still 0-100, just means something different
2. **Existing signals still used** — Same data, different interpretation
3. **Outreach execution unchanged** — Downstream systems receive authorized messages same as before

---

## Alternatives Considered

### Alternative 1: Tune Existing Weights

Adjust signal weights to favor DOL over Blog.

**Rejected because:** Still treats BIT as "goodness" score. Doesn't solve convergence detection or proof requirement.

### Alternative 2: Add Convergence as Bonus

Keep scoring, add convergence multiplier.

**Rejected because:** Grafting convergence onto accumulation model creates inconsistent semantics. "Score" still means "good" not "authorized."

### Alternative 3: Separate Authorization Layer

Keep BIT scoring, add separate authorization gate.

**Rejected because:** Creates redundant systems. If authorization is the real gate, scoring becomes vestigial.

---

## Migration Strategy

### Principle: Parallel Before Cutover

New system runs in shadow mode alongside existing scoring. Cutover only after validation.

### Phase 1: Schema Additions (Non-Breaking)

Add new tables without modifying existing:
- `bit.movement_events` — Movement event storage
- `bit.proof_lines` — Proof line storage
- `bit.authorization_log` — Action authorization audit
- `bit.phase_state` — Current phase per company

Add columns to existing:
- `bit.bit_signal.movement_class` — Classification of existing signals
- `bit.bit_signal.pressure_class` — Pressure class mapping

### Phase 2: Movement Emission

Modify hubs to emit movement events:
- DOL Hub: Emit structural pressure events with YoY comparison
- People Hub: Emit decision surface events
- Blog Hub: Already emits — add trust cap enforcement

Shadow calculation:
- Calculate both old score and new band
- Log discrepancies for analysis
- No behavior change yet

### Phase 3: Proof Line Infrastructure

Build proof generation pipeline:
- Proof line generator from movement events
- Proof validation function
- Proof attachment to messages
- Proof expiration handling

### Phase 4: Cutover

- Replace score-based gates with band-based gates
- Require proof line validation before send
- Deprecate tier terminology (COLD/WARM/HOT/BURNING)
- Archive old scoring logic

### Rollback Plan

Each phase is independently reversible:
- Phase 1: Drop new tables (no functional change)
- Phase 2: Disable movement emission (old scoring continues)
- Phase 3: Bypass proof validation (messages send without proof)
- Phase 4: Re-enable score-based gates

---

## Validation Criteria

### Phase 2 Exit Criteria
- [ ] Movement events emitting for all three domains
- [ ] Band calculation matches expected behavior on test set
- [ ] Shadow mode shows <5% unexpected discrepancies

### Phase 3 Exit Criteria
- [ ] Proof lines generating for all pressure classes
- [ ] Proof validation blocking invalid sends in test
- [ ] Machine-readable proofs trace to source records

### Phase 4 Exit Criteria
- [ ] All outreach paths check band authorization
- [ ] All Band 3+ messages have valid proof attached
- [ ] No messages sent with expired proofs
- [ ] Monitoring confirms expected volume change

---

## References

- `doctrine/ple/BIT_AUTHORIZATION_BANDS.md` — Band definitions
- `doctrine/ple/PROOF_LINE_RULE.md` — Proof requirements
- `CLAUDE.md` — AI enforcement instructions
- `docs/prd/PRD_BIT_ENGINE.md` — Superseded scoring system

---

## Approval

| Role | Name | Date |
|------|------|------|
| System Owner | Dave Barton | 2026-01-25 |
| Architect | | |

---

**Document Control:**
| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Status | ACCEPTED |
| Supersedes | PRD_BIT_ENGINE.md v2.1 |
