"""
Verify RLS Migration on Neon PostgreSQL
Date: 2026-01-13
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from urllib.parse import quote_plus

# Connection string (via Doppler env vars)
CONNECTION_STRING = (
    f"postgresql://{quote_plus(os.environ['NEON_USER'])}:{quote_plus(os.environ['NEON_PASSWORD'])}@"
    f"{os.environ['NEON_HOST']}/"
    f"{quote_plus(os.environ['NEON_DATABASE'])}?sslmode=require"
)

def verify_migration():
    """Verify the RLS migration was successful"""
    print("=" * 80)
    print("VERIFYING RLS MIGRATION ON NEON POSTGRESQL")
    print("=" * 80)

    try:
        conn = psycopg2.connect(CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("[OK] Connected to database\n")

        # 1. Verify roles created
        print("=" * 80)
        print("1. CHECKING ROLES")
        print("=" * 80)
        cursor.execute("""
            SELECT rolname, rolcanlogin
            FROM pg_roles
            WHERE rolname IN ('outreach_hub_writer', 'dol_hub_writer', 'hub_reader')
            ORDER BY rolname;
        """)
        roles = cursor.fetchall()

        if roles:
            print(f"Found {len(roles)} application roles:")
            for role in roles:
                login_status = "CAN LOGIN" if role['rolcanlogin'] else "NOLOGIN"
                print(f"  - {role['rolname']} ({login_status})")
        else:
            print("[WARNING] No application roles found!")

        # 2. Verify RLS enabled on tables
        print("\n" + "=" * 80)
        print("2. CHECKING RLS STATUS ON TABLES")
        print("=" * 80)
        cursor.execute("""
            SELECT
                n.nspname AS schema_name,
                c.relname AS table_name,
                c.relrowsecurity AS rls_enabled,
                c.relforcerowsecurity AS rls_forced
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname IN ('outreach', 'dol')
              AND c.relkind = 'r'
            ORDER BY n.nspname, c.relname;
        """)
        tables = cursor.fetchall()

        if tables:
            print(f"Found {len(tables)} tables in outreach/dol schemas:")
            rls_enabled_count = 0
            for table in tables:
                status = "ENABLED" if table['rls_enabled'] else "DISABLED"
                if table['rls_enabled']:
                    rls_enabled_count += 1
                print(f"  - {table['schema_name']}.{table['table_name']}: RLS {status}")
            print(f"\nTables with RLS enabled: {rls_enabled_count}/{len(tables)}")
        else:
            print("[WARNING] No tables found in outreach/dol schemas!")

        # 3. Verify policies created
        print("\n" + "=" * 80)
        print("3. CHECKING RLS POLICIES")
        print("=" * 80)
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                policyname,
                cmd,
                permissive
            FROM pg_policies
            WHERE schemaname IN ('outreach', 'dol')
            ORDER BY schemaname, tablename, policyname;
        """)
        policies = cursor.fetchall()

        if policies:
            print(f"Found {len(policies)} RLS policies:\n")

            # Group by table
            from collections import defaultdict
            policies_by_table = defaultdict(list)
            for policy in policies:
                table_key = f"{policy['schemaname']}.{policy['tablename']}"
                policies_by_table[table_key].append(policy)

            for table_name, table_policies in sorted(policies_by_table.items()):
                print(f"  {table_name}:")
                for policy in table_policies:
                    print(f"    - {policy['policyname']} ({policy['cmd']})")
        else:
            print("[WARNING] No policies found!")

        # 4. Verify immutability trigger
        print("\n" + "=" * 80)
        print("4. CHECKING IMMUTABILITY TRIGGER")
        print("=" * 80)
        cursor.execute("""
            SELECT
                trigger_name,
                event_manipulation,
                action_statement
            FROM information_schema.triggers
            WHERE event_object_schema = 'outreach'
              AND event_object_table = 'engagement_events'
              AND trigger_name LIKE '%immutability%';
        """)
        triggers = cursor.fetchall()

        if triggers:
            print(f"Found {len(triggers)} immutability trigger(s):")
            for trigger in triggers:
                print(f"  - {trigger['trigger_name']} (ON {trigger['event_manipulation']})")
        else:
            print("[WARNING] No immutability trigger found on engagement_events!")

        # 5. Verify permissions
        print("\n" + "=" * 80)
        print("5. CHECKING ROLE PERMISSIONS")
        print("=" * 80)
        cursor.execute("""
            SELECT
                grantee,
                table_schema,
                table_name,
                privilege_type
            FROM information_schema.table_privileges
            WHERE grantee IN ('outreach_hub_writer', 'dol_hub_writer', 'hub_reader')
              AND table_schema IN ('outreach', 'dol')
            ORDER BY grantee, table_schema, table_name, privilege_type;
        """)
        permissions = cursor.fetchall()

        if permissions:
            from collections import defaultdict
            perms_by_role = defaultdict(lambda: defaultdict(set))

            for perm in permissions:
                perms_by_role[perm['grantee']][f"{perm['table_schema']}.{perm['table_name']}"].add(perm['privilege_type'])

            for role, tables in sorted(perms_by_role.items()):
                print(f"\n  Role: {role}")
                for table, privs in sorted(tables.items()):
                    print(f"    {table}: {', '.join(sorted(privs))}")
        else:
            print("[WARNING] No permissions found for application roles!")

        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] during verification: {e}")
        return False

    return True

if __name__ == "__main__":
    verify_migration()
