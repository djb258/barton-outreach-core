const axios = require('axios');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

class HeyReachService {
  constructor() {
    this.apiKey = process.env.HEYREACH_API_KEY;
    this.baseUrl = 'https://api.heyreach.io/api/v1';
    this.axios = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async createCampaign(campaignData) {
    try {
      logger.info('Creating HeyReach campaign', { name: campaignData.name });
      
      const response = await this.axios.post('/campaigns', {
        name: campaignData.name,
        type: campaignData.type || 'connection_request',
        daily_limit: campaignData.dailyLimit || 20,
        timezone: campaignData.timezone || 'America/New_York',
        schedule: {
          days: campaignData.days || ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
          start_hour: campaignData.startHour || 9,
          end_hour: campaignData.endHour || 17
        },
        connection_request_message: campaignData.connectionMessage,
        follow_up_messages: campaignData.followUpMessages || []
      });

      return {
        success: true,
        campaignId: response.data.id,
        status: 'created',
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to create campaign', error);
      throw error;
    }
  }

  async addLeadsToCampaign(campaignId, leads) {
    try {
      logger.info(`Adding ${leads.length} leads to campaign ${campaignId}`);
      
      const formattedLeads = leads.map(lead => ({
        linkedin_url: lead.linkedinUrl,
        first_name: lead.firstName,
        last_name: lead.lastName,
        company: lead.companyName,
        title: lead.title,
        email: lead.email,
        custom_fields: {
          contact_id: lead.contactId,
          company_id: lead.companyId,
          slot_type: lead.slotType,
          phone: lead.phone
        }
      }));

      const response = await this.axios.post(`/campaigns/${campaignId}/leads`, {
        leads: formattedLeads
      });

      return {
        success: true,
        added: response.data.added_count,
        skipped: response.data.skipped_count,
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to add leads to campaign', error);
      throw error;
    }
  }

  async startCampaign(campaignId) {
    try {
      logger.info(`Starting campaign ${campaignId}`);
      
      const response = await this.axios.post(`/campaigns/${campaignId}/start`);

      return {
        success: true,
        status: 'running',
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to start campaign', error);
      throw error;
    }
  }

  async pauseCampaign(campaignId) {
    try {
      logger.info(`Pausing campaign ${campaignId}`);
      
      const response = await this.axios.post(`/campaigns/${campaignId}/pause`);

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
      
      const response = await this.axios.get(`/campaigns/${campaignId}/stats`);

      return {
        success: true,
        stats: {
          totalLeads: response.data.total_leads,
          connectionsSent: response.data.connections_sent,
          connectionsAccepted: response.data.connections_accepted,
          messagesSent: response.data.messages_sent,
          messagesReplied: response.data.messages_replied,
          connectionRate: response.data.connection_rate,
          replyRate: response.data.reply_rate,
          profilesViewed: response.data.profiles_viewed
        }
      };
    } catch (error) {
      logger.error('Failed to get campaign stats', error);
      throw error;
    }
  }

  async getLeadStatus(leadId) {
    try {
      logger.info(`Getting status for lead ${leadId}`);
      
      const response = await this.axios.get(`/leads/${leadId}`);

      return {
        success: true,
        status: response.data.status,
        connectionStatus: response.data.connection_status,
        lastActivity: response.data.last_activity,
        messages: response.data.messages
      };
    } catch (error) {
      logger.error('Failed to get lead status', error);
      throw error;
    }
  }

  async sendMessage(leadId, message) {
    try {
      logger.info(`Sending message to lead ${leadId}`);
      
      const response = await this.axios.post(`/leads/${leadId}/message`, {
        message: message.text,
        schedule_for: message.scheduleFor
      });

      return {
        success: true,
        messageId: response.data.message_id,
        status: 'scheduled'
      };
    } catch (error) {
      logger.error('Failed to send message', error);
      throw error;
    }
  }

  async handleWebhook(webhookData) {
    try {
      logger.info('Processing HeyReach webhook', { type: webhookData.event });
      
      const outcome = {
        id: uuidv4(),
        platform: 'heyreach',
        eventType: webhookData.event,
        leadId: webhookData.lead_id,
        campaignId: webhookData.campaign_id,
        timestamp: new Date(webhookData.timestamp),
        details: {
          campaignName: webhookData.campaign_name,
          linkedinUrl: webhookData.linkedin_url,
          contactId: webhookData.custom_fields?.contact_id,
          companyId: webhookData.custom_fields?.company_id,
          slotType: webhookData.custom_fields?.slot_type
        }
      };

      switch (webhookData.event) {
        case 'connection_request_sent':
          outcome.status = 'connection_sent';
          break;
        case 'connection_accepted':
          outcome.status = 'connected';
          outcome.details.connectedAt = webhookData.connected_at;
          break;
        case 'message_sent':
          outcome.status = 'message_sent';
          outcome.details.messageContent = webhookData.message_content;
          break;
        case 'message_replied':
          outcome.status = 'replied';
          outcome.details.replyContent = webhookData.reply_content;
          break;
        case 'profile_viewed':
          outcome.status = 'profile_viewed';
          break;
        case 'connection_declined':
          outcome.status = 'declined';
          break;
        case 'lead_skipped':
          outcome.status = 'skipped';
          outcome.details.skipReason = webhookData.skip_reason;
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
      const response = await this.axios.get('/account/limits');

      return {
        success: true,
        limits: {
          dailyConnectionLimit: response.data.daily_connection_limit,
          dailyMessageLimit: response.data.daily_message_limit,
          connectionsToday: response.data.connections_sent_today,
          messagesToday: response.data.messages_sent_today,
          accountStatus: response.data.status,
          linkedInAccounts: response.data.linkedin_accounts
        }
      };
    } catch (error) {
      logger.error('Failed to get account limits', error);
      throw error;
    }
  }

  async createMessageSequence(sequenceData) {
    try {
      logger.info('Creating message sequence', { name: sequenceData.name });
      
      const sequence = {
        name: sequenceData.name,
        messages: sequenceData.messages.map((msg, index) => ({
          content: msg.content,
          delay_days: msg.delayDays || index * 3,
          send_only_if_no_reply: true,
          personalization_tags: msg.personalizationTags || []
        }))
      };

      const response = await this.axios.post('/sequences', sequence);

      return {
        success: true,
        sequenceId: response.data.id,
        messageCount: response.data.message_count
      };
    } catch (error) {
      logger.error('Failed to create sequence', error);
      throw error;
    }
  }

  async searchLinkedInProfiles(searchCriteria) {
    try {
      logger.info('Searching LinkedIn profiles', searchCriteria);
      
      const response = await this.axios.post('/search/linkedin', {
        keywords: searchCriteria.keywords,
        location: searchCriteria.location,
        industry: searchCriteria.industry,
        company_size: searchCriteria.companySize,
        title: searchCriteria.title,
        limit: searchCriteria.limit || 100
      });

      return {
        success: true,
        profiles: response.data.profiles,
        total: response.data.total_found
      };
    } catch (error) {
      logger.error('Failed to search profiles', error);
      throw error;
    }
  }

  async extractProfileData(linkedinUrl) {
    try {
      logger.info('Extracting profile data', { url: linkedinUrl });
      
      const response = await this.axios.post('/extract/profile', {
        linkedin_url: linkedinUrl
      });

      return {
        success: true,
        profile: {
          firstName: response.data.first_name,
          lastName: response.data.last_name,
          title: response.data.title,
          company: response.data.company,
          location: response.data.location,
          about: response.data.about,
          experience: response.data.experience,
          skills: response.data.skills
        }
      };
    } catch (error) {
      logger.error('Failed to extract profile', error);
      throw error;
    }
  }

  async testConnection() {
    try {
      const response = await this.axios.get('/account/status');

      return {
        success: true,
        connected: response.data.status === 'active',
        accountEmail: response.data.email,
        linkedInAccounts: response.data.linkedin_accounts,
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

module.exports = new HeyReachService();