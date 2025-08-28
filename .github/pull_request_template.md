# Pull Request: [Node-X] Brief Description

## Summary
<!-- Provide a brief summary of the changes -->

## Node & Altitude
- **Node**: <!-- e.g., node-1-company-db -->
- **Altitude**: <!-- e.g., 30k -->
- **Type**: <!-- feature/bugfix/refactor -->

## Changes
<!-- List the key changes made -->
- [ ] 
- [ ] 
- [ ] 

## ORBT Checklist

## Operate
<!-- How will this be operated in production? -->
- [ ] Logging configured for key operations
- [ ] Metrics/monitoring points identified
- [ ] Health checks implemented
- [ ] Operational runbook updated

## Repair
<!-- How can issues be fixed? -->
- [ ] Error handling implemented
- [ ] Dead letter queue configured
- [ ] Idempotent operations verified
- [ ] Rollback strategy documented

## Build
<!-- Build and deployment considerations -->
- [ ] Schema migrations versioned
- [ ] CI checks pass (ddl-validate, orbt-check, lint)
- [ ] Dependencies documented
- [ ] Environment variables documented

## Train
<!-- Knowledge transfer and documentation -->
- [ ] README updated with new features
- [ ] Code comments added for complex logic
- [ ] Example usage provided
- [ ] Team notified of breaking changes

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Edge cases considered

## Acceptance Criteria
<!-- From the node's README -->
- [ ] Each new company gets a unique company_uid
- [ ] Each company has exactly 3 slots with distinct slot_uids
- [ ] Re-runs do not create duplicate slots
- [ ] No credentials in repository

## Database Changes
- [ ] Schema changes reviewed
- [ ] Migrations tested on dev
- [ ] Rollback script provided
- [ ] Indexes optimized

## Security
- [ ] No hardcoded credentials
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] Access controls reviewed

## Additional Notes
<!-- Any additional context or notes -->

---
**Reviewer Checklist:**
- [ ] Code follows project standards
- [ ] ORBT sections adequately addressed
- [ ] Tests provide sufficient coverage
- [ ] Documentation is clear and complete