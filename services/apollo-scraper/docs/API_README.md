# Apollo Scraper API

A comprehensive API for scraping Apollo.io contact data and storing it in your Render marketing database.

## 🚀 Quick Start

### 1. Environment Setup
Create a `.env` file with your credentials:
```bash
# Apify Configuration (WORKING!)
APIFY_API_KEY=apify_api_63CEvQr4uy247iyULJibGB1JSOHYtd2RVDqH
APIFY_ACTOR_ID=jljBwyyQakqrL1wae

# Port Configuration
PORT=3000

# Run Mode
DRY_RUN=false
```

### 2. Start the API Server
```bash
# Production mode
npm run start:api

# Development mode (with auto-reload)
npm run dev:api
```

### 3. Test the API
Visit http://localhost:3000 to see available endpoints.

## 📊 Available Endpoints

### Integrated Endpoints (Recommended)
These endpoints combine scraping with database storage:

#### Start Scraping & Store Results
```bash
POST /api/v1/integrated/scrape-and-store
```

**Example Request:**
```json
{
  "companyName": "German Tech Corp",
  "apolloUrl": "https://app.apollo.io/#/people?personLocations[]=Germany&organizationNumEmployeesRanges[]=5000%2C5200",
  "maxResults": 1000,
  "filterByTitle": true,
  "industry": "Technology",
  "location": "Germany"
}
```

**Example Response:**
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

#### Batch Scraping
```bash
POST /api/v1/integrated/batch-scrape
```

**Example Request:**
```json
{
  "companies": [
    {
      "name": "Tech Corp 1",
      "url": "https://app.apollo.io/...",
      "industry": "Technology",
      "location": "Germany"
    },
    {
      "name": "Tech Corp 2", 
      "url": "https://app.apollo.io/...",
      "industry": "Software",
      "location": "Berlin"
    }
  ]
}
```

#### Check Company Status
```bash
GET /api/v1/integrated/company-status/{companyName}
```

### Individual Service Endpoints

#### Scraper Operations
- `POST /api/v1/scraper/start` - Start a scraping job
- `GET /api/v1/scraper/status/{jobId}` - Check job status
- `GET /api/v1/scraper/results/{jobId}` - Get results
- `POST /api/v1/scraper/batch` - Batch scraping
- `GET /api/v1/scraper/jobs` - List all jobs

#### Marketing Database Operations
- `GET /api/v1/companies` - List companies
- `POST /api/v1/companies` - Create company
- `GET /api/v1/results/apollo` - Get Apollo data
- `POST /api/v1/results/apollo` - Submit Apollo data

#### Health & Status
- `GET /api/v1/health` - Overall health check
- `GET /api/v1/health/render` - Render DB health
- `GET /api/v1/health/database` - Database status
- `GET /api/v1/integrated/test-connection` - Test Render connection

## 🔧 Configuration

### Render Marketing Database
The API connects to your Render-hosted marketing database at:
```
https://render-marketing-db.onrender.com
```

Supported endpoints:
- `/api/marketing/companies` - Company management
- `/api/apollo/raw` - Apollo data storage
- `/api/health` - Health checks

### Apify Integration
Uses the Apollo scraper actor: `apollo-io-scraper` (ID: `jljBwyyQakqrL1wae`)

Configuration options:
- `maxResults`: Number of contacts to scrape (default: 1000)
- `cleanOutput`: Data cleaning (default: false)
- `filterByTitle`: Filter for executive titles (default: true)

## 📚 API Documentation

### OpenAPI Specification
View the complete API documentation at:
```
http://localhost:3000/api/v1/docs
```

### Example Usage with cURL

#### Start a scraping job:
```bash
curl -X POST http://localhost:3000/api/v1/integrated/scrape-and-store \
  -H "Content-Type: application/json" \
  -d '{
    "companyName": "Example Corp",
    "apolloUrl": "https://app.apollo.io/#/people?personLocations[]=Germany",
    "maxResults": 500
  }'
```

#### Check health:
```bash
curl http://localhost:3000/api/v1/health
```

## 🔍 Monitoring & Logging

The API provides comprehensive logging:
- Request/response logging via Morgan
- Apify operation tracking
- Database operation status
- Error handling and reporting

Log levels:
- `[Integrated]` - Combined operations
- `[RenderDB]` - Database operations  
- `[Apify]` - Scraping operations

## 🚨 Error Handling

Standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "error": {
    "message": "Error description",
    "status": 400,
    "timestamp": "2024-01-15T10:00:00.000Z"
  }
}
```

## 🔐 Security Features

- Helmet.js for security headers
- CORS configuration
- Request validation
- Error sanitization
- Timeout handling

## 📈 Performance

- Request compression with gzip
- Connection pooling
- Async processing for long-running jobs
- Pagination support for large datasets

## 🧪 Testing

Run connection tests:
```bash
# Test Render DB connection
npm run test:render

# Test Apify API
node testApifyConnection.js

# Test complete pipeline
node testMockScraper.js
```

## 📝 Integration with Barton Outreach Core

This scraping tool should be integrated as a branch of the main outreach repository:
```bash
git remote add upstream https://github.com/djb258/barton-outreach-core.git
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## 📞 Support

For issues or questions:
- Email: dbarton@svg.agency
- Repository: https://github.com/djb258/barton-outreach-core.git