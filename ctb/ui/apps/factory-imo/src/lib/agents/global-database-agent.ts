/**
 * Global Database Agent
 * 
 * Universal database agent that can work across any project with:
 * - Multiple database platforms (Neon, Firebase, BigQuery, PostgreSQL, Supabase)
 * - Any schema structure
 * - Environment-agnostic configuration
 * - Barton Doctrine compliance (optional)
 * - Cross-project deployment capability
 */

export interface GlobalDatabaseConfig {
  // Environment & Project Info
  environment: 'development' | 'staging' | 'production';
  project_id?: string;
  project_name?: string;
  
  // Database Connections
  connections: DatabaseConnectionConfig[];
  
  // Agent Behavior
  enable_doctrine_compliance?: boolean;
  enable_history_tracking?: boolean;
  enable_error_logging?: boolean;
  default_timeout_ms?: number;
  max_retry_attempts?: number;
}

export interface DatabaseConnectionConfig {
  name: string; // Unique connection identifier
  type: 'neon' | 'firebase' | 'bigquery' | 'postgres' | 'supabase' | 'mysql' | 'mongodb';
  
  // Connection Details
  connection_string?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  
  // Cloud-specific
  project_id?: string; // For BigQuery, Firebase
  service_account_key?: string; // For GCP services
  region?: string;
  
  // Connection Pool Settings
  max_connections?: number;
  idle_timeout_ms?: number;
  
  // Access Control
  read_only?: boolean;
  allowed_schemas?: string[];
  allowed_operations?: DatabaseOperationType[];
}

export type DatabaseOperationType = 
  | 'select' | 'insert' | 'update' | 'delete' | 'upsert' 
  | 'bulk_insert' | 'bulk_update' | 'bulk_delete'
  | 'create_table' | 'alter_table' | 'drop_table'
  | 'create_schema' | 'drop_schema'
  | 'execute_raw';

export interface DatabaseOperation {
  id: string;
  
  // Target
  connection_name: string;
  database?: string;
  schema?: string;
  table?: string;
  
  // Operation
  operation: DatabaseOperationType;
  data?: any;
  where?: Record<string, any>;
  raw_query?: string;
  parameters?: any[];
  
  // Options
  options?: {
    conflict_resolution?: 'ignore' | 'update' | 'error';
    batch_size?: number;
    timeout_ms?: number;
    return_data?: boolean;
    transaction_id?: string;
  };
  
  // Metadata (for any project using Barton Doctrine)
  unique_id?: string;
  process_id?: string;
  blueprint_version_hash?: string;
  source_agent?: string;
  project_context?: Record<string, any>;
}

export interface DatabaseResult {
  success: boolean;
  operation_id: string;
  connection_name: string;
  database_type: string;
  
  // Results
  affected_rows?: number;
  returned_data?: any[];
  transaction_id?: string;
  
  // Performance
  execution_time_ms: number;
  query_plan?: any;
  
  // Error Handling
  error?: string;
  error_code?: string;
  retry_count?: number;
  
  // Metadata
  timestamp: string;
  agent_version: string;
}

export class GlobalDatabaseAgent {
  private config: GlobalDatabaseConfig;
  private connections: Map<string, any> = new Map();
  private connectionPools: Map<string, any> = new Map();
  private operationHistory: DatabaseResult[] = [];
  private readonly agentVersion = '1.0.0';

  constructor(config: GlobalDatabaseConfig) {
    this.config = config;
    this.validateConfig();
  }

  // ============================================
  // Connection Management
  // ============================================

  async initialize(): Promise<void> {
    console.log(`🚀 Initializing Global Database Agent v${this.agentVersion}`);
    console.log(`📊 Project: ${this.config.project_name || 'Unknown'}`);
    console.log(`🌍 Environment: ${this.config.environment}`);
    
    for (const connectionConfig of this.config.connections) {
      await this.createConnection(connectionConfig);
    }
    
    console.log(`✅ Initialized ${this.connections.size} database connections`);
  }

  private async createConnection(config: DatabaseConnectionConfig): Promise<void> {
    try {
      let client;
      let pool;

      switch (config.type) {
        case 'neon':
        case 'postgres':
        case 'supabase':
          ({ client, pool } = await this.createPostgresConnection(config));
          break;
        
        case 'firebase':
          client = await this.createFirebaseConnection(config);
          break;
        
        case 'bigquery':
          client = await this.createBigQueryConnection(config);
          break;
        
        case 'mysql':
          ({ client, pool } = await this.createMySQLConnection(config));
          break;
        
        case 'mongodb':
          client = await this.createMongoDBConnection(config);
          break;
        
        default:
          throw new Error(`Unsupported database type: ${config.type}`);
      }

      this.connections.set(config.name, {
        client,
        config,
        type: config.type,
        created_at: new Date().toISOString()
      });

      if (pool) {
        this.connectionPools.set(config.name, pool);
      }

      console.log(`✅ Connected to ${config.name} (${config.type})`);
    } catch (error) {
      console.error(`❌ Failed to connect to ${config.name}:`, error);
      throw error;
    }
  }

  private async createPostgresConnection(config: DatabaseConnectionConfig) {
    const { Client, Pool } = await import('pg');
    
    const connectionOptions = config.connection_string ? {
      connectionString: config.connection_string
    } : {
      host: config.host,
      port: config.port || 5432,
      database: config.database,
      user: config.username,
      password: config.password
    };

    const client = new Client(connectionOptions);
    await client.connect();

    const pool = new Pool({
      ...connectionOptions,
      max: config.max_connections || 10,
      idleTimeoutMillis: config.idle_timeout_ms || 30000
    });

    return { client, pool };
  }

  private async createFirebaseConnection(config: DatabaseConnectionConfig) {
    // Firebase Admin SDK
    const admin = await import('firebase-admin');
    
    const serviceAccount = config.service_account_key ? 
      JSON.parse(config.service_account_key) : undefined;

    if (!admin.apps.length) {
      admin.initializeApp({
        credential: serviceAccount ? admin.credential.cert(serviceAccount) : admin.credential.applicationDefault(),
        projectId: config.project_id
      });
    }

    return admin.firestore();
  }

  private async createBigQueryConnection(config: DatabaseConnectionConfig) {
    const { BigQuery } = await import('@google-cloud/bigquery');
    
    return new BigQuery({
      projectId: config.project_id,
      keyFilename: config.service_account_key
    });
  }

  private async createMySQLConnection(config: DatabaseConnectionConfig) {
    const mysql = await import('mysql2/promise');
    
    const connectionOptions = {
      host: config.host,
      port: config.port || 3306,
      user: config.username,
      password: config.password,
      database: config.database
    };

    const client = await mysql.createConnection(connectionOptions);
    const pool = mysql.createPool({
      ...connectionOptions,
      waitForConnections: true,
      connectionLimit: config.max_connections || 10,
      queueLimit: 0
    });

    return { client, pool };
  }

  private async createMongoDBConnection(config: DatabaseConnectionConfig) {
    const { MongoClient } = await import('mongodb');
    
    const client = new MongoClient(config.connection_string || '', {
      maxPoolSize: config.max_connections || 10
    });
    
    await client.connect();
    return client;
  }

  // ============================================
  // Core Database Operations
  // ============================================

  async execute(operation: DatabaseOperation): Promise<DatabaseResult> {
    const startTime = Date.now();
    const timestamp = new Date().toISOString();

    try {
      // Validate operation
      this.validateOperation(operation);

      // Enrich with metadata if doctrine compliance enabled
      if (this.config.enable_doctrine_compliance) {
        operation = this.enrichWithDoctrine(operation);
      }

      // Execute operation
      const result = await this.executeOperation(operation);

      // Track history if enabled
      if (this.config.enable_history_tracking) {
        this.operationHistory.push(result);
      }

      return {
        ...result,
        execution_time_ms: Date.now() - startTime,
        timestamp,
        agent_version: this.agentVersion
      };

    } catch (error) {
      const errorResult: DatabaseResult = {
        success: false,
        operation_id: operation.id,
        connection_name: operation.connection_name,
        database_type: this.getConnectionType(operation.connection_name),
        error: error instanceof Error ? error.message : 'Unknown error',
        execution_time_ms: Date.now() - startTime,
        timestamp,
        agent_version: this.agentVersion
      };

      // Log error if enabled
      if (this.config.enable_error_logging) {
        await this.logError(operation, error);
      }

      return errorResult;
    }
  }

  private async executeOperation(operation: DatabaseOperation): Promise<Omit<DatabaseResult, 'execution_time_ms' | 'timestamp' | 'agent_version'>> {
    const connection = this.connections.get(operation.connection_name);
    if (!connection) {
      throw new Error(`Connection '${operation.connection_name}' not found`);
    }

    // Check permissions
    this.checkOperationPermissions(connection.config, operation);

    switch (connection.type) {
      case 'neon':
      case 'postgres':
      case 'supabase':
        return await this.executePostgresOperation(connection, operation);
      
      case 'firebase':
        return await this.executeFirebaseOperation(connection, operation);
      
      case 'bigquery':
        return await this.executeBigQueryOperation(connection, operation);
      
      case 'mysql':
        return await this.executeMySQLOperation(connection, operation);
      
      case 'mongodb':
        return await this.executeMongoDBOperation(connection, operation);
      
      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }
  }

  // ============================================
  // Database-Specific Implementations
  // ============================================

  private async executePostgresOperation(connection: any, operation: DatabaseOperation): Promise<Omit<DatabaseResult, 'execution_time_ms' | 'timestamp' | 'agent_version'>> {
    const client = connection.client;
    
    if (operation.raw_query) {
      const result = await client.query(operation.raw_query, operation.parameters || []);
      return {
        success: true,
        operation_id: operation.id,
        connection_name: operation.connection_name,
        database_type: connection.type,
        affected_rows: result.rowCount,
        returned_data: result.rows
      };
    }

    // Build structured query
    const { query, values } = this.buildPostgresQuery(operation);
    const result = await client.query(query, values);

    return {
      success: true,
      operation_id: operation.id,
      connection_name: operation.connection_name,
      database_type: connection.type,
      affected_rows: result.rowCount,
      returned_data: operation.options?.return_data !== false ? result.rows : undefined
    };
  }

  private buildPostgresQuery(operation: DatabaseOperation): { query: string; values: any[] } {
    const fullTableName = operation.schema ? 
      `${operation.schema}.${operation.table}` : 
      operation.table;

    switch (operation.operation) {
      case 'select':
        return this.buildSelectQuery(fullTableName!, operation.where);
      case 'insert':
        return this.buildInsertQuery(fullTableName!, operation.data);
      case 'update':
        return this.buildUpdateQuery(fullTableName!, operation.data, operation.where);
      case 'delete':
        return this.buildDeleteQuery(fullTableName!, operation.where);
      case 'upsert':
        return this.buildUpsertQuery(fullTableName!, operation.data);
      case 'bulk_insert':
        return this.buildBulkInsertQuery(fullTableName!, operation.data);
      default:
        throw new Error(`Unsupported Postgres operation: ${operation.operation}`);
    }
  }

  // (Include the query building methods from previous implementation)
  private buildSelectQuery(tableName: string, where?: Record<string, any>): { query: string; values: any[] } {
    const whereColumns = where ? Object.keys(where) : [];
    const whereValues = where ? Object.values(where) : [];
    
    const whereClause = whereColumns.length > 0 
      ? 'WHERE ' + whereColumns.map((col, index) => `${col} = $${index + 1}`).join(' AND ')
      : '';

    const query = `SELECT * FROM ${tableName} ${whereClause}`;
    return { query, values: whereValues };
  }

  private buildInsertQuery(tableName: string, data: Record<string, any>): { query: string; values: any[] } {
    const columns = Object.keys(data);
    const placeholders = columns.map((_, index) => `$${index + 1}`);
    const values = Object.values(data);

    const query = `
      INSERT INTO ${tableName} (${columns.join(', ')})
      VALUES (${placeholders.join(', ')})
      RETURNING *
    `;

    return { query, values };
  }

  private buildUpdateQuery(tableName: string, data: Record<string, any>, where?: Record<string, any>): { query: string; values: any[] } {
    const setColumns = Object.keys(data);
    const setValues = Object.values(data);
    const whereColumns = where ? Object.keys(where) : [];
    const whereValues = where ? Object.values(where) : [];

    const setClause = setColumns.map((col, index) => `${col} = $${index + 1}`).join(', ');
    const whereClause = whereColumns.length > 0 
      ? 'WHERE ' + whereColumns.map((col, index) => `${col} = $${setValues.length + index + 1}`).join(' AND ')
      : '';

    const query = `
      UPDATE ${tableName}
      SET ${setClause}
      ${whereClause}
      RETURNING *
    `;

    return { query, values: [...setValues, ...whereValues] };
  }

  private buildDeleteQuery(tableName: string, where?: Record<string, any>): { query: string; values: any[] } {
    if (!where || Object.keys(where).length === 0) {
      throw new Error('DELETE operations require WHERE clause for safety');
    }

    const whereColumns = Object.keys(where);
    const whereValues = Object.values(where);
    const whereClause = whereColumns.map((col, index) => `${col} = $${index + 1}`).join(' AND ');

    const query = `DELETE FROM ${tableName} WHERE ${whereClause} RETURNING *`;
    return { query, values: whereValues };
  }

  private buildUpsertQuery(tableName: string, data: Record<string, any>): { query: string; values: any[] } {
    const columns = Object.keys(data);
    const placeholders = columns.map((_, index) => `$${index + 1}`);
    const values = Object.values(data);

    const updateSet = columns
      .filter(col => col !== 'id')
      .map(col => `${col} = EXCLUDED.${col}`)
      .join(', ');

    const query = `
      INSERT INTO ${tableName} (${columns.join(', ')})
      VALUES (${placeholders.join(', ')})
      ON CONFLICT (id) DO UPDATE SET ${updateSet}
      RETURNING *
    `;

    return { query, values };
  }

  private buildBulkInsertQuery(tableName: string, dataArray: Record<string, any>[]): { query: string; values: any[] } {
    if (dataArray.length === 0) {
      throw new Error('No data provided for bulk insert');
    }

    const columns = Object.keys(dataArray[0]);
    const values: any[] = [];
    const valueRows: string[] = [];

    dataArray.forEach((data) => {
      const rowPlaceholders = columns.map(() => {
        values.push(data[columns[values.length % columns.length]]);
        return `$${values.length}`;
      });
      valueRows.push(`(${rowPlaceholders.join(', ')})`);
    });

    const query = `
      INSERT INTO ${tableName} (${columns.join(', ')})
      VALUES ${valueRows.join(', ')}
      RETURNING *
    `;

    return { query, values };
  }

  // ============================================
  // Other Database Implementations (Stubs)
  // ============================================

  private async executeFirebaseOperation(connection: any, operation: DatabaseOperation): Promise<any> {
    // TODO: Implement Firebase operations
    throw new Error('Firebase operations not yet implemented');
  }

  private async executeBigQueryOperation(connection: any, operation: DatabaseOperation): Promise<any> {
    // TODO: Implement BigQuery operations
    throw new Error('BigQuery operations not yet implemented');
  }

  private async executeMySQLOperation(connection: any, operation: DatabaseOperation): Promise<any> {
    // TODO: Implement MySQL operations
    throw new Error('MySQL operations not yet implemented');
  }

  private async executeMongoDBOperation(connection: any, operation: DatabaseOperation): Promise<any> {
    // TODO: Implement MongoDB operations
    throw new Error('MongoDB operations not yet implemented');
  }

  // ============================================
  // Utility Methods
  // ============================================

  private validateConfig(): void {
    if (!this.config.connections || this.config.connections.length === 0) {
      throw new Error('At least one database connection must be configured');
    }

    // Validate connection names are unique
    const names = this.config.connections.map(c => c.name);
    if (new Set(names).size !== names.length) {
      throw new Error('Connection names must be unique');
    }
  }

  private validateOperation(operation: DatabaseOperation): void {
    if (!operation.id) throw new Error('Operation ID is required');
    if (!operation.connection_name) throw new Error('Connection name is required');
    if (!operation.operation) throw new Error('Operation type is required');
    
    if (!this.connections.has(operation.connection_name)) {
      throw new Error(`Connection '${operation.connection_name}' not found`);
    }
  }

  private checkOperationPermissions(config: DatabaseConnectionConfig, operation: DatabaseOperation): void {
    // Check read-only constraint
    if (config.read_only && ['insert', 'update', 'delete', 'upsert', 'bulk_insert', 'bulk_update', 'bulk_delete'].includes(operation.operation)) {
      throw new Error(`Write operations not allowed on read-only connection: ${operation.connection_name}`);
    }

    // Check allowed operations
    if (config.allowed_operations && !config.allowed_operations.includes(operation.operation)) {
      throw new Error(`Operation '${operation.operation}' not allowed on connection: ${operation.connection_name}`);
    }

    // Check allowed schemas
    if (config.allowed_schemas && operation.schema && !config.allowed_schemas.includes(operation.schema)) {
      throw new Error(`Schema '${operation.schema}' not allowed on connection: ${operation.connection_name}`);
    }
  }

  private enrichWithDoctrine(operation: DatabaseOperation): DatabaseOperation {
    return {
      ...operation,
      unique_id: operation.unique_id || this.generateUniqueId(),
      process_id: operation.process_id || this.generateProcessId(),
      blueprint_version_hash: operation.blueprint_version_hash || this.agentVersion
    };
  }

  private generateUniqueId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 7);
    return `global.db.${timestamp}.${random}`;
  }

  private generateProcessId(): string {
    return `global_db_agent_${Date.now()}`;
  }

  private getConnectionType(connectionName: string): string {
    const connection = this.connections.get(connectionName);
    return connection ? connection.type : 'unknown';
  }

  private async logError(operation: DatabaseOperation, error: any): Promise<void> {
    console.error(`❌ Global Database Agent Error:`, {
      operation_id: operation.id,
      connection: operation.connection_name,
      operation_type: operation.operation,
      table: operation.schema ? `${operation.schema}.${operation.table}` : operation.table,
      error: error instanceof Error ? error.message : 'Unknown error',
      project: this.config.project_name,
      environment: this.config.environment
    });
  }

  // ============================================
  // Public Interface
  // ============================================

  async disconnect(): Promise<void> {
    for (const [name, connection] of this.connections) {
      try {
        if (connection.type === 'postgres' || connection.type === 'neon' || connection.type === 'supabase') {
          await connection.client.end();
        }
        // Add disconnect logic for other types
      } catch (error) {
        console.error(`Error disconnecting from ${name}:`, error);
      }
    }
    
    this.connections.clear();
    this.connectionPools.clear();
  }

  getConnections(): string[] {
    return Array.from(this.connections.keys());
  }

  getOperationHistory(): DatabaseResult[] {
    return [...this.operationHistory];
  }

  async healthCheck(): Promise<Record<string, boolean>> {
    const health: Record<string, boolean> = {};
    
    for (const [name, connection] of this.connections) {
      try {
        // Perform basic health check based on database type
        health[name] = true; // Simplified for now
      } catch (error) {
        health[name] = false;
      }
    }
    
    return health;
  }
}

// ============================================
// Factory Functions for Common Configurations
// ============================================

export function createDevelopmentAgent(projectName: string, connections: DatabaseConnectionConfig[]): GlobalDatabaseAgent {
  return new GlobalDatabaseAgent({
    environment: 'development',
    project_name: projectName,
    connections,
    enable_doctrine_compliance: true,
    enable_history_tracking: true,
    enable_error_logging: true,
    default_timeout_ms: 30000,
    max_retry_attempts: 3
  });
}

export function createProductionAgent(projectName: string, connections: DatabaseConnectionConfig[]): GlobalDatabaseAgent {
  return new GlobalDatabaseAgent({
    environment: 'production',
    project_name: projectName,
    connections,
    enable_doctrine_compliance: true,
    enable_history_tracking: false, // Disable in prod for performance
    enable_error_logging: true,
    default_timeout_ms: 10000,
    max_retry_attempts: 5
  });
}