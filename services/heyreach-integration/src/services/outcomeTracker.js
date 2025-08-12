const winston = require('winston');
const { v4: uuidv4 } = require('uuid');
const EventEmitter = require('events');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

class OutcomeTracker extends EventEmitter {
  constructor() {
    super();
    this.outcomes = new Map();
    this.metrics = {
      connection_sent: 0,
      connected: 0,
      message_sent: 0,
      replied: 0,
      profile_viewed: 0,
      declined: 0,
      meeting_booked: 0,
      conversions: 0
    };
  }

  async trackOutcome(outcome) {
    try {
      const outcomeId = outcome.id || uuidv4();
      const timestamp = new Date();
      
      const fullOutcome = {
        id: outcomeId,
        platform: outcome.platform,
        channel: 'linkedin',
        contactId: outcome.contactId,
        companyId: outcome.companyId,
        campaignId: outcome.campaignId,
        slotType: outcome.slotType,
        status: outcome.status,
        timestamp: timestamp,
        metadata: outcome.metadata || {},
        score: this.calculateOutcomeScore(outcome)
      };

      this.outcomes.set(outcomeId, fullOutcome);
      this.updateMetrics(outcome.status);
      this.emit('outcome_tracked', fullOutcome);

      logger.info('Outcome tracked', {
        id: outcomeId,
        status: outcome.status,
        platform: outcome.platform
      });

      return fullOutcome;
    } catch (error) {
      logger.error('Failed to track outcome', error);
      throw error;
    }
  }

  calculateOutcomeScore(outcome) {
    const scores = {
      connection_sent: 1,
      profile_viewed: 1,
      connected: 3,
      message_sent: 2,
      replied: 5,
      meeting_booked: 10,
      converted: 20,
      declined: -1,
      ignored: -1,
      blocked: -5
    };

    return scores[outcome.status] || 0;
  }

  updateMetrics(status) {
    if (this.metrics.hasOwnProperty(status)) {
      this.metrics[status]++;
    }
  }

  async getOutcomesByContact(contactId) {
    const contactOutcomes = [];
    for (const [id, outcome] of this.outcomes) {
      if (outcome.contactId === contactId) {
        contactOutcomes.push(outcome);
      }
    }
    return contactOutcomes.sort((a, b) => b.timestamp - a.timestamp);
  }

  async getOutcomesByCampaign(campaignId) {
    const campaignOutcomes = [];
    for (const [id, outcome] of this.outcomes) {
      if (outcome.campaignId === campaignId) {
        campaignOutcomes.push(outcome);
      }
    }
    return campaignOutcomes;
  }

  async getOutcomesByCompany(companyId) {
    const companyOutcomes = [];
    for (const [id, outcome] of this.outcomes) {
      if (outcome.companyId === companyId) {
        companyOutcomes.push(outcome);
      }
    }
    return companyOutcomes;
  }

  async getEngagementScore(contactId) {
    const outcomes = await this.getOutcomesByContact(contactId);
    let totalScore = 0;
    
    for (const outcome of outcomes) {
      totalScore += outcome.score;
    }

    const engagementLevel = totalScore >= 10 ? 'high' :
                           totalScore >= 5 ? 'medium' :
                           totalScore >= 1 ? 'low' : 'none';

    return {
      contactId,
      totalScore,
      engagementLevel,
      outcomeCount: outcomes.length,
      lastActivity: outcomes[0]?.timestamp
    };
  }

  async getCampaignPerformance(campaignId) {
    const outcomes = await this.getOutcomesByCampaign(campaignId);
    
    const metrics = {
      connection_sent: 0,
      connected: 0,
      message_sent: 0,
      replied: 0,
      declined: 0
    };

    for (const outcome of outcomes) {
      if (metrics.hasOwnProperty(outcome.status)) {
        metrics[outcome.status]++;
      }
    }

    const connectionRate = metrics.connection_sent > 0 ? 
      (metrics.connected / metrics.connection_sent) * 100 : 0;
    const replyRate = metrics.message_sent > 0 ? 
      (metrics.replied / metrics.message_sent) * 100 : 0;

    return {
      campaignId,
      metrics,
      rates: {
        connectionRate: connectionRate.toFixed(2),
        replyRate: replyRate.toFixed(2)
      },
      totalContacts: outcomes.length
    };
  }

  async getSlotPerformance() {
    const slotMetrics = {
      CEO: { sent: 0, connected: 0, replied: 0, converted: 0 },
      CFO: { sent: 0, connected: 0, replied: 0, converted: 0 },
      HR: { sent: 0, connected: 0, replied: 0, converted: 0 }
    };

    for (const [id, outcome] of this.outcomes) {
      const slot = outcome.slotType;
      if (slotMetrics[slot]) {
        if (outcome.status === 'connection_sent') slotMetrics[slot].sent++;
        if (outcome.status === 'connected') slotMetrics[slot].connected++;
        if (outcome.status === 'replied') slotMetrics[slot].replied++;
        if (outcome.status === 'converted') slotMetrics[slot].converted++;
      }
    }

    for (const slot in slotMetrics) {
      const metrics = slotMetrics[slot];
      metrics.connectionRate = metrics.sent > 0 ? 
        (metrics.connected / metrics.sent) * 100 : 0;
      metrics.replyRate = metrics.connected > 0 ? 
        (metrics.replied / metrics.connected) * 100 : 0;
      metrics.conversionRate = metrics.sent > 0 ? 
        (metrics.converted / metrics.sent) * 100 : 0;
    }

    return slotMetrics;
  }

  async aggregateOutcomes(timeRange = '24h') {
    const now = new Date();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000
    };

    const cutoff = new Date(now - timeRanges[timeRange]);
    const recentOutcomes = [];

    for (const [id, outcome] of this.outcomes) {
      if (outcome.timestamp >= cutoff) {
        recentOutcomes.push(outcome);
      }
    }

    return {
      timeRange,
      totalOutcomes: recentOutcomes.length,
      metrics: this.metrics,
      topPerformers: this.getTopPerformers(recentOutcomes)
    };
  }

  getTopPerformers(outcomes) {
    const contactScores = new Map();

    for (const outcome of outcomes) {
      const current = contactScores.get(outcome.contactId) || 0;
      contactScores.set(outcome.contactId, current + outcome.score);
    }

    const sorted = Array.from(contactScores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    return sorted.map(([contactId, score]) => ({ contactId, score }));
  }

  async getLinkedInNetworkGrowth() {
    let connectionsByDay = new Map();
    
    for (const [id, outcome] of this.outcomes) {
      if (outcome.status === 'connected') {
        const day = outcome.timestamp.toISOString().split('T')[0];
        connectionsByDay.set(day, (connectionsByDay.get(day) || 0) + 1);
      }
    }

    return Array.from(connectionsByDay.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([date, count]) => ({ date, connections: count }));
  }

  async exportOutcomes(format = 'json') {
    const allOutcomes = Array.from(this.outcomes.values());

    if (format === 'csv') {
      const headers = ['ID', 'Platform', 'Contact ID', 'Company ID', 'Campaign ID', 
                      'Slot Type', 'Status', 'Score', 'Timestamp'];
      const rows = allOutcomes.map(o => [
        o.id, o.platform, o.contactId, o.companyId, o.campaignId,
        o.slotType, o.status, o.score, o.timestamp.toISOString()
      ]);
      
      return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    return allOutcomes;
  }
}

module.exports = new OutcomeTracker();