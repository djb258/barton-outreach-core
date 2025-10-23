/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/agents
Barton ID: 03.01.01
Unique ID: CTB-72AA7720
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

/**
 * Barton Outreach Core – Apify Scraper Runner
 * Enforces Barton Doctrine: unique_id, process_id, Firebase working memory, Neon vault, audit logging.
 * ALL external operations go through Composio MCP tools
 */

import { initializeApp, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import { postToAuditLog } from "../../ops/orbt/auditLogger.js";
import { insertIntoNeon, queryFromNeon } from "../../ops/orbt/neonWriter.js";
import { checkHistoryBeforeRun, recordHistoryEntry } from "../../ops/orbt/historyEnforcer.js";
import dotenv from 'dotenv';
import crypto from 'crypto';

dotenv.config();

const PROCESS_ID = "Scrape Contact Emails from Apify";
const APIFY_ACTOR_ID = process.env.APIFY_ACTOR_ID || "apify/email-phone-scraper";
const APIFY_API_KEY = process.env.APIFY_API_KEY;
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';

// Initialize Firebase Admin
let firebaseApp;
let db;

function initFirebase() {
  if (!firebaseApp) {
    firebaseApp = initializeApp({
      projectId: process.env.FIREBASE_PROJECT_ID || "barton-outreach-core",
      // Use service account for production
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
async function generateUniqueId(companyUniqueId, stepNumber = 1) {
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
      WHERE process_name = 'Apify Contact Scraper'
      LIMIT 1
    `;

    const result = await queryFromNeon(query, [], {
      process_id: PROCESS_ID
    });

    if (result.rows && result.rows.length > 0) {
      const mapping = result.rows[0];
      const timestamp = Date.now();
      const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();

      return `${mapping.database_id || '04'}.${mapping.subhive_id || '01'}.${mapping.microprocess_id || '02'}.${mapping.tool_id || '07'}.${mapping.altitude || '10000'}.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
    }
  } catch (error) {
    console.warn('Could not query process key reference, using defaults:', error.message);
  }

  // Fallback to default values if query fails
  const timestamp = Date.now();
  const randomSuffix = Math.random().toString(36).substr(2, 5).toUpperCase();
  return `04.01.02.07.10000.${stepNumber}.${timestamp % 1000}.${randomSuffix}`;
}

/**
 * Generate Barton ID for contact records
 */
function generateContactBartonId() {
  const timestamp = Date.now();
  const segment1 = String(timestamp % 100).padStart(2, '0');
  const segment2 = String((timestamp >> 8) % 100).padStart(2, '0');
  const segment3 = String(Math.floor(Math.random() * 100)).padStart(2, '0');
  const segment4 = '07'; // Database record designation
  const segment5 = String(Math.floor(Math.random() * 100000)).padStart(5, '0');
  const segment6 = String(Math.floor(Math.random() * 1000)).padStart(3, '0');

  return `${segment1}.${segment2}.${segment3}.${segment4}.${segment5}.${segment6}`;
}

/**
 * Call Apify actor through Composio MCP
 */
async function callApifyActor(companyId, domainUrl, uniqueId) {
  if (!APIFY_API_KEY) {
    throw new Error('APIFY_API_KEY not configured in environment');
  }

  const runPayload = {
    tool: "apify.run_actor",
    params: {
      actor_id: APIFY_ACTOR_ID,
      run_input: {
        startUrls: [{ url: domainUrl }],
        companyId: companyId,
        maxPagesToScrape: parseInt(process.env.APIFY_MAX_PAGES || '5'),
        extractEmails: true,
        extractPhones: true,
        extractLinkedIn: true,
        extractNames: true,
        extractJobTitles: true,
        proxyConfiguration: {
          useApifyProxy: true
        }
      },
      build: "latest",
      memory_mbytes: 512,
      timeout_secs: 300,
      wait_for_finish: true // Wait for the actor to complete
    },
    metadata: {
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      orbt_layer: 10000,
      blueprint_version: "1.0",
      timestamp: new Date().toISOString()
    }
  };

  console.log(`🎬 Starting Apify actor ${APIFY_ACTOR_ID} for company ${companyId}`);

  const response = await fetch('http://localhost:3001/tool', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY,
      'X-Apify-Api-Key': APIFY_API_KEY
    },
    body: JSON.stringify(runPayload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Apify actor run failed: ${response.statusText} - ${errorText}`);
  }

  const runResult = await response.json();

  // Get the dataset items from the run
  if (runResult.data?.defaultDatasetId) {
    const datasetPayload = {
      tool: "apify.get_dataset_items",
      params: {
        dataset_id: runResult.data.defaultDatasetId,
        limit: 1000,
        offset: 0,
        fields: ["email", "phone", "linkedin", "name", "firstName", "lastName", "jobTitle", "department", "sourceUrl"]
      },
      metadata: runPayload.metadata
    };

    const datasetResponse = await fetch('http://localhost:3001/tool', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Composio-Api-Key': COMPOSIO_API_KEY,
        'X-Apify-Api-Key': APIFY_API_KEY
      },
      body: JSON.stringify(datasetPayload)
    });

    if (datasetResponse.ok) {
      const datasetResult = await datasetResponse.json();
      return datasetResult.data?.items || datasetResult.data || [];
    }
  }

  return [];
}

/**
 * Normalize Apify results into standard contact schema
 */
function normalizeContacts(apifyResults, companyUniqueId, uniqueId) {
  const timestamp = new Date().toISOString();

  return apifyResults.map((rawContact, index) => {
    // Generate unique contact ID
    const contactUniqueId = generateContactBartonId();

    // Normalize the contact data
    return {
      // Required Barton Doctrine fields
      company_unique_id: companyUniqueId,
      contact_unique_id: contactUniqueId,

      // Contact information (matching required schema)
      email: rawContact.email || rawContact.contactEmail || null,
      phone: rawContact.phone || rawContact.contactPhone || null,
      linkedin: rawContact.linkedin || rawContact.linkedinUrl || null,

      // Additional fields for enrichment
      first_name: rawContact.firstName || null,
      last_name: rawContact.lastName || null,
      full_name: rawContact.name || rawContact.fullName || null,
      job_title: rawContact.jobTitle || rawContact.title || null,
      department: rawContact.department || null,

      // Required status and timestamp
      status: "scraped",
      timestamp: timestamp,

      // Barton Doctrine metadata
      unique_id: `${uniqueId}.contact.${index}`,
      process_id: PROCESS_ID,
      altitude: 10000,
      source: "apify",
      source_url: rawContact.sourceUrl || null,
      confidence_score: 0.7, // Default confidence for scraped data

      // Tracking timestamps
      scraped_at: timestamp,
      created_at: timestamp,
      updated_at: timestamp,
      validated: false
    };
  });
}

/**
 * Write contacts to Firebase (working memory)
 */
async function writeToFirebase(contacts, companyUniqueId) {
  const db = initFirebase();
  const batch = db.batch();

  for (const contact of contacts) {
    // Write to agent_whiteboard collection
    const whiteboardRef = db
      .collection('agent_whiteboard')
      .doc(contact.contact_unique_id);

    batch.set(whiteboardRef, {
      ...contact,
      firebase_write_timestamp: new Date().toISOString(),
      collection_type: "apify_scrape_results"
    });

    // Write relationship to company_contacts
    const relationshipRef = db
      .collection('company_contacts')
      .doc(`${companyUniqueId}_${contact.contact_unique_id}`);

    batch.set(relationshipRef, {
      company_unique_id: companyUniqueId,
      contact_unique_id: contact.contact_unique_id,
      relationship_type: "scraped_contact",
      created_at: contact.created_at
    });
  }

  await batch.commit();
  console.log(`✅ Wrote ${contacts.length} contacts to Firebase`);
}

/**
 * Main Apify scraper runner with full Barton Doctrine compliance
 */
export async function runApifyScrape({ company_unique_id, domain_url, blueprint_id, force = false }) {
  const startTime = Date.now();
  const uniqueId = await generateUniqueId(company_unique_id, 1);
  const runTimestamp = new Date().toISOString();

  console.log(`\n🚀 Starting Apify scrape for company: ${company_unique_id}`);
  console.log(`📍 Domain: ${domain_url}`);
  console.log(`🔑 Unique ID: ${uniqueId}`);

  // 0️⃣ Check History Layer to prevent duplicate scraping
  const historyCheck = await checkHistoryBeforeRun({
    entity_id: company_unique_id,
    field: 'apify_scrape',
    windowDays: 7,
    forceRun: force,
    strategy: 'firebase-first'
  });

  if (!historyCheck.shouldRun) {
    console.log(`⏭️ Skipping scrape - already scraped within last 7 days`);

    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id,
      status: "Skipped",
      source: "apify-runner",
      altitude: 10000,
      blueprint_id,
      domain_url,
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
      company_unique_id,
      domain_url
    };
  }

  // 1️⃣ Audit start
  await postToAuditLog({
    unique_id: uniqueId,
    process_id: PROCESS_ID,
    company_unique_id,
    status: "Pending",
    source: "apify-runner",
    altitude: 10000,
    blueprint_id,
    domain_url,
    started_at: runTimestamp,
    timestamp: runTimestamp
  });

  try {
    // 2️⃣ Call Apify actor through Composio
    const apifyResults = await callApifyActor(company_unique_id, domain_url, uniqueId);
    console.log(`📊 Apify returned ${apifyResults.length} raw results`);

    // 3️⃣ Normalize contacts to standard schema
    const contacts = normalizeContacts(apifyResults, company_unique_id, uniqueId);
    console.log(`✨ Normalized to ${contacts.length} contacts`);

    // 4️⃣ Write to Firebase (working memory)
    if (contacts.length > 0) {
      await writeToFirebase(contacts, company_unique_id);
    }

    // 5️⃣ Write to Neon vault (permanent storage)
    if (contacts.length > 0) {
      await insertIntoNeon("marketing.contact_verification", contacts, {
        unique_id: uniqueId,
        process_id: PROCESS_ID,
        on_conflict: "do_nothing" // Skip duplicates
      });
    }

    // 6️⃣ Calculate metrics
    const metrics = {
      total_contacts: contacts.length,
      with_email: contacts.filter(c => c.email).length,
      with_phone: contacts.filter(c => c.phone).length,
      with_linkedin: contacts.filter(c => c.linkedin).length,
      with_name: contacts.filter(c => c.full_name || (c.first_name && c.last_name)).length,
      with_title: contacts.filter(c => c.job_title).length
    };

    // 7️⃣ Record in History Layer
    await recordHistoryEntry({
      entity_id: company_unique_id,
      field: 'apify_scrape',
      value_found: `${metrics.total_contacts} contacts`,
      source: 'apify',
      process_id: PROCESS_ID,
      confidence_score: 0.8,
      metadata: {
        emails_found: metrics.with_email,
        phones_found: metrics.with_phone,
        linkedin_found: metrics.with_linkedin,
        domain_url: domain_url
      }
    });

    // 8️⃣ Audit success
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id,
      status: "Success",
      source: "apify-runner",
      altitude: 10000,
      blueprint_id,
      domain_url,
      records_scraped: metrics.total_contacts,
      emails_found: metrics.with_email,
      phones_found: metrics.with_phone,
      linkedin_found: metrics.with_linkedin,
      names_found: metrics.with_name,
      titles_found: metrics.with_title,
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.log(`\n✅ Apify scrape completed successfully!`);
    console.log(`📈 Metrics:`, metrics);
    console.log(`⏱️ Duration: ${duration}ms`);

    return {
      success: true,
      unique_id: uniqueId,
      company_unique_id,
      contacts,
      metrics,
      duration_ms: duration
    };

  } catch (error) {
    // 8️⃣ Audit failure
    const duration = Date.now() - startTime;
    await postToAuditLog({
      unique_id: uniqueId,
      process_id: PROCESS_ID,
      company_unique_id,
      status: "Failed",
      source: "apify-runner",
      altitude: 10000,
      blueprint_id,
      domain_url,
      error: error.message,
      error_stack: error.stack,
      duration_ms: duration,
      started_at: runTimestamp,
      completed_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    });

    console.error(`\n❌ Apify scrape failed for ${company_unique_id}:`, error.message);
    throw error;
  }
}

/**
 * CLI runner
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  // Parse command line arguments
  const args = process.argv.slice(2);
  let companyId, domainUrl, blueprintId;
  const forceRun = args.includes('--force');

  // Support both positional and named arguments
  if (args[0]?.startsWith('--company=')) {
    // Named arguments: --company=CMP-123 --domain=example.com --blueprint=BP-001
    const parseArg = (arg, name) => {
      const prefix = `--${name}=`;
      const found = args.find(a => a.startsWith(prefix));
      return found ? found.slice(prefix.length) : null;
    };

    companyId = parseArg(args, 'company');
    domainUrl = parseArg(args, 'domain');
    blueprintId = parseArg(args, 'blueprint') || 'BP-DEFAULT';
  } else {
    // Positional arguments: <company_id> <domain_url> [blueprint_id]
    const positionalArgs = args.filter(a => !a.startsWith('--'));
    [companyId, domainUrl, blueprintId = 'BP-DEFAULT'] = positionalArgs;
  }

  if (!companyId || !domainUrl) {
    console.log('\n📖 Usage:');
    console.log('  npm run scrape:apify -- --company=<id> --domain=<url> [--blueprint=<id>] [--force]');
    console.log('  npm run scrape:apify -- <company_id> <domain_url> [blueprint_id] [--force]');
    console.log('\n📋 Examples:');
    console.log('  npm run scrape:apify -- --company=CMP-12345 --domain=https://example.com');
    console.log('  npm run scrape:apify -- CMP-12345 https://example.com BP-001');
    console.log('  npm run scrape:apify -- --company=CMP-12345 --domain=https://example.com --force');
    console.log('\nOptions:');
    console.log('  --force    Force run (bypass history check)');
    process.exit(1);
  }

  // Ensure domain has protocol
  if (!domainUrl.startsWith('http://') && !domainUrl.startsWith('https://')) {
    domainUrl = `https://${domainUrl}`;
  }

  console.log('\n🏁 Starting Apify Scraper Runner');
  console.log('─'.repeat(50));
  if (forceRun) {
    console.log('🔓 Force run enabled - bypassing history check');
  }

  runApifyScrape({
    company_unique_id: companyId,
    domain_url: domainUrl,
    blueprint_id: blueprintId,
    force: forceRun
  })
    .then(result => {
      console.log('\n🎉 Scrape completed successfully!');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 Scrape failed:', error.message);
      process.exit(1);
    });
}

export default runApifyScrape;