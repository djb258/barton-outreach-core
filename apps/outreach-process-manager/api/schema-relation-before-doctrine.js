/**
 * API Endpoint: /api/schema-relation
 * Schema Relationship Management - Add and manage table relationships
 * Uses Standard Composio MCP Pattern for all database operations
 */

import { addTableRelationship, getTableRelationships, autoDiscoverRelationships, getRelationshipStatistics } from '../services/relationshipTracker.js';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  try {
    if (req.method === 'POST') {
      const { source, target, relation, metadata = {} } = req.body;

      // Validate required fields
      if (!source || !target || !relation) {
        return res.status(400).json({
          error: 'Missing required fields',
          message: 'source, target, and relation are required',
          required_format: {
            source: 'schema.table',
            target: 'schema.table',
            relation: 'promotion|foreign_key|join|reference'
          }
        });
      }

      // Parse source and target
      const [sourceSchema, sourceTable] = source.split('.');
      const [targetSchema, targetTable] = target.split('.');

      if (!sourceSchema || !sourceTable || !targetSchema || !targetTable) {
        return res.status(400).json({
          error: 'Invalid format',
          message: 'Source and target must be in format: schema.table'
        });
      }

      const result = await addTableRelationship({
        sourceSchema,
        sourceTable,
        targetSchema,
        targetTable,
        relationshipType: relation,
        relationshipData: metadata,
        createdBy: 'api_user'
      });

      return res.status(201).json(result);

    } else if (req.method === 'GET') {
      const { schema, table, direction, action } = req.query;

      if (action === 'auto-discover') {
        console.log(`[SCHEMA-RELATION] Running auto-discovery`);
        const result = await autoDiscoverRelationships();
        return res.status(200).json(result);
      }

      if (action === 'statistics') {
        console.log(`[SCHEMA-RELATION] Getting relationship statistics`);
        const result = await getRelationshipStatistics();
        return res.status(200).json(result);
      }

      if (schema && table) {
        const result = await getTableRelationships(schema, table, direction || 'both');
        return res.status(200).json(result);
      }

      return res.status(400).json({
        error: 'Missing parameters',
        message: 'For GET requests, provide schema and table, or use action=auto-discover or action=statistics'
      });

    } else {
      return res.status(405).json({
        error: 'Method not allowed',
        message: 'Only POST and GET requests are accepted'
      });
    }

  } catch (error) {
    console.error('[SCHEMA-RELATION] Request failed:', error);
    return res.status(500).json({
      error: 'Relationship operation failed',
      message: error.message,
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }
}