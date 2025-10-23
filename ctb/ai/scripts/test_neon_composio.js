/*
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/scripts
Barton ID: 03.01.04
Unique ID: CTB-C0E4F47B
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: HEIR
─────────────────────────────────────────────
*/

import { Composio } from '@composio/core';

const composio = new Composio({
  apiKey: process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn',
});

async function testNeonTool() {
  try {
    console.log('Testing Neon tool availability through Composio SDK...\n');

    // First, list all available actions to see if neon exists
    const actions = await composio.actions.list();
    const neonActions = actions.items?.filter(action =>
      action.name.toLowerCase().includes('neon') ||
      action.appName?.toLowerCase() === 'neon'
    );

    console.log(`Total actions available: ${actions.items?.length || actions.length || 0}`);
    console.log(`Neon actions found: ${neonActions?.length || 0}\n`);

    if (neonActions && neonActions.length > 0) {
      console.log('Neon actions:', neonActions.map(a => a.name));
    } else {
      console.log('❌ No Neon actions found in Composio');
      console.log('\nChecking connected accounts...\n');

      const accounts = await composio.connectedAccounts.list();
      const neonAccounts = accounts.items?.filter(acc =>
        acc.appName?.toLowerCase() === 'neon'
      );

      console.log(`Neon connected accounts: ${neonAccounts?.length || 0}`);
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

testNeonTool();
