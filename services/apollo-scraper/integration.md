# Apollo Scraper Service Integration

## Overview
This document outlines how the Apollo Scraper Service integrates with the Barton Outreach Core system.

## Integration Points

### 1. HEIR Architecture Integration

#### Agent Registry Integration
Add to `src/lib/heir/agent-registry.ts`:

```typescript
import { apolloScraperAgent } from '../../services/apollo-scraper/integration/agent-config';

export const agentRegistry = {
  // existing agents...
  'apollo-scraper': apolloScraperAgent,
  // other agents...
};
```

#### Orchestration Engine Integration
Add to `src/lib/heir/orchestration-engine.ts`:

```typescript
// Apollo Scraper task definitions
export const apolloScraperTasks = {
  'scrape-company': {
    agent: 'apollo-scraper',
    endpoint: '/api/v1/integrated/scrape-and-store',
    timeout: 300000, // 5 minutes
    retries: 2
  },
  'batch-scrape': {
    agent: 'apollo-scraper', 
    endpoint: '/api/v1/integrated/batch-scrape',
    timeout: 600000, // 10 minutes
    retries: 1
  }
};
```

### 2. Frontend Integration

#### Campaign Execution Page
Update `src/pages/doctrine/CampaignExecutionPage.tsx`:

```typescript
import { apolloScraperService } from '../../services/apollo-scraper/client';

// Add scraping capability to campaign execution
const handleApolloScrape = async (company: Company) => {
  try {
    const result = await apolloScraperService.scrapeAndStore({
      companyName: company.name,
      apolloUrl: company.apolloUrl,
      maxResults: 1000,
      filterByTitle: true
    });
    
    // Update UI with scraping status
    setScrapingJobs(prev => [...prev, result.job]);
  } catch (error) {
    console.error('Scraping failed:', error);
  }
};
```

#### Lead Intake Page 
Update `src/pages/doctrine/LeadIntakePage.tsx`:

```typescript
// Add Apollo URL validation and company setup
const handleCompanySetup = async (companyData: CompanyData) => {
  // Validate Apollo URL
  const isValidUrl = await apolloScraperService.validateApolloUrl(companyData.apolloUrl);
  
  if (isValidUrl) {
    // Store company for future scraping
    await apolloScraperService.createCompany(companyData);
  }
};
```

### 3. Component Integration

#### Add Apollo Scraper Dashboard Component
Create `src/components/heir/ApolloScraperDashboard.tsx`:

```typescript
import React from 'react';
import { useApolloScraper } from '../../hooks/useApolloScraper';

export const ApolloScraperDashboard = () => {
  const { jobs, startScrape, getJobStatus } = useApolloScraper();
  
  return (
    <div className="apollo-scraper-dashboard">
      <h2>Apollo Scraping Jobs</h2>
      {/* Dashboard implementation */}
    </div>
  );
};
```

#### Custom Hook
Create `src/hooks/useApolloScraper.ts`:

```typescript
import { useState, useEffect } from 'react';
import { apolloScraperService } from '../services/apollo-scraper/client';

export const useApolloScraper = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const startScrape = async (companyData) => {
    setLoading(true);
    try {
      const result = await apolloScraperService.scrapeAndStore(companyData);
      setJobs(prev => [...prev, result.job]);
      return result;
    } finally {
      setLoading(false);
    }
  };
  
  return { jobs, startScrape, loading };
};
```

### 4. Service Client
Create `services/apollo-scraper/client/index.ts`:

```typescript
class ApolloScraperService {
  private baseUrl: string;
  
  constructor(baseUrl = 'http://localhost:3000') {
    this.baseUrl = baseUrl;
  }
  
  async scrapeAndStore(data: ScrapeRequest) {
    const response = await fetch(`${this.baseUrl}/api/v1/integrated/scrape-and-store`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
  
  async getJobStatus(jobId: string) {
    const response = await fetch(`${this.baseUrl}/api/v1/scraper/status/${jobId}`);
    return response.json();
  }
  
  // Additional methods...
}

export const apolloScraperService = new ApolloScraperService();
```

### 5. Environment Configuration

#### Add to main `.env`:
```env
# Apollo Scraper Service
APOLLO_SCRAPER_URL=http://localhost:3000
APOLLO_SCRAPER_ENABLED=true
APIFY_API_KEY=apify_api_63CEvQr4uy247iyULJibGB1JSOHYtd2RVDqH
```

#### Update `vite.config.ts` for development:
```typescript
export default defineConfig({
  // existing config...
  server: {
    proxy: {
      '/api/apollo-scraper': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/apollo-scraper/, '/api/v1')
      }
    }
  }
});
```

### 6. Package.json Scripts

#### Add to main `package.json`:
```json
{
  "scripts": {
    // existing scripts...
    "start:apollo-scraper": "cd services/apollo-scraper && npm run start:api",
    "dev:apollo-scraper": "cd services/apollo-scraper && npm run dev:api",
    "test:apollo-scraper": "cd services/apollo-scraper && npm run test:all",
    "dev:full": "concurrently \"npm run dev\" \"npm run dev:apollo-scraper\""
  }
}
```

### 7. Docker Integration

#### Add to `docker-compose.yml`:
```yaml
version: '3.8'
services:
  barton-core:
    # existing service config...
  
  apollo-scraper:
    build: ./services/apollo-scraper
    ports:
      - "3000:3000"
    environment:
      - APIFY_API_KEY=${APIFY_API_KEY}
      - RENDER_DB_URL=${RENDER_DB_URL}
    depends_on:
      - barton-core
```

### 8. Monitoring Integration

#### Add health checks to main monitoring:
```typescript
// src/components/heir/SystemMonitor.tsx
const apolloScraperHealth = await fetch('/api/apollo-scraper/health');
const healthData = await apolloScraperHealth.json();

// Display health status in main dashboard
```

## Deployment Strategy

### Development
1. Start main Barton Core: `npm run dev`
2. Start Apollo Scraper: `npm run dev:apollo-scraper`
3. Both services run concurrently

### Production
1. Deploy as microservice alongside main application
2. Configure service discovery
3. Set up health checks and monitoring
4. Configure logging aggregation

## Testing Integration

### End-to-End Tests
```typescript
// cypress/integration/apollo-scraper.spec.ts
describe('Apollo Scraper Integration', () => {
  it('should start scraping from campaign page', () => {
    cy.visit('/doctrine/campaign-execution');
    cy.get('[data-testid="start-scrape-button"]').click();
    cy.get('[data-testid="scraping-job-status"]').should('contain', 'running');
  });
});
```

This integration ensures the Apollo Scraper Service seamlessly fits into the existing Barton Outreach Core architecture while maintaining the HEIR principles.