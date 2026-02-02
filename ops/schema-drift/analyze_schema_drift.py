#!/usr/bin/env python3
"""
Analyze schema drift between ERD documentation and Neon database
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

def load_neon_snapshot() -> Dict:
    """Load the Neon schema snapshot"""
    with open('neon_schema_snapshot.json', 'r') as f:
        return json.load(f)

def parse_schema_md(file_path: str) -> Dict[str, Dict]:
    """Parse a SCHEMA.md file to extract table definitions from Mermaid ERD blocks"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = {}

    # Extract mermaid blocks
    mermaid_blocks = re.findall(r'```mermaid\s+erDiagram(.*?)```', content, re.DOTALL | re.IGNORECASE)

    for block in mermaid_blocks:
        # Find entity definitions (tables with column lists)
        # Pattern: TABLE_NAME { column_name type constraints }
        entity_pattern = r'(\w+)\s*\{([^}]+)\}'
        entities = re.findall(entity_pattern, block)

        for entity_name, columns_text in entities:
            # Convert entity name from MERMAID format (SCHEMA_TABLE) to schema.table
            # Example: OUTREACH_OUTREACH -> outreach.outreach
            parts = entity_name.lower().split('_', 1)
            if len(parts) == 2:
                schema, table = parts
                full_name = f"{schema}.{table}"

                # Parse columns
                columns = []
                column_lines = [line.strip() for line in columns_text.split('\n') if line.strip()]

                for line in column_lines:
                    # Parse mermaid column format: data_type column_name constraints
                    # Example: "uuid outreach_id PK"
                    # Example: "text company_name"
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        col_type = parts[0]
                        col_name = parts[1]
                        constraints = ' '.join(parts[2:]) if len(parts) > 2 else ''

                        columns.append({
                            'name': col_name,
                            'type': col_type,
                            'nullable': 'NOT NULL' not in constraints.upper(),
                            'raw': line
                        })

                if columns:
                    tables[full_name] = {
                        'columns': columns,
                        'source': file_path
                    }

    return tables

def get_all_erd_tables() -> Dict[str, Dict]:
    """Get all tables documented in ERD files"""
    erd_tables = {}

    schema_files = [
        'hubs/blog-content/SCHEMA.md',
        'hubs/company-target/SCHEMA.md',
        'hubs/dol-filings/SCHEMA.md',
        'hubs/outreach-execution/SCHEMA.md',
        'hubs/people-intelligence/SCHEMA.md',
        'hubs/talent-flow/SCHEMA.md'
    ]

    for schema_file in schema_files:
        if os.path.exists(schema_file):
            tables = parse_schema_md(schema_file)
            erd_tables.update(tables)
            print(f"Loaded {len(tables)} tables from {schema_file}")

    return erd_tables

def normalize_type(pg_type: str) -> str:
    """Normalize PostgreSQL data type for comparison"""
    # Handle common variations
    type_map = {
        'character varying': 'varchar',
        'timestamp without time zone': 'timestamp',
        'timestamp with time zone': 'timestamptz',
        'integer': 'int',
        'bigint': 'int8',
        'boolean': 'bool',
        'double precision': 'float8',
    }

    pg_type_lower = pg_type.lower()
    for full, short in type_map.items():
        if pg_type_lower == full:
            return short

    return pg_type_lower.split('(')[0]  # Remove length modifiers

def compare_schemas(neon_data: Dict, erd_tables: Dict[str, Dict]) -> Dict:
    """Compare Neon schema against ERD documentation"""

    # Get sets of table names
    neon_tables = {f"{t['table_schema']}.{t['table_name']}" for t in neon_data['tables']}
    erd_table_names = set(erd_tables.keys())

    # Filter to only tables we expect to be documented (outreach, cl, people, dol, company, bit)
    relevant_schemas = {'outreach', 'cl', 'people', 'dol', 'company', 'bit'}
    neon_relevant = {t for t in neon_tables if t.split('.')[0] in relevant_schemas}

    # Find differences
    in_neon_not_erd = neon_relevant - erd_table_names
    in_erd_not_neon = erd_table_names - neon_relevant
    in_both = neon_relevant & erd_table_names

    # Compare columns for tables in both
    column_mismatches = []

    for table_name in sorted(in_both):
        schema, table = table_name.split('.')

        # Get Neon columns
        neon_cols = {col['column_name']: col for col in neon_data['schema_details'].get(table_name, [])}

        # Get ERD columns
        erd_cols = {col['name']: col for col in erd_tables[table_name]['columns']}

        # Compare
        neon_col_names = set(neon_cols.keys())
        erd_col_names = set(erd_cols.keys())

        cols_in_neon_not_erd = neon_col_names - erd_col_names
        cols_in_erd_not_neon = erd_col_names - neon_col_names

        # Check data types for matching columns
        type_mismatches = []
        for col_name in neon_col_names & erd_col_names:
            neon_type = normalize_type(neon_cols[col_name]['data_type'])
            erd_type = normalize_type(erd_cols[col_name]['type'])

            if neon_type != erd_type:
                type_mismatches.append({
                    'column': col_name,
                    'neon_type': neon_cols[col_name]['data_type'],
                    'erd_type': erd_cols[col_name]['type']
                })

        if cols_in_neon_not_erd or cols_in_erd_not_neon or type_mismatches:
            column_mismatches.append({
                'table': table_name,
                'in_neon_not_erd': sorted(cols_in_neon_not_erd),
                'in_erd_not_neon': sorted(cols_in_erd_not_neon),
                'type_mismatches': type_mismatches,
                'erd_source': erd_tables[table_name]['source']
            })

    return {
        'tables_in_neon_not_erd': sorted(in_neon_not_erd),
        'tables_in_erd_not_neon': sorted(in_erd_not_neon),
        'tables_in_both': sorted(in_both),
        'column_mismatches': column_mismatches,
        'neon_table_count': len(neon_relevant),
        'erd_table_count': len(erd_table_names),
        'matching_tables': len(in_both)
    }

def generate_report(comparison: Dict) -> str:
    """Generate markdown drift report"""

    report = []
    report.append("# ERD vs Neon Schema Drift Report\n")
    report.append(f"**Generated**: {os.popen('date /t').read().strip()} {os.popen('time /t').read().strip()}\n")
    report.append(f"**Neon Tables (Relevant Schemas)**: {comparison['neon_table_count']}")
    report.append(f"**ERD Documented Tables**: {comparison['erd_table_count']}")
    report.append(f"**Matching Tables**: {comparison['matching_tables']}\n")

    # Summary
    report.append("## Summary\n")
    report.append(f"- **Undocumented Tables** (in Neon, not in ERD): {len(comparison['tables_in_neon_not_erd'])}")
    report.append(f"- **Stale/Missing Tables** (in ERD, not in Neon): {len(comparison['tables_in_erd_not_neon'])}")
    report.append(f"- **Tables with Column Mismatches**: {len(comparison['column_mismatches'])}\n")

    # Undocumented tables
    if comparison['tables_in_neon_not_erd']:
        report.append("## 1. Tables in Neon but NOT in ERD (Undocumented)\n")
        report.append("These tables exist in the database but are not documented in any SCHEMA.md file:\n")

        # Group by schema
        by_schema = {}
        for table in comparison['tables_in_neon_not_erd']:
            schema = table.split('.')[0]
            if schema not in by_schema:
                by_schema[schema] = []
            by_schema[schema].append(table)

        for schema in sorted(by_schema.keys()):
            report.append(f"\n### {schema} schema\n")
            for table in sorted(by_schema[schema]):
                report.append(f"- `{table}`")
        report.append("")

    # Stale documentation
    if comparison['tables_in_erd_not_neon']:
        report.append("## 2. Tables in ERD but NOT in Neon (Stale Documentation)\n")
        report.append("These tables are documented but don't exist in the database:\n")
        for table in comparison['tables_in_erd_not_neon']:
            report.append(f"- `{table}`")
        report.append("")

    # Column mismatches
    if comparison['column_mismatches']:
        report.append("## 3. Column Mismatches\n")
        report.append("Tables where columns differ between ERD and Neon:\n")

        for mismatch in comparison['column_mismatches']:
            report.append(f"\n### {mismatch['table']}\n")
            report.append(f"*Source: `{mismatch['erd_source']}`*\n")

            if mismatch['in_neon_not_erd']:
                report.append("**Columns in Neon but not in ERD:**")
                for col in mismatch['in_neon_not_erd']:
                    report.append(f"- `{col}`")
                report.append("")

            if mismatch['in_erd_not_neon']:
                report.append("**Columns in ERD but not in Neon:**")
                for col in mismatch['in_erd_not_neon']:
                    report.append(f"- `{col}`")
                report.append("")

            if mismatch['type_mismatches']:
                report.append("**Data Type Mismatches:**\n")
                report.append("| Column | Neon Type | ERD Type |")
                report.append("|--------|-----------|----------|")
                for tm in mismatch['type_mismatches']:
                    report.append(f"| `{tm['column']}` | `{tm['neon_type']}` | `{tm['erd_type']}` |")
                report.append("")

    # Recommendations
    report.append("## 4. Recommendations\n")

    if comparison['tables_in_neon_not_erd']:
        report.append("### Undocumented Tables")
        report.append("- Review each undocumented table")
        report.append("- If table is operational: Add to appropriate SCHEMA.md")
        report.append("- If table is legacy/unused: Consider archiving or dropping")
        report.append("- Special attention to: *_archive, *_errors, *_excluded tables\n")

    if comparison['tables_in_erd_not_neon']:
        report.append("### Stale Documentation")
        report.append("- Remove or mark as deprecated in ERD")
        report.append("- Update migration scripts if tables were intentionally dropped\n")

    if comparison['column_mismatches']:
        report.append("### Column Mismatches")
        report.append("- Update SCHEMA.md files to reflect actual Neon schema")
        report.append("- Consider if schema changes need migrations")
        report.append("- Verify foreign key relationships are documented")

    return "\n".join(report)

def main():
    """Main execution"""
    print("Loading Neon schema snapshot...")
    neon_data = load_neon_snapshot()

    print("\nParsing ERD documentation...")
    erd_tables = get_all_erd_tables()

    print(f"\nFound {len(erd_tables)} tables in ERD documentation")

    print("\nComparing schemas...")
    comparison = compare_schemas(neon_data, erd_tables)

    print("\nGenerating report...")
    report = generate_report(comparison)

    # Save report
    with open('ERD_NEON_DRIFT_REPORT.md', 'w') as f:
        f.write(report)

    print("\n" + "="*80)
    print("DRIFT REPORT SUMMARY")
    print("="*80)
    print(f"Neon Tables: {comparison['neon_table_count']}")
    print(f"ERD Tables: {comparison['erd_table_count']}")
    print(f"Matching: {comparison['matching_tables']}")
    print(f"Undocumented (in Neon only): {len(comparison['tables_in_neon_not_erd'])}")
    print(f"Stale (in ERD only): {len(comparison['tables_in_erd_not_neon'])}")
    print(f"Column mismatches: {len(comparison['column_mismatches'])}")
    print("\nFull report saved to: ERD_NEON_DRIFT_REPORT.md")

if __name__ == '__main__':
    main()
