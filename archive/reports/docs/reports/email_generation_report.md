# Email Generation Report - 2026-02-05

## Executive Summary

Successfully generated **3,473 emails** for people missing them using company email patterns, improving email coverage from **96.64%** to **98.96%** (+2.32%).

## Results

### Before Generation
- **Total people (filled slots)**: 149,616
- **Has email**: 144,585 (96.64%)
- **Missing email**: 5,031

### After Generation
- **Total people (filled slots)**: 149,616
- **Has email**: 148,057 (98.96%)
- **Missing email**: 1,559

### Improvement
- **Emails generated**: 3,473
- **Coverage improvement**: +2.32%
- **Reduction in missing emails**: 3,472 (69.0% of missing emails resolved)

## Methodology

### Supported Hunter Patterns (11 total)
1. `{first}.{last}` - john.smith@domain.com
2. `{f}{last}` - jsmith@domain.com
3. `{first}` - john@domain.com
4. `{first}{last}` - johnsmith@domain.com
5. `{first}{l}` - johns@domain.com
6. `{f}.{last}` - j.smith@domain.com
7. `{last}` - smith@domain.com
8. `{last}{f}` - smithj@domain.com
9. `{first}.{l}` - john.s@domain.com
10. `{first}_{last}` - john_smith@domain.com
11. `{last}{first}` - smithjohn@domain.com (attempted but 0 records)

### Name Sanitization
- All names sanitized to alphanumeric characters only (removed spaces, punctuation, Unicode)
- Pattern matching works with or without `@domain` suffix in `email_method` field

## Remaining Missing Emails (1,559)

### Breakdown

#### 1. NULL email_method (848 people, 54.4%)
Companies without a discovered email pattern in `outreach.company_target`.

**By Slot Type:**
- CEO: 478 (56.4%)
- HR: 216 (25.5%)
- CFO: 154 (18.2%)

**Sample domains:**
- shockeybuilds.com
- unitekglobalservices.com
- rwndevelopmentgroup.com
- ridesofconover.com
- servicemasterrestore.com

**Root Cause**: Company Target phase did not discover an email pattern for these companies.

**Recommendation**: Re-run Phase 3 (Email Pattern Waterfall) for these 13,181 companies with NULL email_method.

#### 2. Invalid Names (711 people, 45.6%)
People whose names cannot be sanitized to valid email addresses.

**Examples of Invalid Names:**

| Person ID | First Name | Last Name | Issue |
|-----------|------------|-----------|-------|
| 04.04.02.99.15986.986 | Raju | . | Last name is just "." |
| 04.04.02.99.24891.891 | Dr. Richa | . | Last name is just "." |
| 04.04.02.99.29701.701 | 盛 晖 | Jack Sheng | First name is Chinese characters (sanitizes to empty) |
| 04.04.02.99.15510.510 | ሾላ | S. | First name is Amharic characters (sanitizes to empty) |
| 04.04.02.99.29815.815 | 'Paul | ' | Last name is Unicode quote (sanitizes to empty) |
| 04.04.02.99.41367.367 | Pea | -. | Last name is just "-." |

**Root Cause**: Data quality issues in intake. Names with:
- Non-Latin characters (Chinese, Amharic, etc.)
- Invalid last names (just punctuation)
- Unicode quotes and special characters

**Recommendation**: Implement data validation in intake pipeline to flag/fix invalid names.

## Email Pattern Distribution (Company Level)

Top patterns by company count:

| Pattern | Companies | % of Total |
|---------|-----------|------------|
| {first}.{last} | 43,999 | 43.9% |
| {first} | 16,206 | 16.2% |
| {f}{last} | 15,321 | 15.3% |
| NULL | 13,181 | 13.2% |
| {first}{l} | 1,421 | 1.4% |
| {last} | 1,289 | 1.3% |
| {first}{last} | 1,193 | 1.2% |
| {f}.{last} | 645 | 0.6% |
| {last}{f} | 441 | 0.4% |
| {last}{first} | 144 | 0.1% |
| {first}_{last} | 119 | 0.1% |

**Total companies**: 100,173

## Email Verification Source Distribution

| Source | Count | % of Total |
|--------|-------|------------|
| NULL | 123,078 | 83.0% |
| mv_invalid | 12,838 | 8.7% |
| mv_verified | 5,854 | 4.0% |
| **pattern_generated** | **3,473** | **2.3%** |
| millionverifier:invalid | 1,469 | 1.0% |
| millionverifier:catch_all | 421 | 0.3% |
| millionverifier:ok | 371 | 0.3% |
| MillionVerifier | 354 | 0.2% |
| millionverifier:unknown | 198 | 0.1% |
| millionverifier:disposable | 1 | 0.0% |

**Note**: 83% of emails have NULL verification source, indicating they came from intake without verification.

## Recommendations

### Immediate Actions

1. **Re-run Phase 3 for NULL patterns**: 13,181 companies need email pattern discovery
   - This would enable generation for 848 additional people
   - Potential to improve coverage from 98.96% to 99.52%

2. **Fix invalid names in intake**: 711 people have names that cannot generate valid emails
   - Add validation rules to intake pipeline
   - Flag names with only Unicode/punctuation
   - Consider using full_name field to extract valid components

### Future Enhancements

1. **Add more pattern support**: 20+ additional patterns detected but not yet supported
   - `{last}{first}`: 144 companies (3 people affected)
   - `{last}.{first}`: 47 companies
   - `{l}{first}`: 28 companies
   - `{f}_{last}`: 24 companies

2. **Verify pattern-generated emails**: 3,473 new emails should be verified
   - Send to MillionVerifier or similar service
   - Expected verification rate: ~70-80% valid

3. **Monitor email quality**: Track bounce rates for pattern-generated emails
   - If high bounce rate, investigate specific patterns or companies
   - Consider implementing email verification before use

## Files Generated

- `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\generate_missing_emails.py` - Initial version (135 emails)
- `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\generate_missing_emails_v2.py` - Handles @domain suffix (3,334 emails)
- `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\generate_missing_emails_v3.py` - Adds {last}{first} pattern (0 additional)
- `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\investigate_missing_patterns.py` - Pattern analysis
- `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\investigate_final_failures.py` - Failure analysis

## Conclusion

The email generation pipeline successfully generated 3,473 emails, reducing missing emails by 69.0% and improving coverage to 98.96%. The remaining 1,559 missing emails are primarily due to:
1. Companies without discovered email patterns (54.4%)
2. Invalid/non-Latin names in the source data (45.6%)

Both issues can be addressed through targeted fixes to Phase 3 (Email Pattern Discovery) and intake data validation.

---

**Generated**: 2026-02-05
**Database**: Neon PostgreSQL (Marketing DB)
**Schema**: outreach.company_target, people.people_master, people.company_slot
**Execution**: LIVE (committed to production)
