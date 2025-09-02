/**
 * Data Router - Shared library for pushing data rows to the Barton Outreach API
 */

import axios, { AxiosResponse } from 'axios';

export interface PushRowsOptions {
  source?: string;
  apiBase?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface DataRow {
  [key: string]: any;
}

export interface IngestResponse {
  success: boolean;
  count: number;
  batch_id?: string;
  errors?: string[];
}

export interface ContactRecord {
  id?: string;
  email?: string;
  name?: string;
  phone?: string;
  company?: string;
  title?: string;
  source?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

/**
 * Push JSON rows to the API ingest endpoint
 */
export async function pushRows(
  rows: DataRow[], 
  options: PushRowsOptions = {}
): Promise<IngestResponse> {
  const {
    source = 'data-router',
    apiBase = process.env.API_BASE || 'http://localhost:3000',
    timeout = 30000,
    headers = {}
  } = options;

  try {
    const response: AxiosResponse<IngestResponse> = await axios.post(
      `${apiBase}/ingest/json`,
      {
        rows,
        metadata: {
          source,
          timestamp: new Date().toISOString(),
          count: rows.length
        }
      },
      {
        timeout,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Failed to push rows: ${error.response?.status} ${error.response?.statusText} - ${
          error.response?.data?.message || error.message
        }`
      );
    }
    throw error;
  }
}

/**
 * Push CSV data to the API ingest endpoint
 */
export async function pushCSV(
  csvContent: string, 
  options: PushRowsOptions = {}
): Promise<IngestResponse> {
  const {
    source = 'data-router',
    apiBase = process.env.API_BASE || 'http://localhost:3000',
    timeout = 30000,
    headers = {}
  } = options;

  try {
    const response: AxiosResponse<IngestResponse> = await axios.post(
      `${apiBase}/ingest/csv`,
      {
        csv: csvContent,
        metadata: {
          source,
          timestamp: new Date().toISOString()
        }
      },
      {
        timeout,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Failed to push CSV: ${error.response?.status} ${error.response?.statusText} - ${
          error.response?.data?.message || error.message
        }`
      );
    }
    throw error;
  }
}

/**
 * Promote staged data to contacts vault
 */
export async function promoteToContacts(
  filter?: Record<string, any>, 
  options: PushRowsOptions = {}
): Promise<{ success: boolean; promoted_count: number }> {
  const {
    apiBase = process.env.API_BASE || 'http://localhost:3000',
    timeout = 30000,
    headers = {}
  } = options;

  try {
    const response = await axios.post(
      `${apiBase}/promote/contacts`,
      { filter },
      {
        timeout,
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Failed to promote contacts: ${error.response?.status} ${error.response?.statusText} - ${
          error.response?.data?.message || error.message
        }`
      );
    }
    throw error;
  }
}

/**
 * Get contacts from the vault
 */
export async function getContacts(
  params: {
    limit?: number;
    offset?: number;
    search?: string;
    source?: string;
  } = {},
  options: PushRowsOptions = {}
): Promise<{
  contacts: ContactRecord[];
  total: number;
  limit: number;
  offset: number;
}> {
  const {
    apiBase = process.env.API_BASE || 'http://localhost:3000',
    timeout = 30000,
    headers = {}
  } = options;

  try {
    const response = await axios.get(
      `${apiBase}/contacts`,
      {
        params,
        timeout,
        headers: {
          'Accept': 'application/json',
          ...headers
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Failed to get contacts: ${error.response?.status} ${error.response?.statusText} - ${
          error.response?.data?.message || error.message
        }`
      );
    }
    throw error;
  }
}

/**
 * Check API health
 */
export async function checkHealth(
  options: PushRowsOptions = {}
): Promise<{ status: string; timestamp: string; version?: string }> {
  const {
    apiBase = process.env.API_BASE || 'http://localhost:3000',
    timeout = 5000,
    headers = {}
  } = options;

  try {
    const response = await axios.get(
      `${apiBase}/health`,
      {
        timeout,
        headers: {
          'Accept': 'application/json',
          ...headers
        }
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `Health check failed: ${error.response?.status} ${error.response?.statusText}`
      );
    }
    throw error;
  }
}

/**
 * Batch process multiple data operations
 */
export async function batchProcess(
  operations: Array<{
    type: 'json' | 'csv' | 'promote';
    data: any;
    options?: PushRowsOptions;
  }>,
  globalOptions: PushRowsOptions = {}
): Promise<Array<{ success: boolean; result?: any; error?: string }>> {
  const results = [];
  
  for (const operation of operations) {
    try {
      let result;
      const opOptions = { ...globalOptions, ...operation.options };
      
      switch (operation.type) {
        case 'json':
          result = await pushRows(operation.data, opOptions);
          break;
        case 'csv':
          result = await pushCSV(operation.data, opOptions);
          break;
        case 'promote':
          result = await promoteToContacts(operation.data, opOptions);
          break;
        default:
          throw new Error(`Unknown operation type: ${operation.type}`);
      }
      
      results.push({ success: true, result });
    } catch (error) {
      results.push({ 
        success: false, 
        error: error instanceof Error ? error.message : String(error)
      });
    }
  }
  
  return results;
}

// Export types for consumers
export type {
  PushRowsOptions,
  DataRow,
  IngestResponse,
  ContactRecord
};