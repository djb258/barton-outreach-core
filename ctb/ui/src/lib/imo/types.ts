export interface IMOStage {
  id: string;
  name: string;
  status: 'todo' | 'wip' | 'done';
  description?: string;
  tasks?: string[];
}

export interface IMOBucket {
  id: string;
  name: string;
  stages: IMOStage[];
  progress?: {
    done: number;
    wip: number;
    todo: number;
    total: number;
  };
}

export interface IMOManifest {
  meta: {
    app_name: string;
    stage?: string;
    created?: string;
    updated?: string;
  };
  doctrine?: {
    unique_id?: string;
    process_id?: string;
    blueprint_version_hash?: string;
    schema_version?: string;
  };
  buckets: {
    input?: IMOBucket;
    middle?: IMOBucket;
    output?: IMOBucket;
  };
}

export interface IMODiagram {
  type: 'tree' | 'ladder';
  bucket?: 'input' | 'middle' | 'output';
  mermaidCode: string;
}

export interface IMOProvider {
  type: 'anthropic' | 'openai';
  apiKey?: string;
  model?: string;
  available: boolean;
}

export interface IMOLLMRequest {
  provider?: 'anthropic' | 'openai';
  model?: string;
  system?: string;
  prompt: string;
  json?: boolean;
  max_tokens?: number;
}

export interface IMOLLMResponse {
  content: string;
  provider: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}