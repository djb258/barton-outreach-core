const { spawn } = require('child_process');
const axios = require('axios');
const winston = require('winston');
const EventEmitter = require('events');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

class InstantlyMCPManager extends EventEmitter {
  constructor() {
    super();
    this.process = null;
    this.isRunning = false;
    this.apiKey = process.env.INSTANTLY_API_KEY;
    this.restartAttempts = 0;
    this.maxRestartAttempts = 3;
  }

  async start() {
    if (this.isRunning) {
      logger.warn('Instantly MCP server is already running');
      return;
    }

    try {
      logger.info('Starting Instantly MCP server...');
      
      this.process = spawn('npx', [
        'instantly-mcp', 
        `--api-key=${this.apiKey}`
      ], {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      this.process.stdout.on('data', (data) => {
        logger.info(`Instantly MCP stdout: ${data.toString()}`);
      });

      this.process.stderr.on('data', (data) => {
        logger.error(`Instantly MCP stderr: ${data.toString()}`);
      });

      this.process.on('close', (code) => {
        logger.warn(`Instantly MCP server exited with code ${code}`);
        this.isRunning = false;
        this.emit('stopped', code);
        
        if (code !== 0 && this.restartAttempts < this.maxRestartAttempts) {
          this.restartAttempts++;
          logger.info(`Attempting restart ${this.restartAttempts}/${this.maxRestartAttempts}`);
          setTimeout(() => this.start(), 5000);
        }
      });

      this.process.on('error', (error) => {
        logger.error('Instantly MCP server error:', error);
        this.emit('error', error);
      });

      this.isRunning = true;
      this.restartAttempts = 0;
      this.emit('started');
      
      logger.info('Instantly MCP server started successfully');

    } catch (error) {
      logger.error('Failed to start Instantly MCP server:', error);
      throw error;
    }
  }

  async stop() {
    if (!this.isRunning || !this.process) {
      return;
    }

    logger.info('Stopping Instantly MCP server...');
    
    this.process.kill('SIGTERM');
    
    // Force kill after 10 seconds if needed
    setTimeout(() => {
      if (this.isRunning && this.process) {
        logger.warn('Force killing Instantly MCP server');
        this.process.kill('SIGKILL');
      }
    }, 10000);

    this.isRunning = false;
    this.emit('stopped');
  }

  async sendMCPRequest(method, params = {}) {
    if (!this.isRunning) {
      throw new Error('Instantly MCP server is not running');
    }

    try {
      // MCP communication through stdio
      const request = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: method,
        params: params
      };

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('MCP request timeout'));
        }, 30000);

        this.process.stdin.write(JSON.stringify(request) + '\n');

        const onData = (data) => {
          try {
            const response = JSON.parse(data.toString());
            if (response.id === request.id) {
              clearTimeout(timeout);
              this.process.stdout.removeListener('data', onData);
              
              if (response.error) {
                reject(new Error(response.error.message));
              } else {
                resolve(response.result);
              }
            }
          } catch (error) {
            // Ignore parse errors for non-JSON output
          }
        };

        this.process.stdout.on('data', onData);
      });

    } catch (error) {
      logger.error('MCP request failed:', error);
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

  async getCampaigns() {
    return this.sendMCPRequest('getCampaigns');
  }

  async getCampaignStats(campaignId) {
    return this.sendMCPRequest('getCampaignStats', { campaignId });
  }

  async getAccountInfo() {
    return this.sendMCPRequest('getAccountInfo');
  }

  getStatus() {
    return {
      running: this.isRunning,
      pid: this.process ? this.process.pid : null,
      restartAttempts: this.restartAttempts,
      apiKeyConfigured: !!this.apiKey
    };
  }
}

module.exports = new InstantlyMCPManager();