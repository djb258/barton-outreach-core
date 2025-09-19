# Barton Outreach Core - UI Applications

This branch contains multiple UI applications for the Barton Outreach system:

## Applications

### 1. UI Workspace (`apps/ui-workspace/`)
A modern React-based UI for outreach management with:
- Dashboard with metrics overview
- Company and People databases
- Campaign management
- MCP integrations

**Run:** `cd apps/ui-workspace && npm install && npm run dev`

### 2. Outreach Process Manager (`apps/outreach-process-manager/`)
A comprehensive process management UI featuring:
- Visual process flows with D3.js
- Redux state management
- Framer Motion animations
- Tailwind CSS components
- DHiWise component tagging

**Run:** `cd apps/outreach-process-manager && npm install && npm start`

### 3. Amplify Client (`apps/amplify-client/`)
AWS Amplify-optimized client with:
- AWS Amplify integration
- Cloud-ready deployment
- React Query for data fetching
- Builder.io and Plasmic integrations

**Run:** `cd apps/amplify-client && npm install && npm run dev`

### 4. Factory IMO (`apps/factory-imo/`)
Factory pattern implementation for:
- IMO (Internal Model Objects) management
- Garage MCP integration
- Blueprint system

### 5. Outreach UI (`apps/outreach-ui/`)
Core outreach UI components and blueprints

## MCP Server Integrations

The branch includes MCP (Model Context Protocol) servers for:
- **GitHub** (via Composio and Direct API)
- **Smartsheet** integration
- **Data routing** via `@barton/data-router`

Start MCP servers:
- `./start-github-mcp.bat` - GitHub via Composio
- `./start-github-direct.bat` - Direct GitHub API
- `./start-smartsheet-mcp.bat` - Smartsheet integration

## Development

Each application can be run independently:

1. Navigate to the app directory
2. Install dependencies: `npm install`
3. Start development server: `npm run dev` or `npm start`

## Architecture

```
apps/
├── ui-workspace/          # Modern React UI
├── outreach-process-manager/  # Process management UI
├── amplify-client/        # AWS Amplify client
├── factory-imo/           # Factory pattern system
└── outreach-ui/          # Core UI components

mcp-servers/              # MCP integration servers
config/                   # Configuration files
packages/                 # Shared packages
```

## Technologies Used

- React 18 with TypeScript
- Vite & Webpack build systems
- Tailwind CSS
- Redux Toolkit
- React Router
- D3.js for visualizations
- Framer Motion for animations
- AWS Amplify
- MCP Protocol integrations