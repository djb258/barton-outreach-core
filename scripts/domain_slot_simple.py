"""Quick domain slot analysis - simplified version"""
import psycopg2
import os

HOST = 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'
DATABASE = 'Marketing DB'
USER = 'Marketing DB_owner'
PASSWORD = os.getenv('NEON_PASSWORD', 'npg_OsE4Z2oPCpiT')

conn = psycopg2.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD, sslmode='require')
cur = conn.cursor()

print("Query 1: Hunter contacts matchable via domain")
cur.execute("""
    SELECT COUNT(DISTINCT hc.domain)
    FROM enrichment.hunter_contact hc
    JOIN outreach.outreach o ON LOWER(hc.domain) = LOWER(o.domain);
""")
print(f"Result: {cur.fetchone()[0]:,}\n")

print("Query 2: CEO slot fill potential")
cur.execute("""
    SELECT COUNT(*)
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE cs.slot_type = 'CEO'
      AND cs.is_filled = FALSE
      AND cs.person_unique_id IS NULL
      AND (hc.job_title ILIKE '%chief executive%'
           OR hc.job_title ILIKE '%ceo%'
           OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'));
""")
print(f"Result: {cur.fetchone()[0]:,}\n")

print("Query 3: CFO slot fill potential")
cur.execute("""
    SELECT COUNT(*)
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE cs.slot_type = 'CFO'
      AND cs.is_filled = FALSE
      AND cs.person_unique_id IS NULL
      AND (hc.job_title ILIKE '%chief financial%'
           OR hc.job_title ILIKE '%cfo%');
""")
print(f"Result: {cur.fetchone()[0]:,}\n")

print("Query 4: HR slot fill potential")
cur.execute("""
    SELECT COUNT(*)
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE cs.slot_type = 'HR'
      AND cs.is_filled = FALSE
      AND cs.person_unique_id IS NULL
      AND (hc.job_title ILIKE '%human resources%'
           OR hc.job_title ILIKE '%hr director%');
""")
print(f"Result: {cur.fetchone()[0]:,}\n")

print("Query 5: Sample CEO fills")
cur.execute("""
    SELECT o.domain, hc.email, hc.first_name, hc.last_name, hc.job_title
    FROM people.company_slot cs
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE cs.slot_type = 'CEO'
      AND cs.is_filled = FALSE
      AND (hc.job_title ILIKE '%ceo%' OR hc.job_title ILIKE '%chief executive%')
    LIMIT 5;
""")
for row in cur.fetchall():
    print(f"  {row[0]} | {row[2]} {row[3]} | {row[4]} | {row[1]}")

print("\nQuery 6: Check outreach.company_target schema")
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'outreach' AND table_name = 'company_target'
    AND column_name = 'domain';
""")
has_domain = cur.fetchone()
print(f"domain column exists in company_target: {bool(has_domain)}")

cur.close()
conn.close()
