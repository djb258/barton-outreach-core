#!/usr/bin/env python3
"""Clean-slate audit of Outreach repo for Phase 2C."""

import psycopg2
import os
import re

print('=' * 70)
print('  OUTREACH REPO CLEAN-SLATE AUDIT')
print('  Date: 2025-12-26')
print('  Auditor: Doctrine Enforcement Engineer')
print('=' * 70)
print()

# Connect to Neon
conn = psycopg2.connect(
    host='ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    database='Marketing DB',
    user='Marketing DB_owner',
    password='npg_OsE4Z2oPCpiT',
    sslmode='require'
)
cur = conn.cursor()

results = {
    'pass': [],
    'fail': [],
    'warn': []
}

# ============================================================================
# AUDIT 1: Table Ownership Comments
# ============================================================================
print('AUDIT 1: Table Ownership Comments')
print('-' * 40)

cur.execute('''
    SELECT c.relname, d.description
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
    WHERE n.nspname = 'outreach' AND c.relkind = 'r'
''')

for table, desc in cur.fetchall():
    if desc and 'Sub-hub:' in desc:
        print(f'  [PASS] outreach.{table}: Has ownership comment')
        results['pass'].append(f'Table comment: outreach.{table}')
    else:
        print(f'  [FAIL] outreach.{table}: Missing ownership comment')
        results['fail'].append(f'Missing table comment: outreach.{table}')

print()

# ============================================================================
# AUDIT 2: Anchor Topology (FK to CL)
# ============================================================================
print('AUDIT 2: Anchor Topology')
print('-' * 40)

# Check company_target has FK to CL
cur.execute('''
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = 'outreach'
    AND table_name = 'company_target'
    AND column_name = 'company_unique_id'
''')
has_fk_col = cur.fetchone()[0] > 0

if has_fk_col:
    print('  [PASS] company_target has company_unique_id column')
    results['pass'].append('Anchor: company_target.company_unique_id exists')
else:
    print('  [FAIL] company_target missing company_unique_id')
    results['fail'].append('Anchor: company_target.company_unique_id missing')

# Check no other table has direct CL FK
cur.execute('''
    SELECT tc.table_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'outreach'
    AND tc.table_name != 'company_target'
    AND ccu.table_schema = 'cl'
''')
bypasses = cur.fetchall()

if not bypasses:
    print('  [PASS] No CL bypass detected')
    results['pass'].append('Anchor: No CL bypass')
else:
    for t, c in bypasses:
        print(f'  [FAIL] {t}.{c} bypasses anchor')
        results['fail'].append(f'CL bypass: {t}.{c}')

print()

# ============================================================================
# AUDIT 3: Column Registry Coverage
# ============================================================================
print('AUDIT 3: Column Registry Coverage')
print('-' * 40)

cur.execute('''
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = 'outreach' AND table_name != 'column_registry'
''')
total_cols = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(*) FROM outreach.column_registry
    WHERE schema_name = 'outreach'
''')
registered_cols = cur.fetchone()[0]

coverage = (registered_cols / total_cols * 100) if total_cols > 0 else 0
print(f'  Total columns: {total_cols}')
print(f'  Registered: {registered_cols}')
print(f'  Coverage: {coverage:.1f}%')

if coverage >= 80:
    print(f'  [PASS] Coverage >= 80%')
    results['pass'].append(f'Column registry: {coverage:.1f}% coverage')
else:
    print(f'  [FAIL] Coverage < 80%')
    results['fail'].append(f'Column registry: {coverage:.1f}% coverage (need 80%)')

print()

# ============================================================================
# AUDIT 4: Column Comments
# ============================================================================
print('AUDIT 4: Column Comments')
print('-' * 40)

cur.execute('''
    SELECT COUNT(*) FROM (
        SELECT a.attname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = a.attnum
        WHERE n.nspname = 'outreach' AND c.relkind = 'r' AND a.attnum > 0
        AND NOT a.attisdropped AND d.description IS NOT NULL
    ) commented
''')
commented_cols = cur.fetchone()[0]

# Total including column_registry
cur.execute('''
    SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'outreach'
''')
all_cols = cur.fetchone()[0]

comment_coverage = (commented_cols / all_cols * 100) if all_cols > 0 else 0
print(f'  Columns with comments: {commented_cols}/{all_cols}')
print(f'  Coverage: {comment_coverage:.1f}%')

if comment_coverage >= 80:
    print(f'  [PASS] Comment coverage >= 80%')
    results['pass'].append(f'Column comments: {comment_coverage:.1f}%')
else:
    print(f'  [WARN] Comment coverage < 80%')
    results['warn'].append(f'Column comments: {comment_coverage:.1f}%')

print()

cur.close()
conn.close()

# ============================================================================
# AUDIT 5: Hub Manifests
# ============================================================================
print('AUDIT 5: Hub Manifests')
print('-' * 40)

manifest_path = 'hubs/company-target/hub.manifest.yaml'
if os.path.exists(manifest_path):
    with open(manifest_path) as f:
        content = f.read()
    if 'sub-hub' in content and 'HUB-COMPANY-LIFECYCLE' in content:
        print(f'  [PASS] company-target manifest declares sub-hub with CL parent')
        results['pass'].append('Manifest: company-target correct')
    else:
        print(f'  [FAIL] company-target manifest missing sub-hub/parent')
        results['fail'].append('Manifest: company-target incorrect')
else:
    print(f'  [FAIL] company-target manifest not found')
    results['fail'].append('Manifest: company-target not found')

print()

# ============================================================================
# AUDIT 6: Identity Minting Code Check
# ============================================================================
print('AUDIT 6: Identity Minting Check')
print('-' * 40)

identity_violations = []
forbidden_patterns = [
    r'company_unique_id\s*=\s*str\(uuid',
    r'gen_random_uuid.*company_unique_id',
    r'mint.*company.*id',
]

if os.path.exists('hubs'):
    for root, dirs, files in os.walk('hubs'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                fpath = os.path.join(root, f)
                with open(fpath, 'r', errors='ignore') as file:
                    content = file.read()
                for pattern in forbidden_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        identity_violations.append(fpath)
                        break

if not identity_violations:
    print('  [PASS] No identity minting in hubs/')
    results['pass'].append('Identity: No minting in hubs/')
else:
    for v in identity_violations:
        print(f'  [FAIL] {v}')
        results['fail'].append(f'Identity minting: {v}')

print()

# ============================================================================
# AUDIT 7: CI Guards Exist
# ============================================================================
print('AUDIT 7: CI Guards')
print('-' * 40)

guards = [
    ('.github/workflows/constitutional-hub-guard.yml', 'Constitutional Hub Guard'),
    ('.github/workflows/outreach-schema-guard.yml', 'Outreach Schema Guard'),
    ('.github/workflows/hub-spoke-guard.yml', 'Hub-Spoke Guard'),
]

for path, name in guards:
    if os.path.exists(path):
        print(f'  [PASS] {name} exists')
        results['pass'].append(f'CI: {name}')
    else:
        print(f'  [FAIL] {name} missing')
        results['fail'].append(f'CI: {name} missing')

print()

# ============================================================================
# AUDIT 8: Doctrine Documents
# ============================================================================
print('AUDIT 8: Doctrine Documents')
print('-' * 40)

docs = [
    ('doctrine/CL_NON_OPERATIONAL_LOCK.md', 'CL Non-Operational Lock'),
    ('doctrine/CL_ADMISSION_GATE_DOCTRINE.md', 'CL Admission Gate'),
    ('doctrine/CL_ADMISSION_GATE_WIRING.md', 'CL Admission Wiring'),
]

for path, name in docs:
    if os.path.exists(path):
        print(f'  [PASS] {name} exists')
        results['pass'].append(f'Doctrine: {name}')
    else:
        print(f'  [FAIL] {name} missing')
        results['fail'].append(f'Doctrine: {name} missing')

print()

# ============================================================================
# SUMMARY
# ============================================================================
print('=' * 70)
print('  AUDIT SUMMARY')
print('=' * 70)
print()
print(f'  PASS: {len(results["pass"])}')
print(f'  FAIL: {len(results["fail"])}')
print(f'  WARN: {len(results["warn"])}')
print()

if results['fail']:
    print('  FAILURES:')
    for f in results['fail']:
        print(f'    - {f}')
    print()
    print('  VERDICT: FAIL')
else:
    print('  VERDICT: PASS')
print()
