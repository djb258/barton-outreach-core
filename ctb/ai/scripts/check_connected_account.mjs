#!/usr/bin/env node
/**
 * Check Connected Account Details and Available Actions
 */

import fetch from 'node-fetch';

const COMPOSIO_API_KEY = 'ak_j35MCGETpmFuX8iUpC0q';
const COMPOSIO_BASE_URL = 'https://backend.composio.dev/api/v3';
const CONNECTED_ACCOUNT_ID = 'ca_ePsJy2rp-R7Q';

console.log('\n=== Composio Connected Account Check ===\n');
console.log(`API Key: ${COMPOSIO_API_KEY.substring(0, 10)}...`);
console.log(`Connected Account: ${CONNECTED_ACCOUNT_ID}\n`);

async function checkConnectedAccount() {
  try {
    // Get connected account details
    console.log('[1/3] Fetching connected account details...');
    const accountResponse = await fetch(
      `${COMPOSIO_BASE_URL}/connectedAccounts/${CONNECTED_ACCOUNT_ID}`,
      {
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!accountResponse.ok) {
      console.error(`❌ HTTP ${accountResponse.status}`);
      const text = await accountResponse.text();
      console.error(text.substring(0, 500));
    } else {
      const accountData = await accountResponse.json();
      console.log('✅ Connected Account Details:');
      console.log(`   App: ${accountData.appUniqueId || accountData.appName || 'N/A'}`);
      console.log(`   Status: ${accountData.status || 'N/A'}`);
      console.log(`   Created: ${accountData.createdAt || 'N/A'}`);
      console.log(`   Integration ID: ${accountData.integrationId || 'N/A'}`);
      console.log('');
    }

    // List available actions for this account
    console.log('[2/3] Fetching available actions for this account...');
    const actionsResponse = await fetch(
      `${COMPOSIO_BASE_URL}/actions?connectedAccountId=${CONNECTED_ACCOUNT_ID}`,
      {
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!actionsResponse.ok) {
      console.error(`❌ HTTP ${actionsResponse.status}`);
      const text = await actionsResponse.text();
      console.error(text.substring(0, 500));
    } else {
      const actionsData = await actionsResponse.json();
      const actions = actionsData.items || [];

      console.log(`✅ Found ${actions.length} actions`);

      // Filter for Neon or SQL related
      const neonActions = actions.filter(a =>
        a.name?.toLowerCase().includes('neon') ||
        a.name?.toLowerCase().includes('sql') ||
        a.appName?.toLowerCase().includes('neon')
      );

      if (neonActions.length > 0) {
        console.log(`\n🔍 Neon/SQL Actions (${neonActions.length}):\n`);
        neonActions.forEach(action => {
          console.log(`   • ${action.name}`);
          console.log(`     App: ${action.appName || 'N/A'}`);
          console.log(`     Description: ${action.description || 'N/A'}`);
          console.log('');
        });
      } else {
        console.log('\n⚠️  No Neon or SQL actions found for this account');
      }

      // Show first 10 actions for reference
      if (actions.length > 0) {
        console.log(`\n📋 First 10 actions:\n`);
        actions.slice(0, 10).forEach(action => {
          console.log(`   • ${action.name} (${action.appName || 'N/A'})`);
        });
      }
    }

    // Get integration details
    console.log('\n[3/3] Fetching integrations list...');
    const integrationsResponse = await fetch(
      `${COMPOSIO_BASE_URL}/integrations`,
      {
        headers: {
          'x-api-key': COMPOSIO_API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!integrationsResponse.ok) {
      console.error(`❌ HTTP ${integrationsResponse.status}`);
    } else {
      const integrationsData = await integrationsResponse.json();
      const integrations = integrationsData.items || [];

      const neonIntegrations = integrations.filter(i =>
        i.name?.toLowerCase().includes('neon') ||
        i.appName?.toLowerCase().includes('neon')
      );

      if (neonIntegrations.length > 0) {
        console.log(`✅ Neon Integrations (${neonIntegrations.length}):\n`);
        neonIntegrations.forEach(integration => {
          console.log(`   • ${integration.name || integration.appName}`);
          console.log(`     ID: ${integration.id}`);
          console.log(`     Status: ${integration.status || 'N/A'}`);
          console.log('');
        });
      } else {
        console.log('⚠️  No Neon integrations found');
      }
    }

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
  }
}

checkConnectedAccount();
