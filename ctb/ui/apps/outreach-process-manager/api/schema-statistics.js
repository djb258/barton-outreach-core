/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.67612.895
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/schema-statistics
 * Schema Registry Statistics - Returns database schema statistics
 * Part of the Schema Registry and Visualization system
 */

import { getSchemaRegistryStatistics } from '../routes/schemaRegistry.js';

export default getSchemaRegistryStatistics;