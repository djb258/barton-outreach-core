import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
conn = psycopg2.connect(
    host=os.getenv('NEON_HOST'),
    database=os.getenv('NEON_DATABASE'),
    user=os.getenv('NEON_USER'),
    password=os.getenv('NEON_PASSWORD'),
    sslmode='require'
)

queries = [
    # Core alignment counts
    ("outreach.outreach", "SELECT 'outreach.outreach' as metric, COUNT(*) as value FROM outreach.outreach"),
    ("cl.company_identity with outreach_id", "SELECT 'cl.company_identity with outreach_id' as metric, COUNT(*) as value FROM cl.company_identity WHERE outreach_id IS NOT NULL"),
    ("outreach.outreach_excluded", "SELECT 'outreach.outreach_excluded' as metric, COUNT(*) as value FROM outreach.outreach_excluded"),

    # Sub-hub counts
    ("outreach.company_target", "SELECT 'outreach.company_target' as metric, COUNT(*) as value FROM outreach.company_target"),
    ("outreach.dol", "SELECT 'outreach.dol' as metric, COUNT(*) as value FROM outreach.dol"),
    ("outreach.blog", "SELECT 'outreach.blog' as metric, COUNT(*) as value FROM outreach.blog"),
    ("outreach.bit_scores", "SELECT 'outreach.bit_scores' as metric, COUNT(*) as value FROM outreach.bit_scores"),
    ("outreach.people", "SELECT 'outreach.people' as metric, COUNT(*) as value FROM outreach.people"),
    ("people.company_slot", "SELECT 'people.company_slot' as metric, COUNT(*) as value FROM people.company_slot"),
    ("people.people_master", "SELECT 'people.people_master' as metric, COUNT(*) as value FROM people.people_master"),

    # CL counts
    ("cl.company_identity total", "SELECT 'cl.company_identity total' as metric, COUNT(*) as value FROM cl.company_identity"),
    ("cl.company_identity PASS", "SELECT 'cl.company_identity PASS' as metric, COUNT(*) as value FROM cl.company_identity WHERE identity_status = 'PASS'"),
    ("cl.company_domains", "SELECT 'cl.company_domains' as metric, COUNT(*) as value FROM cl.company_domains"),

    # DOL counts
    ("dol.form_5500", "SELECT 'dol.form_5500' as metric, COUNT(*) as value FROM dol.form_5500"),
    ("dol.form_5500_sf", "SELECT 'dol.form_5500_sf' as metric, COUNT(*) as value FROM dol.form_5500_sf"),
    ("dol.ein_urls", "SELECT 'dol.ein_urls' as metric, COUNT(*) as value FROM dol.ein_urls"),

    # Company counts
    ("company.company_master", "SELECT 'company.company_master' as metric, COUNT(*) as value FROM company.company_master"),
    ("company.company_source_urls", "SELECT 'company.company_source_urls' as metric, COUNT(*) as value FROM company.company_source_urls"),
]

results = []

try:
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    for label, query in queries:
        try:
            cursor.execute(query)
            row = cursor.fetchone()
            results.append({
                'metric': row['metric'],
                'value': row['value']
            })
        except Exception as e:
            results.append({
                'metric': label,
                'value': f'ERROR: {str(e)}'
            })

    # Exclusion breakdown
    try:
        cursor.execute("""
            SELECT exclusion_reason, COUNT(*) as count
            FROM outreach.outreach_excluded
            GROUP BY exclusion_reason
            ORDER BY COUNT(*) DESC
        """)
        exclusion_breakdown = cursor.fetchall()
    except Exception as e:
        exclusion_breakdown = [{'exclusion_reason': 'ERROR', 'count': str(e)}]

    cursor.close()

except Exception as e:
    print(f"Connection error: {e}")
    exit(1)
finally:
    conn.close()

# Print results
print("\n" + "="*80)
print("BARTON OUTREACH CORE - DATABASE METRICS")
print("="*80)
print()

# Core alignment
print("CORE ALIGNMENT")
print("-" * 80)
for r in results[:3]:
    print(f"{r['metric']:<50} {str(r['value']):>20}")

# Sub-hub counts
print()
print("SUB-HUB COUNTS")
print("-" * 80)
for r in results[3:10]:
    print(f"{r['metric']:<50} {str(r['value']):>20}")

# CL counts
print()
print("CL (COMPANY LIFECYCLE) COUNTS")
print("-" * 80)
for r in results[10:13]:
    print(f"{r['metric']:<50} {str(r['value']):>20}")

# DOL counts
print()
print("DOL (DEPARTMENT OF LABOR) COUNTS")
print("-" * 80)
for r in results[13:16]:
    print(f"{r['metric']:<50} {str(r['value']):>20}")

# Company counts
print()
print("COMPANY SCHEMA COUNTS")
print("-" * 80)
for r in results[16:]:
    print(f"{r['metric']:<50} {str(r['value']):>20}")

# Exclusion breakdown
print()
print("EXCLUSION REASON BREAKDOWN")
print("-" * 80)
if exclusion_breakdown:
    for exc in exclusion_breakdown:
        print(f"{exc['exclusion_reason']:<50} {str(exc['count']):>20}")
else:
    print("No exclusions found")

print()
print("="*80)

# Verify alignment
try:
    outreach_count = [r for r in results if r['metric'] == 'outreach.outreach'][0]['value']
    cl_count = [r for r in results if r['metric'] == 'cl.company_identity with outreach_id'][0]['value']

    print()
    print("ALIGNMENT CHECK")
    print("-" * 80)
    if outreach_count == cl_count:
        print(f"✓ ALIGNED: {outreach_count} = {cl_count}")
    else:
        print(f"✗ MISALIGNED: outreach.outreach={outreach_count}, cl.company_identity (with outreach_id)={cl_count}")
    print()
except:
    pass
