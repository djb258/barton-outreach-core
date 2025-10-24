#!/usr/bin/env node
const { makeApiRequest } = require('./bootstrap_n8n.js');

async function checkStatus() {
  console.log('\n════════════════════════════════════════════════════════════════════════════════');
  console.log('📊 N8N WORKFLOW STATUS CHECK');
  console.log('════════════════════════════════════════════════════════════════════════════════\n');

  try {
    // Get workflows
    const workflows = await makeApiRequest('/api/v1/workflows');

    console.log('| Workflow                  | ID               | Active | Status |');
    console.log('|---------------------------|------------------|--------|--------|');

    workflows.data.forEach(w => {
      const name = w.name.padEnd(25);
      const id = w.id.slice(0, 16);
      const active = w.active ? '✅ Yes' : '❌ No';
      const status = w.active ? 'Ready' : 'Ready';
      console.log(`| ${name} | ${id} | ${active}  | ${status} |`);
    });

    console.log('\n════════════════════════════════════════════════════════════════════════════════');
    console.log(`Total Workflows: ${workflows.data.length}`);
    console.log(`Active: ${workflows.data.filter(w => w.active).length}`);
    console.log(`Inactive: ${workflows.data.filter(w => !w.active).length}`);
    console.log('════════════════════════════════════════════════════════════════════════════════\n');

    // Get credentials
    console.log('🔐 CREDENTIALS:\n');
    try {
      const creds = await makeApiRequest('/api/v1/credentials');
      if (creds.data && creds.data.length > 0) {
        creds.data.forEach(c => {
          console.log(`  ✅ ${c.name} (Type: ${c.type}, ID: ${c.id})`);
        });
      }
    } catch (e) {
      console.log('  ℹ️  Cannot list credentials via API (may require different permissions)');
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  checkStatus();
}

module.exports = { checkStatus };
