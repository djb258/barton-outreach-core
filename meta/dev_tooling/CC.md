# Dev Tooling — Local Only

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

CC_LAYER: N/A (Developer convenience)
PURPOSE: Local development tools and IDE configurations
ALLOWED_DEPENDENCIES: None (local execution only)
FORBIDDEN_DEPENDENCIES: Must not be imported by production code

---

## Contents

| Item | Purpose |
|------|---------|
| `.devcontainer/` | VS Code dev container config |
| `.vscode/` | VS Code workspace settings |

## Rules

1. **Local only** — Never executed in CI or production
2. **No CC imports** — Cannot depend on CC-02/03/04 code
3. **Developer convenience** — IDE settings, local scripts
