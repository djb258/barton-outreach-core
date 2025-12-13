const { spawn } = require('child_process');
const axios = require('axios');
const winston = require('winston');
const EventEmitter = require('events');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

class HeyReachMCPManager extends EventEmitter {
  constructor() {
    super();
    this.httpProcess = null;
    this.isRunning = false;
    this.apiKey = process.env.HEYREACH_API_KEY;
    this.httpPort = 3009; // Different from our service port (3007)
    this.restartAttempts = 0;
    this.maxRestartAttempts = 3;
    this.baseUrl = `http://localhost:${this.httpPort}`;
  }

  async start() {
    if (this.isRunning) {
      logger.warn('HeyReach MCP server is already running');
      return;
    }

    try {
      logger.info(`Starting HeyReach MCP HTTP server on port ${this.httpPort}...`);
      
      this.httpProcess = spawn('npx', [
        'heyreach-mcp-server',
        '--http',
        `--port=${this.httpPort}`
      ], {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      this.httpProcess.stdout.on('data', (data) => {
        logger.info(`HeyReach MCP stdout: ${data.toString()}`);
      });

      this.httpProcess.stderr.on('data', (data) => {
        const message = data.toString();
        logger.info(`HeyReach MCP stderr: ${message}`);
        
        // Check if server started successfully
        if (message.includes('listening on port')) {
          this.emit('started');
        }
      });

      this.httpProcess.on('close', (code) => {
        logger.warn(`HeyReach MCP server exited with code ${code}`);
        this.isRunning = false;
        this.emit('stopped', code);
        
        if (code !== 0 && this.restartAttempts < this.maxRestartAttempts) {
          this.restartAttempts++;
          logger.info(`Attempting restart ${this.restartAttempts}/${this.maxRestartAttempts}`);
          setTimeout(() => this.start(), 5000);
        }
      });

      this.httpProcess.on('error', (error) => {
        logger.error('HeyReach MCP server error:', error);
        this.emit('error', error);
      });

      // Wait for server to start
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('HeyReach MCP server start timeout'));
        }, 10000);

        this.once('started', () => {
          clearTimeout(timeout);
          resolve();
        });

        this.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

      this.isRunning = true;
      this.restartAttempts = 0;
      
      // Verify health
      await this.healthCheck();
      logger.info('HeyReach MCP server started and health check passed');

    } catch (error) {
      logger.error('Failed to start HeyReach MCP server:', error);
      throw error;
    }
  }

  async stop() {
    if (!this.isRunning || !this.httpProcess) {
      return;
    }

    logger.info('Stopping HeyReach MCP server...');
    
    this.httpProcess.kill('SIGTERM');
    
    // Force kill after 10 seconds if needed
    setTimeout(() => {
      if (this.isRunning && this.httpProcess) {
        logger.warn('Force killing HeyReach MCP server');
        this.httpProcess.kill('SIGKILL');
      }
    }, 10000);

    this.isRunning = false;
    this.emit('stopped');
  }

  async healthCheck() {
    try {
      const response = await axios.get(`${this.baseUrl}/health`, {
        timeout: 5000
      });
      
      return response.data;
    } catch (error) {
      logger.error('HeyReach MCP health check failed:', error.message);
      throw error;
    }
  }

  async sendMCPRequest(method, params = {}) {
    if (!this.isRunning) {
      throw new Error('HeyReach MCP server is not running');
    }

    try {
      const response = await axios.post(`${this.baseUrl}/mcp`, {
        jsonrpc: '2.0',
        id: Date.now(),
        method: method,
        params: params
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      });

      if (response.data.error) {
        throw new Error(response.data.error.message);
      }

      return response.data.result;

    } catch (error) {
      if (error.response) {
        logger.error(`MCP request failed: ${error.response.status} ${error.response.statusText}`);
        throw new Error(`MCP request failed: ${error.response.data?.message || error.response.statusText}`);
      }
      
      logger.error('MCP request failed:', error.message);
      throw error;
    }
  }

  // High-level methods for common operations
  async createCampaign(campaignData) {
    return this.sendMCPRequest('createCampaign', campaignData);
  }

  async addLeads(campaignId, leads) {
    return this.sendMCPRequest('addLeads', { campaignId, leads });
  }

  async startCampaign(campaignId) {
    return this.sendMCPRequest('startCampaign', { campaignId });
  }

  async stopCampaign(campaignId) {
    return this.sendMCPRequest('stopCampaign', { campaignId });
  }

  async getCampaigns() {
    return this.sendMCPRequest('getCampaigns');
  }

  async getCampaignStats(campaignId) {
    return this.sendMCPRequest('getCampaignStats', { campaignId });
  }

  async getLeads(campaignId) {
    return this.sendMCPRequest('getLeads', { campaignId });
  }

  async sendMessage(leadId, message) {
    return this.sendMCPRequest('sendMessage', { leadId, message });
  }

  async getAccount() {
    return this.sendMCPRequest('getAccount');
  }

  async extractProfile(linkedinUrl) {
    return this.sendMCPRequest('extractProfile', { linkedinUrl });
  }

  async searchProfiles(criteria) {
    return this.sendMCPRequest('searchProfiles', criteria);
  }

  getStatus() {
    return {
      running: this.isRunning,
      httpPort: this.httpPort,
      pid: this.httpProcess ? this.httpProcess.pid : null,
      restartAttempts: this.restartAttempts,
      apiKeyConfigured: !!this.apiKey,
      baseUrl: this.baseUrl
    };
  }

  // Test method to verify connection
  async testConnection() {
    try {
      await this.healthCheck();
      const account = await this.getAccount();
      return {
        success: true,
        connected: true,
        account: account
      };
    } catch (error) {
      return {
        success: false,
        connected: false,
        error: error.message
      };
    }
  }
}

module.exports = new HeyReachMCPManager();