# DOL Federal Data Catalog

## Overview

The DOL (Department of Labor) schema contains federal Employee Benefits Security Administration (EBSA) data from Form 5500 filings. This data provides insights into company benefit plans, participant counts, and insurance arrangements.

**Schema:** `dol`
**Total Records:** ~1.3M across all tables
**Data Year:** 2023

---

## Table Inventory

| Table | Records | Description | Status |
|-------|---------|-------------|--------|
| `form_5500` | 230,009 | Full Form 5500 filings (100+ employees) | Production |
| `form_5500_sf` | 759,569 | Short Form 5500-SF filings (<100 employees) | Production |
| `schedule_a` | 336,817 | Insurance policy details | Production |
| `v_5500_summary` | 171,056 | Aggregated view of 5500 data | View |
| `v_schedule_a_carriers` | 13,856 | Insurance carrier summary | View |
| `violations` | 0 | DOL violation records | Empty |

---

## Column Reference

### dol.form_5500 (Large Filers)

Companies with 100+ plan participants file the full Form 5500.

#### Identification Columns

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `id` | DOL-5500-001 | integer | Auto-increment | Internal primary key |
| `ack_id` | DOL-5500-002 | varchar(30) | `YYYYMMDDHHMMSS...` | DOL acknowledgment ID |
| `company_unique_id` | DOL-5500-003 | text | `04.04.01.XX.XXXXX.XXX` | Barton ID (when linked) |
| `sponsor_dfe_ein` | DOL-5500-004 | varchar(9) | `XXXXXXXXX` | Employer Identification Number |

#### Company Information

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `sponsor_dfe_name` | DOL-5500-005 | varchar(70) | Mixed case | Legal company name |
| `spons_dfe_dba_name` | DOL-5500-006 | varchar(70) | Mixed case | "Doing Business As" name |
| `spons_dfe_care_of_name` | DOL-5500-007 | varchar(70) | Mixed case | C/O contact name |
| `business_code` | DOL-5500-008 | varchar(6) | `XXXXXX` | NAICS business code |

#### Mailing Address (PRIMARY - Use These!)

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `spons_dfe_mail_us_address1` | DOL-5500-009 | varchar(35) | Street | Mailing address line 1 |
| `spons_dfe_mail_us_address2` | DOL-5500-010 | varchar(35) | Suite/Apt | Mailing address line 2 |
| `spons_dfe_mail_us_city` | DOL-5500-011 | varchar(22) | City name | Mailing city |
| `spons_dfe_mail_us_state` | DOL-5500-012 | varchar(2) | `XX` | Mailing state (2-letter) |
| `spons_dfe_mail_us_zip` | DOL-5500-013 | varchar(12) | `XXXXX` or `XXXXX-XXXX` | Mailing ZIP code |

> **IMPORTANT:** Use `mail_*` columns for matching - `loc_*` columns are mostly NULL (92%)

#### Location Address (Often NULL)

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `spons_dfe_loc_us_address1` | DOL-5500-014 | varchar(35) | Street | Physical address line 1 |
| `spons_dfe_loc_us_address2` | DOL-5500-015 | varchar(35) | Suite/Apt | Physical address line 2 |
| `spons_dfe_loc_us_city` | DOL-5500-016 | varchar(22) | City name | Physical city |
| `spons_dfe_loc_us_state` | DOL-5500-017 | varchar(2) | `XX` | Physical state |
| `spons_dfe_loc_us_zip` | DOL-5500-018 | varchar(12) | `XXXXX` | Physical ZIP code |

#### Contact

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `spons_dfe_phone_num` | DOL-5500-019 | varchar(10) | `XXXXXXXXXX` | Phone number (no formatting) |

#### Filing Information

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `filing_status` | DOL-5500-020 | varchar(50) | Enum | `FILING_RECEIVED` |
| `date_received` | DOL-5500-021 | date | `YYYY-MM-DD` | Filing received date |
| `form_type` | DOL-5500-022 | varchar(10) | `5500` | Form type |
| `form_year` | DOL-5500-023 | integer | `YYYY` | Plan year (e.g., 2023) |
| `form_plan_year_begin_date` | DOL-5500-024 | date | `YYYY-MM-DD` | Plan year start |
| `form_tax_prd` | DOL-5500-025 | date | `YYYY-MM-DD` | Tax period end |

#### Filing Indicators

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `initial_filing_ind` | DOL-5500-026 | varchar(1) | `0`/`1` | First-time filing |
| `amended_ind` | DOL-5500-027 | varchar(1) | `0`/`1` | Amended filing |
| `final_filing_ind` | DOL-5500-028 | varchar(1) | `0`/`1` | Final/termination filing |
| `short_plan_yr_ind` | DOL-5500-029 | varchar(1) | `0`/`1` | Short plan year |
| `collective_bargain_ind` | DOL-5500-030 | varchar(1) | `0`/`1` | Union/collective bargaining |

#### Plan Information

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `plan_name` | DOL-5500-031 | varchar(140) | Mixed case | Benefit plan name |
| `plan_number` | DOL-5500-032 | varchar(3) | `001`-`999` | Plan number |
| `plan_eff_date` | DOL-5500-033 | date | `YYYY-MM-DD` | Plan effective date |
| `type_plan_entity_cd` | DOL-5500-034 | varchar(1) | `1`/`2`/`3` | Entity type code |
| `type_dfe_plan_entity_cd` | DOL-5500-035 | varchar(1) | `C`/`D`/`E` | DFE entity code |

#### Participant Counts (KEY METRICS)

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `tot_partcp_boy_cnt` | DOL-5500-036 | integer | Count | Total participants (beginning of year) |
| `tot_active_partcp_cnt` | DOL-5500-037 | integer | Count | Active participants |
| `rtd_sep_partcp_rcvg_cnt` | DOL-5500-038 | integer | Count | Retired/separated receiving benefits |
| `rtd_sep_partcp_fut_cnt` | DOL-5500-039 | integer | Count | Retired/separated future benefits |
| `subtl_act_rtd_sep_cnt` | DOL-5500-040 | integer | Count | Subtotal active/retired/separated |
| `benef_rcvg_bnft_cnt` | DOL-5500-041 | integer | Count | Beneficiaries receiving benefits |
| `tot_act_rtd_sep_benef_cnt` | DOL-5500-042 | integer | Count | Total all categories |
| `partcp_account_bal_cnt` | DOL-5500-043 | integer | Count | Participants with account balances |
| `sep_partcp_partl_vstd_cnt` | DOL-5500-044 | integer | Count | Separated partially vested |
| `contrib_emplrs_cnt` | DOL-5500-045 | integer | Count | Contributing employers |

#### Benefit Type Codes

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `type_pension_bnft_code` | DOL-5500-046 | varchar(40) | Codes | Pension benefit types (e.g., `1A1B`) |
| `type_welfare_bnft_code` | DOL-5500-047 | varchar(40) | Codes | Welfare benefit types (e.g., `4A4D4E`) |

#### Funding/Benefit Indicators

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `funding_insurance_ind` | DOL-5500-048 | varchar(1) | `0`/`1` | Funded by insurance |
| `funding_sec412_ind` | DOL-5500-049 | varchar(1) | `0`/`1` | Section 412 funding |
| `funding_trust_ind` | DOL-5500-050 | varchar(1) | `0`/`1` | Trust funded |
| `funding_gen_asset_ind` | DOL-5500-051 | varchar(1) | `0`/`1` | General assets funded |
| `benefit_insurance_ind` | DOL-5500-052 | varchar(1) | `0`/`1` | Benefits from insurance |
| `benefit_sec412_ind` | DOL-5500-053 | varchar(1) | `0`/`1` | Benefits from Sec 412 |
| `benefit_trust_ind` | DOL-5500-054 | varchar(1) | `0`/`1` | Benefits from trust |
| `benefit_gen_asset_ind` | DOL-5500-055 | varchar(1) | `0`/`1` | Benefits from general assets |

#### Schedule Attachments

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `sch_a_attached_ind` | DOL-5500-056 | varchar(1) | `0`/`1` | Schedule A (Insurance) attached |
| `num_sch_a_attached_cnt` | DOL-5500-057 | integer | Count | Number of Schedule A forms |
| `sch_c_attached_ind` | DOL-5500-058 | varchar(1) | `0`/`1` | Schedule C (Service Providers) |
| `sch_d_attached_ind` | DOL-5500-059 | varchar(1) | `0`/`1` | Schedule D (DFE/Participating Plans) |
| `sch_g_attached_ind` | DOL-5500-060 | varchar(1) | `0`/`1` | Schedule G (Financial Transactions) |
| `sch_h_attached_ind` | DOL-5500-061 | varchar(1) | `0`/`1` | Schedule H (Financial Info - Large) |
| `sch_i_attached_ind` | DOL-5500-062 | varchar(1) | `0`/`1` | Schedule I (Financial Info - Small) |
| `sch_mb_attached_ind` | DOL-5500-063 | varchar(1) | `0`/`1` | Schedule MB (Multiemployer DB) |
| `sch_sb_attached_ind` | DOL-5500-064 | varchar(1) | `0`/`1` | Schedule SB (Single Employer DB) |
| `sch_r_attached_ind` | DOL-5500-065 | varchar(1) | `0`/`1` | Schedule R (Retirement Plan) |

#### Administrator Information

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `admin_name` | DOL-5500-066 | varchar(70) | Mixed case | Plan administrator name |
| `admin_ein` | DOL-5500-067 | varchar(9) | `XXXXXXXXX` | Administrator EIN |
| `admin_us_state` | DOL-5500-068 | varchar(2) | `XX` | Administrator state |

#### System Columns

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `raw_payload` | DOL-5500-069 | jsonb | JSON | Original DOL JSON data |
| `created_at` | DOL-5500-070 | timestamp | `YYYY-MM-DD HH:MM:SS` | Record creation time |
| `updated_at` | DOL-5500-071 | timestamp | `YYYY-MM-DD HH:MM:SS` | Last update time |

---

### dol.form_5500_sf (Small Filers)

Companies with <100 plan participants file the Short Form 5500-SF.

> **Note:** Similar structure to form_5500 but with fewer fields. Key difference: uses `tot_active_partcp_boy_cnt` and `tot_active_partcp_eoy_cnt` for participant tracking.

| Column | ID | Type | Description |
|--------|-----|------|-------------|
| `id` | DOL-5500SF-001 | integer | Primary key |
| `ack_id` | DOL-5500SF-002 | varchar(255) | DOL acknowledgment ID |
| `sponsor_dfe_ein` | DOL-5500SF-003 | varchar(255) | Employer EIN |
| `sponsor_dfe_name` | DOL-5500SF-004 | varchar(255) | Company name |
| `spons_dfe_mail_us_*` | DOL-5500SF-005-009 | varchar(255) | Mailing address fields |
| `spons_dfe_loc_us_*` | DOL-5500SF-010-014 | varchar(255) | Location address fields |
| `spons_dfe_phone_num` | DOL-5500SF-015 | varchar(255) | Phone number |
| `plan_name` | DOL-5500SF-016 | varchar(255) | Plan name |
| `plan_number` | DOL-5500SF-017 | varchar(255) | Plan number |
| `tot_active_partcp_boy_cnt` | DOL-5500SF-018 | integer | Active participants (BOY) |
| `tot_partcp_boy_cnt` | DOL-5500SF-019 | integer | Total participants (BOY) |
| `tot_active_partcp_eoy_cnt` | DOL-5500SF-020 | integer | Active participants (EOY) |
| `tot_partcp_eoy_cnt` | DOL-5500SF-021 | integer | Total participants (EOY) |

---

### dol.schedule_a (Insurance Policies)

Details on insurance arrangements for benefit plans.

| Column | ID | Type | Format | Description |
|--------|-----|------|--------|-------------|
| `id` | DOL-SCHA-001 | integer | Auto-increment | Primary key |
| `ack_id` | DOL-SCHA-002 | varchar(30) | `YYYYMMDD...` | Links to form_5500 |
| `insurance_company_name` | DOL-SCHA-003 | varchar(140) | Mixed case | Insurance carrier name |
| `insurance_company_ein` | DOL-SCHA-004 | varchar(9) | `XXXXXXXXX` | Carrier EIN |
| `contract_number` | DOL-SCHA-005 | varchar(50) | Various | Policy/contract number |
| `policy_year_begin_date` | DOL-SCHA-006 | date | `YYYY-MM-DD` | Policy start date |
| `policy_year_end_date` | DOL-SCHA-007 | date | `YYYY-MM-DD` | Policy end date |
| `covered_lives` | DOL-SCHA-008 | integer | Count | Number of covered lives |
| `wlfr_bnft_health_ind` | DOL-SCHA-009 | varchar(1) | `0`/`1` | Health benefits |
| `wlfr_bnft_dental_ind` | DOL-SCHA-010 | varchar(1) | `0`/`1` | Dental benefits |
| `wlfr_bnft_vision_ind` | DOL-SCHA-011 | varchar(1) | `0`/`1` | Vision benefits |
| `wlfr_bnft_life_ind` | DOL-SCHA-012 | varchar(1) | `0`/`1` | Life insurance |
| `wlfr_bnft_stdisd_ind` | DOL-SCHA-013 | varchar(1) | `0`/`1` | Short-term disability |
| `wlfr_bnft_ltdisd_ind` | DOL-SCHA-014 | varchar(1) | `0`/`1` | Long-term disability |
| `insurance_commissions_fees` | DOL-SCHA-015 | numeric | Currency | Commissions/fees paid |
| `total_premiums_paid` | DOL-SCHA-016 | numeric | Currency | Total premiums |

---

## Data Quality Notes

### Known Issues

1. **Location State NULL (92%)**: `spons_dfe_loc_us_state` is NULL for 211,426 records. **Use `spons_dfe_mail_us_state` instead.**

2. **5500-SF Location Fields**: `spons_dfe_loc_us_state` contains international data (Canada provinces, etc.) - not reliable for US matching.

3. **Phone Number Formatting**: `spons_dfe_phone_num` has no formatting (10 digits, some with leading zeros).

4. **ZIP Code Formats**: Mix of 5-digit and 9-digit formats, some with leading zeros stripped.

### Matching Recommendations

**Best Match Strategy (State → City → Name):**
```sql
SELECT cm.*, d.sponsor_dfe_ein
FROM company.company_master cm
JOIN dol.form_5500 d
  ON cm.address_state = d.spons_dfe_mail_us_state       -- State first
  AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))  -- City second
  AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > 0.7   -- Name last
```

**Match Rate by Threshold:**
| Similarity | Companies | Percentage |
|------------|-----------|------------|
| > 0.9 | 3,867 | 7.3% |
| > 0.8 | 5,239 | 9.9% |
| > 0.7 | 5,972 | 11.3% |
| > 0.6 | 6,758 | 12.8% |
| > 0.5 | 7,795 | 14.7% |

---

## Geographic Coverage (Target States)

| State | Form 5500 | Form 5500-SF | Total |
|-------|-----------|--------------|-------|
| PA | 11,389 | TBD | 11,389+ |
| OH | 9,013 | TBD | 9,013+ |
| VA | 6,135 | TBD | 6,135+ |
| MD | 4,264 | TBD | 4,264+ |
| KY | 2,382 | TBD | 2,382+ |
| OK | 2,255 | TBD | 2,255+ |
| DE | 691 | TBD | 691+ |
| WV | 638 | TBD | 638+ |
| **Total** | **36,767** | - | **36,767+** |

---

## Related Documentation

- [PLE Hub-Spoke Schema Architecture](./Hub-Spoke-Schema-Architecture.md)
- [Company Master Schema](../../repo-data-diagrams/PLE_SCHEMA_REFERENCE.md)
- [Form 5500 Official Documentation](https://www.dol.gov/agencies/ebsa/employers-and-advisers/plan-administration-and-compliance/reporting-and-filing/form-5500)

---

**Last Updated:** 2025-12-02
**Data Source:** DOL EBSA Form 5500 Public Disclosure
**Schema Version:** 1.0
