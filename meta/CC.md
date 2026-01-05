# Meta Directory — Visibility Only

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

CC_LAYER: N/A (Visibility/Quarantine)
PURPOSE: Houses non-CC artifacts, legacy code, and dev tooling
ALLOWED_DEPENDENCIES: None (not executed)
FORBIDDEN_DEPENDENCIES: Must not be imported by CC-02/03/04 code

---

## Contents

| Subdirectory | Purpose |
|--------------|---------|
| `legacy_quarantine/` | Non-CC-compliant code awaiting deletion or migration |
| `dev_tooling/` | Developer convenience tools (not production) |

## Rules

1. **No runtime imports** — Nothing in `meta/` may be imported by CC code
2. **No CI execution** — Scripts here do not run in CI
3. **Quarantine is temporary** — Items should be deleted or migrated within 90 days
4. **Visibility only** — For reference and historical context
