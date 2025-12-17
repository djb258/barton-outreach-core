# API Documentation

This directory contains API documentation for all system endpoints.

## Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token

### User Management
- `GET /api/users/:id` - Get user profile
- `PUT /api/users/:id` - Update user profile
- `DELETE /api/users/:id` - Delete user account

### Data Operations
- Document CRUD operations here
- Query endpoints
- Batch operations

## API Standards

- **Format**: RESTful JSON
- **Authentication**: JWT Bearer tokens
- **Rate Limiting**: 60 requests/minute
- **Versioning**: URI versioning (e.g., `/api/v1/...`)

## Response Format

```json
{
  "success": true,
  "data": {},
  "error": null,
  "metadata": {
    "timestamp": "2025-10-23T00:00:00Z",
    "version": "1.0.0"
  }
}
```

## Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

## OpenAPI Specification

OpenAPI/Swagger specifications will be generated automatically and placed in this directory.
