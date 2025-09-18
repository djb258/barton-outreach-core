/**
 * PLE (Pipeline Logic Engine) Orchestrator
 * Manages the complete data flow: Ingestor → Neon → Apify → PLE → Bit
 */

import { createDefaultConnection } from '../factory/client-factory.js';
import { ApifyMCPClient } from './apify-mcp-client.js';
import { NeonMCPClient } from './neon-mcp-client.js';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface PLEConfig {
  apify?: MCPClientConfig;
  neon?: MCPClientConfig;
  composio?: MCPClientConfig;
  batchSize?: number;
  maxRetries?: number;
  timeout?: number;
}

export interface PLEPipelineResult {
  ingestedCount: number;
  scrapedCount: number;
  promotedCount: number;
  componentsShared: number;
  errors: string[];
  batchId: string;
  duration: number;
}

export interface PLEJobConfig {
  jobId: string;
  source: 'csv' | 'api' | 'manual';
  enableScraping: boolean;
  enablePromotion: boolean;
  enableBitSync: boolean;
  notificationWebhook?: string;
}

export class PLEOrchestrator {
  private composio: any;
  private apify: ApifyMCPClient;
  private neon: NeonMCPClient;
  private config: PLEConfig;

  constructor(config: PLEConfig = {}) {
    this.config = {
      batchSize: 50,
      maxRetries: 3,
      timeout: 300000, // 5 minutes
      ...config
    };

    // Initialize MCP clients with Composio as primary
    this.composio = createDefaultConnection(this.config.composio);
    this.apify = new ApifyMCPClient(this.config.apify);
    this.neon = new NeonMCPClient(this.config.neon);
  }

  /**
   * Execute the complete pipeline: Ingestor → Neon → Apify → PLE → Bit
   */
  async executePipeline(
    data: any[],
    jobConfig: PLEJobConfig
  ): Promise<MCPResponse<PLEPipelineResult>> {
    const startTime = Date.now();
    const result: PLEPipelineResult = {
      ingestedCount: 0,
      scrapedCount: 0,
      promotedCount: 0,
      componentsShared: 0,
      errors: [],
      batchId: jobConfig.jobId,
      duration: 0
    };

    try {
      console.log(`🚀 PLE Pipeline Starting - Job: ${jobConfig.jobId}`);
      console.log(`📊 Input Records: ${data.length}`);

      // Step 1: Ingest data into Neon via Composio MCP
      console.log('📥 Step 1: Ingesting data into Neon...');
      const ingestionResult = await this.ingestToNeon(data, jobConfig.jobId);
      
      if (!ingestionResult.success) {
        result.errors.push(`Ingestion failed: ${ingestionResult.error}`);
        return { success: false, error: 'Pipeline failed at ingestion step', data: result };
      }

      result.ingestedCount = ingestionResult.data?.insertedCount || data.length;
      console.log(`✅ Ingested ${result.ingestedCount} records`);

      // Step 2: Scrape additional data with Apify (if enabled)
      if (jobConfig.enableScraping) {
        console.log('🕷️ Step 2: Scraping additional data with Apify...');
        const scrapingResult = await this.scrapeData(data, jobConfig.jobId);
        
        if (scrapingResult.success) {
          result.scrapedCount = scrapingResult.data?.length || 0;
          console.log(`✅ Scraped ${result.scrapedCount} additional records`);
        } else {
          result.errors.push(`Scraping failed: ${scrapingResult.error}`);
        }
      }

      // Step 3: Promote data using PLE logic (if enabled)
      if (jobConfig.enablePromotion) {
        console.log('⬆️ Step 3: Promoting data with PLE logic...');
        const promotionResult = await this.promoteData(jobConfig.jobId);
        
        if (promotionResult.success) {
          result.promotedCount = promotionResult.data?.promotedCount || 0;
          console.log(`✅ Promoted ${result.promotedCount} records`);
        } else {
          result.errors.push(`Promotion failed: ${promotionResult.error}`);
        }
      }

      // Step 4: Sync components to Bit (if enabled)
      if (jobConfig.enableBitSync) {
        console.log('🔄 Step 4: Syncing components to Bit...');
        const bitSyncResult = await this.syncToBit(jobConfig.jobId);
        
        if (bitSyncResult.success) {
          result.componentsShared = bitSyncResult.data?.sharedCount || 0;
          console.log(`✅ Shared ${result.componentsShared} components to Bit`);
        } else {
          result.errors.push(`Bit sync failed: ${bitSyncResult.error}`);
        }
      }

      // Send notification if webhook provided
      if (jobConfig.notificationWebhook) {
        await this.sendNotification(jobConfig.notificationWebhook, result);
      }

      result.duration = Date.now() - startTime;
      console.log(`🎉 PLE Pipeline Complete - Duration: ${result.duration}ms`);

      return {
        success: true,
        data: result,
        metadata: {
          pipeline: 'ingestor_neon_apify_ple_bit',
          version: '1.0.0',
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      result.duration = Date.now() - startTime;
      result.errors.push(error.message);
      
      console.error('❌ PLE Pipeline Failed:', error);
      
      return {
        success: false,
        error: `Pipeline execution failed: ${error.message}`,
        data: result
      };
    }
  }

  /**
   * Step 1: Ingest data into Neon database
   */
  private async ingestToNeon(
    data: any[],
    batchId: string
  ): Promise<MCPResponse<{ insertedCount: number }>> {
    try {
      // Use Composio MCP to call the database function
      const result = await this.composio.executeAction('neon_function_call', {
        function_name: 'intake.f_ingest_company_csv',
        parameters: [
          JSON.stringify(data),
          batchId
        ]
      });

      if (result.success) {
        return {
          success: true,
          data: {
            insertedCount: result.data?.inserted_count || data.length
          }
        };
      } else {
        throw new Error(result.error || 'Neon ingestion failed');
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Neon ingestion error: ${error.message}`
      };
    }
  }

  /**
   * Step 2: Scrape additional data using Apify
   */
  private async scrapeData(
    data: any[],
    batchId: string
  ): Promise<MCPResponse<any[]>> {
    try {
      const websiteUrls = data
        .map(item => item.website || item.url)
        .filter(Boolean)
        .slice(0, this.config.batchSize); // Limit for API quotas

      if (websiteUrls.length === 0) {
        return {
          success: true,
          data: [],
          metadata: { message: 'No URLs to scrape' }
        };
      }

      const scrapingResult = await this.apify.scrapeWebsite(websiteUrls, true);
      
      if (scrapingResult.success) {
        // Store scraped data back to Neon
        await this.storeScrapedData(scrapingResult.data || [], batchId);
      }

      return scrapingResult;
    } catch (error: any) {
      return {
        success: false,
        error: `Apify scraping error: ${error.message}`
      };
    }
  }

  /**
   * Step 3: Promote data using Pipeline Logic Engine rules
   */
  private async promoteData(
    batchId: string
  ): Promise<MCPResponse<{ promotedCount: number }>> {
    try {
      // Execute PLE promotion logic via Composio MCP
      const result = await this.composio.executeAction('neon_function_call', {
        function_name: 'intake.f_promote_batch',
        parameters: [batchId]
      });

      if (result.success) {
        return {
          success: true,
          data: {
            promotedCount: result.data?.promoted_count || 0
          }
        };
      } else {
        throw new Error(result.error || 'Data promotion failed');
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Promotion error: ${error.message}`
      };
    }
  }

  /**
   * Step 4: Sync components to Bit.dev
   */
  private async syncToBit(
    batchId: string
  ): Promise<MCPResponse<{ sharedCount: number }>> {
    try {
      // Generate components from promoted data
      const componentGenResult = await this.generateComponents(batchId);
      
      if (!componentGenResult.success) {
        return {
          success: false,
          error: componentGenResult.error,
          data: { sharedCount: 0 }
        };
      }

      // Use Composio to sync with Bit.dev
      const result = await this.composio.executeAction('bit_sync_components', {
        components: componentGenResult.data,
        collection: 'barton-outreach',
        version: '1.0.0'
      });

      if (result.success) {
        return {
          success: true,
          data: {
            sharedCount: result.data?.shared_count || 0
          }
        };
      } else {
        throw new Error(result.error || 'Bit sync failed');
      }
    } catch (error: any) {
      return {
        success: false,
        error: `Bit sync error: ${error.message}`
      };
    }
  }

  /**
   * Store scraped data back to Neon
   */
  private async storeScrapedData(scrapedData: any[], batchId: string): Promise<void> {
    try {
      await this.composio.executeAction('neon_function_call', {
        function_name: 'intake.f_store_scraped_data',
        parameters: [
          JSON.stringify(scrapedData),
          batchId
        ]
      });
    } catch (error) {
      console.warn('Failed to store scraped data:', error);
    }
  }

  /**
   * Generate components from promoted data
   */
  private async generateComponents(
    batchId: string
  ): Promise<MCPResponse<any[]>> {
    try {
      // Query promoted data
      const queryResult = await this.composio.executeAction('neon_query_secure', {
        query: 'SELECT * FROM vault.contacts WHERE load_id IN (SELECT load_id FROM intake.raw_loads WHERE batch_id = $1)',
        params: [batchId]
      });

      if (queryResult.success && queryResult.data?.rows) {
        // Generate reusable components from the data
        const components = queryResult.data.rows.map((contact: any, index: number) => ({
          name: `ContactCard${index}`,
          type: 'contact-card',
          props: {
            email: contact.email,
            name: contact.name,
            company: contact.company,
            title: contact.title
          },
          template: 'react-typescript'
        }));

        return {
          success: true,
          data: components
        };
      }

      return {
        success: false,
        error: 'No promoted data found for component generation'
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Component generation error: ${error.message}`
      };
    }
  }

  /**
   * Send notification webhook
   */
  private async sendNotification(webhookUrl: string, result: PLEPipelineResult): Promise<void> {
    try {
      await this.composio.executeAction('webhook_send', {
        url: webhookUrl,
        method: 'POST',
        data: {
          event: 'ple_pipeline_complete',
          result,
          timestamp: new Date().toISOString()
        }
      });
    } catch (error) {
      console.warn('Failed to send notification:', error);
    }
  }

  /**
   * Health check for all pipeline components
   */
  async healthCheck(): Promise<MCPResponse<{ [key: string]: string }>> {
    const health: { [key: string]: string } = {};

    try {
      // Check Composio MCP
      try {
        await this.composio.executeAction('health_check', {});
        health.composio = 'healthy';
      } catch {
        health.composio = 'unhealthy';
      }

      // Check Apify
      const apifyHealth = await this.apify.healthCheck();
      health.apify = apifyHealth.success ? 'healthy' : 'unhealthy';

      // Check Neon
      const neonHealth = await this.neon.healthCheck();
      health.neon = neonHealth.success ? 'healthy' : 'unhealthy';

      return {
        success: true,
        data: health,
        metadata: {
          timestamp: new Date().toISOString(),
          overall: Object.values(health).every(status => status === 'healthy') ? 'healthy' : 'degraded'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Health check failed: ${error.message}`,
        data: health
      };
    }
  }
}