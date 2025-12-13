# -*- coding: utf-8 -*-
"""
Update Database with ScraperAPI Enrichment Results
Pushes enriched companies back to raw intake for re-validation

Barton Doctrine ID: 04.04.02.04.enrichment.update_db
"""

import os
import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv('../../../.env')

import psycopg2
from psycopg2.extras import RealDictCursor

# The 106 successful enrichments from the ScraperAPI run
SUCCESSFUL_ENRICHMENTS = [
    ("167 Airlift Wing", "http://www.167aw.ang.af.mil/"),
    ("AARP Services, Inc.", "https://states.aarp.org/west-virginia/"),
    ("ANDERSON MEDICAL GROUP", "https://andersonmg.com/"),
    ("Affinity Salon", "https://www.affinity.salon/"),
    ("BECKLEY VAMC", "https://www.va.gov/beckley-health-care"),
    ("Banter by Piercing Pagoda", "https://www.banter.com/"),
    ("Bar Inc", "https://wvbar.org/"),
    ("Bee Queen", "https://www.newsandsentinel.com/news/community-news/2025/08/busy-bees-west-virginia-honey-festival-to-set-city-park-abuzz/"),
    ("Braxton County Schools", "https://boe.brax.k12.wv.us/"),
    ("Brooke County Board Education", "https://www.brooke.k12.wv.us/"),
    ("CALHOUN COUNTY SCHOOLS", "https://boe.calhoun.k12.wv.us/"),
    ("Camc Memorial Hospital", "https://www.camc.org/locations/camc-memorial-hospital"),
    ("Cecil I Walker Machinery Co.", "https://www.constructionequipment.com/earthmoving/company/10742494/cecil-i-walker-machinery-co"),
    ("Charleston Area Medical Center, Inc.", "https://www.camc.org/"),
    ("Charleston Police Department", "https://charlestonwvpolice.org/"),
    ("City of South Charleston, WV", "https://cityofsouthcharleston.com/"),
    ("Coach USA Transit Service", "https://www.coachusa.com/"),
    ("Contemporary Service", "https://www.prweb.com/releases/contemporary_services_corporation_contracts_with_west_virginia_university/prweb12227360.htm"),
    ("Cool Runnings", "https://www.coolrunnings.com/"),
    ("Departamento de Hacienda de Puerto Rico", "https://hacienda.pr.gov/"),
    ("Department Of Army", "https://www.wv.ng.mil/"),
    ("ELK ENERGY SERVICES, LLC", "https://elkenergyservices.com/"),
    ("Eagle Manufacturing Company", "https://eagle.justrite.com/"),
    ("FIRST CHOICE WV PLLC", "https://firstchoiceservices.org/"),
    ("Fat Pattys", "https://fatpattys.com/"),
    ("Fox Automotive", "http://www.foxautomotive.org/"),
    ("Fusion Technologies", "https://www.fusiontechnology-llc.com/"),
    ("GREENBRIER COUNTY SCHOOLS", "https://www.greenbriercountyschools.org/"),
    ("Gabriel Brothers, Inc.", "https://gabesstores.com/"),
    ("Grant County School District", "https://www.grantcountyschools.org/"),
    ("Graphics In Print", "https://www.graphicsinprint.com/"),
    ("HAMPSHIRE COUNTY SCHOOLS", "https://boe.hampshire.k12.wv.us/"),
    ("HARDY COUNTY SCHOOLS", "https://www.hardycountyschools.com/"),
    ("HARRISON COUNTY BOE", "https://www.harcoboe.net/"),
    ("HERBERT J THOMAS MEMORIAL HOSPITAL", "https://wvumedicine.org/thomas-hospitals/"),
    ("HUNTINGTON VA MEDICAL CENTER", "http://www.huntington.va.gov/"),
    ("Home Heath", "https://wvumedicine.org/princeton/services/home-health-services/"),
    ("House Keepers", "https://www.mountaintidywv.com/"),
    ("Jones Lang LaSalle Americas, Inc.", "https://www.jll.com/en-us/"),
    ("LOGAN COUNTY SCHOOLS", "https://boe.logan.k12.wv.us/"),
    ("LOUIS A. JOHNSON VA MEDICAL CENTER", "https://www.va.gov/clarksburg-health-care/locations/louis-a-johnson-veterans-administration-medical-center"),
    ("Local 33", "https://smwlu33.org/"),
    ("MILLWRIGHT LOCAL 1755", "https://ubcmillwrights.org/"),
    ("MINGO COUNTY SCHOOLS", "https://www.mingoschools.com/"),
    ("MONROE COUNTY SCHOOLS", "https://boe.monroe.k12.wv.us/"),
    ("Mardi Gras Casino", "https://www.mardigrascasinowv.com/"),
    ("Mc Donalds Central Service", "https://www.mcdonalds.com/us/en-us/location/wv/vienna/903-grand-central-ave/5282.html"),
    ("Merrick Engineering Inc", "http://www.merrickengineering.com/"),
    ("Mineral County School District", "https://www.boe.mine.k12.wv.us/"),
    ("Mon General Hospital", "https://www.monhealth.com/"),
    ("Monongalia County Schools", "https://www.boe.mono.k12.wv.us/"),
    ("Morgantown High School", "http://mohigans.mono.k12.wv.us/"),
    ("Mountaineer Casino Resort", "https://www.cnty.com/mountaineer/"),
    ("Municipal Corporation", "https://www.bluefieldva.org/agenda_detail_T22_R373.php"),
    ("NICHOLS CONSTRUCTION", "https://nicholscontracting.com/nichols-construction-services/"),
    ("NewForce by Generation West Virginia", "https://generationwv.org/our-work/newforce/"),
    ("Nicholas County Board Of Educ", "http://boe.nich.k12.wv.us/"),
    ("Ohio Valley Physicians", "https://ovphealth.com/"),
    ("PAR Mar", "https://www.parmarstores.com/"),
    ("PENDLETON COUNTY SCHOOLS", "https://www.pendletoncountyschools.com/"),
    ("PROMONTORY INTERFINANCIAL NETWORK, LLC", "https://www.intrafi.com/"),
    ("Pakistan Stock Exchange", "https://www.psx.com.pk/"),
    ("Potomac Edison Company", "https://www.firstenergycorp.com/potomac_edison.html"),
    ("Pre School", "https://www.berkeleycountyschools.org/page/pre-k"),
    ("RITCHIE COUNTY SCHOOLS", "https://www.ritchieschools.com/"),
    ("Raleigh County Schools", "https://boe.rale.k12.wv.us/"),
    ("Revelation Energy, LLC", "https://seamless.ai/b/revelation-energy-llc-20279236"),
    ("Reverse Mortgage Specialist", "https://www.huntington.com/Personal/mortgage-education-tools/find-a-mortgage-loan-officer/west-virginia/north-central-wv-mortgage-banking-office"),
    ("Ron Hughes Media", "https://x.com/ronhughes12"),
    ("SUPERMEDIA LLC", "https://www.sec.gov/Archives/edgar/vprr/1202/12026189.pdf"),
    ("Self-Employed Health and Wellness Consultant", "https://williamsonhealthwellness.com/"),
    ("Self-Employed/Contractor/Consultant", "https://www.ncpc.gov/files/projects/2021/8113_Marriner_S_Eccles_and_Federal_Reserve_Board-East_Building_Renovation_and_Expansion_Submission_Materials_Sep2021.pdf"),
    ("Shoney S", "https://www.shoneys.com/"),
    ("Smoke House BBQ", "https://smokinjsribs.com/"),
    ("Soaring Eagles", "https://wvtourism.com/things-to-do/outdoor-adventures/winter-sports/"),
    ("Standard Oil Company, Inc", "https://standardoil.biz/"),
    ("Summit Environmental Services", "https://summit-environmental.net/"),
    ("TEAM Environmental LLC", "http://teamenv.com/"),
    ("TMMWV TEAM MEMBERS ACTIVITIES ASSOCIATION INC", "https://projects.propublica.org/nonprofits/organizations/550784516/202401349349202420/full/"),
    ("Thrasher Engineering, Inc", "https://thethrashergroup.com/home/"),
    ("Total IT Solutions", "http://www.totalitsol.com/"),
    ("Touch Stone", "https://touchstonedatasystems.com/"),
    ("UPSHUR COUNTY SCHOOLS", "https://www.upshurschools.com/"),
    ("VV", "https://www.wvu.edu/"),
    ("WELDING, INC.", "http://business.cawv.org/list/member/engel-welding-inc-50040"),
    ("WEST VIRGINIA CHOICE", "https://www.choicecareathome.com/"),
    ("WHOLESALE TIRE, INC.", "https://business.michelinman.com/dealer-locator/clarksburg/wholesale-tire-inc-comm-tad-1267637036"),
    ("WILLIAM R SHARPE JR HOSPITAL", "https://medicine.hsc.wvu.edu/bmed/faculty-and-staff/public-sector-psychology-william-r-sharpe-jr-hospital/"),
    ("WV DEPARTMENT OF HIGHWAYS", "https://wvdot.attract.neogov.com/"),
    ("WV Division Of Rehabilitation", "https://wvdrs.org/"),
    ("WV SUPREME COURT", "https://www.wvsd.uscourts.gov/"),
    ("WV State Police", "https://www.wvsp.gov/"),
    ("WVUH-EAST", "https://wvumedicine.org/"),
    ("WYOMING COUNTY SCHOOLS", "https://boe.wyom.k12.wv.us/"),
    ("WesBanco Bank, Inc.", "https://www.wesbanco.com/"),
    ("West Virginia Army National Guard", "https://www.wv.ng.mil/"),
    ("West Virginia Birth To Three", "https://www.wvdhhr.org/birth23/"),
    ("West Virginia Department of Agriculture", "https://www.fns.usda.gov/fns-contact/west-virginia-department-agriculture-0"),
    ("West Virginia Department of Environmental Protecti", "https://www.wvdhhr.org/oehs/"),
    ("West Virginia Division Highway", "https://highways.dot.gov/field-offices/west-virginia"),
    ("West Virginia Junior College Bridgeport", "https://www.wvjc.edu/"),
    ("Westbrook Health Services", "https://www.westbrookhealth.org/"),
    ("Westwood Middle School", "https://wms.mono.k12.wv.us/"),
    ("Wheeling Island Hotel-Casino-Racetrack Jobs", "https://www.wheelingisland.com/"),
    ("kingdom of God", "https://wvcog.com/"),
    ("national navigation company", "https://nnc.com.eg/"),
]


def main():
    print(f"Loaded {len(SUCCESSFUL_ENRICHMENTS)} enriched companies")
    print()

    # Connect to database
    conn_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("STEP 1: Update website URLs in company_invalid")
    print("=" * 80)

    updated_count = 0
    for company_name, website in SUCCESSFUL_ENRICHMENTS:
        cursor.execute(
            """
            UPDATE marketing.company_invalid
            SET website = %s
            WHERE company_name = %s
        """,
            (website, company_name),
        )
        if cursor.rowcount > 0:
            updated_count += 1

    conn.commit()
    print(f"Updated {updated_count} companies with enriched websites")
    print()

    print("=" * 80)
    print("STEP 2: Copy enriched companies to intake.company_raw_intake")
    print("=" * 80)

    # First, check if intake.company_raw_intake table exists
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'intake'
            AND table_name = 'company_raw_intake'
        );
    """
    )
    table_exists = cursor.fetchone()["exists"]

    # Table already exists - use the correct column names
    # Insert the enriched companies into raw intake for re-validation
    inserted_count = 0
    for company_name, website in SUCCESSFUL_ENRICHMENTS:
        # Get additional details from company_invalid
        cursor.execute(
            """
            SELECT city, state, employee_count, industry
            FROM marketing.company_invalid
            WHERE company_name = %s
            LIMIT 1
        """,
            (company_name,),
        )
        row = cursor.fetchone()

        if row:
            # Use correct column names: company, company_city, company_state, num_employees
            cursor.execute(
                """
                INSERT INTO intake.company_raw_intake
                (company, website, company_city, company_state, num_employees, industry,
                 validated, validation_notes, enrichment_attempt, enriched_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    company_name,
                    website,
                    row.get("city"),
                    row.get("state"),
                    row.get("employee_count"),
                    row.get("industry"),
                    False,  # validated = False (needs re-validation)
                    "Enriched by ScraperAPI - needs re-validation",
                    1,  # enrichment_attempt = 1
                    "scraperapi",
                ),
            )
            inserted_count += 1

    conn.commit()
    print(f"Inserted {inserted_count} companies into intake.company_raw_intake")
    print()

    print("=" * 80)
    print("STEP 3: Mark enriched companies as reviewed in company_invalid")
    print("=" * 80)

    # Mark them as reviewed (but keep them in the invalid queue for now)
    company_names = tuple([c[0] for c in SUCCESSFUL_ENRICHMENTS])
    cursor.execute(
        """
        UPDATE marketing.company_invalid
        SET reviewed = TRUE
        WHERE company_name IN %s
    """,
        (company_names,),
    )

    conn.commit()
    print(f"Marked {cursor.rowcount} companies as reviewed")
    print()

    # Show remaining unreviewed count
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM marketing.company_invalid WHERE reviewed = FALSE"
    )
    remaining = cursor.fetchone()["cnt"]
    print(f"Remaining unreviewed companies: {remaining}")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("DATABASE UPDATE COMPLETE")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Updated websites:     {updated_count}")
    print(f"  - Pushed to raw intake: {inserted_count}")
    print(f"  - Remaining to review:  {remaining}")


if __name__ == "__main__":
    main()
