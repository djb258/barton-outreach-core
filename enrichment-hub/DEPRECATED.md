# DEPRECATED — enrichment-hub

**Status:** DEPRECATED
**Date:** 2026-01-01
**Reason:** Violates CL Parent-Child Doctrine

---

## Why This Is Deprecated

This directory was part of an older structure where enrichment was treated
as a standalone hub. Under the current doctrine:

1. **Enrichment is not a hub** — it's a capability within sub-hubs
2. **Company Target owns pattern discovery** — Phases 3-4
3. **People Intelligence owns people enrichment** — Phase 7
4. **No standalone enrichment hub exists**

---

## What Replaces This

| Old Location | New Location |
|--------------|--------------|
| enrichment-hub/* | hubs/company-target/imo/middle/phases/ |
| enrichment-hub/* | hubs/people-intelligence/imo/middle/phases/ |

---

## Do Not Use

Do not add code to this directory. It will be removed in a future cleanup.

Any enrichment logic should be placed in the appropriate sub-hub's
`imo/middle/` directory with proper lifecycle gates and cost controls.
