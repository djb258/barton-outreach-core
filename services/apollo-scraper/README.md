# Apollo Scraper Service

A comprehensive Apollo.io scraping service integrated with the Barton Outreach Core system. This service provides REST API endpoints for scraping contact data from Apollo.io and storing it in the Render marketing database.

## 🏗️ Architecture Integration

This service is part of the **Barton Outreach Core** ecosystem and follows the HEIR architecture pattern:

```
barton-outreach-core/
├── services/
│   └── apollo-scraper/          # This service
│       ├── api/                 # REST API endpoints
│       ├── modules/             # Core scraping logic
│       ├── docs/                # Documentation
│       └── tests/               # Test suites
├── src/                         # Main application
└── ops/orbt/                    # Operations & runbooks
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd services/apollo-scraper
npm install
```

### 2. Configure Environment
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Update with your credentials:
```env
# Apify Configuration (WORKING!)
APIFY_API_KEY=apify_api_63CEvQr4uy247iyULJibGB1JSOHYtd2RVDqH
APIFY_ACTOR_ID=jljBwyyQakqrL1wae

# API Configuration
PORT=3000
DRY_RUN=false
```

### 3. Start the Service
```bash
npm run start:api
```

Visit: http://localhost:3000

## 📊 Core Capabilities

### Integrated Scraping Workflow
1. **Apollo URL Analysis** - Parse and validate Apollo search parameters
2. **Apify Integration** - Launch scraping jobs using the Apollo scraper actor
3. **Data Processing** - Filter contacts by executive titles and roles
4. **Database Storage** - Store results in Render marketing database
5. **Status Tracking** - Monitor job progress and completion

### API Endpoints

#### Primary Integration Endpoints
- `POST /api/v1/integrated/scrape-and-store` - Complete scrape & store workflow
- `POST /api/v1/integrated/batch-scrape` - Process multiple companies
- `GET /api/v1/integrated/company-status/{name}` - Check company status

#### Individual Service Endpoints  
- Scraper operations (`/api/v1/scraper/*`)
- Company management (`/api/v1/companies/*`)
- Results handling (`/api/v1/results/*`)
- Health monitoring (`/api/v1/health/*`)

## 🎯 Example Usage

### Start a Scraping Job
```bash
curl -X POST http://localhost:3000/api/v1/integrated/scrape-and-store \
  -H "Content-Type: application/json" \
  -d '{
    "companyName": "German Tech Corp",
    "apolloUrl": "https://app.apollo.io/#/people?personLocations[]=Germany&organizationNumEmployeesRanges[]=5000%2C5200",
    "maxResults": 1000,
    "filterByTitle": true,
    "industry": "Technology",
    "location": "Germany"
  }'
```

### Response
```json
{
  "success": true,
  "message": "Scraping job started for German Tech Corp",
  "job": {
    "id": "apify-run-12345",
    "companyName": "German Tech Corp",  
    "status": "running",
    "datasetId": "dataset-67890"
  }
}
```

## 🔧 Integration with Barton Core

### HEIR Architecture Alignment
- **H**ierarchical: Service operates as a specialized agent within the core system
- **E**vent-driven: Async processing with status updates and callbacks
- **I**ntelligent: Smart filtering and data processing capabilities  
- **R**esilient: Comprehensive error handling and retry mechanisms

### Data Flow Integration
```
Barton Core → Apollo Scraper → Apify → Apollo.io
     ↓              ↓             ↓
Render DB ← Data Processing ← Raw Results
```

### Service Registry
The Apollo Scraper registers itself with the core system:
```typescript
// Integration point with src/lib/heir/agent-registry.ts
export const apolloScraperAgent = {
  id: 'apollo-scraper',
  type: 'data-collection',
  capabilities: ['apollo-scraping', 'contact-enrichment', 'lead-generation'],
  endpoints: {
    base: 'http://localhost:3000',
    health: '/api/v1/health',
    scrape: '/api/v1/integrated/scrape-and-store'
  }
}
```

## 📈 Performance & Monitoring

### Metrics Dashboard Integration
The service exposes metrics for the main dashboard:
- Active scraping jobs
- Completion rates
- Error rates
- Database connection status
- API response times

### Health Checks
- `/api/v1/health` - Overall service health
- `/api/v1/health/render` - Render DB connectivity
- `/api/v1/health/database` - Database status

## 🛠️ Development

### Running Tests
```bash
# Test all components
npm run test:all

# Test Render DB connection  
npm run test:render

# Test Apify integration
node tests/testApifyConnection.js

# Mock testing (no API calls)
node tests/testMockScraper.js
```

### Local Development
```bash
# Development mode with auto-reload
npm run dev:api

# Debug mode
DEBUG=apollo-scraper:* npm run dev:api
```

## 🔐 Security & Compliance

### API Security
- Helmet.js security headers
- CORS configuration for allowed origins
- Request validation and sanitization
- Rate limiting (configurable)

### Data Handling
- Compliant with Apollo.io terms of service
- GDPR-aware data processing
- Secure credential management
- Audit logging for all operations

## 📚 Documentation

Detailed documentation available in `/docs/`:
- [API Reference](docs/API_README.md)
- [Apollo URL Parameters](docs/APOLLO_URL_DOCUMENTATION.md) 
- [Render DB Integration](docs/RENDER_API_DOCUMENTATION.md)
- [OpenAPI Specification](api/openapi.json)

## 🤝 Contributing

This service follows the Barton Outreach Core contribution guidelines:

1. Create feature branch from `main`
2. Follow HEIR architecture patterns
3. Add comprehensive tests
4. Update documentation
5. Submit PR for review

### Branch Naming
- `feature/apollo-scraper-*` - New features
- `fix/apollo-scraper-*` - Bug fixes  
- `docs/apollo-scraper-*` - Documentation updates

## 🌐 Deployment

### Production Setup
1. Configure environment variables
2. Set up health check endpoints
3. Configure monitoring and logging
4. Deploy with container orchestration

### Environment Variables
```env
NODE_ENV=production
PORT=3000
APIFY_API_KEY=your_production_key
APIFY_ACTOR_ID=jljBwyyQakqrL1wae
RENDER_DB_URL=https://render-marketing-db.onrender.com
LOG_LEVEL=info
```

## 📞 Support

For questions or issues:
- **Email**: dbarton@svg.agency  
- **Repository**: https://github.com/djb258/barton-outreach-core
- **Branch**: `feature/apollo-scraper-api`
- **Docs**: Available in `/services/apollo-scraper/docs/`

## 📄 License

Part of the Barton Outreach Core system. See main repository for license details.