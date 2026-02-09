"""Fix form_5500 schema issues for 2024 import:
1. Country columns incorrectly typed as NUMERIC -> VARCHAR
2. preparer_foreign_cntry also NUMERIC -> VARCHAR
"""
import os, psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Enable import mode
cur.execute("SET session \"dol.import_mode\" = 'active';")

# Fix country columns that should be VARCHAR, not NUMERIC
fixes = [
    ("form_5500", "spons_dfe_mail_foreign_cntry", "VARCHAR(100)"),
    ("form_5500", "spons_dfe_loc_foreign_cntry", "VARCHAR(100)"),
    ("form_5500", "admin_foreign_cntry", "VARCHAR(100)"),
    ("form_5500", "preparer_foreign_cntry", "VARCHAR(100)"),
]

for table, col, new_type in fixes:
    sql = f"ALTER TABLE dol.{table} ALTER COLUMN {col} TYPE {new_type} USING {col}::text;"
    print(f"  Fixing dol.{table}.{col} -> {new_type}")
    cur.execute(sql)

conn.commit()
print("\nDone. Country columns fixed.")
conn.close()
