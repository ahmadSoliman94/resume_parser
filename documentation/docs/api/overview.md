# API Overview

The Resume Parser AI API provides a comprehensive set of endpoints for processing and extracting data from resume documents. This page gives you a high-level overview of the API structure, authentication, and general usage patterns.

## API Structure

The API is organized into four functional categories:

1. **📤 Upload & Storage Management**
   - Endpoints for uploading resume files and managing storage
   - Examples: 
     - `/api/resumes/upload` - Upload a resume
     - `/api/resumes/upload-and-process` - Upload and process in one step

2. **🔍 OCR Processing**
   - Endpoints for processing resumes and extracting data
   - Example: `/api/resumes/process`

3. **📊 Results & Reporting**
   - Endpoints for retrieving processing results
   - Example: `/api/resumes/results/{file_id}`

4. **🧹 System Maintenance**
   - Endpoints for system cleanup and maintenance
   - Example: `/api/resumes/cleanup`

## Base URL

All API endpoints are relative to the base URL of your deployment:

```
http://localhost:8000/api
```

In production environments, you would replace `localhost` with your server domain.

## Authentication

The API currently uses a simple approach to authentication:

- No authentication is required for local development
- For production, you should implement appropriate authentication using a reverse proxy or API gateway
- CORS (Cross-Origin Resource Sharing) is enabled for all origins by default

## Request & Response Format

### Request Format

- **GET** requests pass parameters as query strings
- **POST** requests accept both query parameters and JSON bodies
- File uploads use `multipart/form-data` encoding

### Response Format

All API responses follow a consistent JSON structure:

```json
{
  "status": "success",  // or "error"
  "message": "Operation completed successfully",
  "data": {
    // Operation-specific data
  },
  "execution_time": 1.25  // Processing time in seconds (optional)
}
```

Error responses include appropriate HTTP status codes and details:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Common Parameters

These parameters are used across multiple endpoints:

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | Identifier for a processed resume file |
| `annotate` | boolean | Whether to create visual annotations |
| `generate_summary` | boolean | Whether to create a professional summary |

## Rate Limiting

The API does not implement rate limiting by default, but in production, you should consider:

- Adding rate limiting based on client IP or API key
- Setting appropriate timeouts for long-running operations

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include descriptive messages to help diagnose issues.

## Data Storage

The API stores data in several directories:

- **Uploads**: Original resume files
- **Extraction Results**: JSON files with extracted data
- **Annotations**: Annotated resume images
- **Logs**: Processing logs and metrics

Use the cleanup endpoint to clear these directories when needed.

## Technical Limitations

Be aware of these technical considerations:

- **File Size**: Large files (>10MB) may require additional processing time
- **GPU Memory**: Processing is GPU accelerated where available
- **Processing Time**: Complex or multi-page resumes take longer to process
- **Concurrent Requests**: The system is optimized for moderate concurrency

## Next Steps

Explore the detailed documentation for each endpoint:

- [Endpoints Documentation](endpoints.md): Complete details on all available endpoints
- [Models Documentation](models.md): Information on data models and schemas