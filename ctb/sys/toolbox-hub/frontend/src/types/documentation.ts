export interface DocumentationPage {
  id: string;
  title: string;
  slug: string;
  content: string;
  category: 'overview' | 'tool' | 'api' | 'process' | 'reference';
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ProcessDiagram {
  id: string;
  name: string;
  description: string;
  diagram_type: 'flowchart' | 'sequence' | 'architecture';
  mermaid_code: string;
  tools_involved: string[];
  created_at: string;
}

export interface ApiEndpoint {
  id: string;
  tool_id: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  request_schema?: Record<string, any>;
  response_schema?: Record<string, any>;
}
