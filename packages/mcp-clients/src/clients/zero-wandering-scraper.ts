/**
 * Zero Wandering Scraper - Production-ready scraper following the simple queue approach
 * Direct consumption of three core queues with simple timestamp updates
 */

import { neon } from '@neondatabase/serverless';
import { ApifyMCPClient } from './apify-mcp-client';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface ScraperStats {
  company_urls_processed: number;
  profiles_processed: number;
  emails_processed: number;
  total_processed: number;
  errors: string[];
}

export class ZeroWanderingScraper {
  private sql: ReturnType<typeof neon>;
  private scraper: ApifyMCPClient;

  constructor(config: MCPClientConfig = {}) {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    if (!connectionString) {
      throw new Error('Database connection required');
    }
    
    this.sql = neon(connectionString);
    this.scraper = new ApifyMCPClient(config);
  }

  /**
   * Process company URLs - the core scraping workflow
   */
  async processCompanyUrls(limit: number = 10): Promise<MCPResponse<ScraperStats>> {
    try {
      // Get queue - exactly as specified
      const queue = await this.sql`
        SELECT company_id, kind, url
        FROM company.next_company_urls_30d
        ORDER BY company_id, kind
        LIMIT ${limit}
      `;

      const stats: ScraperStats = {
        company_urls_processed: 0,
        profiles_processed: 0,
        emails_processed: 0,
        total_processed: 0,
        errors: []
      };

      for (const item of queue as any[]) {
        try {
          // Scrape based on URL kind
          if (item.kind === 'website') {
            await this.scraper.scrapeWebsite([item.url], true);
          } else if (item.kind === 'linkedin') {
            await this.scraper.scrapeLinkedIn([item.url], true);
          }
          // News URLs just get marked as checked

          // Simple timestamp update - removes from queue automatically
          await this.sql`
            UPDATE company.company
            SET last_site_checked_at = CASE WHEN ${item.kind} = 'website' THEN NOW() ELSE last_site_checked_at END,
                last_linkedin_checked_at = CASE WHEN ${item.kind} = 'linkedin' THEN NOW() ELSE last_linkedin_checked_at END,
                last_news_checked_at = CASE WHEN ${item.kind} = 'news' THEN NOW() ELSE last_news_checked_at END
            WHERE company_id = ${item.company_id}
          `;

          stats.company_urls_processed++;

        } catch (error: any) {
          stats.errors.push(`Company ${item.company_id} ${item.kind}: ${error.message}`);
        }
      }

      stats.total_processed = stats.company_urls_processed;

      return {
        success: true,
        data: stats,
        metadata: {
          queue_size: (queue as any[]).length,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Company URL processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process contact profiles
   */
  async processProfiles(limit: number = 5): Promise<MCPResponse<ScraperStats>> {
    try {
      // Get queue - exactly as specified
      const queue = await this.sql`
        SELECT contact_id, kind, url
        FROM people.next_profile_urls_30d
        LIMIT ${limit}
      `;

      const stats: ScraperStats = {
        company_urls_processed: 0,
        profiles_processed: 0,
        emails_processed: 0,
        total_processed: 0,
        errors: []
      };

      // Batch scrape all LinkedIn URLs
      const urls = (queue as any[]).map((item: any) => item.url);
      if (urls.length > 0) {
        await this.scraper.scrapeLinkedIn(urls, true);
      }

      for (const item of queue as any[]) {
        try {
          // Simple timestamp update - removes from queue automatically
          await this.sql`
            UPDATE people.contact
            SET last_profile_checked_at = NOW()
            WHERE contact_id = ${item.contact_id}
          `;

          stats.profiles_processed++;

        } catch (error: any) {
          stats.errors.push(`Profile ${item.contact_id}: ${error.message}`);
        }
      }

      stats.total_processed = stats.profiles_processed;

      return {
        success: true,
        data: stats,
        metadata: {
          queue_size: (queue as any[]).length,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Profile processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process email verifications (placeholder for MillionVerifier integration)
   */
  async processEmails(limit: number = 20): Promise<MCPResponse<ScraperStats>> {
    try {
      // Get queue - exactly as specified
      const queue = await this.sql`
        SELECT contact_id, email
        FROM people.due_email_recheck_30d
        LIMIT ${limit}
      `;

      const stats: ScraperStats = {
        company_urls_processed: 0,
        profiles_processed: 0,
        emails_processed: 0,
        total_processed: 0,
        errors: []
      };

      for (const item of queue as any[]) {
        try {
          // TODO: Integrate with MillionVerifier here
          // For now, just mark as checked
          
          // Simple timestamp update - removes from queue automatically
          await this.sql`
            UPDATE people.contact_verification
            SET email_checked_at = NOW()
            WHERE contact_id = ${item.contact_id}
          `;

          stats.emails_processed++;

        } catch (error: any) {
          stats.errors.push(`Email ${item.contact_id}: ${error.message}`);
        }
      }

      stats.total_processed = stats.emails_processed;

      return {
        success: true,
        data: stats,
        metadata: {
          queue_size: (queue as any[]).length,
          timestamp: new Date().toISOString(),
          note: 'Placeholder - integrate with MillionVerifier'
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Email processing failed: ${error.message}`
      };
    }
  }

  /**
   * Process all three queues in one run
   */
  async processAll(limits = { company: 10, profile: 5, email: 20 }): Promise<MCPResponse<ScraperStats>> {
    try {
      const companyResult = await this.processCompanyUrls(limits.company);
      const profileResult = await this.processProfiles(limits.profile);
      const emailResult = await this.processEmails(limits.email);

      const combinedStats: ScraperStats = {
        company_urls_processed: companyResult.data?.company_urls_processed || 0,
        profiles_processed: profileResult.data?.profiles_processed || 0,
        emails_processed: emailResult.data?.emails_processed || 0,
        total_processed: 0,
        errors: [
          ...(companyResult.data?.errors || []),
          ...(profileResult.data?.errors || []),
          ...(emailResult.data?.errors || [])
        ]
      };

      combinedStats.total_processed = 
        combinedStats.company_urls_processed + 
        combinedStats.profiles_processed + 
        combinedStats.emails_processed;

      return {
        success: true,
        data: combinedStats,
        metadata: {
          timestamp: new Date().toISOString(),
          limits_used: limits
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Combined processing failed: ${error.message}`
      };
    }
  }

  /**
   * Get current queue sizes
   */
  async getQueueStatus(): Promise<MCPResponse<{
    company_queue: number;
    profile_queue: number;
    email_queue: number;
    total_pending: number;
  }>> {
    try {
      const [companyCount] = (await this.sql`SELECT COUNT(*) as count FROM company.next_company_urls_30d`) as any[];
      const [profileCount] = (await this.sql`SELECT COUNT(*) as count FROM people.next_profile_urls_30d`) as any[];
      const [emailCount] = (await this.sql`SELECT COUNT(*) as count FROM people.due_email_recheck_30d`) as any[];

      const status = {
        company_queue: parseInt(companyCount.count),
        profile_queue: parseInt(profileCount.count),
        email_queue: parseInt(emailCount.count),
        total_pending: 0
      };

      status.total_pending = status.company_queue + status.profile_queue + status.email_queue;

      return {
        success: true,
        data: status,
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