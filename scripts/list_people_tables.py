#!/usr/bin/env python3
"""List all people-related tables."""
import os
import psycopg2

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # List all tables in people schema
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'people'
        ORDER BY table_name
    """)
    print('Tables in people schema:')
    for row in cur.fetchall():
        print(f'  {row[1]}')
    
    # Count records in each
    cur.execute("SELECT COUNT(*) FROM people.people_master")
    print(f'\npeople.people_master: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM people.people_staging")
    print(f'people.people_staging: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM people.company_slot")
    print(f'people.company_slot: {cur.fetchone()[0]:,}')
    
    # Check if there's a people_intake or similar
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'people'
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f'\nAll people tables: {tables}')
    
    conn.close()

if __name__ == '__main__':
    main()
