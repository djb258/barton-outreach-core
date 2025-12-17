# Global Factory

The Global Factory is the central orchestration point for CTB (Component-Task-Blueprint) operations.

## Purpose

The Global Factory:
- Enforces CTB doctrine and standards
- Manages auto-sync operations
- Coordinates compliance checks
- Orchestrates remediation workflows
- Maintains the CTB registry

## Configuration

Configuration is managed through:
- `global-config.yaml` (root level)
- `factory.config.json` (this directory)
- Environment variables

## Doctrine Enforcement

### Settings
- **Auto Sync**: `true`
- **Min Score**: `70`
- **Composio Scenario**: `CTB_Compliance_Cycle`
- **Auto Remediate**: `true`
- **Audit Frequency**: `monthly`

## Operations

### Compliance Checks
Automated compliance checks run on:
- New file creation
- File modifications
- Pull requests
- Monthly audits

### Remediation
When compliance score falls below threshold:
1. Identify non-compliant files
2. Generate remediation plan
3. Auto-remediate if enabled
4. Log remediation actions
5. Re-audit to verify

### Logging
All factory operations are logged to:
- `logs/audit.log`
- `logs/error.log`
- Retention: 90 days

## Integration

The Global Factory integrates with:
- **Composio MCP**: Workflow automation
- **GitHub Factory**: Version control operations
- **CTB Meta**: Registry updates
- **Logging System**: Audit trails

## Maintenance

Monthly audits automatically:
- Check CTB compliance
- Validate file tags
- Update registry
- Generate reports
- Trigger alerts if needed
