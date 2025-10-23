/**
 * Doctrine Spec:
 * - Barton ID: 14.01.01.07.10000.001
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Unified orchestrator for all MCP services
 * - Input: Orchestration requests and workflows
 * - Output: Coordinated service results
 * - MCP: Multi-service orchestration (Composio, Firebase, Neon)
 */

import ComposioNeonBridge from '../lib/composio-neon-bridge.js';
import ComposioEnhancedService from '../services/composio-enhanced.js';
import FirebaseMCPService from '../services/firebase-mcp-service.js';

class OutreachOrchestrator {
  constructor() {
    this.neonBridge = new ComposioNeonBridge();
    this.composioService = new ComposioEnhancedService();
    this.firebaseService = new FirebaseMCPService();
    this.initialized = false;
    this.workflows = new Map();
  }

  /**
   * Initialize all services
   */
  async initialize() {
    console.log('[ORCHESTRATOR] Initializing all services...');

    try {
      // Initialize services in parallel
      const [neonResult, composioResult, firebaseResult] = await Promise.all([
        this.neonBridge.initialize(),
        this.composioService.initialize(),
        this.firebaseService.initialize()
      ]);

      this.initialized = true;

      console.log('[ORCHESTRATOR] All services initialized successfully');
      return {
        success: true,
        services: {
          neon: 'ready',
          composio: `${composioResult.toolCount} tools available`,
          firebase: 'connected'
        }
      };
    } catch (error) {
      console.error('[ORCHESTRATOR] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Execute a complete outreach workflow
   */
  async executeOutreachWorkflow(workflowData) {
    const workflowId = this.generateWorkflowId();
    console.log(`[ORCHESTRATOR] Starting workflow: ${workflowId}`);

    const workflow = {
      id: workflowId,
      status: 'running',
      steps: [],
      startTime: new Date().toISOString()
    };

    this.workflows.set(workflowId, workflow);

    try {
      // Step 1: Ingest contacts into Neon
      const ingestResult = await this.ingestContacts(workflowData.contacts);
      workflow.steps.push({
        name: 'Contact Ingestion',
        result: ingestResult,
        timestamp: new Date().toISOString()
      });

      // Step 2: Calculate lead scores
      const scoringResult = await this.calculateLeadScores(ingestResult.data.contactIds);
      workflow.steps.push({
        name: 'Lead Scoring',
        result: scoringResult,
        timestamp: new Date().toISOString()
      });

      // Step 3: Create campaign in Firebase
      const campaignResult = await this.createCampaign(workflowData.campaign);
      workflow.steps.push({
        name: 'Campaign Creation',
        result: campaignResult,
        timestamp: new Date().toISOString()
      });

      // Step 4: Send emails via Composio
      const emailResult = await this.sendCampaignEmails(
        scoringResult.data.qualifiedLeads,
        campaignResult.data.campaignId
      );
      workflow.steps.push({
        name: 'Email Sending',
        result: emailResult,
        timestamp: new Date().toISOString()
      });

      // Step 5: Track events in Firebase
      const trackingResult = await this.trackCampaignEvents(
        campaignResult.data.campaignId,
        emailResult.data.sentEmails
      );
      workflow.steps.push({
        name: 'Event Tracking',
        result: trackingResult,
        timestamp: new Date().toISOString()
      });

      // Step 6: Send notifications
      const notificationResult = await this.sendNotifications(workflowId, 'completed');
      workflow.steps.push({
        name: 'Notifications',
        result: notificationResult,
        timestamp: new Date().toISOString()
      });

      workflow.status = 'completed';
      workflow.endTime = new Date().toISOString();

      return {
        success: true,
        workflowId,
        steps: workflow.steps.length,
        summary: this.generateWorkflowSummary(workflow)
      };

    } catch (error) {
      workflow.status = 'failed';
      workflow.error = error.message;
      workflow.endTime = new Date().toISOString();

      console.error(`[ORCHESTRATOR] Workflow ${workflowId} failed:`, error);

      // Send failure notification
      await this.sendNotifications(workflowId, 'failed', error.message);

      throw error;
    }
  }

  /**
   * Ingest contacts using Neon bridge
   */
  async ingestContacts(contacts) {
    console.log(`[ORCHESTRATOR] Ingesting ${contacts.length} contacts...`);

    const rows = contacts.map(contact => ({
      email: contact.email,
      name: contact.name,
      company: contact.company,
      phone: contact.phone,
      tags: contact.tags || [],
      custom_fields: contact.custom_fields || {}
    }));

    const result = await this.neonBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `SELECT * FROM intake.f_ingest_json($1::jsonb[], $2, $3)`,
      params: [JSON.stringify(rows), 'orchestrator', `batch-${Date.now()}`]
    });

    if (result.success) {
      // Extract contact IDs from result
      const contactIds = result.data.rows?.map(r => r.load_id) || [];

      return {
        success: true,
        data: {
          contactIds,
          count: contacts.length
        }
      };
    }

    return result;
  }

  /**
   * Calculate lead scores
   */
  async calculateLeadScores(contactIds) {
    console.log(`[ORCHESTRATOR] Calculating scores for ${contactIds.length} contacts...`);

    const scores = [];
    const qualifiedLeads = [];

    for (const contactId of contactIds) {
      // Get contact data
      const contactData = await this.neonBridge.queryRows('vault.contacts', {
        load_id: contactId
      });

      if (contactData.success && contactData.data.rows.length > 0) {
        const contact = contactData.data.rows[0];

        // Calculate score based on multiple factors
        let score = 0;
        const factors = [];

        // Company factor
        if (contact.company) {
          score += 20;
          factors.push('Has company: +20');
        }

        // Email domain factor
        if (contact.email && !contact.email.includes('gmail.com')) {
          score += 15;
          factors.push('Business email: +15');
        }

        // Phone factor
        if (contact.phone) {
          score += 10;
          factors.push('Has phone: +10');
        }

        // Tags factor
        if (contact.tags && contact.tags.length > 0) {
          score += 5 * contact.tags.length;
          factors.push(`${contact.tags.length} tags: +${5 * contact.tags.length}`);
        }

        // Custom fields factor
        if (contact.custom_fields && Object.keys(contact.custom_fields).length > 0) {
          score += 10;
          factors.push('Has custom data: +10');
        }

        // Store score in Firebase
        await this.firebaseService.updateLeadScore(contact.email, {
          score,
          factors,
          triggers: score >= 50 ? ['qualified', 'ready_for_outreach'] : []
        });

        scores.push({ contactId, email: contact.email, score, factors });

        if (score >= 50) {
          qualifiedLeads.push(contact);
        }
      }
    }

    return {
      success: true,
      data: {
        scores,
        qualifiedLeads,
        averageScore: scores.reduce((sum, s) => sum + s.score, 0) / scores.length
      }
    };
  }

  /**
   * Create campaign in Firebase
   */
  async createCampaign(campaignData) {
    console.log('[ORCHESTRATOR] Creating campaign...');

    const campaign = {
      name: campaignData.name,
      subject: campaignData.subject,
      template: campaignData.template,
      status: 'active',
      created_by: 'orchestrator',
      settings: campaignData.settings || {}
    };

    const result = await this.firebaseService.createDocument('campaigns', campaign);

    if (result.success) {
      return {
        success: true,
        data: {
          campaignId: result.id,
          bartonId: result.barton_id
        }
      };
    }

    return result;
  }

  /**
   * Send campaign emails via Composio
   */
  async sendCampaignEmails(leads, campaignId) {
    console.log(`[ORCHESTRATOR] Sending emails to ${leads.length} qualified leads...`);

    const sentEmails = [];
    const failures = [];

    for (const lead of leads) {
      try {
        const emailResult = await this.composioService.sendEmail('sendgrid', {
          to: lead.email,
          subject: `Special offer for ${lead.name || 'you'}`,
          body: this.generateEmailBody(lead),
          from: process.env.CAMPAIGN_FROM_EMAIL || 'campaigns@example.com'
        });

        if (emailResult.success) {
          sentEmails.push({
            email: lead.email,
            status: 'sent',
            timestamp: new Date().toISOString()
          });
        } else {
          failures.push({
            email: lead.email,
            error: emailResult.error
          });
        }
      } catch (error) {
        failures.push({
          email: lead.email,
          error: error.message
        });
      }

      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return {
      success: true,
      data: {
        sentEmails,
        failures,
        successRate: (sentEmails.length / leads.length) * 100
      }
    };
  }

  /**
   * Track campaign events in Firebase
   */
  async trackCampaignEvents(campaignId, sentEmails) {
    console.log(`[ORCHESTRATOR] Tracking ${sentEmails.length} email events...`);

    const trackingResults = [];

    for (const email of sentEmails) {
      const result = await this.firebaseService.trackCampaignEvent(
        campaignId,
        'email_sent',
        {
          recipient: email.email,
          timestamp: email.timestamp,
          status: email.status
        }
      );

      trackingResults.push(result);
    }

    // Also track in Mixpanel via Composio
    await this.composioService.trackEvent('campaign_executed', {
      campaignId,
      emailsSent: sentEmails.length,
      timestamp: new Date().toISOString()
    });

    return {
      success: true,
      data: {
        eventsTracked: trackingResults.length
      }
    };
  }

  /**
   * Send notifications about workflow status
   */
  async sendNotifications(workflowId, status, errorMessage = null) {
    console.log(`[ORCHESTRATOR] Sending ${status} notification for workflow ${workflowId}`);

    const notifications = [];

    // Slack notification
    const slackMessage = status === 'completed'
      ? `✅ Workflow ${workflowId} completed successfully!`
      : `❌ Workflow ${workflowId} failed: ${errorMessage}`;

    const slackResult = await this.composioService.sendSlackMessage(
      process.env.SLACK_NOTIFICATION_CHANNEL || '#outreach',
      slackMessage
    );

    notifications.push({ channel: 'slack', result: slackResult });

    // Create GitHub issue for failures
    if (status === 'failed') {
      const issueResult = await this.composioService.createGitHubIssue(
        'barton-outreach-core',
        `Workflow failure: ${workflowId}`,
        `Workflow ${workflowId} failed with error:\n\n\`\`\`\n${errorMessage}\n\`\`\``,
        ['bug', 'workflow-failure']
      );

      notifications.push({ channel: 'github', result: issueResult });
    }

    return {
      success: true,
      data: {
        notifications
      }
    };
  }

  /**
   * Generate email body for a lead
   */
  generateEmailBody(lead) {
    return `
      <h2>Hello ${lead.name || 'there'}!</h2>

      <p>We noticed you're interested in our services${lead.company ? ` at ${lead.company}` : ''}.</p>

      <p>Based on your profile, we have a special offer that might interest you.</p>

      <p>Here's what we can offer:</p>
      <ul>
        <li>Personalized outreach campaigns</li>
        <li>Advanced lead scoring</li>
        <li>Multi-channel engagement</li>
        <li>Real-time analytics</li>
      </ul>

      <p>Ready to take your outreach to the next level?</p>

      <p><a href="${process.env.CAMPAIGN_CTA_URL || 'https://example.com/get-started'}">Get Started Now</a></p>

      <p>Best regards,<br>The Outreach Team</p>
    `;
  }

  /**
   * Generate workflow summary
   */
  generateWorkflowSummary(workflow) {
    const duration = new Date(workflow.endTime) - new Date(workflow.startTime);
    const durationSeconds = Math.floor(duration / 1000);

    return {
      id: workflow.id,
      status: workflow.status,
      steps: workflow.steps.length,
      duration: `${durationSeconds} seconds`,
      startTime: workflow.startTime,
      endTime: workflow.endTime
    };
  }

  /**
   * Generate workflow ID
   */
  generateWorkflowId() {
    return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get workflow status
   */
  getWorkflowStatus(workflowId) {
    const workflow = this.workflows.get(workflowId);

    if (!workflow) {
      return {
        success: false,
        error: 'Workflow not found'
      };
    }

    return {
      success: true,
      data: workflow
    };
  }

  /**
   * Health check for all services
   */
  async healthCheck() {
    const checks = await Promise.allSettled([
      this.composioService.healthCheck(),
      this.firebaseService.healthCheck()
    ]);

    return {
      composio: checks[0].status === 'fulfilled' ? checks[0].value : { healthy: false },
      firebase: checks[1].status === 'fulfilled' ? checks[1].value : { healthy: false },
      neon: { healthy: this.neonBridge.isInitialized },
      orchestrator: { healthy: this.initialized }
    };
  }
}

// Export as API handler for Vercel
export default async function handler(req, res) {
  const orchestrator = new OutreachOrchestrator();

  try {
    await orchestrator.initialize();

    if (req.method === 'POST') {
      const { action, data } = req.body;

      switch (action) {
        case 'execute_workflow':
          const result = await orchestrator.executeOutreachWorkflow(data);
          return res.status(200).json(result);

        case 'get_workflow_status':
          const status = orchestrator.getWorkflowStatus(data.workflowId);
          return res.status(200).json(status);

        case 'health_check':
          const health = await orchestrator.healthCheck();
          return res.status(200).json(health);

        default:
          return res.status(400).json({ error: 'Invalid action' });
      }
    } else {
      return res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error) {
    console.error('[API] Error:', error);
    return res.status(500).json({
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}