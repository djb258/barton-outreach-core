/**
 * Doctrine MCP Routes - Barton Doctrine compliant data endpoints
 * Integrates with Neon database via MCP for Builder.io compatibility
 */
import express from "express";
import { neon } from "@neondatabase/serverless";
import dotenv from "dotenv";

dotenv.config();

const router = express.Router();
const sql = neon(process.env.DATABASE_URL || process.env.NEON_DATABASE_URL);

/**
 * Generate Barton-compliant operation ID
 */
function generateOperationId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8).toUpperCase();
  return `DOCTRINE-${timestamp}-${random}`;
}

/**
 * Validate Barton ID format
 */
function validateBartonId(id) {
  if (!id) return false;

  const standardPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  const extendedPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d+\.\d+\.[A-Z0-9]+$/;
  const shortPattern = /^(CMP|PER|CNT|AUDIT|NEON|HIST|DOCTRINE)-/;

  return standardPattern.test(id) || extendedPattern.test(id) || shortPattern.test(id);
}

/**
 * POST /doctrine/steps - Fetch process steps with Barton Doctrine compliance
 */
router.post("/steps", async (req, res) => {
  const { microprocess_id, blueprint_id, metadata } = req.body;
  const operationId = metadata?.unique_id || generateOperationId();

  console.log(`📊 Doctrine steps request: ${operationId}`, {
    microprocess_id,
    blueprint_id,
    timestamp: new Date().toISOString()
  });

  try {
    // Build dynamic query based on available parameters
    let query = `
      SELECT
        unique_id,
        process_id,
        altitude,
        tool_id,
        table_reference,
        created_at,
        updated_at,
        status
      FROM shq_process_registry
      WHERE 1=1
    `;
    const params = [];

    // Add filters based on provided parameters
    if (microprocess_id) {
      query += ` AND microprocess_id = $${params.length + 1}`;
      params.push(microprocess_id);
    }

    if (blueprint_id) {
      query += ` AND blueprint_id = $${params.length + 1}`;
      params.push(blueprint_id);
    }

    // Add Barton ID validation filter
    query += ` AND (
      unique_id ~ '^\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{5}\\.\\d{3}$' OR
      unique_id ~ '^\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{2}\\.\\d{5}\\.\\d+\\.\\d+\\.[A-Z0-9]+$' OR
      unique_id ~ '^(CMP|PER|CNT|AUDIT|NEON|HIST|DOCTRINE)-'
    )`;

    // Order by altitude (descending) then by unique_id
    query += ` ORDER BY altitude DESC, unique_id ASC`;

    console.log(`🔍 Executing query: ${query}`, { params });

    const result = await sql(query, params);

    // Additional validation on the Node.js side
    const validSteps = result.filter(step => validateBartonId(step.unique_id));

    console.log(`✅ Query successful: ${validSteps.length}/${result.length} valid steps`, {
      operationId,
      total_fetched: result.length,
      valid_count: validSteps.length
    });

    // Log to audit table for compliance
    try {
      await sql(`
        INSERT INTO marketing.shq_audit_log (
          unique_id, process_id, status, source, operation_type, record_count, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        operationId,
        'doctrine-steps-fetch',
        'Success',
        'doctrine-mcp-route',
        'query',
        validSteps.length,
        new Date().toISOString()
      ]);
    } catch (auditError) {
      console.warn('⚠️ Audit logging failed:', auditError.message);
    }

    res.json({
      success: true,
      steps: validSteps,
      metadata: {
        operation_id: operationId,
        total_fetched: result.length,
        valid_count: validSteps.length,
        filters: { microprocess_id, blueprint_id },
        timestamp: new Date().toISOString()
      }
    });

  } catch (err) {
    console.error("❌ Doctrine fetch failed:", {
      error: err.message,
      operationId,
      microprocess_id,
      blueprint_id
    });

    // Log error to audit table
    try {
      await sql(`
        INSERT INTO marketing.shq_audit_log (
          unique_id, process_id, status, source, operation_type, error, timestamp
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      `, [
        operationId,
        'doctrine-steps-fetch',
        'Failed',
        'doctrine-mcp-route',
        'query',
        err.message,
        new Date().toISOString()
      ]);
    } catch (auditError) {
      console.warn('⚠️ Error audit logging failed:', auditError.message);
    }

    res.status(500).json({
      success: false,
      error: "Failed to fetch doctrine steps",
      details: err.message,
      operation_id: operationId
    });
  }
});

/**
 * GET /doctrine/health - Health check for doctrine endpoints
 */
router.get("/health", async (req, res) => {
  try {
    // Test database connection
    const testResult = await sql`SELECT 1 as test`;

    res.json({
      success: true,
      status: "healthy",
      database: "connected",
      timestamp: new Date().toISOString(),
      test_result: testResult[0]?.test === 1
    });
  } catch (err) {
    res.status(500).json({
      success: false,
      status: "unhealthy",
      database: "disconnected",
      error: err.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /doctrine/validate - Validate Barton ID format
 */
router.post("/validate", (req, res) => {
  const { unique_id } = req.body;

  if (!unique_id) {
    return res.status(400).json({
      success: false,
      error: "unique_id is required"
    });
  }

  const isValid = validateBartonId(unique_id);

  res.json({
    success: true,
    unique_id,
    valid: isValid,
    patterns: {
      standard: /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/.test(unique_id),
      extended: /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d+\.\d+\.[A-Z0-9]+$/.test(unique_id),
      short_prefix: /^(CMP|PER|CNT|AUDIT|NEON|HIST|DOCTRINE)-/.test(unique_id)
    }
  });
});

export default router;