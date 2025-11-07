# Barton Outreach Core - Diagrams

This directory contains all architectural and system diagrams for the project.

## 📁 Structure

```
diagrams/
├── eraser/             # Eraser.io diagram-as-code files
│   ├── *.eraser       # Source diagram files
│   ├── exports/       # Exported SVG/PNG files
│   └── README.md
└── README.md          # This file
```

## 🎨 Diagram Tools

### Eraser.io (Primary)
- **Format**: `.eraser` (diagram-as-code)
- **Location**: `diagrams/eraser/`
- **Exports**: SVG, PNG, PDF
- **Version Control**: Git-tracked source files
- **Doctrine ID**: 04.04.15

### ChartDB (Database Schemas)
- **Format**: JSON + Visual Editor
- **Location**: Root `/chartdb/`
- **Purpose**: Database ER diagrams
- **Doctrine ID**: 04.04.07

### Grafana (Dashboards)
- **Format**: JSON
- **Location**: `/grafana/dashboards/`
- **Purpose**: Metrics visualization
- **Doctrine ID**: 04.04.11

## 🚀 Quick Start

### Using Eraser.io

1. **Create Diagram**
   ```bash
   # Visit https://app.eraser.io
   # Create new diagram
   # Save as: diagrams/eraser/your-diagram.eraser
   ```

2. **Edit Locally**
   ```bash
   # Open .eraser file in text editor
   # Eraser uses simple diagram-as-code syntax
   # Commit changes to Git
   ```

3. **Export**
   ```bash
   # Export from Eraser.io UI
   # Save to: diagrams/eraser/exports/
   # Formats: SVG (preferred), PNG, PDF
   ```

## 📊 Diagram Types

### Architecture Diagrams
- **Purpose**: System architecture, component relationships
- **Format**: Eraser.io
- **Examples**: `system-architecture.eraser`, `ctb-structure.eraser`

### Sequence Diagrams
- **Purpose**: Process flows, API interactions
- **Format**: Eraser.io
- **Examples**: `outreach-flow.eraser`, `mcp-integration.eraser`

### Database ER Diagrams
- **Purpose**: Database schema visualization
- **Format**: ChartDB
- **Location**: `/chartdb_schemas/`

### Monitoring Dashboards
- **Purpose**: Metrics and KPIs
- **Format**: Grafana
- **Location**: `/grafana/dashboards/`

## 🔄 Workflow

### Creating New Diagram

1. **Choose Tool**
   - Architecture/Flow → Eraser.io
   - Database Schema → ChartDB
   - Metrics Dashboard → Grafana

2. **Create in Tool**
   - Use tool's UI/editor
   - Follow naming convention: `component-type.eraser`

3. **Save to Repo**
   ```bash
   # Add source file
   git add diagrams/eraser/my-diagram.eraser

   # Export visual
   # Save to exports/
   git add diagrams/eraser/exports/my-diagram.svg

   # Commit
   git commit -m "docs: add my-diagram architecture diagram"
   ```

4. **Link in Documentation**
   ```markdown
   ![My Diagram](./diagrams/eraser/exports/my-diagram.svg)
   ```

### Updating Existing Diagram

1. **Edit Source**
   - Eraser.io: Edit `.eraser` file or use web editor
   - ChartDB: Use visual editor
   - Grafana: Edit dashboard JSON or UI

2. **Re-export**
   - Export updated visual files
   - Overwrite in `exports/`

3. **Commit Changes**
   ```bash
   git add diagrams/eraser/my-diagram.eraser
   git add diagrams/eraser/exports/my-diagram.svg
   git commit -m "docs: update my-diagram with new components"
   ```

## 🎯 Naming Conventions

### File Names
- Use kebab-case: `system-architecture.eraser`
- Descriptive names: `outreach-pipeline-flow.eraser`
- Version if needed: `api-v2-architecture.eraser`

### Export Files
- Match source name: `system-architecture.svg`
- Include format: `.svg`, `.png`, `.pdf`
- Store in `exports/` subdirectory

## 🔗 Integration

### Eraser.io GitHub Integration
```bash
# Link Eraser.io workspace to GitHub repo
# Enable auto-export on save
# Configure export path: diagrams/eraser/exports/
```

### Markdown Embedding
```markdown
# Architecture Overview

![System Architecture](./diagrams/eraser/exports/system-architecture.svg)

See source: [system-architecture.eraser](./diagrams/eraser/system-architecture.eraser)
```

### Obsidian Linking
```markdown
![[../diagrams/eraser/exports/system-architecture.svg]]
```

## 📚 Diagram Catalog

### System Architecture
- **File**: `eraser/system-architecture.eraser`
- **Description**: Overall system architecture
- **Components**: MCP servers, databases, integrations
- **Status**: Active

### CTB Structure
- **File**: `eraser/ctb-structure.eraser`
- **Description**: CTB altitude-based organization
- **Layers**: 40k/20k/10k/5k/Ground
- **Status**: Active

### Outreach Pipeline
- **File**: `eraser/outreach-pipeline.eraser`
- **Description**: Lead processing pipeline
- **Flow**: Ingest → Enrich → Validate → Outreach
- **Status**: Planned

### Database Schema
- **File**: `../chartdb/neon-marketing-schema.json`
- **Description**: Marketing database ER diagram
- **Tables**: company_master, people_master, slots
- **Status**: Active

## 🛠️ Tools & Resources

### Eraser.io
- Website: https://app.eraser.io
- Docs: https://docs.eraser.io
- Syntax: https://docs.eraser.io/docs/diagram-as-code

### ChartDB
- Location: `/chartdb/`
- Docs: Internal README

### Grafana
- Location: `/grafana/`
- Dashboard: http://localhost:3000

---

**Created:** 2025-11-06
**CTB Branch:** sys/eraser
**Doctrine ID:** 04.04.15
