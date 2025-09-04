/**
 * Neon MCP Client - Enhanced with email status dot color updates
 */

import { neon } from '@neondatabase/serverless';
import type { MCPClientConfig, MCPResponse } from '../types/mcp-types';

export interface EmailStatusUpdate {
  email: string;
  dot_color: 'green' | 'yellow' | 'red' | 'gray';
  verification_result?: string;
  verification_score?: number;
  last_verified_at: string;
  ttl_expires_at: string;
}

export interface ContactWithStatus {
  contact_id: number;
  email: string;
  name?: string;
  company?: string;
  dot_color: 'green' | 'yellow' | 'red' | 'gray';
  verification_result?: string;
  verification_score?: number;
  last_verified_at?: string;
  needs_verification: boolean;
}

export class NeonMCPClient {
  private connectionString: string;

  constructor(config: MCPClientConfig = {}) {
    this.connectionString = process.env.DATABASE_URL || 
                           process.env.NEON_DATABASE_URL || 
                           config.baseUrl || '';
  }

  /**
   * Update email status dot color
   */
  async updateEmailStatus(updates: EmailStatusUpdate[]): Promise<MCPResponse<any>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured'
        };
      }

      const sql = neon(this.connectionString);
      
      // Use a secure function to update email statuses
      const query = 'SELECT * FROM vault.f_update_email_statuses($1::jsonb)';
      const result = await sql(query, [JSON.stringify(updates)]);

      return {
        success: true,
        data: result[0],
        metadata: {
          updated_count: updates.length,
          source: 'neon-status-update'
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Email status update failed: ${error.message}`
      };
    }
  }

  /**
   * Get contacts that need verification (TTL expired)
   */
  async getContactsNeedingVerification(limit: number = 100): Promise<MCPResponse<ContactWithStatus[]>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured'
        };
      }

      const sql = neon(this.connectionString);
      
      const query = `
        SELECT 
          contact_id,
          email,
          name,
          company,
          COALESCE(email_dot_color, 'gray') as dot_color,
          email_verification_result as verification_result,
          email_verification_score as verification_score,
          email_last_verified_at as last_verified_at,
          CASE 
            WHEN email_last_verified_at IS NULL THEN true
            WHEN email_last_verified_at < NOW() - INTERVAL '30 days' THEN true
            ELSE false
          END as needs_verification
        FROM vault.contacts 
        WHERE 
          email IS NOT NULL 
          AND (
            email_last_verified_at IS NULL 
            OR email_last_verified_at < NOW() - INTERVAL '30 days'
          )
        ORDER BY 
          CASE WHEN email_last_verified_at IS NULL THEN 1 ELSE 2 END,
          email_last_verified_at ASC NULLS FIRST
        LIMIT $1
      `;
      
      const result = await sql(query, [limit]);
      
      const contacts: ContactWithStatus[] = result.map(row => ({
        contact_id: row.contact_id,
        email: row.email,
        name: row.name,
        company: row.company,
        dot_color: row.dot_color as 'green' | 'yellow' | 'red' | 'gray',
        verification_result: row.verification_result,
        verification_score: row.verification_score,
        last_verified_at: row.last_verified_at,
        needs_verification: row.needs_verification
      }));

      return {
        success: true,
        data: contacts,
        metadata: {
          total_needing_verification: contacts.length,
          never_verified: contacts.filter(c => !c.last_verified_at).length,
          expired_ttl: contacts.filter(c => c.last_verified_at && c.needs_verification).length
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get contacts needing verification: ${error.message}`
      };
    }
  }

  /**
   * Ingest scraped data with source tracking
   */
  async ingestScrapedData(
    data: Array<{
      slot: string;
      email: string;
      source_url: string;
      name?: string;
      company?: string;
      title?: string;
    }>,
    source: string
  ): Promise<MCPResponse<any>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured'
        };
      }

      const sql = neon(this.connectionString);
      
      // Convert to format expected by the ingestion function
      const rows = data.map(item => ({
        email: item.email,
        name: item.name,
        company: item.company,
        title: item.title,
        source: source,
        custom_fields: {
          slot: item.slot,
          source_url: item.source_url,
          scraped_at: new Date().toISOString()
        }
      }));

      const query = 'SELECT * FROM intake.f_ingest_json($1::jsonb[], $2::text, $3::text)';
      const batchId = `scraped-${source}-${Date.now()}`;
      
      const result = await sql(query, [JSON.stringify(rows), source, batchId]);

      return {
        success: true,
        data: result[0],
        metadata: {
          batch_id: batchId,
          source: source,
          records_ingested: data.length
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Scraped data ingestion failed: ${error.message}`
      };
    }
  }

  /**
   * Get contact statistics by dot color
   */
  async getContactStats(): Promise<MCPResponse<any>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured'
        };
      }

      const sql = neon(this.connectionString);
      
      const query = `
        SELECT 
          COALESCE(email_dot_color, 'gray') as dot_color,
          COUNT(*) as count,
          COUNT(CASE WHEN email_last_verified_at > NOW() - INTERVAL '30 days' THEN 1 END) as fresh_count,
          COUNT(CASE WHEN email_last_verified_at IS NULL OR email_last_verified_at <= NOW() - INTERVAL '30 days' THEN 1 END) as stale_count
        FROM vault.contacts 
        WHERE email IS NOT NULL
        GROUP BY COALESCE(email_dot_color, 'gray')
        ORDER BY dot_color
      `;
      
      const result = await sql(query);
      
      const stats = {
        total_contacts: result.reduce((sum, row) => sum + row.count, 0),
        by_status: result.reduce((acc, row) => {
          acc[row.dot_color] = {
            total: row.count,
            fresh: row.fresh_count,
            stale: row.stale_count
          };
          return acc;
        }, {} as Record<string, any>),
        freshness: {
          fresh_total: result.reduce((sum, row) => sum + row.fresh_count, 0),
          stale_total: result.reduce((sum, row) => sum + row.stale_count, 0)
        }
      };

      return {
        success: true,
        data: stats,
        metadata: {
          query_time: new Date().toISOString(),
          ttl_threshold: '30 days'
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get contact stats: ${error.message}`
      };
    }
  }

  /**
   * Execute secure promotion with email status preservation
   */
  async promoteWithEmailStatus(loadIds?: number[]): Promise<MCPResponse<any>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured'
        };
      }

      const sql = neon(this.connectionString);
      
      const query = loadIds 
        ? 'SELECT * FROM vault.f_promote_contacts($1::bigint[])'
        : 'SELECT * FROM vault.f_promote_contacts(NULL)';
        
      const params = loadIds ? [loadIds] : [];
      const result = await sql(query, ...params);

      return {
        success: true,
        data: result[0],
        metadata: {
          source: 'neon-promote-with-status',
          load_ids_count: loadIds?.length || 0
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: `Promotion with email status failed: ${error.message}`
      };
    }
  }

  /**
   * Health check for Neon database
   */
  async healthCheck(): Promise<MCPResponse<{ status: string; timestamp: string }>> {
    try {
      if (!this.connectionString) {
        return {
          success: false,
          error: 'No database connection string configured',
          data: {
            status: 'unhealthy',
            timestamp: new Date().toISOString()
          }
        };
      }

      const sql = neon(this.connectionString);
      await sql`SELECT 1`;

      return {
        success: true,
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString()
        },
        metadata: {
          database_type: 'neon',
          connection_verified: true
        }
      };

    } catch (error: any) {
      return {
        success: false,
        error: 'Neon database unhealthy',
        data: {
          status: 'unhealthy',
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  /**
   * Check TTL freshness for specific emails
   */
  checkEmailFreshness(emails: string[], lastVerifiedDates: (string | null)[]): boolean[] {
    const ttlThreshold = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds
    const now = Date.now();

    return emails.map((email, index) => {
      const lastVerified = lastVerifiedDates[index];
      
      if (!lastVerified) return false; // Never verified = not fresh
      
      const verifiedTime = new Date(lastVerified).getTime();
      const age = now - verifiedTime;
      
      return age < ttlThreshold; // Fresh if less than 30 days old
    });
  }
}