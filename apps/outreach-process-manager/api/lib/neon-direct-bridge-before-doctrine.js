/**
 * Neon Direct Bridge
 * Direct connection to Neon database for validation operations
 * Uses the Composio MCP server's established connection
 */

import pkg from 'pg';
const { Client } = pkg;

class NeonDirectBridge {
  constructor() {
    this.connectionString = process.env.NEON_DATABASE_URL ||
      'postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/Marketing%20DB?sslmode=require';
    this.client = null;
  }

  /**
   * Connect to Neon database
   */
  async connect() {
    if (this.client) return;

    this.client = new Client({
      connectionString: this.connectionString
    });

    await this.client.connect();
    console.log('✅ Connected to Neon database directly');
  }

  /**
   * Execute SQL query
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
        }
      };
    } catch (error) {
      console.error('❌ SQL execution error:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Fetch pending validation records
   */
  async fetchPendingRecords({ batch_id, limit, status }) {
    const conditions = [`status = $1`];
    const params = [status || 'pending'];

    if (batch_id) {
      conditions.push(`batch_id = $${params.length + 1}`);
      params.push(batch_id);
    }

    const whereClause = `WHERE ${conditions.join(' AND ')}`;

    const sql = `
      SELECT
        unique_id,
        company_name,
        website_url,
        company_linkedin_url,
        facebook_url,
        twitter_url,
        company_state,
        num_employees,
        founded_year,
        batch_id,
        created_at
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
   * Update validation status
   */
  async updateValidationStatus(unique_id, isValid, errorMessage, normalizedData) {
    const sql = isValid
      ? `
        UPDATE intake.company_raw_intake
        SET
          status = 'validated',
          validated = true,
          error_message = NULL,
          validated_at = NOW(),
          updated_at = NOW()
          ${normalizedData ? `, normalized_data = $2` : ''}
        WHERE unique_id = $1
      `
      : `
        UPDATE intake.company_raw_intake
        SET
          status = 'failed',
          validated = false,
          error_message = $2,
          validated_at = NOW(),
          updated_at = NOW()
        WHERE unique_id = $1
      `;

    const params = isValid
      ? normalizedData ? [unique_id, JSON.stringify(normalizedData)] : [unique_id]
      : [unique_id, errorMessage];

    return await this.executeSQL(sql, params);
  }

  /**
   * Log validation attempt to audit table
   */
  async logValidationAttempt({ unique_id, company_name, batch_id, status, error_message, timestamp }) {
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
      unique_id,
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

export default NeonDirectBridge;