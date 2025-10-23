/**
 * MCP Clients - Composio.dev integration for Barton Outreach Core
 */

export { ComposioMCPClient } from './clients/composio-client.js';
export { RefToolsMCPClient } from './clients/reftools-client.js';
export { ApifyMCPClient } from './clients/apify-mcp-client.js';
export { NeonMCPClient } from './clients/neon-mcp-client.js';
export { PLEOrchestrator } from './clients/ple-orchestrator.js';
export { BitMCPClient } from './clients/bit-mcp-client.js';
export { MCPOrchestrator } from './orchestrator/mcp-orchestrator.js';

export type {
  MCPClientConfig,
  ComposioAction,
  ComposioApp,
  ComposioWorkflow,
  ComposioTool,
  ComposioExecutionResult,
  RefToolsSearchResult,
  RefToolsValidationResult,
  MCPResponse
} from './types/mcp-types';

export {
  createComposioClient,
  createRefToolsClient,
  createOrchestrator
} from './factory/client-factory.js';