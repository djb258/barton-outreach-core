/**
 * RefTools MCP Client - API documentation and reference tools
 */

import axios, { AxiosInstance } from 'axios';
import type {
  MCPClientConfig,
  MCPResponse,
  RefToolsSearchResult,
  RefToolsValidationResult,
  RefToolsDocumentation,
  RefToolsCodeExample
} from '../types/mcp-types';

export class RefToolsMCPClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: MCPClientConfig = {}) {
    this.apiKey = config.apiKey || process.env.REFTOOLS_API_KEY || '';
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.ref.tools/v1',
      timeout: config.timeout || 15000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'barton-outreach-core/1.0.0'
      }
    });
  }

  /**
   * Search for API references and documentation
   */
  async searchReferences(
    query: string,
    language?: string,
    framework?: string,
    limit: number = 10
  ): Promise<MCPResponse<RefToolsSearchResult[]>> {
    try {
      // If no API key, return fallback results
      if (!this.apiKey) {
        return this.getFallbackReferences(query, language);
      }

      const response = await this.client.get('/search', {
        params: {
          query,
          language,
          framework,
          limit
        }
      });

      return {
        success: true,
        data: response.data.results || [],
        metadata: {
          query,
          total_found: response.data.total_count,
          search_time_ms: response.data.search_time_ms
        }
      };
    } catch (error: any) {
      console.warn('RefTools API unavailable, using fallback');
      return this.getFallbackReferences(query, language);
    }
  }

  /**
   * Get detailed documentation for a specific API or framework
   */
  async getDocumentation(
    apiName: string,
    version?: string
  ): Promise<MCPResponse<RefToolsDocumentation>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackDocumentation(apiName);
      }

      const response = await this.client.get(`/docs/${apiName}`, {
        params: version ? { version } : {}
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      return this.getFallbackDocumentation(apiName);
    }
  }

  /**
   * Validate API specification (OpenAPI, AsyncAPI, etc.)
   */
  async validateAPISpecification(
    specification: string,
    specType: 'openapi' | 'asyncapi' | 'graphql' = 'openapi'
  ): Promise<MCPResponse<RefToolsValidationResult>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackValidation(specification, specType);
      }

      const response = await this.client.post('/validate', {
        specification,
        spec_type: specType
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error: any) {
      return this.getFallbackValidation(specification, specType);
    }
  }

  /**
   * Get code examples for specific API endpoints
   */
  async getCodeExamples(
    apiName: string,
    endpoint?: string,
    language?: string
  ): Promise<MCPResponse<RefToolsCodeExample[]>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackCodeExamples(apiName, endpoint, language);
      }

      const response = await this.client.get(`/examples/${apiName}`, {
        params: {
          endpoint,
          language
        }
      });

      return {
        success: true,
        data: response.data.examples || []
      };
    } catch (error: any) {
      return this.getFallbackCodeExamples(apiName, endpoint, language);
    }
  }

  /**
   * Health check for RefTools service
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      const response = await this.client.get('/health');

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: 'RefTools service unavailable',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  // Fallback methods when API is unavailable
  private getFallbackReferences(
    query: string, 
    language?: string
  ): MCPResponse<RefToolsSearchResult[]> {
    const fallbackResults: RefToolsSearchResult[] = [
      {
        title: `${query} Official Documentation`,
        url: `https://docs.example.com/${query.toLowerCase()}`,
        description: `Official documentation for ${query}`,
        type: 'documentation',
        language: language || 'javascript',
        score: 0.9,
        last_updated: '2024-01-01'
      },
      {
        title: `${query} API Reference`,
        url: `https://api-docs.example.com/${query.toLowerCase()}`,
        description: `API reference documentation for ${query}`,
        type: 'reference',
        language: language || 'javascript',
        score: 0.8,
        last_updated: '2024-01-01'
      }
    ];

    return {
      success: true,
      data: fallbackResults,
      metadata: {
        fallback: true,
        query,
        message: 'Using fallback references - RefTools API unavailable'
      }
    };
  }

  private getFallbackDocumentation(apiName: string): MCPResponse<RefToolsDocumentation> {
    const fallbackDoc: RefToolsDocumentation = {
      title: `${apiName} Documentation`,
      content: `This is fallback documentation for ${apiName}. Please configure RefTools API key for full documentation access.`,
      sections: [
        {
          title: 'Getting Started',
          content: `Basic information about ${apiName}`,
          code_examples: [
            {
              language: 'javascript',
              code: `// Example usage of ${apiName}\nconsole.log('Hello from ${apiName}');`,
              description: 'Basic example'
            }
          ]
        }
      ],
      metadata: {
        language: 'javascript',
        framework: apiName.toLowerCase(),
        version: '1.0.0',
        last_updated: '2024-01-01'
      }
    };

    return {
      success: true,
      data: fallbackDoc,
      metadata: {
        fallback: true,
        api_name: apiName
      }
    };
  }

  private getFallbackValidation(
    specification: string,
    specType: string
  ): MCPResponse<RefToolsValidationResult> {
    // Simple basic validation
    let valid = true;
    const errors: string[] = [];
    
    if (!specification.trim()) {
      valid = false;
      errors.push('Specification cannot be empty');
    }

    if (specType === 'openapi') {
      if (!specification.includes('openapi') && !specification.includes('swagger')) {
        errors.push('Does not appear to be a valid OpenAPI specification');
        valid = false;
      }
    }

    return {
      success: true,
      data: {
        valid,
        errors,
        warnings: ['Using fallback validation - RefTools API unavailable'],
        suggestions: ['Configure RefTools API key for comprehensive validation']
      },
      metadata: {
        fallback: true,
        spec_type: specType
      }
    };
  }

  private getFallbackCodeExamples(
    apiName: string,
    endpoint?: string,
    language?: string
  ): MCPResponse<RefToolsCodeExample[]> {
    const examples: RefToolsCodeExample[] = [
      {
        language: language || 'javascript',
        code: `// Example for ${apiName}${endpoint ? ` - ${endpoint}` : ''}\nfetch('https://api.example.com/${endpoint || 'data'}', {\n  method: 'GET',\n  headers: {\n    'Authorization': 'Bearer your-token'\n  }\n}).then(response => response.json());`,
        description: `Basic ${language || 'JavaScript'} example for ${apiName}`,
        executable: false
      }
    ];

    return {
      success: true,
      data: examples,
      metadata: {
        fallback: true,
        api_name: apiName,
        endpoint,
        language
      }
    };
  }
}