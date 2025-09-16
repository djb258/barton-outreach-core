/**
 * Bit.dev MCP Client - Component sharing and version management
 */

import axios, { AxiosInstance } from 'axios';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface BitComponent {
  name: string;
  type: 'react' | 'vue' | 'angular' | 'vanilla';
  template: string;
  props?: Record<string, any>;
  code?: string;
  styles?: string;
  dependencies?: string[];
  description?: string;
  tags?: string[];
}

export interface BitCollection {
  name: string;
  scope: string;
  components: BitComponent[];
  version: string;
  description?: string;
}

export interface BitSyncResult {
  componentId: string;
  version: string;
  status: 'success' | 'failed' | 'skipped';
  url?: string;
  error?: string;
}

export class BitMCPClient {
  private client: AxiosInstance;
  private token: string;
  private scope: string;

  constructor(config: MCPClientConfig = {}) {
    this.token = config.apiKey || process.env.BIT_TOKEN || '';
    this.scope = config.scope || process.env.BIT_SCOPE || 'barton-outreach';
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.bit.dev',
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        'User-Agent': 'barton-outreach-core/1.0.0'
      }
    });
  }

  /**
   * Sync components to Bit.dev collection
   */
  async syncComponents(
    components: BitComponent[],
    collection: string = 'barton-outreach',
    version: string = '1.0.0'
  ): Promise<MCPResponse<BitSyncResult[]>> {
    try {
      if (!this.token) {
        return this.getFallbackComponentSync(components);
      }

      const results: BitSyncResult[] = [];

      // Process components in batches to avoid rate limits
      const batchSize = 5;
      for (let i = 0; i < components.length; i += batchSize) {
        const batch = components.slice(i, i + batchSize);
        const batchResults = await this.processBatch(batch, collection, version);
        results.push(...batchResults);
      }

      const successCount = results.filter(r => r.status === 'success').length;
      const failedCount = results.filter(r => r.status === 'failed').length;

      return {
        success: true,
        data: results,
        metadata: {
          total: components.length,
          success: successCount,
          failed: failedCount,
          collection: `${this.scope}/${collection}`,
          version
        }
      };

    } catch (error: any) {
      return this.handleError(error, 'Component sync failed');
    }
  }

  /**
   * Create a new component in Bit collection
   */
  async createComponent(
    component: BitComponent,
    collection: string,
    version: string = '1.0.0'
  ): Promise<MCPResponse<BitSyncResult>> {
    try {
      if (!this.token) {
        return {
          success: true,
          data: {
            componentId: `${this.scope}/${collection}/${component.name}`,
            version,
            status: 'skipped',
            url: `https://bit.dev/${this.scope}/${collection}/${component.name}`
          },
          metadata: { fallback: true }
        };
      }

      // Generate component code based on type
      const componentCode = this.generateComponentCode(component);
      
      const response = await this.client.post(`/v2/scopes/${this.scope}/collections/${collection}/components`, {
        name: component.name,
        version,
        type: component.type,
        description: component.description || `Auto-generated ${component.type} component`,
        tags: component.tags || ['auto-generated', 'barton-outreach'],
        files: [
          {
            path: `${component.name}.${this.getFileExtension(component.type)}`,
            content: componentCode
          },
          ...(component.styles ? [{
            path: `${component.name}.css`,
            content: component.styles
          }] : [])
        ],
        dependencies: component.dependencies || this.getDefaultDependencies(component.type)
      });

      return {
        success: true,
        data: {
          componentId: response.data.id,
          version: response.data.version,
          status: 'success',
          url: response.data.url
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Component creation failed: ${error.response?.data?.message || error.message}`,
        data: {
          componentId: `${this.scope}/${collection}/${component.name}`,
          version,
          status: 'failed',
          error: error.message
        }
      };
    }
  }

  /**
   * Update an existing component
   */
  async updateComponent(
    componentId: string,
    component: BitComponent,
    version: string
  ): Promise<MCPResponse<BitSyncResult>> {
    try {
      const componentCode = this.generateComponentCode(component);
      
      const response = await this.client.put(`/v2/components/${componentId}/versions/${version}`, {
        description: component.description || `Updated ${component.type} component`,
        tags: component.tags || ['auto-generated', 'barton-outreach'],
        files: [
          {
            path: `${component.name}.${this.getFileExtension(component.type)}`,
            content: componentCode
          }
        ],
        dependencies: component.dependencies || this.getDefaultDependencies(component.type)
      });

      return {
        success: true,
        data: {
          componentId,
          version: response.data.version,
          status: 'success',
          url: response.data.url
        }
      };

    } catch (error: any) {
      return this.handleError(error, 'Component update failed');
    }
  }

  /**
   * Get component from Bit collection
   */
  async getComponent(
    componentId: string,
    version?: string
  ): Promise<MCPResponse<BitComponent>> {
    try {
      const url = version 
        ? `/v2/components/${componentId}/versions/${version}`
        : `/v2/components/${componentId}`;
        
      const response = await this.client.get(url);
      
      const component: BitComponent = {
        name: response.data.name,
        type: response.data.type,
        template: response.data.template || 'react-typescript',
        description: response.data.description,
        tags: response.data.tags,
        dependencies: response.data.dependencies
      };

      return {
        success: true,
        data: component,
        metadata: {
          version: response.data.version,
          url: response.data.url,
          downloads: response.data.downloads
        }
      };

    } catch (error: any) {
      return this.handleError(error, 'Component retrieval failed');
    }
  }

  /**
   * List components in a collection
   */
  async listComponents(
    collection: string,
    page: number = 1,
    limit: number = 20
  ): Promise<MCPResponse<BitComponent[]>> {
    try {
      const response = await this.client.get(`/v2/scopes/${this.scope}/collections/${collection}/components`, {
        params: { page, limit }
      });

      const components: BitComponent[] = response.data.results.map((item: any) => ({
        name: item.name,
        type: item.type,
        template: item.template,
        description: item.description,
        tags: item.tags
      }));

      return {
        success: true,
        data: components,
        metadata: {
          total: response.data.total,
          page,
          limit,
          collection: `${this.scope}/${collection}`
        }
      };

    } catch (error: any) {
      return this.handleError(error, 'Component listing failed');
    }
  }

  /**
   * Health check for Bit.dev service
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      const response = await this.client.get('/v2/user');

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        },
        metadata: {
          user: response.data.username,
          scope: this.scope
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: 'Bit.dev service unhealthy',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  // Private methods
  private async processBatch(
    components: BitComponent[],
    collection: string,
    version: string
  ): Promise<BitSyncResult[]> {
    const results: BitSyncResult[] = [];

    for (const component of components) {
      try {
        const result = await this.createComponent(component, collection, version);
        results.push(result.data!);
      } catch (error: any) {
        results.push({
          componentId: `${this.scope}/${collection}/${component.name}`,
          version,
          status: 'failed',
          error: error.message
        });
      }

      // Rate limiting - wait 200ms between requests
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    return results;
  }

  private generateComponentCode(component: BitComponent): string {
    switch (component.type) {
      case 'react':
        return this.generateReactComponent(component);
      case 'vue':
        return this.generateVueComponent(component);
      case 'angular':
        return this.generateAngularComponent(component);
      default:
        return this.generateReactComponent(component);
    }
  }

  private generateReactComponent(component: BitComponent): string {
    const propsInterface = component.props 
      ? `interface ${component.name}Props {\n${Object.entries(component.props)
          .map(([key, value]) => `  ${key}: ${typeof value};`)
          .join('\n')}\n}\n\n`
      : '';

    const propsParam = component.props ? `props: ${component.name}Props` : '';

    return `${component.code || `import React from 'react';
${component.styles ? `import './${component.name}.css';` : ''}

${propsInterface}export const ${component.name} = (${propsParam}) => {
  return (
    <div className="${component.name.toLowerCase()}">
      {/* Auto-generated component */}
      ${component.props ? Object.keys(component.props).map(key => 
        `<div>{props.${key}}</div>`
      ).join('\n      ') : '<div>Component content</div>'}
    </div>
  );
};

export default ${component.name};`}`;
  }

  private generateVueComponent(component: BitComponent): string {
    return component.code || `<template>
  <div class="${component.name.toLowerCase()}">
    <!-- Auto-generated Vue component -->
    ${component.props ? Object.keys(component.props).map(key => 
      `<div>{{ ${key} }}</div>`
    ).join('\n    ') : '<div>Component content</div>'}
  </div>
</template>

<script>
export default {
  name: '${component.name}',
  props: {
    ${component.props ? Object.entries(component.props).map(([key, value]) => 
      `${key}: ${typeof value === 'string' ? 'String' : 'Object'}`
    ).join(',\n    ') : ''}
  }
}
</script>

${component.styles ? `<style>
${component.styles}
</style>` : ''}`;
  }

  private generateAngularComponent(component: BitComponent): string {
    return component.code || `import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-${component.name.toLowerCase()}',
  template: \`
    <div class="${component.name.toLowerCase()}">
      <!-- Auto-generated Angular component -->
      ${component.props ? Object.keys(component.props).map(key => 
        `<div>{{ ${key} }}</div>`
      ).join('\n      ') : '<div>Component content</div>'}
    </div>
  \`,
  ${component.styles ? `styleUrls: ['./${component.name.toLowerCase()}.component.css']` : ''}
})
export class ${component.name}Component {
  ${component.props ? Object.entries(component.props).map(([key, value]) => 
    `@Input() ${key}: ${typeof value} = ${JSON.stringify(value)};`
  ).join('\n  ') : ''}
}`;
  }

  private getFileExtension(type: string): string {
    switch (type) {
      case 'react': return 'tsx';
      case 'vue': return 'vue';
      case 'angular': return 'ts';
      default: return 'tsx';
    }
  }

  private getDefaultDependencies(type: string): string[] {
    switch (type) {
      case 'react':
        return ['react@^18.0.0', '@types/react@^18.0.0'];
      case 'vue':
        return ['vue@^3.0.0'];
      case 'angular':
        return ['@angular/core@^16.0.0'];
      default:
        return [];
    }
  }

  private getFallbackComponentSync(components: BitComponent[]): MCPResponse<BitSyncResult[]> {
    const results: BitSyncResult[] = components.map((component, index) => ({
      componentId: `${this.scope}/barton-outreach/${component.name}`,
      version: '1.0.0',
      status: 'skipped' as const,
      url: `https://bit.dev/${this.scope}/barton-outreach/${component.name}`
    }));

    return {
      success: true,
      data: results,
      metadata: {
        fallback: true,
        message: 'Bit token not configured - components created locally'
      }
    };
  }

  private handleError(error: any, context: string): MCPResponse {
    return {
      success: false,
      error: `${context}: ${error.response?.data?.message || error.message}`,
      metadata: {
        status_code: error.response?.status,
        timestamp: new Date().toISOString()
      }
    };
  }
}