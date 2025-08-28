# Node 1: Company + DB (PLE + Enrich)

## Scope
This node handles the foundation layer of the outreach system:
- Company data ingestion and storage
- People, Lead, and Entity (PLE) management
- Data enrichment pipeline
- Database schema and operations

## Acceptance Checklist

### Schema
- [ ] Company table with normalized fields
- [ ] People table with contact information
- [ ] Lead tracking and scoring tables
- [ ] Entity relationships defined
- [ ] Indexes for performance optimization

### Ingestor
- [ ] CSV file parser with delimiter detection
- [ ] Excel file support (.xlsx, .xls)
- [ ] Google Sheets integration
- [ ] Apollo.io sync capability
- [ ] Web form intake endpoint
- [ ] Batch processing with error handling
- [ ] Duplicate detection and merging logic

### PLE (People, Lead, Entity)
- [ ] Person profile management
- [ ] Lead scoring algorithm
- [ ] Entity classification system
- [ ] Relationship mapping between entities
- [ ] BIT tag assignment logic
- [ ] Lead prioritization engine

### Enrich
- [ ] Email validation service integration
- [ ] Phone number normalization (E.164)
- [ ] Domain apex extraction
- [ ] EIN validation and formatting
- [ ] Company data enrichment (industry, size, revenue)
- [ ] Social profile discovery (LinkedIn, X)
- [ ] Data quality scoring

## Folder Structure
```
node-1-company-db/
├── schema/          # Database schemas and migrations
├── ingestor/        # Data intake and parsing
├── ple/             # People, Lead, Entity management
└── enrich/          # Data enrichment services
```

## Dependencies
- PostgreSQL for data storage
- libphonenumber-js for phone validation
- psl for domain validation
- papaparse for CSV handling
- xlsx for Excel file processing

## API Contracts
- POST /api/intake/companies
- POST /api/intake/people
- GET /api/ple/leads
- POST /api/enrich/validate