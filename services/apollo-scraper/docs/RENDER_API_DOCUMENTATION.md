# Render Marketing Database API Documentation

## Base URL
```
https://render-marketing-db.onrender.com
```

## Available Endpoints

### 1. Health & Status Endpoints

#### GET `/`
- **Description**: Root endpoint with service info
- **Response**: Service status and available endpoints list

#### GET `/api/health`
- **Description**: Health check with CORS info
- **Response**: 
```json
{
  "status": "OK",
  "timestamp": "2024-01-15T10:00:00",
  "cors": "enabled",
  "environment": "production",
  "service": "Render Database Endpoint"
}
```

#### GET `/fire`
- **Description**: Simple status check
- **Response**: `{"status": "🔥 Database endpoint is live"}`

#### GET `/api/db/status`
- **Description**: Database connection status
- **Response**: 
```json
{
  "status": "connected",
  "database": "Neon PostgreSQL",
  "service": "Render Database Endpoint"
}
```

### 2. Marketing Companies Endpoints

#### GET `/api/marketing/companies`
- **Description**: Retrieve marketing companies
- **Response**: 
```json
{
  "status": "success",
  "companies": [],
  "message": "Companies endpoint ready for database integration"
}
```

#### POST `/api/marketing/companies`
- **Description**: Create a new marketing company
- **Request Body**: 
```json
{
  "company_name": "string",
  "apollo_url": "string",
  "industry": "string",
  "location": "string"
}
```
- **Response**: 
```json
{
  "status": "success",
  "message": "Company created successfully",
  "data": {...}
}
```

### 3. Apollo Data Endpoints

#### GET `/api/apollo/raw`
- **Description**: Retrieve Apollo scraping data
- **Response**: 
```json
{
  "status": "success",
  "apollo_data": [],
  "message": "Apollo data endpoint ready for database integration"
}
```

#### POST `/api/apollo/raw`
- **Description**: Submit Apollo scraping results
- **Request Body**: 
```json
{
  "company_id": "string",
  "contacts": [],
  "scraped_at": "timestamp",
  "total_contacts": "number"
}
```
- **Response**: 
```json
{
  "status": "success",
  "message": "Apollo data submitted successfully",
  "data": {...}
}
```

### 4. Legacy Upload Endpoint

#### POST `/insert`
- **Description**: Legacy endpoint for uploading records
- **Request Body**: Variable structure
- **Response**: 
```json
{
  "status": "success",
  "message": "Records uploaded successfully",
  "data": {...}
}
```

### 5. Testing Endpoints

#### POST `/pingpong`
- **Description**: Echo test endpoint
- **Request Body**: 
```json
{
  "prompt": "string"
}
```
- **Response**: 
```json
{
  "response": "Echo: [prompt]",
  "service": "Render Database Endpoint"
}
```

#### GET `/cors-test`
- **Description**: Test CORS configuration
- **Response**: CORS test result

## CORS Configuration

The API supports the following origins:
- `https://*.lovable.dev`
- `https://lovable.dev`
- `https://*.lovableproject.com`
- `https://lovableproject.com`
- `http://localhost:3000`
- `http://localhost:5173`
- `http://localhost:8080`
- `http://localhost:8000`

## Authentication

Currently, the API doesn't appear to require authentication tokens. This may change in production.

## Rate Limiting

No rate limiting information available in the current implementation.

## Error Responses

Standard HTTP error codes:
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

## Integration Notes

1. The API is hosted on Render.com
2. Uses FastAPI (Python) framework
3. Database backend is Neon PostgreSQL
4. CORS is enabled for specific origins
5. All responses are JSON formatted