# Technical Architecture Specification: CI Compliance Enforcement

**Repository**: barton-outreach-core
**Workflow**: `.github/workflows/tas-compliance.yml`
**Version**: 1.0.0

---

## Purpose

This CI workflow enforces TAS documentation consistency. It FAILS the build when documentation drift is detected.

---

## Triggers

The workflow runs on:

| Trigger | Paths |
|---------|-------|
| Pull Request | `docs/TAS_*.md`, `docs/diagrams/**/*.mmd`, `docs/DIAGRAMS_INDEX.md`, `neon/migrations/*.sql` |
| Push to main | Same paths |

---

## Checks Performed

### 1. TAS-ERD Consistency

**Rule**: When TAS docs change, ERD diagrams must be reviewed.

| TAS Changed | ERD Changed | Result |
|-------------|-------------|--------|
| YES | YES | PASS |
| YES | NO | FAIL |
| NO | YES | FAIL |
| NO | NO | PASS |

**Rationale**: TAS documents describe data flows and schema contracts. ERD diagrams visualize those contracts. If one changes without the other, documentation drift has occurred.

### 2. Diagram Index Completeness

**Rule**: All `.mmd` files in `docs/diagrams/` must be listed in `DIAGRAMS_INDEX.md`.

**Check**: Scans all `.mmd` files and verifies each filename appears in the index.

**Failure**: Missing diagram from index.

### 3. Migration Documentation

**Rule**: New migrations should be referenced in documentation.

**Checks**:
- Migration filename referenced in `docs/*.md`
- Warns on destructive operations (DROP, TRUNCATE, DELETE)

### 4. Mermaid Syntax Validation

**Rule**: All `.mmd` files must have valid Mermaid syntax.

**Check**: Runs `mmdc` (Mermaid CLI) to validate each diagram.

**Failure**: Syntax error in any diagram.

---

## Failure Scenarios

### Scenario A: TAS Updated Without ERD

```
docs/TAS_DATA_OPERATIONS.md  [MODIFIED]
docs/diagrams/erd/*.mmd       [UNCHANGED]
```

**Error**: "TAS documentation changed but ERD diagrams were not updated."

**Fix**: Review and update relevant ERD diagrams, or add a commit message explaining why no ERD changes are needed.

### Scenario B: ERD Updated Without TAS

```
docs/diagrams/erd/CORE_SCHEMA.mmd  [MODIFIED]
docs/TAS_*.md                       [UNCHANGED]
```

**Error**: "ERD diagrams changed but TAS documentation was not updated."

**Fix**: Review and update relevant TAS documents.

### Scenario C: New Diagram Not Indexed

```
docs/diagrams/erd/NEW_DIAGRAM.mmd  [CREATED]
docs/DIAGRAMS_INDEX.md             [UNCHANGED]
```

**Error**: "Diagrams not listed in DIAGRAMS_INDEX.md"

**Fix**: Add the new diagram to `DIAGRAMS_INDEX.md`.

### Scenario D: Invalid Mermaid Syntax

```
docs/diagrams/erd/BROKEN.mmd  [SYNTAX ERROR]
```

**Error**: "Mermaid syntax error in docs/diagrams/erd/BROKEN.mmd"

**Fix**: Correct the Mermaid syntax in the diagram.

---

## Bypassing Checks

**DO NOT bypass these checks** without ADR documentation.

If a bypass is absolutely necessary:
1. Document reason in PR description
2. Create ADR for the exception
3. Use `[skip-tas-check]` in commit message (not recommended)

---

## Local Validation

Run checks locally before pushing:

```bash
# Check diagram index
for f in docs/diagrams/**/*.mmd; do
  basename "$f" | xargs -I {} grep -q {} docs/DIAGRAMS_INDEX.md || echo "Missing: $f"
done

# Validate Mermaid syntax (requires mmdc)
npm install -g @mermaid-js/mermaid-cli
for f in docs/diagrams/**/*.mmd; do
  mmdc -i "$f" -o /tmp/test.svg || echo "Syntax error: $f"
done
```

---

## What This Does NOT Check

| Not Checked | Reason |
|-------------|--------|
| Code logic | CI is documentation-focused |
| Database state | Requires live connection |
| Business rules | Covered by unit tests |
| Schema correctness | Migration verification is manual |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-28 |
| Author | Claude Code (AI Employee) |
| Workflow | .github/workflows/tas-compliance.yml |
| Enforcement | Blocks merge on failure |
