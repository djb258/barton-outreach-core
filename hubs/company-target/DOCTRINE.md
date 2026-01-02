# OUTREACH THREAD CONTEXT — SOVEREIGN ID & COMPANY_TARGET DOCTRINE

**Canonical Rule (Non-Negotiable)**

> **Company Lifecycle (CL) is the ONLY authority that can mint, modify, merge, or correct a sovereign company ID (`company_unique_id`).**
> Outreach **never** creates, alters, repairs, or "fixes" sovereign identity. Ever.

---

## SYSTEM BOUNDARIES

### CL (Company Lifecycle)

* Owns sovereign identity
* Owns existence, deduplication, merges, and corrections
* Writes to `company_master`
* Final authority on what a company *is*

### Outreach (This Thread)

* Treats `company_unique_id` as **read-only**
* Operates strictly **post-CL PASS**
* Evaluates *viability*, not *identity*
* Emits signals, never identity changes

If Outreach thinks an ID is wrong → **emit FAIL + reason**.
Do **not** repair. Do **not** retry. Do **not** improvise.

---

## UPSTREAM CONTRACT (CL GATE)

> **Outreach assumes Company Life Cycle existence verification has already passed.**
> **Outreach will not execute without an `EXISTENCE_PASS` signal.**

### Enforcement

At Company Target entry (before ANY logic):

1. Check if `company_sov_id` exists in `cl.company_identity`
2. If EXISTS → `EXISTENCE_PASS` (proceed)
3. If MISSING → Route to `outreach_errors.company_target_errors`:
   - `failure_code`: `CT_UPSTREAM_CL_NOT_VERIFIED`
   - `pipeline_stage`: `upstream_cl_gate`
   - `severity`: `blocking`
4. Raise `CLNotVerifiedError` and STOP

### Explicit Prohibitions

Missing upstream signals are **NOT an Outreach error to fix**.

You MUST NOT:

* Implement CL existence checks (domain resolution, name coherence, state matching)
* Add CL error tables
* Retry or "repair" missing CL signals
* Infer existence from domains, LinkedIn, or names
* Soft-fail or partially proceed

Outreach is a **consumer of truth**, not a creator of it.
If the upstream worker didn't stamp the passport, the traveler doesn't cross.

---

## COMPANY_TARGET POSITION IN OUTREACH

* Company Target is the **first Outreach sub-hub**
* Inputs:
  * `company_unique_id` (immutable)
  * `outreach_context_id` (mandatory, disposable, cost scope)
* Outputs:
  * Email domain viability
  * Email pattern (or FAIL)
  * Cost-logged, context-bound signals only

Company Target answers one question only:

> **"Is this company email-addressable at an acceptable cost?"**

---

## PRIME DIRECTIVE (LOCKED)

> **Cost containment is a hard gate. Accuracy is a tiebreaker, not a justification to spend.**

Implications:

* Free → Low-cost → Premium (single-shot) waterfall
* Tier-2 tools are fuse-protected per `outreach_context_id`
* No retries
* No soft-fails
* No "confidence-based escalation"

---

## IDENTITY SAFETY RULES

| Forbidden | Allowed |
|-----------|---------|
| ❌ Outreach cannot mint IDs | ✅ Read CL data |
| ❌ Outreach cannot merge companies | ✅ Match companies (read-only) |
| ❌ Outreach cannot override CL decisions | ✅ Flag collisions |
| ❌ Outreach cannot "fix upstream data" | ✅ Emit FAIL signals with reasons |

Any attempt to bypass this boundary is a **doctrine violation**.

---

## ENFORCEMENT STATUS

* `company_target` is the **reference implementation**
* `CERTIFICATION.md` documents verification (9 tests passed)
* `CHECKLIST.md` is the freeze line
* CI guards DG-013/014 enforce Tier-2 single-shot
* All 14 doctrine guards (DG-001 through DG-014) active

---

## DOCUMENT HIERARCHY

```
DOCTRINE.md          ← This file (governing context)
CHECKLIST.md         ← Freeze line (all boxes must be checked)
CERTIFICATION.md     ← Verification record
```

---

**Doctrine Version**: 1.0
**Last Updated**: 2026-01-01
**Authority**: Outreach Doctrine v1.0
