# UI ERD — Summary (Mirror)

**Status**: DERIVED
**Authority**: SUBORDINATE TO docs/ERD_SUMMARY.md
**Generated**: 2026-01-29
**Type**: READ-ONLY MIRROR

---

## Mirror Contract

This document is a **1:1 mirror** of the canonical ERD with UI-specific annotations.

- Same entities
- Same fields
- Same relationships
- Same cardinality

**No structural changes allowed.**

---

## UI Annotations

Annotations added for UI consumption only:

| Annotation | Purpose |
|------------|---------|
| `visibility` | Whether field is displayed in UI |
| `render_hint` | How to render the field |
| `permissions` | UI-level access control |
| `read_only` | Whether field is editable in UI |

---

## Outreach Schema (UI View)

### outreach.outreach

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| outreach_id | UUID | visible | ID badge | YES |
| sovereign_id | UUID | visible | Link to CL | YES |
| domain | TEXT | visible | Text | YES |
| status | TEXT | visible | Status badge | YES |
| created_at | TIMESTAMPTZ | visible | Datetime | YES |

### outreach.company_target

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| outreach_id | UUID | visible | Link | YES |
| target_status | TEXT | visible | Status badge | YES |
| email_method | TEXT | visible | Text | YES |
| email_pattern | TEXT | visible | Code | YES |
| pattern_confidence | NUMERIC | visible | Percentage | YES |

### outreach.bit_scores

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| outreach_id | UUID | visible | Link | YES |
| bit_score | NUMERIC | visible | Score bar | YES |
| computed_tier | TEXT | visible | Tier badge | YES |
| effective_tier | TEXT | visible | Tier badge | YES |

### outreach.manual_overrides

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| override_id | UUID | visible | ID badge | YES |
| outreach_id | UUID | visible | Link | YES |
| override_type | TEXT | visible | Type badge | YES |
| reason | TEXT | visible | Text area | YES |
| created_by | TEXT | visible | User link | YES |
| expires_at | TIMESTAMPTZ | visible | Datetime | YES |

---

## People Schema (UI View)

### people.company_slot

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| slot_id | UUID | visible | ID badge | YES |
| outreach_id | UUID | visible | Link | YES |
| slot_type | TEXT | visible | Slot badge | YES |
| is_filled | BOOLEAN | visible | Checkbox | YES |
| person_unique_id | TEXT | visible | Link | YES |

### people.people_master

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| unique_id | TEXT | visible | ID badge | YES |
| first_name | TEXT | visible | Text | YES |
| last_name | TEXT | visible | Text | YES |
| title | TEXT | visible | Text | YES |
| email | TEXT | visible | Email link | YES |
| linkedin_url | TEXT | visible | External link | YES |

---

## DOL Schema (UI View)

### dol.form_5500

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| filing_id | UUID | visible | ID badge | YES |
| ein | TEXT | visible | EIN format | YES |
| plan_year_end | DATE | visible | Date | YES |
| total_participants | INTEGER | visible | Number | YES |

### dol.schedule_a

| Column | Type | Visibility | Render Hint | Read Only |
|--------|------|------------|-------------|-----------|
| schedule_id | UUID | visible | ID badge | YES |
| filing_id | UUID | visible | Link | YES |
| broker_name | TEXT | visible | Text | YES |
| commission_amount | NUMERIC | visible | Currency | YES |

---

## Views (UI Consumption)

### vw_marketing_eligibility_with_overrides

| Column | Visibility | Render Hint |
|--------|------------|-------------|
| company_unique_id | visible | Link |
| overall_status | visible | Status badge |
| company_target_status | visible | Sub-status |
| dol_status | visible | Sub-status |
| people_status | visible | Sub-status |
| bit_gate_status | visible | Gate indicator |
| bit_score | visible | Score bar |
| computed_tier | visible | Tier badge |
| effective_tier | visible | Tier badge (highlighted) |

### vw_sovereign_completion

| Column | Visibility | Render Hint |
|--------|------------|-------------|
| outreach_id | visible | Link |
| ct_pass | visible | Pass/Fail indicator |
| dol_pass | visible | Pass/Fail indicator |
| people_pass | visible | Pass/Fail indicator |
| blog_pass | visible | Pass/Fail indicator |
| overall_completion | visible | Percentage bar |

---

## Relationship Diagram (Reference Only)

```
cl.company_identity
        │
        │ sovereign_id (FK)
        ▼
outreach.outreach (spine)
        │
        ├─── outreach_id ───► outreach.company_target
        │
        ├─── outreach_id ───► outreach.dol
        │
        ├─── outreach_id ───► outreach.people
        │
        ├─── outreach_id ───► outreach.blog
        │
        ├─── outreach_id ───► outreach.bit_scores
        │
        └─── outreach_id ───► outreach.manual_overrides
```

**UI does not create or modify these relationships.**

---

## Document Control

| Field | Value |
|-------|-------|
| Canonical Source | docs/ERD_SUMMARY.md |
| Mirror Type | READ-ONLY |
| Annotations Added | visibility, render_hint, permissions, read_only |
| Structural Changes | NONE (prohibited) |
| Regenerable | YES |
