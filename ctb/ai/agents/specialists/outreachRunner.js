/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/agents
Barton ID: 03.01.01
Unique ID: CTB-AE5F8B9E
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Barton Outreach Core – Outreach Campaign Runner
 * Enforces Barton Doctrine: unique_id, process_id, Firebase working memory, Neon vault, audit logging.
 * Launches campaigns in Instantly or HeyReach via Composio MCP with history layer checking
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { postToAuditLog } from "../../ops/orbt/auditLogger.js";
import { insertIntoNeon, queryFromNeon } from "../../ops/orbt/neonWriter.js";
import HistoryMCPClient from "../../apps/outreach-process-manager/api/lib/history-mcp-client.js";
import dotenv from 'dotenv';

dotenv.config();

const PROCESS_ID = "Launch Outreach Campaign";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';

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
 */
async function generateUniqueId(contactUniqueId, stepNumber = 1) {
  try {
    const query = `
      SELECT
        database_id,
        subhive_id,
        microprocess_id,
        tool_id,
        altitude
      FROM marketing.shq_process_key_reference
      WHERE process_name = 'Outreach Campaign Launcher'
      LIMIT 1
    `;

    const result = await queryFromNeon(query, [], {
      process_id: PROCESS_ID
    });

    if (result.rows && result.rows.length > 0) {
      const mapping = result.rows[0];
      const timestamp = Date.now();
      const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();

      return `${mapping.database_id || '04'}.${mapping.subhive_id || '02'}.${mapping.microprocess_id || '03'}.${mapping.tool_id || '08'}.${mapping.altitude || '15000'}.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
    }
  } catch (error) {
    console.warn('Could not query process key reference, using defaults:', error.message);
  }

  // Fallback to default values for outreach operations
  const timestamp = Date.now();
  const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();
  return `04.02.03.08.15000.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
}

/**
 * Generate Barton ID for outreach records
 */
function generateOutreachBartonId() {
  const timestamp = Date.now();
  const segment1 = String(timestamp % 100).padStart(2, '0');
  const segment2 = String((timestamp >> 8) % 100).padStart(2, '0');
  const segment3 = String(Math.floor(Math.random() * 100)).padStart(2, '0');
  const segment4 = '08'; // Outreach designation
  const segment5 = String(Math.floor(Math.random() * 100000)).padStart(5, '0');
  const segment6 = String(Math.floor(Math.random() * 1000)).padStart(3, '0');

  return `${segment1}.${segment2}.${segment3}.${segment4}.${segment5}.${segment6}`;
}

/**
 * Check History Layer to prevent duplicate outreach
 */
async function checkOutreachHistory(contactUniqueId, campaignId, platform) {
  const historyClient = new HistoryMCPClient();

  try {
    // Check if outreach already sent for this contact + campaign combination
    const recentCheck = await historyClient.checkFieldDiscovered(
      contactUniqueId,
      `outreach_${platform}_${campaignId}`,
      'person',
      168 // Check last 7 days (168 hours)
    );

    if (recentCheck.success && recentCheck.data.found) {
      console.log(`⚠️ Outreach already sent: Contact ${contactUniqueId}, Campaign ${campaignId}, Platform ${platform}`);

      // Get details of the previous outreach
      const latestValue = await historyClient.getLatestFieldValue(
        contactUniqueId,
        `outreach_${platform}_${campaignId}`,
        'person'
      );

      return {
        shouldSkip: true,
        reason: 'duplicate_outreach_prevented',
        previousOutreach: latestValue.data || {}
      };
    }

    return {
      shouldSkip: false,
      reason: 'no_recent_outreach'
    };

  } catch (error) {
    console.error('History check failed:', error);
    return {
      shouldSkip: false,
      reason: 'history_check_failed',
      error: error.message
    };
  }
}

/**
 * Record outreach attempt in History Layer
 */
async function recordOutreachHistory(contactUniqueId, campaignId, platform, status, uniqueId) {
  const historyClient = new HistoryMCPClient();

  try {
    await historyClient.addPersonHistoryEntry(
      contactUniqueId,
      `outreach_${platform}_${campaignId}`,
      status,
      'outreach-runner',
      {
        processId: PROCESS_ID,
        confidenceScore: status === 'launched' ? 1.0 : 0.0,
        changeReason: 'outreach_campaign',
        metadata: {
          campaign_id: campaignId,
          platform: platform,
          outreach_timestamp: new Date().toISOString(),
          unique_id: uniqueId
        }
      }
    );

    console.log(`✅ Recorded outreach history: ${contactUniqueId} -> ${campaignId} (${platform})`);
  } catch (error) {
    console.error('Failed to record outreach history:', error);
  }
}

/**
 * Launch campaign on Instantly through Composio MCP
 */
async function launchInstantlyCampaign(contactUniqueId, campaignId, uniqueId) {
  const mcpPayload = {
    tool: "instantly.launch_campaign",
    params: {
      campaign_id: campaignId,
      contact_id: contactUniqueId,
      variables: {
        contact_unique_id: contactUniqueId
      },
      schedule_immediately: true
    },
    metadata: {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      orbt_layer: 15000,
      platform: "instantly",
      timestamp: new Date().toISOString()
    }
  };

  console.log(`🚀 Launching Instantly campaign ${campaignId} for contact ${contactUniqueId}`);

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Instantly campaign launch failed: ${response.statusText} - ${errorText}`);
  }

  const result = await response.json();

  return {
    status: result.success ? 'launched' : 'failed',
    response: result.data ? JSON.stringify(result.data) : null,
    campaign_sequence_id: result.data?.sequence_id || null,
    platform_response: result
  };
}

/**
 * Launch campaign on HeyReach through Composio MCP
 */
async function launchHeyReachCampaign(contactUniqueId, campaignId, uniqueId) {
  const mcpPayload = {
    tool: "heyreach.launch_campaign",
    params: {
      campaign_id: campaignId,
      contact_id: contactUniqueId,
      personalization: {
        contact_unique_id: contactUniqueId
      },
      send_immediately: true
    },
    metadata: {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      orbt_layer: 15000,
      platform: "heyreach",
      timestamp: new Date().toISOString()
    }
  };

  console.log(`🚀 Launching HeyReach campaign ${campaignId} for contact ${contactUniqueId}`);

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(mcpPayload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HeyReach campaign launch failed: ${response.statusText} - ${errorText}`);
  }

  const result = await response.json();

  return {
    status: result.success ? 'launched' : 'failed',
    response: result.data ? JSON.stringify(result.data) : null,
    campaign_sequence_id: result.data?.sequence_id || null,
    platform_response: result
  };
}

/**
 * Normalize outreach results into standard schema
 */
function normalizeOutreachResult(contactUniqueId, campaignId, platform, launchResult, uniqueId) {
  const timestamp = new Date().toISOString();

  return {
    // Required schema fields
    contact_unique_id: contactUniqueId,
    campaign_id: campaignId,
    platform: platform,
    status: launchResult.status,
    response: launchResult.response,
    timestamp: timestamp,

    // Additional Barton Doctrine fields
    outreach_unique_id: generateOutreachBartonId(),
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    altitude: 15000,

    // Platform-specific fields
    campaign_sequence_id: launchResult.campaign_sequence_id,
    platform_response_code: launchResult.platform_response?.status || null,

    // Tracking timestamps
    launched_at: timestamp,
    created_at: timestamp,
    updated_at: timestamp
  };
}

/**
 * Write outreach result to Firebase (working memory)
 */
async function writeToFirebase(outreachResult) {
  const db = initFirebase();

  // Write to agent_whiteboard collection
  const whiteboardRef = db
    .collection('agent_whiteboard')
    .doc(outreachResult.outreach_unique_id);

  await whiteboardRef.set({
    ...outreachResult,
    firebase_write_timestamp: new Date().toISOString(),
    collection_type: "outreach_results"
  });

  // Also write to outreach_activity for quick lookups
  const activityRef = db
    .collection('outreach_activity')
    .doc(`${outreachResult.contact_unique_id}_${outreachResult.campaign_id}_${outreachResult.platform}`);

  await activityRef.set({
    contact_unique_id: outreachResult.contact_unique_id,
    campaign_id: outreachResult.campaign_id,
    platform: outreachResult.platform,
    status: outreachResult.status,
    outreach_unique_id: outreachResult.outreach_unique_id,
    launched_at: outreachResult.launched_at
  });

  console.log(`✅ Wrote outreach result to Firebase: ${outreachResult.outreach_unique_id}`);
}

/**
 * Main outreach runner function
 */
export async function runOutreach({ contact_unique_id, campaign_id, platform }) {
  if (!contact_unique_id || !campaign_id || !platform) {
    throw new Error('contact_unique_id, campaign_id, and platform are required');
  }

  if (!['instantly', 'heyreach'].includes(platform)) {
    throw new Error('platform must be "instantly" or "heyreach"');
  }

  const startTime = Date.now();
  const uniqueId = await generateUniqueId(contact_unique_id, 1);
  const runTimestamp = new Date().toISOString();

  console.log(`\n🎯 Starting outreach campaign`);
  console.log(`👤 Contact: ${contact_unique_id}`);
  console.log(`📧 Campaign: ${campaign_id}`);
  console.log(`🌐 Platform: ${platform}`);
  console.log(`🔑 Unique ID: ${uniqueId}`);

  // 1️⃣ Audit start
  await postToAuditLog({
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    contact_unique_id,
    status: "Pending",
    source: "outreach-runner",
    altitude: 15000,
    campaign_id,
    platform,
    started_at: runTimestamp,
    timestamp: runTimestamp
  });

  try {
    // 2️⃣ Check History Layer for duplicates
    const historyCheck = await checkOutreachHistory(contact_unique_id, campaign_id, platform);

    if (historyCheck.shouldSkip) {
      const duration = Date.now() - startTime;

      await postToAuditLog({
        unique_id: uniqueId,
        process_id: PROCESS_ID,
        contact_unique_id,
        status: "Skipped",
        source: "outreach-runner",
        altitude: 15000,
        campaign_id,
        platform,
        skip_reason: historyCheck.reason,
        duration_ms: duration,
        started_at: runTimestamp,
        completed_at: new Date().toISOString(),
        timestamp: new Date().toISOString()
      });

      console.log(`⏭️ Outreach skipped: ${historyCheck.reason}`);

      return {
        success: true,
        skipped: true,
        reason: historyCheck.reason,
        unique_id: uniqueId,
        contact_unique_id,
        campaign_id,
        platform,
        previousOutreach: historyCheck.previousOutreach
      };
    }

    // 3️⃣ Launch campaign on appropriate platform
    let launchResult;
    if (platform === 'instantly') {
      launchResult = await launchInstantlyCampaign(contact_unique_id, campaign_id, uniqueId);
    } else if (platform === 'heyreach') {
      launchResult = await launchHeyReachCampaign(contact_unique_id, campaign_id, uniqueId);
    }

    // 4️⃣ Normalize results to standard schema
    const outreachResult = normalizeOutreachResult(
      contact_unique_id,
      campaign_id,
      platform,
      launchResult,
      uniqueId
    );

    // 5️⃣ Write to Firebase (working memory)
    await writeToFirebase(outreachResult);

    // 6️⃣ Write to Neon vault (permanent storage)
    await insertIntoNeon("marketing.outreach_activity", [outreachResult], {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      on_conflict: "do_nothing"
    });

    // 7️⃣ Record in History Layer for future duplicate prevention
    await recordOutreachHistory(contact_unique_id, campaign_id, platform, launchResult.status, uniqueId);

    // 8️⃣ Audit success
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      contact_unique_id,
      status: launchResult.status === 'launched' ? "Success" : "Failed",
      source: "outreach-runner",
      altitude: 15000,
      campaign_id,
      platform,
      outreach_status: launchResult.status,
      campaign_sequence_id: launchResult.campaign_sequence_id,
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.log(`\n✅ Outreach ${launchResult.status === 'launched' ? 'launched successfully' : 'failed'}!`);
    console.log(`⏱️ Duration: ${duration}ms`);

    return {
      success: launchResult.status === 'launched',
      skipped: false,
      unique_id: uniqueId,
      contact_unique_id,
      campaign_id,
      platform,
      status: launchResult.status,
      outreach_result: outreachResult,
      duration_ms: duration
    };

  } catch (error) {
    // 9️⃣ Audit failure
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      contact_unique_id,
      status: "Failed",
      source: "outreach-runner",
      altitude: 15000,
      campaign_id,
      platform,
      error: error.message,
      error_stack: error.stack,
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.error(`\n❌ Outreach failed for ${contact_unique_id}:`, error.message);
    throw error;
  }
}

/**
 * CLI runner
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  let contactId, campaignId, platform;

  // Support both positional and named arguments
  if (args[0]?.startsWith('--contact=')) {
    const parseArg = (arg, name) => {
      const prefix = `--${name}=`;
      const found = args.find(a => a.startsWith(prefix));
      return found ? found.slice(prefix.length) : null;
    };

    contactId = parseArg(args, 'contact');
    campaignId = parseArg(args, 'campaign');
    platform = parseArg(args, 'platform');
  } else {
    [contactId, campaignId, platform] = args;
  }

  if (!contactId || !campaignId || !platform) {
    console.log('\n📖 Usage:');
    console.log('  npm run outreach:run -- --contact=<id> --campaign=<id> --platform=<instantly|heyreach>');
    console.log('  npm run outreach:run -- <contact_id> <campaign_id> <platform>');
    console.log('\n📋 Examples:');
    console.log('  npm run outreach:run -- --contact=07.23.45.07.12345.678 --campaign=CAM-001 --platform=instantly');
    console.log('  npm run outreach:run -- 07.23.45.07.12345.678 CAM-001 heyreach');
    process.exit(1);
  }

  if (!['instantly', 'heyreach'].includes(platform)) {
    console.error('\n❌ Platform must be "instantly" or "heyreach"');
    process.exit(1);
  }

  console.log('\n🏁 Starting Outreach Campaign Runner');
  console.log('─'.repeat(50));

  runOutreach({
    contact_unique_id: contactId,
    campaign_id: campaignId,
    platform: platform
  })
    .then(result => {
      if (result.skipped) {
        console.log('\n⏭️ Outreach skipped (duplicate prevention)');
      } else {
        console.log('\n🎉 Outreach campaign launched successfully!');
      }
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 Outreach failed:', error.message);
      process.exit(1);
    });
}

export default runOutreach;