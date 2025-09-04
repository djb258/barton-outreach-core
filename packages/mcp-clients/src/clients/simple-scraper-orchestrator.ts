/**
 * Simple Scraper Orchestrator - Zero wandering queue consumption
 * Direct processing of the three core queues with simple timestamp updates
 */

import { neon } from '@neondatabase/serverless';
import { ApifyMCPClient, ApifyScrapedData } from './apify-mcp-client';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface CompanyQueueItem {
  company_id: number;
  kind: 'website' | 'linkedin' | 'news';
  url: string;
}

export interface ProfileQueueItem {
  contact_id: number;
  kind: 'profile';
  url: string;
}

export interface EmailQueueItem {
  contact_id: number;
  email: string;
}

export interface ProcessingResult {
  processed: number;
  succeeded: number;
  failed: number;
  errors: string[];
}

export class SimpleScraperOrchestrator {
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
   * Get company crawl queue - exactly as specified
   */
  async getCompanyQueue(): Promise<MCPResponse<CompanyQueueItem[]>> {
    try {
      const queue = await this.sql`
        SELECT company_id, kind, url
        FROM company.next_company_urls_30d
        ORDER BY company_id, kind
      `;

      return {
        success: true,
        data: queue,
        metadata: {
          queue_size: queue.length,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get company queue: ${error.message}`
      };
    }
  }

  /**
   * Get person profile queue - exactly as specified
   */
  async getProfileQueue(): Promise<MCPResponse<ProfileQueueItem[]>> {
    try {
      const queue = await this.sql`
        SELECT contact_id, kind, url
        FROM people.next_profile_urls_30d
      `;

      return {
        success: true,
        data: queue,
        metadata: {
          queue_size: queue.length,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get profile queue: ${error.message}`
      };
    }
  }

  /**
   * Get email verify queue - exactly as specified
   */
  async getEmailQueue(): Promise<MCPResponse<EmailQueueItem[]>> {
    try {
      const queue = await this.sql`
        SELECT contact_id, email
        FROM people.due_email_recheck_30d
      `;

      return {
        success: true,
        data: queue,
        metadata: {
          queue_size: queue.length,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get email queue: ${error.message}`
      };
    }
  }

  /**
   * Process company URLs from queue
   */
  async processCompanyQueue(limit: number = 10): Promise<MCPResponse<ProcessingResult>> {
    try {
      const queueResult = await this.getCompanyQueue();
      
      if (!queueResult.success || !queueResult.data) {
        return {
          success: false,
          error: `Failed to get company queue: ${queueResult.error}`
        };
      }

      const queue = queueResult.data.slice(0, limit);
      const result: ProcessingResult = {
        processed: 0,
        succeeded: 0,
        failed: 0,
        errors: []
      };

      for (const item of queue) {
        result.processed++;
        
        try {
          // Scrape based on kind
          let scrapingResult;
          
          if (item.kind === 'website') {
            scrapingResult = await this.scraper.scrapeWebsite([item.url], true);
          } else if (item.kind === 'linkedin') {
            scrapingResult = await this.scraper.scrapeLinkedIn([item.url], true);
          } else {
            // For news, just mark as checked without scraping
            scrapingResult = { success: true };
          }

          // Mark as checked in database - simple timestamp update
          await this.sql`
            UPDATE company.company
            SET last_site_checked_at = CASE WHEN ${item.kind} = 'website' THEN NOW() ELSE last_site_checked_at END,
                last_linkedin_checked_at = CASE WHEN ${item.kind} = 'linkedin' THEN NOW() ELSE last_linkedin_checked_at END,
                last_news_checked_at = CASE WHEN ${item.kind} = 'news' THEN NOW() ELSE last_news_checked_at END
            WHERE company_id = ${item.company_id}
          `;

          result.succeeded++;

        } catch (error: any) {
          result.failed++;
          result.errors.push(`Company ${item.company_id} ${item.kind}: ${error.message}`);
        }
      }

      return {
        success: true,
        data: result,
        metadata: {
          queue_processed: queue.length,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Company queue processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process contact profiles from queue
   */
  async processProfileQueue(limit: number = 5): Promise<MCPResponse<ProcessingResult>> {
    try {
      const queueResult = await this.getProfileQueue();
      
      if (!queueResult.success || !queueResult.data) {
        return {
          success: false,
          error: `Failed to get profile queue: ${queueResult.error}`
        };
      }

      const queue = queueResult.data.slice(0, limit);
      const result: ProcessingResult = {
        processed: 0,
        succeeded: 0,
        failed: 0,
        errors: []
      };

      // Extract URLs for batch scraping
      const urls = queue.map(item => item.url);
      const scrapingResult = await this.scraper.scrapeLinkedIn(urls, true);

      for (const item of queue) {
        result.processed++;
        
        try {
          // Simple timestamp update - mark profile as checked
          await this.sql`
            UPDATE people.contact
            SET last_profile_checked_at = NOW()
            WHERE contact_id = ${item.contact_id}
          `;

          result.succeeded++;

        } catch (error: any) {
          result.failed++;
          result.errors.push(`Profile ${item.contact_id}: ${error.message}`);
        }
      }

      return {
        success: true,
        data: result,
        metadata: {
          queue_processed: queue.length,
          scraping_success: scrapingResult.success,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Profile queue processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process email verification queue (placeholder - integrate with MillionVerifier)
   */
  async processEmailQueue(limit: number = 20): Promise<MCPResponse<ProcessingResult>> {
    try {
      const queueResult = await this.getEmailQueue();
      
      if (!queueResult.success || !queueResult.data) {
        return {
          success: false,
          error: `Failed to get email queue: ${queueResult.error}`
        };
      }

      const queue = queueResult.data.slice(0, limit);
      const result: ProcessingResult = {
        processed: 0,
        succeeded: 0,
        failed: 0,
        errors: []
      };

      for (const item of queue) {
        result.processed++;
        
        try {
          // Simple timestamp update - mark email as checked
          // In production, integrate with MillionVerifier here
          await this.sql`
            UPDATE people.contact_verification
            SET email_checked_at = NOW()
            WHERE contact_id = ${item.contact_id}
          `;

          result.succeeded++;

        } catch (error: any) {
          result.failed++;
          result.errors.push(`Email ${item.contact_id}: ${error.message}`);
        }
      }

      return {
        success: true,
        data: result,
        metadata: {
          queue_processed: queue.length,
          timestamp: new Date().toISOString(),
          note: 'Email verification placeholder - integrate with MillionVerifier'
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Email queue processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process all three queues in sequence
   */
  async processAllQueues(limits = { company: 10, profile: 5, email: 20 }): Promise<MCPResponse<{
    company_result: ProcessingResult;
    profile_result: ProcessingResult;
    email_result: ProcessingResult;
    total_processed: number;
  }>> {
    try {
      console.log('🔄 Processing company queue...');
      const companyResult = await this.processCompanyQueue(limits.company);
      
      console.log('🔄 Processing profile queue...');
      const profileResult = await this.processProfileQueue(limits.profile);
      
      console.log('🔄 Processing email queue...');
      const emailResult = await this.processEmailQueue(limits.email);

      const totalProcessed = 
        (companyResult.data?.processed || 0) +
        (profileResult.data?.processed || 0) +
        (emailResult.data?.processed || 0);

      return {
        success: true,
        data: {
          company_result: companyResult.data || { processed: 0, succeeded: 0, failed: 0, errors: [] },
          profile_result: profileResult.data || { processed: 0, succeeded: 0, failed: 0, errors: [] },
          email_result: emailResult.data || { processed: 0, succeeded: 0, failed: 0, errors: [] },
          total_processed: totalProcessed
        },
        metadata: {
          timestamp: new Date().toISOString(),
          limits_used: limits
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Queue processing failed: ${error.message}`
      };
    }
  }

  /**
   * Get simple queue status summary
   */
  async getQueueStatus(): Promise<MCPResponse<{
    company_queue_size: number;
    profile_queue_size: number;
    email_queue_size: number;
    total_pending: number;
  }>> {
    try {
      const companyQueue = await this.getCompanyQueue();
      const profileQueue = await this.getProfileQueue();
      const emailQueue = await this.getEmailQueue();

      const companySize = companyQueue.data?.length || 0;
      const profileSize = profileQueue.data?.length || 0;
      const emailSize = emailQueue.data?.length || 0;

      return {
        success: true,
        data: {
          company_queue_size: companySize,
          profile_queue_size: profileSize,
          email_queue_size: emailSize,
          total_pending: companySize + profileSize + emailSize
        },
        metadata: {
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Queue status check failed: ${error.message}`
      };
    }
  }
}