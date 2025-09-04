let manifest = null;
let progress = null;
const SLUG = new URL(location.href).searchParams.get('slug') || 'barton-outreach';

// API endpoints
const OUTREACH_URL = new URLSearchParams(location.search).get('api') || '/api/outreach';
const LLM_URL = new URLSearchParams(location.search).get('llm') || '/api/llm';

// Outreach service instance
let outreachService = null;

// Current state
let selectedBucket = 'company';
let isProcessing = false;

// Initialize the application
window.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Barton Outreach Core UI initialized');
  
  // Initialize outreach service
  outreachService = {
    async loadManifest() {
      try {
        const response = await fetch(`${OUTREACH_URL}/manifest/${SLUG}`);
        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.error('Error loading manifest:', error);
      }
      return getDefaultManifest();
    },
    
    async saveManifest(manifest) {
      try {
        await fetch(`${OUTREACH_URL}/manifest/${SLUG}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(manifest)
        });
      } catch (error) {
        console.error('Error saving manifest:', error);
      }
    },
    
    async getStats() {
      try {
        const response = await fetch(`${OUTREACH_URL}/stats`);
        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.error('Error loading stats:', error);
      }
      return {
        total_companies: 0,
        verified_contacts: 0,
        active_campaigns: 0,
        queue_items: 0
      };
    },
    
    async getQueues() {
      try {
        const response = await fetch(`${OUTREACH_URL}/queues`);
        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.error('Error loading queues:', error);
      }
      return [];
    },
    
    async processQueue(queueType, limit = 10) {
      try {
        const response = await fetch(`${OUTREACH_URL}/queues/${queueType}/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ limit })
        });
        if (response.ok) {
          return await response.json();
        }
      } catch (error) {
        console.error(`Error processing ${queueType} queue:`, error);
      }
      return { processed: 0, errors: 0 };
    }
  };
  
  // Load initial data
  await loadManifest();
  await updateStats();
  await renderUI();
  
  // Set up auto-refresh
  setInterval(async () => {
    if (!isProcessing) {
      await updateStats();
      await updateQueueCounts();
    }
  }, 30000); // Refresh every 30 seconds
});

function getDefaultManifest() {
  return {
    meta: {
      app_name: 'Barton Outreach Core',
      stage: 'active',
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
    },
    doctrine: {
      schema_version: 'HEIR/1.0',
    },
    buckets: {
      company: {
        id: 'company',
        name: 'Company Management',
        stages: [
          { id: 'discovery', name: 'Company Discovery', status: 'todo', queue_count: 0, description: 'Discover and validate new companies' },
          { id: 'verification', name: 'Data Verification', status: 'todo', queue_count: 0, description: 'Verify company information and contact details' },
          { id: 'enrichment', name: 'Profile Enrichment', status: 'todo', queue_count: 0, description: 'Enrich company profiles with additional data' },
        ],
      },
      people: {
        id: 'people',
        name: 'Contact Management', 
        stages: [
          { id: 'scraping', name: 'Contact Scraping', status: 'todo', queue_count: 0, description: 'Scrape LinkedIn and website contacts' },
          { id: 'verification', name: 'Email Verification', status: 'todo', queue_count: 0, description: 'Verify email addresses with MillionVerifier' },
          { id: 'enrichment', name: 'Profile Enrichment', status: 'todo', queue_count: 0, description: 'Enrich contact profiles and update dot colors' },
        ],
      },
      campaigns: {
        id: 'campaigns',
        name: 'Campaign Management',
        stages: [
          { id: 'planning', name: 'Campaign Planning', status: 'todo', queue_count: 0, description: 'Plan and design outreach campaigns' },
          { id: 'execution', name: 'Campaign Execution', status: 'todo', queue_count: 0, description: 'Execute outreach campaigns and track responses' },
          { id: 'tracking', name: 'Performance Tracking', status: 'todo', queue_count: 0, description: 'Track campaign performance and optimize' },
        ],
      },
    },
    stats: {
      total_companies: 0,
      verified_contacts: 0,
      active_campaigns: 0,
      queue_items: 0,
    },
  };
}

async function loadManifest() {
  manifest = await outreachService.loadManifest();
  console.log('📋 Manifest loaded:', manifest.meta.app_name);
  return manifest;
}

async function saveManifest() {
  if (manifest) {
    manifest.meta.updated = new Date().toISOString();
    await outreachService.saveManifest(manifest);
    console.log('💾 Manifest saved');
  }
}

async function updateStats() {
  if (manifest) {
    manifest.stats = await outreachService.getStats();
  }
}

async function updateQueueCounts() {
  if (!manifest) return;
  
  const queues = await outreachService.getQueues();
  
  // Update queue counts for each stage
  Object.values(manifest.buckets).forEach(bucket => {
    if (bucket && bucket.stages) {
      bucket.stages.forEach(stage => {
        const queueType = `${bucket.id}_${stage.id}`;
        const queueData = queues.find(q => q.type === queueType);
        stage.queue_count = queueData ? queueData.count : 0;
      });
    }
  });
}

function calculateOverallProgress() {
  let totalDone = 0;
  let totalWip = 0;
  let totalStages = 0;

  Object.values(manifest.buckets).forEach(bucket => {
    if (bucket && bucket.stages) {
      bucket.stages.forEach(stage => {
        totalStages++;
        if (stage.status === 'done') totalDone++;
        if (stage.status === 'wip') totalWip++;
      });
    }
  });

  const percentage = totalStages > 0 ? ((totalDone + totalWip * 0.5) / totalStages) * 100 : 0;
  return { percentage: Math.round(percentage), done: totalDone, wip: totalWip, total: totalStages };
}

async function renderUI() {
  if (!manifest) return;
  
  const app = document.getElementById('app');
  if (!app) return;
  
  const overallProgress = calculateOverallProgress();
  
  app.innerHTML = `
    <div class="outreach-container">
      <!-- Header -->
      <header class="outreach-header">
        <div class="header-content">
          <h1>${manifest.meta.app_name}</h1>
          <div class="header-stats">
            <div class="stat-item">
              <span class="stat-value">${manifest.stats.total_companies}</span>
              <span class="stat-label">Companies</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">${manifest.stats.verified_contacts}</span>
              <span class="stat-label">Contacts</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">${manifest.stats.active_campaigns}</span>
              <span class="stat-label">Campaigns</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">${manifest.stats.queue_items}</span>
              <span class="stat-label">Queue Items</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Progress Overview -->
      <div class="progress-overview">
        <h2>Overall Progress</h2>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${overallProgress.percentage}%"></div>
        </div>
        <div class="progress-stats">
          <span>${overallProgress.done} done</span>
          <span>${overallProgress.wip} in progress</span>
          <span>${overallProgress.total - overallProgress.done - overallProgress.wip} todo</span>
        </div>
      </div>

      <!-- Bucket Navigation -->
      <nav class="bucket-nav">
        ${Object.entries(manifest.buckets).map(([key, bucket]) => `
          <button class="bucket-tab ${selectedBucket === key ? 'active' : ''}" 
                  onclick="selectBucket('${key}')">
            ${bucket.name}
          </button>
        `).join('')}
      </nav>

      <!-- Bucket Content -->
      <div class="bucket-content">
        ${renderBucket(manifest.buckets[selectedBucket])}
      </div>

      <!-- Actions -->
      <div class="actions">
        <button onclick="processAllQueues()" class="btn-primary" ${isProcessing ? 'disabled' : ''}>
          ${isProcessing ? 'Processing...' : 'Process All Queues'}
        </button>
        <button onclick="refreshData()" class="btn-secondary">
          Refresh Data
        </button>
        <button onclick="saveManifest()" class="btn-secondary">
          Save Progress
        </button>
      </div>
    </div>
  `;
}

function renderBucket(bucket) {
  if (!bucket) return '<div class="empty-bucket">No bucket selected</div>';
  
  return `
    <div class="bucket">
      <h3>${bucket.name}</h3>
      <div class="stages">
        ${bucket.stages.map(stage => `
          <div class="stage ${stage.status}">
            <div class="stage-header">
              <h4>${stage.name}</h4>
              <div class="stage-controls">
                ${stage.queue_count > 0 ? `<span class="queue-count">${stage.queue_count} queued</span>` : ''}
                <button onclick="processStageQueue('${bucket.id}', '${stage.id}')" 
                        class="btn-small" ${stage.queue_count === 0 ? 'disabled' : ''}>
                  Process
                </button>
                <select onchange="updateStageStatus('${bucket.id}', '${stage.id}', this.value)">
                  <option value="todo" ${stage.status === 'todo' ? 'selected' : ''}>Todo</option>
                  <option value="wip" ${stage.status === 'wip' ? 'selected' : ''}>In Progress</option>
                  <option value="done" ${stage.status === 'done' ? 'selected' : ''}>Done</option>
                </select>
              </div>
            </div>
            <p class="stage-description">${stage.description || ''}</p>
            ${stage.status === 'wip' ? `<div class="stage-progress">Processing...</div>` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// Event handlers
function selectBucket(bucketId) {
  selectedBucket = bucketId;
  renderUI();
}

async function updateStageStatus(bucketId, stageId, status) {
  if (!manifest || !manifest.buckets[bucketId]) return;
  
  const stage = manifest.buckets[bucketId].stages.find(s => s.id === stageId);
  if (stage) {
    stage.status = status;
    await saveManifest();
    await renderUI();
  }
}

async function processStageQueue(bucketId, stageId) {
  const queueType = `${bucketId}_${stageId}`;
  console.log(`🔄 Processing ${queueType} queue`);
  
  isProcessing = true;
  await renderUI();
  
  try {
    const result = await outreachService.processQueue(queueType, 10);
    console.log(`✅ Processed ${result.processed} items from ${queueType} queue`);
    
    if (result.errors > 0) {
      console.warn(`⚠️ ${result.errors} errors occurred`);
    }
    
    await updateQueueCounts();
  } catch (error) {
    console.error(`❌ Error processing ${queueType} queue:`, error);
  } finally {
    isProcessing = false;
    await renderUI();
  }
}

async function processAllQueues() {
  console.log('🔄 Processing all queues');
  
  isProcessing = true;
  await renderUI();
  
  try {
    // Process company queues
    await outreachService.processQueue('company_discovery', 5);
    await outreachService.processQueue('company_verification', 5);
    
    // Process people queues  
    await outreachService.processQueue('people_scraping', 10);
    await outreachService.processQueue('people_verification', 20);
    
    // Process campaign queues
    await outreachService.processQueue('campaigns_execution', 5);
    
    console.log('✅ All queues processed');
    await updateQueueCounts();
  } catch (error) {
    console.error('❌ Error processing queues:', error);
  } finally {
    isProcessing = false;
    await renderUI();
  }
}

async function refreshData() {
  console.log('🔄 Refreshing data');
  await updateStats();
  await updateQueueCounts();
  await renderUI();
  console.log('✅ Data refreshed');
}

// CSS Styles
const styles = `
  <style>
    .outreach-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .outreach-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 30px;
    }
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 20px;
    }
    
    .outreach-header h1 {
      margin: 0;
      font-size: 2.5em;
      font-weight: 700;
    }
    
    .header-stats {
      display: flex;
      gap: 30px;
      flex-wrap: wrap;
    }
    
    .stat-item {
      text-align: center;
    }
    
    .stat-value {
      display: block;
      font-size: 2em;
      font-weight: 700;
      line-height: 1;
    }
    
    .stat-label {
      font-size: 0.9em;
      opacity: 0.9;
    }
    
    .progress-overview {
      background: white;
      padding: 25px;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      margin-bottom: 30px;
    }
    
    .progress-overview h2 {
      margin: 0 0 15px 0;
      color: #333;
    }
    
    .progress-bar {
      width: 100%;
      height: 20px;
      background: #e0e0e0;
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 10px;
    }
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #4CAF50, #45a049);
      transition: width 0.3s ease;
    }
    
    .progress-stats {
      display: flex;
      justify-content: space-between;
      font-size: 0.9em;
      color: #666;
    }
    
    .bucket-nav {
      display: flex;
      gap: 0;
      margin-bottom: 30px;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .bucket-tab {
      flex: 1;
      padding: 20px;
      border: none;
      background: white;
      color: #666;
      font-size: 1.1em;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
      border-right: 1px solid #e0e0e0;
    }
    
    .bucket-tab:last-child {
      border-right: none;
    }
    
    .bucket-tab:hover {
      background: #f5f5f5;
    }
    
    .bucket-tab.active {
      background: #667eea;
      color: white;
    }
    
    .bucket-content {
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      margin-bottom: 30px;
    }
    
    .bucket {
      padding: 30px;
    }
    
    .bucket h3 {
      margin: 0 0 25px 0;
      color: #333;
      font-size: 1.8em;
    }
    
    .stages {
      display: grid;
      gap: 20px;
    }
    
    .stage {
      border: 2px solid #e0e0e0;
      border-radius: 8px;
      padding: 20px;
      transition: all 0.3s ease;
    }
    
    .stage.todo {
      border-color: #ddd;
      background: #fafafa;
    }
    
    .stage.wip {
      border-color: #ff9800;
      background: #fff3e0;
    }
    
    .stage.done {
      border-color: #4caf50;
      background: #e8f5e8;
    }
    
    .stage-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      flex-wrap: wrap;
      gap: 10px;
    }
    
    .stage-header h4 {
      margin: 0;
      color: #333;
      font-size: 1.3em;
    }
    
    .stage-controls {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .queue-count {
      background: #667eea;
      color: white;
      padding: 4px 8px;
      border-radius: 20px;
      font-size: 0.8em;
      font-weight: 500;
    }
    
    .stage-description {
      margin: 0;
      color: #666;
      font-size: 0.95em;
    }
    
    .stage-progress {
      margin-top: 15px;
      padding: 10px;
      background: #fff;
      border-radius: 4px;
      border: 1px solid #ddd;
      color: #666;
      font-style: italic;
    }
    
    .actions {
      display: flex;
      gap: 15px;
      justify-content: center;
      flex-wrap: wrap;
    }
    
    .btn-primary, .btn-secondary, .btn-small {
      padding: 12px 24px;
      border: none;
      border-radius: 8px;
      font-size: 1em;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-block;
      text-align: center;
    }
    
    .btn-primary {
      background: #667eea;
      color: white;
    }
    
    .btn-primary:hover:not(:disabled) {
      background: #5a6fd8;
      transform: translateY(-2px);
    }
    
    .btn-secondary {
      background: #f5f5f5;
      color: #333;
      border: 1px solid #ddd;
    }
    
    .btn-secondary:hover {
      background: #ebebeb;
    }
    
    .btn-small {
      padding: 6px 12px;
      font-size: 0.85em;
      background: #4caf50;
      color: white;
    }
    
    .btn-small:hover:not(:disabled) {
      background: #45a049;
    }
    
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    select {
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 0.9em;
    }
    
    .empty-bucket {
      padding: 40px;
      text-align: center;
      color: #666;
      font-style: italic;
    }
    
    @media (max-width: 768px) {
      .outreach-container {
        padding: 15px;
      }
      
      .header-content {
        flex-direction: column;
        text-align: center;
      }
      
      .bucket-nav {
        flex-direction: column;
      }
      
      .bucket-tab {
        border-right: none;
        border-bottom: 1px solid #e0e0e0;
      }
      
      .bucket-tab:last-child {
        border-bottom: none;
      }
      
      .stage-header {
        flex-direction: column;
        align-items: flex-start;
      }
      
      .actions {
        flex-direction: column;
      }
    }
  </style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', styles);

console.log('🎨 Barton Outreach Core UI ready');