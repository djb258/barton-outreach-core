/**
 * Barton Outreach Core – MillionVerify Runner
 * Enforces Barton Doctrine: unique_id, process_id, Firebase working memory, Neon vault, audit logging.
 * ALL external operations go through Composio MCP tools
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { postToAuditLog } from "../../ops/orbt/auditLogger.js";
import { insertIntoNeon, queryFromNeon } from "../../ops/orbt/neonWriter.js";
import { checkHistoryBeforeRun, recordHistoryEntry } from "../../ops/orbt/historyEnforcer.js";
import dotenv from 'dotenv';

dotenv.config();

const PROCESS_ID = "Verify Email with MillionVerify";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const MILLIONVERIFY_API_KEY = process.env.MILLIONVERIFY_API_KEY;

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
 * Query shq_process_key_reference to generate proper unique_id
 * Format: [db].[subhive].[microprocess].[tool].[altitude].[step]
 */
async function generateUniqueId(contactUniqueId, stepNumber = 1) {
  try {
    // Query the process key reference table for correct mapping
    const query = `
      SELECT
        database_id,
        subhive_id,
        microprocess_id,
        tool_id,
        altitude
      FROM marketing.shq_process_key_reference
      WHERE process_name = 'MillionVerify Email Verifier'
      LIMIT 1
    `;

    const result = await queryFromNeon(query, [], {
      process_id: PROCESS_ID
    });

    if (result.rows && result.rows.length > 0) {
      const mapping = result.rows[0];
      const timestamp = Date.now();
      const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();

      return `${mapping.database_id || '04'}.${mapping.subhive_id || '02'}.${mapping.microprocess_id || '03'}.${mapping.tool_id || '09'}.${mapping.altitude || '9000'}.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
    }
  } catch (error) {
    console.warn('Could not query process key reference, using defaults:', error.message);
  }

  // Fallback to default values if query fails
  const timestamp = Date.now();
  const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();
  return `04.02.03.09.9000.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
}

/**
 * Generate Barton ID for verification records
 */
function generateVerificationBartonId() {
  const timestamp = Date.now();
  const segment1 = String(timestamp % 100).padStart(2, '0');
  const segment2 = String((timestamp >> 8) % 100).padStart(2, '0');
  const segment3 = String(Math.floor(Math.random() * 100)).padStart(2, '0');
  const segment4 = '09'; // Verification tool designation
  const segment5 = String(Math.floor(Math.random() * 100000)).padStart(5, '0');
  const segment6 = String(Math.floor(Math.random() * 1000)).padStart(3, '0');

  return `${segment1}.${segment2}.${segment3}.${segment4}.${segment5}.${segment6}`;
}

// Removed - now using historyEnforcer.checkHistoryBeforeRun()

/**
 * Call MillionVerify through Composio MCP
 */
async function callMillionVerifyMCP(email, uniqueId) {
  if (!MILLIONVERIFY_API_KEY) {
    throw new Error('MILLIONVERIFY_API_KEY not configured in environment');
  }

  const verifyPayload = {
    tool: "millionverify.verify_email",
    params: {
      api_key: MILLIONVERIFY_API_KEY,
      email: email,
      timeout: 30
    },
    metadata: {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      orbt_layer: 9000,
      blueprint_version: "1.0",
      timestamp: new Date().toISOString()
    }
  };

  console.log(`🔍 Verifying email: ${email}`);

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(verifyPayload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`MillionVerify MCP call failed: ${response.statusText} - ${errorText}`);
  }

  const verifyResult = await response.json();
  return verifyResult.data || verifyResult;
}

/**
 * Normalize MillionVerify results into standard schema
 */
function normalizeVerificationResult(mvResult, contactUniqueId, email, uniqueId) {
  const timestamp = new Date().toISOString();

  // Map MillionVerify result codes to our standard status
  let verificationStatus = 'unknown';
  let confidence = 50;

  if (mvResult.result) {
    switch (mvResult.result.toLowerCase()) {
      case 'ok':
      case 'valid':
      case 'deliverable':
        verificationStatus = 'valid';
        confidence = 95;
        break;
      case 'invalid':
      case 'bad':
      case 'undeliverable':
        verificationStatus = 'invalid';
        confidence = 95;
        break;
      case 'risky':
      case 'catch_all':
      case 'accept_all':
      case 'unknown':
        verificationStatus = 'risky';
        confidence = 60;
        break;
      default:
        verificationStatus = 'unknown';
        confidence = 30;
    }
  }

  // If result_code exists, use it for additional confidence adjustment
  if (mvResult.result_code) {
    confidence = Math.min(mvResult.result_code, 100);
  }

  return {
    // Required schema fields
    contact_unique_id: contactUniqueId,
    email: email,
    verification_status: verificationStatus,
    confidence: confidence,
    source: 'millionverify',
    timestamp: timestamp,

    // Additional verification metadata
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    altitude: 9000,

    // MillionVerify specific fields
    result: mvResult.result || null,
    result_code: mvResult.result_code || null,
    credits: mvResult.credits || null,
    free_email: mvResult.free_email || false,
    role_account: mvResult.role_account || false,
    disposable: mvResult.disposable || false,

    // Status tracking
    status: "verified",
    verified_at: timestamp,
    created_at: timestamp,
    updated_at: timestamp
  };
}

/**
 * Write verification to Firebase (working memory)
 */
async function writeToFirebase(verification, contactUniqueId) {
  const db = initFirebase();

  // Write to agent_whiteboard collection
  const whiteboardRef = db
    .collection('agent_whiteboard')
    .doc(`${contactUniqueId}_verification`);

  await whiteboardRef.set({
    ...verification,
    firebase_write_timestamp: new Date().toISOString(),
    collection_type: "millionverify_results"
  });

  // Also write to person_history for History Layer tracking
  const historyRef = db.collection('person_history').doc();

  await historyRef.set({
    person_id: contactUniqueId,
    field: 'email_verification',
    value_found: verification.verification_status,
    source: 'millionverify',
    timestamp_found: new Date(),
    confidence_score: verification.confidence / 100,
    process_id: PROCESS_ID,
    session_id: verification.unique_id,
    change_reason: 'email_verification',
    metadata: {
      result: verification.result,
      result_code: verification.result_code,
      free_email: verification.free_email,
      disposable: verification.disposable
    }
  });

  console.log(`✅ Wrote verification to Firebase: ${contactUniqueId}`);
}

/**
 * Main MillionVerify runner with full Barton Doctrine compliance
 */
export async function runMillionVerify({ contact_unique_id, email, force = false }) {
  const startTime = Date.now();
  const uniqueId = await generateUniqueId(contact_unique_id, 1);
  const runTimestamp = new Date().toISOString();

  console.log(`\n🚀 Starting MillionVerify for contact: ${contact_unique_id}`);
  console.log(`📧 Email: ${email}`);
  console.log(`🔑 Unique ID: ${uniqueId}`);

  // 1️⃣ Check History Layer to prevent redundant verification
  const historyCheck = await checkHistoryBeforeRun({
    entity_id: contact_unique_id,
    field: 'email_verification',
    windowDays: 7,
    forceRun: force,
    strategy: 'firebase-first'
  });

  if (!historyCheck.shouldRun) {
    console.log(`⏭️ Skipping verification - recently verified`);

    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id: null,
      status: "Skipped",
      source: "millionverify-runner",
      altitude: 9000,
      domain_url: email,
      skip_reason: historyCheck.reason,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString(),
      metadata: {
        last_run: historyCheck.lastRun,
        data_source: historyCheck.data_source
      }
    });

    return {
      success: true,
      skipped: true,
      reason: historyCheck.reason,
      last_run: historyCheck.lastRun,
      contact_unique_id,
      email
    };
  }

  // 2️⃣ Audit start
  await postToAuditLog({
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    company_unique_id: null, // Can be null for contact-level operations
    status: "Pending",
    source: "millionverify-runner",
    altitude: 9000,
    domain_url: email,
    started_at: runTimestamp,
    timestamp: runTimestamp
  });

  try {
    // 3️⃣ Call MillionVerify through Composio MCP
    const mvResult = await callMillionVerifyMCP(email, uniqueId);
    console.log(`📊 MillionVerify returned result:`, mvResult.result || 'unknown');

    // 4️⃣ Normalize verification result to standard schema
    const verification = normalizeVerificationResult(mvResult, contact_unique_id, email, uniqueId);
    console.log(`✨ Normalized result: ${verification.verification_status} (${verification.confidence}% confidence)`);

    // 5️⃣ Write to Firebase (working memory)
    await writeToFirebase(verification, contact_unique_id);

    // 6️⃣ Write to Neon vault (permanent storage)
    await insertIntoNeon("marketing.contact_verification", [verification], {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      on_conflict: "do_update" // Update if exists
    });

    // 7️⃣ Record in History Layer
    await recordHistoryEntry({
      entity_id: contact_unique_id,
      field: 'email_verification',
      value_found: verification.verification_status,
      source: 'millionverify',
      process_id: PROCESS_ID,
      confidence_score: verification.confidence / 100,
      metadata: {
        email: email,
        result: verification.result,
        result_code: verification.result_code,
        free_email: verification.free_email,
        disposable: verification.disposable
      }
    });

    // 8️⃣ Audit success
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id: null,
      status: "Success",
      source: "millionverify-runner",
      altitude: 9000,
      domain_url: email,
      records_scraped: 1,
      metadata: {
        verification_status: verification.verification_status,
        confidence: verification.confidence,
        result: verification.result
      },
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.log(`\n✅ MillionVerify completed successfully!`);
    console.log(`📈 Result: ${verification.verification_status} (${verification.confidence}% confidence)`);
    console.log(`⏱️ Duration: ${duration}ms`);

    return {
      success: true,
      unique_id: uniqueId,
      contact_unique_id,
      email,
      verification,
      duration_ms: duration
    };

  } catch (error) {
    // 8️⃣ Audit failure
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id: null,
      status: "Failed",
      source: "millionverify-runner",
      altitude: 9000,
      domain_url: email,
      error: error.message,
      error_stack: error.stack,
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.error(`\n❌ MillionVerify failed for ${contact_unique_id}:`, error.message);
    throw error;
  }
}

/**
 * CLI runner
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  // Parse command line arguments
  const args = process.argv.slice(2);
  let contactId, email;
  const forceRun = args.includes('--force');

  // Support both positional and named arguments
  if (args[0]?.startsWith('--contact=')) {
    // Named arguments: --contact=CNT-123 --email=test@example.com
    const parseArg = (arg, name) => {
      const prefix = `--${name}=`;
      const found = args.find(a => a.startsWith(prefix));
      return found ? found.slice(prefix.length) : null;
    };

    contactId = parseArg(args, 'contact');
    email = parseArg(args, 'email');
  } else {
    // Positional arguments: <contact_id> <email>
    const positionalArgs = args.filter(a => !a.startsWith('--'));
    [contactId, email] = positionalArgs;
  }

  if (!contactId || !email) {
    console.log('\n📖 Usage:');
    console.log('  npm run verify:email -- --contact=<id> --email=<email> [--force]');
    console.log('  npm run verify:email -- <contact_id> <email> [--force]');
    console.log('\n📋 Examples:');
    console.log('  npm run verify:email -- --contact=CNT-12345 --email=test@example.com');
    console.log('  npm run verify:email -- CNT-12345 test@example.com');
    console.log('  npm run verify:email -- --contact=CNT-12345 --email=test@example.com --force');
    console.log('\nOptions:');
    console.log('  --force    Force run (bypass history check)');
    process.exit(1);
  }

  console.log('\n🏁 Starting MillionVerify Runner');
  console.log('─'.repeat(50));
  if (forceRun) {
    console.log('🔓 Force run enabled - bypassing history check');
  }

  runMillionVerify({
    contact_unique_id: contactId,
    email: email,
    force: forceRun
  })
    .then(result => {
      if (result.skipped) {
        console.log('\n⏭️ Verification skipped (recently verified)');
      } else {
        console.log('\n🎉 Verification completed successfully!');
      }
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 Verification failed:', error.message);
      process.exit(1);
    });
}

export default runMillionVerify;