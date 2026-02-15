"""Full CT (outreach.company_target) column fill audit."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Get all columns
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'outreach' AND table_name = 'company_target'
    ORDER BY ordinal_position
""")
columns = cur.fetchall()

print(f"{'='*80}")
print(f"  CT (outreach.company_target) — Full Column Fill Audit")
print(f"{'='*80}")

# Get total
cur.execute("SELECT COUNT(*) FROM outreach.company_target")
total = cur.fetchone()[0]
print(f"\n  Total CT records: {total:,}\n")

print(f"  {'Column':<35s} {'Type':<20s} {'Filled':>8s} {'%':>7s}  {'Empty':>8s}")
print(f"  {'-'*35} {'-'*20} {'-'*8} {'-'*7}  {'-'*8}")

for col_name, data_type, nullable in columns:
    # Count non-null, non-empty values
    cur.execute(f"""
        SELECT
            COUNT(CASE WHEN "{col_name}" IS NOT NULL
                        AND TRIM("{col_name}"::text) != '' THEN 1 END) AS filled,
            COUNT(CASE WHEN "{col_name}" IS NULL
                        OR TRIM("{col_name}"::text) = '' THEN 1 END) AS empty
        FROM outreach.company_target
    """)
    filled, empty = cur.fetchone()
    pct = 100 * filled / total if total > 0 else 0

    # Color coding via markers
    if pct >= 90:
        marker = "  "
    elif pct >= 50:
        marker = "~ "
    elif pct > 0:
        marker = "! "
    else:
        marker = "X "

    dtype_short = data_type[:18]
    print(f"{marker}{col_name:<35s} {dtype_short:<20s} {filled:>8,} {pct:>6.1f}%  {empty:>8,}")

# Summary by fill tier
print(f"\n  {'='*80}")
print(f"  Fill Tier Summary:")
print(f"  {'='*80}")

tiers = {"90-100% (good)": [], "50-89% (partial)": [], "1-49% (low)": [], "0% (empty)": []}

for col_name, data_type, nullable in columns:
    cur.execute(f"""
        SELECT COUNT(CASE WHEN "{col_name}" IS NOT NULL
                          AND TRIM("{col_name}"::text) != '' THEN 1 END)
        FROM outreach.company_target
    """)
    filled = cur.fetchone()[0]
    pct = 100 * filled / total if total > 0 else 0

    if pct >= 90:
        tiers["90-100% (good)"].append((col_name, pct))
    elif pct >= 50:
        tiers["50-89% (partial)"].append((col_name, pct))
    elif pct > 0:
        tiers["1-49% (low)"].append((col_name, pct))
    else:
        tiers["0% (empty)"].append((col_name, pct))

for tier_name, cols in tiers.items():
    print(f"\n  {tier_name}: {len(cols)} columns")
    for c, p in sorted(cols, key=lambda x: -x[1]):
        print(f"    {c:<35s} {p:.1f}%")

conn.close()
print(f"\n{'='*80}")
print(f"  Done.")
print(f"{'='*80}")
