# CSV Data Ingestor Service

A HEIR-compliant microservice for intelligent CSV/Excel data ingestion and processing within the Barton Outreach Core system.

## 🏗️ HEIR Architecture Compliance

This service exemplifies all four HEIR principles:

### **H - Hierarchical**
- Operates as a specialized data processing agent within the Barton ecosystem
- Communicates through the orchestration layer, not peer-to-peer
- Integrates seamlessly with Apollo Scraper service

### **E - Event-driven** 
- All operations are asynchronous with status events
- Publishes data ingestion events to the system event bus
- Responds to system-wide configuration and shutdown events

### **I - Intelligent**
- Smart file type detection and parsing
- Automatic field mapping and data type inference
- Quality assessment and validation algorithms
- Apollo URL generation based on company data

### **R - Resilient**
- Comprehensive error handling with graceful degradation
- Circuit breaker patterns for external service calls
- File size limits and validation to prevent system overload
- Health monitoring with self-diagnosis capabilities

## 🎯 Core Capabilities

### Data Processing
- **Multi-format Support**: CSV, Excel (.xlsx/.xls), JSON
- **Intelligent Parsing**: Automatic field detection and mapping
- **Quality Assessment**: Comprehensive data validation and scoring
- **Batch Processing**: Handle multiple files with resilient error handling

### Integration Features
- **Apollo Sync**: Automatic triggering of Apollo scraper for new companies
- **Render DB**: Direct ingestion to marketing database
- **Real-time Status**: Live processing status and health monitoring

### HEIR Service Features
- **Event Publishing**: All major operations publish events for orchestration
- **Health Endpoints**: Comprehensive health checks for monitoring
- **Smart Recovery**: Automatic retry and fallback mechanisms

## 🚀 Quick Start

### Installation
```bash
cd services/csv-data-ingestor
npm install
```

### Environment Configuration
```env
PORT=3001
APOLLO_SCRAPER_URL=http://localhost:3000
RENDER_DB_URL=https://render-marketing-db.onrender.com
LOG_LEVEL=info
```

### Start the Service
```bash
# Production mode
npm run start:api

# Development mode
npm run dev:api
```

## 📊 API Endpoints

### Core Ingestion
- `POST /api/v1/ingest/parse` - Parse file with intelligence
- `POST /api/v1/ingest/upload-and-process` - Complete workflow
- `POST /api/v1/ingest/batch` - Process multiple files
- `GET /api/v1/ingest/supported-formats` - Get format info

### Apollo Integration
- `POST /api/v1/apollo-sync/trigger-scrape` - Trigger Apollo scrapes
- `GET /api/v1/apollo-sync/status` - Check scrape status
- `POST /api/v1/apollo-sync/auto-sync` - Automatic sync workflow
- `POST /api/v1/apollo-sync/generate-urls` - Generate Apollo URLs

### Service Management
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/detailed` - Detailed diagnostics
- `GET /api/v1/process/status` - Processing statistics

## 💡 Intelligent Features

### Smart Field Mapping
Automatically maps common field variations:
```
'Company Name' → 'company_name'
'Email Address' → 'email'
'First Name' → 'first_name'
'Job Title' → 'title'
```

### Data Type Detection
Automatically determines if data contains:
- **Companies**: Based on fields like company_name, domain, industry
- **People**: Based on fields like first_name, email, title
- **Mixed**: Contains both company and people data

### Quality Scoring
Evaluates data quality based on:
- Field completeness (% of filled fields)
- Data consistency across records
- Critical field presence
- Format validation (emails, URLs, etc.)

## 🔄 Apollo Scraper Integration

### Automatic Triggering
When companies are ingested, the service can automatically:
1. Generate Apollo search URLs based on company data
2. Trigger Apollo scraper jobs via API calls
3. Monitor scraping progress and results
4. Coordinate data flow between services

### Smart URL Generation
Creates Apollo URLs using:
- Company name for organization filter
- Location for geographic targeting
- Employee count for company size ranges
- Industry for sector-specific searches

## 📈 Usage Examples

### Parse a CSV File
```bash
curl -X POST http://localhost:3001/api/v1/ingest/parse \
  -H "Content-Type: multipart/form-data" \
  -F "file=@companies.csv"
```

### Complete Workflow (Parse + Ingest)
```bash
curl -X POST http://localhost:3001/api/v1/ingest/upload-and-process \
  -H "Content-Type: multipart/form-data" \
  -F "file=@companies.csv" \
  -F "targetTable=company.marketing_company"
```

### Trigger Apollo Scrapes
```bash
curl -X POST http://localhost:3001/api/v1/apollo-sync/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "companies": [
      {
        "company_name": "Tech Corp",
        "location": "Germany",
        "industry": "Technology"
      }
    ]
  }'
```

### Auto-sync Recent Ingestions
```bash
curl -X POST http://localhost:3001/api/v1/apollo-sync/auto-sync \
  -H "Content-Type: application/json" \
  -d '{
    "timeRange": "2h",
    "maxCompanies": 5
  }'
```

## 🔧 Configuration

### File Upload Limits
- Maximum file size: 50MB
- Maximum files per batch: 10
- Supported formats: CSV, Excel, JSON

### Processing Limits
- Maximum records per file: 100,000
- Quality score threshold: 60/100
- Concurrent processing: 3 files

### Integration Settings
- Apollo scraper timeout: 10 seconds
- Render DB timeout: 30 seconds
- Health check interval: 30 seconds

## 🧪 Testing

```bash
# Test all components
npm run test:all

# Test parsers specifically  
npm run test:parsers

# Test Apollo integration
npm run test:apollo-sync

# Test with real integration
npm run test:integration
```

## 🔍 Monitoring & Observability

### Health Checks
- Service health: `/api/v1/health`
- Detailed diagnostics: `/api/v1/health/detailed`
- Processing statistics: `/api/v1/process/status`

### Event Publishing
The service publishes HEIR-compliant events:
- `data.parsing.completed`
- `data.ingestion.completed`
- `apollo.scrape.triggered`
- `service.error`

### Metrics
- Files processed per hour/day
- Average quality scores
- Success/failure rates
- Integration response times

## 🔒 Security Features

- File type validation and sanitization
- Size limits to prevent DoS attacks
- Input validation and SQL injection prevention
- CORS configuration for web integration
- Error message sanitization

## 🌐 Deployment

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

### Environment Variables
```env
NODE_ENV=production
PORT=3001
APOLLO_SCRAPER_URL=https://apollo-scraper.yourdomain.com
RENDER_DB_URL=https://render-marketing-db.onrender.com
LOG_LEVEL=info
MAX_FILE_SIZE=52428800
MAX_FILES=10
```

## 📞 Integration with Barton Core

This service integrates with the main Barton Outreach Core system through:

1. **HEIR Agent Registry**: Registers as a data processing agent
2. **Event Bus**: Publishes and subscribes to system events  
3. **Orchestration Layer**: Receives tasks from the orchestration engine
4. **Health Monitoring**: Reports status to central monitoring

## 📄 License

Part of the Barton Outreach Core system. See main repository for license details.

## 📞 Support

- **Repository**: https://github.com/djb258/barton-outreach-core
- **Branch**: `feature/csv-data-ingestor`
- **Email**: dbarton@svg.agency