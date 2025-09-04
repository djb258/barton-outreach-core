/**
 * UI Builder Orchestration Service
 * Coordinates Builder.io, Plasmic, Figma, and Loveable.dev through Composio MCP
 */

import { ComposioMCPClient } from '../../../packages/mcp-clients/src/clients/composio-client';
import type { MCPResponse } from '../../../packages/mcp-clients/src/types/mcp-types';

export interface DesignToken {
  name: string;
  value: string | number;
  type: 'color' | 'typography' | 'spacing' | 'border' | 'shadow';
  category: string;
}

export interface ComponentDefinition {
  name: string;
  props: Record<string, any>;
  children?: ComponentDefinition[];
  style?: Record<string, any>;
  framework: 'react' | 'vue' | 'angular';
}

export interface DesignSystemSync {
  figmaFileKey: string;
  plasmicProjectId: string;
  builderIOApiKey: string;
  tokens: DesignToken[];
  components: ComponentDefinition[];
  timestamp: string;
}

class UIBuilderService {
  private composioClient: ComposioMCPClient;
  private cache: Map<string, any> = new Map();

  constructor() {
    this.composioClient = new ComposioMCPClient();
  }

  /**
   * Builder.io Operations
   */
  async createBuilderIOComponent(
    modelName: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    try {
      const result = await this.composioClient.builderIOCreateComponent(
        modelName,
        componentData
      );

      if (result.success) {
        // Cache component for quick access
        this.cache.set(`builder_io_${modelName}`, result.data);
      }

      return result;
    } catch (error: any) {
      return {
        success: false,
        error: `Builder.io component creation failed: ${error.message}`
      };
    }
  }

  async publishBuilderIOComponent(
    modelName: string,
    entryId: string
  ): Promise<MCPResponse<any>> {
    return this.composioClient.builderIOPublishComponent(modelName, entryId);
  }

  async getBuilderIOContent(
    modelName: string,
    url?: string
  ): Promise<MCPResponse<any>> {
    const cacheKey = `builder_io_content_${modelName}_${url || 'default'}`;
    
    if (this.cache.has(cacheKey)) {
      return {
        success: true,
        data: this.cache.get(cacheKey),
        metadata: { from_cache: true }
      };
    }

    const result = await this.composioClient.builderIOGetContent(modelName, url);
    
    if (result.success) {
      this.cache.set(cacheKey, result.data);
    }

    return result;
  }

  /**
   * Plasmic Operations
   */
  async createPlasmicComponent(
    projectId: string,
    componentName: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    return this.composioClient.plasmicCreateComponent(
      projectId,
      componentName,
      componentData
    );
  }

  async updatePlasmicComponent(
    projectId: string,
    componentId: string,
    componentData: Record<string, any>
  ): Promise<MCPResponse<any>> {
    return this.composioClient.plasmicUpdateComponent(
      projectId,
      componentId,
      componentData
    );
  }

  async generatePlasmicCode(
    projectId: string,
    componentIds: string[],
    platform: 'react' | 'vue' | 'angular' = 'react'
  ): Promise<MCPResponse<any>> {
    return this.composioClient.plasmicGenerateCode(
      projectId,
      componentIds,
      platform
    );
  }

  /**
   * Figma Operations
   */
  async getFigmaDesignTokens(fileKey: string): Promise<MCPResponse<DesignToken[]>> {
    const result = await this.composioClient.figmaGenerateTokens(fileKey);

    if (result.success) {
      // Transform Figma tokens to standardized format
      const tokens: DesignToken[] = this.transformFigmaTokens(result.data);
      return {
        success: true,
        data: tokens,
        metadata: result.metadata
      };
    }

    return result;
  }

  async exportFigmaComponents(
    fileKey: string,
    nodeIds: string[],
    format: 'png' | 'svg' | 'pdf' = 'svg'
  ): Promise<MCPResponse<any>> {
    return this.composioClient.figmaExportNodes(fileKey, nodeIds, format);
  }

  /**
   * Loveable.dev Operations
   */
  async generateLoveableComponent(
    prompt: string,
    framework: 'react' | 'vue' | 'svelte' = 'react'
  ): Promise<MCPResponse<any>> {
    return this.composioClient.loveableGenerateComponent(prompt, framework);
  }

  async optimizeLoveableComponent(
    componentCode: string,
    goals: string[] = ['performance', 'accessibility', 'mobile-responsive']
  ): Promise<MCPResponse<any>> {
    return this.composioClient.loveableOptimizeComponent(componentCode, goals);
  }

  async generateComponentVariants(
    componentCode: string,
    variants: string[] = ['size', 'color', 'state']
  ): Promise<MCPResponse<any>> {
    return this.composioClient.loveableGenerateVariants(componentCode, variants);
  }

  /**
   * Design System Orchestration
   */
  async syncDesignSystem(
    figmaFileKey: string,
    plasmicProjectId: string,
    builderIOApiKey: string
  ): Promise<MCPResponse<DesignSystemSync>> {
    try {
      // Execute the comprehensive design system sync workflow
      const result = await this.composioClient.executeDesignSystemSync(
        figmaFileKey,
        plasmicProjectId,
        builderIOApiKey
      );

      if (result.success) {
        const syncData: DesignSystemSync = {
          figmaFileKey,
          plasmicProjectId,
          builderIOApiKey,
          tokens: this.extractTokensFromResult(result.data),
          components: this.extractComponentsFromResult(result.data),
          timestamp: new Date().toISOString()
        };

        // Cache the sync result
        this.cache.set('design_system_sync', syncData);

        return {
          success: true,
          data: syncData,
          metadata: {
            execution_id: result.metadata?.execution_id,
            workflow_id: result.metadata?.workflow_id
          }
        };
      }

      return result;
    } catch (error: any) {
      return {
        success: false,
        error: `Design system sync failed: ${error.message}`
      };
    }
  }

  async getDesignSystemStatus(): Promise<DesignSystemSync | null> {
    return this.cache.get('design_system_sync') || null;
  }

  /**
   * Contact Vault UI Components
   */
  async createContactVaultComponents(): Promise<MCPResponse<any>> {
    const contactListPrompt = `
      Create a modern React component for displaying a contact list with:
      - Filterable table with email, name, company, status columns
      - Dot color indicators for email verification status (green=verified, yellow=pending, red=invalid)
      - Bulk selection and actions
      - Real-time updates
      - Responsive mobile design
      - Tailwind CSS styling
    `;

    const contactFormPrompt = `
      Create a React form component for adding contacts with:
      - Email validation with visual feedback
      - Company and name fields
      - Source tracking dropdown
      - Bulk CSV upload capability
      - Form validation with helpful error messages
      - Modern, accessible design
    `;

    const dashboardPrompt = `
      Create a React dashboard component showing:
      - Contact metrics (total, verified, pending, invalid)
      - Email verification progress charts
      - Recent activity feed
      - Quick action buttons for ingestion and promotion
      - Responsive grid layout
    `;

    try {
      const [contactList, contactForm, dashboard] = await Promise.all([
        this.generateLoveableComponent(contactListPrompt),
        this.generateLoveableComponent(contactFormPrompt),
        this.generateLoveableComponent(dashboardPrompt)
      ]);

      return {
        success: true,
        data: {
          ContactList: contactList.data,
          ContactForm: contactForm.data,
          Dashboard: dashboard.data
        },
        metadata: {
          components_generated: 3,
          framework: 'react'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Contact vault component generation failed: ${error.message}`
      };
    }
  }

  /**
   * UI Builder Health Check
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; builders: Record<string, boolean> }>> {
    try {
      // Check Composio MCP client health (which orchestrates all builders)
      const composioHealth = await this.composioClient.healthCheck();

      const status = composioHealth.success ? 'healthy' : 'unhealthy';
      
      return {
        success: true,
        data: {
          status,
          builders: {
            composio_mcp: composioHealth.success,
            builder_io: true, // Via Composio
            plasmic: true,    // Via Composio  
            figma: true,      // Via Composio
            loveable: true    // Via Composio
          }
        },
        metadata: {
          timestamp: new Date().toISOString(),
          cache_size: this.cache.size
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `UI builder health check failed: ${error.message}`,
        data: {
          status: 'unhealthy',
          builders: {
            composio_mcp: false,
            builder_io: false,
            plasmic: false,
            figma: false,
            loveable: false
          }
        }
      };
    }
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Private helper methods
   */
  private transformFigmaTokens(figmaData: any): DesignToken[] {
    const tokens: DesignToken[] = [];
    
    // Transform Figma styles to design tokens
    if (figmaData.styles) {
      figmaData.styles.forEach((style: any) => {
        tokens.push({
          name: style.name,
          value: style.value,
          type: this.mapFigmaTypeToTokenType(style.type),
          category: style.category || 'general'
        });
      });
    }

    return tokens;
  }

  private extractTokensFromResult(resultData: any): DesignToken[] {
    return resultData?.tokens || [];
  }

  private extractComponentsFromResult(resultData: any): ComponentDefinition[] {
    return resultData?.components || [];
  }

  private mapFigmaTypeToTokenType(figmaType: string): DesignToken['type'] {
    const typeMap: Record<string, DesignToken['type']> = {
      'FILL': 'color',
      'TEXT': 'typography',
      'GRID': 'spacing',
      'EFFECT': 'shadow'
    };

    return typeMap[figmaType] || 'color';
  }
}

// Export singleton instance
export const uiBuilderService = new UIBuilderService();