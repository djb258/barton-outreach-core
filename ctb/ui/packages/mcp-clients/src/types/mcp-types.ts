/**
 * MCP Client Type Definitions
 */

export interface MCPClientConfig {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  retries?: number;
  scope?: string;
}

export interface MCPResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: Record<string, any>;
}

// Composio Types
export interface ComposioApp {
  name: string;
  key: string;
  description: string;
  category: string;
  logo?: string;
  actions: ComposioAction[];
}

export interface ComposioAction {
  name: string;
  display_name: string;
  description: string;
  parameters: ComposioActionParameter[];
  response_schema?: Record<string, any>;
  app_name: string;
  app_key: string;
  enabled: boolean;
  tags: string[];
}

export interface ComposioActionParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
  default?: any;
  enum?: string[];
}

export interface ComposioTool {
  name: string;
  description: string;
  input_schema: Record<string, any>;
  output_schema?: Record<string, any>;
  category: string;
  tags: string[];
}

export interface ComposioWorkflow {
  id: string;
  name: string;
  description: string;
  steps: ComposioWorkflowStep[];
  triggers: ComposioTrigger[];
  status: 'draft' | 'active' | 'paused';
  created_at: string;
  updated_at: string;
}

export interface ComposioWorkflowStep {
  id: string;
  name: string;
  action: string;
  parameters: Record<string, any>;
  conditions?: Record<string, any>;
  retry_config?: {
    max_retries: number;
    backoff_strategy: 'linear' | 'exponential';
  };
}

export interface ComposioTrigger {
  type: 'webhook' | 'schedule' | 'event';
  config: Record<string, any>;
}

export interface ComposioExecutionResult {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  logs?: string[];
  started_at: string;
  completed_at?: string;
  metadata?: Record<string, any>;
}

export interface ComposioEntity {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive';
  metadata: Record<string, any>;
}

// RefTools Types
export interface RefToolsSearchResult {
  title: string;
  url: string;
  description: string;
  type: 'documentation' | 'tutorial' | 'reference' | 'example';
  language?: string;
  framework?: string;
  score: number;
  last_updated?: string;
}

export interface RefToolsValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
  suggestions?: string[];
  schema_version?: string;
}

export interface RefToolsDocumentation {
  title: string;
  content: string;
  sections: RefToolsSection[];
  metadata: {
    language?: string;
    framework?: string;
    version?: string;
    last_updated?: string;
  };
}

export interface RefToolsSection {
  title: string;
  content: string;
  code_examples?: RefToolsCodeExample[];
  subsections?: RefToolsSection[];
}

export interface RefToolsCodeExample {
  language: string;
  code: string;
  description?: string;
  executable?: boolean;
}

// Orchestrator Types
export interface MCPTask {
  id: string;
  name: string;
  description: string;
  client_type: 'composio' | 'reftools';
  action: string;
  parameters: Record<string, any>;
  dependencies?: string[];
  retry_config?: {
    max_retries: number;
    backoff_ms: number;
  };
}

export interface MCPTaskResult {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
  started_at: string;
  completed_at?: string;
  execution_time_ms?: number;
}

export interface MCPOrchestrationPlan {
  id: string;
  name: string;
  tasks: MCPTask[];
  execution_order: string[];
  parallel_groups?: string[][];
}

export interface MCPServerHealth {
  server_id: string;
  name: string;
  type: 'composio' | 'reftools';
  status: 'healthy' | 'unhealthy' | 'unknown';
  response_time_ms?: number;
  last_check: string;
  error?: string;
}