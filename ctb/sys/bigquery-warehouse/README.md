# BigQuery Data Warehouse

**Doctrine ID**: 04.04.04
**Altitude**: 40k ft (System Infrastructure)

## Purpose

BigQuery Data Warehouse provides analytics and historical data storage using Google BigQuery. It implements the STACKED (Structured Table Architecture for Calculated Knowledge & Event Data) schema for comprehensive data warehousing.

## Features

- Centralized analytics data warehouse
- STACKED schema implementation
- Historical data retention and analysis
- Real-time data pipeline integration
- Advanced query optimization
- Data mart creation for business intelligence

## Architecture

### STACKED Schema

The STACKED schema organizes data into layers:

1. **S**taged - Raw data ingestion layer
2. **T**ransformed - Cleaned and normalized data
3. **A**ggregated - Pre-calculated metrics
4. **C**onsolidated - Business-ready datasets
5. **K**nowledge - Derived insights and models
6. **E**xport - Formatted for external systems
7. **D**ata Marts - Domain-specific views

## Setup

### Prerequisites

- Google Cloud Project with BigQuery enabled
- Service account with BigQuery permissions
- MCP vault configuration for credentials

### Configuration

Set up in MCP vault:

```bash
# Via Composio MCP
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET=barton_warehouse
BIGQUERY_LOCATION=US
```

### Schema Deployment

```bash
# Deploy STACKED schema
npm run bigquery:deploy-schema

# Create data marts
npm run bigquery:create-marts
```

## Directory Structure

```
bigquery-warehouse/
├── schemas/          # Table schemas (JSON)
├── queries/          # Saved queries and views
├── dashboards/       # Dashboard configurations
├── migrations/       # Schema migration scripts
└── exports/          # Export configurations
```

## Integration

### Data Pipeline

Data flows from operational systems into BigQuery:

1. **Firestore** → BigQuery (via scheduled queries)
2. **Neon PostgreSQL** → BigQuery (daily sync)
3. **API Events** → BigQuery (streaming)
4. **External Sources** → BigQuery (ETL)

### Query Examples

```sql
-- Example: Get client outreach metrics
SELECT
  client_id,
  COUNT(DISTINCT contact_id) as total_contacts,
  COUNT(outreach_id) as total_outreach,
  AVG(response_rate) as avg_response_rate
FROM `barton_warehouse.outreach_facts`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY client_id;
```

## Usage

### Running Queries

```bash
# Via CLI
bq query --use_legacy_sql=false < queries/monthly_report.sql

# Via Node.js
npm run bigquery:query -- queries/monthly_report.sql
```

### Creating Dashboards

Connect to BigQuery from:
- **Grafana** - Real-time monitoring dashboards
- **Looker** - Business intelligence reports
- **Data Studio** - Custom visualizations
- **Tableau** - Advanced analytics

## Data Marts

Pre-built data marts for common use cases:

- `client_analytics` - Client-level metrics
- `outreach_performance` - Campaign effectiveness
- `compliance_tracking` - Regulatory compliance
- `financial_reporting` - Revenue and billing

## Scheduled Jobs

Automated data processing:

- **Hourly**: Event data ingestion
- **Daily**: Aggregation calculations
- **Weekly**: Data mart refresh
- **Monthly**: Historical archival

## Status

**Status**: Configured (awaiting setup)
**Dataset**: Not yet created
**Tables**: 0
**Size**: N/A

---

For more information, see [CTB_DOCTRINE.md](../../meta/global-config/CTB_DOCTRINE.md)
