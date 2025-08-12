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
      sent: 0,
      opened: 0,
      clicked: 0,
      replied: 0,
      bounced: 0,
      unsubscribed: 0,
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
        channel: 'email',
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
      sent: 1,
      opened: 2,
      clicked: 3,
      replied: 5,
      meeting_booked: 10,
      converted: 20,
      bounced: -2,
      unsubscribed: -3,
      complained: -5
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
      sent: 0,
      opened: 0,
      clicked: 0,
      replied: 0,
      bounced: 0,
      unsubscribed: 0
    };

    for (const outcome of outcomes) {
      if (metrics.hasOwnProperty(outcome.status)) {
        metrics[outcome.status]++;
      }
    }

    const openRate = metrics.sent > 0 ? (metrics.opened / metrics.sent) * 100 : 0;
    const clickRate = metrics.opened > 0 ? (metrics.clicked / metrics.opened) * 100 : 0;
    const replyRate = metrics.sent > 0 ? (metrics.replied / metrics.sent) * 100 : 0;

    return {
      campaignId,
      metrics,
      rates: {
        openRate: openRate.toFixed(2),
        clickRate: clickRate.toFixed(2),
        replyRate: replyRate.toFixed(2)
      },
      totalContacts: outcomes.length
    };
  }

  async getSlotPerformance() {
    const slotMetrics = {
      CEO: { sent: 0, opened: 0, replied: 0, converted: 0 },
      CFO: { sent: 0, opened: 0, replied: 0, converted: 0 },
      HR: { sent: 0, opened: 0, replied: 0, converted: 0 }
    };

    for (const [id, outcome] of this.outcomes) {
      const slot = outcome.slotType;
      if (slotMetrics[slot]) {
        if (outcome.status === 'sent') slotMetrics[slot].sent++;
        if (outcome.status === 'opened') slotMetrics[slot].opened++;
        if (outcome.status === 'replied') slotMetrics[slot].replied++;
        if (outcome.status === 'converted') slotMetrics[slot].converted++;
      }
    }

    for (const slot in slotMetrics) {
      const metrics = slotMetrics[slot];
      metrics.openRate = metrics.sent > 0 ? (metrics.opened / metrics.sent) * 100 : 0;
      metrics.replyRate = metrics.sent > 0 ? (metrics.replied / metrics.sent) * 100 : 0;
      metrics.conversionRate = metrics.sent > 0 ? (metrics.converted / metrics.sent) * 100 : 0;
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