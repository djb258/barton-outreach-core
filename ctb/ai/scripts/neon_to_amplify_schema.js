#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.ntas.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: Transform Neon PostgreSQL manifest to AWS Amplify GraphQL schema
 * Dependencies: yaml@^2.3.0
 * Input: ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml
 * Output: ctb/data/infra/AMPLIFY_TYPES.graphql
 */

const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// Configuration
const MANIFEST_PATH = path.join(__dirname, '../../data/infra/NEON_SCHEMA_MANIFEST.yaml');
const OUTPUT_PATH = path.join(__dirname, '../../data/infra/AMPLIFY_TYPES.graphql');

// Type mapping: PostgreSQL → GraphQL/Amplify
const TYPE_MAP = {
  // Text types
  'text': 'String',
  'varchar': 'String',
  'character varying': 'String',
  'char': 'String',
  'character': 'String',

  // Numeric types - Integer
  'integer': 'Int',
  'int': 'Int',
  'int4': 'Int',
  'smallint': 'Int',
  'int2': 'Int',
  'serial': 'Int',

  // Numeric types - Big Integer (use String for safety)
  'bigint': 'String',
  'int8': 'String',
  'bigserial': 'String',

  // Numeric types - Float
  'numeric': 'Float',
  'decimal': 'Float',
  'real': 'Float',
  'float4': 'Float',
  'double precision': 'Float',
  'float8': 'Float',

  // Boolean
  'boolean': 'Boolean',
  'bool': 'Boolean',

  // Timestamp types
  'timestamp': 'AWSDateTime',
  'timestamptz': 'AWSDateTime',
  'timestamp with time zone': 'AWSDateTime',
  'timestamp without time zone': 'AWSDateTime',
  'date': 'AWSDate',
  'time': 'AWSTime',
  'timetz': 'AWSTime',

  // JSON types
  'json': 'AWSJSON',
  'jsonb': 'AWSJSON',

  // UUID
  'uuid': 'ID',

  // Binary
  'bytea': 'String'
};

/**
 * Main schema generation function
 */
async function generateAmplifySchema() {
  try {
    // Step 1: Load manifest
    console.log('🔍 Loading Neon schema manifest...');
    if (!fs.existsSync(MANIFEST_PATH)) {
      throw new Error(`Manifest not found: ${MANIFEST_PATH}`);
    }

    const manifestContent = fs.readFileSync(MANIFEST_PATH, 'utf8');
    const manifest = yaml.parse(manifestContent);
    console.log(`✅ Loaded manifest (version: ${manifest.version})`);
    console.log(`   Database: ${manifest.database.name}`);
    console.log(`   Schemas: ${manifest.schemas.length}\n`);

    // Step 2: Initialize GraphQL schema
    let graphqlSchema = `# AWS Amplify GraphQL Schema
# Generated from Neon PostgreSQL Manifest
# Version: 1.0
# Generated: ${new Date().toISOString()}
# Source Database: ${manifest.database.name}
# Manifest Version: ${manifest.version}

`;

    // Step 3: Transform each schema
    console.log('🔄 Transforming tables to GraphQL types...\n');

    const stats = {
      types: 0,
      fields: 0,
      models: 0,
      keys: 0,
      connections: 0
    };

    for (const schema of manifest.schemas) {
      console.log(`📁 Processing schema: ${schema.name}`);

      // Add schema comment
      graphqlSchema += `# Schema: ${schema.name}\n`;
      graphqlSchema += `# Tables: ${schema.tables.length} | Views: ${schema.views.length}\n\n`;

      // Transform tables to GraphQL types with @model directive
      for (const table of schema.tables) {
        const typeDefinition = transformTableToGraphQLType(schema.name, table, stats);
        graphqlSchema += typeDefinition + '\n\n';
        console.log(`   ├─ Type: ${toPascalCase(table.name)} (@model, ${table.columns.length} fields)`);
      }

      // Transform views to GraphQL types (read-only, no @model)
      for (const view of schema.views) {
        const typeDefinition = transformViewToGraphQLType(schema.name, view, stats);
        graphqlSchema += typeDefinition + '\n\n';
        console.log(`   ├─ Type: ${toPascalCase(view.name)}View (read-only, ${view.columns.length} fields)`);
      }

      console.log(`   └─ Completed ${schema.name}\n`);
    }

    // Step 4: Write output
    const outputDir = path.dirname(OUTPUT_PATH);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(OUTPUT_PATH, graphqlSchema);

    // Step 5: Summary
    console.log('='.repeat(60));
    console.log('✅ Amplify GraphQL schema generation complete!');
    console.log('='.repeat(60));
    console.log(`📄 Output: ${OUTPUT_PATH}`);
    console.log(`📊 Statistics:`);
    console.log(`   - GraphQL types: ${stats.types}`);
    console.log(`   - @model directives: ${stats.models}`);
    console.log(`   - @key directives: ${stats.keys}`);
    console.log(`   - @connection directives: ${stats.connections}`);
    console.log(`   - Total fields: ${stats.fields}`);
    console.log('='.repeat(60) + '\n');

  } catch (error) {
    console.error('\n❌ Error generating Amplify schema:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

/**
 * Transform PostgreSQL table to GraphQL type with @model directive
 */
function transformTableToGraphQLType(schemaName, table, stats) {
  const typeName = toPascalCase(table.name);
  stats.types++;
  stats.models++;

  let type = `# Source: ${schemaName}.${table.name}\n`;
  type += `type ${typeName} @model`;

  // Add @key directives for indexes
  const keyDirectives = [];

  // Primary key as default @key
  if (table.primary_key && table.primary_key.length > 0) {
    const pkFields = table.primary_key.map(col => toCamelCase(col)).join('", "');
    keyDirectives.push(`@key(fields: ["${pkFields}"])`);
    stats.keys++;
  }

  // Additional indexes as named @key directives
  if (table.indexes && table.indexes.length > 0) {
    for (const index of table.indexes) {
      // Skip primary key index (already added)
      if (index.name && index.name.includes('_pkey')) continue;

      const indexFields = index.columns.map(col => toCamelCase(col)).join('", "');
      const indexName = toSnakeCase(index.name);
      keyDirectives.push(`@key(name: "${indexName}", fields: ["${indexFields}"])`);
      stats.keys++;
    }
  }

  // Add all @key directives
  if (keyDirectives.length > 0) {
    type += ` ${keyDirectives.join(' ')}`;
  }

  type += ` {\n`;

  // Add fields
  for (const column of table.columns) {
    const field = transformColumnToGraphQLField(column, table);
    type += `  ${field}\n`;
    stats.fields++;
  }

  // Add connection fields for foreign keys
  if (table.foreign_keys && table.foreign_keys.length > 0) {
    type += `\n  # Foreign key relationships\n`;
    for (const fk of table.foreign_keys) {
      const connectionField = generateConnectionField(fk, stats);
      type += `  ${connectionField}\n`;
    }
  }

  type += `}`;

  return type;
}

/**
 * Transform PostgreSQL view to GraphQL type (read-only, no @model)
 */
function transformViewToGraphQLType(schemaName, view, stats) {
  const typeName = toPascalCase(view.name) + 'View';
  stats.types++;

  let type = `# Source: ${schemaName}.${view.name} (view - read-only)\n`;
  type += `type ${typeName} {\n`;

  // Add fields
  for (const column of view.columns) {
    const field = transformColumnToGraphQLField(column, null);
    type += `  ${field}\n`;
    stats.fields++;
  }

  type += `}`;

  return type;
}

/**
 * Transform PostgreSQL column to GraphQL field
 */
function transformColumnToGraphQLField(column, table) {
  const fieldName = toCamelCase(column.name);
  let graphqlType = mapPostgreSQLTypeToGraphQL(column.type, column.udt_name);

  // Handle arrays
  if (column.type && column.type.includes('ARRAY')) {
    const elementType = mapPostgreSQLTypeToGraphQL(
      column.type.replace('ARRAY', '').trim(),
      column.udt_name
    );
    graphqlType = `[${elementType}]`;
  }

  // Add non-null modifier if column is not nullable and not auto-generated
  let modifier = '';
  if (column.nullable === false && !isAutoGenerated(column, table)) {
    modifier = '!';
  }

  // Build field with comments
  let field = `${fieldName}: ${graphqlType}${modifier}`;

  // Add inline comment for PostgreSQL type
  field += ` # ${column.type}`;

  if (column.default) {
    field += `, default: ${column.default}`;
  }

  return field;
}

/**
 * Check if column is auto-generated (serial, default, etc.)
 */
function isAutoGenerated(column, table) {
  if (!column) return false;

  // Check if it's a primary key with serial type or default
  if (table && table.primary_key && table.primary_key.includes(column.name)) {
    if (column.type && (column.type.includes('serial') || column.type.includes('SERIAL'))) {
      return true;
    }
    if (column.default && (column.default.includes('nextval') || column.default.includes('gen_random_uuid'))) {
      return true;
    }
  }

  // Check for timestamp defaults
  if (column.default && (column.default.includes('now()') || column.default.includes('CURRENT_TIMESTAMP'))) {
    return true;
  }

  return false;
}

/**
 * Generate @connection field for foreign key
 */
function generateConnectionField(foreignKey, stats) {
  const fieldName = toCamelCase(foreignKey.column.replace('_id', ''));
  const targetType = toPascalCase(foreignKey.references.table);
  stats.connections++;

  return `${fieldName}Relation: ${targetType} @connection(fields: ["${toCamelCase(foreignKey.column)}"])`;
}

/**
 * Map PostgreSQL data type to GraphQL/Amplify type
 */
function mapPostgreSQLTypeToGraphQL(pgType, udtName) {
  if (!pgType) {
    return 'String'; // Default fallback
  }

  // Normalize type
  const normalizedType = pgType.toLowerCase().trim();

  // Check for array type
  if (normalizedType.includes('array') || normalizedType.includes('[]')) {
    return 'String'; // Will be wrapped in [Type] by caller
  }

  // Direct mapping
  if (TYPE_MAP[normalizedType]) {
    return TYPE_MAP[normalizedType];
  }

  // Check UDT name for additional context
  if (udtName) {
    const normalizedUdt = udtName.toLowerCase();
    if (TYPE_MAP[normalizedUdt]) {
      return TYPE_MAP[normalizedUdt];
    }

    // Handle UDT array types
    if (normalizedUdt.startsWith('_')) {
      return 'String'; // Will be wrapped in [Type]
    }
  }

  // Special cases
  if (normalizedType.includes('int')) {
    return 'Int';
  }
  if (normalizedType.includes('char') || normalizedType.includes('text')) {
    return 'String';
  }
  if (normalizedType.includes('time') || normalizedType.includes('date')) {
    return 'AWSDateTime';
  }
  if (normalizedType.includes('json')) {
    return 'AWSJSON';
  }
  if (normalizedType.includes('bool')) {
    return 'Boolean';
  }
  if (normalizedType.includes('uuid')) {
    return 'ID';
  }

  // Unknown types default to String
  console.warn(`⚠️  Unknown type mapping: ${pgType} (UDT: ${udtName}) - defaulting to 'String'`);
  return 'String';
}

/**
 * Convert snake_case to PascalCase
 */
function toPascalCase(str) {
  return str
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
}

/**
 * Convert snake_case to camelCase
 */
function toCamelCase(str) {
  const pascal = toPascalCase(str);
  return pascal.charAt(0).toLowerCase() + pascal.slice(1);
}

/**
 * Convert to snake_case
 */
function toSnakeCase(str) {
  return str
    .replace(/([A-Z])/g, '_$1')
    .toLowerCase()
    .replace(/^_/, '');
}

// Run generation
generateAmplifySchema().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});
