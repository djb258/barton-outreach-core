# Legacy Quarantine — NOT CC COMPLIANT

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

CC_LAYER: QUARANTINE (Not classified)
PURPOSE: Holding area for non-CC-compliant code pending deletion or migration
ALLOWED_DEPENDENCIES: None
FORBIDDEN_DEPENDENCIES: ALL (must not be referenced)

---

## Status

**WARNING**: Code in this directory is NOT CC-compliant and MUST NOT be:
- Imported by any CC-02/03/04 code
- Executed in production
- Referenced in CI pipelines

## Quarantine Protocol

1. Items added here have **90 days** to be either:
   - Migrated to proper CC location
   - Deleted permanently
2. Add a `QUARANTINE_NOTE.md` explaining why item is here
3. PR required to remove items from quarantine

## Contents

Items moved here during CC purification on 2026-01-05.
