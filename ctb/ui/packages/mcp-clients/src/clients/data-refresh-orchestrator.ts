/**
 * Data Refresh Orchestrator - Simple queue-based scraper integration
 * Zero wandering: Direct consumption of company/profile/email queues with timestamp updates
 */

import { neon } from '@neondatabase/serverless';
import { ApifyMCPClient, ApifyScrapedData } from './apify-mcp-client';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface RefreshBatch {
  company_id?: number;
  contact_id?: number;
  batch_group: number;
  kind: 'website' | 'linkedin' | 'news' | 'profile';
  url: string;
}

export interface RefreshResult {
  processed: number;
  succeeded: number;
  failed: number;
  errors: string[];
  details: any[];
}

export interface SystemStatus {
  company_urls_due: number;
  profile_urls_due: number;
  email_verifications_due: number;
  renewal_companies: number;
  unprocessed_signals: number;
}

export class DataRefreshOrchestrator {
  private sql: any;
  private scraper: ApifyMCPClient;

  constructor(config: MCPClientConfig = {}) {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    if (!connectionString) {
      throw new Error('No database connection string found');
    }
    
    this.sql = neon(connectionString);
    this.scraper = new ApifyMCPClient(config);
  }

  /**
   * Get comprehensive system refresh status
   */
  async getSystemStatus(): Promise<MCPResponse<SystemStatus>> {
    try {
      const statusResult = await this.sql`SELECT * FROM admin.get_refresh_status()`;
      
      const status: SystemStatus = {
        company_urls_due: 0,
        profile_urls_due: 0, 
        email_verifications_due: 0,
        renewal_companies: 0,
        unprocessed_signals: 0
      };

      statusResult.forEach((item: any) => {
        switch (item.metric) {
          case 'Company URLs Due':
            status.company_urls_due = parseInt(item.count);
            break;
          case 'Contact Profiles Due':
            status.profile_urls_due = parseInt(item.count);
            break;
          case 'Email Verifications Due':
            status.email_verifications_due = parseInt(item.count);
            break;
          case 'Companies in Renewal Window':
            status.renewal_companies = parseInt(item.count);
            break;
          case 'Unprocessed BIT Signals':
            status.unprocessed_signals = parseInt(item.count);
            break;
        }
      });

      return {
        success: true,
        data: status,
        metadata: {
          timestamp: new Date().toISOString(),
          source: 'database-refresh-status'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get system status: ${error.message}`
      };
    }
  }

  /**
   * Process a batch of company URLs (website, LinkedIn, news)
   */
  async processCompanyUrlBatch(batchGroup: number = 1): Promise<MCPResponse<RefreshResult>> {
    try {
      // Get the batch from database
      const batch = await this.sql`
        SELECT company_id, kind, url 
        FROM company.vw_next_url_batch 
        WHERE batch_group = ${batchGroup}
        ORDER BY company_id, kind
      `;

      if (batch.length === 0) {
        return {
          success: true,
          data: {
            processed: 0,
            succeeded: 0,
            failed: 0,
            errors: [],
            details: []
          },
          metadata: {
            message: `No URLs found in batch ${batchGroup}`,
            batch_group: batchGroup
          }
        };
      }

      const result: RefreshResult = {
        processed: 0,
        succeeded: 0,
        failed: 0,
        errors: [],
        details: []
      };

      // Group URLs by type for efficient scraping
      const urlsByType = {
        website: [] as any[],
        linkedin: [] as any[],
        news: [] as any[]
      };

      batch.forEach((item: any) => {
        if (urlsByType[item.kind as keyof typeof urlsByType]) {
          urlsByType[item.kind as keyof typeof urlsByType].push(item);
        }
      });

      // Process website URLs
      if (urlsByType.website.length > 0) {
        const websiteUrls = urlsByType.website.map(item => item.url);
        const websiteResults = await this.scraper.scrapeWebsite(websiteUrls, true);
        
        for (const item of urlsByType.website) {
          result.processed++;
          
          if (websiteResults.success) {
            // Mark as checked in database
            await this.sql`SELECT * FROM company.mark_company_page_checked(${item.company_id}, 'website')`;
            result.succeeded++;
            
            // Store scraped data if emails found
            if (websiteResults.data && websiteResults.data.length > 0) {
              const emailsFound = websiteResults.data.filter(d => d.source_url === item.url);
              result.details.push({
                company_id: item.company_id,
                type: 'website',
                url: item.url,
                emails_found: emailsFound.length,
                data: emailsFound
              });
            }
          } else {
            result.failed++;
            result.errors.push(`Website scraping failed for company ${item.company_id}: ${websiteResults.error}`);
          }
        }
      }

      // Process LinkedIn URLs  
      if (urlsByType.linkedin.length > 0) {
        const linkedinUrls = urlsByType.linkedin.map(item => item.url);
        const linkedinResults = await this.scraper.scrapeLinkedIn(linkedinUrls, true);
        
        for (const item of urlsByType.linkedin) {
          result.processed++;
          
          if (linkedinResults.success) {
            await this.sql`SELECT * FROM company.mark_company_page_checked(${item.company_id}, 'linkedin')`;
            result.succeeded++;
            
            if (linkedinResults.data && linkedinResults.data.length > 0) {
              const profilesFound = linkedinResults.data.filter(d => d.source_url === item.url);
              result.details.push({
                company_id: item.company_id,
                type: 'linkedin',
                url: item.url,
                profiles_found: profilesFound.length,
                data: profilesFound
              });
            }
          } else {
            result.failed++;
            result.errors.push(`LinkedIn scraping failed for company ${item.company_id}: ${linkedinResults.error}`);
          }
        }
      }

      // Process news URLs (mark as checked without scraping for now)
      if (urlsByType.news.length > 0) {
        for (const item of urlsByType.news) {
          result.processed++;
          
          try {
            await this.sql`SELECT * FROM company.mark_company_page_checked(${item.company_id}, 'news')`;
            result.succeeded++;
            result.details.push({
              company_id: item.company_id,
              type: 'news',
              url: item.url,
              status: 'marked_as_checked'
            });
          } catch (error: any) {
            result.failed++;
            result.errors.push(`Failed to mark news URL as checked for company ${item.company_id}: ${error.message}`);
          }
        }
      }

      return {
        success: true,
        data: result,
        metadata: {
          batch_group: batchGroup,
          timestamp: new Date().toISOString(),
          batch_size: batch.length
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Company URL batch processing failed: ${error.message}`,
        data: {
          processed: 0,
          succeeded: 0, 
          failed: 0,
          errors: [error.message],
          details: []
        }
      };
    }
  }

  /**
   * Process a batch of contact profile URLs
   */
  async processProfileBatch(batchGroup: number = 1): Promise<MCPResponse<RefreshResult>> {
    try {
      // Get the profile batch from database
      const batch = await this.sql`
        SELECT contact_id, full_name, email, url
        FROM people.vw_next_profile_batch 
        WHERE batch_group = ${batchGroup}
        ORDER BY contact_id
      `;

      if (batch.length === 0) {
        return {
          success: true,
          data: {
            processed: 0,
            succeeded: 0,
            failed: 0,
            errors: [],
            details: []
          },
          metadata: {
            message: `No profiles found in batch ${batchGroup}`,
            batch_group: batchGroup
          }
        };
      }

      const result: RefreshResult = {
        processed: 0,
        succeeded: 0,
        failed: 0,
        errors: [],
        details: []
      };

      // Extract LinkedIn URLs for scraping
      const linkedinUrls = batch.map((item: any) => item.url);
      const scrapingResults = await this.scraper.scrapeLinkedIn(linkedinUrls, true);

      // Process each profile
      for (const item of batch) {
        result.processed++;
        
        try {
          // Mark profile as checked
          await this.sql`SELECT * FROM people.mark_contact_profile_checked(${item.contact_id})`;
          
          // If scraping was successful, store additional data
          if (scrapingResults.success && scrapingResults.data) {
            const profileData = scrapingResults.data.find(d => d.source_url === item.url);
            
            if (profileData) {
              // Update contact with scraped title if available
              if (profileData.title && profileData.title !== item.title) {
                await this.sql`
                  UPDATE people.contact 
                  SET title = ${profileData.title}, updated_at = NOW()
                  WHERE contact_id = ${item.contact_id}
                `;
              }

              // Update email verification if new email found
              if (profileData.email && profileData.email !== item.email) {
                await this.sql`
                  SELECT * FROM people.mark_email_verified(${item.contact_id}, ${item.url})
                `;
              }
            }
          }
          
          result.succeeded++;
          result.details.push({
            contact_id: item.contact_id,
            full_name: item.full_name,
            url: item.url,
            status: 'updated',
            scraped_data: scrapingResults.success ? 
              scrapingResults.data?.find(d => d.source_url === item.url) : null
          });

        } catch (error: any) {
          result.failed++;
          result.errors.push(`Profile update failed for ${item.full_name}: ${error.message}`);
        }
      }

      return {
        success: true,
        data: result,
        metadata: {
          batch_group: batchGroup,
          timestamp: new Date().toISOString(),
          batch_size: batch.length,
          scraping_success: scrapingResults.success
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Profile batch processing failed: ${error.message}`,
        data: {
          processed: 0,
          succeeded: 0,
          failed: 0,
          errors: [error.message],
          details: []
        }
      };
    }
  }

  /**
   * Auto-process all pending batches up to a limit
   */
  async processAllPendingBatches(maxBatches: number = 3): Promise<MCPResponse<{
    company_batches_processed: number;
    profile_batches_processed: number;
    total_company_urls: number;
    total_profiles: number;
    errors: string[];
  }>> {
    try {
      const results = {
        company_batches_processed: 0,
        profile_batches_processed: 0,
        total_company_urls: 0,
        total_profiles: 0,
        errors: [] as string[]
      };

      // Process company URL batches
      const companyBatches = await this.sql`
        SELECT DISTINCT batch_group 
        FROM company.vw_next_url_batch 
        ORDER BY batch_group 
        LIMIT ${maxBatches}
      `;

      for (const batch of companyBatches) {
        const batchResult = await this.processCompanyUrlBatch(batch.batch_group);
        results.company_batches_processed++;
        
        if (batchResult.success && batchResult.data) {
          results.total_company_urls += batchResult.data.processed;
          results.errors.push(...batchResult.data.errors);
        } else {
          results.errors.push(`Company batch ${batch.batch_group} failed: ${batchResult.error}`);
        }

        // Small delay between batches to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      // Process profile batches
      const profileBatches = await this.sql`
        SELECT DISTINCT batch_group 
        FROM people.vw_next_profile_batch 
        ORDER BY batch_group 
        LIMIT ${maxBatches}
      `;

      for (const batch of profileBatches) {
        const batchResult = await this.processProfileBatch(batch.batch_group);
        results.profile_batches_processed++;
        
        if (batchResult.success && batchResult.data) {
          results.total_profiles += batchResult.data.processed;
          results.errors.push(...batchResult.data.errors);
        } else {
          results.errors.push(`Profile batch ${batch.batch_group} failed: ${batchResult.error}`);
        }

        // Small delay between batches
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      return {
        success: true,
        data: results,
        metadata: {
          timestamp: new Date().toISOString(),
          max_batches_limit: maxBatches,
          processing_complete: results.company_batches_processed === 0 && results.profile_batches_processed === 0
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Auto-processing failed: ${error.message}`
      };
    }
  }

  /**
   * Health check for the entire data refresh system
   */
  async healthCheck(): Promise<MCPResponse<{
    database: boolean;
    scraper: boolean;
    system_status: SystemStatus;
    recommendations: string[];
  }>> {
    try {
      const results = {
        database: false,
        scraper: false,
        system_status: {} as SystemStatus,
        recommendations: [] as string[]
      };

      // Test database connection
      try {
        await this.sql`SELECT 1`;
        results.database = true;
      } catch {
        results.database = false;
        results.recommendations.push('Database connection failed - check connection string');
      }

      // Test scraper service
      const scraperHealth = await this.scraper.healthCheck();
      results.scraper = scraperHealth.success;
      
      if (!scraperHealth.success) {
        results.recommendations.push('Scraper service unavailable - check Apify API key');
      }

      // Get system status
      const statusResult = await this.getSystemStatus();
      if (statusResult.success && statusResult.data) {
        results.system_status = statusResult.data;
        
        // Add recommendations based on system status
        if (statusResult.data.company_urls_due > 0) {
          results.recommendations.push(`${statusResult.data.company_urls_due} company URLs need refresh`);
        }
        if (statusResult.data.profile_urls_due > 0) {
          results.recommendations.push(`${statusResult.data.profile_urls_due} contact profiles need refresh`);
        }
        if (statusResult.data.email_verifications_due > 0) {
          results.recommendations.push(`${statusResult.data.email_verifications_due} emails need verification`);
        }
        if (statusResult.data.unprocessed_signals > 0) {
          results.recommendations.push(`${statusResult.data.unprocessed_signals} BIT signals need processing`);
        }
      }

      const overallHealth = results.database && results.scraper;

      return {
        success: overallHealth,
        data: results,
        metadata: {
          timestamp: new Date().toISOString(),
          overall_health: overallHealth ? 'healthy' : 'degraded'
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Health check failed: ${error.message}`
      };
    }
  }
}