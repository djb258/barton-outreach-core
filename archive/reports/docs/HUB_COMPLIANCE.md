# Hub Compliance Checklist — Barton Outreach Core

This checklist must be completed before any hub can ship.
No exceptions. No partial compliance.

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **Claimed CC Layer** | CC-02 |
| **Effective CC Layer** | CC-03 (DOWNGRADED) |
| **Sovereign ID** | barton-enterprises |
| **Hub ID** | outreach-core-001 |

---

## Canonical Authority Check (FAIL-CLOSED)

> **DOCTRINE**: `claimed_cc_layer ≠ effective_cc_layer`
> CC-02 requires external delegation from upstream CC-02 or CC-01.
> Absence of proof = failure. No self-declaration allowed.

### Authority Status

| Field | Value |
|-------|-------|
| **Claimed** | CC-02 |
| **Effective** | CC-03 |
| **Delegation Status** | DOWNGRADED |
| **Reason** | No external delegation artifact from CC-01 or upstream CC-02 |

### Authority Validation Checklist

- [ ] **Delegation artifact exists** — External warrant from upstream authority
- [ ] **Artifact reference valid** — `authority.delegation.artifact_ref` in heir.doctrine.yaml
- [ ] **Upstream authority verified** — company-lifecycle-cl-001 or barton-enterprises sovereign
- [ ] **Signature valid** — Delegation artifact contains valid signature
- [ ] **Authority gate passes** — `python ops/enforcement/authority_gate.py`

### Required for CC-02 Claim

To claim CC-02, this hub must:

1. **Obtain delegation artifact** from upstream CC-02 (company-lifecycle-cl) or CC-01 (barton-enterprises)
2. **Place artifact** at specified path (e.g., `delegations/outreach-core-001.yaml`)
3. **Update heir.doctrine.yaml** with `authority.delegation.artifact_ref`
4. **Run authority gate** to validate: `python ops/enforcement/authority_gate.py`
5. **Pass CI gate** — GitHub workflow must pass before merge

### Delegation Artifact Template

```yaml
# delegations/outreach-core-001.yaml
delegation:
  delegator: "company-lifecycle-cl-001"  # Upstream authority
  delegator_cc_layer: "CC-02"
  delegatee: "outreach-core-001"         # This hub
  cc_layer_granted: "CC-02"
  scope: "Marketing intelligence and outreach execution"
  constraints:
    - "Must reference company_unique_id from CL"
    - "No identity minting"
    - "Read-only access to cl.* schema"
  issued_at: "2026-01-05T00:00:00Z"
  expires_at: null  # null = no expiration
  signature: "<signed-by-upstream-authority>"
```

### Current Status: ⚠️ DOWNGRADED

This hub currently operates at **CC-03** (Context) until a valid delegation artifact is provided.
All CC-02 claims in documentation are **aspirational**, not **effective**.

---

## Canonical Chain (CC) Compliance

- [x] Sovereign declared (CC-01 reference)
- [x] Hub ID assigned (unique, immutable) (CC-02)
- [x] All child contexts scoped to CC-03
- [x] All processes scoped to CC-04
- [x] Authorization matrix honored (no upward writes)
- [x] Doctrine version declared

---

## Hub Identity (CC-02)

- [x] Hub ID assigned: `outreach-core-001`
- [x] Process ID pattern defined: `outreach-core-001-${TIMESTAMP}-${RANDOM_HEX}`
- [x] Hub Name defined: `outreach-core`
- [x] Hub Owner assigned: Outreach Team

---

## CTB Placement

- [x] CTB path defined: `barton/outreach/core`
- [x] Branch level specified: `outreach`
- [ ] Parent hub identified (if nested hub): N/A - this is root hub

---

## IMO Structure

### Ingress (I Layer)

- [x] Ingress points defined (CL identity, CSV intake, API responses)
- [x] Ingress contains no logic
- [x] Ingress contains no state
- [x] UI (if present) is dumb ingress only

### Middle (M Layer)

- [x] All logic resides in M layer
- [x] All state resides in M layer
- [x] All decisions occur in M layer
- [x] Tools scoped to M layer only

### Sub-Hubs (CC-03 Contexts within M Layer)

| Sub-Hub | Hub ID | Doctrine ID | Status |
|---------|--------|-------------|--------|
| Company Target | HUB-CT-001 | 04.04.01 | [x] Compliant |
| People Intelligence | HUB-PI-001 | 04.04.02 | [x] Compliant |
| DOL Filings | HUB-DOL-001 | 04.04.03 | [x] Compliant |
| Outreach Execution | HUB-OE-001 | 04.04.04 | [x] Compliant |
| Blog Content | HUB-BC-001 | 04.04.05 | [x] Compliant |

### Egress (O Layer)

- [x] Egress points defined (campaign output, analytics signals)
- [x] Egress contains no logic
- [x] Egress contains no state

---

## Spokes

- [x] All spokes typed as I or O only
- [x] No spoke contains logic
- [x] No spoke contains state
- [x] No spoke owns tools
- [x] No spoke performs decisions

### Spoke Registry

| Spoke Name | Type | Direction | Contract |
|------------|------|-----------|----------|
| cl-identity | I | Inbound | contracts/cl-identity.contract.yaml |
| intake-csv | I | Inbound | contracts/intake-csv.contract.yaml |
| campaign-output | O | Outbound | contracts/campaign-output.contract.yaml |
| analytics-signal | O | Outbound | contracts/analytics-signal.contract.yaml |

---

## Tools

- [x] All tools scoped inside this hub
- [x] All tools have Doctrine ID
- [x] All tools have ADR reference
- [x] No tools exposed to spokes

### Tool Registry

| Tool | Solution Type | CC Layer | IMO Layer |
|------|---------------|----------|-----------|
| BIT Engine | Deterministic | CC-02 | M |
| Email Pattern Waterfall | LLM-tail | CC-02 | M |
| Domain Resolution | Deterministic | CC-02 | M |
| Slot Assignment | Deterministic | CC-02 | M |
| EIN Matcher | Deterministic | CC-02 | M |

---

## Connectors

- [x] Connectors (API / CSV / Event) defined
- [x] Connector direction specified (Inbound / Outbound)
- [x] Connector contracts documented

### Connector Registry

| Connector | Direction | Type | CC Layer |
|-----------|-----------|------|----------|
| Neon PostgreSQL | Bidirectional | Database | CC-04 |
| CSV Intake | Inbound | File | CC-03 |
| Composio MCP | Bidirectional | API | CC-04 |

---

## Cross-Hub Isolation

- [x] No sideways hub-to-hub calls
- [x] No cross-hub logic
- [x] No shared mutable state between hubs

---

## Guard Rails

- [x] Rate limits defined
- [x] Timeouts defined
- [x] Validation implemented
- [x] Permissions enforced

---

## Kill Switch

- [x] Kill switch endpoint defined
- [x] Kill switch activation criteria documented
- [x] Kill switch tested and verified
- [x] Emergency contact assigned

---

## Rollback

- [x] Rollback plan documented
- [x] Rollback tested and verified

---

## Observability

- [x] Logging implemented (public.shq_error_log)
- [x] Metrics implemented
- [x] Alerts configured
- [x] Shipping without observability is forbidden

---

## Failure Modes

- [x] Failure modes documented
- [x] Severity levels assigned
- [x] Remediation steps defined

---

## Human Override

- [x] Override conditions defined
- [x] Override approvers assigned

---

## Traceability

- [x] PRD exists and is current (CC-02): docs/prd/PRD_COMPANY_HUB.md
- [x] ADR exists for each decision (CC-03): docs/adr/ADR-001_Hub_Spoke_Architecture.md
- [x] Work item linked
- [x] PR linked (CC-04)
- [x] Canonical Doctrine referenced: templates/doctrine/CANONICAL_ARCHITECTURE_DOCTRINE.md

---

## CC Layer Verification

| Layer | Verified | Notes |
|-------|----------|-------|
| CC-01 (Sovereign) | [x] | barton-enterprises declared |
| CC-02 (Hub) | [x] | Identity, PRD, CTB complete |
| CC-03 (Context) | [x] | ADRs, spokes, guard rails defined |
| CC-04 (Process) | [x] | PIDs, code, tests implemented |

---

## Compliance Rule

If any box is unchecked, this hub may not ship.

---

## Traceability Reference

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | templates/doctrine/CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | templates/doctrine/HUB_SPOKE_ARCHITECTURE.md |
| CC Descent Protocol | templates/doctrine/ALTITUDE_DESCENT_MODEL.md |
| HEIR Configuration | heir.doctrine.yaml |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-05 |
| Last Modified | 2026-01-05 |
| Doctrine Version | 1.1.0 |
| Claimed CC Layer | CC-02 |
| Effective CC Layer | CC-03 |
| Authority Status | DOWNGRADED |
| Status | PARTIAL — Awaiting delegation artifact |
