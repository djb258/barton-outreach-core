# Composio Standard Integration Pattern

**CRITICAL**: This is the definitive, standardized way to integrate with Composio across ALL projects. This pattern MUST be used consistently to avoid reinventing the wheel.

## Overview

Composio integration uses the established MCP (Model Context Protocol) server pattern with direct database connections when action execution endpoints are not functional.

## Standard Integration Pattern

### 1. Environment Variables (Required)
```env
# Composio Configuration - REQUIRED for all projects
COMPOSIO_API_KEY=your_api_key_here
COMPOSIO_BASE_URL=https://backend.composio.dev
NEON_DATABASE_URL=your_neon_connection_string_here
```

### 2. Standard Bridge Class Structure

```javascript
import pkg from 'pg';
const { Client } = pkg;

class StandardComposioNeonBridge {
  constructor() {
    this.neonDatabaseUrl = process.env.NEON_DATABASE_URL;
    this.client = null;
  }

  async connect() {
    if (this.client) return;
    this.client = new Client({ connectionString: this.neonDatabaseUrl });
    await this.client.connect();
    console.log('✅ Connected to Neon via Composio MCP configuration');
  }

  async executeSQL(sql, params = []) {
    try {
      await this.connect();
      const result = await this.client.query(sql, params);
      return {
        success: true,
        data: { rows: result.rows, rowCount: result.rowCount }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async close() {
    if (this.client) {
      await this.client.end();
      this.client = null;
    }
  }
}
```

### 3. Service Layer Pattern

```javascript
import StandardComposioNeonBridge from './standard-composio-neon-bridge.js';

export async function performDatabaseOperation(operationParams) {
  const bridge = new StandardComposioNeonBridge();

  try {
    // Execute database operations
    const result = await bridge.executeSQL(sql, params);

    if (!result.success) {
      throw new Error(result.error);
    }

    return { success: true, data: result.data };
  } catch (error) {
    console.error('Database operation failed:', error);
    throw error;
  } finally {
    await bridge.close();
  }
}
```

### 4. API Endpoint Pattern

```javascript
import { performDatabaseOperation } from '../services/your-service.js';

export default async function handler(req, res) {
  // Set standard CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const result = await performDatabaseOperation(req.body);

    return res.status(200).json({
      ...result,
      doctrine: 'STAMPED',
      altitude: 10000,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return res.status(500).json({
      error: 'Operation failed',
      message: error.message
    });
  }
}
```

## Key Principles

1. **Composio First**: Always attempt Composio MCP connection first
2. **Standard Error Handling**: Consistent error patterns across all integrations
3. **Connection Management**: Proper connection opening/closing
4. **Barton Doctrine Compliance**: Include altitude, doctrine, timestamps
5. **Audit Logging**: Log all operations to marketing.company_audit_log

## Installation Requirements

```bash
npm install pg @composio/core
```

## Usage in New Projects

1. Copy the standard bridge class
2. Update environment variables
3. Follow the service layer pattern
4. Use standard API endpoint structure
5. Include audit logging

## Do NOT

- Create direct database connections outside this pattern
- Skip error handling
- Omit audit logging
- Use different environment variable names
- Bypass the standard bridge class

This pattern ensures consistency, maintainability, and reduces debugging time across all projects.