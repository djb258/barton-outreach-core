"""Per-company sub-hub completeness for 26739 100mi market."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Build radius ZIPs + allowed states
cur.execute("""
    CREATE TEMP TABLE tmp_radius AS
    SELECT z.zip, z.state_id
    FROM reference.us_zip_codes z,
        (SELECT lat, lng FROM reference.us_zip_codes WHERE zip = '26739') a
    WHERE (3959 * acos(LEAST(1.0, GREATEST(-1.0,
        cos(radians(a.lat)) * cos(radians(z.lat)) *
        cos(radians(z.lng) - radians(a.lng)) +
        sin(radians(a.lat)) * sin(radians(z.lat))
    )))) <= 100
""")
cur.execute("SELECT DISTINCT state_id FROM tmp_radius")
allowed_states = [r[0] for r in cur.fetchall()]
cur.execute("SELECT COUNT(DISTINCT zip) FROM tmp_radius")
zip_count = cur.fetchone()[0]

# Per-company status
cur.execute("""
    SELECT
        ct.outreach_id,
        o.domain,
        ct.state,
        (d.outreach_id IS NOT NULL) AS has_dol,
        (b.outreach_id IS NOT NULL) AS has_blog,
        COALESCE(ceo.is_filled, FALSE) AS ceo_filled,
        COALESCE(cfo.is_filled, FALSE) AS cfo_filled,
        COALESCE(hr.is_filled, FALSE) AS hr_filled
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
    LEFT JOIN people.company_slot ceo ON ceo.outreach_id = ct.outreach_id AND ceo.slot_type = 'CEO'
    LEFT JOIN people.company_slot cfo ON cfo.outreach_id = ct.outreach_id AND cfo.slot_type = 'CFO'
    LEFT JOIN people.company_slot hr ON hr.outreach_id = ct.outreach_id AND hr.slot_type = 'HR'
    WHERE LEFT(TRIM(ct.postal_code), 5) IN (SELECT zip FROM tmp_radius)
      AND UPPER(TRIM(ct.state)) = ANY(%s)
""", (allowed_states,))
rows = cur.fetchall()

print(f"{'='*95}")
print(f"  Per-Company Sub-Hub Status — 26739 100mi ({len(rows):,} companies)")
print(f"{'='*95}")

# Sample
print(f"\n  {'outreach_id':36s} {'domain':28s} {'ST':3s} DOL BLG CEO CFO HR")
print(f"  {'-'*88}")
for r in rows[:20]:
    dol = "YES" if r[3] else " - "
    blg = "YES" if r[4] else " - "
    ceo = "YES" if r[5] else " - "
    cfo = "YES" if r[6] else " - "
    hr  = "YES" if r[7] else " - "
    print(f"  {str(r[0]):36s} {r[1]:28s} {r[2]:3s} {dol} {blg} {ceo} {cfo} {hr}")

# Completeness summary
total = len(rows)
all_complete = sum(1 for r in rows if r[3] and r[4] and r[5] and r[6] and r[7])
people_complete = sum(1 for r in rows if r[5] and r[6] and r[7])
needs_people = total - people_complete
no_dol = sum(1 for r in rows if not r[3])
no_blog = sum(1 for r in rows if not r[4])

# Breakdown by what's missing
no_ceo = sum(1 for r in rows if not r[5])
no_cfo = sum(1 for r in rows if not r[6])
no_hr  = sum(1 for r in rows if not r[7])
only_missing_dol = sum(1 for r in rows if not r[3] and r[5] and r[6] and r[7])

print(f"\n  {'='*65}")
print(f"  COMPLETENESS SUMMARY")
print(f"  {'='*65}")
print(f"    Total companies:             {total:,}")
print(f"    ALL sub-hubs complete:       {all_complete:,} ({100*all_complete/total:.0f}%)")
print(f"    People slots all filled:     {people_complete:,} ({100*people_complete/total:.0f}%)")
print(f"")
print(f"    Missing CEO:                 {no_ceo:,}")
print(f"    Missing CFO:                 {no_cfo:,}")
print(f"    Missing HR:                  {no_hr:,}")
print(f"    No DOL (expected):           {no_dol:,}")
print(f"    No Blog:                     {no_blog:,}")
print(f"")
print(f"    People-ready but no DOL:     {only_missing_dol:,}")
print(f"    Needs people work:           {needs_people:,}")

conn.close()
print(f"\n{'='*95}")
print(f"  Done.")
print(f"{'='*95}")
