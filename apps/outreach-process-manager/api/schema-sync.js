/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.87615.783
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/schema-sync
 * Schema Registry Sync - Scans and syncs database metadata
 * Part of the Schema Registry and Visualization system
 */

import { syncSchemaRegistry } from '../routes/schemaRegistry.js';

export default syncSchemaRegistry;