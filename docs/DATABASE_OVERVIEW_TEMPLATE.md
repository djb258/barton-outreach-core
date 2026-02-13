# Database Overview Template

> **Purpose**: Standard view for "what do we have" — used at full database level and at ZIP + radius market level.
> **Structure**: Sovereign States → CT → DOL → Blog → People → Messaging Lanes
> **Last Updated**: 2026-02-13

---

## BARTON OUTREACH — DATABASE OVERVIEW

### Total Companies: 94,129

---

### SOVEREIGN STATES (90,308 companies — excludes CA & NY)

| State | Companies | 50+ Emp% | DOL% | Blog% | Co LI% | CEO% | CEO LI% | CFO% | CFO LI% | HR% | HR LI% |
|-------|-----------|----------|------|-------|--------|------|---------|------|---------|-----|--------|
| **PA** | 17,566 | 42.1% | 76.6% | 99.9% | 50.6% | 66.1% | 53.4% | 58.9% | 47.5% | 58.6% | 48.1% |
| **OH** | 17,012 | 40.3% | 79.0% | 99.9% | 47.7% | 65.3% | 52.4% | 59.8% | 48.8% | 62.4% | 52.0% |
| **VA** | 12,645 | 44.1% | 76.2% | 99.8% | 51.9% | 68.1% | 55.6% | 61.3% | 51.1% | 59.5% | 49.8% |
| **NC** | 11,866 | 44.9% | 71.6% | 99.8% | 54.8% | 69.2% | 55.8% | 63.4% | 51.7% | 65.8% | 55.1% |
| **MD** | 9,784 | 39.0% | 79.6% | 99.9% | 45.1% | 65.2% | 52.4% | 61.0% | 49.9% | 62.7% | 52.2% |
| **KY** | 4,352 | — | 81.0% | 99.9% | 43.3% | 60.6% | 47.3% | 56.2% | 43.5% | 58.7% | 46.2% |
| **DC** | 2,621 | — | 98.6% | 100% | 47.0% | 84.4% | 69.1% | 84.5% | 70.6% | 84.3% | 70.7% |
| **OK** | 1,849 | — | 55.1% | 99.8% | 36.8% | 58.2% | 42.8% | 56.0% | 41.2% | 56.0% | 40.6% |

**Column Definitions:**
- **Companies**: Count of companies in `outreach.company_target` for that state
- **50+ Emp%**: % of companies with 50 or more employees
- **DOL%**: % of companies with a DOL EIN link (`outreach.dol`)
- **Blog%**: % of companies with a blog record (`outreach.blog`)
- **Co LI%**: % of companies with a LinkedIn URL (`cl.company_identity.linkedin_company_url`)
- **CEO/CFO/HR %**: % of companies with that slot filled (`people.company_slot`)
- **CEO/CFO/HR LI%**: % of companies where that filled slot has a LinkedIn URL (`people.people_master.linkedin_url`)

**Note**: Sovereign states exclude CA and NY. All percentages are against the state's company count.

---

### CT SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| **Has Employee Data** | 70,392 | 74.8% of companies |
| **50+ Employees** | 37,493 | 39.8% of companies |
| **Total Employees (50+)** | **16,205,443** | — |
| Email Method | 80,950 | 86.0% of companies |
| Domain Reachable | 52,870 | 85.4% of checked |
| Domain Unreachable | 9,047 | 14.6% of checked |

**Employee Size Bands (50+ only):**

| Band | Companies | Total Employees | % |
|------|-----------|-----------------|---|
| 50-100 | 24,179 | 1,233,129 | 64.5% |
| 101-250 | 6,795 | 1,365,795 | 18.1% |
| 501-1,000 | 2,696 | 1,350,696 | 7.2% |
| 1,001-5,000 | 2,657 | 2,659,657 | 7.1% |
| 5,001+ | 1,166 | 9,596,166 | 3.1% |
| **Total** | **37,493** | **16,205,443** | **100%** |

**Note**: Employee counts are based on Hunter enrichment band minimums (floor estimates). The 251-500 band shows zero because Hunter stores band minimums (51, 201, 501, 1001) — companies jump from the 101-250 band to the 501-1,000 band. Real employee totals would be higher than shown.

**Data Sources:**
- Employee Data: `outreach.company_target.employees`
- Email Method: `outreach.company_target.email_method`
- Domain Health: `outreach.sitemap_discovery.domain_reachable`

---

### DOL SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| **DOL Linked (EIN)** | 73,617 | 78.2% of companies |
| → Has Filing | 69,318 | 94.2% of DOL |
| → Renewal Month | 69,029 | 93.8% of DOL |
| → Carrier | 9,991 | 13.6% of DOL |
| → Broker/Advisor | 6,818 | 9.3% of DOL |

**Percentage Logic**: DOL Linked is measured against total companies. All sub-metrics (Filing, Renewal, Carrier, Broker) are measured against DOL Linked — because those data points only exist once the EIN match is made.

**Funding Type:**

| Type | Count | % of DOL |
|------|-------|----------|
| Pension Only | 54,673 | 74.3% |
| Fully Insured | 11,567 | 15.7% |
| Unknown | 4,588 | 6.2% |
| Self-Funded | 2,874 | 3.9% |

---

### BLOG SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| Blog Coverage | 93,596 | 99.4% of companies |
| Companies with Sitemap | 31,679 | 33.7% of companies |
| Companies with Source URLs | 40,381 | 42.9% of companies |
| Company LinkedIn | 45,057 | 47.9% of companies |

**Data Sources:**
- Blog Coverage: `outreach.blog`
- Sitemaps: `outreach.sitemap_discovery` (has_sitemap = TRUE)
- Source URLs: `company.company_source_urls` (about, press, leadership, team, careers, contact pages)
- Company LinkedIn: `cl.company_identity.linkedin_company_url`

---

### PEOPLE SUB-HUB

**Readiness Funnel:**

| Step | Count | % |
|------|-------|---|
| **Total Companies** | 94,129 | 100% |
| **At Least 1 Slot Filled** | 63,648 | 67.6% |
| **At Least 1 Person Reachable** | 60,180 | 63.9% |
| **Zero Slots (unreachable)** | 30,481 | 32.4% |

**Reachable** = has a verified email (outreach_ready = TRUE) OR a LinkedIn URL for at least one filled slot.

**Depth of Coverage:**

| Depth | Companies | All Have Email | All Have LinkedIn | Full Coverage (Both) |
|-------|-----------|----------------|-------------------|---------------------|
| **All 3 Slots Filled** | 54,949 | 32,585 (59.3%) | 41,689 (75.9%) | **25,014 (45.5%)** |
| **2 of 3 Filled** | 2,884 | 1,155 (40.0%) | 2,271 (78.7%) | 1,048 (36.3%) |
| **1 of 3 Filled** | 5,815 | 2,843 (48.9%) | 4,949 (85.1%) | 2,749 (47.3%) |
| **0 Filled** | 30,481 | — | — | — |

**Percentage Logic**: Each depth tier's email/LinkedIn/full coverage percentages are against the companies in that tier — not against CT total. The question is: "of the companies at this depth, how complete is our contact data?"

**Email Verification:**

| Metric | Count | % |
|--------|-------|---|
| People with Email | 181,478 | — |
| Email Verified | 145,358 | 80.1% of emails |
| Outreach Ready | 122,094 | 67.3% of emails |
| Companies with 1+ Ready Email | 47,504 | 50.5% of companies |

---

### THREE MESSAGING LANES

| Lane | Records |
|------|---------|
| Cold Outreach | 94,129 |
| Appointments Already Had | 771 |
| Fractional CFO Partners | 833 |

---
---

## BARTON OUTREACH — ZIP 24015 (Roanoke, VA) — 100-Mile Radius

### Total Companies: 3,561

---

### STATES IN RADIUS (excludes CA & NY)

| State | Companies | 50+ Emp% | DOL% | Blog% | Co LI% | CEO% | CEO LI% | CFO% | CFO LI% | HR% | HR LI% |
|-------|-----------|----------|------|-------|--------|------|---------|------|---------|-----|--------|
| **NC** | 1,749 | 44.6% | 71.1% | 99.9% | 53.5% | 68.8% | 81.2% | 63.0% | 82.1% | 65.5% | 84.3% |
| **VA** | 1,305 | 43.5% | 75.2% | 99.9% | 48.1% | 68.2% | 79.3% | 63.8% | 80.3% | 61.1% | 80.1% |
| **WV** | 141 | 36.2% | 70.2% | 100% | 47.5% | 52.5% | 60.8% | 47.5% | 62.7% | 48.9% | 60.9% |

---

### CT SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| **Has Employee Data** | 2,727 | 76.6% of companies |
| **50+ Employees** | 1,516 | 42.6% of companies |
| **Total Employees (50+)** | **623,416** | — |
| Email Method | 3,134 | 88.0% of companies |
| Domain Reachable | 1,987 | 84.7% of checked |
| Domain Unreachable | 360 | 15.3% of checked |

**Employee Size Bands (50+ only):**

| Band | Companies | Total Employees | % |
|------|-----------|-----------------|---|
| 50-100 | 1,018 | 51,918 | 67.2% |
| 101-250 | 260 | 52,260 | 17.2% |
| 501-1,000 | 94 | 47,094 | 6.2% |
| 1,001-5,000 | 102 | 102,102 | 6.7% |
| 5,001+ | 42 | 370,042 | 2.8% |
| **Total** | **1,516** | **623,416** | **100%** |

**Note**: Employee counts are based on Hunter enrichment band minimums (floor estimates). Real employee totals would be higher than shown.

---

### DOL SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| **DOL Linked (EIN)** | 2,685 | 75.4% of companies |
| → Has Filing | 2,533 | 94.3% of DOL |
| → Renewal Month | 2,558 | 95.3% of DOL |
| → Carrier | 428 | 15.9% of DOL |
| → Broker/Advisor | 275 | 10.2% of DOL |

**Funding Type:**

| Type | Count | % of DOL |
|------|-------|----------|
| Pension Only | 2,199 | 81.9% |
| Fully Insured | 224 | 8.3% |
| Self-Funded | 136 | 5.1% |

---

### BLOG SUB-HUB

| Metric | Count | % |
|--------|-------|---|
| Blog Coverage | 3,559 | 99.9% of companies |
| Companies with Sitemap | 1,212 | 34.0% of companies |
| Company LinkedIn | 1,685 | 47.3% of companies |

---

### PEOPLE SUB-HUB

**Readiness Funnel:**

| Step | Count | % |
|------|-------|---|
| **Total Companies** | 3,561 | 100% |
| **At Least 1 Slot Filled** | 2,499 | 70.2% |
| **At Least 1 Person Reachable** | 2,460 | 69.1% |
| **Zero Slots (unreachable)** | 1,062 | 29.8% |

**Depth of Coverage:**

| Depth | Companies | All Have Email | All Have LinkedIn | Full Coverage (Both) |
|-------|-----------|----------------|-------------------|---------------------|
| **All 3 Slots Filled** | 2,168 | 1,246 (57.5%) | 1,610 (74.3%) | **914 (42.2%)** |
| **2 of 3 Filled** | 110 | 47 (42.7%) | 95 (86.4%) | 43 (39.1%) |
| **1 of 3 Filled** | 221 | 110 (49.8%) | 196 (88.7%) | 108 (48.9%) |
| **0 Filled** | 1,062 | — | — | — |

**Email Verification:**

| Metric | Count | % |
|--------|-------|---|
| People with Email | 6,937 | — |
| Email Verified | 5,511 | 79.4% of emails |
| Outreach Ready | 4,735 | 68.3% of emails |

---

### THREE MESSAGING LANES (in radius)

| Lane | Records |
|------|---------|
| Cold Outreach | 3,561 |
| Appointments Already Had | 5 |

---
---

## HOW TO USE THIS TEMPLATE

### Full Database View
Run with no filters — shows the entire outreach universe.

### ZIP + Radius View
Same structure, but scoped to companies within a geographic radius:
- **Sovereign States** → becomes a state breakdown of companies within the radius
- **CT/DOL/Blog/People** → same metrics, same percentage logic, just filtered to the market
- **Total Companies** → becomes the count within the radius instead of 94,129

### Section Order
1. **Sovereign States** — always lead with geography (includes 50+ Emp% column)
2. **CT Sub-Hub** — employee data, size bands (50+ only with total employees), domain health, email method
3. **DOL Sub-Hub** — EIN linkage (% of companies), then filing/renewal/carrier/broker (% of DOL), funding type
4. **Blog Sub-Hub** — coverage, sitemaps, source URLs, company LinkedIn
5. **People Sub-Hub** — readiness funnel, depth of coverage, email verification
6. **Three Messaging Lanes** — lane counts

### Key Principles
1. **Sovereign States first** — always lead with geography
2. **CT = company profile** — employee bands (50+ only, with total employees per band), domain health
3. **DOL cascades off DOL Linked** — sub-metrics use DOL as denominator
4. **Blog includes sitemaps** — sitemap coverage is a key intelligence asset
5. **People = readiness story** — not "how many slots" but "can we reach anyone and how deep"
6. **No CLS/BIT scores** — scoring is internal, not part of the sales view
7. **Exclude CA and NY** — not sovereign states for this operation
8. **Employee bands exclude below 50** — target market is 50+ employees
9. **Employee totals are floor estimates** — Hunter stores band minimums, real totals would be higher

### Data Sources Quick Reference
| Metric | Source Table | Join Key |
|--------|-------------|----------|
| Companies | `outreach.company_target` | `outreach_id` |
| Employee Count | `outreach.company_target.employees` | direct |
| DOL | `outreach.dol` | `outreach_id` |
| Blog | `outreach.blog` | `outreach_id` |
| Sitemaps | `outreach.sitemap_discovery` | `outreach_id` |
| Source URLs | `company.company_source_urls` | `company_unique_id` (bridge) |
| Company LinkedIn | `cl.company_identity.linkedin_company_url` | `outreach_id` via `outreach.outreach` |
| Slot Fill | `people.company_slot` | `outreach_id` |
| Person LinkedIn | `people.people_master.linkedin_url` | `people_id` via `company_slot` |
| Email Verification | `people.people_master.outreach_ready` | `people_id` |
| Domain Health | `outreach.sitemap_discovery.domain_reachable` | `outreach_id` |
| Geographic Filter | `reference.us_zip_codes` | Haversine on `lat`/`lng`, match via `postal_code` |

---

*Template created: 2026-02-13*
*Source queries: See `hubs/coverage/imo/middle/run_coverage.py` for ZIP-scoped version*
