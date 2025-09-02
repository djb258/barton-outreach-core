/**
 * Composio MCP Client - Advanced AI agent tools integration
 */

import axios, { AxiosInstance } from 'axios';
import type {
  MCPClientConfig,
  MCPResponse,
  ComposioApp,
  ComposioAction,
  ComposioTool,
  ComposioWorkflow,
  ComposioWorkflowStep,
  ComposioExecutionResult,
  ComposioEntity
} from '../types/mcp-types';

export class ComposioMCPClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: MCPClientConfig = {}) {
    this.apiKey = config.apiKey || process.env.COMPOSIO_API_KEY || '';
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://backend.composio.dev/api',
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'barton-outreach-core/1.0.0'
      }
    });

    // Add response interceptor for consistent error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Composio API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get all available apps in Composio catalog
   */
  async getApps(category?: string): Promise<MCPResponse<ComposioApp[]>> {
    try {
      const response = await this.client.get('/v1/apps', {
        params: category ? { category } : {}
      });

      return {
        success: true,
        data: response.data.apps || response.data,
        metadata: {
          total_count: response.data.total_count,
          page: response.data.page,
          limit: response.data.limit
        }
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to fetch apps');
    }
  }

  /**
   * Get specific app details including actions
   */
  async getApp(appKey: string): Promise<MCPResponse<ComposioApp>> {
    try {
      const response = await this.client.get(`/v1/apps/${appKey}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to fetch app: ${appKey}`);
    }
  }

  /**
   * Get all available actions, optionally filtered by app
   */
  async getActions(appKey?: string, tags?: string[]): Promise<MCPResponse<ComposioAction[]>> {
    try {
      const params: any = {};
      if (appKey) params.app_name = appKey;
      if (tags?.length) params.tags = tags.join(',');

      const response = await this.client.get('/v1/actions', { params });

      return {
        success: true,
        data: response.data.actions || response.data,
        metadata: {
          total_count: response.data.total_count,
          filtered_by: params
        }
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to fetch actions');
    }
  }

  /**
   * Execute a specific action with parameters
   */
  async executeAction(
    actionName: string, 
    parameters: Record<string, any> = {},
    entityId?: string
  ): Promise<MCPResponse<ComposioExecutionResult>> {
    try {
      const payload = {
        action: actionName,
        parameters,
        entity_id: entityId || this.getDefaultEntity()
      };

      const response = await this.client.post('/v1/actions/execute', payload);

      return {
        success: true,
        data: response.data,
        metadata: {
          execution_id: response.data.execution_id,
          action: actionName
        }
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to execute action: ${actionName}`);
    }
  }

  /**
   * Get execution status and result
   */
  async getExecutionResult(executionId: string): Promise<MCPResponse<ComposioExecutionResult>> {
    try {
      const response = await this.client.get(`/v1/executions/${executionId}`);

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to get execution result: ${executionId}`);
    }
  }

  /**
   * List all available tools optimized for AI agents
   */
  async getAIOptimizedTools(agentType: 'claude' | 'gpt' | 'generic' = 'claude'): Promise<MCPResponse<ComposioTool[]>> {
    try {
      const response = await this.client.get('/v1/tools', {
        params: {
          agent_type: agentType,
          optimized: true
        }
      });

      return {
        success: true,
        data: response.data.tools || response.data,
        metadata: {
          agent_type: agentType,
          optimization_level: 'high'
        }
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to fetch AI-optimized tools');
    }
  }

  /**
   * Create a new workflow with steps
   */
  async createWorkflow(
    name: string,
    description: string,
    steps: ComposioWorkflowStep[]
  ): Promise<MCPResponse<ComposioWorkflow>> {
    try {
      const payload = {
        name,
        description,
        steps,
        triggers: [] // Can be added later
      };

      const response = await this.client.post('/v1/workflows', payload);

      return {
        success: true,
        data: response.data,
        metadata: {
          workflow_id: response.data.id,
          steps_count: steps.length
        }
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to create workflow');
    }
  }

  /**
   * Execute a workflow
   */
  async executeWorkflow(
    workflowId: string,
    inputs?: Record<string, any>
  ): Promise<MCPResponse<ComposioExecutionResult>> {
    try {
      const payload = {
        workflow_id: workflowId,
        inputs: inputs || {}
      };

      const response = await this.client.post('/v1/workflows/execute', payload);

      return {
        success: true,
        data: response.data,
        metadata: {
          workflow_id: workflowId,
          execution_id: response.data.execution_id
        }
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to execute workflow: ${workflowId}`);
    }
  }

  /**
   * Get all workflows
   */
  async getWorkflows(): Promise<MCPResponse<ComposioWorkflow[]>> {
    try {
      const response = await this.client.get('/v1/workflows');

      return {
        success: true,
        data: response.data.workflows || response.data
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to fetch workflows');
    }
  }

  /**
   * Manage entities (connections to external services)
   */
  async getEntities(): Promise<MCPResponse<ComposioEntity[]>> {
    try {
      const response = await this.client.get('/v1/entities');

      return {
        success: true,
        data: response.data.entities || response.data
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to fetch entities');
    }
  }

  /**
   * Create a new entity connection
   */
  async createEntity(
    name: string,
    appKey: string,
    connectionConfig: Record<string, any>
  ): Promise<MCPResponse<ComposioEntity>> {
    try {
      const payload = {
        name,
        app_name: appKey,
        connection_config: connectionConfig
      };

      const response = await this.client.post('/v1/entities', payload);

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      return this.handleError(error, 'Failed to create entity');
    }
  }

  /**
   * Health check for Composio service
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      const response = await this.client.get('/health');

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        },
        metadata: {
          response_time: Date.now(),
          api_version: response.headers['api-version'] || 'v1'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: 'Composio service unhealthy',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  /**
   * Search for specific tools or actions
   */
  async searchTools(
    query: string,
    category?: string,
    limit: number = 20
  ): Promise<MCPResponse<ComposioTool[]>> {
    try {
      const response = await this.client.get('/v1/tools/search', {
        params: {
          query,
          category,
          limit
        }
      });

      return {
        success: true,
        data: response.data.tools || response.data,
        metadata: {
          query,
          category,
          results_count: response.data.tools?.length || 0
        }
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to search tools for: ${query}`);
    }
  }

  /**
   * Get tool recommendations based on use case
   */
  async getToolRecommendations(
    useCase: string,
    context?: Record<string, any>
  ): Promise<MCPResponse<ComposioTool[]>> {
    try {
      const response = await this.client.post('/v1/tools/recommend', {
        use_case: useCase,
        context: context || {}
      });

      return {
        success: true,
        data: response.data.recommendations || response.data,
        metadata: {
          use_case: useCase,
          context_provided: !!context
        }
      };
    } catch (error: any) {
      return this.handleError(error, `Failed to get tool recommendations for: ${useCase}`);
    }
  }

  private handleError(error: any, context: string): MCPResponse {
    const errorMessage = error.response?.data?.message || error.message || 'Unknown error';
    
    return {
      success: false,
      error: `${context}: ${errorMessage}`,
      metadata: {
        status_code: error.response?.status,
        timestamp: new Date().toISOString()
      }
    };
  }

  private getDefaultEntity(): string {
    // Return a default entity ID or generate one
    return process.env.COMPOSIO_DEFAULT_ENTITY || 'default';
  }
}