# Outreach Execution — Compliance Checklist

**DOCTRINE LOCK**: This checklist is the freeze line for Outreach Execution.
No code ships unless every box is checked. No exceptions. No partial compliance.

---

## 0. CL Upstream Gate (FIRST CHECK)

> Outreach Execution assumes Company Life Cycle existence verification has already passed.
> Outreach Execution will not execute without an `EXISTENCE_PASS` signal from CL.

### Gate Enforcement

- [ ] `CLGate.enforce_or_fail()` called BEFORE any Outreach Execution logic
- [ ] Checks `company_unique_id` exists in `cl.company_identity`
- [ ] EXISTS → `EXISTENCE_PASS` → proceed
- [ ] MISSING → Write `OE_UPSTREAM_CL_NOT_VERIFIED` error → STOP

### Explicit Prohibitions

- [ ] Does NOT implement CL existence checks
- [ ] Does NOT add CL error tables
- [ ] Does NOT retry or "repair" missing CL signals
- [ ] Does NOT infer existence from domains or names
- [ ] Does NOT soft-fail or partially proceed

### Error Routing

- [ ] Missing CL company → `outreach.outreach_errors`
- [ ] `failure_code`: `OE_UPSTREAM_CL_NOT_VERIFIED`
- [ ] `pipeline_stage`: `upstream_cl_gate`
- [ ] `severity`: `blocking`
- [ ] Error terminates execution immediately

---

## 1. Hard Input Contract (MANDATORY)

### Required Inputs

- [ ] `company_unique_id` received (read-only, pre-minted from CL)
- [ ] `outreach_context_id` received (MANDATORY, cost + retry scope)
- [ ] `correlation_id` received (MANDATORY, tracing only)
- [ ] `outreach_id` received (from outreach.outreach table)

### Input Validation

- [ ] FAIL IMMEDIATELY if `outreach_context_id` is missing
- [ ] FAIL IMMEDIATELY if `company_unique_id` is missing
- [ ] FAIL IMMEDIATELY if `correlation_id` is missing
- [ ] No identity minting (CL owns company_unique_id)

---

## 2. Upstream Dependencies (MANDATORY)

### All Upstream Hubs Must PASS

Outreach Execution is the FINAL hub in the waterfall. It requires PASS from:

- [ ] Company Target (04.04.01) - domain + email pattern
- [ ] DOL Filings (04.04.03) - EIN + filing signals
- [ ] People Intelligence (04.04.02) - contacts + slots

### Golden Rule Validation

- [ ] `company_unique_id` exists and is valid
- [ ] `domain` exists (from Company Target)
- [ ] `email_pattern` exists (from Company Target)
- [ ] At least ONE contact available (from People Intelligence)
- [ ] BIT score >= WARM_THRESHOLD (25)

---

## 3. Lifecycle State Gate (MANDATORY)

### Targetable State Required

- [ ] Company lifecycle_state >= `TARGETABLE`
- [ ] If lifecycle_state == `CHURNED` → BLOCKED
- [ ] If lifecycle_state == `DO_NOT_CONTACT` → BLOCKED
- [ ] If lifecycle_state == `CLIENT` → BLOCKED (different flow)

### State Transitions (READ-ONLY)

- [ ] Does NOT mutate lifecycle_state
- [ ] Does NOT promote to SALES
- [ ] Does NOT promote to CLIENT
- [ ] Only RECORDS engagement signals

---

## 4. BIT Score Gate (MANDATORY)

### BIT Threshold Enforcement

- [ ] BIT score checked BEFORE campaign creation
- [ ] COLD (0-24) → BLOCKED (no outreach)
- [ ] WARM (25-49) → ALLOWED (standard cadence)
- [ ] HOT (50-74) → ALLOWED (accelerated cadence)
- [ ] BURNING (75+) → ALLOWED (priority cadence)

### BIT Score Source

- [ ] BIT score from `outreach.bit_scores` table
- [ ] Score includes signals from all upstream hubs
- [ ] Decay applied to stale signals
- [ ] No manual score overrides

---

## 5. Campaign Execution Rules (IMMUTABLE)

### Campaign Creation

- [ ] Campaign requires valid `target_id`
- [ ] Campaign requires valid `person_id`
- [ ] Campaign requires verified email
- [ ] Campaign respects daily send limits
- [ ] Campaign respects total send limits

### Sequence Execution

- [ ] Sequences execute in `sequence_order`
- [ ] Delay rules enforced (`delay_days`, `delay_hours`)
- [ ] Send time preference respected
- [ ] No skipping sequence steps

### Cooling Off Period

- [ ] Respect cooling off after bounce
- [ ] Respect cooling off after spam flag
- [ ] Respect cooling off after unsubscribe
- [ ] No outreach during cooling off

---

## 6. Contact Selection Rules (IMMUTABLE)

### Contact Requirements

- [ ] Contact must have verified email
- [ ] Contact must be assigned to valid slot
- [ ] Contact must not be in cooling off
- [ ] Contact must not be unsubscribed

### Selection Priority

- [ ] CEO slot prioritized first
- [ ] CFO slot second priority
- [ ] HR slot third priority
- [ ] Selection respects BIT score

---

## 7. Send Execution (STRICT)

### Pre-Send Validation

- [ ] Email address verified (not just formatted)
- [ ] Domain MX records valid
- [ ] Not a catch-all domain (unless allowed)
- [ ] Subject line populated
- [ ] Body template rendered

### Send Logging

- [ ] All sends logged to `outreach.send_log`
- [ ] `send_status` tracked (pending, sent, delivered, bounced)
- [ ] `scheduled_at` recorded
- [ ] `sent_at` recorded on actual send
- [ ] Error messages captured on failure

### Post-Send Tracking

- [ ] Opens tracked (`opened_at`)
- [ ] Clicks tracked (`clicked_at`)
- [ ] Replies tracked (`replied_at`)
- [ ] Bounces tracked (`bounced_at`)
- [ ] `open_count`, `click_count` incremented

---

## 8. Engagement Event Emission (STRICT)

### Event Contract

All engagement events MUST emit:

- [ ] `person_id` - Contact reference
- [ ] `target_id` - Company target reference
- [ ] `outreach_id` - Outreach context reference
- [ ] `company_unique_id` - Company reference
- [ ] `event_type` - Type of engagement
- [ ] `event_ts` - Timestamp of event
- [ ] `correlation_id` - Tracing ID

### Event Types

| Event | Description |
|-------|-------------|
| `email_open` | Email opened |
| `email_click` | Link clicked |
| `email_reply` | Reply received |
| `email_bounce` | Bounce detected |
| `unsubscribe` | Unsubscribe requested |

### BIT Signal Propagation

- [ ] Engagement events trigger BIT signals
- [ ] BIT scores updated on engagement
- [ ] Signals propagate to company-level score

---

## 9. Output Contract (STRICT)

Must emit exactly:

- [ ] `company_unique_id`
- [ ] `outreach_context_id`
- [ ] `campaign_id` (if campaign created)
- [ ] `send_status` (PASS | FAIL)
- [ ] `engagement_summary`
- [ ] `failure_reason` (if FAIL)

No partial success. No soft states.

---

## 10. Forbidden Actions

- [ ] **NO** identity minting
- [ ] **NO** lifecycle state mutations
- [ ] **NO** upstream hub data modifications
- [ ] **NO** bypassing BIT threshold
- [ ] **NO** bypassing cooling off period
- [ ] **NO** sending to unverified emails
- [ ] **NO** skipping sequence steps
- [ ] **NO** manual BIT score overrides

---

## 11. Kill Switch

Pipeline MUST exit immediately if:

- [ ] `company_unique_id` is null
- [ ] `outreach_context_id` is missing
- [ ] `correlation_id` is missing
- [ ] Upstream hub BLOCKED or FAIL
- [ ] BIT score below threshold
- [ ] No contacts available
- [ ] Lifecycle state not targetable
- [ ] Cooling off period active

---

## 12. Error Handling Compliance

### Error Codes

| Code | Description | Severity |
|------|-------------|----------|
| `OE_UPSTREAM_CL_NOT_VERIFIED` | CL gate failure | blocking |
| `OE_MISSING_SOV_ID` | Missing sovereign ID | blocking |
| `OE_MISSING_DOMAIN` | No domain resolved | blocking |
| `OE_MISSING_PATTERN` | No email pattern | blocking |
| `OE_BIT_BELOW_THRESHOLD` | BIT score too low | blocking |
| `OE_NO_CONTACTS_AVAILABLE` | No valid contacts | blocking |
| `OE_LIFECYCLE_GATE_FAIL` | Not targetable | blocking |
| `OE_COOLING_OFF_ACTIVE` | In cooling off period | blocking |
| `OE_SEND_FAIL` | Send execution failed | warning |
| `OE_BOUNCE_DETECTED` | Email bounced | warning |
| `OE_SPAM_FLAGGED` | Flagged as spam | blocking |
| `OE_UNKNOWN_ERROR` | Unexpected error | blocking |

### Error Table

- [ ] All failures written to `outreach.outreach_errors`
- [ ] Error terminates execution for blocking severity
- [ ] Spend frozen for context on blocking error

---

## 13. Cross-Hub Repair Rules

### Upstream Resolution Required

| Error | Resolution |
|-------|------------|
| `OE_MISSING_DOMAIN` | Resolve Company Target first |
| `OE_MISSING_PATTERN` | Resolve Company Target first |
| `OE_NO_CONTACTS_AVAILABLE` | Resolve People Intelligence first |
| `OE_BIT_BELOW_THRESHOLD` | Wait for BIT improvement |

### Repair Does NOT Modify

- [ ] Does NOT repair Company Target errors
- [ ] Does NOT repair DOL errors
- [ ] Does NOT repair People Intelligence errors
- [ ] Repairs only OE_* errors

---

## 14. CI Doctrine Compliance

### Hub Boundaries (DG-003)

- [ ] No imports from upstream hubs (only spoke imports)
- [ ] No lateral hub-to-hub imports

### Signal Validity (DG-007, DG-008)

- [ ] No old/prior context signal usage
- [ ] No signal refresh patterns
- [ ] Signals are origin-bound

### Immutability (DG-009, DG-010, DG-011)

- [ ] No send_log deletions
- [ ] No engagement_events mutations
- [ ] Error rows never deleted

---

## 15. External CL + Program Scope Compliance

### CL is External

- [ ] Understands CL is NOT part of Outreach program
- [ ] Does NOT invoke Company Lifecycle
- [ ] Does NOT gate on CL operations
- [ ] Consumes company_unique_id as read-only input

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | Outreach Execution | CONSUME company_unique_id |
| Company Target | Outreach Execution | CONSUME domain, pattern |
| DOL | Outreach Execution | CONSUME filing signals |
| People Intelligence | Outreach Execution | CONSUME contacts, slots |
| BIT Engine | Outreach Execution | CONSUME/EMIT BIT signals |

---

## Prime Directive

> **No outreach without BIT. No outreach without contacts. No outreach without identity.**

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-25
**Hub**: Outreach Execution (04.04.04)
**Doctrine Version**: 1.0
