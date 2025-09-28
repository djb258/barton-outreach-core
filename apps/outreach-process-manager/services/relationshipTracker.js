/**
 * Relationship Tracker Service
 * Manages table-to-table relationships and dependencies
 * Tracks promotion paths, foreign keys, and logical connections
 */

import StandardComposioNeonBridge from '../api/lib/standard-composio-neon-bridge.js';

/**
 * Add a new relationship between tables
 */
export async function addTableRelationship({
  sourceSchema,
  sourceTable,
  targetSchema,
  targetTable,
  relationshipType,
  relationshipData = {},
  confidenceScore = 1.0,
  createdBy = 'system'
}) {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[RELATIONSHIP-TRACKER] Adding relationship: ${sourceSchema}.${sourceTable} -> ${targetSchema}.${targetTable} (${relationshipType})`);

    const sql = `
      INSERT INTO shq.table_relationships (
        source_schema, source_table, target_schema, target_table,
        relationship_type, relationship_data, confidence_score, created_by
      ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8)
      ON CONFLICT (source_schema, source_table, target_schema, target_table, relationship_type)
      DO UPDATE SET
        relationship_data = EXCLUDED.relationship_data,
        confidence_score = EXCLUDED.confidence_score,
        created_by = EXCLUDED.created_by,
        updated_at = NOW()
      RETURNING id
    `;

    const params = [
      sourceSchema, sourceTable, targetSchema, targetTable,
      relationshipType, JSON.stringify(relationshipData), confidenceScore, createdBy
    ];

    const result = await bridge.executeSQL(sql, params);

    if (!result.success) {
      throw new Error(`Failed to add relationship: ${result.error}`);
    }

    // Update doctrine tags in schema registry
    await updateDoctrineTags(bridge, {
      sourceSchema, sourceTable, targetSchema, targetTable, relationshipType, relationshipData
    });

    console.log(`[RELATIONSHIP-TRACKER] Successfully added relationship with ID: ${result.data.rows[0]?.id}`);

    return {
      success: true,
      relationship_id: result.data.rows[0]?.id,
      message: 'Relationship added successfully',
      metadata: {
        source: `${sourceSchema}.${sourceTable}`,
        target: `${targetSchema}.${targetTable}`,
        type: relationshipType,
        created_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[RELATIONSHIP-TRACKER] Failed to add relationship:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Get all relationships for a table
 */
export async function getTableRelationships(schema, table, direction = 'both') {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[RELATIONSHIP-TRACKER] Getting relationships for ${schema}.${table} (direction: ${direction})`);

    let whereConditions = [];
    let params = [];

    if (direction === 'outbound' || direction === 'both') {
      whereConditions.push(`(source_schema = $${params.length + 1} AND source_table = $${params.length + 2})`);
      params.push(schema, table);
    }

    if (direction === 'inbound' || direction === 'both') {
      whereConditions.push(`(target_schema = $${params.length + 1} AND target_table = $${params.length + 2})`);
      params.push(schema, table);
    }

    const sql = `
      SELECT
        id,
        source_schema,
        source_table,
        target_schema,
        target_table,
        relationship_type,
        relationship_data,
        confidence_score,
        created_by,
        created_at,
        updated_at
      FROM shq.table_relationships
      WHERE ${whereConditions.join(' OR ')}
      ORDER BY relationship_type, created_at DESC
    `;

    const result = await bridge.executeSQL(sql, params);

    if (!result.success) {
      throw new Error(`Failed to get table relationships: ${result.error}`);
    }

    return {
      success: true,
      data: result.data.rows,
      metadata: {
        table: `${schema}.${table}`,
        direction: direction,
        total_relationships: result.data.rows.length,
        fetched_at: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[RELATIONSHIP-TRACKER] Failed to get table relationships:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Auto-discover relationships based on naming patterns and foreign keys
 */
export async function autoDiscoverRelationships() {
  const bridge = new StandardComposioNeonBridge();

  try {
    console.log(`[RELATIONSHIP-TRACKER] Starting auto-discovery of relationships`);

    const discoveredRelationships = [];

    // 1. Discover promotion relationships (intake -> public/marketing)
    const promotionRelationships = await discoverPromotionRelationships(bridge);
    discoveredRelationships.push(...promotionRelationships);

    // 2. Discover foreign key relationships
    const foreignKeyRelationships = await discoverForeignKeyRelationships(bridge);
    discoveredRelationships.push(...foreignKeyRelationships);

    // 3. Discover naming pattern relationships
    const namingPatternRelationships = await discoverNamingPatternRelationships(bridge);
    discoveredRelationships.push(...namingPatternRelationships);

    console.log(`[RELATIONSHIP-TRACKER] Auto-discovered ${discoveredRelationships.length} relationships`);

    // Add discovered relationships
    const addPromises = discoveredRelationships.map(rel =>
      addTableRelationship({
        ...rel,
        createdBy: 'auto_discovery'
      })
    );

    const results = await Promise.allSettled(addPromises);
    const successCount = results.filter(r => r.status === 'fulfilled').length;
    const failureCount = results.filter(r => r.status === 'rejected').length;

    return {
      success: true,
      data: {
        discovered: discoveredRelationships.length,
        added_successfully: successCount,
        failed_to_add: failureCount,
        relationships: discoveredRelationships
      },
      metadata: {
        discovery_timestamp: new Date().toISOString(),
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    };

  } catch (error) {
    console.error('[RELATIONSHIP-TRACKER] Auto-discovery failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}

/**
 * Discover promotion relationships (intake -> production tables)
 */
async function discoverPromotionRelationships(bridge) {
  const promotionPairs = [
    { source: 'intake', target: 'public', pattern: 'company' },
    { source: 'intake', target: 'marketing', pattern: 'company' },
    { source: 'intake', target: 'people', pattern: 'contact' }
  ];

  const relationships = [];

  for (const pair of promotionPairs) {
    const sql = `
      SELECT DISTINCT
        s.table_name as source_table,
        t.table_name as target_table
      FROM information_schema.tables s
      JOIN information_schema.tables t ON t.table_name ILIKE '%${pair.pattern}%'
      WHERE s.table_schema = $1
      AND t.table_schema = $2
      AND s.table_name ILIKE '%${pair.pattern}%'
    `;

    const result = await bridge.executeSQL(sql, [pair.source, pair.target]);

    if (result.success) {
      result.data.rows.forEach(row => {
        relationships.push({
          sourceSchema: pair.source,
          sourceTable: row.source_table,
          targetSchema: pair.target,
          targetTable: row.target_table,
          relationshipType: 'promotion',
          relationshipData: {
            discovery_method: 'naming_pattern',
            pattern: pair.pattern
          },
          confidenceScore: 0.8
        });
      });
    }
  }

  return relationships;
}

/**
 * Discover foreign key relationships
 */
async function discoverForeignKeyRelationships(bridge) {
  const sql = `
    SELECT
      kcu.table_schema as source_schema,
      kcu.table_name as source_table,
      kcu.column_name as source_column,
      ccu.table_schema as target_schema,
      ccu.table_name as target_table,
      ccu.column_name as target_column,
      tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema IN ('public', 'intake', 'marketing', 'people')
  `;

  const result = await bridge.executeSQL(sql);
  const relationships = [];

  if (result.success) {
    result.data.rows.forEach(row => {
      relationships.push({
        sourceSchema: row.source_schema,
        sourceTable: row.source_table,
        targetSchema: row.target_schema,
        targetTable: row.target_table,
        relationshipType: 'foreign_key',
        relationshipData: {
          discovery_method: 'foreign_key_constraint',
          source_column: row.source_column,
          target_column: row.target_column,
          constraint_name: row.constraint_name
        },
        confidenceScore: 1.0
      });
    });
  }

  return relationships;
}

/**
 * Discover relationships based on naming patterns
 */
async function discoverNamingPatternRelationships(bridge) {
  const relationships = [];

  // Pattern 1: Tables with similar names across schemas
  const namePatternsSQL = `
    SELECT
      t1.table_schema as source_schema,
      t1.table_name as source_table,
      t2.table_schema as target_schema,
      t2.table_name as target_table,
      GREATEST(
        similarity(t1.table_name, t2.table_name),
        similarity(replace(t1.table_name, '_raw_', '_'), t2.table_name)
      ) as similarity_score
    FROM information_schema.tables t1
    JOIN information_schema.tables t2 ON t1.table_name != t2.table_name
    WHERE t1.table_schema IN ('intake', 'public', 'marketing', 'people')
    AND t2.table_schema IN ('intake', 'public', 'marketing', 'people')
    AND t1.table_schema != t2.table_schema
    AND (
      t1.table_name ILIKE '%' || replace(t2.table_name, '_', '%') || '%'
      OR t2.table_name ILIKE '%' || replace(t1.table_name, '_', '%') || '%'
      OR similarity(t1.table_name, t2.table_name) > 0.3
    )
  `;

  const result = await bridge.executeSQL(namePatternsSQL);

  if (result.success) {
    result.data.rows.forEach(row => {
      if (row.similarity_score > 0.5) {
        relationships.push({
          sourceSchema: row.source_schema,
          sourceTable: row.source_table,
          targetSchema: row.target_schema,
          targetTable: row.target_table,
          relationshipType: 'similar_structure',
          relationshipData: {
            discovery_method: 'naming_similarity',
            similarity_score: row.similarity_score
          },
          confidenceScore: Math.min(row.similarity_score, 0.9)
        });
      }
    });
  }

  return relationships;
}

/**
 * Update doctrine tags in schema registry with relationship information
 */
async function updateDoctrineTags(bridge, { sourceSchema, sourceTable, targetSchema, targetTable, relationshipType, relationshipData }) {
  const relationshipTag = {
    relation: relationshipType,
    source: `${sourceSchema}.${sourceTable}`,
    target: `${targetSchema}.${targetTable}`,
    metadata: relationshipData
  };

  // Update source table columns
  const updateSourceSQL = `
    UPDATE shq.schema_registry
    SET doctrine_tag = COALESCE(doctrine_tag, '{}'::jsonb) || $3::jsonb
    WHERE schema_name = $1 AND table_name = $2
  `;

  await bridge.executeSQL(updateSourceSQL, [sourceSchema, sourceTable, JSON.stringify({
    relationships_outbound: [relationshipTag]
  })]);

  // Update target table columns
  const updateTargetSQL = `
    UPDATE shq.schema_registry
    SET doctrine_tag = COALESCE(doctrine_tag, '{}'::jsonb) || $3::jsonb
    WHERE schema_name = $1 AND table_name = $2
  `;

  await bridge.executeSQL(updateTargetSQL, [targetSchema, targetTable, JSON.stringify({
    relationships_inbound: [{
      relation: relationshipType,
      source: `${sourceSchema}.${sourceTable}`,
      target: `${targetSchema}.${targetTable}`,
      metadata: relationshipData
    }]
  })]);
}

/**
 * Get relationship statistics
 */
export async function getRelationshipStatistics() {
  const bridge = new StandardComposioNeonBridge();

  try {
    const sql = `
      SELECT
        relationship_type,
        COUNT(*) as count,
        AVG(confidence_score) as avg_confidence,
        COUNT(DISTINCT source_schema || '.' || source_table) as unique_source_tables,
        COUNT(DISTINCT target_schema || '.' || target_table) as unique_target_tables
      FROM shq.table_relationships
      GROUP BY relationship_type
      ORDER BY count DESC
    `;

    const result = await bridge.executeSQL(sql);

    if (!result.success) {
      throw new Error(`Failed to get relationship statistics: ${result.error}`);
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
    console.error('[RELATIONSHIP-TRACKER] Failed to get statistics:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}