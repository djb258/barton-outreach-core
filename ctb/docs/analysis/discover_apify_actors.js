/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs/analysis
Barton ID: 06.01.01
Unique ID: CTB-8FCD3F43
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
*/

/**
 * Apify Actor Discovery Script
 * Connects to Composio MCP to discover all Apify actors and their schemas
 */

import fetch from 'node-fetch';
import fs from 'fs/promises';
import path from 'path';

const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn';
const APIFY_API_KEY = process.env.APIFY_API_KEY;

// Barton Doctrine metadata
const UNIQUE_ID = '04.01.99.11.05000.001';
const PROCESS_ID = 'Apify Actor Discovery and Schema Analysis';

/**
 * Call Composio MCP tool
 */
async function callComposioTool(tool, params, metadata = {}) {
  const payload = {
    tool,
    data: params,
    unique_id: UNIQUE_ID,
    process_id: PROCESS_ID,
    orbt_layer: 5,
    blueprint_version: '1.0',
    ...metadata
  };

  console.log(`📡 Calling Composio tool: ${tool}`);

  const response = await fetch(`${COMPOSIO_MCP_URL}/tool`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Composio-Api-Key': COMPOSIO_API_KEY
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Composio MCP call failed: ${response.statusText} - ${errorText}`);
  }

  return await response.json();
}

/**
 * Fetch actor details directly from Apify API
 */
async function fetchActorDetails(actorId) {
  if (!APIFY_API_KEY) {
    throw new Error('APIFY_API_KEY not configured');
  }

  const url = `https://api.apify.com/v2/acts/${actorId}?token=${APIFY_API_KEY}`;

  console.log(`  📥 Fetching details for: ${actorId}`);

  const response = await fetch(url);

  if (!response.ok) {
    console.warn(`  ⚠️  Failed to fetch ${actorId}: ${response.statusText}`);
    return null;
  }

  return await response.json();
}

/**
 * Analyze actor input schema for executive enrichment relevance
 */
function analyzeActorForExecutives(actor) {
  const schema = actor.data || actor;
  const inputSchema = schema.input_schema || schema.inputSchema || {};
  const defaultInput = schema.default_input || schema.defaultInput || {};

  const executiveKeywords = [
    'ceo', 'cfo', 'hr', 'executive', 'officer', 'director', 'manager',
    'leadership', 'title', 'role', 'position', 'linkedin', 'contact',
    'email', 'name', 'company', 'organization'
  ];

  let score = 0;
  let relevantFields = [];

  // Analyze input schema properties
  const properties = inputSchema.properties || {};
  Object.keys(properties).forEach(field => {
    const fieldLower = field.toLowerCase();
    const fieldData = properties[field];
    const description = (fieldData.description || '').toLowerCase();

    executiveKeywords.forEach(keyword => {
      if (fieldLower.includes(keyword) || description.includes(keyword)) {
        score += 10;
        relevantFields.push({
          field,
          type: fieldData.type,
          description: fieldData.description || '',
          keyword
        });
      }
    });
  });

  // Check title and description
  const title = (schema.title || '').toLowerCase();
  const description = (schema.description || '').toLowerCase();

  executiveKeywords.forEach(keyword => {
    if (title.includes(keyword)) score += 5;
    if (description.includes(keyword)) score += 3;
  });

  return {
    relevanceScore: score,
    relevantFields,
    isPeopleEnrichment: title.includes('people') || title.includes('contact') || title.includes('profile'),
    isCompanyEnrichment: title.includes('company') || title.includes('organization') || title.includes('business'),
    isLinkedInSpecific: title.includes('linkedin') || description.includes('linkedin')
  };
}

/**
 * Main discovery function
 */
async function discoverApifyActors() {
  console.log('\n🚀 Starting Apify Actor Discovery');
  console.log('═'.repeat(70));
  console.log(`📍 Composio MCP: ${COMPOSIO_MCP_URL}`);
  console.log(`🔑 Process ID: ${PROCESS_ID}`);
  console.log(`🆔 Unique ID: ${UNIQUE_ID}`);
  console.log('═'.repeat(70));

  const results = {
    timestamp: new Date().toISOString(),
    unique_id: UNIQUE_ID,
    process_id: PROCESS_ID,
    discoveredActors: [],
    currentlyUsedActors: [
      {
        actorId: 'apify/email-phone-scraper',
        usage: 'Primary contact scraper in apifyRunner.js',
        location: 'agents/specialists/apifyRunner.js:18'
      },
      {
        actorId: 'apify~linkedin-profile-scraper',
        usage: 'LinkedIn profile scraping',
        location: 'packages/mcp-clients/src/clients/apify-mcp-client.ts:57'
      },
      {
        actorId: 'apify~website-content-crawler',
        usage: 'Website contact extraction',
        location: 'packages/mcp-clients/src/clients/apify-mcp-client.ts:118'
      }
    ],
    mockActors: [
      'linkedin-company-scraper',
      'website-content-crawler',
      'company-data-scraper',
      'business-permit-scraper',
      'financial-data-scraper'
    ],
    errors: []
  };

  try {
    // Step 1: Try to list actors via Composio MCP
    console.log('\n📋 Step 1: Listing Apify actors via Composio MCP...\n');

    try {
      const actorListResult = await callComposioTool('apify.list_actors', {
        my: true,
        limit: 100
      });

      if (actorListResult.success && actorListResult.data) {
        console.log(`✅ Found ${actorListResult.data.items?.length || 0} actors via MCP`);
        if (actorListResult.data.items) {
          results.discoveredActors.push(...actorListResult.data.items);
        }
      }
    } catch (mcpError) {
      console.warn('⚠️  MCP list_actors not available, falling back to direct API');
      results.errors.push({
        step: 'list_actors_mcp',
        error: mcpError.message
      });
    }

    // Step 2: Fetch details for known actors
    console.log('\n📋 Step 2: Fetching details for known actors...\n');

    const knownActorIds = [
      'apify/email-phone-scraper',
      'apify/linkedin-profile-scraper',
      'apify/website-content-crawler',
      'apify/linkedin-company-scraper',
      'apify/google-search-scraper',
      'apify/contact-finder',
      'apify/people-data-scraper',
      'compass/apollo-scraper',
      'compass/linkedin-people-scraper'
    ];

    for (const actorId of knownActorIds) {
      try {
        const actorDetails = await fetchActorDetails(actorId);

        if (actorDetails) {
          // Analyze for executive enrichment
          const analysis = analyzeActorForExecutives(actorDetails);

          results.discoveredActors.push({
            actorId,
            title: actorDetails.data?.title || actorId,
            description: actorDetails.data?.description || '',
            username: actorDetails.data?.username || actorId.split('/')[0],
            isPublic: actorDetails.data?.isPublic !== false,
            stats: actorDetails.data?.stats || {},
            inputSchema: actorDetails.data?.inputSchema || {},
            outputSchema: actorDetails.data?.outputSchema || {},
            readme: actorDetails.data?.readme?.substr(0, 500) || '',
            analysis
          });

          console.log(`  ✅ ${actorId}`);
          console.log(`     📊 Relevance Score: ${analysis.relevanceScore}`);
          console.log(`     👥 People Enrichment: ${analysis.isPeopleEnrichment ? 'Yes' : 'No'}`);
          console.log(`     🏢 Company Enrichment: ${analysis.isCompanyEnrichment ? 'Yes' : 'No'}`);
          if (analysis.relevantFields.length > 0) {
            console.log(`     🎯 Key Fields: ${analysis.relevantFields.slice(0, 3).map(f => f.field).join(', ')}`);
          }
          console.log('');
        }
      } catch (error) {
        results.errors.push({
          actorId,
          step: 'fetch_details',
          error: error.message
        });
      }
    }

    // Step 3: Rank actors for executive enrichment
    console.log('\n🏆 Step 3: Ranking actors for executive enrichment...\n');

    const rankedActors = results.discoveredActors
      .filter(actor => actor.analysis && actor.analysis.relevanceScore > 0)
      .sort((a, b) => b.analysis.relevanceScore - a.analysis.relevanceScore)
      .slice(0, 10);

    results.topExecutiveEnrichmentActors = rankedActors.map((actor, index) => ({
      rank: index + 1,
      actorId: actor.actorId,
      title: actor.title,
      relevanceScore: actor.analysis.relevanceScore,
      isPeopleEnrichment: actor.analysis.isPeopleEnrichment,
      isLinkedInSpecific: actor.analysis.isLinkedInSpecific,
      keyFields: actor.analysis.relevantFields.slice(0, 5)
    }));

    // Step 4: Save results
    console.log('\n💾 Step 4: Saving discovery results...\n');

    const outputPath = path.join(process.cwd(), 'analysis', 'apify_discovery_raw.json');
    await fs.writeFile(outputPath, JSON.stringify(results, null, 2));
    console.log(`✅ Saved raw results to: ${outputPath}`);

    // Display summary
    console.log('\n📊 DISCOVERY SUMMARY');
    console.log('═'.repeat(70));
    console.log(`Total Actors Discovered: ${results.discoveredActors.length}`);
    console.log(`Currently Used in Codebase: ${results.currentlyUsedActors.length}`);
    console.log(`Errors Encountered: ${results.errors.length}`);
    console.log(`\nTop 3 Actors for Executive Enrichment:`);

    results.topExecutiveEnrichmentActors.slice(0, 3).forEach((actor, i) => {
      console.log(`\n${i + 1}. ${actor.actorId}`);
      console.log(`   📊 Score: ${actor.relevanceScore}`);
      console.log(`   👥 People-focused: ${actor.isPeopleEnrichment ? 'Yes' : 'No'}`);
      console.log(`   🔗 LinkedIn: ${actor.isLinkedInSpecific ? 'Yes' : 'No'}`);
      console.log(`   🎯 Key Fields: ${actor.keyFields.map(f => f.field).join(', ')}`);
    });

    console.log('\n═'.repeat(70));

    return results;

  } catch (error) {
    console.error('\n❌ Discovery failed:', error.message);
    console.error(error.stack);
    throw error;
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  discoverApifyActors()
    .then(() => {
      console.log('\n✅ Discovery completed successfully!');
      process.exit(0);
    })
    .catch(error => {
      console.error('\n💥 Discovery failed:', error.message);
      process.exit(1);
    });
}

export default discoverApifyActors;
