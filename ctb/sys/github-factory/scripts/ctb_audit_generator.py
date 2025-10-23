#!/usr/bin/env python3
"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/github-factory
Barton ID: 04.04.06.02
Unique ID: CTB-AUDIT-GEN-001
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────

CTB Audit Report Generator

Generates comprehensive audit report with:
- Metadata coverage statistics
- Enforcement distribution
- Branch compliance scores
- Recommendations
- Overall CTB compliance score (0-100)
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import datetime

# CTB Branch definitions with expected purposes
CTB_BRANCHES = {
    'sys/firebase-workbench': 'Firebase configuration and MCP',
    'sys/composio-mcp': 'Composio MCP server integration',
    'sys/neon-vault': 'Neon PostgreSQL schemas and migrations',
    'sys/github-factory': 'CI/CD automation and GitHub Actions',
    'sys/security-audit': 'Security compliance and auditing',
    'sys/chartdb': 'Database schema visualization',
    'sys/activepieces': 'Workflow automation platform',
    'sys/windmill': 'Workflow engine',
    'sys/api': 'API services and endpoints',
    'sys/ops': 'Operations tooling (ORBT)',
    'sys/cli': 'Command-line interfaces',
    'sys/services': 'Backend services',
    'sys/tooling': 'System tooling and utilities',
    'sys/tests': 'System-level tests',
    'sys/packages': 'System-level packages',
    'ai/agents': 'HEIR agents (orchestrators, specialists)',
    'ai/garage-bay': 'Garage Bay Python tools',
    'ai/testing': 'AI and MCP testing scripts',
    'ai/scripts': 'AI automation scripts',
    'ai/tools': 'AI utilities and tools',
    'data/infra': 'Database infrastructure schemas',
    'data/migrations': 'SQL migration scripts',
    'data/schemas': 'Schema definitions and maps',
    'docs/analysis': 'Analysis and production readiness docs',
    'docs/audit': 'Audit reports and compliance',
    'docs/examples': 'Code examples and patterns',
    'docs/scripts': 'Documentation generation scripts',
    'docs/archive': 'Archived documentation',
    'ui/apps': 'Frontend applications',
    'ui/src': 'UI source code',
    'ui/public': 'Static assets',
    'ui/templates': 'UI templates',
    'ui/packages': 'UI packages (data-router, mcp-clients)',
    'meta/global-config': 'CTB doctrine and global config',
    'meta/config': 'Application configuration',
}

# Skip patterns
SKIP_PATTERNS = ['node_modules', '.git', '__pycache__', 'dist', 'build', '.next']
SKIP_EXTENSIONS = ['.map', '.pyc', '.min.js', '.min.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.ttf', '.woff', '.woff2']


class CTBMetadata:
    """Represents extracted CTB metadata from a file."""
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.has_metadata = False
        self.ctb_branch = None
        self.barton_id = None
        self.unique_id = None
        self.blueprint_hash = None
        self.last_updated = None
        self.enforcement = None


def should_skip(filepath: Path) -> bool:
    """Check if file should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in str(filepath):
            return True

    ext = filepath.suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return True

    return False


def extract_metadata(filepath: Path) -> CTBMetadata:
    """Extract CTB metadata from a file."""
    metadata = CTBMetadata(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # Read first 2000 chars

            # Check for CTB metadata
            if 'CTB Classification Metadata' not in content:
                return metadata

            metadata.has_metadata = True

            # Extract fields using regex
            if match := re.search(r'CTB Branch:\s*(.+)', content):
                metadata.ctb_branch = match.group(1).strip()

            if match := re.search(r'Barton ID:\s*(.+)', content):
                metadata.barton_id = match.group(1).strip()

            if match := re.search(r'Unique ID:\s*(.+)', content):
                metadata.unique_id = match.group(1).strip()

            if match := re.search(r'Blueprint Hash:\s*(.+)', content):
                val = match.group(1).strip()
                metadata.blueprint_hash = val if val else None

            if match := re.search(r'Last Updated:\s*(.+)', content):
                metadata.last_updated = match.group(1).strip()

            if match := re.search(r'Enforcement:\s*(.+)', content):
                metadata.enforcement = match.group(1).strip()

    except Exception:
        pass

    return metadata


def get_ctb_branch_from_path(filepath: Path, ctb_root: Path) -> str:
    """Determine CTB branch from file path."""
    rel_path = filepath.relative_to(ctb_root)
    parts = list(rel_path.parts)

    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    elif len(parts) >= 1:
        return parts[0]
    else:
        return "unknown"


def audit_repository(ctb_root: Path) -> Dict:
    """Audit the entire CTB repository."""
    stats = {
        'total_files': 0,
        'skipped_files': 0,
        'tagged_files': 0,
        'untagged_files': 0,
        'missing_barton_id': 0,
        'missing_unique_id': 0,
        'missing_enforcement': 0,
        'has_blueprint_hash': 0,
        'enforcement_dist': defaultdict(int),
        'branch_stats': defaultdict(lambda: {
            'total': 0,
            'tagged': 0,
            'untagged': 0,
            'missing_barton_id': 0,
            'enforcement': defaultdict(int),
            'file_types': defaultdict(int),
        }),
        'files': [],
    }

    # Walk through CTB directory
    for filepath in ctb_root.rglob('*'):
        if not filepath.is_file():
            continue

        stats['total_files'] += 1

        # Skip certain files
        if should_skip(filepath):
            stats['skipped_files'] += 1
            continue

        # Extract metadata
        metadata = extract_metadata(filepath)
        branch = get_ctb_branch_from_path(filepath, ctb_root)

        # Update stats
        if metadata.has_metadata:
            stats['tagged_files'] += 1
            stats['branch_stats'][branch]['tagged'] += 1

            if not metadata.barton_id or metadata.barton_id == '00.00.00':
                stats['missing_barton_id'] += 1
                stats['branch_stats'][branch]['missing_barton_id'] += 1

            if not metadata.unique_id:
                stats['missing_unique_id'] += 1

            if not metadata.enforcement or metadata.enforcement == 'None':
                stats['missing_enforcement'] += 1

            if metadata.blueprint_hash:
                stats['has_blueprint_hash'] += 1

            if metadata.enforcement:
                stats['enforcement_dist'][metadata.enforcement] += 1
                stats['branch_stats'][branch]['enforcement'][metadata.enforcement] += 1
        else:
            stats['untagged_files'] += 1
            stats['branch_stats'][branch]['untagged'] += 1

        # Track file types
        ext = filepath.suffix.lower()
        stats['branch_stats'][branch]['file_types'][ext] += 1
        stats['branch_stats'][branch]['total'] += 1

        # Store metadata
        stats['files'].append({
            'path': str(filepath.relative_to(ctb_root)),
            'branch': branch,
            'metadata': metadata,
        })

    return stats


def calculate_compliance_score(stats: Dict) -> Tuple[int, Dict[str, int]]:
    """Calculate CTB compliance score (0-100)."""
    scores = {}

    # 1. Metadata Coverage (30 points)
    if stats['total_files'] - stats['skipped_files'] > 0:
        taggable_files = stats['total_files'] - stats['skipped_files']
        coverage = (stats['tagged_files'] / taggable_files) * 100
        scores['metadata_coverage'] = int((coverage / 100) * 30)
    else:
        scores['metadata_coverage'] = 0

    # 2. Barton ID Completeness (20 points)
    if stats['tagged_files'] > 0:
        valid_ids = stats['tagged_files'] - stats['missing_barton_id']
        id_score = (valid_ids / stats['tagged_files']) * 100
        scores['barton_id_complete'] = int((id_score / 100) * 20)
    else:
        scores['barton_id_complete'] = 0

    # 3. Enforcement Classification (20 points)
    if stats['tagged_files'] > 0:
        classified = stats['tagged_files'] - stats['missing_enforcement']
        enf_score = (classified / stats['tagged_files']) * 100
        scores['enforcement_classified'] = int((enf_score / 100) * 20)
    else:
        scores['enforcement_classified'] = 0

    # 4. Branch Organization (15 points)
    # Penalize if too many files in root branches vs sub-branches
    branch_organization_score = 15  # Start at full points
    for branch, data in stats['branch_stats'].items():
        if '/' not in branch and data['total'] > 50:
            branch_organization_score -= 3  # Penalize unorganized branches
    scores['branch_organization'] = max(0, branch_organization_score)

    # 5. Blueprint Coverage (15 points)
    if stats['tagged_files'] > 0:
        bp_coverage = (stats['has_blueprint_hash'] / stats['tagged_files']) * 100
        scores['blueprint_coverage'] = int((bp_coverage / 100) * 15)
    else:
        scores['blueprint_coverage'] = 0

    total_score = sum(scores.values())
    return total_score, scores


def generate_report(stats: Dict, ctb_root: Path) -> str:
    """Generate markdown audit report."""
    total_score, score_breakdown = calculate_compliance_score(stats)
    now = datetime.datetime.now().isoformat()

    # Determine grade
    if total_score >= 90:
        grade = "🏆 EXCELLENT"
        grade_icon = "✅"
    elif total_score >= 75:
        grade = "✅ GOOD"
        grade_icon = "✅"
    elif total_score >= 60:
        grade = "⚠️ FAIR"
        grade_icon = "⚠️"
    elif total_score >= 40:
        grade = "⚠️ NEEDS IMPROVEMENT"
        grade_icon = "⚠️"
    else:
        grade = "❌ CRITICAL"
        grade_icon = "❌"

    report = f"""# 🏛️ CTB Doctrine Audit Report

**Repository**: barton-outreach-core
**Audit Date**: {now}
**CTB Compliance Score**: {total_score}/100 {grade_icon}
**Grade**: {grade}

---

## 📊 Executive Summary

### Overall Compliance Score: {total_score}/100

| Category | Score | Weight | Status |
|----------|-------|--------|--------|
| Metadata Coverage | {score_breakdown['metadata_coverage']}/30 | 30% | {"✅" if score_breakdown['metadata_coverage'] >= 24 else "⚠️" if score_breakdown['metadata_coverage'] >= 18 else "❌"} |
| Barton ID Completeness | {score_breakdown['barton_id_complete']}/20 | 20% | {"✅" if score_breakdown['barton_id_complete'] >= 16 else "⚠️" if score_breakdown['barton_id_complete'] >= 12 else "❌"} |
| Enforcement Classification | {score_breakdown['enforcement_classified']}/20 | 20% | {"✅" if score_breakdown['enforcement_classified'] >= 16 else "⚠️" if score_breakdown['enforcement_classified'] >= 12 else "❌"} |
| Branch Organization | {score_breakdown['branch_organization']}/15 | 15% | {"✅" if score_breakdown['branch_organization'] >= 12 else "⚠️" if score_breakdown['branch_organization'] >= 9 else "❌"} |
| Blueprint Coverage | {score_breakdown['blueprint_coverage']}/15 | 15% | {"✅" if score_breakdown['blueprint_coverage'] >= 12 else "⚠️" if score_breakdown['blueprint_coverage'] >= 9 else "❌"} |

---

## 📈 Repository Statistics

### File Coverage

- **Total Files**: {stats['total_files']:,}
- **Skipped Files**: {stats['skipped_files']:,} (binaries, node_modules, etc.)
- **Taggable Files**: {stats['total_files'] - stats['skipped_files']:,}
- **Tagged Files**: {stats['tagged_files']:,} ({(stats['tagged_files'] / max(1, stats['total_files'] - stats['skipped_files']) * 100):.1f}%)
- **Untagged Files**: {stats['untagged_files']:,} ({(stats['untagged_files'] / max(1, stats['total_files'] - stats['skipped_files']) * 100):.1f}%)

### Metadata Completeness

- **Files with Barton ID**: {stats['tagged_files'] - stats['missing_barton_id']:,} of {stats['tagged_files']:,}
- **Files with Valid Barton ID**: {stats['tagged_files'] - stats['missing_barton_id']:,} (excluding 00.00.00)
- **Files with Unique ID**: {stats['tagged_files'] - stats['missing_unique_id']:,} of {stats['tagged_files']:,}
- **Files with Enforcement**: {stats['tagged_files'] - stats['missing_enforcement']:,} of {stats['tagged_files']:,}
- **Files with Blueprint Hash**: {stats['has_blueprint_hash']:,} of {stats['tagged_files']:,}

### Enforcement Distribution

"""

    # Add enforcement distribution table
    report += "| Enforcement Type | Count | Percentage |\n"
    report += "|------------------|-------|-----------|\n"
    for enf_type in ['HEIR', 'ORBT', 'None']:
        count = stats['enforcement_dist'].get(enf_type, 0)
        pct = (count / max(1, stats['tagged_files'])) * 100
        icon = "✅" if count > 0 else "⚠️"
        report += f"| {icon} {enf_type} | {count} | {pct:.1f}% |\n"

    report += "\n---\n\n## 🌲 CTB Branch Compliance\n\n"

    # Sort branches by total files
    sorted_branches = sorted(
        stats['branch_stats'].items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )

    report += "| CTB Branch | Files | Tagged | Untagged | Missing Barton ID | HEIR | ORBT | None | Status |\n"
    report += "|------------|-------|--------|----------|-------------------|------|------|------|--------|\n"

    for branch, data in sorted_branches:
        total = data['total']
        tagged = data['tagged']
        untagged = data['untagged']
        missing_id = data['missing_barton_id']

        heir_count = data['enforcement'].get('HEIR', 0)
        orbt_count = data['enforcement'].get('ORBT', 0)
        none_count = data['enforcement'].get('None', 0)

        # Determine status
        if total == 0:
            status = "⚠️ Empty"
        elif tagged == 0:
            status = "❌ No Tags"
        elif untagged > tagged:
            status = "⚠️ Low Coverage"
        elif missing_id > tagged * 0.5:
            status = "⚠️ Missing IDs"
        else:
            status = "✅ Good"

        # Get expected purpose
        purpose = CTB_BRANCHES.get(branch, 'Unknown')

        report += f"| **{branch}** | {total} | {tagged} | {untagged} | {missing_id} | {heir_count} | {orbt_count} | {none_count} | {status} |\n"

    report += "\n---\n\n## 📋 Branch Analysis\n\n"

    # Detailed branch analysis
    for branch, data in sorted_branches[:10]:  # Top 10 branches
        total = data['total']
        tagged = data['tagged']
        purpose = CTB_BRANCHES.get(branch, 'Unknown purpose')

        coverage_pct = (tagged / max(1, total)) * 100

        report += f"### {branch}\n\n"
        report += f"**Purpose**: {purpose}\n\n"
        report += f"- Total Files: {total}\n"
        report += f"- Tagged: {tagged} ({coverage_pct:.1f}%)\n"
        report += f"- Untagged: {data['untagged']}\n"
        report += f"- Missing Barton ID: {data['missing_barton_id']}\n"

        # File types
        if data['file_types']:
            top_types = sorted(data['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
            report += f"- Top File Types: {', '.join([f'{ext}({count})' for ext, count in top_types])}\n"

        # Recommendations
        report += "\n**Recommendations**:\n"
        if data['untagged'] > 0:
            report += f"- ⚠️ Tag {data['untagged']} remaining files\n"
        if data['missing_barton_id'] > 0:
            report += f"- ⚠️ Assign valid Barton IDs to {data['missing_barton_id']} files\n"
        if coverage_pct >= 90:
            report += "- ✅ Excellent coverage - maintain compliance\n"

        report += "\n"

    report += "---\n\n## ⚠️ Issues & Gaps\n\n"

    issues = []

    # Identify issues
    if stats['missing_barton_id'] > 0:
        issues.append(f"### Missing or Invalid Barton IDs\n\n{stats['missing_barton_id']} files have missing or placeholder Barton IDs (00.00.00). These need to be assigned proper doctrine identifiers.\n")

    if stats['missing_unique_id'] > 0:
        issues.append(f"### Missing Unique IDs\n\n{stats['missing_unique_id']} files are missing Unique IDs. These should be auto-generated hash-based identifiers.\n")

    if stats['has_blueprint_hash'] == 0:
        issues.append(f"### No Blueprint Coverage\n\n0 files have Blueprint Hashes assigned. Blueprint coverage helps track architectural relationships and dependencies.\n")

    if stats['untagged_files'] > 100:
        issues.append(f"### High Number of Untagged Files\n\n{stats['untagged_files']} files remain untagged. Consider running the tagger on additional directories or file types.\n")

    # Empty or underutilized branches
    empty_branches = [branch for branch, data in stats['branch_stats'].items() if data['total'] < 3]
    if empty_branches:
        issues.append(f"### Underutilized CTB Branches\n\nThe following branches have fewer than 3 files:\n\n" +
                     "\n".join([f"- `{branch}`: {stats['branch_stats'][branch]['total']} files" for branch in empty_branches]))

    if issues:
        report += "\n".join(issues)
    else:
        report += "✅ No critical issues detected.\n"

    report += "\n---\n\n## ✅ Recommendations\n\n"

    recommendations = []

    # Coverage recommendations
    if score_breakdown['metadata_coverage'] < 24:
        recommendations.append("### Improve Metadata Coverage\n\n- Run `ctb_metadata_tagger.py` on untagged directories\n- Focus on high-value source files in `ctb/ui/apps/` and `ctb/ui/src/`\n- Target: 90%+ coverage of source files\n")

    # Barton ID recommendations
    if score_breakdown['barton_id_complete'] < 16:
        recommendations.append("### Fix Barton ID Assignments\n\n- Review tagger script logic for path-based ID assignment\n- Manually assign IDs to files with 00.00.00\n- Ensure IDs match CTB branch structure\n")

    # Enforcement recommendations
    if score_breakdown['enforcement_classified'] < 16:
        recommendations.append("### Classify Enforcement Types\n\n- Review files with `Enforcement: None`\n- Assign HEIR to validators, agents, tests\n- Assign ORBT to migrations, schemas, APIs\n- Update tagger heuristics for better automatic classification\n")

    # Blueprint recommendations
    if score_breakdown['blueprint_coverage'] < 9:
        recommendations.append("### Add Blueprint Coverage\n\n- Identify architectural blueprints\n- Generate hash-based blueprint identifiers\n- Link related files via Blueprint Hash field\n- Create blueprint registry in `ctb/docs/`\n")

    # Branch organization recommendations
    if score_breakdown['branch_organization'] < 12:
        recommendations.append("### Improve Branch Organization\n\n- Move files from root branches to sub-branches\n- Create additional sub-branches for better categorization\n- Follow CTB doctrine branch structure strictly\n")

    # Testing recommendations
    test_files = sum(1 for f in stats['files'] if 'test' in f['path'].lower())
    if test_files < 50:
        recommendations.append(f"### Add More Tests\n\nOnly {test_files} test files detected. Recommended:\n\n- Add unit tests to `ctb/sys/tests/`\n- Add integration tests to `ctb/ai/testing/`\n- Target: 1 test file per 5 source files\n")

    # GitHub Actions recommendations
    gh_actions = sum(1 for f in stats['files'] if '.github' in f['path'].lower())
    if gh_actions == 0:
        recommendations.append("### Set Up CI/CD\n\n- Add GitHub Actions workflows to `ctb/sys/github-factory/.github/workflows/`\n- Implement automated CTB compliance checks\n- Add pre-commit hooks for metadata validation\n")

    if recommendations:
        report += "\n".join(recommendations)
    else:
        report += "✅ No immediate recommendations - repository is well-maintained.\n"

    report += "\n---\n\n## 📝 Action Items\n\n"

    # Generate action checklist
    report += "### High Priority\n\n"
    if stats['missing_barton_id'] > 50:
        report += f"- [ ] Fix {stats['missing_barton_id']} files with missing/invalid Barton IDs\n"
    if stats['untagged_files'] > 100:
        report += f"- [ ] Tag {stats['untagged_files']} remaining untagged files\n"
    if gh_actions == 0:
        report += "- [ ] Set up GitHub Actions for automated compliance\n"

    report += "\n### Medium Priority\n\n"
    if stats['has_blueprint_hash'] < 50:
        report += "- [ ] Add Blueprint Hash coverage to key architectural files\n"
    if stats['missing_enforcement'] > 100:
        report += f"- [ ] Classify {stats['missing_enforcement']} files with missing enforcement types\n"
    if test_files < 50:
        report += "- [ ] Increase test coverage to 50+ test files\n"

    report += "\n### Low Priority\n\n"
    report += "- [ ] Create blueprint registry documentation\n"
    report += "- [ ] Add git integration to tagger for automatic Last Updated\n"
    report += "- [ ] Generate metadata index for fast searching\n"
    if empty_branches:
        report += f"- [ ] Review and populate {len(empty_branches)} underutilized branches\n"

    report += "\n---\n\n## 🔄 Next Audit\n\n"
    report += "**Recommended Frequency**: Weekly during active development, Monthly during maintenance\n\n"
    report += "**Re-run Command**:\n"
    report += "```bash\n"
    report += "python ctb/sys/github-factory/scripts/ctb_audit_generator.py ctb/\n"
    report += "```\n\n"

    report += "**Target Next Audit**:\n"
    report += f"- Current Score: {total_score}/100\n"
    next_target = min(100, total_score + 10)
    report += f"- Target Score: {next_target}/100\n"
    report += "- Focus Areas: " + ", ".join([
        cat for cat, score in score_breakdown.items()
        if score < (30 if 'coverage' in cat else 20 if 'complete' in cat or 'classified' in cat else 15)
    ][:3]) + "\n"

    report += "\n---\n\n"
    report += f"**Report Generated**: {now}\n"
    report += f"**Tool**: ctb_audit_generator.py\n"
    report += f"**Version**: 1.0\n"
    report += f"**CTB Compliance**: {grade}\n"

    return report


def main():
    """Main entry point."""
    import argparse
    import sys

    # Force UTF-8 encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description='Generate CTB audit report')
    parser.add_argument('directory', help='CTB directory to audit')
    parser.add_argument('--output', '-o', help='Output file path', default='CTB_AUDIT_REPORT.md')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    ctb_root = Path(args.directory).resolve()
    if not ctb_root.exists():
        print(f"[X] Directory not found: {ctb_root}")
        return 1

    print("CTB Audit Report Generator")
    print(f"Directory: {ctb_root}")
    print()
    print("Scanning repository...")

    # Run audit
    stats = audit_repository(ctb_root)

    print(f"Scanned: {stats['total_files']:,} files")
    print(f"Tagged: {stats['tagged_files']:,} files")
    print()
    print("Generating report...")

    # Generate report
    report = generate_report(stats, ctb_root)

    # Write to file
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ctb_root.parent / output_path

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print()
    print(f"[OK] Report generated: {output_path}")

    # Calculate and display score
    total_score, score_breakdown = calculate_compliance_score(stats)

    print()
    print("=" * 50)
    print("CTB COMPLIANCE SCORE")
    print("=" * 50)
    print(f"Overall: {total_score}/100")
    print()
    for category, score in score_breakdown.items():
        max_score = 30 if 'coverage' in category else 20 if 'complete' in category or 'classified' in category else 15
        pct = (score / max_score) * 100
        print(f"  {category}: {score}/{max_score} ({pct:.0f}%)")
    print("=" * 50)

    if total_score >= 90:
        print("[EXCELLENT] Repository is highly compliant with CTB doctrine")
    elif total_score >= 75:
        print("[GOOD] Repository meets CTB standards with minor improvements needed")
    elif total_score >= 60:
        print("[FAIR] Repository needs moderate improvements for full compliance")
    else:
        print("[NEEDS WORK] Repository requires significant improvements")

    return 0


if __name__ == '__main__':
    exit(main())
