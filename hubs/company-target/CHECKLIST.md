# Company Target — Compliance Checklist

**DOCTRINE LOCK**: This checklist is the freeze line for Company Target.
No code ships unless every box is checked. No exceptions. No partial compliance.

---

## 0. CL Upstream Gate (FIRST CHECK)

> Outreach assumes Company Life Cycle existence verification has already passed.
> Outreach will not execute without an `EXISTENCE_PASS` signal.

### Gate Enforcement

- [ ] `CLGate.enforce_or_fail()` called BEFORE any Company Target logic
- [ ] Checks `company_sov_id` exists in `cl.company_identity`
- [ ] EXISTS → `EXISTENCE_PASS` → proceed to Phase 1
- [ ] MISSING → Write `CT_UPSTREAM_CL_NOT_VERIFIED` error → STOP

### Explicit Prohibitions

- [ ] Does NOT implement CL existence checks (domain resolution, name coherence, state matching)
- [ ] Does NOT add CL error tables
- [ ] Does NOT retry or "repair" missing CL signals
- [ ] Does NOT infer existence from domains, LinkedIn, or names
- [ ] Does NOT soft-fail or partially proceed

### Error Routing

- [ ] Missing CL company → `outreach_errors.company_target_errors`
- [ ] `failure_code`: `CT_UPSTREAM_CL_NOT_VERIFIED`
- [ ] `pipeline_stage`: `upstream_cl_gate`
- [ ] `severity`: `blocking`
- [ ] Error terminates execution immediately

---

## 1. Hard Input Contract (MANDATORY)

### Required Inputs

- [ ] `company_unique_id` received (read-only, pre-minted from CL)
- [ ] `outreach_id` received (MANDATORY, cost + retry scope)
- [ ] `correlation_id` received (MANDATORY, tracing only)

### Input Validation

- [ ] FAIL IMMEDIATELY if `outreach_id` is missing
- [ ] FAIL IMMEDIATELY if `company_sov_id` is missing
- [ ] FAIL IMMEDIATELY if `correlation_id` is missing
- [ ] No identity minting (CL owns company_unique_id)

---

## 2. Phase Order (IMMUTABLE)

Phases MUST execute in this exact order. No skipping, no reordering.

### Phase 1 — Company Matching (READ-ONLY)

- [ ] Match against `company_master` only
- [ ] GOLD: Exact domain match (score = 1.0)
- [ ] SILVER: Exact name match (score = 0.95)
- [ ] BRONZE: Fuzzy + city guard (0.85–0.92)
- [ ] BRONZE+: Fuzzy >= 0.92 (no city required)
- [ ] Collision threshold = 0.03 score difference
- [ ] Collision resolution: Abacus.ai Fuzzy Arbitrator (Tool 3) ONLY
- [ ] NO other LLM allowed in pipeline
- [ ] No match minting
- [ ] No writes upstream

### Phase 2 — Domain Resolution (FREE ONLY)

- [ ] Domain from `company_master` first
- [ ] Domain from input record fallback
- [ ] DNS validation
- [ ] MX validation
- [ ] No valid domain → `needs_enrichment = true` → FAIL COMPANY_TARGET

### Phase 3 — Email Pattern Waterfall (COST-FIRST)

#### Tier 0 (FREE) — REQUIRED

- [ ] Firecrawl
- [ ] Google Places / public web scrape
- [ ] Zero cost only

#### Tier 1 (LOW COST) — BUDGET-GATED

- [ ] Hunter.io
- [ ] Clearbit
- [ ] Apollo
- [ ] Allowed only if Tier 0 FAILS
- [ ] Tier-1 spend cap for `outreach_id` not exceeded

#### Tier 2 (PREMIUM) — SINGLE-SHOT

- [ ] Prospeo
- [ ] Snov
- [ ] Clay
- [ ] Requires `can_attempt_tier2(outreach_id) == TRUE`
- [ ] **ONE Tier-2 attempt per outreach_id TOTAL**
- [ ] If Tier-2 fails → no retry, no alternate provider

#### Waterfall Behavior

- [ ] Waterfall stops on first successful pattern discovery
- [ ] Cost-first: Exhaust cheaper signals before spending more

### Phase 4 — Pattern Verification (CHEAP FIRST)

- [ ] Match against known valid emails (free)
- [ ] MX / catch-all check (free)
- [ ] SMTP probe only if non–catch-all
- [ ] Emit `email_pattern`
- [ ] Emit `pattern_verified = PASS | FAIL`
- [ ] Emit `catch_all_flag`
- [ ] Emit `confidence_score` (metadata only)
- [ ] **Decision is binary. Confidence NEVER upgrades a FAIL.**

---

## 3. Cost & Logging Doctrine (NON-NEGOTIABLE)

### Tool Context Enforcement

- [ ] Every paid tool call includes `outreach_id`
- [ ] Every paid tool call includes `company_sov_id`
- [ ] All spend logged per context, not global
- [ ] `correlation_id` is for tracing only — never cost logic

### Tier-2 Single-Shot Enforcement

- [ ] `can_attempt_tier2()` called before EVERY Tier-2 provider call
- [ ] Tier-2 returns early if guard returns FALSE
- [ ] No fallback to alternate Tier-2 provider on guard block
- [ ] `log_tool_attempt()` called after EVERY paid tool call

### Cost Logging

- [ ] All tool attempts logged to `outreach_ctx.tool_attempts`
- [ ] All spend logged to `outreach_ctx.spend_log`
- [ ] Missing context = HARD FAIL

---

## 4. Output Contract (STRICT)

Must emit exactly:

- [ ] `company_unique_id`
- [ ] `outreach_id`
- [ ] `email_pattern` (or null)
- [ ] `email_domain_status`
- [ ] `pattern_verified` (PASS | FAIL)
- [ ] `catch_all_flag`
- [ ] `cost_summary`
- [ ] `failure_reason` (if FAIL)

No partial success. No soft states.

---

## 5. Forbidden Actions

- [ ] **NO** identity minting
- [ ] **NO** people-level verification
- [ ] **NO** retry loops
- [ ] **NO** tool escalation for "accuracy"
- [ ] **NO** writing upstream tables
- [ ] **NO** lifecycle state mutations
- [ ] **NO** reviving dead companies

---

## 6. Kill Switch

Pipeline MUST exit immediately if:

- [ ] Domain invalid
- [ ] Cost guards violated
- [ ] Tier-2 exhausted
- [ ] Verification FAILS
- [ ] Missing context ID
- [ ] Missing sovereign ID

---

## 7. Error Handling Compliance

### When Errors Are Emitted

- [ ] CL gate failure → `CT_UPSTREAM_CL_NOT_VERIFIED` error
- [ ] Phase 1 match failure → `CT_MATCH_*` error
- [ ] Phase 2 domain failure → `CT_DOMAIN_*` error
- [ ] Phase 3 pattern failure → `CT_PATTERN_*` or `CT_TIER2_EXHAUSTED`
- [ ] Phase 4 verification failure → `CT_VERIFICATION_*` error
- [ ] Lifecycle gate failure → `CT_LIFECYCLE_GATE_FAIL`
- [ ] Missing identity → `CT_MISSING_SOV_ID` or `CT_MISSING_CONTEXT_ID`

### Blocking Failures

A failure is **blocking** if:

- [ ] CL upstream gate fails (company not in CL)
- [ ] No company match found (cannot proceed without anchor)
- [ ] Domain unresolved after all attempts
- [ ] Pattern not found after Tier-2 exhausted
- [ ] Lifecycle gate not met
- [ ] Missing sovereign ID or context ID

### Resolution Authority

| Error Type | Resolver |
|------------|----------|
| CL gate errors | CL repo (create company in CL first) |
| Match errors | Human (investigate source) |
| Domain errors | Agent (retry with new context) |
| Pattern errors | Human (manual research) |
| Lifecycle errors | Wait (automatic on state change) |
| Provider errors | Agent (retry with new context) |

### Error Table

- [ ] All failures written to `outreach_errors.company_target_errors`
- [ ] Error terminates execution immediately
- [ ] Spend frozen for context on blocking error

---

## 8. Signal Validity Compliance

### Execution Order

- [ ] Executes FIRST in canonical order
- [ ] No upstream sub-hub dependencies (CL is external)
- [ ] Verifies CL lifecycle_state >= ACTIVE before proceeding

### Signal Origin

- [ ] company_sov_id sourced from Company Lifecycle only
- [ ] lifecycle_state sourced from Company Lifecycle only
- [ ] No signals consumed from DOL, People, or Blog

### Signal Validity

- [ ] Signals are origin-bound (declared source only)
- [ ] Signals are run-bound to current outreach_id
- [ ] Signals from prior contexts are NOT authoritative
- [ ] Signal age does NOT justify action

### Non-Refreshing

- [ ] Does NOT re-query CL for "fresher" data within same context
- [ ] Does NOT re-enrich on stale signal
- [ ] Missing signal → FAIL (not retry)

### Downstream Effects

- [ ] On PASS: DOL Filings may execute
- [ ] On FAIL: DOL, People, Blog do NOT execute
- [ ] FAIL propagates forward (no skip-and-continue)

---

## 9. Kill-Switch Compliance

### UNKNOWN_ERROR Doctrine

- [ ] `CT_UNKNOWN_ERROR` triggers immediate FAIL
- [ ] Context is finalized with `final_state = 'FAIL'`
- [ ] Spend is frozen for that context
- [ ] Alert sent to on-call (PagerDuty/Slack)
- [ ] Stack trace captured in error table
- [ ] Human investigation required before retry

### Cross-Hub Repair Rules

| Downstream Error | Resolution Required |
|------------------|---------------------|
| `PI_NO_PATTERN_AVAILABLE` | Resolve CT pattern discovery first |
| `OE_MISSING_DOMAIN` | Resolve CT domain resolution first |
| `OE_MISSING_PATTERN` | Resolve CT pattern discovery first |

### SLA Aging

- [ ] `sla_expires_at` enforced for all contexts
- [ ] Auto-ABORT on SLA expiry
- [ ] `outreach_ctx.abort_expired_sla()` runs every 5 minutes

---

## 10. Repair Doctrine Compliance

### History Immutability

- [ ] Error rows are never deleted (only `resolved_at` set)
- [ ] Signals once emitted are never modified
- [ ] Prior contexts are never edited or reopened
- [ ] Cost logs are never adjusted retroactively

### Repair Scope

- [ ] This hub repairs only CT_* errors
- [ ] Does NOT repair PI_*, DOL_*, OE_*, BC_* errors
- [ ] Repairs unblock, they do not rewrite

### Context Lineage

- [ ] All retries create new `outreach_id`
- [ ] New contexts do NOT inherit signals from prior contexts
- [ ] Prior context remains for audit (never deleted)

---

## 11. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [ ] All paid tools called with `outreach_id`
- [ ] All tools listed in `tooling/tool_registry.md`
- [ ] Tier-2 tools use `can_attempt_tier2()` guard

### Hub Boundaries (DG-003)

- [ ] No imports from downstream hubs (DOL, People, Blog)
- [ ] No lateral hub-to-hub imports (only spoke imports)

### Doctrine Sync (DG-005, DG-006)

- [ ] PRD changes accompanied by CHECKLIST changes
- [ ] Error codes registered in `docs/error_codes.md`

### Signal Validity (DG-007, DG-008)

- [ ] No old/prior context signal usage
- [ ] No signal refresh patterns

### Immutability (DG-009, DG-010, DG-011, DG-012)

- [ ] No lifecycle state mutations
- [ ] No error row deletions
- [ ] No context resurrection
- [ ] No signal mutations

### Tier-2 Guard (DG-013, DG-014)

- [ ] Phase 3 calls `can_attempt_tier2()` before Tier-2 providers
- [ ] Phase 3 calls `log_tool_attempt()` after every paid tool

---

## 12. External CL + Program Scope Compliance

### CL is External

- [ ] Understands CL is NOT part of Outreach program
- [ ] Does NOT invoke Company Lifecycle (CL is external)
- [ ] Does NOT gate on CL operations (CL already verified existence)
- [ ] Consumes company_unique_id as read-only input

### Outreach Context Authority

- [ ] outreach_id sourced from Outreach Orchestration (not CL)
- [ ] All operations bound by outreach_id
- [ ] Does NOT mint outreach_id (Orchestration does)
- [ ] Reads from outreach.outreach_context table

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | Company Target | CONSUME company_unique_id |
| Orchestration | Company Target | CONSUME outreach_id |
| DOL (downstream) | Company Target | EMIT domain, verified_pattern |

### Explicit Prohibitions

- [ ] Does NOT call CL APIs or endpoints
- [ ] Does NOT verify company existence (CL did that)
- [ ] Does NOT retry CL operations
- [ ] Does NOT create outreach_id

---

## Prime Directive

> **Cost containment is a hard gate. Accuracy is a tiebreaker, not a justification to spend.**

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-02
**Hub**: Company Target (04.04.01)
**Doctrine Version**: 1.0
