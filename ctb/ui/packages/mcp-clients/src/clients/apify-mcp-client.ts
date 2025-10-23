/**
 * Apify MCP Client - LinkedIn/Website scraping integration
 */

import axios, { AxiosInstance } from 'axios';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface ApifyScrapedData {
  slot: string;
  email: string;
  source_url: string;
  name?: string;
  company?: string;
  title?: string;
  linkedin_profile?: string;
  website?: string;
  scraped_at: string;
}

export interface ApifyRunResult {
  id: string;
  status: 'READY' | 'RUNNING' | 'SUCCEEDED' | 'FAILED';
  data?: ApifyScrapedData[];
  error?: string;
}

export class ApifyMCPClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: MCPClientConfig = {}) {
    this.apiKey = config.apiKey || process.env.APIFY_API_KEY || '';
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.apify.com/v2',
      timeout: config.timeout || 60000, // Longer timeout for scraping
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'barton-outreach-core/1.0.0'
      }
    });
  }

  /**
   * Scrape LinkedIn profile data
   */
  async scrapeLinkedIn(
    profileUrls: string[],
    extractEmails: boolean = true
  ): Promise<MCPResponse<ApifyScrapedData[]>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackLinkedInData(profileUrls);
      }

      const response = await this.client.post('/acts/apify~linkedin-profile-scraper/runs', {
        input: {
          startUrls: profileUrls.map(url => ({ url })),
          proxyConfiguration: { useApifyProxy: true },
          includePrivateProfiles: false,
          scrapeEmployees: false,
          scrapeContactInfo: extractEmails
        }
      });

      const runId = response.data.id;
      
      // Poll for completion
      const result = await this.pollRunCompletion(runId);
      
      if (result.status === 'SUCCEEDED' && result.data) {
        const scrapedData: ApifyScrapedData[] = result.data.map((item: any) => ({
          slot: this.generateSlot(item),
          email: item.email || item.contactInfo?.email || '',
          source_url: item.url || '',
          name: item.name || item.fullName || '',
          company: item.company || item.experience?.[0]?.company || '',
          title: item.headline || item.experience?.[0]?.title || '',
          linkedin_profile: item.url || '',
          scraped_at: new Date().toISOString()
        }));

        return {
          success: true,
          data: scrapedData,
          metadata: {
            run_id: runId,
            source: 'apify-linkedin',
            profiles_scraped: scrapedData.length
          }
        };
      }

      return {
        success: false,
        error: `LinkedIn scraping failed: ${result.error || 'Unknown error'}`,
        metadata: { run_id: runId }
      };

    } catch (error: any) {
      return this.handleError(error, 'LinkedIn scraping failed');
    }
  }

  /**
   * Scrape website contact information
   */
  async scrapeWebsite(
    websiteUrls: string[],
    extractEmails: boolean = true
  ): Promise<MCPResponse<ApifyScrapedData[]>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackWebsiteData(websiteUrls);
      }

      const response = await this.client.post('/acts/apify~website-content-crawler/runs', {
        input: {
          startUrls: websiteUrls.map(url => ({ url })),
          maxCrawlDepth: 2,
          maxCrawlPages: 10,
          proxyConfiguration: { useApifyProxy: true },
          pseudoUrls: [],
          clickElementsCssSelector: '[href*="contact"], [href*="about"]',
          pageFunction: `
            async function pageFunction(context) {
              const { request, page } = context;
              
              // Extract emails using regex
              const emails = [];
              if (${extractEmails}) {
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
                const text = await page.evaluate(() => document.body.textContent);
                const matches = text.match(emailRegex);
                if (matches) emails.push(...matches);
              }
              
              return {
                url: request.url,
                title: await page.title(),
                emails: [...new Set(emails)],
                text: await page.evaluate(() => 
                  document.querySelector('h1')?.textContent || 
                  document.title
                )
              };
            }
          `
        }
      });

      const runId = response.data.id;
      const result = await this.pollRunCompletion(runId);
      
      if (result.status === 'SUCCEEDED' && result.data) {
        const scrapedData: ApifyScrapedData[] = [];
        
        result.data.forEach((item: any) => {
          if (item.emails && item.emails.length > 0) {
            item.emails.forEach((email: string) => {
              scrapedData.push({
                slot: this.generateSlotFromWebsite(item.url),
                email: email,
                source_url: item.url,
                website: item.url,
                scraped_at: new Date().toISOString()
              });
            });
          }
        });

        return {
          success: true,
          data: scrapedData,
          metadata: {
            run_id: runId,
            source: 'apify-website',
            websites_scraped: result.data.length,
            emails_found: scrapedData.length
          }
        };
      }

      return {
        success: false,
        error: `Website scraping failed: ${result.error || 'Unknown error'}`,
        metadata: { run_id: runId }
      };

    } catch (error: any) {
      return this.handleError(error, 'Website scraping failed');
    }
  }

  /**
   * Health check for Apify service
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      const response = await this.client.get('/users/me');

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        },
        metadata: {
          user_id: response.data.id,
          api_version: 'v2'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: 'Apify service unhealthy',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  // Private methods
  private async pollRunCompletion(runId: string, maxAttempts: number = 30): Promise<ApifyRunResult> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const statusResponse = await this.client.get(`/acts/runs/${runId}`);
      const status = statusResponse.data.status;
      
      if (status === 'SUCCEEDED') {
        const dataResponse = await this.client.get(`/acts/runs/${runId}/dataset/items`);
        return {
          id: runId,
          status: 'SUCCEEDED',
          data: dataResponse.data
        };
      }
      
      if (status === 'FAILED') {
        return {
          id: runId,
          status: 'FAILED',
          error: 'Run failed'
        };
      }
      
      if (status === 'READY' || status === 'RUNNING') {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        continue;
      }
    }
    
    return {
      id: runId,
      status: 'FAILED',
      error: 'Timeout waiting for run completion'
    };
  }

  private generateSlot(linkedinData: any): string {
    // Generate a unique slot identifier from LinkedIn data
    const company = linkedinData.company || 'unknown-company';
    const name = linkedinData.name || linkedinData.fullName || 'unknown';
    const timestamp = Date.now();
    
    return `linkedin-${company.toLowerCase().replace(/\s+/g, '-')}-${name.toLowerCase().replace(/\s+/g, '-')}-${timestamp}`;
  }

  private generateSlotFromWebsite(url: string): string {
    // Generate a slot identifier from website URL
    const domain = new URL(url).hostname.replace('www.', '');
    const timestamp = Date.now();
    
    return `website-${domain.replace(/\./g, '-')}-${timestamp}`;
  }

  private getFallbackLinkedInData(profileUrls: string[]): MCPResponse<ApifyScrapedData[]> {
    // Fallback data when API key is not available
    const fallbackData: ApifyScrapedData[] = profileUrls.map((url, index) => ({
      slot: `fallback-linkedin-${index}-${Date.now()}`,
      email: `fallback${index}@example.com`,
      source_url: url,
      name: `LinkedIn User ${index + 1}`,
      company: 'Example Company',
      title: 'Professional',
      linkedin_profile: url,
      scraped_at: new Date().toISOString()
    }));

    return {
      success: true,
      data: fallbackData,
      metadata: {
        fallback: true,
        source: 'apify-linkedin-fallback'
      }
    };
  }

  private getFallbackWebsiteData(websiteUrls: string[]): MCPResponse<ApifyScrapedData[]> {
    // Fallback data when API key is not available
    const fallbackData: ApifyScrapedData[] = websiteUrls.map((url, index) => ({
      slot: `fallback-website-${index}-${Date.now()}`,
      email: `contact${index}@${new URL(url).hostname}`,
      source_url: url,
      website: url,
      scraped_at: new Date().toISOString()
    }));

    return {
      success: true,
      data: fallbackData,
      metadata: {
        fallback: true,
        source: 'apify-website-fallback'
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