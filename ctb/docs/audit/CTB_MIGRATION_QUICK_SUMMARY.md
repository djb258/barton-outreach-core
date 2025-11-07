# CTB Migration - Quick Summary

**Repository**: barton-outreach-core
**Date**: 2025-11-07
**Status**: ⚠️ PREVIEW ONLY - NO CHANGES MADE

---

## TL;DR

The barton-outreach-core repository has **~65% CTB compliance**. To reach **100% compliance**, we need to:

- ✅ Create 3 missing sys/* directories (deepwiki, bigquery-warehouse, builder-bridge)
- ✅ Create ops/ branch at CTB level
- ✅ Move ~120 files from root into CTB structure
- ✅ Add 10 configuration files
- ✅ Create 7 branch README files

**Estimated Time**: 12-18 hours (1.5-2 days)
**Risk Level**: MEDIUM
**Rollback Available**: YES (via git tags and backup branches)

---

## What's Currently Wrong?

### Missing Directories (15-20)
```
❌ ctb/sys/deepwiki/
❌ ctb/sys/bigquery-warehouse/
❌ ctb/sys/builder-bridge/
❌ ctb/ops/
❌ .barton/
❌ config/
❌ (and ~9 more subdirectories)
```

### Files in Wrong Places (~120 files)
```
❌ 35+ documentation files at root (should be in ctb/docs/)
❌ 10 Python scripts at root (should be in ctb/sys/tools/ or ctb/data/migrations/)
❌ 10+ directories at root (should be in CTB structure)
❌ Source code in src/ (should be in ctb/ai/ or ctb/sys/)
```

### Missing Configuration Files (10)
```
❌ LLM_ONBOARDING.md (root)
❌ .barton/repo_config.yaml
❌ .barton/doctrine_id.txt
❌ .barton/hive_assignment.txt
❌ config/mcp_registry.json
❌ config/deployment_config.yaml
❌ config/feature_flags.json
❌ ctb/meta/config/ctb_config.json
❌ 7 branch README files
```

---

## What Needs to Happen?

### Phase 1: Foundation (1-2 hours, LOW RISK)
Create directories and add config files

### Phase 2: Documentation (2-3 hours, LOW RISK)
Move 35+ docs into ctb/docs/ structure

### Phase 3: Scripts (2-3 hours, MEDIUM RISK)
Move Python scripts, update workflows

### Phase 4: Source Code (4-6 hours, HIGH RISK)
Move src/ files, update ALL imports

### Phase 5: Verification (2-4 hours, CRITICAL)
Test everything, deploy to staging

---

## What Are The Risks?

### HIGH RISK ⚠️
- **Import path changes** - All Python imports need updating
  ```python
  # OLD: from libs.imo_tools import X
  # NEW: from ctb.sys.libs.imo_tools import X
  ```

### MEDIUM RISK ⚠️
- **CI/CD updates** - GitHub Actions paths need updating
- **Config loading** - File reference paths need updating

### LOW RISK ✅
- **Documentation moves** - Links need updating but low impact
- **Directory moves** - Systematic and straightforward

---

## How Do We Roll Back?

### Before Starting:
```bash
git tag pre-ctb-migration-$(date +%Y%m%d)
git checkout -b backup/pre-ctb-migration
git push origin --tags
```

### To Undo Everything:
```bash
git reset --hard pre-ctb-migration-YYYYMMDD
# OR
git checkout backup/pre-ctb-migration
```

---

## Example Changes

### Before (Current):
```
barton-outreach-core/
├── ARCHITECTURE_SUMMARY.md          ❌ Wrong place
├── check_db_schema.py                ❌ Wrong place
├── src/main.py                       ❌ Wrong place
├── docs/                             ❌ Duplicate
├── global-config.yaml                ❌ Wrong place
├── libs/imo_tools/                   ❌ Wrong place
├── ctb/
│   ├── sys/                          ✅ Correct
│   │   ├── composio-mcp/            ✅ Correct
│   │   └── (missing deepwiki, bigquery, builder-bridge)
│   ├── ai/                           ✅ Correct
│   ├── data/                         ✅ Correct
│   └── (missing ops/ branch)
```

### After (CTB Compliant):
```
barton-outreach-core/
├── CLAUDE.md                         ✅ Root (correct)
├── README.md                         ✅ Root (correct)
├── LLM_ONBOARDING.md                 ✅ Root (new)
├── .barton/                          ✅ Root config (new)
│   ├── repo_config.yaml
│   ├── doctrine_id.txt
│   └── hive_assignment.txt
├── config/                           ✅ Runtime config (new)
│   ├── mcp_registry.json
│   ├── deployment_config.yaml
│   └── feature_flags.json
├── ctb/
│   ├── sys/                          ✅ System infrastructure
│   │   ├── composio-mcp/
│   │   ├── neon-vault/
│   │   ├── deepwiki/                ✅ New
│   │   ├── bigquery-warehouse/      ✅ New
│   │   ├── builder-bridge/          ✅ New
│   │   ├── tools/
│   │   │   └── check_db_schema.py  ✅ Moved here
│   │   └── libs/
│   │       └── imo_tools/           ✅ Moved here
│   ├── ai/                           ✅ AI layer
│   │   ├── main.py                  ✅ Moved here
│   │   └── agents/
│   ├── data/                         ✅ Data layer
│   │   ├── schemas/
│   │   │   └── ARCHITECTURE_SUMMARY.md
│   │   └── migrations/
│   ├── docs/                         ✅ Documentation
│   │   ├── architecture/
│   │   │   └── ARCHITECTURE_SUMMARY.md  ✅ Moved here
│   │   ├── guides/
│   │   ├── integration/
│   │   └── audit/
│   ├── ui/                           ✅ UI layer
│   ├── meta/                         ✅ Meta config
│   │   ├── global-config/           ✅ Moved here
│   │   │   └── global-config.yaml
│   │   └── config/
│   │       └── ctb_config.json      ✅ New
│   └── ops/                          ✅ New operations branch
│       ├── automation-scripts/
│       └── report-builder/
```

---

## Key Decisions Needed

Before proceeding, please decide:

1. **apps/** directory - Stay at root or move to ctb/ui/apps/?
2. **src/main.py** - Move to ctb/ai/ or ctb/sys/api/?
3. **Deployment configs** - Stay at root or move with symlinks?
4. **Timeline** - When should this happen?

---

## Full Details

See: `CTB_IMPLEMENTATION_PREVIEW_REPORT.md` (complete 50-page analysis)

---

## Quick Start (If Approved)

```bash
# 1. Create backup
git tag pre-ctb-migration-$(date +%Y%m%d)
git checkout -b backup/pre-ctb-migration
git push origin --tags

# 2. Start migration on feature branch
git checkout -b feature/ctb-full-implementation

# 3. Run automated migration (if approved)
bash CTB_FULL_MIGRATION.sh --dry-run  # Preview
bash CTB_FULL_MIGRATION.sh             # Execute

# 4. Verify
bash global-config/scripts/ctb_verify.sh

# 5. Test
pytest
npm test

# 6. Deploy to staging
# (follow deployment process)
```

---

## Questions?

Review the full report: `CTB_IMPLEMENTATION_PREVIEW_REPORT.md`

**Status**: Waiting for approval to proceed
