import os, psycopg2

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    dbname=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

# === FULL DATABASE CT SUB-HUB ===
print("=== FULL DATABASE — CT SUB-HUB ===")
print()

cur.execute("SELECT COUNT(*) FROM outreach.company_target")
ct_total = cur.fetchone()[0]
print(f"Total Companies: {ct_total:,}")

# Employee data coverage
cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE employees IS NOT NULL")
has_emp = cur.fetchone()[0]
print(f"Has Employee Data: {has_emp:,} ({100.0*has_emp/ct_total:.1f}%)")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE employees >= 50")
emp_50plus = cur.fetchone()[0]
print(f"50+ Employees: {emp_50plus:,} ({100.0*emp_50plus/ct_total:.1f}%)")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE employees IS NOT NULL AND employees < 50")
emp_below = cur.fetchone()[0]
print(f"Below 50 (filtered out): {emp_below:,}")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE employees IS NULL")
emp_null = cur.fetchone()[0]
print(f"No Employee Data: {emp_null:,} ({100.0*emp_null/ct_total:.1f}%)")
print()

# 50+ bands
cur.execute("""
    SELECT
        CASE
            WHEN employees BETWEEN 50 AND 100 THEN '50-100'
            WHEN employees BETWEEN 101 AND 250 THEN '101-250'
            WHEN employees BETWEEN 251 AND 500 THEN '251-500'
            WHEN employees BETWEEN 501 AND 1000 THEN '501-1,000'
            WHEN employees BETWEEN 1001 AND 5000 THEN '1,001-5,000'
            WHEN employees > 5000 THEN '5,001+'
        END as band,
        COUNT(*) as cnt
    FROM outreach.company_target
    WHERE employees >= 50
    GROUP BY 1
    ORDER BY MIN(employees)
""")
print("Employee Size Bands (50+):")
for row in cur.fetchall():
    print(f"  {row[0]:>12}: {row[1]:>8,} ({100.0*row[1]/emp_50plus:.1f}%)")
print()

# Domain health
print("Domain Health:")
try:
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN domain_alive = TRUE THEN 1 END) as alive,
            COUNT(CASE WHEN domain_alive = FALSE THEN 1 END) as dead,
            COUNT(CASE WHEN domain_alive IS NULL THEN 1 END) as unchecked
        FROM outreach.company_target
    """)
    r = cur.fetchone()
    checked = r[1] + r[2]
    if checked > 0:
        print(f"  Checked: {checked:,}")
        print(f"  Alive: {r[1]:,} ({100.0*r[1]/checked:.1f}% of checked)")
        print(f"  Dead: {r[2]:,} ({100.0*r[2]/checked:.1f}% of checked)")
        print(f"  Unchecked: {r[3]:,}")
    else:
        print("  No domain_alive data")
except Exception as e:
    print(f"  No domain_alive column: {e}")
    conn.rollback()

# Try alternate domain health location
try:
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN domain_reachable = TRUE THEN 1 END) as alive,
            COUNT(CASE WHEN domain_reachable = FALSE THEN 1 END) as dead
        FROM outreach.sitemap_discovery
    """)
    r = cur.fetchone()
    checked = r[1] + r[2]
    if checked > 0:
        print(f"\n  (From sitemap_discovery):")
        print(f"  Reachable: {r[1]:,} ({100.0*r[1]/r[0]:.1f}%)")
        print(f"  Unreachable: {r[2]:,} ({100.0*r[2]/r[0]:.1f}%)")
except Exception as e:
    conn.rollback()

# Check for email_method coverage (CT-level metric)
try:
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN email_method IS NOT NULL AND email_method != '' THEN 1 END) as has_method
        FROM outreach.company_target
    """)
    r = cur.fetchone()
    print(f"\n  Email Method: {r[1]:,} / {r[0]:,} ({100.0*r[1]/r[0]:.1f}%)")
except Exception as e:
    conn.rollback()

# State breakdown with employee 50+ and Emp% column
print()
print("Sovereign States — 50+ Employee %:")
cur.execute("""
    SELECT
        state,
        COUNT(*) as companies,
        COUNT(CASE WHEN employees >= 50 THEN 1 END) as emp_50plus,
        ROUND(100.0 * COUNT(CASE WHEN employees >= 50 THEN 1 END) / COUNT(*), 1) as emp_pct
    FROM outreach.company_target
    WHERE state NOT IN ('CA', 'NY')
    GROUP BY state
    ORDER BY COUNT(*) DESC
    LIMIT 8
""")
print(f"{'State':<6} {'Companies':>10} {'50+ Emp':>10} {'50+%':>7}")
print("-" * 35)
for row in cur.fetchall():
    print(f"{row[0]:<6} {row[1]:>10,} {row[2]:>10,} {row[3]:>6.1f}%")

print()
print("=" * 60)

# === ZIP 24015 / 100mi ===
print("=== ZIP 24015 (Roanoke, VA) 100mi — CT SUB-HUB ===")
print()

cur.execute("SELECT lat, lng FROM reference.us_zip_codes WHERE zip = '24015'")
anchor = cur.fetchone()
anchor_lat, anchor_lng = float(anchor[0]), float(anchor[1])

cur.execute("""
    SELECT zip FROM reference.us_zip_codes
    WHERE (
        3959 * acos(
            cos(radians(%s)) * cos(radians(lat)) * cos(radians(lng) - radians(%s))
            + sin(radians(%s)) * sin(radians(lat))
        )
    ) <= 100
""", (anchor_lat, anchor_lng, anchor_lat))
radius_zips = [row[0] for row in cur.fetchall()]

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE postal_code = ANY(%s)", (radius_zips,))
r_total = cur.fetchone()[0]
print(f"Total in Radius: {r_total:,}")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE postal_code = ANY(%s) AND employees IS NOT NULL", (radius_zips,))
r_has_emp = cur.fetchone()[0]
print(f"Has Employee Data: {r_has_emp:,} ({100.0*r_has_emp/r_total:.1f}%)")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE postal_code = ANY(%s) AND employees >= 50", (radius_zips,))
r_50plus = cur.fetchone()[0]
print(f"50+ Employees: {r_50plus:,} ({100.0*r_50plus/r_total:.1f}%)")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE postal_code = ANY(%s) AND employees IS NOT NULL AND employees < 50", (radius_zips,))
r_below = cur.fetchone()[0]
print(f"Below 50 (filtered out): {r_below:,}")

cur.execute("SELECT COUNT(*) FROM outreach.company_target WHERE postal_code = ANY(%s) AND employees IS NULL", (radius_zips,))
r_null = cur.fetchone()[0]
print(f"No Employee Data: {r_null:,} ({100.0*r_null/r_total:.1f}%)")
print()

# 50+ bands in radius
cur.execute("""
    SELECT
        CASE
            WHEN employees BETWEEN 50 AND 100 THEN '50-100'
            WHEN employees BETWEEN 101 AND 250 THEN '101-250'
            WHEN employees BETWEEN 251 AND 500 THEN '251-500'
            WHEN employees BETWEEN 501 AND 1000 THEN '501-1,000'
            WHEN employees BETWEEN 1001 AND 5000 THEN '1,001-5,000'
            WHEN employees > 5000 THEN '5,001+'
        END as band,
        COUNT(*) as cnt
    FROM outreach.company_target
    WHERE postal_code = ANY(%s) AND employees >= 50
    GROUP BY 1
    ORDER BY MIN(employees)
""", (radius_zips,))
print("Employee Size Bands (50+):")
for row in cur.fetchall():
    print(f"  {row[0]:>12}: {row[1]:>8,} ({100.0*row[1]/r_50plus:.1f}%)")
print()

# Domain health in radius
try:
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN sd.domain_reachable = TRUE THEN 1 END) as alive,
            COUNT(CASE WHEN sd.domain_reachable = FALSE THEN 1 END) as dead
        FROM outreach.company_target ct
        LEFT JOIN outreach.sitemap_discovery sd ON sd.outreach_id = ct.outreach_id
        WHERE ct.postal_code = ANY(%s)
    """, (radius_zips,))
    r = cur.fetchone()
    checked = r[1] + r[2]
    if checked > 0:
        print(f"Domain Health (from sitemap_discovery):")
        print(f"  Reachable: {r[1]:,} ({100.0*r[1]/checked:.1f}% of checked)")
        print(f"  Unreachable: {r[2]:,} ({100.0*r[2]/checked:.1f}% of checked)")
        print(f"  Unchecked: {r[0] - checked:,}")
except Exception as e:
    print(f"  Error: {e}")
    conn.rollback()

# Email method in radius
try:
    cur.execute("""
        SELECT
            COUNT(*),
            COUNT(CASE WHEN email_method IS NOT NULL AND email_method != '' THEN 1 END)
        FROM outreach.company_target
        WHERE postal_code = ANY(%s)
    """, (radius_zips,))
    r = cur.fetchone()
    print(f"\nEmail Method: {r[1]:,} / {r[0]:,} ({100.0*r[1]/r[0]:.1f}%)")
except Exception as e:
    conn.rollback()

print()

# State breakdown in radius
cur.execute("""
    SELECT
        state,
        COUNT(*) as companies,
        COUNT(CASE WHEN employees >= 50 THEN 1 END) as emp_50plus,
        ROUND(100.0 * COUNT(CASE WHEN employees >= 50 THEN 1 END) / COUNT(*), 1) as emp_pct
    FROM outreach.company_target
    WHERE postal_code = ANY(%s) AND state NOT IN ('CA', 'NY')
    GROUP BY state
    ORDER BY COUNT(*) DESC
""", (radius_zips,))
print("States in Radius — 50+ Employee %:")
print(f"{'State':<6} {'Companies':>10} {'50+ Emp':>10} {'50+%':>7}")
print("-" * 35)
for row in cur.fetchall():
    print(f"{row[0]:<6} {row[1]:>10,} {row[2]:>10,} {row[3]:>6.1f}%")

conn.close()
