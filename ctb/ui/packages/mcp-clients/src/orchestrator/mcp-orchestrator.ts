/**
 * MCP Orchestrator - Coordinates multiple MCP clients with heavy Composio emphasis
 */

import { ComposioMCPClient } from '../clients/composio-client.js';
import { RefToolsMCPClient } from '../clients/reftools-client.js';
import type {
  MCPClientConfig,
  MCPResponse,
  MCPTask,
  MCPTaskResult,
  MCPOrchestrationPlan,
  MCPServerHealth,
  ComposioTool,
  ComposioExecutionResult
} from '../types/mcp-types';

export class MCPOrchestrator {
  private composioClient: ComposioMCPClient;
  private refToolsClient: RefToolsMCPClient;
  private taskQueue: Map<string, MCPTask> = new Map();
  private taskResults: Map<string, MCPTaskResult> = new Map();

  constructor(
    composioConfig: MCPClientConfig = {},
    refToolsConfig: MCPClientConfig = {}
  ) {
    this.composioClient = new ComposioMCPClient(composioConfig);
    this.refToolsClient = new RefToolsMCPClient(refToolsConfig);
  }

  /**
   * Primary method - Execute complex task using Composio as the main orchestrator
   */
  async orchestrateComplexTask(
    description: string,
    context?: Record<string, any>
  ): Promise<MCPResponse<{
    task: string;
    steps_completed: MCPTaskResult[];
    errors: string[];
  }>> {
    const errors: string[] = [];
    const stepsCompleted: MCPTaskResult[] = [];

    try {
      // Step 1: Get Composio tool recommendations for the task
      console.log('🔍 Getting Composio tool recommendations...');
      const toolsResponse = await this.composioClient.getToolRecommendations(description, context);
      
      if (!toolsResponse.success) {
        errors.push(`Tool recommendation failed: ${toolsResponse.error}`);
      }

      // Step 2: If task involves documentation/API work, get RefTools assistance
      if (this.isDocumentationTask(description)) {
        console.log('📚 Fetching relevant documentation...');
        const docsResponse = await this.refToolsClient.searchReferences(
          this.extractKeywords(description),
          context?.language || 'javascript'
        );
        
        if (docsResponse.success && docsResponse.data) {
          stepsCompleted.push({
            task_id: 'reftools-search',
            status: 'completed',
            result: docsResponse.data,
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            execution_time_ms: 100
          });
        }
      }

      // Step 3: Execute primary Composio workflow
      console.log('🚀 Executing Composio workflow...');
      const workflowSteps = this.createWorkflowSteps(description, toolsResponse.data);
      
      if (workflowSteps.length > 0) {
        const workflowResponse = await this.composioClient.createWorkflow(
          `Auto-generated: ${description}`,
          description,
          workflowSteps
        );

        if (workflowResponse.success && workflowResponse.data) {
          // Execute the workflow
          const executionResponse = await this.composioClient.executeWorkflow(
            workflowResponse.data.id
          );

          if (executionResponse.success) {
            stepsCompleted.push({
              task_id: 'composio-workflow',
              status: 'completed',
              result: executionResponse.data,
              started_at: new Date().toISOString(),
              completed_at: new Date().toISOString(),
              execution_time_ms: 500
            });
          } else {
            errors.push(`Workflow execution failed: ${executionResponse.error}`);
          }
        } else {
          errors.push(`Workflow creation failed: ${workflowResponse.error}`);
        }
      }

      return {
        success: true,
        data: {
          task: description,
          steps_completed: stepsCompleted,
          errors
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Orchestration failed: ${error.message}`,
        data: {
          task: description,
          steps_completed: stepsCompleted,
          errors: [...errors, error.message]
        }
      };
    }
  }

  /**
   * Get all available Composio tools with categories
   */
  async getAvailableComposioTools(category?: string): Promise<MCPResponse<ComposioTool[]>> {
    try {
      // First get AI-optimized tools for Claude
      const optimizedResponse = await this.composioClient.getAIOptimizedTools('claude');
      
      if (optimizedResponse.success && optimizedResponse.data) {
        let tools = optimizedResponse.data;
        
        // Filter by category if provided
        if (category) {
          tools = tools.filter(tool => 
            tool.category?.toLowerCase() === category.toLowerCase() ||
            tool.tags?.some(tag => tag.toLowerCase() === category.toLowerCase())
          );
        }

        return {
          success: true,
          data: tools,
          metadata: {
            source: 'composio-optimized',
            filtered_by_category: category,
            optimization_level: 'claude'
          }
        };
      }

      // Fallback: try to get regular tools
      const searchResponse = await this.composioClient.searchTools('', category);
      return searchResponse;

    } catch (error: any) {
      return {
        success: false,
        error: `Failed to fetch Composio tools: ${error.message}`
      };
    }
  }

  /**
   * Execute Composio action directly
   */
  async executeComposioAction(
    actionName: string,
    parameters: Record<string, any> = {},
    entityId?: string
  ): Promise<MCPResponse<ComposioExecutionResult>> {
    return await this.composioClient.executeAction(actionName, parameters, entityId);
  }

  /**
   * Search for API documentation using RefTools
   */
  async searchAPIDocumentation(
    query: string,
    language?: string,
    framework?: string
  ): Promise<MCPResponse<any>> {
    return await this.refToolsClient.searchReferences(query, language, framework);
  }

  /**
   * Health check all MCP servers
   */
  async healthCheckAllServers(): Promise<Record<string, MCPServerHealth>> {
    const results: Record<string, MCPServerHealth> = {};
    const startTime = Date.now();

    // Check Composio
    try {
      const composioHealth = await this.composioClient.healthCheck();
      results.composio = {
        server_id: 'composio',
        name: 'Composio AI Tools',
        type: 'composio',
        status: composioHealth.success ? 'healthy' : 'unhealthy',
        response_time_ms: Date.now() - startTime,
        last_check: new Date().toISOString(),
        error: composioHealth.error
      };
    } catch (error: any) {
      results.composio = {
        server_id: 'composio',
        name: 'Composio AI Tools', 
        type: 'composio',
        status: 'unhealthy',
        response_time_ms: Date.now() - startTime,
        last_check: new Date().toISOString(),
        error: error.message
      };
    }

    // Check RefTools
    const refStartTime = Date.now();
    try {
      const refToolsHealth = await this.refToolsClient.healthCheck();
      results.reftools = {
        server_id: 'reftools',
        name: 'RefTools Documentation',
        type: 'reftools',
        status: refToolsHealth.success ? 'healthy' : 'unhealthy',
        response_time_ms: Date.now() - refStartTime,
        last_check: new Date().toISOString(),
        error: refToolsHealth.error
      };
    } catch (error: any) {
      results.reftools = {
        server_id: 'reftools',
        name: 'RefTools Documentation',
        type: 'reftools',
        status: 'unhealthy', 
        response_time_ms: Date.now() - refStartTime,
        last_check: new Date().toISOString(),
        error: error.message
      };
    }

    return results;
  }

  /**
   * List all configured servers
   */
  listAllServers(): Array<{
    name: string;
    type: 'composio' | 'reftools';
    has_driver: boolean;
    enabled: boolean;
  }> {
    return [
      {
        name: 'Composio AI Tools Platform',
        type: 'composio',
        has_driver: true,
        enabled: true
      },
      {
        name: 'RefTools Documentation Service', 
        type: 'reftools',
        has_driver: true,
        enabled: true
      }
    ];
  }

  /**
   * Create Composio workflow for AI agent automation
   */
  async createComposioWorkflow(
    name: string,
    description: string,
    automationSteps: Array<{
      action: string;
      params: Record<string, any>;
      conditions?: Record<string, any>;
    }>
  ): Promise<MCPResponse<any>> {
    const workflowSteps = automationSteps.map((step, index) => ({
      id: `step-${index + 1}`,
      name: `${step.action} Step`,
      action: step.action,
      parameters: step.params,
      conditions: step.conditions,
      retry_config: {
        max_retries: 3,
        backoff_strategy: 'exponential' as const
      }
    }));

    return await this.composioClient.createWorkflow(name, description, workflowSteps);
  }

  // Private helper methods
  private isDocumentationTask(description: string): boolean {
    const docKeywords = ['api', 'documentation', 'docs', 'reference', 'guide', 'tutorial', 'spec', 'openapi'];
    return docKeywords.some(keyword => description.toLowerCase().includes(keyword));
  }

  private extractKeywords(description: string): string {
    // Simple keyword extraction - could be enhanced with NLP
    const words = description.toLowerCase().split(' ');
    return words.filter(word => word.length > 3).slice(0, 3).join(' ');
  }

  private createWorkflowSteps(description: string, tools?: ComposioTool[]) {
    // Create basic workflow steps based on task description
    const steps = [];
    
    if (description.includes('search') || description.includes('find')) {
      steps.push({
        id: 'search-step',
        name: 'Search and Discovery',
        action: 'web_search',
        parameters: { query: this.extractKeywords(description) },
        retry_config: { max_retries: 2, backoff_strategy: 'linear' as const }
      });
    }

    if (description.includes('generate') || description.includes('create')) {
      steps.push({
        id: 'generation-step',
        name: 'Content Generation',
        action: 'code_generation',
        parameters: { 
          task: description,
          language: 'javascript' // Default, could be enhanced
        },
        retry_config: { max_retries: 2, backoff_strategy: 'linear' as const }
      });
    }

    return steps;
  }
}