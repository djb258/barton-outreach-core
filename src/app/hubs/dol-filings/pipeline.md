# DOL Filings — Pipeline Definition

> **IMO DOCTRINE v1.1 (Error-Only Enforcement)**
> 
> The DOL Sub-Hub emits facts only.
> All failures are DATA DEFICIENCIES, not system failures.
> Therefore, the DOL Sub-Hub NEVER writes to AIR.
>
> **AIR logging is FORBIDDEN.** All failures route to `shq.error_master`.
> **Geographic scope:** 8 target states (WV, VA, PA, MD, OH, KY, DE, NC)

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DOL FILINGS PIPELINE                      │
│               (IMO Facts-Only Architecture)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ INGEST: Load DOL CSV Files                                   │
│ ─────────────────────────────────────────────────────────── │
│ • Form 5500 (large plans >= 100 participants)               │
│ • Form 5500-SF (small plans < 100 participants)             │
│ • Schedule A (insurance broker data)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PARSE: Extract and Validate Records                          │
│ ─────────────────────────────────────────────────────────── │
│ • Parse: ACK_ID, EIN, PLAN_YEAR, PARTICIPANTS, ASSETS       │
│ • Validate: Required fields present                         │
│ • Stage to: marketing.form_5500_staging                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCH: EIN Matching (Exact Only)                             │
│ ─────────────────────────────────────────────────────────── │
│ • Query company_master by EIN (READ ONLY)                   │
│ • EXACT MATCH ONLY — no fuzzy                               │
│ • No retries on mismatch                                    │
│ • Doctrine: Fail closed                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Match Found?   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌─────────┐                   ┌─────────┐
        │   YES   │                   │   NO    │
        └────┬────┘                   └────┬────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ ATTACH: Link Filing     │    │ LOG: Unmatched Filing   │
│ ─────────────────────── │    │ ─────────────────────── │
│ • Attach to company     │    │ • Write to              │
│ • Store in dol.form_5500│    │   shq.error_master ONLY │
│ • Store in dol.schedule_a│   │ • NO AIR LOGGING        │
└────────────┬────────────┘    │ • STOP processing       │
             │                 └─────────────────────────┘
             ▼
┌─────────────────────────────────────────────────────────────┐
│ OUTPUT: Store Facts (IMO Output Layer - ERROR ONLY)          │
│ ─────────────────────────────────────────────────────────── │
│ • Facts stored directly in dol.* tables                     │
│ • FORM_5500 → dol.form_5500                                 │
│ • SCHEDULE_A → dol.schedule_a                               │
│ • EIN_LINKAGE → dol.ein_linkage                             │
│                                                             │
│ ╔═══════════════════════════════════════════════════════╗   │
│ ║ ❌ AIR LOGGING IS FORBIDDEN                           ║   │
│ ║ ❌ NO dol.air_log writes                              ║   │
│ ║ ✅ All failures route to shq.error_master ONLY        ║   │
│ ╚═══════════════════════════════════════════════════════╝   │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Files

| Component | File |
|-----------|------|
| Form 5500 Importer | `imo/middle/importers/import_5500.py` |
| Form 5500-SF Importer | `imo/middle/importers/import_5500_sf.py` |
| Schedule A Importer | `imo/middle/importers/import_schedule_a.py` |
| EIN Matcher | `imo/middle/ein_matcher.py` |
| DOL Hub Spoke | `imo/middle/dol_hub.py` |
| Error Writer | `imo/output/error_writer.py` |
| Doctrine Guards | `imo/middle/doctrine_guards.py` |

---

## IMO Enforcement Boundaries (v1.1 - Error-Only)

| Operation | Allowed? | Target |
|-----------|----------|--------|
| READ company_master | ✅ YES | EIN lookup |
| WRITE company_master | ❌ NO | CL sovereignty |
| WRITE dol.* tables | ✅ YES | Append-only facts |
| WRITE shq.error_master | ✅ YES | Errors ONLY |
| WRITE dol.air_log | ❌ NO | AIR FORBIDDEN |
| EMIT BIT signals | ❌ NO | Facts-only spoke |

---

## Geographic Scope

DOL Sub-Hub processes **only 8 target states**:

| State | Region |
|-------|--------|
| WV | Appalachian |
| VA | Mid-Atlantic |
| PA | Mid-Atlantic |
| MD | Mid-Atlantic |
| OH | Midwest |
| KY | Appalachian |
| DE | Mid-Atlantic |
| NC | Southeast |

**Out-of-scope records are silently skipped** (no error, no counter, no AIR).
