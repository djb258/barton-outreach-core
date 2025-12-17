# CTB Meta

This directory contains metadata, registry, and organizational structures for the CTB system.

## HEIR/ORBT System

**HEIR**: Hierarchical Execution & Integration Registry
**ORBT**: Organizational Blueprint Tracking

### HEIR Format
```
HEIR-YYYY-MM-SYSTEM-MODE-VN
```

Example: `HEIR-2025-10-ENRICHA-PROD-V1`

### Process ID Format
```
PRC-SYSTEM-EPOCHTIMESTAMP
```

Example: `PRC-ENRICHA-1729728000000`

### ORBT Layers

#### Layer 1: Infrastructure
Core system services, database, authentication, hosting
- Database setup
- Authentication services
- Hosting infrastructure
- Logging and monitoring

#### Layer 2: Integration
External service connections and APIs
- Firebase integration
- Neon PostgreSQL
- Composio MCP
- GitHub API
- AI providers (Gemini, OpenAI)

#### Layer 3: Application
Business logic and data processing
- Business rules
- Data models
- State management
- Validation
- Workflows

#### Layer 4: Presentation
User interface and user experience
- React components
- Pages and routing
- Styling (Tailwind CSS)
- User interactions

## CTB Registry

The registry (`registry.json`) tracks:
- All CTB components
- Component metadata
- Compliance status
- Version history
- Dependencies

## Files

- `heir-orbt.config.json` - HEIR/ORBT configuration
- `registry.json` - CTB component registry
- `manifest.json` - System manifest
- `tags.json` - File tagging database

## Maintenance

Registry is automatically updated by:
- Global Factory on file changes
- Monthly audit processes
- Compliance checks
- Manual updates (when needed)

## Integration

CTB Meta integrates with:
- **Global Factory**: Registry updates
- **Doctrine Enforcement**: Compliance tracking
- **Logging**: Audit trails
