/**
 * Composio-Neon Bridge
 * Connects to actual Composio MCP server for Neon operations
 * This is the REAL implementation that calls Composio tools
 */

import fetch from 'node-fetch';
import { spawn } from 'child_process';
import path from 'path';

class ComposioNeonBridge {
  constructor() {
    this.composioBaseUrl = process.env.COMPOSIO_BASE_URL || 'https://backend.composio.dev';
    this.composioApiKey = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
    this.neonDatabaseUrl = process.env.NEON_DATABASE_URL;
    this.mcpServerUrl = process.env.MCP_SERVER_URL || 'http://localhost:3001';
    this.isInitialized = false;
  }

  /**
   * Initialize MCP server connection
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Start MCP server if not running
      await this.startMCPServer();
      this.isInitialized = true;
    } catch (error) {
      console.error('[BRIDGE] Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Start the MCP server process
   */
  async startMCPServer() {
    return new Promise((resolve, reject) => {
      const mcpServerPath = path.join(
        process.cwd(),
        'mcp-servers',
        'github-composio-server.js'
      );

      // Check if server is already running
      fetch(`${this.mcpServerUrl}/health`)
        .then(res => {
          if (res.ok) {
            console.log('[BRIDGE] MCP server already running');
            resolve();
          }
        })
        .catch(() => {
          // Server not running, start it
          console.log('[BRIDGE] Starting MCP server...');

          const mcpProcess = spawn('node', [mcpServerPath], {
            env: {
              ...process.env,
              COMPOSIO_API_KEY: this.composioApiKey,
              COMPOSIO_BASE_URL: this.composioBaseUrl,
              PORT: '3001'
            },
            detached: false
          });

          mcpProcess.stdout.on('data', (data) => {
            console.log(`[MCP Server]: ${data}`);
            if (data.toString().includes('MCP server running')) {
              resolve();
            }
          });

          mcpProcess.stderr.on('data', (data) => {
            console.error(`[MCP Server Error]: ${data}`);
          });

          mcpProcess.on('error', (error) => {
            reject(error);
          });

          // Give server time to start
          setTimeout(resolve, 2000);
        });
    });
  }

  /**
   * Execute Neon database operation through Composio
   */
  async executeNeonOperation(operation, params) {
    await this.initialize();

    const toolName = `NEON_${operation.toUpperCase()}`;

    try {
      // Call Composio API directly for Neon operations
      const response = await fetch(`${this.composioBaseUrl}/api/v1/actions/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.composioApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          appName: 'neon',
          actionName: toolName,
          params: {
            ...params,
            database_url: this.neonDatabaseUrl
          }
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Composio API error: ${error}`);
      }

      const result = await response.json();
      return {
        success: true,
        data: result.data || result,
        metadata: {
          tool: toolName,
          timestamp: new Date().toISOString(),
          composio_request_id: result.request_id
        }
      };
    } catch (error) {
      console.error(`[BRIDGE] Neon operation failed (${operation}):`, error);
      return {
        success: false,
        error: error.message,
        tool: toolName
      };
    }
  }

  /**
   * Insert rows into Neon through Composio
   */
  async insertRows(tableName, rows) {
    const sql = this.buildInsertSQL(tableName, rows);

    return await this.executeNeonOperation('EXECUTE_SQL', {
      sql,
      mode: 'write',
      return_type: 'affected_rows'
    });
  }

  /**
   * Query rows from Neon
   */
  async queryRows(tableName, filter = {}, limit = 100) {
    const sql = this.buildSelectSQL(tableName, filter, limit);

    return await this.executeNeonOperation('EXECUTE_SQL', {
      sql,
      mode: 'read',
      return_type: 'rows'
    });
  }

  /**
   * Validate rows against schema
   */
  async validateSchema(tableName, rows) {
    // Get table schema first
    const schemaSQL = `
      SELECT column_name, data_type, is_nullable, column_default
      FROM information_schema.columns
      WHERE table_name = '${tableName.split('.').pop()}'
      AND table_schema = '${tableName.split('.')[0] || 'public'}'
    `;

    const schemaResult = await this.executeNeonOperation('EXECUTE_SQL', {
      sql: schemaSQL,
      mode: 'read'
    });

    if (!schemaResult.success) {
      return schemaResult;
    }

    // Validate each row against schema
    const errors = [];
    const schema = schemaResult.data.rows || [];

    rows.forEach((row, rowIndex) => {
      schema.forEach(column => {
        const value = row[column.column_name];

        // Check required fields
        if (column.is_nullable === 'NO' && !column.column_default && !value) {
          errors.push({
            row: rowIndex,
            field: column.column_name,
            message: `Required field ${column.column_name} is missing`,
            severity: 'error'
          });
        }

        // Check data types
        if (value !== null && value !== undefined) {
          const typeValid = this.validateDataType(value, column.data_type);
          if (!typeValid) {
            errors.push({
              row: rowIndex,
              field: column.column_name,
              message: `Invalid type for ${column.column_name}: expected ${column.data_type}`,
              severity: 'error'
            });
          }
        }
      });
    });

    return {
      success: errors.length === 0,
      data: {
        valid: errors.length === 0,
        errors,
        schema
      }
    };
  }

  /**
   * Promote rows from one table to another
   */
  async promoteRows(sourceTable, targetTable, filter = {}) {
    // Build promotion SQL with filter
    const whereClause = this.buildWhereClause(filter);
    const sql = `
      INSERT INTO ${targetTable}
      SELECT * FROM ${sourceTable}
      ${whereClause}
      ON CONFLICT (unique_id) DO UPDATE SET
        updated_at = EXCLUDED.updated_at,
        altitude = 'production',
        promoted_at = NOW()
      RETURNING unique_id
    `;

    const result = await this.executeNeonOperation('EXECUTE_SQL', {
      sql,
      mode: 'write',
      return_type: 'rows'
    });

    if (result.success && result.data) {
      const promotedIds = result.data.rows?.map(r => r.unique_id) || [];
      return {
        success: true,
        data: {
          rowsPromoted: promotedIds.length,
          promotedIds,
          slotCreationTriggered: true
        }
      };
    }

    return result;
  }

  /**
   * Build INSERT SQL statement
   */
  buildInsertSQL(tableName, rows) {
    if (!rows || rows.length === 0) {
      throw new Error('No rows to insert');
    }

    const columns = Object.keys(rows[0]);
    const values = rows.map(row => {
      const rowValues = columns.map(col => {
        const value = row[col];
        if (value === null || value === undefined) return 'NULL';
        if (typeof value === 'string') return `'${value.replace(/'/g, "''")}'`;
        if (typeof value === 'object') return `'${JSON.stringify(value).replace(/'/g, "''")}'`;
        return value;
      });
      return `(${rowValues.join(', ')})`;
    });

    return `
      INSERT INTO ${tableName} (${columns.join(', ')})
      VALUES ${values.join(',\n')}
      ON CONFLICT (unique_id) DO UPDATE SET
        updated_at = EXCLUDED.updated_at
      RETURNING unique_id
    `;
  }

  /**
   * Build SELECT SQL statement
   */
  buildSelectSQL(tableName, filter = {}, limit = 100) {
    const whereClause = this.buildWhereClause(filter);
    return `
      SELECT *
      FROM ${tableName}
      ${whereClause}
      ORDER BY created_at DESC
      LIMIT ${limit}
    `;
  }

  /**
   * Build WHERE clause from filter object
   */
  buildWhereClause(filter) {
    if (!filter || Object.keys(filter).length === 0) {
      return '';
    }

    const conditions = Object.entries(filter).map(([key, value]) => {
      if (value === null) return `${key} IS NULL`;
      if (value === true || value === false) return `${key} = ${value}`;
      if (typeof value === 'string') return `${key} = '${value.replace(/'/g, "''")}'`;
      if (typeof value === 'object' && value.$in) {
        const inValues = value.$in.map(v =>
          typeof v === 'string' ? `'${v.replace(/'/g, "''")}'` : v
        );
        return `${key} IN (${inValues.join(', ')})`;
      }
      return `${key} = ${value}`;
    });

    return `WHERE ${conditions.join(' AND ')}`;
  }

  /**
   * Validate data type
   */
  validateDataType(value, expectedType) {
    const type = expectedType.toLowerCase();

    if (type.includes('int') || type.includes('numeric')) {
      return !isNaN(value);
    }
    if (type.includes('bool')) {
      return typeof value === 'boolean';
    }
    if (type.includes('json')) {
      try {
        JSON.parse(typeof value === 'string' ? value : JSON.stringify(value));
        return true;
      } catch {
        return false;
      }
    }
    if (type.includes('timestamp') || type.includes('date')) {
      return !isNaN(Date.parse(value));
    }

    return true; // Default to valid for other types
  }
}

export default ComposioNeonBridge;