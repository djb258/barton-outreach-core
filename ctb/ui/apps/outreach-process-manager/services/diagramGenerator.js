/**
 * Diagram Generator Service
 * Generates ER diagrams from schema registry data
 * Supports Mermaid ER diagrams and JSON exports for LLMs
 * Uses Standard Composio MCP Pattern for all database operations
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * Generate Mermaid ER diagram from schema registry
 */
export async function generateMermaidDiagram(options = {}) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[DIAGRAM-GENERATOR] Generating Mermaid ER diagram`);

    const {
      schemas = ['public', 'intake', 'marketing', 'people'],
      includeRelationships = true,
      includeColumns = true,
      maxTablesPerSchema = 10
    } = options;

    // 1. Get table structure from registry
    const tableData = await getTableStructureData(bridge, schemas, maxTablesPerSchema);

    // 2. Get relationships if requested
    const relationships = includeRelationships
      ? await getRelationshipData(bridge, schemas)
      : [];

    // 3. Generate Mermaid syntax
    const mermaidDiagram = buildMermaidDiagram(tableData, relationships, includeColumns);

    console.log(`[DIAGRAM-GENERATOR] Generated Mermaid diagram for ${tableData.length} tables`);

    return {
      success: true,
      data: {
        diagram: mermaidDiagram,
        format: 'mermaid',
        tables_included: tableData.length,
        relationships_included: relationships.length
      },
      metadata: {
        generated_at: new Date().toISOString(),
        schemas: schemas,
        options: options,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[DIAGRAM-GENERATOR] Mermaid generation failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Generate dbdiagram.io compatible diagram
 */
export async function generateDbDiagramIo(options = {}) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[DIAGRAM-GENERATOR] Generating dbdiagram.io diagram`);

    const {
      schemas = ['public', 'intake', 'marketing', 'people'],
      includeRelationships = true,
      maxTablesPerSchema = 10
    } = options;

    // 1. Get table structure from registry
    const tableData = await getTableStructureData(bridge, schemas, maxTablesPerSchema);

    // 2. Get relationships if requested
    const relationships = includeRelationships
      ? await getRelationshipData(bridge, schemas)
      : [];

    // 3. Generate dbdiagram.io syntax
    const dbDiagram = buildDbDiagramIo(tableData, relationships);

    console.log(`[DIAGRAM-GENERATOR] Generated dbdiagram.io diagram for ${tableData.length} tables`);

    return {
      success: true,
      data: {
        diagram: dbDiagram,
        format: 'dbdiagram.io',
        tables_included: tableData.length,
        relationships_included: relationships.length
      },
      metadata: {
        generated_at: new Date().toISOString(),
        schemas: schemas,
        options: options,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[DIAGRAM-GENERATOR] dbdiagram.io generation failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Generate JSON export for LLMs
 */
export async function generateJsonExport(options = {}) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[DIAGRAM-GENERATOR] Generating JSON export for LLMs`);

    const {
      schemas = ['public', 'intake', 'marketing', 'people'],
      includeRelationships = true,
      includeStatistics = true,
      maxTablesPerSchema = 50
    } = options;

    // 1. Get comprehensive table data
    const tableData = await getDetailedTableData(bridge, schemas, maxTablesPerSchema);

    // 2. Get relationships
    const relationships = includeRelationships
      ? await getRelationshipData(bridge, schemas)
      : [];

    // 3. Get statistics if requested
    const statistics = includeStatistics
      ? await generateSchemaStatistics(bridge, schemas)
      : null;

    // 4. Build structured JSON
    const jsonExport = {
      database_schema: {
        schemas: buildSchemaJson(tableData),
        relationships: relationships,
        statistics: statistics,
        metadata: {
          generated_at: new Date().toISOString(),
          schemas_included: schemas,
          total_tables: tableData.length,
          total_relationships: relationships.length,
          export_options: options
        }
      }
    };

    console.log(`[DIAGRAM-GENERATOR] Generated JSON export with ${tableData.length} tables`);

    return {
      success: true,
      data: jsonExport,
      format: 'json',
      metadata: {
        generated_at: new Date().toISOString(),
        schemas: schemas,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[DIAGRAM-GENERATOR] JSON export generation failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Get table structure data from schema registry
 */
async function getTableStructureData(bridge, schemas, maxTablesPerSchema) {
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  const sql = `
    SELECT
      schema_name,
      table_name,
      column_name,
      data_type,
      is_nullable,
      column_default,
      is_primary_key,
      is_foreign_key,
      ordinal_position,
      doctrine_tag
    FROM shq.schema_registry
    WHERE schema_name IN (${schemaPlaceholders})
    AND table_name IN (
      SELECT DISTINCT table_name
      FROM shq.schema_registry
      WHERE schema_name IN (${schemaPlaceholders})
      ORDER BY table_name
      LIMIT ${maxTablesPerSchema * schemas.length}
    )
    ORDER BY schema_name, table_name, ordinal_position
  `;

  const result = await bridge.executeSQL(sql, schemas);

  if (!result.success) {
    throw new Error(`Failed to get table structure: ${result.error}`);
  }

  return result.data.rows;
}

/**
 * Get detailed table data including constraints and indexes
 */
async function getDetailedTableData(bridge, schemas, maxTablesPerSchema) {
  const basicData = await getTableStructureData(bridge, schemas, maxTablesPerSchema);

  // Group by table for easier processing
  const tableGroups = {};
  basicData.forEach(row => {
    const tableKey = `${row.schema_name}.${row.table_name}`;
    if (!tableGroups[tableKey]) {
      tableGroups[tableKey] = {
        schema: row.schema_name,
        table: row.table_name,
        columns: []
      };
    }
    tableGroups[tableKey].columns.push(row);
  });

  return Object.values(tableGroups);
}

/**
 * Get relationship data from relationships table
 */
async function getRelationshipData(bridge, schemas) {
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  const sql = `
    SELECT
      source_schema,
      source_table,
      target_schema,
      target_table,
      relationship_type,
      relationship_data,
      confidence_score
    FROM shq.table_relationships
    WHERE source_schema IN (${schemaPlaceholders})
    OR target_schema IN (${schemaPlaceholders})
    ORDER BY relationship_type, confidence_score DESC
  `;

  const result = await bridge.executeSQL(sql, schemas);

  if (!result.success) {
    throw new Error(`Failed to get relationship data: ${result.error}`);
  }

  return result.data.rows;
}

/**
 * Generate schema statistics
 */
async function generateSchemaStatistics(bridge, schemas) {
  const schemaPlaceholders = schemas.map((_, i) => `$${i + 1}`).join(', ');

  const sql = `
    SELECT
      schema_name,
      COUNT(DISTINCT table_name) as table_count,
      COUNT(*) as column_count,
      COUNT(CASE WHEN is_primary_key THEN 1 END) as primary_key_count,
      COUNT(CASE WHEN is_foreign_key THEN 1 END) as foreign_key_count,
      COUNT(CASE WHEN is_nullable = false THEN 1 END) as required_columns
    FROM shq.schema_registry
    WHERE schema_name IN (${schemaPlaceholders})
    GROUP BY schema_name
    ORDER BY schema_name
  `;

  const result = await bridge.executeSQL(sql, schemas);
  return result.success ? result.data.rows : [];
}

/**
 * Build Mermaid ER diagram syntax
 */
function buildMermaidDiagram(tableData, relationships, includeColumns) {
  let mermaid = 'erDiagram\n';

  // Group columns by table
  const tables = {};
  tableData.forEach(row => {
    const tableKey = `${row.schema_name}_${row.table_name}`;
    if (!tables[tableKey]) {
      tables[tableKey] = {
        schema: row.schema_name,
        table: row.table_name,
        columns: []
      };
    }
    tables[tableKey].columns.push(row);
  });

  // Add table definitions
  Object.values(tables).forEach(table => {
    mermaid += `  ${table.schema}_${table.table} {\n`;

    if (includeColumns) {
      table.columns.forEach(col => {
        let columnType = col.data_type;
        let constraints = '';

        if (col.is_primary_key) constraints += ' PK';
        if (col.is_foreign_key) constraints += ' FK';
        if (!col.is_nullable) constraints += ' NOT NULL';

        mermaid += `    ${columnType} ${col.column_name}${constraints}\n`;
      });
    }

    mermaid += '  }\n';
  });

  // Add relationships
  relationships.forEach(rel => {
    const source = `${rel.source_schema}_${rel.source_table}`;
    const target = `${rel.target_schema}_${rel.target_table}`;

    let relationSymbol = '||--||';
    switch (rel.relationship_type) {
      case 'promotion':
        relationSymbol = '||--o|';
        break;
      case 'foreign_key':
        relationSymbol = '}|--||';
        break;
      case 'one_to_many':
        relationSymbol = '||--o{';
        break;
      default:
        relationSymbol = '||--||';
    }

    mermaid += `  ${source} ${relationSymbol} ${target} : "${rel.relationship_type}"\n`;
  });

  return mermaid;
}

/**
 * Build dbdiagram.io syntax
 */
function buildDbDiagramIo(tableData, relationships) {
  let diagram = '// Generated by Schema Registry System\n\n';

  // Group columns by table
  const tables = {};
  tableData.forEach(row => {
    const tableKey = `${row.schema_name}.${row.table_name}`;
    if (!tables[tableKey]) {
      tables[tableKey] = {
        schema: row.schema_name,
        table: row.table_name,
        columns: []
      };
    }
    tables[tableKey].columns.push(row);
  });

  // Add table definitions
  Object.values(tables).forEach(table => {
    diagram += `Table "${table.schema}"."${table.table}" {\n`;

    table.columns.forEach(col => {
      let columnDef = `  "${col.column_name}" ${col.data_type.toUpperCase()}`;

      if (col.is_primary_key) columnDef += ' [pk]';
      if (col.is_foreign_key) columnDef += ' [ref: > other.table.id]';
      if (!col.is_nullable) columnDef += ' [not null]';
      if (col.column_default) columnDef += ` [default: '${col.column_default}']`;

      diagram += columnDef + '\n';
    });

    diagram += '}\n\n';
  });

  // Add relationships
  relationships.forEach(rel => {
    const source = `"${rel.source_schema}"."${rel.source_table}".id`;
    const target = `"${rel.target_schema}"."${rel.target_table}".id`;

    let refType = '>';
    switch (rel.relationship_type) {
      case 'promotion':
        refType = '-';
        break;
      case 'foreign_key':
        refType = '>';
        break;
      default:
        refType = '-';
    }

    diagram += `Ref: ${source} ${refType} ${target} // ${rel.relationship_type}\n`;
  });

  return diagram;
}

/**
 * Build structured JSON for schemas
 */
function buildSchemaJson(tableGroups) {
  const schemaJson = {};

  tableGroups.forEach(table => {
    if (!schemaJson[table.schema]) {
      schemaJson[table.schema] = {
        name: table.schema,
        tables: {}
      };
    }

    schemaJson[table.schema].tables[table.table] = {
      name: table.table,
      columns: table.columns.map(col => ({
        name: col.column_name,
        type: col.data_type,
        nullable: col.is_nullable,
        primary_key: col.is_primary_key,
        foreign_key: col.is_foreign_key,
        default_value: col.column_default,
        position: col.ordinal_position,
        doctrine_tags: col.doctrine_tag
      }))
    };
  });

  return schemaJson;
}