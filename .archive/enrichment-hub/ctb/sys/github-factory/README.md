# GitHub Factory

The GitHub Factory handles all GitHub-related operations and integrations.

## Purpose

The GitHub Factory manages:
- Repository operations
- Branch management
- Pull request automation
- GitHub Actions workflows
- Issue management
- Secrets synchronization

## Configuration

Configuration is in `github.config.json` in this directory.

## Operations

### Repository Management
- Create/update repositories
- Manage repository settings
- Configure branch protection
- Set up webhooks

### Branch Operations
- Protected branches: `main`, `master`
- Development branch: `develop`
- Feature branch conventions
- Auto-merge policies

### Pull Request Automation
- Auto-label PRs
- Run compliance checks
- Request reviews
- Auto-merge when approved

### GitHub Actions
- CI/CD workflows
- Automated testing
- Deployment pipelines
- Compliance checks

### Issue Management
- Auto-create issues for compliance failures
- Label management
- Issue templates
- Project board integration

## Workflows

### CI/CD Pipeline
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  - lint
  - test
  - build
  - deploy (production only)
```

### Compliance Check
Runs on every PR:
1. Check CTB structure
2. Validate file tags
3. Run doctrine enforcement
4. Generate compliance report

## Authentication

Authentication via:
- **Personal Access Token**: `GITHUB_TOKEN` environment variable
- **Permissions Required**: repo, workflow, read:org

## Integration

Integrates with:
- **Global Factory**: For compliance orchestration
- **Composio MCP**: For workflow automation
- **Logging System**: For audit trails

## Best Practices

1. Use branch protection on main/master
2. Require PR reviews before merge
3. Run automated tests on all PRs
4. Keep workflows simple and maintainable
5. Secure secrets properly
6. Document workflow changes
