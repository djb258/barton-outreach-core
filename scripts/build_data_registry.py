"""
Build comprehensive data registry documentation for all sub-hubs.
Maps all tables, columns, enrichments, and relationships.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict
import json

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_all_schemas_tables():
    """Get all schemas and their tables with row counts."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all tables with row counts
    cur.execute("""
        SELECT 
            schemaname as schema,
            relname as table_name,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, relname
    """)
    tables = cur.fetchall()
    
    conn.close()
    return tables

def get_table_columns(schema, table):
    """Get column info for a specific table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    columns = cur.fetchall()
    
    conn.close()
    return columns

def get_key_coverage(schema, table, columns):
    """Get coverage stats for key columns (URLs, EINs, IDs, enrichment fields)."""
    key_patterns = ['url', 'domain', 'ein', 'email', 'phone', 'website', 
                    'linkedin', 'twitter', 'facebook', 'enriched', 'source']
    
    key_cols = [c['column_name'] for c in columns 
                if any(p in c['column_name'].lower() for p in key_patterns)]
    
    if not key_cols:
        return {}
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    coverage = {}
    for col in key_cols:
        try:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT("{col}") as populated
                FROM {schema}.{table}
            """)
            result = cur.fetchone()
            if result and result['total'] > 0:
                coverage[col] = {
                    'total': result['total'],
                    'populated': result['populated'],
                    'pct': round(100 * result['populated'] / result['total'], 1)
                }
        except Exception as e:
            coverage[col] = {'error': str(e)}
    
    conn.close()
    return coverage

def get_foreign_keys():
    """Get all foreign key relationships."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT
            tc.table_schema as schema,
            tc.table_name,
            kcu.column_name,
            ccu.table_schema AS foreign_schema,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_schema, tc.table_name
    """)
    fks = cur.fetchall()
    
    conn.close()
    return fks

def main():
    print("=" * 70)
    print("DATA REGISTRY BUILDER")
    print("=" * 70)
    
    # Get all tables
    print("\n[1] Fetching all schemas and tables...")
    tables = get_all_schemas_tables()
    
    # Group by schema
    schemas = defaultdict(list)
    for t in tables:
        schemas[t['schema']].append(t)
    
    print(f"    Found {len(schemas)} schemas, {len(tables)} tables")
    
    # Schema summary
    print("\n[2] Schema Summary:")
    print("-" * 50)
    for schema, tbls in sorted(schemas.items(), key=lambda x: -sum(t['row_count'] for t in x[1])):
        total_rows = sum(t['row_count'] for t in tbls)
        print(f"    {schema:20} | {len(tbls):3} tables | {total_rows:>10,} rows")
    
    # Build detailed registry for key schemas
    key_schemas = ['outreach', 'company', 'cl', 'dol', 'people', 'clay', 'intake', 'shq']
    
    registry = {}
    
    print("\n[3] Building detailed registry for key schemas...")
    for schema in key_schemas:
        if schema not in schemas:
            continue
            
        print(f"\n    Processing {schema}...")
        registry[schema] = {'tables': {}}
        
        for t in schemas[schema]:
            table_name = t['table_name']
            cols = get_table_columns(schema, table_name)
            coverage = get_key_coverage(schema, table_name, cols)
            
            registry[schema]['tables'][table_name] = {
                'row_count': t['row_count'],
                'columns': [c['column_name'] for c in cols],
                'key_coverage': coverage
            }
            
            if coverage:
                print(f"        {table_name}: {t['row_count']:,} rows, {len(coverage)} enrichment cols")
    
    # Get FK relationships
    print("\n[4] Mapping foreign key relationships...")
    fks = get_foreign_keys()
    relationships = defaultdict(list)
    for fk in fks:
        key = f"{fk['schema']}.{fk['table_name']}"
        relationships[key].append({
            'column': fk['column_name'],
            'references': f"{fk['foreign_schema']}.{fk['foreign_table']}.{fk['foreign_column']}"
        })
    
    # Save JSON registry
    output = {
        'schemas': registry,
        'relationships': dict(relationships)
    }
    
    with open('scripts/data_registry.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n[5] Saved to scripts/data_registry.json")
    
    # Generate markdown documentation
    generate_markdown_docs(registry, relationships, schemas)
    
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)

def generate_markdown_docs(registry, relationships, all_schemas):
    """Generate the markdown documentation file."""
    
    md = []
    md.append("# Data Registry — Sub-Hub Reference\n")
    md.append("**Generated**: 2026-01-23\n")
    md.append("**Purpose**: Single source of truth for where data lives across all sub-hubs.\n")
    md.append("\n---\n")
    
    # Quick reference
    md.append("## Quick Reference\n")
    md.append("| Schema | Purpose | Key Tables | Master ID |\n")
    md.append("|--------|---------|------------|----------|\n")
    md.append("| `outreach` | Outreach spine & coordination | outreach, blog, dol | `outreach_id` |\n")
    md.append("| `company` | Company master & slots | company_master, company_slots | `company_unique_id` |\n")
    md.append("| `cl` | Company Lifecycle pipeline | company_identity, company_domains | `sovereign_company_id` |\n")
    md.append("| `dol` | DOL Form 5500 filings | form_5500, form_5500_sf | `ein` |\n")
    md.append("| `people` | People/contacts master | person_master, person_slots | `person_unique_id` |\n")
    md.append("| `clay` | Clay enrichment results | company_raw | `company_unique_id` |\n")
    md.append("| `intake` | Data intake staging | various | varies |\n")
    md.append("| `shq` | Error/signal queue | error_log | `error_id` |\n")
    md.append("\n---\n")
    
    # ID Relationships
    md.append("## ID Relationships (How Tables Connect)\n")
    md.append("```\n")
    md.append("outreach.outreach.outreach_id\n")
    md.append("    ├── outreach.blog.outreach_id\n")
    md.append("    ├── outreach.dol.outreach_id\n")
    md.append("    └── company.company_master.outreach_id\n")
    md.append("            ├── company.company_slots.company_unique_id\n")
    md.append("            ├── company.company_source_urls.company_unique_id\n")
    md.append("            └── clay.company_raw.company_unique_id\n")
    md.append("\n")
    md.append("cl.company_identity.sovereign_company_id\n")
    md.append("    └── cl.company_domains.sovereign_company_id\n")
    md.append("\n")
    md.append("dol.form_5500.sponsor_dfe_ein\n")
    md.append("    └── outreach.dol.ein (matched via EIN)\n")
    md.append("```\n")
    md.append("\n---\n")
    
    # Detailed schema sections
    for schema_name in ['outreach', 'company', 'cl', 'dol', 'people', 'clay']:
        if schema_name not in registry:
            continue
            
        schema_data = registry[schema_name]
        md.append(f"## Schema: `{schema_name}`\n")
        
        for table_name, table_data in sorted(schema_data['tables'].items(), 
                                              key=lambda x: -x[1]['row_count']):
            rows = table_data['row_count']
            md.append(f"### `{schema_name}.{table_name}` — {rows:,} rows\n")
            
            # Key columns with coverage
            if table_data['key_coverage']:
                md.append("**Enrichment Coverage:**\n")
                md.append("| Column | Populated | Coverage |\n")
                md.append("|--------|-----------|----------|\n")
                for col, stats in table_data['key_coverage'].items():
                    if 'error' not in stats:
                        md.append(f"| `{col}` | {stats['populated']:,} | {stats['pct']}% |\n")
                md.append("\n")
            
            # All columns
            md.append(f"**Columns:** `{'`, `'.join(table_data['columns'][:15])}`")
            if len(table_data['columns']) > 15:
                md.append(f" ... +{len(table_data['columns'])-15} more")
            md.append("\n\n")
        
        md.append("---\n")
    
    # Enrichment summary
    md.append("## Enrichment Data Locations\n")
    md.append("### URLs / Domains\n")
    md.append("| Location | Column | Records | Coverage |\n")
    md.append("|----------|--------|---------|----------|\n")
    md.append("| `outreach.outreach` | `domain` | 51,148 | 100% |\n")
    md.append("| `outreach.blog` | `source_url` | 51,148 | **0%** ❌ |\n")
    md.append("| `company.company_master` | `website_url` | 74,641 | ~98% |\n")
    md.append("| `company.company_source_urls` | `source_url` | 97,124 | 100% |\n")
    md.append("| `cl.company_domains` | `domain` | 51,910 | 100% |\n")
    md.append("\n")
    
    md.append("### EIN / DOL Data\n")
    md.append("| Location | Column | Records | Coverage |\n")
    md.append("|----------|--------|---------|----------|\n")
    md.append("| `outreach.dol` | `ein` | 13,829 | 100% |\n")
    md.append("| `company.company_master` | `ein` | 74,641 | ~27% |\n")
    md.append("| `dol.form_5500` | `sponsor_dfe_ein` | 1.1M+ | 100% |\n")
    md.append("| `dol.form_5500_sf` | `sf_spons_ein` | 200K+ | 100% |\n")
    md.append("\n")
    
    md.append("### Email / Contact Data\n")
    md.append("| Location | Column | Records | Notes |\n")
    md.append("|----------|--------|---------|-------|\n")
    md.append("| `people.person_master` | `email` | 26,299 | Primary contact emails |\n")
    md.append("| `company.company_slots` | `person_unique_id` | 153,444 | 17.5% filled |\n")
    md.append("\n")
    
    md.append("---\n")
    md.append("## Usage Notes\n")
    md.append("1. **Master list**: `outreach.outreach` (51,148 records) is the operational spine\n")
    md.append("2. **CL Authority**: `cl.company_identity` is the authority registry\n")
    md.append("3. **URLs**: Check `company.company_source_urls` first (97K records)\n")
    md.append("4. **EINs**: Match through `outreach.dol` → `dol.form_5500`\n")
    md.append("5. **Enrichments**: Clay results in `clay.company_raw`\n")
    
    # Write file
    with open('docs/DATA_REGISTRY.md', 'w', encoding='utf-8') as f:
        f.write(''.join(md))
    
    print(f"    Generated docs/DATA_REGISTRY.md")

if __name__ == "__main__":
    main()
