# ADR: CT Postal Code Repair via DOL Evidence

**Date**: 2026-02-10
**Status**: ACCEPTED
**Scope**: outreach.company_target postal_code repair
**Trigger**: Coverage-to-company matching revealed 92% CT postal_code gap; DOL Form 5500 contains sponsor ZIP evidence for 947 repairable companies

---

## 1. Why CT Must Remain the ZIP Authority

CT (outreach.company_target) is the sole scoping surface for company geography. Doctrine is unambiguous:

- **Waterfall order** (§CLAUDE.md): CT is Gate #1. All downstream sub-hubs — DOL, People, Blog, CLS — consume CT attributes. If scoping logic reads ZIP from DOL directly, it bypasses the gate and creates a parallel truth: some companies scoped by CT ZIP, others by DOL ZIP. That split is a **CC violation** — two authorities for the same attribute at the same CC layer.

- **Hub state ownership** (§3.1): CT owns company geography. DOL owns filing intelligence. Each hub owns its declared boundary. DOL's `spons_dfe_loc_us_zip` is an attribute of the *filing sponsor*, not an attribute of the *outreach target company*. The sponsor may have a different mailing address than the company's operational location.

- **Single source of truth**: Coverage runs join to `company_target.postal_code`. Readiness views join to `company_target.postal_code`. If we allow ad-hoc DOL ZIP joins elsewhere, every consumer must know about two paths — that's the definition of a doctrinal leak.

**Conclusion**: CT is the sole ZIP authority. Period.

---

## 2. Why DOL ZIPs Are Valid Repair Evidence but Invalid Scoping Inputs

DOL Form 5500 sponsor ZIPs are **evidence** — a signal that a company's physical location is near a particular ZIP code. They are not **authority** because:

1. **Sponsor vs company**: The plan sponsor address may be a registered agent, law firm, or PO box, not the company's operating location.
2. **Temporal lag**: Filings reflect the plan year, not current state. A company may have moved.
3. **Incomplete coverage**: Only 15,134 of 432,582 filings carry ZIP data (3.5%). The 2023 vintage was imported without ZIP — using DOL ZIPs as a scoping input would create an arbitrary coverage cliff between filing years.

However, as *repair evidence* for CT, these ZIPs are valuable because:
- They come from federal filings (high trust, not self-reported marketing data)
- When a company has NO ZIP in CT at all, even an imperfect sponsor ZIP is better than nothing
- The repair only *proposes* — it never overwrites existing CT data

**Rule**: DOL ZIPs may flow INTO CT as proposed repairs. They may NEVER flow into scoping, readiness, or outreach logic directly.

---

## 3. Why This Process Must Be Deterministic and Repeatable

- **Deterministic**: Given the same DOL filings and the same CT state, the repair produces the same output. No randomness, no human judgment in the loop, no ML scoring.
- **Repeatable**: As new Form 5500 vintages arrive (2025, 2026...), re-running the repair picks up newly available ZIPs without re-processing already-repaired companies.
- **Idempotent**: Companies that already have CT postal_code are never touched. Running the repair twice produces no additional changes.

This matters because CT is a frozen core table. Changes must be traceable and reversible. A deterministic process produces an audit trail that can be validated after the fact.

---

## 4. Why ZIP Repair Belongs in CT Maintenance, Not Outreach Readiness

Outreach readiness is a *read surface* — it reports gaps, it doesn't fix them. If readiness logic also writes to CT, it violates the IMO boundary:

- **Middle (M)** is for logic and decisions
- **Egress (O)** is for read-only views

Readiness views belong in O. Repair scripts belong in M — specifically, CT maintenance within the Company Target hub's Middle layer. The repair script lives alongside other CT pipeline logic, not alongside readiness consumers.

---

## 5. Repair Surface

| Metric | Count |
|--------|-------|
| CT total | 95,837 |
| CT with postal_code | 7,706 (8.0%) |
| CT missing postal_code | 88,131 (92.0%) |
| DOL filings with ZIP | 15,134 (of 432,582) |
| CT-missing companies with DOL ZIP evidence | **947** |
| Post-repair CT with postal_code | ~8,653 (9.0%) |

The 2023 Form 5500 vintage (230,482 filings) was imported without ZIP data. Future re-imports with ZIP will increase the repair surface significantly.

---

## 6. Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| View location | `outreach` schema | CT data lives in `outreach`; no new schema needed |
| CTB registration | None | Views are derived read surfaces, not truth |
| Tracking columns | `postal_code_source`, `postal_code_updated_at` on CT | Audit trail for repair provenance |
| Confidence scoring | occurrence_count + recency | Simple, deterministic, no ML |
| Overwrite protection | HARD — never overwrite existing postal_code | CT authority preserved |
