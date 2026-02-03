#!/usr/bin/env python3
"""Find outreach tables and count records."""
import os
import psycopg2

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Find outreach tables
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%outreach%'
        ORDER BY 1, 2
    """)
    print('Outreach tables:')
    tables = cur.fetchall()
    for row in tables:
        print(f'  {row[0]}.{row[1]}')
    
    # Check if there's an outreach schema
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'outreach'
        ORDER BY table_name
    """)
    outreach_tables = cur.fetchall()
    if outreach_tables:
        print('\nTables in outreach schema:')
        for row in outreach_tables:
            print(f'  {row[1]}')
            # Get count
            try:
                cur.execute(f'SELECT COUNT(*) FROM outreach.{row[1]}')
                print(f'    Count: {cur.fetchone()[0]:,}')
            except:
                pass
    
    # Check for outreach_id column in various tables
    cur.execute("""
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns 
        WHERE column_name = 'outreach_id'
        ORDER BY 1, 2
    """)
    print('\nTables with outreach_id column:')
    for row in cur.fetchall():
        print(f'  {row[0]}.{row[1]}')
    
    conn.close()

if __name__ == '__main__':
    main()
