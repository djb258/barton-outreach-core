# DEPRECATED — outreach_core

**Status:** DEPRECATED
**Date:** 2026-01-01
**Reason:** Legacy structure, replaced by hubs/ directory

---

## Why This Is Deprecated

This directory was part of an older monolithic structure. Under the current
CL Parent-Child doctrine:

1. **Outreach is not a main hub** — it's a collection of sub-hubs
2. **All sub-hubs live in hubs/** — company-target, people-intelligence, etc.
3. **This directory is empty** — no migration needed

---

## What Replaces This

| Old Concept | New Location |
|-------------|--------------|
| Outreach core logic | hubs/outreach-execution/ |
| Company targeting | hubs/company-target/ |
| People management | hubs/people-intelligence/ |

---

## Do Not Use

Do not add code to this directory. It will be removed in a future cleanup.
