/**
 * Schema Scanner Service
 * Extracts metadata from Neon database schemas using Standard Composio MCP Pattern
 * Scans public, intake, and marketing schemas for complete registry
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * Main schema scanning function
 * Returns structured metadata for all tables and columns
 */
export async function scanSchemas() {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[SCHEMA-SCANNER] Starting schema metadata extraction`);

    // Target schemas to scan
    const targetSchemas = ['public', 'intake', 'marketing', 'people', 'shq'];

    // Extract all schema metadata
    const schemaMetadata = await extractSchemaMetadata(bridge, targetSchemas);

    console.log(`[SCHEMA-SCANNER] Extracted metadata for ${schemaMetadata.length} columns across ${targetSchemas.length} schemas`);

    return {
      success: true,
      data: schemaMetadata,
      metadata: {
        schemas_scanned: targetSchemas,
        total_columns: schemaMetadata.length,
        scan_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[SCHEMA-SCANNER] Schema scan failed:', error);
    throw new Error(`Schema scanning failed: ${error.message}`);
  } finally {
    await bridge.close();
  }
}

/**
 * Extract detailed metadata from information_schema
 */
async function extractSchemaMetadata(bridge, targetSchemas) {
  const schemaPlaceholders = targetSchemas.map((_, i) => `$${i + 1}`).join(', ');

  const sql = `
    SELECT
      c.table_schema as schema_name,
      c.table_name,
      c.column_name,
      c.data_type,
      c.is_nullable,
      c.column_default,
      c.character_maximum_length,
      c.numeric_precision,
      c.numeric_scale,
      c.ordinal_position,
      CASE
        WHEN tc.constraint_type = 'PRIMARY KEY' THEN true
        ELSE false
      END as is_primary_key,
      CASE
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN true
        ELSE false
      END as is_foreign_key,
      tc.constraint_name,
      t.table_type
    FROM information_schema.columns c
    LEFT JOIN information_schema.tables t
      ON c.table_schema = t.table_schema
      AND c.table_name = t.table_name
    LEFT JOIN information_schema.key_column_usage kcu
      ON c.table_schema = kcu.table_schema
      AND c.table_name = kcu.table_name
      AND c.column_name = kcu.column_name
    LEFT JOIN information_schema.table_constraints tc
      ON kcu.constraint_name = tc.constraint_name
      AND kcu.table_schema = tc.table_schema
    WHERE c.table_schema IN (${schemaPlaceholders})
    ORDER BY c.table_schema, c.table_name, c.ordinal_position
  `;

  console.log(`[SCHEMA-SCANNER] Querying metadata for schemas: ${targetSchemas.join(', ')}`);

  const result = await bridge.executeSQL(sql, targetSchemas);

  if (!result.success) {
    throw new Error(`Failed to extract schema metadata: ${result.error}`);
  }

  return result.data.rows.map(row => ({
    schema: row.schema_name,
    table: row.table_name,
    column: row.column_name,
    type: row.data_type,
    nullable: row.is_nullable === 'YES',
    default_value: row.column_default,
    max_length: row.character_maximum_length,
    precision: row.numeric_precision,
    scale: row.numeric_scale,
    position: row.ordinal_position,
    primary_key: row.is_primary_key,
    foreign_key: row.is_foreign_key,
    constraint_name: row.constraint_name,
    table_type: row.table_type
  }));
}

/**
 * Get schema statistics for reporting
 */
export async function getSchemaStatistics() {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[SCHEMA-SCANNER] Generating schema statistics`);

    const sql = `
      SELECT
        table_schema as schema_name,
        COUNT(DISTINCT table_name) as table_count,
        COUNT(*) as column_count,
        COUNT(CASE WHEN is_nullable = 'NO' THEN 1 END) as required_columns,
        COUNT(CASE WHEN column_default IS NOT NULL THEN 1 END) as columns_with_defaults
      FROM information_schema.columns
      WHERE table_schema IN ('public', 'intake', 'marketing', 'people', 'shq')
      GROUP BY table_schema
      ORDER BY table_schema
    `;

    const result = await bridge.executeSQL(sql);

    if (!result.success) {
      throw new Error(`Failed to generate schema statistics: ${result.error}`);
    }

    return {
      success: true,
      data: result.data.rows,
      metadata: {
        generated_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[SCHEMA-SCANNER] Statistics generation failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Scan specific table for detailed structure
 */
export async function scanTableStructure(schemaName, tableName) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[SCHEMA-SCANNER] Scanning table structure: ${schemaName}.${tableName}`);

    const sql = `
      SELECT
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length,
        numeric_precision,
        numeric_scale,
        ordinal_position
      FROM information_schema.columns
      WHERE table_schema = $1 AND table_name = $2
      ORDER BY ordinal_position
    `;

    const result = await bridge.executeSQL(sql, [schemaName, tableName]);

    if (!result.success) {
      throw new Error(`Failed to scan table structure: ${result.error}`);
    }

    return {
      success: true,
      data: {
        schema: schemaName,
        table: tableName,
        columns: result.data.rows,
        column_count: result.data.rows.length
      },
      metadata: {
        scan_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error(`[SCHEMA-SCANNER] Table scan failed for ${schemaName}.${tableName}:`, error);
    throw error;
  } finally {
    await bridge.close();
  }
}