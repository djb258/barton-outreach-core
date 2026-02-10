# ADR: Coverage Run Refactor — Intent + View

**Date**: 2026-02-10
**Status**: ACCEPTED
**Scope**: coverage schema
**Trigger**: Post-implementation doctrine review of coverage_run_zip materialization

---

## 1. Doctrinal Pressure Test

### Why storing `coverage_run_zip` is NOT doctrinally correct

`coverage_run_zip` materializes the output of a haversine distance formula applied to `reference.us_zip_codes`. It contains no business truth — every row is deterministically derivable from two inputs: an anchor ZIP's coordinates and a radius value. Storing it violates three doctrine principles:

1. **CTB Purity (§1.1)**: CTB governs "physical placement of all components." `coverage_run_zip` is not a component — it is a projection of `reference.us_zip_codes` filtered by math. Registering derived math in CTB pollutes the truth surface.

2. **Constants vs Variables (§4)**: The ZIP membership set is a **derived variable** — a function of two constants (anchor_zip, radius_miles) and a reference table. Materializing a derived variable into a CANONICAL table creates the illusion that the ZIP list is an independent truth, when it is not.

3. **Hub State Ownership (§3.1)**: A hub "owns all logic, state, and decisions." The *decision* here is the intent: "cover 50 miles around 75201." The ZIP list is a *consequence* of that decision, not the decision itself. Persisting consequences instead of decisions inverts the authority model.

### When materialization WOULD be correct

Materialized membership would be justified if:
- The ZIP list were **curated** (human-edited, not formula-derived)
- The system needed **point-in-time audit replay** (exact ZIP set at time T)
- The haversine computation were **expensive** (it is not — 0.08–0.20s)

None of these conditions apply to Barton's coverage use case.

---

## 2. Model Comparison

| Dimension | Model A: Materialized Table | Model B: Intent + View |
|-----------|---------------------------|----------------------|
| **What's stored** | 386+ rows per run (ZIP, distance) | 1 row per run (anchor, radius) |
| **Truth surface** | Pretends ZIP list is independent truth | Intent is the truth; ZIP list is derived |
| **Table bloat** | O(n × runs) rows; 386 per 50mi run | O(runs) rows; always 1 per run |
| **CTB purity** | 3 CANONICAL tables for 1 real entity | 2 CANONICAL tables (both real entities) |
| **Drift risk** | ZIP list frozen at creation time; stale if reference.us_zip_codes updates | Always current with reference data |
| **Auditability** | Immutable snapshot of past ZIP membership | Reproducible: same intent + same reference = same result |
| **Replay** | Exact replay from stored rows | Replay via re-query (deterministic given stable reference) |
| **Performance** | O(1) lookup for ZIP membership | O(0.2s) query per coverage_id — acceptable |
| **Cost** | Storage grows linearly with runs | Storage flat; compute on read |
| **Determinism** | Frozen at write time | Deterministic given same reference.us_zip_codes |

---

## 3. Decision

**Model B: Intent + View** is correct for Barton.

Rationale:
- **CTB purity**: Only real entities (service_agent, service_agent_coverage) are registered. The view is outside CTB.
- **Cost-first**: No storage growth per run. reference.us_zip_codes is 41,551 rows; haversine with bounding box pre-filter returns in <0.2s.
- **Deterministic joins**: `coverage_id` is the stable FK for all downstream joins. The view is a function of coverage_id.
- **Owner authority**: The hub owns the *intent* (anchor + radius). The *membership* is a read projection — it belongs in Egress (O layer), which is "read-only views" per IMO §3.5.
- **Immutability**: The intent row is immutable once written. The derived view is deterministic.

---

## 4. What Stays vs What Becomes Views

| Artifact | Type | Justification |
|----------|------|---------------|
| `coverage.service_agent` | **TABLE** (CANONICAL) | Real entity — agent identity, owns coverage runs |
| `coverage.service_agent_coverage` | **TABLE** (CANONICAL) | Real entity — persisted intent (anchor + radius + lifecycle) |
| `coverage.v_service_agent_coverage_zips` | **VIEW** | Derived — haversine projection of intent against reference.us_zip_codes |
| `coverage.coverage_run` | **DROP** | Replaced by service_agent_coverage |
| `coverage.coverage_run_zip` | **DROP** | Replaced by view |

CTB registrations:
- `coverage.service_agent` → CANONICAL (keep)
- `coverage.service_agent_coverage` → CANONICAL (new)
- `coverage.coverage_run` → DELETE from registry
- `coverage.coverage_run_zip` → DELETE from registry
- View is NOT registered in CTB (views are not truth surfaces)

---

## 5. Migration Summary

1. Create `coverage.service_agent_coverage` table
2. Migrate any existing `coverage.coverage_run` rows into it
3. Create `coverage.v_service_agent_coverage_zips` view
4. Drop `coverage.coverage_run_zip` table
5. Drop `coverage.coverage_run` table
6. Update CTB registry (remove old, add new)
