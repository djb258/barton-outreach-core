/**
 * Apollo Ingest Client - Specialized CSV ingestion to marketing_apollo_raw
 * Handles CSV processing and routing through Composio MCP
 */

import { ComposioMCPClient } from './composio-client.js';
import type { MCPResponse, MCPClientConfig } from '../types/mcp-types';

export interface ApolloCsvRecord {
  [key: string]: any;
}

export interface ApolloIngestConfig {
  batchId?: string;
  source?: string;
  blueprintId?: string;
  createdBy?: string;
  dataQualityThreshold?: number;
}

export interface ApolloIngestResult {
  inserted_count: number;
  batch_id: string;
  failed_records: number;
  processing_id: string;
  table_target: string;
}

export class ApolloIngestClient extends ComposioMCPClient {
  constructor(config: MCPClientConfig = {}) {
    super(config);
  }

  /**
   * Parse CSV content into structured records
   */
  private parseCsvContent(csvContent: string): ApolloCsvRecord[] {
    const lines = csvContent.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV must have at least header and one data row');
    }

    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    const records: ApolloCsvRecord[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
      const record: ApolloCsvRecord = {};
      
      headers.forEach((header, index) => {
        record[header] = values[index] || null;
      });

      records.push(record);
    }

    return records;
  }

  /**
   * Validate Apollo CSV record structure
   */
  private validateApolloRecord(record: ApolloCsvRecord): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check for required Apollo fields (common ones)
    const commonFields = ['email', 'first_name', 'last_name', 'company_name'];
    const presentFields = Object.keys(record);
    
    // At least one contact identifier should be present
    if (!record.email && !record.linkedin_url) {
      errors.push('Record must have either email or linkedin_url');
    }

    // Email format validation if present
    if (record.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(record.email)) {
      errors.push('Invalid email format');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Calculate data quality score for a record
   */
  private calculateDataQuality(record: ApolloCsvRecord): number {
    let score = 0;
    let maxScore = 0;

    // Email presence and validity (25 points)
    maxScore += 25;
    if (record.email) {
      if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(record.email)) {
        score += 25;
      } else {
        score += 10; // Has email but invalid format
      }
    }

    // Name completeness (20 points)
    maxScore += 20;
    if (record.first_name && record.last_name) {
      score += 20;
    } else if (record.first_name || record.last_name || record.full_name) {
      score += 10;
    }

    // Company information (20 points)
    maxScore += 20;
    if (record.company_name) {
      score += 20;
    }

    // Contact details (15 points)
    maxScore += 15;
    if (record.phone || record.mobile_phone) {
      score += 15;
    }

    // Professional information (10 points)
    maxScore += 10;
    if (record.title || record.job_title) {
      score += 10;
    }

    // Location information (10 points)
    maxScore += 10;
    if (record.city || record.state || record.country) {
      score += 10;
    }

    return Math.round((score / maxScore) * 100);
  }

  /**
   * Ingest CSV content directly to marketing_apollo_raw table
   */
  async ingestCsvToApollo(
    csvContent: string,
    config: ApolloIngestConfig = {}
  ): Promise<MCPResponse<ApolloIngestResult>> {
    try {
      console.log('🔄 Starting Apollo CSV ingestion...');
      
      // Parse CSV content
      const records = this.parseCsvContent(csvContent);
      console.log(`📊 Parsed ${records.length} records from CSV`);

      // Validate records
      const validRecords: ApolloCsvRecord[] = [];
      const failedRecords: { record: ApolloCsvRecord; errors: string[] }[] = [];

      for (const record of records) {
        const validation = this.validateApolloRecord(record);
        if (validation.valid) {
          validRecords.push(record);
        } else {
          failedRecords.push({ record, errors: validation.errors });
        }
      }

      console.log(`✅ ${validRecords.length} valid records, ❌ ${failedRecords.length} failed validation`);

      if (validRecords.length === 0) {
        return {
          success: false,
          error: 'No valid records to ingest',
          data: {
            inserted_count: 0,
            batch_id: config.batchId || '',
            failed_records: failedRecords.length,
            processing_id: '',
            table_target: 'marketing.marketing_apollo_raw'
          }
        };
      }

      // Prepare batch data
      const batchId = config.batchId || `apollo_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;
      const timestamp = new Date().toISOString();

      // Process each record with quality scoring
      const processedRecords = validRecords.map(record => ({
        raw_data: record,
        source: config.source || 'csv_upload',
        blueprint_id: config.blueprintId || 'apollo_csv_import',
        status: 'ingested',
        inserted_at: timestamp,
        created_by: config.createdBy || 'api_user',
        version: 1,
        data_quality_score: this.calculateDataQuality(record),
        verification_status: 'pending',
        compliance_status: 'pending',
        batch_id: batchId,
        processing_attempts: 0
      }));

      // Execute ingestion through Composio MCP
      console.log('🔌 Executing ingestion via Composio MCP...');
      const result = await this.executeAction('postgresql_bulk_insert', {
        table: 'marketing.marketing_apollo_raw',
        records: processedRecords,
        on_conflict: 'skip', // Skip duplicates
        return_affected: true
      });

      if (result.success) {
        console.log('✅ Apollo CSV ingestion completed successfully');
        return {
          success: true,
          data: {
            inserted_count: validRecords.length,
            batch_id: batchId,
            failed_records: failedRecords.length,
            processing_id: result.data?.execution_id || batchId,
            table_target: 'marketing.marketing_apollo_raw'
          },
          metadata: {
            total_parsed: records.length,
            validation_passed: validRecords.length,
            validation_failed: failedRecords.length,
            average_quality_score: processedRecords.reduce((sum, r) => sum + r.data_quality_score, 0) / processedRecords.length,
            failed_records_details: failedRecords
          }
        };
      } else {
        throw new Error(result.error || 'Composio MCP insertion failed');
      }

    } catch (error: any) {
      console.error('❌ Apollo CSV ingestion failed:', error);
      return {
        success: false,
        error: error.message || 'Apollo CSV ingestion failed',
        data: {
          inserted_count: 0,
          batch_id: config.batchId || '',
          failed_records: 0,
          processing_id: '',
          table_target: 'marketing.marketing_apollo_raw'
        }
      };
    }
  }

  /**
   * Get ingestion status for a batch
   */
  async getIngestionStatus(batchId: string): Promise<MCPResponse<any>> {
    try {
      return await this.executeAction('postgresql_execute_query', {
        query: `
          SELECT 
            batch_id,
            COUNT(*) as total_records,
            COUNT(*) FILTER (WHERE status = 'ingested') as ingested_count,
            COUNT(*) FILTER (WHERE status = 'processed') as processed_count,
            COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
            AVG(data_quality_score) as avg_quality_score,
            MIN(inserted_at) as batch_start,
            MAX(COALESCE(processed_at, inserted_at)) as last_activity
          FROM marketing.marketing_apollo_raw 
          WHERE batch_id = $1
          GROUP BY batch_id
        `,
        parameters: [batchId]
      });
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to get ingestion status: ${error.message || 'Unknown error'}`
      };
    }
  }

  /**
   * List recent ingestion batches
   */
  async listRecentBatches(limit: number = 10): Promise<MCPResponse<any>> {
    try {
      return await this.executeAction('postgresql_execute_query', {
        query: `
          SELECT 
            batch_id,
            source,
            blueprint_id,
            COUNT(*) as record_count,
            AVG(data_quality_score) as avg_quality,
            MIN(inserted_at) as created_at,
            created_by
          FROM marketing.marketing_apollo_raw 
          GROUP BY batch_id, source, blueprint_id, created_by
          ORDER BY MIN(inserted_at) DESC
          LIMIT $1
        `,
        parameters: [limit]
      });
    } catch (error: any) {
      return {
        success: false,
        error: `Failed to list recent batches: ${error.message || 'Unknown error'}`
      };
    }
  }

  /**
   * Validate CSV format before ingestion
   */
  async validateCsvFormat(csvContent: string): Promise<MCPResponse<any>> {
    try {
      const records = this.parseCsvContent(csvContent);
      const sample = records.slice(0, 10); // Validate first 10 records
      
      const validationResults = sample.map((record, index) => ({
        row: index + 2, // +2 because index 0 = row 2 (after header)
        ...this.validateApolloRecord(record),
        quality_score: this.calculateDataQuality(record)
      }));

      const validCount = validationResults.filter(r => r.valid).length;
      const avgQuality = validationResults.reduce((sum, r) => sum + r.quality_score, 0) / validationResults.length;

      return {
        success: true,
        data: {
          total_records: records.length,
          sample_size: sample.length,
          valid_sample: validCount,
          invalid_sample: sample.length - validCount,
          estimated_success_rate: (validCount / sample.length) * 100,
          average_quality_score: avgQuality,
          validation_details: validationResults,
          headers: Object.keys(records[0] || {}),
          recommendations: this.generateRecommendations(validationResults)
        }
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'CSV validation failed'
      };
    }
  }

  /**
   * Generate recommendations for improving CSV quality
   */
  private generateRecommendations(validationResults: any[]): string[] {
    const recommendations: string[] = [];
    const errors = validationResults.flatMap(r => r.errors);
    
    if (errors.some(e => e.includes('email'))) {
      recommendations.push('Ensure all email addresses are properly formatted');
    }
    
    if (errors.some(e => e.includes('linkedin_url'))) {
      recommendations.push('Include LinkedIn URLs for contacts without email addresses');
    }
    
    const avgQuality = validationResults.reduce((sum, r) => sum + r.quality_score, 0) / validationResults.length;
    if (avgQuality < 70) {
      recommendations.push('Consider enriching data with additional contact information');
    }
    
    if (avgQuality < 50) {
      recommendations.push('Data quality is low - review source data before ingestion');
    }

    return recommendations;
  }
}

export default ApolloIngestClient;