/**
 * Doctrine Spec:
 * - Barton ID: 12.01.01.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Enhanced Composio integration with full tool suite
 * - Input: Tool execution requests
 * - Output: Tool results and metadata
 * - MCP: Composio (Full Integration)
 */

import { Composio } from '@composio/core';

class ComposioEnhancedService {
  constructor() {
    this.composio = new Composio({
      apiKey: process.env.COMPOSIO_API_KEY || 'ak_t-F0AbvfZHUZSUrqAGNn',
    });
    this.toolCache = new Map();
    this.connectionCache = new Map();
  }

  /**
   * Initialize and verify all Composio connections
   */
  async initialize() {
    console.log('[COMPOSIO] Initializing enhanced service...');

    try {
      // Get all available tools
      const tools = await this.composio.actions.list();
      console.log(`[COMPOSIO] Found ${tools.length} available tools`);

      // Cache tools by category
      this.categorizeTools(tools);

      // Get connected accounts
      const accounts = await this.composio.connectedAccounts.list();
      console.log(`[COMPOSIO] Found ${accounts.length} connected accounts`);

      // Cache connections
      accounts.forEach(account => {
        this.connectionCache.set(account.appName, account.id);
      });

      return {
        success: true,
        toolCount: tools.length,
        connectionCount: accounts.length
      };
    } catch (error) {
      console.error('[COMPOSIO] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Categorize tools for easier access
   */
  categorizeTools(tools) {
    const categories = {
      database: [],
      email: [],
      calendar: [],
      storage: [],
      communication: [],
      analytics: [],
      ai: [],
      automation: []
    };

    tools.forEach(tool => {
      const name = tool.name.toLowerCase();

      if (name.includes('neon') || name.includes('postgres') || name.includes('sql')) {
        categories.database.push(tool);
      } else if (name.includes('gmail') || name.includes('sendgrid') || name.includes('email')) {
        categories.email.push(tool);
      } else if (name.includes('calendar') || name.includes('schedule')) {
        categories.calendar.push(tool);
      } else if (name.includes('drive') || name.includes('storage') || name.includes('s3')) {
        categories.storage.push(tool);
      } else if (name.includes('slack') || name.includes('discord') || name.includes('teams')) {
        categories.communication.push(tool);
      } else if (name.includes('analytics') || name.includes('mixpanel')) {
        categories.analytics.push(tool);
      } else if (name.includes('openai') || name.includes('anthropic') || name.includes('llm')) {
        categories.ai.push(tool);
      } else {
        categories.automation.push(tool);
      }
    });

    this.toolCache.set('categories', categories);
    return categories;
  }

  /**
   * Execute a Composio tool
   */
  async executeTool(toolName, params) {
    console.log(`[COMPOSIO] Executing tool: ${toolName}`);

    try {
      // Map tool name to app name
      const appName = this.getAppName(toolName);
      const connectedAccountId = this.connectionCache.get(appName);

      const result = await this.composio.actions.execute({
        actionName: toolName,
        appName: appName,
        params: params,
        connectedAccountId: connectedAccountId
      });

      return {
        success: true,
        data: result.data || result,
        tool: toolName,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error(`[COMPOSIO] Tool execution failed:`, error);
      return {
        success: false,
        error: error.message,
        tool: toolName,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get app name from tool name
   */
  getAppName(toolName) {
    const mappings = {
      'neon_execute_sql': 'neon',
      'gmail_send_email': 'gmail',
      'slack_send_message': 'slack',
      'google_drive_upload': 'googledrive',
      'github_create_issue': 'github',
      'mixpanel_track_event': 'mixpanel',
      'sendgrid_send_email': 'sendgrid'
    };

    return mappings[toolName] || toolName.split('_')[0];
  }

  /**
   * Database operations via Composio
   */
  async executeNeonSQL(sql, params = {}) {
    return await this.executeTool('neon_execute_sql', {
      sql,
      database_url: process.env.NEON_DATABASE_URL,
      ...params
    });
  }

  /**
   * Send email via Composio
   */
  async sendEmail(provider, emailData) {
    const toolName = provider === 'gmail' ? 'gmail_send_email' : 'sendgrid_send_email';

    return await this.executeTool(toolName, {
      to: emailData.to,
      subject: emailData.subject,
      body: emailData.body,
      from: emailData.from || process.env.DEFAULT_EMAIL_FROM
    });
  }

  /**
   * Send Slack message
   */
  async sendSlackMessage(channel, message) {
    return await this.executeTool('slack_send_message', {
      channel,
      text: message
    });
  }

  /**
   * Track analytics event
   */
  async trackEvent(eventName, properties) {
    return await this.executeTool('mixpanel_track_event', {
      event: eventName,
      properties: {
        ...properties,
        barton_id: this.generateBartonId(),
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Upload file to cloud storage
   */
  async uploadFile(fileName, fileContent, provider = 'googledrive') {
    const toolName = provider === 's3' ? 's3_upload_file' : 'google_drive_upload';

    return await this.executeTool(toolName, {
      fileName,
      fileContent,
      mimeType: 'application/octet-stream'
    });
  }

  /**
   * Create GitHub issue
   */
  async createGitHubIssue(repo, title, body, labels = []) {
    return await this.executeTool('github_create_issue', {
      repo,
      title,
      body,
      labels
    });
  }

  /**
   * Execute OpenAI completion
   */
  async getAICompletion(prompt, model = 'gpt-4') {
    return await this.executeTool('openai_create_completion', {
      prompt,
      model,
      max_tokens: 1000,
      temperature: 0.7
    });
  }

  /**
   * Schedule calendar event
   */
  async scheduleEvent(eventData) {
    return await this.executeTool('google_calendar_create_event', {
      summary: eventData.title,
      description: eventData.description,
      start: eventData.startTime,
      end: eventData.endTime,
      attendees: eventData.attendees || []
    });
  }

  /**
   * Generate Barton ID
   */
  generateBartonId() {
    const segment1 = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    const segment2 = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    const segment3 = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    const segment4 = '07'; // Fixed for Composio operations
    const segment5 = Math.floor(Math.random() * 100000).toString().padStart(5, '0');
    const segment6 = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

    return `${segment1}.${segment2}.${segment3}.${segment4}.${segment5}.${segment6}`;
  }

  /**
   * Get available tools by category
   */
  getToolsByCategory(category) {
    const categories = this.toolCache.get('categories');
    return categories ? categories[category] || [] : [];
  }

  /**
   * Health check for all connections
   */
  async healthCheck() {
    const results = {};

    for (const [appName, accountId] of this.connectionCache) {
      try {
        // Attempt a simple operation for each app
        const testResult = await this.composio.actions.execute({
          actionName: `${appName}_list`,
          appName: appName,
          params: { limit: 1 },
          connectedAccountId: accountId
        });

        results[appName] = {
          status: 'healthy',
          connected: true
        };
      } catch (error) {
        results[appName] = {
          status: 'unhealthy',
          connected: false,
          error: error.message
        };
      }
    }

    return results;
  }
}

export default ComposioEnhancedService;