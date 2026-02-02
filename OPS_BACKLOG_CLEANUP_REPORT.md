# Ops Backlog Cleanup Report

**Execution Date**: 2026-02-02 13:40:17 UTC
**Executor**: ops_cleanup_agent
**Mode**: Operations Cleanup (No Doctrine Changes)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Errors Processed | 35,197 |
| DOL Errors Parked (Structural) | 29,740 |
| CT Errors Parked | 26 |
| CT Errors Retried | 4,378 |
| People Errors Parked | 0 |
| People Errors Retried | 1,053 |
| CT Records Reset to Pending | 13 |

*Note: DOL errors were parked in first execution run.*

---

## Promotion Readiness Delta

| Tier | Before | After | Delta |
|------|--------|-------|-------|
| NOT_READY | 4,314 | 4,314 | 0 |
| TIER_0_ANCHOR_DONE | 34,124 | 34,124 | 0 |
| TIER_2_ENRICHMENT_COMPLETE | 3,737 | 3,737 | 0 |
| TIER_3_CAMPAIGN_READY | 17 | 17 | 0 |

---

## Actions Taken

### DOL Errors (Structural - Parked)

These errors represent companies with no DOL filing match. Retrying won't resolve them.

- **NO_MATCH**: Company name doesn't match any DOL Form 5500 filings
- **NO_STATE**: Missing state information for DOL lookup

Action: Parked with reason `STRUCTURAL_NO_DOL_MATCH`

### CT Errors (CT-M-NO-MX)

These errors indicate the domain has no MX record (no email server).

- Errors with retry_count >= 2: **Parked** (unlikely to resolve)
- Errors with retry_count < 2: **Retried** (DNS can change)

### People Errors

General processing errors during people enrichment.

- Errors with retry_count >= 2: **Parked**
- Errors with retry_count < 2: **Retried**

### CT Record Resets

Failed CT records with no remaining blocking errors were reset to `pending` to allow pipeline retry.

---

## Why NOT_READY Records Remain

The majority of NOT_READY records are not due to blocking errors but due to **missing DONE state criteria**:

| Reason | Count | Notes |
|--------|-------|-------|
| CT execution_status = 'pending' | ~2,700 | Needs pipeline execution |
| CT execution_status = 'failed' | ~855 | Has blocking errors |
| No CT record | ~767 | Needs pipeline to create |

These require **pipeline execution**, not ops cleanup:
- Company Target pipeline must run to populate email_method, confidence_score
- DOL pipeline must run to match EIN/filings
- People pipeline must run to assign slots

---

## Compliance Statement

This cleanup operation:
- [x] Did NOT modify doctrine, policies, or enforcement logic
- [x] Did NOT bypass promotion gates
- [x] Operated only on existing records
- [x] Maintained full audit trail
- [x] Preferred RETRY -> RESOLVE over PARK -> ARCHIVE
- [x] Parked only structural/unrecoverable errors

---

## Audit Trail Summary

| Action | Count |
|--------|-------|
| PARK | 26 |
| RETRY | 5,431 |
| RESET | 13 |
| **Total** | 5,470 |

<details>
<summary>Click to expand audit log sample (first 50 entries)</summary>

```json
[
  {
    "timestamp": "2026-02-02T13:37:18.665045+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "b0dde39a-063c-4425-b2c5-3aaf9f22488f",
    "details": {
      "outreach_id": "49c8d32b-a24f-4888-a30a-6f62ec716a48",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.701633+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "f75d9179-65bc-483e-9805-8173058952dc",
    "details": {
      "outreach_id": "0c966848-0001-4ed8-8339-fdbfc0e03268",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.732485+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "293518b0-cd0e-4b2b-97a7-e67e6ee92cd8",
    "details": {
      "outreach_id": "0181a702-74fe-4685-897d-aecb415ab26e",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.768119+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "7136b574-53cd-4af9-b012-0058add077fb",
    "details": {
      "outreach_id": "bbded0fd-f26a-443d-aab9-a18a78cbfdad",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.795904+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "3c8a5fc0-739c-443b-aca3-8f474104a182",
    "details": {
      "outreach_id": "0f39f6cd-08ae-4aaa-81c0-39b63e668c83",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.828087+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "47b8cd05-0ad5-4afa-b4f0-7dfd105cae9b",
    "details": {
      "outreach_id": "1028fcd8-cc6e-4bfb-9b94-48bc06895152",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.860584+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "45cfa2e6-bbb1-4ce2-9e4d-cf3bf63ed8c6",
    "details": {
      "outreach_id": "1f76f113-7ecd-410c-b938-4c210e114702",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.892160+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "dbbd0438-1cc0-4a2f-a363-2b907442e0d0",
    "details": {
      "outreach_id": "49d0b9b9-d7a6-48a7-841d-a07130abd3ed",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.922113+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "c3cddb05-530c-45e5-820c-61ea0db0cf53",
    "details": {
      "outreach_id": "8a0a914d-6706-4898-8bba-1cc8ed273383",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.951870+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "81552136-0bbf-474b-a16d-af72c8f04432",
    "details": {
      "outreach_id": "95decfae-72a9-4e7f-bea3-a053004663e2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:18.990372+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "34a15b40-a209-45fa-872c-f5bc632b3e9b",
    "details": {
      "outreach_id": "6f32c61e-de59-4c51-ab39-ec2a70a94644",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.019849+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "1afe04f7-ac34-4530-a859-bdabca2a6418",
    "details": {
      "outreach_id": "b1377065-4010-4c98-a218-0e14d4aca422",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.048300+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "d4d9a015-07b1-42c6-bcf4-43809ee5884a",
    "details": {
      "outreach_id": "c99e577c-3f82-4b55-8654-675c56c62073",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.075941+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "bd57fa47-0fd3-4468-832a-852dcd64cb6f",
    "details": {
      "outreach_id": "dd1405fc-bc18-429b-bf72-0b8426f6233d",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.111747+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "96b8a00b-82e4-4f9f-8528-9991160425da",
    "details": {
      "outreach_id": "d23ab97a-b875-4031-915c-09af49369265",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.139946+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "28d3aaa7-8400-4ede-b73a-3c45e220b334",
    "details": {
      "outreach_id": "7747d9d5-73cb-4b1c-a8e6-47e0d1cd41c8",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.170230+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "0ba1d137-808b-4441-b957-d53bbbc7c9ec",
    "details": {
      "outreach_id": "71840fee-0b1e-4678-9134-ea07cb8baca3",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.199350+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "96ebd9b9-c65f-4c50-9771-e56839b338e5",
    "details": {
      "outreach_id": "161abe21-e4b9-4d90-86ab-359d2e22672c",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.227301+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "a9b2585d-0086-4513-b80b-642e80574744",
    "details": {
      "outreach_id": "10ff592f-2400-458c-8e6c-0ed7607912a9",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.264212+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "c0611cd8-6f99-4ac0-856a-66dec01b90a0",
    "details": {
      "outreach_id": "14d9aa6c-dfdd-4eba-8908-306331ea66a2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.292155+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "4694c535-4207-4ef4-a62f-2c9290672518",
    "details": {
      "outreach_id": "8684a20d-8bcc-4e1b-9768-ddcab2235659",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.332236+00:00",
    "action": "PARK",
    "entity_type": "ct_error",
    "entity_id": "a3dbe1ea-3dca-4e60-82a4-4fbb285922e3",
    "details": {
      "outreach_id": "23c69c48-436c-41ca-8858-c202e1ee7063",
      "reason": "NO_MX_AFTER_RETRIES",
      "retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.364295+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "46da2c45-a278-405f-9869-5f1756a90789",
    "details": {
      "outreach_id": "f2196d6b-8bd5-4cff-9966-43a4a7770cd2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.392343+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "07de8925-7454-4bc9-882c-3491aa2b5059",
    "details": {
      "outreach_id": "780428d2-ee00-4601-90c3-892c24911685",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.421339+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "fa8c2584-be39-4a39-9ea2-bd407deae517",
    "details": {
      "outreach_id": "91c452ca-b4eb-4e4e-9df8-17c42a497492",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.451328+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "828d54fb-6316-473c-9083-c3f1f403d81c",
    "details": {
      "outreach_id": "69ba60e1-9b1f-4d34-9a50-af0c01c333db",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.484506+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "7212e6b6-845a-4e8c-92d0-795dc5d484ce",
    "details": {
      "outreach_id": "0ee1d3cd-abd6-45b9-b6a5-f1c54470c232",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.513328+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "6600fb56-c5f7-46dc-b1ca-09dc6e28476f",
    "details": {
      "outreach_id": "664dc1f9-7fce-4fbd-bd90-5eb206f273f1",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.543691+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "5b46b9bf-4d55-4d67-9aca-c49a1a8590a8",
    "details": {
      "outreach_id": "6974a600-dca7-4f69-a388-d4dd4358bbf9",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.572538+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "9f5990ca-f62e-424d-848c-e5a14981d900",
    "details": {
      "outreach_id": "c73e7221-b44d-45ef-bf87-bf46c8df19a9",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.600501+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "411699b4-b213-49b4-99b7-54b79b70fb0c",
    "details": {
      "outreach_id": "c691cbb7-c092-4bfb-a2ff-fc0cc94551bc",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.628814+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "ca4cae06-f652-4ec0-8210-b3c796e64b9c",
    "details": {
      "outreach_id": "ae339ed8-0d44-4a5c-b09c-ad985a531916",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.660005+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "cf7c8c0c-6a1b-4161-a64b-915ab9626059",
    "details": {
      "outreach_id": "dbb72cbb-2789-4f01-8187-9a33ecbe2ce5",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.696503+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "1211e6e3-1506-4a8e-b55e-67a6b54b6eab",
    "details": {
      "outreach_id": "ac49832a-aad1-4e39-8897-18b4b9534122",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.726861+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "27939a05-befe-4fa8-b5e0-6e710c728c69",
    "details": {
      "outreach_id": "ea3738f9-909e-4a5a-8921-d0ead6cc1c97",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.757157+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "7d704ba5-2db7-42d6-a4d8-5267d217e961",
    "details": {
      "outreach_id": "865f84f3-db00-472b-b844-031f5db6c839",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.787648+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "7c5e1d6b-41f4-415f-a7e3-68eeb475c16d",
    "details": {
      "outreach_id": "6c2f38e3-5426-48fc-8e32-bcaff286bcf2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.823770+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "2011a495-9b42-4dad-9ed5-1fd671523d0e",
    "details": {
      "outreach_id": "48da3cd8-fc58-4f55-b413-bf5fe1b538e5",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.855427+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "f28abaa2-b250-462c-af75-1d35e17314d9",
    "details": {
      "outreach_id": "4b76da15-7071-4e5a-951e-7e1457c466af",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.883683+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "bcce9028-855c-44ab-9372-d69c61f94368",
    "details": {
      "outreach_id": "ab636bc5-ca48-4ab2-a4e5-a99a42f7e23c",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.916105+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "ad728979-88a2-4367-a527-c67e841c23be",
    "details": {
      "outreach_id": "bdff3ef4-6134-4169-acfb-ffa76daee86a",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.947406+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "c48ccda7-2545-4d90-9d08-2288b389a6aa",
    "details": {
      "outreach_id": "d6ca1dcd-745c-4d52-82e3-f6aed68a0de5",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:19.976886+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "a9501087-b478-4254-9160-0e3f7b5edc57",
    "details": {
      "outreach_id": "7d5899d6-2427-4680-b7c6-ef1642ce9ef6",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.011339+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "045abeab-cf24-464a-8c0c-9533321c8e2c",
    "details": {
      "outreach_id": "b04e998b-e9d1-4395-884a-5f9dc00eb9a8",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.043840+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "0dc2a1e6-39bf-448e-b1ff-ef8bf9053901",
    "details": {
      "outreach_id": "d7bea14b-07d3-4ee1-b182-58259c98b2d2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.071739+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "5d8fd8f3-9cde-43d8-a2f0-5a1465ba9028",
    "details": {
      "outreach_id": "3e0684cd-a1d0-4b82-8410-9f5ae292850c",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.107752+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "72832030-8831-4ebe-af46-278bc9682644",
    "details": {
      "outreach_id": "94f288ca-9467-4570-a327-fa79038ccb36",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.139268+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "0c07ebd0-8cd7-46e5-b146-a62a5cb71d48",
    "details": {
      "outreach_id": "5a25fe19-82f1-4128-8666-3842c28444c2",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.171799+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "9c3ebf0f-bfe4-4695-b4fb-41e4ae9ffacc",
    "details": {
      "outreach_id": "808e31c3-b9f3-4362-ba70-6b677d3319b1",
      "new_retry_count": 2
    }
  },
  {
    "timestamp": "2026-02-02T13:37:20.199972+00:00",
    "action": "RETRY",
    "entity_type": "ct_error",
    "entity_id": "73622397-dddf-4b6d-a13b-e39a7c27c434",
    "details": {
      "outreach_id": "9737240a-9b1a-4666-8292-744878fb79bc",
      "new_retry_count": 2
    }
  }
]
```

</details>

---

## Recommendations (For Pipeline Team)

1. **Run Company Target pipeline** on 2,700+ pending records
2. **Run DOL pipeline** for EIN matching
3. **Schedule daily governance job**: `SELECT * FROM shq.fn_run_error_governance_jobs()`

---

**Generated by**: ops_cleanup_agent
**Timestamp**: 2026-02-02T13:40:17.102557+00:00Z
