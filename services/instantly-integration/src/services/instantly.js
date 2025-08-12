const axios = require('axios');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

class InstantlyService {
  constructor() {
    this.apiKey = process.env.INSTANTLY_API_KEY;
    this.baseUrl = 'https://api.instantly.ai/api/v1';
    this.axios = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async createCampaign(campaignData) {
    try {
      logger.info('Creating Instantly campaign', { name: campaignData.name });
      
      const response = await this.axios.post('/campaign/create', {
        api_key: this.apiKey,
        name: campaignData.name,
        from_name: campaignData.fromName,
        from_email: campaignData.fromEmail,
        reply_to_email: campaignData.replyTo,
        subject: campaignData.subject,
        body_html: campaignData.bodyHtml,
        body_text: campaignData.bodyText,
        schedule: campaignData.schedule || {
          timezone: 'America/New_York',
          days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
          start_hour: 9,
          end_hour: 17,
          emails_per_day: 50
        }
      });

      return {
        success: true,
        campaignId: response.data.campaign_id,
        status: 'created',
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to create campaign', error);
      throw error;
    }
  }

  async addContactsToCampaign(campaignId, contacts) {
    try {
      logger.info(`Adding ${contacts.length} contacts to campaign ${campaignId}`);
      
      const formattedContacts = contacts.map(contact => ({
        email: contact.email,
        first_name: contact.firstName,
        last_name: contact.lastName,
        company_name: contact.companyName,
        title: contact.title,
        custom_variables: {
          contact_id: contact.contactId,
          company_id: contact.companyId,
          slot_type: contact.slotType,
          linkedin_url: contact.linkedinUrl,
          phone: contact.phone
        }
      }));

      const response = await this.axios.post('/campaign/add_leads', {
        api_key: this.apiKey,
        campaign_id: campaignId,
        leads: formattedContacts,
        skip_if_in_workspace: true
      });

      return {
        success: true,
        added: response.data.added_count,
        skipped: response.data.skipped_count,
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to add contacts to campaign', error);
      throw error;
    }
  }

  async launchCampaign(campaignId) {
    try {
      logger.info(`Launching campaign ${campaignId}`);
      
      const response = await this.axios.post('/campaign/launch', {
        api_key: this.apiKey,
        campaign_id: campaignId
      });

      return {
        success: true,
        status: 'launched',
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to launch campaign', error);
      throw error;
    }
  }

  async pauseCampaign(campaignId) {
    try {
      logger.info(`Pausing campaign ${campaignId}`);
      
      const response = await this.axios.post('/campaign/pause', {
        api_key: this.apiKey,
        campaign_id: campaignId
      });

      return {
        success: true,
        status: 'paused',
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to pause campaign', error);
      throw error;
    }
  }

  async getCampaignStats(campaignId) {
    try {
      logger.info(`Getting stats for campaign ${campaignId}`);
      
      const response = await this.axios.get('/analytics/campaign', {
        params: {
          api_key: this.apiKey,
          campaign_id: campaignId
        }
      });

      return {
        success: true,
        stats: {
          sent: response.data.sent_count,
          opened: response.data.opened_count,
          clicked: response.data.clicked_count,
          replied: response.data.replied_count,
          bounced: response.data.bounced_count,
          unsubscribed: response.data.unsubscribed_count,
          openRate: response.data.open_rate,
          clickRate: response.data.click_rate,
          replyRate: response.data.reply_rate
        }
      };
    } catch (error) {
      logger.error('Failed to get campaign stats', error);
      throw error;
    }
  }

  async getEmailStatus(email) {
    try {
      logger.info(`Getting status for email ${email}`);
      
      const response = await this.axios.get('/lead/get', {
        params: {
          api_key: this.apiKey,
          email: email
        }
      });

      return {
        success: true,
        status: response.data.status,
        events: response.data.events,
        lastActivity: response.data.last_activity
      };
    } catch (error) {
      logger.error('Failed to get email status', error);
      throw error;
    }
  }

  async handleWebhook(webhookData) {
    try {
      logger.info('Processing Instantly webhook', { type: webhookData.event_type });
      
      const outcome = {
        id: uuidv4(),
        platform: 'instantly',
        eventType: webhookData.event_type,
        contactEmail: webhookData.lead_email,
        campaignId: webhookData.campaign_id,
        timestamp: new Date(webhookData.timestamp),
        details: {
          campaignName: webhookData.campaign_name,
          contactId: webhookData.custom_variables?.contact_id,
          companyId: webhookData.custom_variables?.company_id,
          slotType: webhookData.custom_variables?.slot_type
        }
      };

      switch (webhookData.event_type) {
        case 'email_sent':
          outcome.status = 'sent';
          break;
        case 'email_opened':
          outcome.status = 'opened';
          outcome.details.openCount = webhookData.open_count;
          break;
        case 'link_clicked':
          outcome.status = 'clicked';
          outcome.details.clickedUrl = webhookData.clicked_url;
          break;
        case 'email_replied':
          outcome.status = 'replied';
          outcome.details.replyContent = webhookData.reply_content;
          break;
        case 'email_bounced':
          outcome.status = 'bounced';
          outcome.details.bounceType = webhookData.bounce_type;
          break;
        case 'unsubscribed':
          outcome.status = 'unsubscribed';
          break;
        default:
          outcome.status = 'unknown';
      }

      return outcome;
    } catch (error) {
      logger.error('Failed to process webhook', error);
      throw error;
    }
  }

  async getAccountLimits() {
    try {
      const response = await this.axios.get('/account/status', {
        params: {
          api_key: this.apiKey
        }
      });

      return {
        success: true,
        limits: {
          emailsPerDay: response.data.emails_per_day_limit,
          emailsSentToday: response.data.emails_sent_today,
          campaignsLimit: response.data.campaigns_limit,
          activeCampaigns: response.data.active_campaigns,
          accountStatus: response.data.status
        }
      };
    } catch (error) {
      logger.error('Failed to get account limits', error);
      throw error;
    }
  }

  async createEmailSequence(sequenceData) {
    try {
      logger.info('Creating email sequence', { name: sequenceData.name });
      
      const sequence = {
        api_key: this.apiKey,
        name: sequenceData.name,
        emails: sequenceData.emails.map((email, index) => ({
          subject: email.subject,
          body_html: email.bodyHtml,
          body_text: email.bodyText,
          delay_days: email.delayDays || index * 3,
          send_on_reply: false
        }))
      };

      const response = await this.axios.post('/sequence/create', sequence);

      return {
        success: true,
        sequenceId: response.data.sequence_id,
        emailCount: response.data.email_count
      };
    } catch (error) {
      logger.error('Failed to create sequence', error);
      throw error;
    }
  }

  async testConnection() {
    try {
      const response = await this.axios.get('/account/status', {
        params: {
          api_key: this.apiKey
        }
      });

      return {
        success: true,
        connected: response.data.status === 'active',
        accountEmail: response.data.email,
        plan: response.data.plan
      };
    } catch (error) {
      logger.error('Connection test failed', error);
      return {
        success: false,
        connected: false,
        error: error.message
      };
    }
  }
}

module.exports = new InstantlyService();