# Neon ↔ Supabase Sync - Quick Reference

**For the Supabase enrichment repo**: This directory contains all information needed to pull invalid records from Neon, enrich them, and push them back.

---

## 📄 Key Files

### 1. **sync_manifest.json** (Machine-Readable)
**Use this for automated scripts**

Contains:
- Complete table schemas (124 records total)
- Field mappings (Neon → Supabase)
- Push-back field lists
- Validation rules
- Workflow stages
- Database connection info

```bash
# Example: Parse in Python
import json
with open('sync_manifest.json') as f:
    manifest = json.load(f)

# Get Neon table schema
company_schema = manifest['source_tables']['company_invalid']['fields']

# Get field mapping
mapping = manifest['field_mappings']['company_invalid_to_company_needs_enrichment']
```

### 2. **NEON_SUPABASE_SYNC_GUIDE.md** (Human-Readable)
**Use this for understanding the pipeline**

Contains:
- Complete 4-stage workflow diagram
- SQL schemas for both Neon and Supabase
- Pull/push queries
- Script descriptions
- Manual enrichment workflow
- Success metrics

---

## 🚀 Quick Start (For Other Repo)

### Pull This Manifest

```bash
# Option 1: Git submodule (recommended)
git submodule add https://github.com/yourusername/barton-outreach-core.git barton-core
# Reference: barton-core/ctb/data/validation-framework/sync_manifest.json

# Option 2: Direct download
curl -O https://raw.githubusercontent.com/yourusername/barton-outreach-core/main/ctb/data/validation-framework/sync_manifest.json

# Option 3: HTTP fetch in your code
import requests
manifest = requests.get('https://raw.githubusercontent.com/yourusername/barton-outreach-core/main/ctb/data/validation-framework/sync_manifest.json').json()
```

### Use the Manifest

```python
import json

# Load manifest
with open('sync_manifest.json') as f:
    config = json.load(f)

# Get source tables
neon_tables = config['source_tables']
company_table = neon_tables['company_invalid']

print(f"Pulling {company_table['record_count']} records from {company_table['full_name']}")

# Get field mapping for Supabase table creation
mapping = config['field_mappings']['company_invalid_to_company_needs_enrichment']

# Build pull query
fields = [f"{neon_col} as {supabase_col}" for neon_col, supabase_col in mapping.items()]
query = f"SELECT {', '.join(fields)} FROM {company_table['full_name']}"

# Get push-back fields
push_fields = config['push_back_fields']['company']
# ['website', 'phone', 'industry', 'employee_count', 'domain', ...]
```

---

## 📊 What's Available

| Table | Records | Primary Key | Status |
|-------|---------|-------------|--------|
| `marketing.company_invalid` | 119 | `company_unique_id` | ✅ Ready |
| `marketing.people_invalid` | 5 | `unique_id` | ✅ Ready |

**Total**: 124 records ready for enrichment

**Primary Enrichment Need**: Missing `website` field (119 companies)

---

## 🔄 Workflow Overview

```
Neon Invalid Tables
      ↓
   [PULL] (Stage 1)
      ↓
Supabase Workspace
      ↓
  [ENRICH] (Stage 2)
      ↓
   [PUSH] (Stage 3)
      ↓
Neon Invalid Tables (updated)
      ↓
[RE-VALIDATE] (Stage 4)
      ↓
 [PROMOTE] (Stage 5)
      ↓
Neon Master Tables
```

---

## 🎯 For Your Repo to Implement

### 1. Create Supabase Tables

Use schemas from `sync_manifest.json`:
- `company_needs_enrichment`
- `people_needs_enrichment`

### 2. Build Pull Script

Pull from:
- `marketing.company_invalid` (119 records)
- `marketing.people_invalid` (5 records)

Field mapping in: `field_mappings` section

### 3. Build Push Script

Push back fields in: `push_back_fields` section

Update these fields in Neon invalid tables:
- Companies: `website`, `phone`, `industry`, etc.
- People: `email`, `phone`, `linkedin_url`, etc.

### 4. Workflow Status Tracking

Use `enrichment_status` field:
- `pending` → Record pulled, awaiting enrichment
- `in_progress` → Currently being enriched
- `complete` → Ready to push back to Neon
- `failed` → Enrichment failed, needs review

---

## 📋 Enrichment Checklist (Manual Steps)

For each company in Supabase:

1. ✅ Search for missing website (Google, LinkedIn, etc.)
2. ✅ Update `website` field
3. ✅ Extract `domain` from website
4. ✅ Add any other missing data (phone, industry)
5. ✅ Set `enrichment_status = 'complete'`
6. ✅ Add `enrichment_notes` (how you found it)
7. ✅ Set `enriched_by` (your email)
8. ✅ Set `enriched_at = now()`

Then trigger push script → data flows back to Neon

---

## 🔧 Scripts We'll Provide Back to You

Once you have Supabase set up and share credentials, we'll build:

1. **pull-invalid-to-supabase.py** - Stage 1 (Neon → Supabase)
2. **push-enriched-to-neon.py** - Stage 3 (Supabase → Neon)
3. **revalidate-enriched.py** - Stage 4 (Re-run validation)
4. **promote-validated.py** - Stage 5 (Move to master)

These will be in: `ctb/data/validation-framework/scripts/python/`

---

## 📞 Questions?

- **Full Guide**: See `NEON_SUPABASE_SYNC_GUIDE.md`
- **Validation Details**: See `docs/VALIDATION_COMPLETE_SUMMARY.md`
- **Contact**: david@svg.agency

---

**Last Updated**: 2025-11-07
**Repo**: barton-outreach-core
**Manifest Version**: 1.0.0
