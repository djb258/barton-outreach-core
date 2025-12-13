# DOL Form 5500 Data Directory

**Purpose:** Store raw DOL Form 5500 FOIA datasets (CSVs and ZIP files)

---

## Download Instructions

### 1. Download from DOL

Visit: https://www.dol.gov/agencies/ebsa/researchers/data/retirement-bulletin

Download these three files for **2023** (most recent year):

| File | Size | Description |
|------|------|-------------|
| `F_5500_2023_latest.zip` | ~500MB | Form 5500 (Regular) - Large plans (≥100 participants) |
| `F_5500_SF_2023_latest.zip` | ~1.5GB | Form 5500-SF (Short Form) - Small plans (<100 participants) |
| `F_SCH_A_2023_latest.zip` | ~300MB | Schedule A - Insurance information |

### 2. Place in This Directory

Drop all three ZIP files here:
```
data/
├── F_5500_2023_latest.zip
├── F_5500_SF_2023_latest.zip
└── F_SCH_A_2023_latest.zip
```

### 3. Extract in Place

```bash
cd data/
unzip F_5500_2023_latest.zip
unzip F_5500_SF_2023_latest.zip
unzip F_SCH_A_2023_latest.zip
```

**Result:**
```
data/
├── F_5500_2023_latest.zip
├── F_5500_2023_latest.csv          # 700K+ records
├── F_5500_SF_2023_latest.zip
├── F_5500_SF_2023_latest.csv       # 2M+ records
├── F_SCH_A_2023_latest.zip
└── F_SCH_A_2023_latest.csv         # 1.5M+ records
```

---

## What Gets Committed to Git?

✅ **Committed:**
- This README.md
- .gitkeep file

❌ **Excluded (in .gitignore):**
- *.csv files (too large)
- *.zip files (too large)

---

## Import Scripts (Already Ready)

Once CSVs are in this directory, run imports:

### Form 5500 (Regular)
```bash
# Already complete from previous work
# See: ctb/sys/enrichment/company_intelligence_enrichment.js
```

### Form 5500-SF (Short Form)
```bash
# 1. Prepare CSV
python ctb/sys/enrichment/import_5500_sf.py

# 2. Import to Neon
psql $NEON_CONNECTION_STRING << 'EOF'
\COPY marketing.form_5500_sf_staging FROM 'output/form_5500_sf_2023_staging.csv' CSV HEADER;
EOF

# 3. Process staging
psql $NEON_CONNECTION_STRING -c "CALL marketing.process_5500_sf_staging();"
```

### Schedule A (Insurance + Renewals)
```bash
# Extract renewal dates
python ctb/sys/enrichment/extract_schedule_a_renewals.py

# Output: output/schedule_a_2023_with_renewals.csv
```

---

## Expected File Sizes

| File | Uncompressed Size | Records |
|------|-------------------|---------|
| F_5500_2023_latest.csv | ~1.2GB | 700,000+ |
| F_5500_SF_2023_latest.csv | ~3.5GB | 2,000,000+ |
| F_SCH_A_2023_latest.csv | ~800MB | 1,500,000+ |

**Total:** ~5.5GB uncompressed

---

## Documentation

- **Complete Guide:** `ctb/sys/enrichment/FORM_5500_COMPLETE_GUIDE.md`
- **Import Checklist:** `ctb/sys/enrichment/IMPORT_CHECKLIST.md`
- **Executive Summary:** `ctb/sys/enrichment/FORM_5500_EXECUTIVE_SUMMARY.md`

---

**Status:** Ready for data download
**Last Updated:** 2025-11-27
