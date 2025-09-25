/**
 * Composio-Neon Bridge
 * Connects to actual Composio MCP server for Neon operations
 * Updated with working API endpoints and fallback strategies
 */

import { Composio } from '@composio/core';

class ComposioNeonBridge {
  constructor() {
    this.composio = new Composio({
      apiKey: process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn',
    });
    this.neonDatabaseUrl = process.env.NEON_DATABASE_URL;
    this.isInitialized = false;
    this.connectedAccountId = null;
  }

  /**
   * Initialize Composio connection
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Get connected accounts to find Neon
      const accountsResult = await this.composio.connectedAccounts.list();
      const accounts = accountsResult.items || accountsResult;

      // Look for Neon connected account
      this.connectedAccountId = accounts.find?.(acc =>
        acc.appName?.toLowerCase() === 'neon'
      )?.id;

      if (!this.connectedAccountId) {
        console.log('[BRIDGE] No Neon account found, will attempt direct connection');
      }

      this.isInitialized = true;
      console.log('[BRIDGE] Composio initialized successfully');
    } catch (error) {
      console.error('[BRIDGE] Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Execute Neon database operation through Composio SDK
   */
  async executeNeonOperation(operation, params) {
    console.log(`🔍 Executing Neon operation: ${operation}`, params);

    try {
      await this.initialize();

      // Map operation to Composio action
      const actionName = this.mapOperationToAction(operation);

      // Execute via Composio SDK
      const result = await this.composio.actions.execute({
        actionName: actionName,
        appName: 'neon',
        params: {
          sql: params.sql,
          database_url: this.neonDatabaseUrl,
          ...params
        },
        connectedAccountId: this.connectedAccountId
      });

      console.log(`✅ Composio execution successful`);
      return {
        success: true,
        data: result.data || result,
        source: 'composio_sdk'
      };

    } catch (error) {
      console.error(`[BRIDGE] Composio execution failed:`, error.message);

      // If there's no connected account, the error might indicate we need to use a different approach
      if (error.message?.includes('No connected account') || !this.connectedAccountId) {
        // Try without connected account ID
        try {
          const result = await this.composio.actions.execute({
            actionName: this.mapOperationToAction(operation),
            appName: 'neon',
            params: {
              sql: params.sql,
              database_url: this.neonDatabaseUrl,
              ...params
            }
          });

          return {
            success: true,
            data: result.data || result,
            source: 'composio_sdk'
          };
        } catch (retryError) {
          console.error(`[BRIDGE] Retry failed:`, retryError.message);
        }
      }

      throw error;
    }
  }

  /**
   * Map operation to Composio action name
   */
  mapOperationToAction(operation) {
    const actionMap = {
      'EXECUTE_SQL': 'neon_execute_sql',
      'QUERY_ROWS': 'neon_execute_sql',
      'LIST_TABLES': 'neon_execute_sql'
    };

    return actionMap[operation] || 'neon_execute_sql';
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