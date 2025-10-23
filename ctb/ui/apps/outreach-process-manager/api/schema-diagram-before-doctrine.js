/**
 * API Endpoint: /api/schema-diagram
 * Schema Diagram Generation - Creates ER diagrams and JSON exports
 * Uses Standard Composio MCP Pattern for all database operations
 */

import { generateMermaidDiagram, generateDbDiagramIo, generateJsonExport } from '../services/diagramGenerator.js';

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  if (req.method !== 'GET' && req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only GET and POST requests are accepted'
    });
  }

  try {
    // Extract options from query params or request body
    const options = req.method === 'POST' ? req.body : req.query;

    const {
      format = 'mermaid',
      schemas = ['public', 'intake', 'marketing', 'people'],
      includeRelationships = true,
      includeColumns = true,
      includeStatistics = false,
      maxTablesPerSchema = 10
    } = options;

    // Parse schemas if it's a string
    const schemaList = Array.isArray(schemas) ? schemas : schemas.split(',').map(s => s.trim());

    const diagramOptions = {
      schemas: schemaList,
      includeRelationships: includeRelationships === 'true' || includeRelationships === true,
      includeColumns: includeColumns === 'true' || includeColumns === true,
      includeStatistics: includeStatistics === 'true' || includeStatistics === true,
      maxTablesPerSchema: parseInt(maxTablesPerSchema) || 10
    };

    console.log(`[SCHEMA-DIAGRAM] Generating ${format} diagram with options:`, diagramOptions);

    let result;

    switch (format.toLowerCase()) {
      case 'mermaid':
        result = await generateMermaidDiagram(diagramOptions);
        break;

      case 'dbdiagram':
      case 'dbdiagram.io':
        result = await generateDbDiagramIo(diagramOptions);
        break;

      case 'json':
        result = await generateJsonExport(diagramOptions);
        break;

      default:
        return res.status(400).json({
          error: 'Invalid format',
          message: 'Supported formats: mermaid, dbdiagram, json',
          supported_formats: ['mermaid', 'dbdiagram', 'json']
        });
    }

    // Set appropriate content type
    if (format === 'json') {
      res.setHeader('Content-Type', 'application/json');
    } else {
      res.setHeader('Content-Type', 'text/plain');
    }

    return res.status(200).json({
      success: true,
      format: format,
      data: result.data,
      metadata: {
        ...result.metadata,
        altitude: 10000,
        doctrine: 'STAMPED'
      }
    });

  } catch (error) {
    console.error('[SCHEMA-DIAGRAM] Diagram generation failed:', error);
    return res.status(500).json({
      error: 'Diagram generation failed',
      message: error.message,
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }
}