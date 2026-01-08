# People Schema Orphan Views Report

**Generated:** 2026-01-08T09:06:35.562527
**Status:** INSPECTION ONLY — NO MODIFICATIONS

---

## Summary

Found **7** objects not in doctrine:

| Object | Type | Action |
|--------|------|--------|
| `person_scores` | BASE TABLE | Review before cleanup |
| `contact_enhanced_view` | VIEW | Review before cleanup |
| `due_email_recheck_30d` | VIEW | Review before cleanup |
| `next_profile_urls_30d` | VIEW | Review before cleanup |
| `v_slot_coverage` | VIEW | Review before cleanup |
| `vw_profile_monitoring` | VIEW | Review before cleanup |
| `vw_profile_staleness` | VIEW | Review before cleanup |

---

## Detailed Analysis

### `person_scores` (BASE TABLE)

**Columns:**
- `id`: integer
- `person_unique_id`: text
- `bit_score`: integer
- `confidence_score`: integer
- `calculated_at`: timestamp without time zone
- `score_factors`: jsonb
- `created_at`: timestamp without time zone
- `updated_at`: timestamp without time zone

**Dependent Objects:** None found

**Row Count:** 0

---

### `contact_enhanced_view` (VIEW)

**View Definition:**
```sql
 SELECT contact_id,
    full_name,
    first_name,
    last_name,
    COALESCE(
        CASE
            WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN concat(first_name, ' ', last_name)
            ELSE full_name
        END, full_name) AS computed_full_name,
    company_unique_id,
    slot_unique_id,
    title,
    seniority,
    department,
    email,
    email_status,
    email_last_verified_at,
    phone,
    mobile_phone_e164,
    work_phone_e164,
    linkedin_url,
    x_url,
 ...
```

**Columns:**
- `contact_id`: bigint
- `full_name`: text
- `first_name`: text
- `last_name`: text
- `computed_full_name`: text
- `company_unique_id`: text
- `slot_unique_id`: text
- `title`: text
- `seniority`: text
- `department`: text
- *(truncated...)*

**Dependent Objects:**
- `people.contact_enhanced_view`

---

### `due_email_recheck_30d` (VIEW)

**View Definition:**
```sql
 SELECT p.contact_id,
    p.full_name,
    p.title,
    p.email,
    v.email_status,
    v.email_checked_at,
    GREATEST(COALESCE(v.email_checked_at, '1970-01-01 00:00:00+00'::timestamp with time zone), '1970-01-01 00:00:00+00'::timestamp with time zone) AS last_checked_at
   FROM archive.people_contact_757489 p
     LEFT JOIN archive.people_contact_verification_757966 v ON v.contact_id = p.contact_id
  WHERE p.email IS NOT NULL AND (v.email_checked_at IS NULL OR v.email_checked_at < (now() - '...
```

**Columns:**
- `contact_id`: bigint
- `full_name`: text
- `title`: text
- `email`: text
- `email_status`: text
- `email_checked_at`: timestamp with time zone
- `last_checked_at`: timestamp with time zone

**Dependent Objects:**
- `marketing.vw_queue_sizes`
- `people.due_email_recheck_30d`

---

### `next_profile_urls_30d` (VIEW)

**View Definition:**
```sql
 SELECT contact_id,
    profile_source_url AS url,
    last_profile_checked_at AS last_checked_at
   FROM archive.people_contact_757489
  WHERE profile_source_url IS NOT NULL AND (last_profile_checked_at IS NULL OR last_profile_checked_at < (now() - '30 days'::interval));
```

**Columns:**
- `contact_id`: bigint
- `url`: text
- `last_checked_at`: timestamp with time zone

**Dependent Objects:**
- `marketing.vw_queue_sizes`
- `people.next_profile_urls_30d`

---

### `v_slot_coverage` (VIEW)

**View Definition:**
```sql
 SELECT cm.company_unique_id,
    cm.company_name,
    cs.slot_type,
        CASE
            WHEN cs.person_unique_id IS NOT NULL THEN 'FILLED'::text
            ELSE 'EMPTY'::text
        END AS status,
    pm.first_name,
    pm.last_name,
    pm.title,
    pm.linkedin_url
   FROM company.company_master cm
     JOIN people.company_slot cs ON cs.company_unique_id = cm.company_unique_id
     LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
  ORDER BY cm.company_name, cs.sl...
```

**Columns:**
- `company_unique_id`: text
- `company_name`: text
- `slot_type`: text
- `status`: text
- `first_name`: text
- `last_name`: text
- `title`: text
- `linkedin_url`: text

**Dependent Objects:**
- `people.v_slot_coverage`

---

### `vw_profile_monitoring` (VIEW)

**View Definition:**
```sql
 SELECT c.contact_id,
    c.full_name,
    c.email,
    c.profile_source_url,
    c.last_profile_checked_at,
    cv.email_status,
    cv.email_checked_at,
        CASE
            WHEN c.profile_source_url IS NULL THEN 'No Profile URL'::text
            WHEN c.last_profile_checked_at IS NULL THEN 'Never Checked'::text
            WHEN c.last_profile_checked_at < (now() - '60 days'::interval) THEN 'Very Stale (60+ days)'::text
            WHEN c.last_profile_checked_at < (now() - '30 days'::inter...
```

**Columns:**
- `contact_id`: bigint
- `full_name`: text
- `email`: text
- `profile_source_url`: text
- `last_profile_checked_at`: timestamp with time zone
- `email_status`: text
- `email_checked_at`: timestamp with time zone
- `profile_status`: text
- `email_verification_status`: text
- `assignment_status`: text
- *(truncated...)*

**Dependent Objects:**
- `people.vw_profile_monitoring`

---

### `vw_profile_staleness` (VIEW)

**View Definition:**
```sql
 SELECT c.contact_id,
    c.full_name,
    c.email,
    c.profile_source_url,
    cv.email_source_url,
        CASE
            WHEN c.last_profile_checked_at IS NULL THEN 'Never'::text
            WHEN c.last_profile_checked_at < (now() - '60 days'::interval) THEN 'Very Stale (60+ days)'::text
            WHEN c.last_profile_checked_at < (now() - '30 days'::interval) THEN 'Stale (30+ days)'::text
            WHEN c.last_profile_checked_at < (now() - '7 days'::interval) THEN 'Old (7+ days)'::tex...
```

**Columns:**
- `contact_id`: bigint
- `full_name`: text
- `email`: text
- `profile_source_url`: text
- `email_source_url`: text
- `profile_status`: text
- `email_status`: text

**Dependent Objects:**
- `people.vw_profile_staleness`

---

## Recommendations

⚠️ **DO NOT DELETE** without team review. These may be used by:

- Dashboards
- Reporting tools
- External integrations
- Legacy processes

**Next Steps:**

1. Review each view/table with the team
2. Check dashboard/report dependencies
3. If unused, mark for deprecation (not immediate deletion)
4. Document any legitimate uses in doctrine

---

**Certification Note:** Orphan objects do not block FULL PASS certification.
They are documented for future cleanup decision.