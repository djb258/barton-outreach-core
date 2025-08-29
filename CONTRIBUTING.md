# Contributing to Barton Outreach Core

Thank you for your interest in contributing to Barton Outreach Core! This project integrates IMO Creator functionality with HEIR/MCP compliance for blueprint planning and outreach orchestration.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd barton-outreach-core
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Install Python dependencies** (for backend tools)
   ```bash
   pip install -r requirements.txt
   ```

## Architecture Overview

This project combines:
- **React Frontend**: TypeScript + Vite + shadcn/ui components
- **HEIR Orchestration**: Hierarchical agent system
- **IMO Creator**: Blueprint planning with SSOT manifests
- **MCP Integration**: Model Context Protocol for validation
- **Python Backend**: FastAPI tools for compliance and scoring

## Key Components

### Frontend Structure
- `src/components/imo/` - IMO Creator components
- `src/components/heir/` - HEIR orchestration components
- `src/lib/imo/` - IMO service logic and MCP integration
- `src/lib/heir/` - HEIR agent registry and orchestration

### Backend Tools
- `api/` - Vercel serverless functions
- `python-server/` - FastAPI backend services
- `tools/` - Compliance checking and blueprint scoring
- `garage-mcp/` - MCP server for HEIR validation

## Development Commands

```bash
# Frontend development
npm run dev                    # Start Vite dev server
npm run build                  # Build for production
npm run lint                   # Run ESLint

# Backend services
npm run mcp:start             # Start MCP server
npm run blueprint:score       # Run blueprint scoring
npm run compliance:check      # Check HEIR compliance
npm run heir:audit           # Full HEIR audit
```

## HEIR Compliance

This project follows HEIR (Hierarchical Error-handling, ID management, and Reporting) principles:

1. **Schema Version**: All manifests must include `doctrine.schema_version`
2. **Unique IDs**: Automatic stamping of `unique_id`, `process_id`, `blueprint_version_hash`
3. **MCP Validation**: Real-time validation via Model Context Protocol
4. **Telemetry**: Event logging to sidecar for monitoring

## Contribution Guidelines

### Code Style
- Use TypeScript for all React components
- Follow existing ESLint configuration
- Use shadcn/ui components for consistency
- Add proper type annotations

### Blueprint Management
- All IMO blueprints must have proper SSOT structure
- Use the BlueprintManager component for UI interactions
- Validate changes through MCP service before persistence

### Testing
- Add tests for new components and services
- Ensure HEIR compliance before submitting
- Test both online and offline (fallback) modes

### Pull Request Process
1. Create a feature branch from `main`
2. Implement changes following the style guide
3. Run compliance checks: `npm run compliance:check`
4. Test both frontend and backend functionality
5. Submit PR with clear description of changes

## SSOT Manifest Structure

```yaml
meta:
  app_name: "Your App Name"
  stage: "overview|input|middle|output"
  created: "ISO timestamp"

doctrine:
  schema_version: "HEIR/1.0"
  unique_id: "shq-03-imo-1-{hash}"
  process_id: "proc-{hash}"
  blueprint_version_hash: "{hash}"

buckets:
  input:
    stages: []
  middle:
    stages: []
  output:
    stages: []
```

## Questions or Issues?

Please open an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Node.js version, browser, etc.)

## License

This project is licensed under the MIT License - see the LICENSE file for details.