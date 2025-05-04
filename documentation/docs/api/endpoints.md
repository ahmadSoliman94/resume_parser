# API Endpoints

This page provides detailed information about all available API endpoints in the Resume Parser AI system.

## Endpoint Categories

The API is organized into four categories:

- **📤 Upload & Storage Management**: Endpoints for uploading and managing resume files
- **🔍 OCR Processing**: Endpoints for OCR processing and data extraction
- **📊 Results & Reporting**: Endpoints for retrieving processing results
- **🧹 System Maintenance**: Endpoints for system cleanup and maintenance

## Upload & Storage Management

### Upload Resume

Upload a resume file for processing. Supports PDF and PNG files.

**Endpoint:** `POST /api/resumes/upload`

**Request Format:**

Form data with a file parameter named `file`.

**Response Format:**

```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "file_id": "john_doe_resume"
}
```

**Example Usage:**

```bash
# Upload a file
curl -X POST -F "file=@resume.pdf" http://localhost:8000/api/resumes/upload
```

### Upload and Process Resume

Upload and process a resume file in a single request. Supports PDF and PNG files.

**Endpoint:** `POST /api/resumes/upload-and-process`

**Request Format:**

Form data with:
- `file`: The resume file (PDF or PNG)
- `annotate`: Boolean indicating whether to create visual annotations (optional, default: true)
- `generate_summary`: Boolean indicating whether to generate a professional summary (optional, default: true)

**Response Format:**

```json
{
  "file_id": "john_doe_resume",
  "processing_time_sec": 5.43,
  "created_at": "2025-04-23T10:15:30Z",
  "pages": [
    {
      "image_id": "john_doe_resume_page1",
      "image_width_px": 595,
      "image_height_px": 842,
      "data": [
        {
          "text": "John Doe",
          "label_name": "Name"
        },
        // Additional extracted fields...
      ],
      "page_num": 1
    }
  ],
  "image_urls": [
    "http://localhost:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
  ],
  "message": "Resume processed successfully",
  "summary_generated": true
}
```

**Example Usage:**

```bash
# Upload and process in one step
curl -X POST -F "file=@resume.pdf" -F "annotate=true" -F "generate_summary=true" http://localhost:8000/api/resumes/upload-and-process
```

## OCR Processing

### Process Resume

Process an uploaded resume for data extraction.

**Endpoint:** `POST /api/resumes/process`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the resume file to process |
| annotate | boolean | No | Create visual annotations (default: true) |
| generate_summary | boolean | No | Generate a professional summary (default: true) |

**Response Format:**

```json
{
  "file_id": "john_doe_resume",
  "processing_time_sec": 5.43,
  "created_at": "2025-04-23T10:15:30Z",
  "pages": [
    {
      "image_id": "john_doe_resume_page1",
      "image_width_px": 595,
      "image_height_px": 842,
      "data": [
        {
          "text": "John Doe",
          "label_name": "Name"
        },
        // Additional extracted fields...
      ],
      "page_num": 1
    }
  ],
  "image_urls": [
    "http://localhost:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
  ],
  "message": "Resume processed successfully",
  "summary_generated": true
}
```

**Example Usage:**

```bash
# Process a file
curl -X POST "http://localhost:8000/api/resumes/process?file_id=john_doe_resume&annotate=true&generate_summary=true"
```

## Results & Reporting

### Get Processing Results

Retrieve the results of resume processing.

**Endpoint:** `GET /api/resumes/results/{file_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the processed resume file |

**Response Format:**

```json
{
  "status": "success",
  "message": "Results retrieved successfully",
  "data": {
    "file_id": "john_doe_resume",
    "extraction_data": {
      "file_id": "john_doe_resume",
      "processing_time_sec": 5.43,
      "created_at": "2025-04-23T10:15:30Z",
      "pages": [
        // Page data...
      ],
      "image_urls": [
        // Annotation URLs...
      ]
    },
    "annotation_files": [
      "/path/to/annotations/john_doe_resume/john_doe_resume_page1.png"
    ]
  }
}
```

**Example Usage:**

```bash
curl -X GET "http://localhost:8000/api/resumes/results/john_doe_resume"
```

## System Maintenance

### Cleanup Storage

Clean up storage directories to free up disk space.

**Endpoint:** `POST /api/resumes/cleanup`

**Response Format:**

```json
{
  "status": "success",
  "message": "Storage directories cleaned and recreated successfully",
  "data": {
    "directories_cleaned": [
      "uploads",
      "extraction_results",
      "annotations",
      "logs"
    ],
    "directories_created": [
      "uploads",
      "extraction_results",
      "annotations",
      "logs"
    ],
    "errors": []
  },
  "execution_time": 0.25
}
```

**Example Usage:**

```bash
curl -X POST "http://localhost:8000/api/resumes/cleanup"
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Successful operation
- `400`: Bad request or invalid parameters
- `404`: Resource not found
- `500`: Internal server error

Error responses include detailed error messages:

```json
{
  "detail": "File not found for ID: john_doe_resume"
}
```

## Cross-Origin Resource Sharing (CORS)

All API endpoints support CORS with the following configuration:

- Allow all origins (`*`)
- Allow credentials
- Allow all methods
- Allow all headers

This configuration can be adjusted in `main.py` if needed.