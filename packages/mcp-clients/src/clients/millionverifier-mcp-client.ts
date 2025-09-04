/**
 * MillionVerifier MCP Client - Email verification integration
 */

import axios, { AxiosInstance } from 'axios';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface EmailVerificationResult {
  email: string;
  result: 'valid' | 'invalid' | 'catch_all' | 'unknown' | 'disposable' | 'role';
  score: number; // 0-100
  dot_color: 'green' | 'yellow' | 'red' | 'gray';
  reason?: string;
  verified_at: string;
  ttl_expires_at: string; // 30 days from verification
}

export interface BulkVerificationJob {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  total_emails: number;
  processed_emails: number;
  results?: EmailVerificationResult[];
}

export class MillionVerifierMCPClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: MCPClientConfig = {}) {
    this.apiKey = config.apiKey || process.env.MILLIONVERIFIER_API_KEY || '';
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.millionverifier.com/api/v3',
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'barton-outreach-core/1.0.0'
      }
    });
  }

  /**
   * Verify single email address
   */
  async verifyEmail(email: string): Promise<MCPResponse<EmailVerificationResult>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackVerification(email);
      }

      const response = await this.client.get('/verifyemail', {
        params: {
          api: this.apiKey,
          email: email,
          timeout: 10
        }
      });

      const data = response.data;
      const now = new Date();
      const ttlExpires = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days

      const result: EmailVerificationResult = {
        email: email,
        result: this.normalizeResult(data.result),
        score: this.calculateScore(data.result, data.quality),
        dot_color: this.getDotColor(data.result, data.quality),
        reason: data.reason || data.error,
        verified_at: now.toISOString(),
        ttl_expires_at: ttlExpires.toISOString()
      };

      return {
        success: true,
        data: result,
        metadata: {
          api_credits_used: 1,
          verification_time_ms: data.executiontime,
          source: 'millionverifier'
        }
      };

    } catch (error: any) {
      return this.handleError(error, `Email verification failed for: ${email}`);
    }
  }

  /**
   * Bulk verify emails
   */
  async verifyEmailsBulk(emails: string[]): Promise<MCPResponse<BulkVerificationJob>> {
    try {
      if (!this.apiKey) {
        return this.getFallbackBulkVerification(emails);
      }

      // Create bulk verification job
      const response = await this.client.post('/bulkverify', {
        api: this.apiKey,
        emaillist: emails.join('\n'),
        listname: `barton-bulk-${Date.now()}`
      });

      const jobId = response.data.file_id;

      return {
        success: true,
        data: {
          job_id: jobId,
          status: 'processing',
          total_emails: emails.length,
          processed_emails: 0
        },
        metadata: {
          api_credits_estimated: emails.length,
          source: 'millionverifier-bulk'
        }
      };

    } catch (error: any) {
      return this.handleError(error, 'Bulk email verification failed');
    }
  }

  /**
   * Get bulk verification results
   */
  async getBulkResults(jobId: string): Promise<MCPResponse<BulkVerificationJob>> {
    try {
      if (!this.apiKey) {
        return {
          success: false,
          error: 'API key required for bulk results'
        };
      }

      const response = await this.client.get('/bulkresults', {
        params: {
          api: this.apiKey,
          file_id: jobId
        }
      });

      const data = response.data;
      
      if (data.status === 'completed') {
        // Parse CSV results
        const results = this.parseBulkResults(data.download_url);
        
        return {
          success: true,
          data: {
            job_id: jobId,
            status: 'completed',
            total_emails: results.length,
            processed_emails: results.length,
            results: results
          }
        };
      }

      return {
        success: true,
        data: {
          job_id: jobId,
          status: data.status,
          total_emails: data.total || 0,
          processed_emails: data.processed || 0
        }
      };

    } catch (error: any) {
      return this.handleError(error, `Failed to get bulk results for job: ${jobId}`);
    }
  }

  /**
   * Check if email needs verification (TTL check)
   */
  async needsVerification(email: string, lastVerifiedAt?: string): Promise<boolean> {
    if (!lastVerifiedAt) return true;
    
    const lastVerified = new Date(lastVerifiedAt);
    const ttlExpiry = new Date(lastVerified.getTime() + (30 * 24 * 60 * 60 * 1000)); // 30 days
    const now = new Date();
    
    return now > ttlExpiry;
  }

  /**
   * Health check for MillionVerifier service
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      const response = await this.client.get('/credits', {
        params: { api: this.apiKey }
      });

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        },
        metadata: {
          credits_remaining: response.data.credits,
          api_version: 'v3'
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: 'MillionVerifier service unhealthy',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  // Private methods
  private normalizeResult(result: string): EmailVerificationResult['result'] {
    const normalized = result?.toLowerCase();
    
    switch (normalized) {
      case 'ok':
      case 'valid':
        return 'valid';
      case 'invalid':
      case 'bad':
        return 'invalid';
      case 'catch_all':
      case 'catchall':
        return 'catch_all';
      case 'disposable':
      case 'temporary':
        return 'disposable';
      case 'role':
      case 'role_based':
        return 'role';
      default:
        return 'unknown';
    }
  }

  private calculateScore(result: string, quality?: number): number {
    if (quality !== undefined) return Math.max(0, Math.min(100, quality));
    
    const normalized = this.normalizeResult(result);
    
    switch (normalized) {
      case 'valid': return 90;
      case 'catch_all': return 70;
      case 'role': return 60;
      case 'unknown': return 40;
      case 'disposable': return 20;
      case 'invalid': return 10;
      default: return 0;
    }
  }

  private getDotColor(result: string, quality?: number): EmailVerificationResult['dot_color'] {
    const score = this.calculateScore(result, quality);
    const normalized = this.normalizeResult(result);
    
    if (normalized === 'valid' && score >= 80) return 'green';
    if (normalized === 'catch_all' || (normalized === 'valid' && score >= 60)) return 'yellow';
    if (normalized === 'invalid' || normalized === 'disposable') return 'red';
    return 'gray'; // unknown, role, or low scores
  }

  private async parseBulkResults(downloadUrl: string): Promise<EmailVerificationResult[]> {
    try {
      const response = await axios.get(downloadUrl);
      const csvData = response.data;
      
      // Simple CSV parsing (assumes email,result,quality format)
      const lines = csvData.split('\n').slice(1); // Skip header
      const now = new Date();
      const ttlExpires = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
      
      return lines
        .filter((line: string) => line.trim())
        .map((line: string) => {
          const [email, result, quality] = line.split(',');
          const qualityScore = quality ? parseInt(quality) : undefined;
          
          return {
            email: email?.trim(),
            result: this.normalizeResult(result?.trim()),
            score: this.calculateScore(result?.trim(), qualityScore),
            dot_color: this.getDotColor(result?.trim(), qualityScore),
            verified_at: now.toISOString(),
            ttl_expires_at: ttlExpires.toISOString()
          };
        });
        
    } catch (error) {
      console.error('Failed to parse bulk results:', error);
      return [];
    }
  }

  private getFallbackVerification(email: string): MCPResponse<EmailVerificationResult> {
    // Simple fallback verification logic
    const now = new Date();
    const ttlExpires = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
    
    const isValidFormat = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const isDisposable = /(10minutemail|tempmail|guerrillamail|throwaway)/i.test(email);
    const isRole = /(admin|info|support|sales|contact|noreply|no-reply)/i.test(email);
    
    let result: EmailVerificationResult['result'];
    let score: number;
    
    if (!isValidFormat) {
      result = 'invalid';
      score = 10;
    } else if (isDisposable) {
      result = 'disposable';
      score = 20;
    } else if (isRole) {
      result = 'role';
      score = 60;
    } else {
      result = 'valid';
      score = 75; // Conservative fallback score
    }
    
    const verificationResult: EmailVerificationResult = {
      email,
      result,
      score,
      dot_color: this.getDotColor(result, score),
      reason: 'Fallback verification - no API key',
      verified_at: now.toISOString(),
      ttl_expires_at: ttlExpires.toISOString()
    };

    return {
      success: true,
      data: verificationResult,
      metadata: {
        fallback: true,
        source: 'millionverifier-fallback'
      }
    };
  }

  private getFallbackBulkVerification(emails: string[]): MCPResponse<BulkVerificationJob> {
    return {
      success: true,
      data: {
        job_id: `fallback-${Date.now()}`,
        status: 'completed',
        total_emails: emails.length,
        processed_emails: emails.length,
        results: emails.map(email => this.getFallbackVerification(email).data!)
      },
      metadata: {
        fallback: true,
        source: 'millionverifier-bulk-fallback'
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