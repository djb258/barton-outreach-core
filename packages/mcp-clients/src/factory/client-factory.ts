/**
 * MCP Client Factory - Easy creation and configuration of MCP clients
 */

import { ComposioMCPClient } from '../clients/composio-client.js';
import { RefToolsMCPClient } from '../clients/reftools-client.js';
import { MCPOrchestrator } from '../orchestrator/mcp-orchestrator.js';
import type { MCPClientConfig } from '../types/mcp-types';

/**
 * Create a Composio client with default configuration
 */
export function createComposioClient(config: MCPClientConfig = {}): ComposioMCPClient {
  const defaultConfig: MCPClientConfig = {
    apiKey: process.env.COMPOSIO_API_KEY,
    timeout: 30000,
    retries: 3,
    ...config
  };

  return new ComposioMCPClient(defaultConfig);
}

/**
 * Create a RefTools client with default configuration
 */
export function createRefToolsClient(config: MCPClientConfig = {}): RefToolsMCPClient {
  const defaultConfig: MCPClientConfig = {
    apiKey: process.env.REFTOOLS_API_KEY,
    timeout: 15000,
    retries: 2,
    ...config
  };

  return new RefToolsMCPClient(defaultConfig);
}

/**
 * Create an orchestrator with both clients configured
 */
export function createOrchestrator(
  composioConfig: MCPClientConfig = {},
  refToolsConfig: MCPClientConfig = {}
): MCPOrchestrator {
  const defaultComposioConfig: MCPClientConfig = {
    apiKey: process.env.COMPOSIO_API_KEY,
    timeout: 30000,
    retries: 3,
    ...composioConfig
  };

  const defaultRefToolsConfig: MCPClientConfig = {
    apiKey: process.env.REFTOOLS_API_KEY,
    timeout: 15000,
    retries: 2,
    ...refToolsConfig
  };

  return new MCPOrchestrator(defaultComposioConfig, defaultRefToolsConfig);
}

/**
 * Create a Composio-focused client for heavy AI automation
 */
export function createComposioFocusedClient(config: MCPClientConfig = {}): {
  composio: ComposioMCPClient;
  orchestrator: MCPOrchestrator;
} {
  const composioConfig: MCPClientConfig = {
    apiKey: process.env.COMPOSIO_API_KEY,
    timeout: 45000, // Longer timeout for AI operations
    retries: 5, // More retries for AI operations
    ...config
  };

  const composio = new ComposioMCPClient(composioConfig);
  const orchestrator = createOrchestrator(composioConfig);

  return {
    composio,
    orchestrator
  };
}

/**
 * Quick setup for development with fallback support
 */
export function createDevelopmentClients(): {
  composio: ComposioMCPClient;
  reftools: RefToolsMCPClient;
  orchestrator: MCPOrchestrator;
} {
  console.log('🔧 Setting up MCP clients for development...');
  
  // Check for API keys and warn if missing
  if (!process.env.COMPOSIO_API_KEY) {
    console.warn('⚠️  COMPOSIO_API_KEY not set - using fallback mode');
  }
  
  if (!process.env.REFTOOLS_API_KEY) {
    console.warn('⚠️  REFTOOLS_API_KEY not set - using fallback mode');
  }

  const composio = createComposioClient({
    timeout: 20000 // Shorter timeout for development
  });

  const reftools = createRefToolsClient({
    timeout: 10000 // Shorter timeout for development
  });

  const orchestrator = createOrchestrator(
    { timeout: 20000 },
    { timeout: 10000 }
  );

  console.log('✅ MCP clients ready for development');
  
  return {
    composio,
    reftools,
    orchestrator
  };
}

/**
 * Production setup with full error handling and monitoring
 */
export function createProductionClients(): {
  composio: ComposioMCPClient;
  reftools: RefToolsMCPClient;
  orchestrator: MCPOrchestrator;
} {
  console.log('🚀 Setting up MCP clients for production...');

  // Validate required environment variables
  const requiredEnvVars = ['COMPOSIO_API_KEY'];
  const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
  
  if (missingVars.length > 0) {
    console.error(`❌ Missing required environment variables: ${missingVars.join(', ')}`);
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }

  if (!process.env.REFTOOLS_API_KEY) {
    console.warn('⚠️  REFTOOLS_API_KEY not set - RefTools will use fallback mode');
  }

  const composio = createComposioClient({
    timeout: 60000, // Longer timeout for production
    retries: 5
  });

  const reftools = createRefToolsClient({
    timeout: 30000, // Longer timeout for production
    retries: 3
  });

  const orchestrator = createOrchestrator(
    { timeout: 60000, retries: 5 },
    { timeout: 30000, retries: 3 }
  );

  console.log('✅ MCP clients ready for production');
  
  return {
    composio,
    reftools,
    orchestrator
  };
}