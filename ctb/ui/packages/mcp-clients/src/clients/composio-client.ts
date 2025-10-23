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

  /**
   * Create Neon Ingest Contacts workflow
   */
  async createNeonIngestWorkflow(): Promise<MCPResponse<ComposioWorkflow>> {
    const workflowName = 'Neon Secure Ingest Contacts';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    const steps: ComposioWorkflowStep[] = [
      {
        id: 'validate-data',
        name: 'Validate Input Data',
        action: 'data_validation',
        parameters: {
          schema: 'contact_schema',
          required_fields: ['email']
        },
        retry_config: {
          max_retries: 2,
          backoff_strategy: 'linear'
        }
      },
      {
        id: 'ingest-to-neon',
        name: 'Ingest to Neon Database',
        action: 'neon_ingest_secure',
        parameters: {
          function: 'intake.f_ingest_json',
          source: `composio.${this.apiKey ? 'authenticated' : 'anonymous'}`,
          batch_id: `batch-${timestamp}`
        },
        retry_config: {
          max_retries: 3,
          backoff_strategy: 'exponential'
        }
      },
      {
        id: 'log-results',
        name: 'Log Ingestion Results',
        action: 'audit_log',
        parameters: {
          operation: 'ingest_contacts',
          timestamp: timestamp
        }
      }
    ];

    return this.createWorkflow(
      workflowName,
      'Securely ingest contacts using Neon SECURITY DEFINER function',
      steps
    );
  }

  /**
   * Create Neon Promote Contacts workflow
   */
  async createNeonPromoteWorkflow(): Promise<MCPResponse<ComposioWorkflow>> {
    const workflowName = 'Neon Secure Promote Contacts';
    
    const steps: ComposioWorkflowStep[] = [
      {
        id: 'fetch-pending',
        name: 'Fetch Pending Loads',
        action: 'neon_query',
        parameters: {
          query: 'SELECT load_id FROM intake.raw_loads WHERE status = \'pending\' LIMIT 100'
        },
        retry_config: {
          max_retries: 2,
          backoff_strategy: 'linear'
        }
      },
      {
        id: 'promote-to-vault',
        name: 'Promote to Contacts Vault',
        action: 'neon_promote_secure',
        parameters: {
          function: 'vault.f_promote_contacts',
          load_ids_from: 'fetch-pending.result'
        },
        retry_config: {
          max_retries: 3,
          backoff_strategy: 'exponential'
        }
      },
      {
        id: 'send-notification',
        name: 'Send Promotion Notification',
        action: 'notification',
        parameters: {
          type: 'promotion_complete',
          include_stats: true
        }
      }
    ];

    return this.createWorkflow(
      workflowName,
      'Securely promote contacts from intake to vault using Neon SECURITY DEFINER function',
      steps
    );
  }

  /**
   * Execute Neon secure ingestion directly
   */
  async executeNeonIngest(
    rows: Array<Record<string, any>>,
    source?: string,
    batchId?: string
  ): Promise<MCPResponse<any>> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    return this.executeAction(
      'neon_ingest_secure',
      {
        rows,
        source: source || `composio.${this.apiKey ? 'authenticated' : 'anonymous'}`,
        batch_id: batchId || `batch-${timestamp}`,
        query: 'SELECT * FROM intake.f_ingest_json($1::jsonb[], $2::text, $3::text)'
      }
    );
  }

  /**
   * Execute Neon secure promotion directly
   */
  async executeNeonPromote(
    loadIds?: number[]
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'neon_promote_secure',
      {
        load_ids: loadIds,
        query: loadIds 
          ? 'SELECT * FROM vault.f_promote_contacts($1::bigint[])' 
          : 'SELECT * FROM vault.f_promote_contacts(NULL)'
      }
    );
  }

  /**
   * UI Builder Integrations via Composio
   */

  /**
   * Builder.io Integration - Create/Update components
   */
  async builderIOCreateComponent(
    modelName: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'builder_io_create_component',
      {
        model: modelName,
        data: componentData,
        publish: false // Draft by default
      }
    );
  }

  async builderIOPublishComponent(
    modelName: string,
    entryId: string
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'builder_io_publish',
      {
        model: modelName,
        entry_id: entryId
      }
    );
  }

  async builderIOGetContent(
    modelName: string,
    url?: string
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'builder_io_get_content',
      {
        model: modelName,
        url: url || window?.location?.pathname || '/'
      }
    );
  }

  /**
   * Plasmic Integration - Manage designs and components
   */
  async plasmicGetProject(projectId: string): Promise<MCPResponse<any>> {
    return this.executeAction(
      'plasmic_get_project',
      {
        project_id: projectId
      }
    );
  }

  async plasmicCreateComponent(
    projectId: string,
    componentName: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'plasmic_create_component',
      {
        project_id: projectId,
        name: componentName,
        data: componentData
      }
    );
  }

  async plasmicUpdateComponent(
    projectId: string,
    componentId: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'plasmic_update_component',
      {
        project_id: projectId,
        component_id: componentId,
        data: componentData
      }
    );
  }

  async plasmicGenerateCode(
    projectId: string,
    componentIds: string[],
    platform: 'react' | 'vue' | 'angular' = 'react'
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'plasmic_generate_code',
      {
        project_id: projectId,
        component_ids: componentIds,
        platform
      }
    );
  }

  /**
   * Figma Integration - Design system sync
   */
  async figmaGetFile(fileKey: string): Promise<MCPResponse<any>> {
    return this.executeAction(
      'figma_get_file',
      {
        file_key: fileKey
      }
    );
  }

  async figmaGetComponents(fileKey: string): Promise<MCPResponse<any>> {
    return this.executeAction(
      'figma_get_components',
      {
        file_key: fileKey
      }
    );
  }

  async figmaGetStyles(fileKey: string): Promise<MCPResponse<any>> {
    return this.executeAction(
      'figma_get_styles',
      {
        file_key: fileKey,
        style_type: 'all' // or 'FILL', 'TEXT', 'EFFECT', 'GRID'
      }
    );
  }

  async figmaExportNodes(
    fileKey: string,
    nodeIds: string[],
    format: 'png' | 'svg' | 'pdf' = 'png'
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'figma_export_nodes',
      {
        file_key: fileKey,
        ids: nodeIds,
        format
      }
    );
  }

  async figmaGenerateTokens(fileKey: string): Promise<MCPResponse<any>> {
    return this.executeAction(
      'figma_generate_design_tokens',
      {
        file_key: fileKey,
        include_colors: true,
        include_typography: true,
        include_spacing: true,
        include_borders: true,
        include_shadows: true
      }
    );
  }

  /**
   * Loveable.dev Integration - AI-generated components
   */
  async loveableGenerateComponent(
    prompt: string,
    framework: 'react' | 'vue' | 'svelte' = 'react'
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'loveable_generate_component',
      {
        prompt,
        framework,
        style_system: 'tailwindcss'
      }
    );
  }

  async loveableOptimizeComponent(
    componentCode: string,
    optimizationGoals: string[]
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'loveable_optimize_component',
      {
        code: componentCode,
        goals: optimizationGoals // ['performance', 'accessibility', 'mobile-responsive']
      }
    );
  }

  async loveableGenerateVariants(
    componentCode: string,
    variantTypes: string[]
  ): Promise<MCPResponse<any>> {
    return this.executeAction(
      'loveable_generate_variants',
      {
        code: componentCode,
        variants: variantTypes // ['size', 'color', 'state']
      }
    );
  }

  /**
   * UI Builder Orchestration Workflows
   */
  async createDesignSystemSyncWorkflow(
    figmaFileKey: string,
    plasmicProjectId: string,
    builderIOApiKey: string
  ): Promise<MCPResponse<ComposioWorkflow>> {
    const workflowName = 'Design System Sync - Figma to UI Builders';
    
    const steps: ComposioWorkflowStep[] = [
      {
        id: 'extract-figma-tokens',
        name: 'Extract Design Tokens from Figma',
        action: 'figma_generate_design_tokens',
        parameters: {
          file_key: figmaFileKey,
          include_colors: true,
          include_typography: true,
          include_spacing: true
        }
      },
      {
        id: 'sync-to-plasmic',
        name: 'Sync Tokens to Plasmic',
        action: 'plasmic_update_design_tokens',
        parameters: {
          project_id: plasmicProjectId,
          tokens_from: 'extract-figma-tokens.result'
        }
      },
      {
        id: 'sync-to-builder',
        name: 'Sync Tokens to Builder.io',
        action: 'builder_io_update_design_system',
        parameters: {
          api_key: builderIOApiKey,
          tokens_from: 'extract-figma-tokens.result'
        }
      },
      {
        id: 'generate-loveable-components',
        name: 'Generate Components with Loveable',
        action: 'loveable_generate_component_library',
        parameters: {
          design_tokens_from: 'extract-figma-tokens.result',
          framework: 'react'
        }
      },
      {
        id: 'audit-sync',
        name: 'Audit Design System Sync',
        action: 'audit_log',
        parameters: {
          operation: 'design_system_sync',
          figma_file: figmaFileKey,
          plasmic_project: plasmicProjectId
        }
      }
    ];

    return this.createWorkflow(
      workflowName,
      'Sync design tokens from Figma to all UI builders and generate component library',
      steps
    );
  }

  async executeDesignSystemSync(
    figmaFileKey: string,
    plasmicProjectId: string,
    builderIOApiKey: string
  ): Promise<MCPResponse<ComposioExecutionResult>> {
    // Create workflow if it doesn't exist
    const workflowResult = await this.createDesignSystemSyncWorkflow(
      figmaFileKey,
      plasmicProjectId,
      builderIOApiKey
    );

    if (!workflowResult.success || !workflowResult.data?.id) {
      return {
        success: false,
        error: 'Failed to create design system sync workflow',
        data: undefined
      };
    }

    // Execute the workflow
    return this.executeWorkflow(workflowResult.data.id, {
      figma_file_key: figmaFileKey,
      plasmic_project_id: plasmicProjectId,
      builder_io_api_key: builderIOApiKey
    });
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