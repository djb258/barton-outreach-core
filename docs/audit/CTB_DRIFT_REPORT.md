# CTB Drift Detection Report

**Generated**: 2026-02-06T10:35:32.951520

---

## Summary

| Drift Type | Count |
|------------|-------|
| MISSING_CONTRACT | 10 |
| DEPRECATED_WITH_DATA | 13 |
| **TOTAL** | **23** |

---

## Drift Items

| Type | Schema | Object | Notes |
|------|--------|--------|-------|
| MISSING_CONTRACT | cl | company_identity_archive.sovereign_company_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | cl | company_identity_excluded.outreach_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | cl | company_identity_excluded.sovereign_company_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | cl | v_company_lifecycle_status.outreach_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | cl | v_company_lifecycle_status.sovereign_company_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | cl | v_company_promotable.sovereign_company_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | outreach | appointments.outreach_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | outreach | bit_errors.outreach_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | outreach | bit_input_history.outreach_id | Key column lacks CTB_CONTRACT comment |
| MISSING_CONTRACT | outreach | bit_scores_archive.outreach_id | Key column lacks CTB_CONTRACT comment |
| DEPRECATED_WITH_DATA | company | company_master | 74641 rows in deprecated table |
| DEPRECATED_WITH_DATA | company | company_slots | 1359 rows in deprecated table |
| DEPRECATED_WITH_DATA | company | company_source_urls | 104012 rows in deprecated table |
| DEPRECATED_WITH_DATA | company | message_key_reference | 8 rows in deprecated table |
| DEPRECATED_WITH_DATA | company | pipeline_events | 2185 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | company_master | 512 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | failed_company_match | 32 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | failed_email_verification | 310 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | failed_low_confidence | 5 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | failed_no_pattern | 6 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | failed_slot_assignment | 222 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | people_master | 149 rows in deprecated table |
| DEPRECATED_WITH_DATA | marketing | review_queue | 516 rows in deprecated table |
