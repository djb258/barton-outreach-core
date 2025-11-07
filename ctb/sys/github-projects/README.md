# GitHub Projects Integration

GitHub Projects v2 integration for managing sprints, tracking features, and visualizing project progress.

## 🚀 Quick Start

### 1. Create GitHub Project
```bash
# Via GitHub UI
1. Go to repository on GitHub
2. Click "Projects" tab
3. Click "New project"
4. Select "Board" or "Table" view
5. Name: "Barton Outreach Core"

# Via GraphQL API
curl -X POST https://api.github.com/graphql \
  -H "Authorization: bearer $GITHUB_TOKEN" \
  -d '{
    "query": "mutation { createProject(input: {ownerId: \"...\", name: \"Barton Outreach Core\"}) { project { id } } }"
  }'
```

### 2. Configure Environment
```bash
# Add to .env
GITHUB_TOKEN=your_github_token_here
GITHUB_PROJECT_ID=your_project_id_here
GITHUB_REPO_OWNER=djb258
GITHUB_REPO_NAME=barton-outreach-core
```

### 3. Set Up Automation
See `automation-rules.json` for GitHub Actions workflows that auto-manage project items.

## 📊 Project Structure

### Views

#### 1. Sprint Board (Kanban)
**Columns:**
- 📋 Backlog
- 🎯 Todo
- 🏃 In Progress
- 👀 In Review
- ✅ Done

**Filters:**
- Sprint: Current
- Status: Open

#### 2. Feature Roadmap (Table)
**Fields:**
- Title
- Status
- Priority
- Estimate
- Sprint
- Assignee
- Labels

**Sort:**
- Priority (High → Low)
- Sprint (Current → Future)

#### 3. Bug Triage (Board)
**Columns:**
- 🐛 New Bugs
- 🔍 Investigating
- 🔧 Fixing
- ✅ Resolved

**Filters:**
- Label: bug
- Status: Open

### Custom Fields

```json
{
  "fields": [
    {
      "name": "Priority",
      "type": "single_select",
      "options": ["🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"]
    },
    {
      "name": "Sprint",
      "type": "iteration",
      "duration": 2,
      "start_day": "Monday"
    },
    {
      "name": "Estimate",
      "type": "number"
    },
    {
      "name": "Component",
      "type": "single_select",
      "options": ["MCP", "Database", "Frontend", "Integration", "Documentation"]
    },
    {
      "name": "Doctrine ID",
      "type": "text"
    }
  ]
}
```

## 🤖 Automation Rules

### Auto-Add Issues
```yaml
on:
  issues:
    types: [opened]
jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - name: Add to project
        uses: actions/add-to-project@v0.4.0
        with:
          project-url: https://github.com/users/djb258/projects/1
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Auto-Move on PR
```yaml
on:
  pull_request:
    types: [opened, closed]
jobs:
  update-project:
    runs-on: ubuntu-latest
    steps:
      - name: Move to In Review
        if: github.event.action == 'opened'
        uses: actions/add-to-project@v0.4.0
        with:
          project-url: https://github.com/users/djb258/projects/1
          github-token: ${{ secrets.GITHUB_TOKEN }}
          column-name: "In Review"

      - name: Move to Done
        if: github.event.pull_request.merged == true
        uses: actions/add-to-project@v0.4.0
        with:
          project-url: https://github.com/users/djb258/projects/1
          github-token: ${{ secrets.GITHUB_TOKEN }}
          column-name: "Done"
```

### Auto-Archive Completed
```yaml
on:
  schedule:
    - cron: "0 0 * * 0"  # Weekly on Sunday
jobs:
  archive-completed:
    runs-on: ubuntu-latest
    steps:
      - name: Archive items
        run: |
          # GraphQL query to archive items
          # older than 30 days in Done column
```

## 🛠️ Project Templates

### Feature Roadmap Template
```markdown
## Feature: [Feature Name]

### Description
[Brief description of the feature]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Technical Notes
- Component: [MCP/Database/Frontend/etc]
- Doctrine ID: [04.XX.XX]
- Estimate: [Points]

### Related
- Issues: #123, #456
- PRs: #789
- Docs: [Link to documentation]
```

### Bug Report Template
```markdown
## Bug: [Bug Title]

### Description
[What's the bug?]

### Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- Component: [Which system]
- Version: [Version/commit]
- Error Log: [Link to shq_error_log entry]

### Priority
[Critical/High/Medium/Low]
```

### Sprint Planning Template
```markdown
## Sprint [Number]: [Dates]

### Goals
- Goal 1
- Goal 2
- Goal 3

### Capacity
- Team Size: X developers
- Available Days: Y days
- Velocity: Z points

### Planned Items
1. [Feature 1] - X points
2. [Feature 2] - Y points
3. [Bug fixes] - Z points

Total: XX points

### Dependencies
- [ ] Dependency 1
- [ ] Dependency 2

### Risks
- Risk 1
- Risk 2
```

## 📈 Project Insights

### Metrics to Track
- Velocity (points per sprint)
- Cycle time (time in progress)
- Lead time (time from todo to done)
- Bug resolution time
- Feature completion rate

### GraphQL Queries

#### Get Project Items
```graphql
query {
  node(id: "PROJECT_ID") {
    ... on ProjectV2 {
      items(first: 100) {
        nodes {
          id
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldTextValue {
                text
                field {
                  ... on ProjectV2Field {
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

#### Update Item Field
```graphql
mutation {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PROJECT_ID"
      itemId: "ITEM_ID"
      fieldId: "FIELD_ID"
      value: {
        singleSelectOptionId: "OPTION_ID"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}
```

## 🔗 Integration with MCP

### Via Composio GitHub Toolkit
```javascript
// Add issue to project
const result = await composio.execute({
  tool: "GITHUB_ADD_PROJECT_ITEM",
  data: {
    project_id: process.env.GITHUB_PROJECT_ID,
    content_id: issue.node_id,
    content_type: "Issue"
  }
});

// Update project field
await composio.execute({
  tool: "GITHUB_UPDATE_PROJECT_FIELD",
  data: {
    project_id: process.env.GITHUB_PROJECT_ID,
    item_id: item.id,
    field_id: "priority_field_id",
    value: "High"
  }
});
```

## 🎯 Workflows

### Feature Development
1. Create issue with Feature template
2. Auto-added to Backlog
3. Sprint planning → Move to Todo
4. Developer starts → Move to In Progress
5. PR created → Move to In Review
6. PR merged → Move to Done
7. Weekly archive → Archived after 30 days

### Bug Triage
1. Bug reported → New Bugs column
2. Investigate → Investigating column
3. Fix started → Fixing column
4. PR merged → Resolved column
5. Auto-archive after verification

## 📚 Resources

- **GitHub Projects Docs**: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- **GraphQL API**: https://docs.github.com/en/graphql
- **Actions Integration**: https://github.com/actions/add-to-project

---

**Created:** 2025-11-06
**CTB Branch:** sys/github-projects
**Doctrine ID:** 04.04.14
