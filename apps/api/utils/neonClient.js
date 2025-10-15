/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Shared Neon database client utility
 * - MCP: Direct Neon Serverless connection
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

dotenv.config();

// Initialize Neon serverless SQL client
const connectionString = process.env.NEON_DATABASE_URL;

if (!connectionString) {
  console.error('❌ NEON_DATABASE_URL environment variable is not set');
  throw new Error('NEON_DATABASE_URL is required');
}

// Create the Neon SQL client
export const sql = neon(connectionString);

/**
 * Execute a query with error handling
 * @param {string} query - SQL query string
 * @param {Array} params - Query parameters
 * @returns {Promise<Array>} Query results
 */
export async function executeQuery(query, params = []) {
  try {
    console.log(`🔍 Executing query: ${query.substring(0, 100)}...`);
    const result = await sql(query, params);
    console.log(`✅ Query executed successfully, returned ${result.length} rows`);
    return result;
  } catch (error) {
    console.error('❌ Neon query error:', error);
    throw error;
  }
}

/**
 * Execute a parameterized query with named parameters
 * @param {Function} queryFn - Neon tagged template function
 * @returns {Promise<Array>} Query results
 */
export async function executeTaggedQuery(queryFn) {
  try {
    const result = await queryFn;
    console.log(`✅ Tagged query executed successfully, returned ${result.length} rows`);
    return result;
  } catch (error) {
    console.error('❌ Neon tagged query error:', error);
    throw error;
  }
}

/**
 * Health check for Neon connection
 * @returns {Promise<boolean>} Connection status
 */
export async function healthCheck() {
  try {
    await sql`SELECT 1 as health`;
    return true;
  } catch (error) {
    console.error('❌ Neon health check failed:', error);
    return false;
  }
}

export default sql;
