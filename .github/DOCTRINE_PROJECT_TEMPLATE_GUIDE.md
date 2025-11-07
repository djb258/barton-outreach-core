# Doctrine Pipeline Project Template — Setup Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-07
**Template File**: `.github/doctrine_project_template.json`

---

## 📋 Overview

The **Doctrine Pipeline** project template defines a complete GitHub Projects board structure for tracking SVG-PLE doctrine work across all layers:

- 🧭 **Doctrine** — Concept and design stage
- 🧱 **Schema** — Database schema and SQL migrations
- ⚙️ **Enrichment** — Data enrichment agent integration
- 📊 **Grafana** — Dashboard and analytics tasks
- 🤖 **Agents** — Automation workflows (n8n, Composio MCP)
- ✅ **Done** — Completed and deployed items

This template integrates seamlessly with the **doctrine-project-sync.yml** GitHub Action workflow.

---

## 🎯 What This Template Provides

### **1. Six Workflow Columns**

| Column | Purpose | Auto-Label | Auto-Close |
|--------|---------|------------|------------|
| 🧭 Doctrine | Concept and design stage | `doctrine` | No |
| 🧱 Schema | SQL schema work in progress | `schema` | No |
| ⚙️ Enrichment | Agent integration (Apify, Abacus, Firecrawl) | `enrichment` | No |
| 📊 Grafana | Dashboard and analytics tasks | `grafana` | No |
| 🤖 Agents | Automation and n8n/Composio flows | `agent` | No |
| ✅ Done | Completed, merged, or deployed | — | Yes |

### **2. Six Color-Coded Labels**

| Label | Color | Hex | Description |
|-------|-------|-----|-------------|
| 🔵 doctrine | Blue | `#1F77B4` | Doctrine or markdown change |
| 🟢 schema | Green | `#2CA02C` | Schema / SQL migration work |
| 🟠 enrichment | Orange | `#FF7F0E` | Data enrichment agents |
| 🟣 grafana | Purple | `#9467BD` | Visualization or dashboard tasks |
| 🔷 agent | Cyan | `#17BECF` | Automation agents / MCP / n8n |
| 🟡 auto-sync | Yellow | `#BCBD22` | Auto-created by doctrine sync workflow |

### **3. Six Automation Rules**

1. **label_added:doctrine** → Move to "🧭 Doctrine" column
2. **label_added:schema** → Move to "🧱 Schema" column
3. **label_added:enrichment** → Move to "⚙️ Enrichment" column
4. **label_added:grafana** → Move to "📊 Grafana" column
5. **label_added:agent** → Move to "🤖 Agents" column
6. **issue_closed** → Move to "✅ Done" column

---

## 🚀 Setup Instructions

### **Option A: Create Project from GitHub UI** (Recommended)

**Step 1: Navigate to Projects**
```
1. Go to your organization: https://github.com/your-org
2. Click "Projects" tab → "New project"
3. Select "New project" → Choose "Board" view
```

**Step 2: Name Your Project**
```
Name: Doctrine Pipeline
Description: Automated doctrine workflow board for SVG-PLE — tracks BIT, Talent Flow, and PLE updates end-to-end.
```

**Step 3: Create Columns Manually**

Create these 6 columns in order:

1. **🧭 Doctrine**
   - Description: "Concept and design stage"

2. **🧱 Schema**
   - Description: "Schema + SQL work in progress"

3. **⚙️ Enrichment**
   - Description: "Agent integration (Apify, Abacus, Firecrawl)"

4. **📊 Grafana**
   - Description: "Dashboard + analytics tasks"

5. **🤖 Agents**
   - Description: "Automation and n8n/Composio flows"

6. **✅ Done**
   - Description: "Completed, merged, or deployed doctrine items"

**Step 4: Create Labels in Repository**

Go to repository Settings → Labels → New label:

```
1. doctrine     | #1F77B4 | Doctrine or markdown change
2. schema       | #2CA02C | Schema / SQL migration work
3. enrichment   | #FF7F0E | Data enrichment agents
4. grafana      | #9467BD | Visualization or dashboard tasks
5. agent        | #17BECF | Automation agents / MCP / n8n
6. auto-sync    | #BCBD22 | Auto-created by doctrine sync workflow
```

**Step 5: Configure Workflow Integration**

Update `.github/workflows/doctrine-project-sync.yml` line 176:

```yaml
# For organization project:
project-url: https://github.com/orgs/YOUR-ORG/projects/PROJECT-NUMBER

# For repository project:
project-url: https://github.com/YOUR-ORG/YOUR-REPO/projects/PROJECT-NUMBER
```

**Find Project Number**:
- Go to your project board
- Look at URL: `https://github.com/orgs/YOUR-ORG/projects/5`
- Project number is `5`

---

### **Option B: Use GitHub CLI** (Advanced)

**Step 1: Install GitHub CLI**
```bash
# Windows (via Chocolatey)
choco install gh

# Mac (via Homebrew)
brew install gh

# Verify installation
gh --version
```

**Step 2: Authenticate**
```bash
gh auth login
```

**Step 3: Create Project**
```bash
# For organization project
gh project create \
  --org "YOUR-ORG" \
  --title "Doctrine Pipeline" \
  --format "board"

# For repository project
gh project create \
  --owner "YOUR-ORG" \
  --repo "barton-outreach-core" \
  --title "Doctrine Pipeline" \
  --format "board"
```

**Step 4: Get Project Number**
```bash
# List all projects
gh project list --org "YOUR-ORG"

# Note the project number (e.g., 5)
```

**Step 5: Create Labels**
```bash
# Navigate to repository
cd barton-outreach-core

# Create labels
gh label create "doctrine" --color "1F77B4" --description "Doctrine or markdown change"
gh label create "schema" --color "2CA02C" --description "Schema / SQL migration work"
gh label create "enrichment" --color "FF7F0E" --description "Data enrichment agents"
gh label create "grafana" --color "9467BD" --description "Visualization or dashboard tasks"
gh label create "agent" --color "17BECF" --description "Automation agents / MCP / n8n"
gh label create "auto-sync" --color "BCBD22" --description "Auto-created by doctrine sync workflow"
```

---

### **Option C: Import Template via API** (Experimental)

**Note**: GitHub Projects v2 API does not currently support importing full templates. This option is reserved for future GitHub API updates.

---

## ✅ Verification Checklist

### **Project Board Setup**

- [ ] Project board created: "Doctrine Pipeline"
- [ ] 6 columns exist in correct order
- [ ] Column descriptions are set
- [ ] Project visibility is "Private"

### **Labels Setup**

- [ ] 6 labels created in repository
- [ ] Label colors match template (Blue, Green, Orange, Purple, Cyan, Yellow)
- [ ] Label descriptions are set
- [ ] Labels visible in repository → Labels section

### **Workflow Integration**

- [ ] `.github/workflows/doctrine-project-sync.yml` exists
- [ ] Workflow `project-url` points to correct project number
- [ ] Workflow has `issues: write` and `projects: write` permissions
- [ ] Workflow triggers on `doctrine/**/*` file changes

### **Test the Integration**

- [ ] Make small change to any doctrine file
- [ ] Commit and push to main branch
- [ ] Workflow runs successfully (check Actions tab)
- [ ] Issue created with correct labels
- [ ] Issue appears in "Doctrine Pipeline" project board

---

## 📊 Workflow Integration Example

### **Scenario: Update BIT Doctrine**

**Step 1: Edit Doctrine in Obsidian**
```bash
# Edit doctrine/ple/BIT-Doctrine.md
# Obsidian Git auto-commits changes every 10 minutes
```

**Step 2: Workflow Triggers**
```yaml
# doctrine-project-sync.yml detects change in doctrine/ple/BIT-Doctrine.md
# Creates issue: "Doctrine Update #42 – 1 file(s) changed"
# Labels: doctrine, auto-sync, documentation
```

**Step 3: Issue Auto-Routed**
```
Issue has label "doctrine"
→ Automation rule: label_added:doctrine
→ Move card to "🧭 Doctrine" column
```

**Step 4: Team Workflow**
```
1. Developer reviews changes in "🧭 Doctrine" column
2. Add label "schema" when SQL work begins
   → Card automatically moves to "🧱 Schema" column
3. Add label "grafana" when creating dashboard
   → Card automatically moves to "📊 Grafana" column
4. Close issue when complete
   → Card automatically moves to "✅ Done" column
```

---

## 🧭 Label-Based Routing Logic

```
┌─────────────────────────────────────────────────────────────┐
│  Issue Created                                               │
│  Labels: doctrine, auto-sync, documentation                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Automation: label_added:doctrine                           │
│  → Move to "🧭 Doctrine" column                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (Developer adds "schema" label)
┌─────────────────────────────────────────────────────────────┐
│  Automation: label_added:schema                             │
│  → Move to "🧱 Schema" column                               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (Developer adds "enrichment" label)
┌─────────────────────────────────────────────────────────────┐
│  Automation: label_added:enrichment                         │
│  → Move to "⚙️ Enrichment" column                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (Developer closes issue)
┌─────────────────────────────────────────────────────────────┐
│  Automation: issue_closed                                   │
│  → Move to "✅ Done" column                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Customization Options

### **Add Custom Columns**

Edit `.github/doctrine_project_template.json`:

```json
{
  "name": "🧪 Testing",
  "purpose": "QA and validation tasks",
  "auto_add_labels": ["testing"]
}
```

Add corresponding automation rule:

```json
{
  "trigger": "label_added:testing",
  "action": "move_card",
  "destination_column": "🧪 Testing"
}
```

### **Add Custom Labels**

```json
{
  "name": "urgent",
  "color": "#D73A4A",
  "description": "High priority doctrine work"
}
```

### **Change Visibility**

```json
"visibility": "public"  // Make project board public
```

---

## 🔄 Integration with Existing Tools

### **Obsidian Dashboard**

The project board integrates with `doctrine/DOCTRINE_DASHBOARD.md`:

```markdown
## 🎯 GitHub Project Board

[View Doctrine Pipeline](https://github.com/orgs/YOUR-ORG/projects/PROJECT-NUMBER)

**Current Tasks**:
- 🧭 Doctrine: 3 items
- 🧱 Schema: 2 items
- ⚙️ Enrichment: 1 item
- ✅ Done: 15 items
```

### **GitKraken**

- View project board issues linked to commits
- Drag commits to create new issues
- Visual commit history with issue references

### **Grafana**

Track doctrine pipeline metrics:

```sql
-- Query: Count issues by column
SELECT
  column_name,
  COUNT(*) as issue_count
FROM github_project_cards
WHERE project_name = 'Doctrine Pipeline'
GROUP BY column_name;
```

---

## 🐛 Troubleshooting

### **Issue: Automation Rules Not Working**

**Symptoms**: Labels added but cards don't move

**Solutions**:
1. Verify project board has automation enabled
2. Check label names match exactly (case-sensitive)
3. Ensure workflow has `projects: write` permission
4. Manually add one card to test automation

### **Issue: Workflow Not Creating Issues**

**Symptoms**: Doctrine changes pushed but no issue created

**Solutions**:
1. Check workflow file path: `.github/workflows/doctrine-project-sync.yml`
2. Verify workflow triggers on correct branch
3. Check Actions tab for workflow errors
4. Review `.github/workflows/DOCTRINE_PIPELINE_SETUP.md` troubleshooting section

### **Issue: Labels Missing from Repository**

**Symptoms**: Workflow fails with "label not found" error

**Solutions**:
1. Create missing labels in repository Settings → Labels
2. Use exact colors from template
3. Verify label descriptions are set
4. Re-run workflow after creating labels

---

## 📚 Related Documentation

### **Workflow Files**
- **Workflow**: `.github/workflows/doctrine-project-sync.yml`
- **Setup Guide**: `.github/workflows/DOCTRINE_PIPELINE_SETUP.md`
- **Template**: `.github/doctrine_project_template.json` (this file)

### **Doctrine Documentation**
- **Dashboard**: `doctrine/DOCTRINE_DASHBOARD.md`
- **Index**: `doctrine/README.md`
- **Master Doctrine**: `doctrine/ple/PLE-Doctrine.md`

### **Obsidian Integration**
- **Plugin Setup**: `.obsidian/plugins-setup.md`
- **Git Sync**: Configured to auto-commit every 10 minutes
- **Dataview**: Auto-lists open doctrine tasks

---

## 🎯 Success Metrics

### **Project Board Health Indicators**

| Metric | Target | Status |
|--------|--------|--------|
| Auto-sync success rate | 95%+ | ✅ |
| Average time in "🧭 Doctrine" | < 3 days | 🟡 |
| Average time in "🧱 Schema" | < 5 days | 🟡 |
| Cards in "✅ Done" per month | 10+ | ✅ |

### **Workflow Metrics**

- **Doctrine changes per week**: 5-10 (typical)
- **Issue creation latency**: < 2 minutes (workflow runtime)
- **Label-based routing accuracy**: 100% (automated)

---

## 🆘 Support

### **Questions**

- **Project Setup**: Review this guide (`.github/DOCTRINE_PROJECT_TEMPLATE_GUIDE.md`)
- **Workflow Issues**: Review `.github/workflows/DOCTRINE_PIPELINE_SETUP.md`
- **Doctrine Changes**: Review `doctrine/DOCTRINE_DASHBOARD.md`

### **Escalation**

- **Workflow Failures**: Open issue with label `workflow-bug`
- **Project Board Setup**: Review GitHub Projects documentation
- **Template Issues**: Edit `.github/doctrine_project_template.json`

---

**Last Updated**: 2025-11-07
**Maintained By**: Barton Outreach Team
**Template Version**: 1.0.0
**Status**: Production Ready ✅
