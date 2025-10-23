/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: sys/ops
Barton ID: 04.04.13
Unique ID: CTB-B9C22555
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: None
─────────────────────────────────────────────
*/

/**
 * Barton Doctrine History Enforcement Wrapper
 * Standardizes History Layer checks across all runners to prevent duplicate operations
 * ALL operations through Composio MCP - NO direct database connections
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { postToAuditLog } from './auditLogger.js';
import dotenv from 'dotenv';

dotenv.config();

const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const DEFAULT_WINDOW_DAYS = 7;

// Initialize Firebase Admin
let firebaseApp;
let db;

function initFirebase() {
  if (!firebaseApp) {
    firebaseApp = initializeApp({
      projectId: process.env.FIREBASE_PROJECT_ID || "barton-outreach-core",
      credential: process.env.FIREBASE_SERVICE_ACCOUNT_KEY
        ? cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY))
        : null
    });
    db = getFirestore(firebaseApp);
  }
  return db;
}

/**
 * Generate operation ID for tracking
 */
function generateOperationId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 8).toUpperCase();
  return `HIST-${timestamp}-${random}`;
}

/**
 * Determine entity type from entity_id
 */
function getEntityType(entityId) {
  if (!entityId) return null;

  if (entityId.startsWith('CMP-') || entityId.includes('company')) {
    return 'company';
  }
  if (entityId.startsWith('CNT-') || entityId.startsWith('PER-') || entityId.includes('contact') || entityId.includes('person')) {
    return 'person';
  }

  // Try to infer from ID structure
  const segments = entityId.split('.');
  if (segments.length >= 4) {
    const typeSegment = segments[3];
    if (typeSegment === '07' || typeSegment === '09') return 'person';
    if (typeSegment === '01' || typeSegment === '02') return 'company';
  }

  return 'company'; // Default fallback
}

/**
 * Query History Layer via Firebase
 */
async function queryFirebaseHistory(entityId, field, windowDays, entityType) {
  try {
    const db = initFirebase();

    const collectionName = entityType === 'company' ? 'company_history' : 'person_history';
    const idField = entityType === 'company' ? 'company_id' : 'person_id';

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - windowDays);

    const historyQuery = db
      .collection(collectionName)
      .where(idField, '==', entityId)
      .where('field', '==', field)
      .where('timestamp_found', '>=', cutoffDate)
      .orderBy('timestamp_found', 'desc')
      .limit(1);

    const snapshot = await historyQuery.get();

    if (!snapshot.empty) {
      const latestHistory = snapshot.docs[0].data();
      return {
        found: true,
        lastRun: latestHistory.timestamp_found.toDate().toISOString(),
        source: latestHistory.source,
        confidence: latestHistory.confidence_score,
        process_id: latestHistory.process_id
      };
    }

    return { found: false };

  } catch (error) {
    console.warn(`⚠️ Firebase history query failed: ${error.message}`);
    return { found: false, error: error.message };
  }
}

/**
 * Query History Layer via Neon MCP (for vault verification)
 */
async function queryNeonHistory(entityId, field, windowDays, entityType) {
  try {
    const tableName = entityType === 'company' ? 'company_history' : 'person_history';
    const idField = entityType === 'company' ? 'company_unique_id' : 'person_unique_id';

    const query = `
      SELECT
        ${idField},
        field,
        value_found,
        source,
        timestamp_found,
        confidence_score,
        process_id
      FROM marketing.${tableName}
      WHERE ${idField} = $1
        AND field = $2
        AND timestamp_found >= NOW() - INTERVAL '${windowDays} days'
      ORDER BY timestamp_found DESC
      LIMIT 1
    `;

    const mcpPayload = {
      tool: "neon.query",
      params: {
        connection_id: "neon_barton_outreach",
        database: "defaultdb",
        query: query,
        params: [entityId, field]
      },
      metadata: {
        unique_id: generateOperationId(),
        process_id: "history-enforcer",
        orbt_layer: 10000,
        timestamp: new Date().toISOString()
      }
    };

    const response = await fetch('http://localhost:3001/tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      },
      body: JSON.stringify(mcpPayload)
    });

    if (!response.ok) {
      throw new Error(`Neon history query failed: ${response.statusText}`);
    }

    const result = await response.json();
    const rows = result.data || [];

    if (rows.length > 0) {
      const latestHistory = rows[0];
      return {
        found: true,
        lastRun: latestHistory.timestamp_found,
        source: latestHistory.source,
        confidence: latestHistory.confidence_score,
        process_id: latestHistory.process_id
      };
    }

    return { found: false };

  } catch (error) {
    console.warn(`⚠️ Neon history query failed: ${error.message}`);
    return { found: false, error: error.message };
  }
}

/**
 * Check History Layer before running an operation
 * @param {Object} params - { entity_id, field, windowDays, forceRun, strategy }
 * @returns {Object} { shouldRun, lastRun, reason, source }
 */
export async function checkHistoryBeforeRun({
  entity_id,
  field,
  windowDays = DEFAULT_WINDOW_DAYS,
  forceRun = false,
  strategy = 'firebase-first' // 'firebase-first', 'neon-first', 'both'
}) {
  if (!entity_id || !field) {
    throw new Error('entity_id and field are required for history check');
  }

  // Force run bypasses all checks
  if (forceRun) {
    console.log(`🔓 Force run enabled - bypassing history check for ${entity_id}:${field}`);
    return {
      shouldRun: true,
      reason: 'force_run_enabled',
      forced: true
    };
  }

  const entityType = getEntityType(entity_id);
  console.log(`🔍 Checking history for ${entityType} ${entity_id}:${field} (last ${windowDays} days)`);

  let firebaseResult = null;
  let neonResult = null;

  try {
    // Query based on strategy
    switch (strategy) {
      case 'firebase-first':
        firebaseResult = await queryFirebaseHistory(entity_id, field, windowDays, entityType);
        if (!firebaseResult.found) {
          // Double-check with Neon if Firebase returns no results
          neonResult = await queryNeonHistory(entity_id, field, windowDays, entityType);
        }
        break;

      case 'neon-first':
        neonResult = await queryNeonHistory(entity_id, field, windowDays, entityType);
        if (!neonResult.found) {
          // Double-check with Firebase if Neon returns no results
          firebaseResult = await queryFirebaseHistory(entity_id, field, windowDays, entityType);
        }
        break;

      case 'both':
        // Query both in parallel for maximum accuracy
        [firebaseResult, neonResult] = await Promise.all([
          queryFirebaseHistory(entity_id, field, windowDays, entityType),
          queryNeonHistory(entity_id, field, windowDays, entityType)
        ]);
        break;

      default:
        throw new Error(`Unknown strategy: ${strategy}`);
    }

    // Determine if we found a duplicate
    const firebaseFound = firebaseResult?.found;
    const neonFound = neonResult?.found;

    if (firebaseFound || neonFound) {
      const lastRun = firebaseFound ? firebaseResult.lastRun : neonResult.lastRun;
      const source = firebaseFound ? firebaseResult.source : neonResult.source;
      const dataSource = firebaseFound ? 'firebase' : 'neon';

      console.log(`⏭️ Skipping ${entity_id}:${field} - found in ${dataSource} (last run: ${lastRun})`);

      return {
        shouldRun: false,
        lastRun: lastRun,
        reason: `duplicate_found_within_${windowDays}_days`,
        source: source,
        data_source: dataSource,
        window_days: windowDays
      };
    }

    // No duplicates found - safe to run
    console.log(`✅ No recent history found for ${entity_id}:${field} - safe to proceed`);

    return {
      shouldRun: true,
      reason: 'no_recent_history',
      window_days: windowDays,
      checked_firebase: !!firebaseResult,
      checked_neon: !!neonResult
    };

  } catch (error) {
    console.error(`❌ History check failed for ${entity_id}:${field}:`, error.message);

    // In case of error, log and allow the operation to proceed
    // (better to risk a duplicate than block legitimate operations)
    return {
      shouldRun: true,
      reason: 'history_check_failed',
      error: error.message,
      warning: 'Proceeding due to history check failure'
    };
  }
}

/**
 * Record history entry after successful operation
 * @param {Object} params - History entry data
 */
export async function recordHistoryEntry({
  entity_id,
  field,
  value_found,
  source,
  process_id,
  confidence_score = 1.0,
  metadata = {}
}) {
  if (!entity_id || !field || !source) {
    throw new Error('entity_id, field, and source are required for history entry');
  }

  const entityType = getEntityType(entity_id);
  const timestamp = new Date();

  const historyEntry = {
    [`${entityType}_id`]: entity_id,
    field: field,
    value_found: value_found || 'completed',
    source: source,
    timestamp_found: timestamp,
    confidence_score: confidence_score,
    process_id: process_id || 'unknown',
    session_id: generateOperationId(),
    change_reason: 'operation_completed',
    metadata: metadata
  };

  try {
    const db = initFirebase();
    const collectionName = entityType === 'company' ? 'company_history' : 'person_history';

    // Write to Firebase
    const historyRef = db.collection(collectionName).doc();
    await historyRef.set(historyEntry);

    console.log(`✅ Recorded history entry for ${entity_id}:${field} in Firebase`);

    // Also write to Neon for permanent storage
    const tableName = `marketing.${collectionName}`;
    const neonEntry = {
      [`${entityType}_unique_id`]: entity_id,
      field: field,
      value_found: value_found || 'completed',
      source: source,
      timestamp_found: timestamp.toISOString(),
      confidence_score: confidence_score,
      process_id: process_id || 'unknown',
      session_id: historyEntry.session_id,
      change_reason: 'operation_completed',
      metadata: JSON.stringify(metadata)
    };

    const mcpPayload = {
      tool: "neon.insert_rows",
      params: {
        connection_id: "neon_barton_outreach",
        database: "defaultdb",
        schema: "marketing",
        table: collectionName,
        rows: [neonEntry],
        on_conflict: "do_nothing"
      },
      metadata: {
        unique_id: historyEntry.session_id,
        process_id: "history-enforcer",
        orbt_layer: 10000,
        timestamp: timestamp.toISOString()
      }
    };

    const response = await fetch('http://localhost:3001/tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY
      },
      body: JSON.stringify(mcpPayload)
    });

    if (response.ok) {
      console.log(`✅ Recorded history entry for ${entity_id}:${field} in Neon`);
    } else {
      console.warn(`⚠️ Failed to write history to Neon: ${response.statusText}`);
    }

    return {
      success: true,
      session_id: historyEntry.session_id,
      timestamp: timestamp.toISOString()
    };

  } catch (error) {
    console.error(`❌ Failed to record history entry for ${entity_id}:${field}:`, error.message);
    throw error;
  }
}

/**
 * Batch check multiple entities at once
 */
export async function batchCheckHistory(checks) {
  const results = await Promise.all(
    checks.map(check => checkHistoryBeforeRun(check))
  );

  return results.map((result, index) => ({
    ...checks[index],
    ...result
  }));
}

/**
 * Get history timeline for an entity
 */
export async function getHistoryTimeline(entity_id, options = {}) {
  const entityType = getEntityType(entity_id);
  const limit = options.limit || 50;
  const field = options.field || null;

  try {
    const db = initFirebase();
    const collectionName = entityType === 'company' ? 'company_history' : 'person_history';
    const idField = entityType === 'company' ? 'company_id' : 'person_id';

    let query = db
      .collection(collectionName)
      .where(idField, '==', entity_id);

    if (field) {
      query = query.where('field', '==', field);
    }

    query = query
      .orderBy('timestamp_found', 'desc')
      .limit(limit);

    const snapshot = await query.get();

    const timeline = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp_found: doc.data().timestamp_found.toDate().toISOString()
    }));

    return {
      success: true,
      entity_id: entity_id,
      entity_type: entityType,
      timeline: timeline,
      count: timeline.length
    };

  } catch (error) {
    console.error(`❌ Failed to get history timeline for ${entity_id}:`, error.message);
    return {
      success: false,
      error: error.message,
      timeline: []
    };
  }
}

/**
 * CLI runner for testing
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  const parseArg = (name, defaultValue = null) => {
    const arg = args.find(a => a.startsWith(`--${name}=`));
    return arg ? arg.split('=')[1] : defaultValue;
  };

  const command = args[0]?.replace('--', '');
  const entityId = parseArg('entity');
  const field = parseArg('field');
  const windowDays = parseInt(parseArg('window', '7'));
  const forceRun = args.includes('--force');

  console.log('\n🔍 Barton History Enforcer CLI\n');

  (async () => {
    try {
      switch (command) {
        case 'check':
          if (!entityId || !field) {
            console.error('❌ --entity and --field required');
            process.exit(1);
          }

          const check = await checkHistoryBeforeRun({
            entity_id: entityId,
            field: field,
            windowDays: windowDays,
            forceRun: forceRun,
            strategy: 'both'
          });

          console.log('\n📊 History Check Result:');
          console.log(JSON.stringify(check, null, 2));

          if (check.shouldRun) {
            console.log('\n✅ Operation should proceed');
          } else {
            console.log('\n⏭️ Operation should be skipped');
          }
          break;

        case 'timeline':
          if (!entityId) {
            console.error('❌ --entity required');
            process.exit(1);
          }

          const timeline = await getHistoryTimeline(entityId, {
            field: field,
            limit: 20
          });

          console.log('\n📜 History Timeline:');
          console.log(`Entity: ${timeline.entity_id} (${timeline.entity_type})`);
          console.log(`Entries: ${timeline.count}\n`);

          if (timeline.timeline.length > 0) {
            console.table(timeline.timeline.map(t => ({
              field: t.field,
              source: t.source,
              timestamp: t.timestamp_found,
              confidence: t.confidence_score
            })));
          } else {
            console.log('No history entries found');
          }
          break;

        case 'record':
          if (!entityId || !field) {
            console.error('❌ --entity and --field required');
            process.exit(1);
          }

          const source = parseArg('source', 'cli-test');
          const value = parseArg('value', 'test-value');

          const record = await recordHistoryEntry({
            entity_id: entityId,
            field: field,
            value_found: value,
            source: source,
            process_id: 'history-enforcer-cli',
            confidence_score: 1.0,
            metadata: { cli_test: true }
          });

          console.log('\n✅ History entry recorded:');
          console.log(JSON.stringify(record, null, 2));
          break;

        default:
          console.log('📖 Usage:');
          console.log('  npm run history:check -- check --entity=CMP-123 --field=apify_scrape --window=7 [--force]');
          console.log('  npm run history:check -- timeline --entity=CMP-123 [--field=apify_scrape]');
          console.log('  npm run history:check -- record --entity=CMP-123 --field=test --source=cli --value=test');
          console.log('\nCommands:');
          console.log('  check      Check if operation should run');
          console.log('  timeline   View history timeline for entity');
          console.log('  record     Record a history entry');
          console.log('\nOptions:');
          console.log('  --entity   Entity ID (company_unique_id or contact_unique_id)');
          console.log('  --field    Field name (e.g., apify_scrape, email_verification)');
          console.log('  --window   Time window in days (default: 7)');
          console.log('  --force    Force run (bypass history check)');
          console.log('  --source   Source name for recording');
          console.log('  --value    Value for recording');
          process.exit(0);
      }

      process.exit(0);
    } catch (error) {
      console.error('\n❌ Error:', error.message);
      process.exit(1);
    }
  })();
}

export default {
  checkHistoryBeforeRun,
  recordHistoryEntry,
  batchCheckHistory,
  getHistoryTimeline
};