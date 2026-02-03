# Company Slot Filling Guide

## Overview

Each company in `people.company_slot` has 3 slots to fill:
- **CEO** - Chief Executive, President, Owner, Founder
- **CFO** - Chief Financial Officer, Controller, Finance Director
- **HR** - Human Resources Director, Manager, Benefits, Payroll

Total: 42,192 companies × 3 slots = **126,576 slots**

## Data Source: Hunter Enrichment

Primary source: `enrichment.hunter_contact` (248,071 contacts)

### Hunter Data Structure
| Column | Description |
|--------|-------------|
| `domain` | Company domain (join key) |
| `department` | Hunter's normalized department (Executive, Management, Finance, HR, etc.) |
| `job_title` | Normalized job title |
| `position_raw` | Original position text |
| `email` | Contact email |
| `first_name`, `last_name` | Name fields |

### Department Distribution in Hunter
```
Management:           39,984
Executive:            36,455
NULL (no department): 59,092
Sales:                29,627
Finance:              10,106
HR:                    6,638
```

## Slot Filling Strategy

### Join Path
```
people.company_slot.outreach_id 
→ outreach.company_target.outreach_id 
→ outreach.outreach.domain 
→ enrichment.hunter_contact.domain
```

### CEO Slots
**Departments searched:** Executive, Management

**Title priority (1 = highest):**
1. CEO, Chief Executive
2. President, Owner, Founder
3. Managing Director, General Manager
4. COO, Chief Operating
5. Partner, Vice President
6. Director
7. Any Executive title

### CFO Slots
**Departments searched:** Finance, Executive, Management, Operations & logistics

**Also searches ANY department (including NULL) for titles matching:**
- CFO, Chief Financial
- Controller, Comptroller
- Finance Director, VP Finance
- Treasurer
- Accounting Director/Manager
- Finance Manager

**Title priority:**
1. CFO, Chief Financial
2. Finance Director, VP Finance
3. Controller
4. Accounting Director
5. Finance/Accounting Manager
6. Treasurer, Financial Analyst
7. Accountant

### HR Slots
**Departments searched:** HR, Executive, Management, Operations & logistics

**Also searches ANY department (including NULL) for titles matching:**
- HR Director, Human Resources Director
- HR Manager, Human Resources Manager
- Head of Human Resources, Head of HR
- VP Human Resources, CHRO, Chief People Officer
- Senior HR titles
- HR Coordinator
- Benefits (Manager, Director, Coordinator, Administrator, Specialist)
- Payroll (Manager, Director, Coordinator, Administrator, Specialist)

**Title priority:**
1. CHRO, VP HR, Head of HR
2. HR Director
3. Senior HR, Senior HR Manager
4. HR Manager
5. Benefits, Payroll
6. HR Coordinator
7. HR Generalist, HR Specialist

### What We EXCLUDE from HR
- ❌ Recruiters
- ❌ Talent Acquisition
- ❌ Staffing
- ❌ Recruiting/Recruitment

**Reason:** Recruiters don't make benefits decisions. We want people who handle employee relations, benefits, and payroll.

## Running the Slot Filler

### Script Location
```
scripts/fill_slots_from_hunter.py
```

### Commands
```bash
# Dry run (see what would be filled)
python scripts/fill_slots_from_hunter.py --slot-type CEO --dry-run
python scripts/fill_slots_from_hunter.py --slot-type CFO --dry-run
python scripts/fill_slots_from_hunter.py --slot-type HR --dry-run

# Execute fills
python scripts/fill_slots_from_hunter.py --slot-type CEO --execute
python scripts/fill_slots_from_hunter.py --slot-type CFO --execute
python scripts/fill_slots_from_hunter.py --slot-type HR --execute
```

### What the Script Does
1. Finds empty slots for the given type
2. Joins to company domain via outreach tables
3. Finds matching Hunter contacts by department + title
4. Prioritizes by title (best titles first)
5. Creates `people_master` record for the person
6. Updates `company_slot` with `people_id` and `is_filled = true`

## Current Fill Status (2026-02-03)

| Slot | Filled | Total | % |
|------|--------|-------|---|
| CEO | 26,190 | 42,192 | 62.1% |
| CFO | 21,596 | 42,192 | 51.2% |
| HR | 22,416 | 42,192 | 53.1% |
| **TOTAL** | **70,202** | **126,576** | **55.5%** |

## Why ~45% Remain Unfilled

Hunter simply doesn't have contacts for those company domains. To fill more:
1. Add another data source (Apollo, ZoomInfo, LinkedIn)
2. Run the same pattern-matching approach against new data

## Key Learnings

### The "Double Filter" Problem
Initially we filtered by department THEN by title, which was too restrictive. Example:
- A "Controller" might be in Hunter's Executive department, not Finance
- An "HR Director" might be in Management department, not HR

**Solution:** For CFO and HR, we now use:
- Department-based matching (Finance, HR, Executive, Management, Ops) 
- **OR** Title-based matching (catches contacts in NULL/other departments)

### NULL Department Has Good Data
59,092 contacts have NULL department. Many have legitimate titles:
- Controllers: 503
- Various HR titles in there too

The title-based patterns catch these.

## Database Tables Involved

```sql
-- Slots to fill
people.company_slot (slot_id, company_id, slot_type, people_id, is_filled)

-- People we create
people.people_master (people_id, first_name, last_name, email, ...)

-- Company info
company.company_master (company_id, domain, ...)

-- Outreach linkage
outreach.outreach (outreach_id, domain, ...)
outreach.company_target (outreach_id, ...)

-- Source data
enrichment.hunter_contact (domain, email, job_title, department, ...)
```

## Maintenance

If you need to update the matching patterns, edit:
- `SLOT_DEPARTMENT_MAP` - which departments to search
- `TITLE_BASED_PATTERNS` - title patterns for CFO/HR (ignores department)
- `TITLE_PRIORITY` - ranking within each slot type

All in `scripts/fill_slots_from_hunter.py`.
