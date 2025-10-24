#!/usr/bin/env node
/**
 * List all available Composio tools
 */

import fetch from 'node-fetch';

const COMPOSIO_API_KEY = 'ak_j35MCGETpmFuX8iUpC0q';
const COMPOSIO_BASE_URL = 'https://backend.composio.dev/api/v3';
const CONNECTED_ACCOUNT_ID = 'ca_ePsJy2rp-R7Q';
const USER_ID = 'napi_xjl7fz34lkcw5j00o1iu8p07mvu4im2uynkk9kiigqp7g9c3aunc57fcc7nbdqu1';

async function listAllTools() {
  console.log('\n=== Composio Tools Catalog (with Connected Account) ===\n');
  console.log(`API Key: ${COMPOSIO_API_KEY.substring(0, 10)}...`);
  console.log(`Endpoint: ${COMPOSIO_BASE_URL}`);
  console.log(`Connected Account: ${CONNECTED_ACCOUNT_ID}`);
  console.log(`User ID: ${USER_ID}\n`);

  let allTools = [];
  let cursor = null;
  let page = 1;

  try {
    while (true) {
      const url = new URL(`${COMPOSIO_BASE_URL}/tools`);
      url.searchParams.set('pageSize', '100');
      url.searchParams.set('showAll', 'true');
      if (cursor) {
        url.searchParams.set('cursor', cursor);
      }

      console.log(`[Page ${page}] Fetching tools...`);

      const response = await fetch(url.toString(), {
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        console.error(`❌ HTTP ${response.status}`);
        const text = await response.text();
        console.error(text.substring(0, 500));
        break;
      }

      const data = await response.json();
      const tools = data.items || [];
      allTools.push(...tools);

      console.log(`   ✓ Got ${tools.length} tools (Total: ${allTools.length})`);

      cursor = data.next_cursor;
      if (!cursor || tools.length === 0) {
        break;
      }

      page++;
      if (page > 20) {
        console.log('   (Stopping at page 20 for safety)');
        break;
      }
    }

    console.log(`\n📊 Total tools found: ${allTools.length}\n`);

    // Search for neon-related tools
    const neonTools = allTools.filter(t =>
      t.slug.toLowerCase().includes('neon') ||
      t.name.toLowerCase().includes('neon') ||
      t.toolkit?.slug === 'neon'
    );

    console.log(`\n🔍 Neon-related tools (${neonTools.length}):\n`);
    neonTools.forEach(tool => {
      console.log(`   • ${tool.slug}`);
      console.log(`     Name: ${tool.name}`);
      console.log(`     Toolkit: ${tool.toolkit?.slug || 'N/A'}`);
      console.log('');
    });

    // Search for SQL-related tools
    const sqlTools = allTools.filter(t =>
      t.slug.toLowerCase().includes('sql') ||
      t.name.toLowerCase().includes('sql') ||
      t.description?.toLowerCase().includes('execute sql')
    );

    console.log(`\n🔍 SQL-related tools (${sqlTools.length}):\n`);
    sqlTools.forEach(tool => {
      console.log(`   • ${tool.slug}`);
      console.log(`     Name: ${tool.name}`);
      console.log(`     Toolkit: ${tool.toolkit?.slug || 'N/A'}`);
      console.log('');
    });

    // List all toolkit names
    const toolkits = [...new Set(allTools.map(t => t.toolkit?.slug).filter(Boolean))];
    console.log(`\n📦 Available toolkits (${toolkits.length}):\n`);
    toolkits.sort().forEach(tk => console.log(`   • ${tk}`));

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
  }
}

listAllTools();
