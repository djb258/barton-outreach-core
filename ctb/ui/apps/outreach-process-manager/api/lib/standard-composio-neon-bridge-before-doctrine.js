/**
 * Standard Composio-Neon Bridge
 * This is the definitive integration pattern for all Composio/Neon operations
 * Uses MCP server configuration with direct database connection
 */

import pkg from 'pg';
const { Client } = pkg;

class StandardComposioNeonBridge {
  constructor() {
    // Use the same connection string as simple-verification.js
    this.neonDatabaseUrl = 'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';
    this.client = null;
  }

  /**
   * Connect to Neon database using Composio MCP configuration
   */
  async connect() {
    if (this.client) return;

    this.client = new Client({
      connectionString: this.neonDatabaseUrl
    });

    await this.client.connect();
    console.log('✅ Connected to Neon via Composio MCP configuration');
  }

  /**
   * Execute SQL query with parameters
   */
  async executeSQL(sql, params = []) {
    try {
      await this.connect();
      console.log('🔍 Executing SQL:', sql.substring(0, 100) + '...');

      const result = await this.client.query(sql, params);

      return {
        success: true,
        data: {
          rows: result.rows,
          rowCount: result.rowCount,
          fields: result.fields?.map(f => f.name)
        },
        source: 'composio_mcp'
      };
    } catch (error) {
      console.error('❌ SQL execution error:', error.message);
      return {
        success: false,
        error: error.message,
        source: 'composio_mcp'
      };
    }
  }

  /**
   * Fetch pending validation records using actual table structure
   */
  async fetchPendingRecords({ batch_id, limit, status }) {
    const conditions = [];
    const params = [];

    // Add status condition if provided
    if (status) {
      conditions.push(`status = $${params.length + 1}`);
      params.push(status);
    }

    if (batch_id) {
      conditions.push(`batch_id = $${params.length + 1}`);
      params.push(batch_id);
    }

    // If no conditions, get all records (or just add a basic condition)
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

    const sql = `
      SELECT
        id,
        company,
        company_name_for_emails,
        website,
        company_linkedin_url,
        facebook_url,
        twitter_url,
        company_state,
        num_employees,
        founded_year,
        batch_id,
        created_at,
        status,
        error_message
      FROM intake.company_raw_intake
      ${whereClause}
      ORDER BY created_at ASC
      LIMIT $${params.length + 1}
    `;

    params.push(limit || 100);

    const result = await this.executeSQL(sql, params);
    return result.success ? result.data.rows : [];
  }

  /**
   * Update validation status for a record using actual table structure
   */
  async updateValidationStatus(recordId, isValid, errorMessage, normalizedData) {
    const sql = isValid
      ? `
        UPDATE intake.company_raw_intake
        SET
          status = 'validated',
          error_message = NULL,
          updated_at = NOW(),
          processed_at = NOW()
        WHERE id = $1
      `
      : `
        UPDATE intake.company_raw_intake
        SET
          status = 'failed',
          error_message = $2,
          updated_at = NOW(),
          processed_at = NOW()
        WHERE id = $1
      `;

    const params = isValid ? [recordId] : [recordId, errorMessage];

    return await this.executeSQL(sql, params);
  }

  /**
   * Log validation attempt to audit table using actual table structure
   */
  async logValidationAttempt({ record_id, company_name, batch_id, status, error_message, timestamp }) {
    const sql = `
      INSERT INTO marketing.company_audit_log (
        unique_id,
        company_name,
        batch_id,
        process_id,
        altitude,
        status,
        errors,
        timestamp,
        source,
        created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, NOW())
    `;

    const params = [
      record_id?.toString() || 'unknown',
      company_name,
      batch_id || null,
      'Validate Company Data',
      10000,
      status,
      error_message ? JSON.stringify([error_message]) : '[]',
      timestamp,
      'validator-step-2'
    ];

    return await this.executeSQL(sql, params);
  }

  /**
   * Close database connection
   */
  async close() {
    if (this.client) {
      await this.client.end();
      this.client = null;
      console.log('🔚 Neon connection closed');
    }
  }
}

export default StandardComposioNeonBridge;