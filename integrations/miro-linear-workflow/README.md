# Miro → Linear → Claude Code Workflow

Complete integration for the **File → Miro → Linear → Claude Code** workflow.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FILE → MIRO → LINEAR → CLAUDE CODE                  │
└─────────────────────────────────────────────────────────────────────────┘

    📄 File                    🎨 Miro                    📋 Linear
    (Markdown docs)      →     (Visualization)      →    (Issue tracking)
                                                               │
                                                               ▼
                                                         🤖 Claude Code
                                                         (Implementation)
```

## Quick Start

### 1. Install Dependencies

```bash
cd integrations/miro-linear-workflow
npm install
```

### 2. Configure Environment

Create a `.env` file (copy from `env.example.txt`):

```bash
# Miro
MIRO_TOKEN=your_miro_access_token
MIRO_BOARD_ID=your_default_board_id

# Linear
LINEAR_API_KEY=lin_api_your_key
LINEAR_TEAM_KEY=ENG
```

### 3. Get API Keys

**Miro:**
1. Go to https://miro.com/app/settings/user-profile/apps
2. Create a new app or use existing
3. Copy the Access Token

**Linear:**
1. Go to https://linear.app/settings/api
2. Create a Personal API Key
3. Copy the key

## Commands

### Push File to Miro

Upload a markdown file to Miro as a structured diagram:

```bash
npm run push -- ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md
```

This will:
- Parse the markdown structure
- Create a frame for the document
- Create shapes for section headers
- Create sticky notes for subsections
- Detect Bicycle Wheel Doctrine format and create wheel visualization

### Sync to Linear

Create Linear issues from a file's section headers:

```bash
npm run linear-sync -- ../../docs/prd/HUB_PROCESS_SIGNAL_MATRIX.md ENG
```

This will:
- Extract `## Headers` as issues
- Tag with `claude-ready` label
- Assign to specified team

### List Claude-Ready Issues

See which issues are ready for implementation:

```bash
npm run issues -- claude-ready
```

### Full Workflow

Run the complete workflow (Miro + Linear):

```bash
npx tsx src/workflow.ts full ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md
```

## MCP Configuration (Claude Code)

To enable Claude Code to interact with Miro and Linear directly, add MCP servers.

### Option 1: Miro MCP (Enterprise)

Miro provides an official MCP server for Enterprise plans:

```json
{
  "mcpServers": {
    "miro": {
      "url": "https://mcp.miro.com",
      "transport": "sse"
    }
  }
}
```

### Option 2: Linear MCP

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@anthropic/linear-mcp-server"],
      "env": {
        "LINEAR_API_KEY": "your_linear_api_key"
      }
    }
  }
}
```

## Workflow Examples

### Example 1: Document → Visual → Tasks

```bash
# 1. Push BICYCLE_WHEEL_DOCTRINE.md to Miro for visual review
npm run push -- ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md

# 2. Review in Miro, add sticky notes for tasks

# 3. Create Linear issues from the document
npm run linear-sync -- ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md

# 4. See what's ready for Claude Code
npx tsx src/workflow.ts claude-ready
```

### Example 2: PRD → Implementation

```bash
# 1. Full workflow for a PRD
npx tsx src/workflow.ts full ../../docs/prd/PRD_PEOPLE_SUBHUB.md

# 2. In Claude Code, ask:
# "Show me claude-ready issues from Linear"
# "Implement the Email Generation phase from PRD_PEOPLE_SUBHUB"
```

## API Reference

### Miro Uploader

```typescript
import { uploadMarkdownToMiro } from './src/miro-uploader.js';

const result = await uploadMarkdownToMiro(
  'path/to/file.md',
  'board_id',  // optional, uses MIRO_BOARD_ID env var
  'token'      // optional, uses MIRO_TOKEN env var
);

console.log(result.itemCount);  // Number of items created
console.log(result.frameId);    // ID of the created frame
```

### Linear Sync

```typescript
import { 
  createIssue, 
  getClaudeReadyIssues,
  createIssuesFromMarkdown 
} from './src/linear-sync.js';

// Create a single issue
const issue = await createIssue(
  'Implement HashAgent',
  'Description here',
  'ENG',                    // team key
  ['claude-ready']          // labels
);

// Get claude-ready issues
const issues = await getClaudeReadyIssues();

// Create issues from markdown sections
const issues = await createIssuesFromMarkdown(
  'path/to/doc.md',
  'ENG'
);
```

## File Structure

```
integrations/miro-linear-workflow/
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── env.example.txt        # Environment template
├── mcp-config.json        # MCP server configuration
├── README.md              # This file
└── src/
    ├── types.ts           # TypeScript types
    ├── miro-uploader.ts   # Miro API integration
    ├── linear-sync.ts     # Linear API integration
    └── workflow.ts        # Unified CLI
```

## Troubleshooting

### Miro API Errors

- **401 Unauthorized**: Check your MIRO_TOKEN
- **404 Not Found**: Check your MIRO_BOARD_ID
- **Rate limited**: Add delay between requests

### Linear API Errors

- **401 Unauthorized**: Check your LINEAR_API_KEY
- **Team not found**: Run `npm run linear-sync -- teams` to see available teams

### File Not Found

- Use relative paths from the `miro-linear-workflow` directory
- Example: `../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md`

## Integration with Barton System

This workflow integrates with:

- **Bicycle Wheel Doctrine**: Auto-detects and creates wheel visualizations
- **Hub-Spoke Architecture**: Parses hub/spoke structure from docs
- **PRD Documents**: Creates issues from PRD sections
- **Talent Engine**: Track implementation tasks in Linear

---

*Part of the Barton Outreach Core integration suite*


