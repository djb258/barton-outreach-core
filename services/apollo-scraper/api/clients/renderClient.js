const axios = require('axios');

class RenderMarketingDBClient {
  constructor(baseURL = 'https://render-marketing-db.onrender.com') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[RenderDB] ${config.method.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[RenderDB] Request error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[RenderDB] Response: ${response.status} ${response.statusText}`);
        return response;
      },
      (error) => {
        console.error('[RenderDB] Response error:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health & Status Methods
  async checkHealth() {
    try {
      const response = await this.client.get('/api/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  async getDatabaseStatus() {
    try {
      const response = await this.client.get('/api/db/status');
      return response.data;
    } catch (error) {
      throw new Error(`Database status check failed: ${error.message}`);
    }
  }

  // Marketing Companies Methods
  async getCompanies(params = {}) {
    try {
      const response = await this.client.get('/api/marketing/companies', { params });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch companies: ${error.message}`);
    }
  }

  async createCompany(companyData) {
    try {
      const response = await this.client.post('/api/marketing/companies', companyData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create company: ${error.message}`);
    }
  }

  async updateCompany(companyId, updateData) {
    try {
      const response = await this.client.put(`/api/marketing/companies/${companyId}`, updateData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update company: ${error.message}`);
    }
  }

  // Apollo Data Methods
  async getApolloData(params = {}) {
    try {
      const response = await this.client.get('/api/apollo/raw', { params });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch Apollo data: ${error.message}`);
    }
  }

  async submitApolloData(apolloData) {
    try {
      const response = await this.client.post('/api/apollo/raw', apolloData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to submit Apollo data: ${error.message}`);
    }
  }

  // Batch submit Apollo contacts
  async submitApolloContacts(companyId, contacts, metadata = {}) {
    try {
      const payload = {
        company_id: companyId,
        contacts: contacts,
        scraped_at: new Date().toISOString(),
        total_contacts: contacts.length,
        ...metadata
      };
      
      const response = await this.client.post('/api/apollo/raw', payload);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to submit Apollo contacts: ${error.message}`);
    }
  }

  // Legacy insert method
  async insertRecords(records) {
    try {
      const response = await this.client.post('/insert', records);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to insert records: ${error.message}`);
    }
  }

  // Utility method to test connection
  async testConnection() {
    try {
      console.log('[RenderDB] Testing connection to:', this.baseURL);
      
      // Test health endpoint
      const health = await this.checkHealth();
      console.log('[RenderDB] Health check:', health.status);
      
      // Test database status
      const dbStatus = await this.getDatabaseStatus();
      console.log('[RenderDB] Database status:', dbStatus.status);
      
      return {
        connected: true,
        health: health.status,
        database: dbStatus.status,
        baseURL: this.baseURL
      };
    } catch (error) {
      console.error('[RenderDB] Connection test failed:', error.message);
      return {
        connected: false,
        error: error.message,
        baseURL: this.baseURL
      };
    }
  }
}

// Export singleton instance and class
const renderClient = new RenderMarketingDBClient();

module.exports = {
  RenderMarketingDBClient,
  renderClient
};