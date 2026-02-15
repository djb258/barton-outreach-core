#!/usr/bin/env python3
"""Analyze Hunter data by Department, Job Title, Position Raw."""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("="*70)
print("HUNTER DATA ANALYSIS: DEPARTMENT → JOB TITLE → POSITION")
print("="*70)

print("\n=== CONTACTS BY DEPARTMENT ===")
cur.execute("""
    SELECT department, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    GROUP BY department 
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {str(r[0]):30} | {r[1]:,}")

print("\n=== EXECUTIVE DEPARTMENT - JOB TITLES ===")
cur.execute("""
    SELECT job_title, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE department = 'Executive'
    AND email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    GROUP BY job_title 
    ORDER BY COUNT(*) DESC
    LIMIT 40
""")
for r in cur.fetchall():
    print(f"  {str(r[0]):50} | {r[1]:,}")

print("\n=== FINANCE DEPARTMENT - JOB TITLES ===")
cur.execute("""
    SELECT job_title, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE department = 'Finance'
    AND email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    GROUP BY job_title 
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  {str(r[0]):50} | {r[1]:,}")

print("\n=== HR DEPARTMENT - JOB TITLES ===")
cur.execute("""
    SELECT job_title, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE department = 'HR'
    AND email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    GROUP BY job_title 
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  {str(r[0]):50} | {r[1]:,}")

# Check position_raw for more context
print("\n=== EXECUTIVE DEPT - POSITION_RAW SAMPLES ===")
cur.execute("""
    SELECT job_title, position_raw, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE department = 'Executive'
    AND position_raw IS NOT NULL AND position_raw != ''
    AND email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    GROUP BY job_title, position_raw
    ORDER BY COUNT(*) DESC
    LIMIT 30
""")
for r in cur.fetchall():
    print(f"  {str(r[0]):30} | {str(r[1]):40} | {r[2]:,}")

# Mapping suggestion
print("\n" + "="*70)
print("SLOT MAPPING SUGGESTION")
print("="*70)

print("\n--- CEO SLOT CANDIDATES ---")
print("Department = 'Executive' AND job_title IN:")
cur.execute("""
    SELECT job_title, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE department = 'Executive'
    AND email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    AND (
        LOWER(job_title) LIKE '%president%'
        OR LOWER(job_title) LIKE '%ceo%'
        OR LOWER(job_title) LIKE '%chief executive%'
        OR LOWER(job_title) = 'owner'
        OR LOWER(job_title) LIKE '%founder%'
        OR LOWER(job_title) LIKE '%managing director%'
        OR LOWER(job_title) LIKE '%general manager%'
        OR LOWER(job_title) = 'partner'
        OR LOWER(job_title) LIKE '%principal%'
    )
    GROUP BY job_title 
    ORDER BY COUNT(*) DESC
""")
total_ceo = 0
for r in cur.fetchall():
    print(f"  {str(r[0]):50} | {r[1]:,}")
    total_ceo += r[1]
print(f"  TOTAL CEO CANDIDATES: {total_ceo:,}")

print("\n--- CFO SLOT CANDIDATES ---")
print("Department = 'Finance' OR (Department = 'Executive' AND finance-related title):")
cur.execute("""
    SELECT job_title, department, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    AND (
        department = 'Finance'
        OR (department = 'Executive' AND (
            LOWER(job_title) LIKE '%cfo%'
            OR LOWER(job_title) LIKE '%chief financial%'
            OR LOWER(job_title) LIKE '%controller%'
            OR LOWER(job_title) LIKE '%treasurer%'
            OR LOWER(job_title) LIKE '%finance%'
        ))
    )
    GROUP BY job_title, department
    ORDER BY COUNT(*) DESC
    LIMIT 25
""")
total_cfo = 0
for r in cur.fetchall():
    print(f"  {str(r[0]):40} | dept={str(r[1]):15} | {r[2]:,}")
    total_cfo += r[2]
print(f"  TOTAL CFO CANDIDATES: {total_cfo:,}")

print("\n--- HR SLOT CANDIDATES ---")
print("Department = 'HR' OR HR-related title:")
cur.execute("""
    SELECT job_title, department, COUNT(*) 
    FROM enrichment.hunter_contact 
    WHERE email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
    AND (
        department = 'HR'
        OR LOWER(job_title) LIKE '%human resource%'
        OR LOWER(job_title) LIKE '%hr %'
        OR LOWER(job_title) LIKE '%talent%'
        OR LOWER(job_title) LIKE '%recruiting%'
        OR LOWER(job_title) LIKE '%people %'
    )
    GROUP BY job_title, department
    ORDER BY COUNT(*) DESC
    LIMIT 25
""")
total_hr = 0
for r in cur.fetchall():
    print(f"  {str(r[0]):40} | dept={str(r[1]):15} | {r[2]:,}")
    total_hr += r[2]
print(f"  TOTAL HR CANDIDATES: {total_hr:,}")

conn.close()
