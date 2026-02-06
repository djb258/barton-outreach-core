"""
Hunter.io Data Flow - Visual Summary
Quick reference for understanding Hunter data integration status
"""

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

print_section("HUNTER.IO DATA FLOW SUMMARY")

print("[DATA] HUNTER DATA SOURCES")
print("-" * 80)
print("+- enrichment.hunter_company")
print("|  |- Total: 88,405 records")
print("|  |- Email Patterns: 75,131 (85.0%)")
print("|  +- Linked to Outreach: 32,901 (37.2%)")
print("|")
print("+- enrichment.hunter_contact")
print("   |- Total: 583,433 records")
print("   |- Emails: 583,433 (100%)")
print("   |- Job Titles: 385,070 (66.0%)")
print("   +- Linked to Outreach: 248,071 (42.5%)")
print()

print_section("DATA SYNC STATUS")

print("[OK] WORKING: Hunter Company -> Company Target")
print("  * Pattern sync: COMPLETE")
print("  * Coverage: 81,412 / 94,237 companies have email_method (86.4%)")
print("  * Status: [OK] PRODUCTION READY")
print()

print("[X] BROKEN: Hunter Contact -> outreach.people")
print("  * Contact sync: MISSING")
print("  * Gap: 248,071 Hunter contacts NOT in outreach.people")
print("  * Current: Only 324 records in outreach.people")
print("  * Status: [X] CRITICAL - NEEDS IMMEDIATE FIX")
print()

print("[!] PARTIAL: Slot Assignment")
print("  * Total slots: 285,012")
print("  * Filled slots: 150,832 (52.9%)")
print("  * Companies with filled slots: 56,709 / 95,004 (59.7%)")
print("  * Status: [!] WORKING but missing Hunter contacts")
print()

print_section("CRITICAL GAP ANALYSIS")

print("[CRITICAL] GAP 1: Hunter Contacts NOT in outreach.people")
print("-" * 80)
print(f"   Size: 248,071 contact records")
print(f"   Impact: CRITICAL")
print(f"   Root Cause: No sync pipeline from hunter_contact -> outreach.people")
print(f"   Fix: Run sync_hunter_to_people.py (to be created)")
print()

print("[RESOLVED] GAP 2: Hunter Patterns in company_target")
print("-" * 80)
print(f"   Size: 0 missing records")
print(f"   Impact: NONE")
print(f"   Status: [OK] RESOLVED - All patterns synced")
print()

print_section("RECOMMENDED DATA FLOW")

print("STEP 1: ENRICHMENT (COMPLETE)")
print("  enrichment.hunter_company --> enrichment.hunter_contact")
print("  Status: [OK] Complete")
print()

print("STEP 2: PATTERN SYNC (COMPLETE)")
print("  enrichment.hunter_company.email_pattern --> outreach.company_target.email_method")
print("  Status: [OK] Complete")
print()

print("STEP 3: CONTACT SYNC (BROKEN)")
print("  enrichment.hunter_contact --> outreach.people")
print("  Status: [X] BROKEN - 248,071 records missing")
print("  Action: CREATE AND RUN sync script")
print()

print("STEP 4: SLOT ASSIGNMENT (PARTIAL)")
print("  outreach.people --> people.company_slot")
print("  Status: [!] Partial - needs Hunter contacts")
print("  Action: Re-run after Step 3 complete")
print()

print("STEP 5: OUTREACH EXECUTION (READY)")
print("  people.company_slot --> campaigns/sequences/send_log")
print("  Status: [WAITING] Awaiting Steps 3-4")
print()

print_section("IMMEDIATE ACTIONS REQUIRED")

print("Priority 1: CRITICAL")
print("  +- Sync 248,071 Hunter contacts to outreach.people")
print("     File: sync_hunter_to_people.py")
print("     Impact: +247,747 people records (75,100% increase)")
print()

print("Priority 2: HIGH")
print("  +- Run slot assignment on newly synced people")
print("     File: hubs/people-intelligence/.../slot_assignment_pipeline.py")
print("     Impact: +100K-150K filled slots (66%-100% increase)")
print()

print("Priority 3: MEDIUM")
print("  +- Sync Hunter company metadata (industry, headcount)")
print("     Target: outreach.company_target")
print("     Impact: Better targeting + BIT scoring")
print()

print_section("DATA QUALITY ASSESSMENT")

print("Hunter Company Data: **** EXCELLENT")
print("  * Pattern coverage: 85.0%")
print("  * Organization: 99.8%")
print("  * Industry: 81.5%")
print()

print("Hunter Contact Data: ***** OUTSTANDING")
print("  * Email coverage: 100%")
print("  * Name coverage: 70.9%")
print("  * Job title coverage: 66.0%")
print("  * Department coverage: 72.3%")
print()

print_section("EXPECTED IMPACT AFTER SYNC")

print("Before Sync:")
print("  * outreach.people: 324 records")
print("  * people.company_slot (filled): 150,832 slots")
print("  * Companies with filled slots: 56,709 (59.7%)")
print()

print("After Sync:")
print("  * outreach.people: ~248,395 records (+247,747)")
print("  * people.company_slot (filled): ~250,000-300,000 slots (+100K-150K)")
print("  * Companies with filled slots: ~75,000-85,000 (79%-89%)")
print()

print("Marketing Impact:")
print("  * Marketing-eligible companies: +20K-30K (35%-53% increase)")
print("  * Campaign capacity: +150K-200K contacts")
print("  * Outreach velocity: 2-3x increase")
print()

print("="*80)
print()

print("[NEXT STEPS]")
print("  1. Review HUNTER_DATA_FLOW_ANALYSIS.md for detailed mapping")
print("  2. Create sync_hunter_to_people.py script")
print("  3. Test sync on 100 records")
print("  4. Run full sync (248K records)")
print("  5. Re-run slot assignment pipeline")
print("  6. Verify marketing eligibility increase")
print()
print("="*80)
