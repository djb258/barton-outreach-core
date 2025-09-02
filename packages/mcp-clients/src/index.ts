/**
 * MCP Clients - Composio.dev integration for Barton Outreach Core
 */

export { ComposioMCPClient } from './clients/composio-client.js';
export { RefToolsMCPClient } from './clients/reftools-client.js';
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