#!/usr/bin/env python3
"""Create invalid tables and run validation"""

import os, sys, psycopg2
from dotenv import load_dotenv

load_dotenv()

print("Creating invalid tables...")
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
cursor = conn.cursor()

sql_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'sql', 'create_invalid_tables.sql'
)

with open(sql_file, 'r') as f:
    cursor.execute(f.read())

print("[OK] Invalid tables created\n")
cursor.close()
conn.close()

# Now run the validator
print("=" * 70)
sys.path.insert(0, os.path.dirname(__file__))
from validate_wv_simple import main
main()
