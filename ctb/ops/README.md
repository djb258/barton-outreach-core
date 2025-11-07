# CTB Operations Branch

**Altitude**: 5k ft (Operations Layer)
**Purpose**: Operational tooling, automation scripts, CI/CD, and deployment management

## Overview

The `ops/` branch contains all operational tools, deployment configurations, automation scripts, and CI/CD pipelines. This is the lowest altitude in the CTB hierarchy, focused on day-to-day operations and deployment management.

## Directory Structure

```
ops/
├── docker/           # Docker configurations and compose files
├── scripts/          # Automation and operational scripts
├── ci-cd/           # CI/CD pipeline configurations
└── README.md        # This file
```

## Subdirectories

### docker/

Container configurations and Docker Compose setups for local development and deployment.

**Contents:**
- `docker-compose.yml` - Multi-container orchestration
- `Dockerfile.*` - Service-specific images
- `.dockerignore` - Docker build exclusions
- Container startup scripts

### scripts/

Operational automation scripts for maintenance, deployment, and monitoring.

**Contents:**
- Deployment automation
- Database backup scripts
- Log rotation and cleanup
- Health check scripts
- Migration helpers

### ci-cd/

CI/CD pipeline configurations for GitHub Actions, GitLab CI, or other platforms.

**Contents:**
- GitHub Actions workflows
- Build scripts
- Test automation
- Deployment pipelines
- Release management

## Usage Patterns

### Local Development

```bash
# Start all services with Docker
cd ctb/ops/docker
docker-compose up -d

# Run operational scripts
cd ctb/ops/scripts
bash backup-database.sh
```

### CI/CD Integration

```yaml
# Example GitHub Action using ops/ resources
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run deployment script
        run: bash ctb/ops/scripts/deploy-production.sh
```

### Automation Scripts

Place all operational automation in `scripts/`:
- Scheduled jobs
- Maintenance tasks
- Reporting automation
- Monitoring scripts

## Best Practices

1. **Keep scripts idempotent** - Safe to run multiple times
2. **Add logging** - All operations should log activity
3. **Use environment variables** - No hardcoded values
4. **Document dependencies** - List required tools/services
5. **Test in staging first** - Never test in production

## Integration with CTB

The ops/ branch integrates with:
- **ctb/sys/** - Uses system infrastructure
- **ctb/ai/** - Deploys AI services
- **ctb/data/** - Manages database operations
- **ctb/ui/** - Builds and deploys UI
- **ctb/meta/** - Follows CTB configuration

## Common Operations

### Deployment

```bash
# Deploy to staging
bash ctb/ops/scripts/deploy-staging.sh

# Deploy to production (requires approval)
bash ctb/ops/scripts/deploy-production.sh
```

### Monitoring

```bash
# Check service health
bash ctb/ops/scripts/health-check.sh

# View logs
bash ctb/ops/scripts/view-logs.sh
```

### Maintenance

```bash
# Database backup
bash ctb/ops/scripts/backup-database.sh

# Clean old logs
bash ctb/ops/scripts/cleanup-logs.sh
```

## Status

**Status**: Initialized
**Docker Configs**: 0
**Automation Scripts**: 0
**CI/CD Pipelines**: 0

---

For more information, see [CTB_DOCTRINE.md](../meta/global-config/CTB_DOCTRINE.md)
