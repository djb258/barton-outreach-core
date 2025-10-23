#!/usr/bin/env node
/**
 * CTB Metadata
 * Barton ID: 03.01.04.20251023.gfss.001
 * Branch: ai
 * Altitude: 30k (HEIR - Hierarchical Execution Intelligence & Repair)
 * Purpose: Transform Neon PostgreSQL manifest to Firestore schema specification
 * Dependencies: yaml@^2.3.0
 * Input: ctb/data/infra/NEON_SCHEMA_MANIFEST.yaml
 * Output: ctb/data/infra/FIRESTORE_SCHEMA.json
 */

const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

// Configuration
const MANIFEST_PATH = path.join(__dirname, '../../data/infra/NEON_SCHEMA_MANIFEST.yaml');
const OUTPUT_PATH = path.join(__dirname, '../../data/infra/FIRESTORE_SCHEMA.json');

// Type mapping: PostgreSQL → Firestore
const TYPE_MAP = {
  // Text types
  'text': 'string',
  'varchar': 'string',
  'character varying': 'string',
  'char': 'string',
  'character': 'string',

  // Numeric types
  'integer': 'number',
  'int': 'number',
  'int4': 'number',
  'smallint': 'number',
  'int2': 'number',
  'bigint': 'number',
  'int8': 'number',
  'serial': 'number',
  'bigserial': 'number',
  'numeric': 'number',
  'decimal': 'number',
  'real': 'number',
  'float4': 'number',
  'double precision': 'number',
  'float8': 'number',

  // Boolean
  'boolean': 'boolean',
  'bool': 'boolean',

  // Timestamp types
  'timestamp': 'timestamp',
  'timestamptz': 'timestamp',
  'timestamp with time zone': 'timestamp',
  'timestamp without time zone': 'timestamp',
  'date': 'timestamp',
  'time': 'timestamp',
  'timetz': 'timestamp',

  // JSON types
  'json': 'map',
  'jsonb': 'map',

  // UUID
  'uuid': 'string',

  // Arrays (handled specially)
  'ARRAY': 'array',

  // Binary
  'bytea': 'bytes'
};

/**
 * Main transformation function
 */
async function generateFirestoreSchema() {
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

    // Step 2: Initialize Firestore schema
    const firestoreSchema = {
      version: '1.0',
      generated: new Date().toISOString(),
      source: {
        database: manifest.database.name,
        manifest_version: manifest.version,
        manifest_generated: manifest.generated
      },
      collections: []
    };

    // Step 3: Transform each schema
    console.log('🔄 Transforming schemas to Firestore collections...\n');

    for (const schema of manifest.schemas) {
      console.log(`📁 Processing schema: ${schema.name}`);

      // Transform tables to collections
      for (const table of schema.tables) {
        const collection = transformTableToCollection(schema.name, table);
        firestoreSchema.collections.push(collection);
        console.log(`   ├─ Collection: ${collection.name} (${collection.fields.length} fields)`);
      }

      // Transform views to read-only collections
      for (const view of schema.views) {
        const collection = transformViewToCollection(schema.name, view);
        firestoreSchema.collections.push(collection);
        console.log(`   ├─ View Collection: ${collection.name} (read-only, ${collection.fields.length} fields)`);
      }

      console.log(`   └─ Total: ${schema.tables.length} tables + ${schema.views.length} views\n`);
    }

    // Step 4: Write output
    const outputDir = path.dirname(OUTPUT_PATH);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(firestoreSchema, null, 2));

    // Step 5: Summary
    console.log('='.repeat(60));
    console.log('✅ Firestore schema generation complete!');
    console.log('='.repeat(60));
    console.log(`📄 Output: ${OUTPUT_PATH}`);
    console.log(`📊 Statistics:`);
    console.log(`   - Total collections: ${firestoreSchema.collections.length}`);
    console.log(`   - Source schemas: ${manifest.schemas.length}`);
    console.log(`   - Total fields: ${firestoreSchema.collections.reduce((sum, c) => sum + c.fields.length, 0)}`);
    console.log(`   - Total indexes: ${firestoreSchema.collections.reduce((sum, c) => sum + c.indexes.length, 0)}`);
    console.log('='.repeat(60) + '\n');

  } catch (error) {
    console.error('\n❌ Error generating Firestore schema:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

/**
 * Transform PostgreSQL table to Firestore collection
 */
function transformTableToCollection(schemaName, table) {
  const collection = {
    name: `${schemaName}_${table.name}`,
    description: `Firestore mirror of ${schemaName}.${table.name}`,
    source: {
      schema: schemaName,
      table: table.name,
      type: 'table'
    },
    read_only: false,
    fields: [],
    indexes: [],
    constraints: {
      primary_key: table.primary_key || [],
      foreign_keys: table.foreign_keys || []
    }
  };

  // Transform columns to fields
  for (const column of table.columns) {
    const field = transformColumnToField(column);
    collection.fields.push(field);
  }

  // Transform indexes
  if (table.indexes && table.indexes.length > 0) {
    for (const index of table.indexes) {
      collection.indexes.push({
        name: index.name,
        fields: index.columns || [],
        unique: index.unique || false,
        source: 'postgresql_index'
      });
    }
  }

  // Add primary key as index if exists
  if (table.primary_key && table.primary_key.length > 0) {
    collection.indexes.push({
      name: `${table.name}_pk`,
      fields: table.primary_key,
      unique: true,
      source: 'primary_key'
    });
  }

  return collection;
}

/**
 * Transform PostgreSQL view to read-only Firestore collection
 */
function transformViewToCollection(schemaName, view) {
  const collection = {
    name: `${schemaName}_${view.name}`,
    description: `Read-only Firestore mirror of view ${schemaName}.${view.name}`,
    source: {
      schema: schemaName,
      table: view.name,
      type: 'view'
    },
    read_only: true,
    fields: [],
    indexes: [],
    constraints: {
      note: 'Views do not have primary keys or foreign keys in Firestore'
    }
  };

  // Transform columns to fields
  for (const column of view.columns) {
    const field = transformColumnToField(column);
    collection.fields.push(field);
  }

  return collection;
}

/**
 * Transform PostgreSQL column to Firestore field
 */
function transformColumnToField(column) {
  const field = {
    name: column.name,
    type: mapPostgreSQLTypeToFirestore(column.type, column.udt_name),
    nullable: column.nullable !== false,
    source: {
      postgres_type: column.type,
      postgres_udt: column.udt_name
    }
  };

  // Add metadata for specific types
  if (column.max_length) {
    field.metadata = field.metadata || {};
    field.metadata.max_length = column.max_length;
  }

  if (column.precision) {
    field.metadata = field.metadata || {};
    field.metadata.precision = column.precision;
  }

  if (column.scale) {
    field.metadata = field.metadata || {};
    field.metadata.scale = column.scale;
  }

  if (column.default) {
    field.metadata = field.metadata || {};
    field.metadata.default_expression = column.default;
  }

  // Handle array types
  if (column.type && column.type.includes('ARRAY')) {
    field.type = 'array';
    field.metadata = field.metadata || {};
    field.metadata.array_element_type = mapPostgreSQLTypeToFirestore(
      column.type.replace('ARRAY', '').trim(),
      column.udt_name
    );
  }

  return field;
}

/**
 * Map PostgreSQL data type to Firestore type
 */
function mapPostgreSQLTypeToFirestore(pgType, udtName) {
  if (!pgType) {
    return 'string'; // Default fallback
  }

  // Normalize type
  const normalizedType = pgType.toLowerCase().trim();

  // Check for array type
  if (normalizedType.includes('array') || normalizedType.includes('[]')) {
    return 'array';
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
      return 'array';
    }
  }

  // Special cases
  if (normalizedType.includes('int')) {
    return 'number';
  }
  if (normalizedType.includes('char') || normalizedType.includes('text')) {
    return 'string';
  }
  if (normalizedType.includes('time') || normalizedType.includes('date')) {
    return 'timestamp';
  }
  if (normalizedType.includes('json')) {
    return 'map';
  }
  if (normalizedType.includes('bool')) {
    return 'boolean';
  }

  // Unknown types default to string
  console.warn(`⚠️  Unknown type mapping: ${pgType} (UDT: ${udtName}) - defaulting to 'string'`);
  return 'string';
}

// Run generation
generateFirestoreSchema().catch(err => {
  console.error('❌ Fatal error:', err.message);
  process.exit(1);
});
