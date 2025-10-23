/**
 * Create audit log table in Neon via Composio MCP
 * Doctrine-compliant audit logging for promotion activities
 */

import ComposioNeonBridge from '../api/lib/composio-neon-bridge.js';

async function createAuditLogTable() {
  const bridge = new ComposioNeonBridge();

  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS marketing.company_promotion_log (
      log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      process_id VARCHAR(255) NOT NULL,
      batch_id VARCHAR(255),
      unique_id VARCHAR(255) NOT NULL,
      company_name VARCHAR(500),
      promotion_status VARCHAR(50) NOT NULL CHECK (promotion_status IN ('PROMOTED', 'FAILED')),
      error_log JSONB DEFAULT '{}',
      audit_entries JSONB NOT NULL DEFAULT '[]',
      entry_count INTEGER DEFAULT 0,
      log_type VARCHAR(100) DEFAULT 'promotion_audit',
      altitude INTEGER DEFAULT 10000,
      doctrine VARCHAR(50) DEFAULT 'STAMPED',
      doctrine_version VARCHAR(20) DEFAULT 'v2.1.0',
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

      -- Barton Doctrine compliance
      source_system VARCHAR(255) DEFAULT 'outreach_process_manager',
      actor VARCHAR(255) DEFAULT 'api_promote_endpoint',
      method VARCHAR(255) DEFAULT 'composio_mcp_promotion',
      environment VARCHAR(100) DEFAULT 'production',

      -- Indexes for performance
      INDEX idx_promotion_log_process_id (process_id),
      INDEX idx_promotion_log_batch_id (batch_id),
      INDEX idx_promotion_log_unique_id (unique_id),
      INDEX idx_promotion_log_status (promotion_status),
      INDEX idx_promotion_log_created (created_at)
    );

    -- Add comment to table
    COMMENT ON TABLE marketing.company_promotion_log IS 'Audit log for company promotion activities following STAMPED doctrine';

    -- Add column comments
    COMMENT ON COLUMN marketing.company_promotion_log.log_id IS 'Unique log entry identifier';
    COMMENT ON COLUMN marketing.company_promotion_log.process_id IS 'Process identifier for bulk promotion batch';
    COMMENT ON COLUMN marketing.company_promotion_log.batch_id IS 'Batch identifier for grouping related promotions';
    COMMENT ON COLUMN marketing.company_promotion_log.unique_id IS 'Company unique identifier being promoted';
    COMMENT ON COLUMN marketing.company_promotion_log.promotion_status IS 'Status of promotion attempt: PROMOTED or FAILED';
    COMMENT ON COLUMN marketing.company_promotion_log.error_log IS 'JSON object containing error details for failed promotions';
    COMMENT ON COLUMN marketing.company_promotion_log.audit_entries IS 'JSON array of detailed audit trail entries';
    COMMENT ON COLUMN marketing.company_promotion_log.altitude IS 'Barton Doctrine altitude level (10000 = production)';
    COMMENT ON COLUMN marketing.company_promotion_log.doctrine IS 'Compliance doctrine (STAMPED)';
  `;

  try {
    console.log('[AUDIT-TABLE] Creating marketing.company_promotion_log table...');

    const result = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: createTableSQL,
      mode: 'write',
      return_type: 'affected_rows'
    });

    if (result.success) {
      console.log('[AUDIT-TABLE] ✓ Table created successfully');
      console.log(`[AUDIT-TABLE] Tool: ${result.metadata?.tool}`);
      console.log(`[AUDIT-TABLE] Timestamp: ${result.metadata?.timestamp}`);
      return {
        success: true,
        message: 'Audit log table created successfully',
        table_name: 'marketing.company_promotion_log',
        doctrine_compliant: true
      };
    } else {
      console.error('[AUDIT-TABLE] ✗ Failed to create table:', result.error);
      return {
        success: false,
        error: result.error,
        message: 'Failed to create audit log table'
      };
    }
  } catch (error) {
    console.error('[AUDIT-TABLE] ✗ Exception creating table:', error);
    return {
      success: false,
      error: error.message,
      message: 'Exception occurred during table creation'
    };
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  createAuditLogTable()
    .then(result => {
      console.log('\n[RESULT]', JSON.stringify(result, null, 2));
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('\n[ERROR]', error);
      process.exit(1);
    });
}

export default createAuditLogTable;