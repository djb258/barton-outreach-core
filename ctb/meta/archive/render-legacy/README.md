<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/archive
Barton ID: 06.01.05
Unique ID: CTB-85647DA7
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
-->

# Legacy Render Files Archive

## Purpose

This directory contains legacy files from the **Render deployment era** (pre-October 2025). These files have been archived as part of the doctrinal compliance audit to eliminate confusion about the current deployment platform.

## Deprecation Notice

**Render deployment is NO LONGER USED** in the Barton Outreach Core architecture.

### Current Deployment Platform

✅ **Vercel Serverless** (primary and only deployment platform)

See: [VERCEL_DEPLOYMENT_GUIDE.md](../../VERCEL_DEPLOYMENT_GUIDE.md)

### Why Render Was Deprecated

1. **Composio MCP Integration**: All external service integrations now flow through Composio MCP server, which runs independently of deployment platform
2. **Serverless Architecture**: Barton Outreach doctrine specifies serverless-first architecture (Sections 2 & 5 of Outreach Doctrine A→Z)
3. **Cost Optimization**: Vercel's edge functions provide better performance and cost efficiency
4. **Simplified Stack**: Single deployment platform reduces complexity

## Archived Files

This directory contains:
- **Old MCP Endpoint Scripts**: Files like `mcp-render-endpoint.js` that integrated with Render's deployment model
- **Legacy Documentation**: `RENDER_DEPENDENCY.md` files explaining old Render-based workflows
- **Before-Doctrine Scripts**: Files with `-before-doctrine` suffix representing pre-audit implementations

### Key Archived Files

| File | Original Location | Reason for Archival |
|------|-------------------|---------------------|
| `mcp-render-endpoint.js` | `apps/api/` | Replaced by Composio MCP integration |
| `mcp-render-endpoint-before-doctrine.js` | `apps/api/` | Pre-audit legacy code |
| `server-before-doctrine.js` | `apps/api/` | Pre-audit legacy code |
| `RENDER_DEPENDENCY.md` | `nodes/*/api/` | Obsolete deployment documentation |

## Migration Path

If you find references to "Render" in active code:

1. **Replace** with `Composio MCP (Serverless Replacement)`
2. **Update endpoint URLs** to use Vercel serverless function URLs
3. **Verify integration** via Composio MCP server on port 3001
4. **Reference documentation**: [COMPOSIO_INTEGRATION.md](../../COMPOSIO_INTEGRATION.md)

## Audit Reference

These files were archived as part of **Fix 3** in the Doctrinal Compliance Audit:

- **Audit Report**: [docs/audit_report.md](../../docs/audit_report.md)
- **Audit Section**: "5. Composio Integration" (Status: ✅ PASS with warnings)
- **Finding**: 36 files with "Render" references (mostly legacy/documentation)
- **Resolution**: Archive obsolete files, update active references

## Restoration Policy

**DO NOT restore these files** unless:
1. Explicitly required for historical research
2. Approved by Doctrine Maintenance Agent
3. Documented in a new architectural decision record (ADR)

## Related Documentation

- [Outreach Doctrine A→Z - Section 2: Architecture Map](../../docs/outreach-doctrine-a2z.md#%EF%B8%8F2%EF%B8%8F⃣-architecture-map)
- [VERCEL_DEPLOYMENT_GUIDE.md](../../VERCEL_DEPLOYMENT_GUIDE.md)
- [COMPOSIO_INTEGRATION.md](../../COMPOSIO_INTEGRATION.md)
- [Audit Report](../../docs/audit_report.md)

---

**Archive Date**: 2025-10-20
**Archived By**: Doctrine Maintenance Agent (Claude Code)
**Audit Reference**: Fix 3 - Legacy Render References
**Doctrine Version**: 1.3.2
