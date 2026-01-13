# Docs Directory — Visibility Only

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

CC_LAYER: N/A (Documentation/Visibility)
PURPOSE: Documentation, diagrams, and reference materials
ALLOWED_DEPENDENCIES: None (not executed)
FORBIDDEN_DEPENDENCIES: Must not contain executable code

---

## Contents

| Subdirectory | Purpose |
|--------------|---------|
| `diagrams/` | Mermaid diagrams, ERDs |
| `doctrine_ref/` | Doctrine reference materials |
| `templates/` | Document templates |
| `adr/` | Architecture Decision Records |
| `prd/` | Product Requirements Documents |

## Rules

1. **No executable code** — Documentation only
2. **Markdown preferred** — Use .md for all docs
3. **Diagrams in Mermaid** — Use .mmd for diagram source
4. **Version controlled** — All docs under git
