-- Company Grid View for Process 100 (LCS Grid Reader)
-- One row per company (outreach_id). Reads from CEO slot as the company-level record.
-- Four sub-hub columns: CT, DOL, SP, People
-- Each column has checkboxes (boolean) and timestamps (last_changed)
-- Process 100 reads this. 300 and 200 write to the source tables.

CREATE VIEW IF NOT EXISTS company_grid AS
SELECT
    sw.outreach_id,
    sw.company_name,
    sw.domain,
    sw.city,
    sw.state,
    sw.employees,
    sw.industry,

    -- CT (Company Target) — checkboxes
    CASE WHEN sw.company_name IS NOT NULL AND sw.company_name != '' THEN 1 ELSE 0 END AS ct_has_name,
    CASE WHEN sw.domain IS NOT NULL AND sw.domain != '' THEN 1 ELSE 0 END AS ct_has_domain,
    CASE WHEN sw.city IS NOT NULL AND sw.city != '' THEN 1 ELSE 0 END AS ct_has_location,
    CASE WHEN sw.employees IS NOT NULL AND sw.employees > 0 THEN 1 ELSE 0 END AS ct_has_employees,
    CASE WHEN sw.ein IS NOT NULL AND sw.ein != '' THEN 1 ELSE 0 END AS ct_has_ein,

    -- DOL — one checkbox: is the EIN linked? If yes, all DOL views are accessible.
    CASE WHEN sw.ein IS NOT NULL AND sw.ein != '' THEN 1 ELSE 0 END AS dol_ein_linked,

    -- SP (Social Platform) — checkboxes + timestamps
    CASE WHEN sw.about_url IS NOT NULL AND sw.about_url != '' THEN 1 ELSE 0 END AS sp_has_about_page,
    CASE WHEN sw.blog_source_url IS NOT NULL AND sw.blog_source_url != '' THEN 1 ELSE 0 END AS sp_has_blog,
    CASE WHEN sw.recon_linkedin_company IS NOT NULL AND sw.recon_linkedin_company != '' THEN 1 ELSE 0 END AS sp_has_linkedin,
    CASE WHEN sw.recon_platform_urls IS NOT NULL AND sw.recon_platform_urls != '' AND sw.recon_platform_urls != '{}' THEN 1 ELSE 0 END AS sp_has_platforms,
    sw.last_recon_at AS sp_last_checked,

    -- People — three slots per company (CEO, CFO, HR)
    -- CEO
    sw.has_name AS people_ceo_has_name,
    sw.has_email AS people_ceo_has_email,
    sw.has_verified_email AS people_ceo_has_verified_email,
    sw.has_linkedin AS people_ceo_has_linkedin,
    sw.is_filled AS people_ceo_is_filled,
    sw.person_found_at AS people_ceo_found_at,

    -- CFO (joined from workbench)
    cfo.has_name AS people_cfo_has_name,
    cfo.has_email AS people_cfo_has_email,
    cfo.has_verified_email AS people_cfo_has_verified_email,
    cfo.has_linkedin AS people_cfo_has_linkedin,
    cfo.is_filled AS people_cfo_is_filled,
    cfo.person_found_at AS people_cfo_found_at,

    -- HR (joined from workbench)
    hr.has_name AS people_hr_has_name,
    hr.has_email AS people_hr_has_email,
    hr.has_verified_email AS people_hr_has_verified_email,
    hr.has_linkedin AS people_hr_has_linkedin,
    hr.is_filled AS people_hr_is_filled,
    hr.person_found_at AS people_hr_found_at,

    -- Baseline + Changed timestamps (Grid Reader pattern)
    -- Baseline = when we FIRST captured this data
    -- Changed = when the value actually MOVED (THE signal)
    sw.ct_baseline_at,
    sw.ct_changed_at,
    sw.dol_baseline_at,
    sw.dol_changed_at,
    sw.sp_baseline_at,
    sw.sp_changed_at,
    sw.people_baseline_at,
    sw.people_changed_at,

    -- Signal indicators (computed from changed timestamps)
    CASE WHEN sw.last_recon_at > datetime('now', '-30 days') THEN 1 ELSE 0 END AS signal_recent_recon,
    CASE WHEN sw.sp_changed_at > datetime('now', '-30 days') THEN 1 ELSE 0 END AS signal_sp_changed,
    CASE WHEN sw.dol_changed_at > datetime('now', '-30 days') THEN 1 ELSE 0 END AS signal_dol_changed,
    CASE WHEN sw.people_changed_at > datetime('now', '-30 days')
         OR cfo.people_changed_at > datetime('now', '-30 days')
         OR hr.people_changed_at > datetime('now', '-30 days')
         THEN 1 ELSE 0 END AS signal_people_changed,
    CASE WHEN sw.person_found_at > datetime('now', '-30 days')
         OR cfo.person_found_at > datetime('now', '-30 days')
         OR hr.person_found_at > datetime('now', '-30 days')
         THEN 1 ELSE 0 END AS signal_recent_person_found,

    -- Completeness scores
    (CASE WHEN sw.company_name IS NOT NULL AND sw.company_name != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.domain IS NOT NULL AND sw.domain != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.city IS NOT NULL AND sw.city != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.employees IS NOT NULL AND sw.employees > 0 THEN 1 ELSE 0 END
     + CASE WHEN sw.ein IS NOT NULL AND sw.ein != '' THEN 1 ELSE 0 END
    ) AS ct_score,

    CASE WHEN sw.ein IS NOT NULL AND sw.ein != '' THEN 1 ELSE 0 END AS dol_score,

    (CASE WHEN sw.about_url IS NOT NULL AND sw.about_url != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.blog_source_url IS NOT NULL AND sw.blog_source_url != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.recon_linkedin_company IS NOT NULL AND sw.recon_linkedin_company != '' THEN 1 ELSE 0 END
     + CASE WHEN sw.recon_platform_urls IS NOT NULL AND sw.recon_platform_urls != '' AND sw.recon_platform_urls != '{}' THEN 1 ELSE 0 END
    ) AS sp_score,

    -- People scores per slot
    (sw.has_name + sw.has_email + sw.has_verified_email + sw.has_linkedin) AS people_ceo_score,
    (COALESCE(cfo.has_name,0) + COALESCE(cfo.has_email,0) + COALESCE(cfo.has_verified_email,0) + COALESCE(cfo.has_linkedin,0)) AS people_cfo_score,
    (COALESCE(hr.has_name,0) + COALESCE(hr.has_email,0) + COALESCE(hr.has_verified_email,0) + COALESCE(hr.has_linkedin,0)) AS people_hr_score,

    -- Total people score across all 3 slots (max 12)
    (sw.has_name + sw.has_email + sw.has_verified_email + sw.has_linkedin
     + COALESCE(cfo.has_name,0) + COALESCE(cfo.has_email,0) + COALESCE(cfo.has_verified_email,0) + COALESCE(cfo.has_linkedin,0)
     + COALESCE(hr.has_name,0) + COALESCE(hr.has_email,0) + COALESCE(hr.has_verified_email,0) + COALESCE(hr.has_linkedin,0)
    ) AS people_total_score,

    -- Slots filled count (0-3)
    (sw.is_filled + COALESCE(cfo.is_filled,0) + COALESCE(hr.is_filled,0)) AS people_slots_filled,

    sw.readiness_tier

FROM slot_workbench sw
LEFT JOIN slot_workbench cfo ON sw.outreach_id = cfo.outreach_id AND cfo.slot_type = 'CFO'
LEFT JOIN slot_workbench hr ON sw.outreach_id = hr.outreach_id AND hr.slot_type = 'HR'
WHERE sw.slot_type = 'CEO';
