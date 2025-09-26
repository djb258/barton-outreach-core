/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.36029.830
 * - Altitude: 10000 (Execution Layer)
 * - Input: API request parameters
 * - Output: API response data
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/schema-registry
 * Schema Registry Contents - Returns current registry data
 * Part of the Schema Registry and Visualization system
 */

import { getRegistryContents } from '../routes/schemaRegistry.js';

export default getRegistryContents;