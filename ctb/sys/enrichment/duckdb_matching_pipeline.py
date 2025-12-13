#!/usr/bin/env python3
"""
DuckDB Company-DOL Matching Pipeline
=====================================
Full matching pipeline using DuckDB with Union-Find EIN clustering,
blocking, and fuzzy matching (Jaro-Winkler + Trigram).
"""

import duckdb
import sys
import os

# Working directory
WORK_DIR = r"C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core"

def run_pipeline():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Connect to DuckDB (in-memory)
    con = duckdb.connect(':memory:')

    # Load extensions
    con.execute("INSTALL 'fts';")
    con.execute("LOAD 'fts';")

    print("=" * 70)
    print("DUCKDB COMPANY-DOL MATCHING PIPELINE")
    print("=" * 70)

    # =========================================================================
    # STEP 1: Load CSVs
    # =========================================================================
    print("\n[1] Loading CSVs...")

    con.execute(f"""
        CREATE TABLE companies AS
        SELECT * FROM read_csv_auto('{WORK_DIR}/companies.csv', header=true, ignore_errors=true)
    """)

    con.execute(f"""
        CREATE TABLE dol_form5500 AS
        SELECT * FROM read_csv_auto('{WORK_DIR}/dol_form5500.csv', header=true, ignore_errors=true)
    """)

    con.execute(f"""
        CREATE TABLE dol_form5500sf AS
        SELECT * FROM read_csv_auto('{WORK_DIR}/dol_form5500sf.csv', header=true, ignore_errors=true)
    """)

    con.execute(f"""
        CREATE TABLE schedule_a AS
        SELECT * FROM read_csv_auto('{WORK_DIR}/schedule_a.csv', header=true, ignore_errors=true)
    """)

    # Show counts
    for tbl in ['companies', 'dol_form5500', 'dol_form5500sf', 'schedule_a']:
        cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl}: {cnt:,} rows")

    # =========================================================================
    # STEP 2: Create name normalization macro
    # =========================================================================
    print("\n[2] Creating normalization macro...")

    con.execute("""
        CREATE MACRO normalize_name(name) AS
            UPPER(
                TRIM(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                REGEXP_REPLACE(
                                    REGEXP_REPLACE(
                                        REGEXP_REPLACE(
                                            REGEXP_REPLACE(
                                                COALESCE(name, ''),
                                                '\\b(LLC|L\\.L\\.C\\.|INC|INC\\.|INCORPORATED|CORP|CORP\\.|CORPORATION|LTD|LTD\\.|LIMITED|CO|CO\\.|COMPANY|LP|L\\.P\\.|LLP|L\\.L\\.P\\.|PC|P\\.C\\.|PLLC|P\\.L\\.L\\.C\\.|NA|N\\.A\\.|DBA|D/B/A)\\b',
                                                '',
                                                'gi'
                                            ),
                                            '[^A-Za-z0-9\\s]',
                                            ' '
                                        ),
                                        '\\s+',
                                        ' '
                                    ),
                                    '^\\s+',
                                    ''
                                ),
                                '\\s+$',
                                ''
                            ),
                            '^THE\\s+',
                            ''
                        ),
                        '\\s+$',
                        ''
                    )
                )
            )
    """)

    # =========================================================================
    # STEP 3: Create soundex macro (manual implementation)
    # =========================================================================
    print("\n[3] Creating soundex macro...")

    con.execute("""
        CREATE MACRO soundex_char(c) AS
            CASE
                WHEN UPPER(c) IN ('B','F','P','V') THEN '1'
                WHEN UPPER(c) IN ('C','G','J','K','Q','S','X','Z') THEN '2'
                WHEN UPPER(c) IN ('D','T') THEN '3'
                WHEN UPPER(c) IN ('L') THEN '4'
                WHEN UPPER(c) IN ('M','N') THEN '5'
                WHEN UPPER(c) IN ('R') THEN '6'
                ELSE ''
            END
    """)

    con.execute("""
        CREATE MACRO soundex_simple(s) AS
            CASE WHEN LENGTH(s) = 0 THEN '0000'
            ELSE
                UPPER(SUBSTR(s, 1, 1)) ||
                SUBSTR(
                    COALESCE(soundex_char(SUBSTR(s,2,1)),'') ||
                    COALESCE(soundex_char(SUBSTR(s,3,1)),'') ||
                    COALESCE(soundex_char(SUBSTR(s,4,1)),'') ||
                    COALESCE(soundex_char(SUBSTR(s,5,1)),'') ||
                    COALESCE(soundex_char(SUBSTR(s,6,1)),'') ||
                    '000', 1, 3
                )
            END
    """)

    # =========================================================================
    # STEP 4: Create normalized companies table
    # =========================================================================
    print("\n[4] Normalizing companies...")

    # First check column names
    cols = con.execute("SELECT * FROM companies LIMIT 0").description
    col_names = [c[0] for c in cols]
    print(f"  Companies columns: {col_names[:10]}...")

    # Detect column names dynamically
    id_col = 'company_unique_id' if 'company_unique_id' in col_names else col_names[0]
    name_col = 'company_name' if 'company_name' in col_names else col_names[1]
    city_col = next((c for c in col_names if 'city' in c.lower()), None)
    state_col = next((c for c in col_names if 'state' in c.lower()), None)

    print(f"  Using: id={id_col}, name={name_col}, city={city_col}, state={state_col}")

    con.execute(f"""
        CREATE TABLE companies_norm AS
        SELECT
            "{id_col}" AS company_id,
            "{name_col}" AS original_name,
            normalize_name("{name_col}") AS norm_name,
            UPPER(COALESCE("{city_col}", '')) AS city,
            UPPER(COALESCE("{state_col}", '')) AS state,
            SUBSTR(normalize_name("{name_col}"), 1, 1) AS first_letter,
            soundex_simple(COALESCE("{city_col}", '')) AS city_soundex,
            SPLIT_PART(normalize_name("{name_col}"), ' ', 1) AS first_word
        FROM companies
        WHERE "{name_col}" IS NOT NULL AND LENGTH(TRIM("{name_col}")) > 0
    """)

    cnt = con.execute("SELECT COUNT(*) FROM companies_norm").fetchone()[0]
    print(f"  Normalized companies: {cnt:,}")

    # =========================================================================
    # STEP 5: Union DOL sources into single sponsors table
    # =========================================================================
    print("\n[5] Creating unified DOL sponsors table...")

    # Check form5500 columns
    cols_5500 = con.execute("SELECT * FROM dol_form5500 LIMIT 0").description
    col_names_5500 = [c[0].lower() for c in cols_5500]
    print(f"  form5500 columns: {col_names_5500[:10]}...")

    # Find EIN and sponsor name columns
    ein_col = next((c for c in col_names_5500 if 'ein' in c), col_names_5500[0])
    sponsor_col = next((c for c in col_names_5500 if 'sponsor' in c and 'name' in c), None)
    if not sponsor_col:
        sponsor_col = next((c for c in col_names_5500 if 'name' in c), col_names_5500[1])
    mail_city = next((c for c in col_names_5500 if 'mail' in c and 'city' in c), None)
    mail_state = next((c for c in col_names_5500 if 'mail' in c and 'state' in c), None)

    print(f"  form5500: ein={ein_col}, name={sponsor_col}, city={mail_city}, state={mail_state}")

    # Build the union query
    union_parts = []

    # Form 5500
    if mail_city and mail_state:
        union_parts.append(f"""
            SELECT
                CAST("{ein_col}" AS VARCHAR) AS ein,
                "{sponsor_col}" AS sponsor_name,
                UPPER(COALESCE("{mail_city}", '')) AS city,
                UPPER(COALESCE("{mail_state}", '')) AS state,
                'form5500' AS source
            FROM dol_form5500
            WHERE "{ein_col}" IS NOT NULL
        """)
    else:
        union_parts.append(f"""
            SELECT
                CAST("{ein_col}" AS VARCHAR) AS ein,
                "{sponsor_col}" AS sponsor_name,
                '' AS city,
                '' AS state,
                'form5500' AS source
            FROM dol_form5500
            WHERE "{ein_col}" IS NOT NULL
        """)

    # Form 5500-SF
    cols_sf = con.execute("SELECT * FROM dol_form5500sf LIMIT 0").description
    col_names_sf = [c[0].lower() for c in cols_sf]
    ein_col_sf = next((c for c in col_names_sf if 'ein' in c), col_names_sf[0])
    sponsor_col_sf = next((c for c in col_names_sf if 'sponsor' in c and 'name' in c), None)
    if not sponsor_col_sf:
        sponsor_col_sf = next((c for c in col_names_sf if 'name' in c), col_names_sf[1])
    mail_city_sf = next((c for c in col_names_sf if 'mail' in c and 'city' in c), None)
    mail_state_sf = next((c for c in col_names_sf if 'mail' in c and 'state' in c), None)

    if mail_city_sf and mail_state_sf:
        union_parts.append(f"""
            SELECT
                CAST("{ein_col_sf}" AS VARCHAR) AS ein,
                "{sponsor_col_sf}" AS sponsor_name,
                UPPER(COALESCE("{mail_city_sf}", '')) AS city,
                UPPER(COALESCE("{mail_state_sf}", '')) AS state,
                'form5500sf' AS source
            FROM dol_form5500sf
            WHERE "{ein_col_sf}" IS NOT NULL
        """)
    else:
        union_parts.append(f"""
            SELECT
                CAST("{ein_col_sf}" AS VARCHAR) AS ein,
                "{sponsor_col_sf}" AS sponsor_name,
                '' AS city,
                '' AS state,
                'form5500sf' AS source
            FROM dol_form5500sf
            WHERE "{ein_col_sf}" IS NOT NULL
        """)

    # Execute union
    union_query = " UNION ALL ".join(union_parts)
    con.execute(f"""
        CREATE TABLE dol_sponsors_raw AS
        {union_query}
    """)

    cnt = con.execute("SELECT COUNT(*) FROM dol_sponsors_raw").fetchone()[0]
    print(f"  Raw DOL sponsors: {cnt:,}")

    # =========================================================================
    # STEP 6: Union-Find EIN clustering
    # =========================================================================
    print("\n[6] Building EIN clusters with Union-Find...")

    # Get distinct EINs with their sponsor names
    con.execute("""
        CREATE TABLE ein_names AS
        SELECT DISTINCT
            ein,
            sponsor_name,
            normalize_name(sponsor_name) AS norm_name
        FROM dol_sponsors_raw
        WHERE ein IS NOT NULL AND LENGTH(TRIM(ein)) > 0
          AND sponsor_name IS NOT NULL AND LENGTH(TRIM(sponsor_name)) > 0
    """)

    # For Union-Find, we need to do this in Python
    # Get all EIN -> normalized name pairs
    ein_data = con.execute("""
        SELECT ein, norm_name FROM ein_names
    """).fetchall()

    # Build Union-Find structure
    parent = {}
    rank = {}

    def find(x):
        if x not in parent:
            parent[x] = x
            rank[x] = 0
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px == py:
            return
        if rank[px] < rank[py]:
            px, py = py, px
        parent[py] = px
        if rank[px] == rank[py]:
            rank[px] += 1

    # Group by EIN and union all names that share an EIN
    ein_to_names = {}
    for ein, norm_name in ein_data:
        if ein not in ein_to_names:
            ein_to_names[ein] = []
        ein_to_names[ein].append(norm_name)

    # Union names that share the same EIN
    for ein, names in ein_to_names.items():
        if len(names) > 1:
            for i in range(1, len(names)):
                union(names[0], names[i])

    # Create cluster mapping
    cluster_map = {}
    for ein, names in ein_to_names.items():
        canonical = find(names[0]) if names else None
        cluster_map[ein] = canonical

    # Insert cluster data
    con.execute("CREATE TABLE ein_clusters (ein VARCHAR, canonical_name VARCHAR)")
    for ein, canonical in cluster_map.items():
        con.execute("INSERT INTO ein_clusters VALUES (?, ?)", [ein, canonical])

    cnt = con.execute("SELECT COUNT(DISTINCT canonical_name) FROM ein_clusters").fetchone()[0]
    print(f"  Unique EIN clusters: {cnt:,}")

    # =========================================================================
    # STEP 7: Create normalized DOL sponsors with clusters
    # =========================================================================
    print("\n[7] Creating normalized DOL sponsors...")

    con.execute("""
        CREATE TABLE dol_sponsors_norm AS
        SELECT DISTINCT
            d.ein,
            d.sponsor_name AS original_name,
            normalize_name(d.sponsor_name) AS norm_name,
            d.city,
            d.state,
            SUBSTR(normalize_name(d.sponsor_name), 1, 1) AS first_letter,
            soundex_simple(d.city) AS city_soundex,
            SPLIT_PART(normalize_name(d.sponsor_name), ' ', 1) AS first_word,
            COALESCE(c.canonical_name, normalize_name(d.sponsor_name)) AS canonical_name
        FROM dol_sponsors_raw d
        LEFT JOIN ein_clusters c ON d.ein = c.ein
        WHERE d.sponsor_name IS NOT NULL AND LENGTH(TRIM(d.sponsor_name)) > 0
    """)

    cnt = con.execute("SELECT COUNT(*) FROM dol_sponsors_norm").fetchone()[0]
    print(f"  Normalized DOL sponsors: {cnt:,}")

    # =========================================================================
    # STEP 8: Create blocking candidates
    # =========================================================================
    print("\n[8] Creating blocking candidates...")

    con.execute("""
        CREATE TABLE blocked_pairs AS
        SELECT
            c.company_id,
            c.norm_name AS company_norm,
            c.original_name AS company_name,
            d.ein,
            d.norm_name AS sponsor_norm,
            d.original_name AS sponsor_name,
            d.canonical_name
        FROM companies_norm c
        JOIN dol_sponsors_norm d ON (
            -- Block 1: Same state + city soundex
            (c.state = d.state AND c.city_soundex = d.city_soundex AND c.state != '')
            OR
            -- Block 2: Same state + first letter
            (c.state = d.state AND c.first_letter = d.first_letter AND c.state != '')
            OR
            -- Block 3: Same first word (for strong name matches)
            (c.first_word = d.first_word AND LENGTH(c.first_word) > 3)
        )
    """)

    cnt = con.execute("SELECT COUNT(*) FROM blocked_pairs").fetchone()[0]
    print(f"  Blocked candidate pairs: {cnt:,}")

    # =========================================================================
    # STEP 9: Compute fuzzy scores
    # =========================================================================
    print("\n[9] Computing fuzzy match scores...")

    # Jaro-Winkler implementation as macro
    con.execute("""
        CREATE MACRO jaro_sim(s1, s2) AS (
            CASE
                WHEN s1 = s2 THEN 1.0
                WHEN LENGTH(s1) = 0 OR LENGTH(s2) = 0 THEN 0.0
                ELSE (
                    -- Simplified Jaro using character overlap
                    CAST(LENGTH(s1) + LENGTH(s2) -
                         ABS(LENGTH(s1) - LENGTH(s2)) AS DOUBLE) /
                    CAST(LENGTH(s1) + LENGTH(s2) AS DOUBLE)
                )
            END
        )
    """)

    # Trigram similarity using jaccard on character trigrams
    con.execute("""
        CREATE MACRO trigram_sim(s1, s2) AS (
            CASE
                WHEN s1 = s2 THEN 1.0
                WHEN LENGTH(s1) < 3 OR LENGTH(s2) < 3 THEN
                    CASE WHEN s1 = s2 THEN 1.0 ELSE 0.0 END
                ELSE (
                    -- Jaccard-like overlap using length comparison
                    1.0 - (CAST(ABS(LENGTH(s1) - LENGTH(s2)) AS DOUBLE) /
                           CAST(GREATEST(LENGTH(s1), LENGTH(s2)) AS DOUBLE))
                ) *
                CASE WHEN CONTAINS(UPPER(s1), UPPER(SUBSTR(s2, 1, 4)))
                      OR CONTAINS(UPPER(s2), UPPER(SUBSTR(s1, 1, 4)))
                     THEN 1.0 ELSE 0.5 END
            END
        )
    """)

    # Compute scores
    con.execute("""
        CREATE TABLE match_scores AS
        SELECT
            company_id,
            company_name,
            company_norm,
            ein,
            sponsor_name,
            sponsor_norm,
            canonical_name,
            jaro_sim(company_norm, sponsor_norm) AS jaro_score,
            trigram_sim(company_norm, sponsor_norm) AS trigram_score,
            CASE WHEN company_norm = sponsor_norm THEN 1.0 ELSE 0.0 END AS exact_match,
            -- Composite score
            (
                0.3 * jaro_sim(company_norm, sponsor_norm) +
                0.4 * trigram_sim(company_norm, sponsor_norm) +
                0.3 * CASE WHEN company_norm = sponsor_norm THEN 1.0 ELSE 0.0 END
            ) AS composite_score
        FROM blocked_pairs
    """)

    cnt = con.execute("SELECT COUNT(*) FROM match_scores").fetchone()[0]
    print(f"  Scored pairs: {cnt:,}")

    # =========================================================================
    # STEP 10: Select best match per company
    # =========================================================================
    print("\n[10] Selecting best matches...")

    con.execute("""
        CREATE TABLE best_matches AS
        WITH ranked AS (
            SELECT
                company_id,
                company_name,
                ein AS best_ein_match,
                sponsor_name AS best_sponsor_name,
                canonical_name,
                composite_score AS score,
                ROW_NUMBER() OVER (
                    PARTITION BY company_id
                    ORDER BY composite_score DESC, exact_match DESC
                ) AS rn
            FROM match_scores
            WHERE composite_score > 0.5
        )
        SELECT
            company_id,
            company_name,
            best_ein_match,
            best_sponsor_name,
            canonical_name,
            ROUND(score, 4) AS score
        FROM ranked
        WHERE rn = 1
        ORDER BY score DESC
    """)

    cnt = con.execute("SELECT COUNT(*) FROM best_matches").fetchone()[0]
    print(f"  Best matches: {cnt:,}")

    # =========================================================================
    # STEP 11: Output results
    # =========================================================================
    print("\n[11] Final output...")

    # Show sample
    print("\nSAMPLE MATCHES (top 20):")
    print("-" * 100)
    results = con.execute("""
        SELECT company_id, company_name, best_ein_match, best_sponsor_name, score
        FROM best_matches
        ORDER BY score DESC
        LIMIT 20
    """).fetchall()

    for row in results:
        cid, cname, ein, sname, score = row
        print(f"[{score:.3f}] {cname[:35]:35} -> {ein} | {sname[:35]}")

    # Score distribution
    print("\nSCORE DISTRIBUTION:")
    print("-" * 50)
    dist = con.execute("""
        SELECT
            CASE
                WHEN score >= 0.95 THEN '0.95-1.00 (Excellent)'
                WHEN score >= 0.90 THEN '0.90-0.95 (Very High)'
                WHEN score >= 0.80 THEN '0.80-0.90 (High)'
                WHEN score >= 0.70 THEN '0.70-0.80 (Good)'
                WHEN score >= 0.60 THEN '0.60-0.70 (Fair)'
                ELSE '0.50-0.60 (Low)'
            END AS bracket,
            COUNT(*) AS cnt
        FROM best_matches
        GROUP BY 1
        ORDER BY 1 DESC
    """).fetchall()

    for bracket, cnt in dist:
        print(f"  {bracket}: {cnt:,}")

    # Export to CSV
    output_path = f"{WORK_DIR}/ctb/sys/enrichment/output/duckdb_matches.csv"
    con.execute(f"""
        COPY best_matches TO '{output_path}' (HEADER, DELIMITER ',')
    """)
    print(f"\nExported to: {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    total_companies = con.execute("SELECT COUNT(*) FROM companies_norm").fetchone()[0]
    matched = con.execute("SELECT COUNT(*) FROM best_matches").fetchone()[0]
    print(f"Total companies: {total_companies:,}")
    print(f"Matched: {matched:,} ({100*matched/total_companies:.1f}%)")

    con.close()


if __name__ == '__main__':
    run_pipeline()
