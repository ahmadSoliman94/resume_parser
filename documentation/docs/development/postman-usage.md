# Postman Usage

This guide provides detailed instructions for using Postman to interact with the Resume Parser AI API. Each endpoint is explained with parameters, example requests, and sample responses.

## Contents

- [Setting Up Postman](#setting-up-postman)
- [Configuring Environments](#configuring-environments)
- [API Endpoints](#api-endpoints)
  - [Upload Endpoint](#upload-endpoint)
  - [Upload and Process Endpoint](#upload-and-process-endpoint)
  - [Process Endpoint](#process-endpoint)
  - [Results Endpoint](#results-endpoint)
  - [Cleanup Endpoint](#cleanup-endpoint)
- [Workflow Examples](#workflow-examples)
- [Troubleshooting](#troubleshooting)

## Setting Up Postman

1. **Install Postman**
   - Download and install Postman from [the official website](https://www.postman.com/downloads/)
   - Create a free account or use Postman without signing in

2. **Create a Collection**
   - Click the "+" next to Collections to create a new collection
   - Name it "Resume Parser AI API"
   - Add a description (optional)
   - Click "Create"

## Configuring Environments

Set up an environment to easily switch between different server configurations:

1. Click on "Environments" in the sidebar
2. Click "+" to create a new environment
3. Name it (e.g., "Local Development")
4. Add the following variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| base_url | http://127.0.0.1:8000/api | http://127.0.0.1:8000/api |

5. Click "Save"
6. Select the environment from the dropdown in the top right

## API Endpoints

### Upload Endpoint

Uploads a resume file (PDF or PNG) to the system for processing.

#### Endpoint Details

- **URL**: `{{base_url}}/resumes/upload`
- **Method**: POST
- **Content-Type**: multipart/form-data

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | The resume file to upload (PDF or PNG) |

#### Example Request

1. Create a new request in your collection
2. Set the request type to POST
3. Enter the URL: `{{base_url}}/resumes/upload`
4. In the "Body" tab, select "form-data"
5. Add a key named "file" and select "File" from the dropdown
6. Click "Select File" and choose your resume file
7. Click "Send"

#### Example Response

```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "file_id": "john_doe_resume"
}
```

### Upload and Process Endpoint

Uploads and processes a resume file in a single step.

#### Endpoint Details

- **URL**: `{{base_url}}/resumes/upload-and-process`
- **Method**: POST
- **Content-Type**: multipart/form-data

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | The resume file to upload and process (PDF or PNG) |
| annotate | boolean | No | Create visual annotations (default: true) |
| generate_summary | boolean | No | Generate a professional summary (default: true) |

#### Example Request

1. Create a new request in your collection
2. Set the request type to POST
3. Enter the URL: `{{base_url}}/resumes/upload-and-process`
4. In the "Body" tab, select "form-data"
5. Add a key named "file" and select "File" from the dropdown
6. Click "Select File" and choose your resume file
7. Add a key named "annotate" with the value "true" (optional)
8. Add a key named "generate_summary" with the value "true" (optional)
9. Click "Send"

#### Example Response (Single-Page Resume)

```json
{
  "file_id": "john_doe_resume",
  "processing_time_sec": 8.45,
  "created_at": "2025-04-24T15:30:22Z",
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
        {
          "text": "john.doe@example.com",
          "label_name": "Email"
        },
        {
          "text": "+1 (555) 123-4567",
          "label_name": "Phone"
        },
        {
          "text": "San Francisco, CA",
          "label_name": "Location"
        },
        {
          "text": "Software Engineer",
          "label_name": "JobTitle"
        },
        {
          "text": "Bachelor of Science in Computer Science",
          "label_name": "Education_1_Degree"
        },
        {
          "text": "Stanford University",
          "label_name": "Education_1_Institution"
        },
        {
          "text": "2018",
          "label_name": "Education_1_GradDate"
        },
        {
          "text": "Python",
          "label_name": "TechnicalSkill_1"
        },
        {
          "text": "JavaScript",
          "label_name": "TechnicalSkill_2"
        },
        {
          "text": "English (Native)",
          "label_name": "Language_1"
        }
      ],
      "page_num": 1
    }
  ],
  "image_urls": [
    "http://127.0.0.1:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
  ],
  "message": "Resume processed successfully",
  "summary_generated": true
}
```

### Process Endpoint

Processes an already uploaded resume file.

#### Endpoint Details

- **URL**: `{{base_url}}/resumes/process`
- **Method**: POST

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the resume file to process |
| annotate | boolean | No | Create visual annotations (default: true) |
| generate_summary | boolean | No | Generate a professional summary (default: true) |

#### Example Request

1. Create a new request in your collection
2. Set the request type to POST
3. Enter the URL: `{{base_url}}/resumes/process`
4. In the "Params" tab, add:
   - Key: `file_id`, Value: `john_doe_resume`
   - Key: `annotate`, Value: `true`
   - Key: `generate_summary`, Value: `true`
5. Click "Send"

#### Example Response (Single-Page Resume)

```json
{
  "file_id": "john_doe_resume",
  "processing_time_sec": 8.45,
  "created_at": "2025-04-24T15:30:22Z",
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
        {
          "text": "john.doe@example.com",
          "label_name": "Email"
        },
        {
          "text": "+1 (555) 123-4567",
          "label_name": "Phone"
        },
        {
          "text": "San Francisco, CA",
          "label_name": "Location"
        },
        {
          "text": "Software Engineer",
          "label_name": "JobTitle"
        }
      ],
      "page_num": 1
    }
  ],
  "image_urls": [
    "http://127.0.0.1:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
  ],
  "message": "Resume processed successfully",
  "summary_generated": true
}
```

#### Example Request (Multi-Page Resume)

1. Create a new request in your collection
2. Set the request type to POST
3. Enter the URL: `{{base_url}}/resumes/process`
4. In the "Params" tab, add:
   - Key: `file_id`, Value: `multi_page_resume`
   - Key: `annotate`, Value: `true`
   - Key: `generate_summary`, Value: `true`
5. Click "Send"

#### Example Response (Multi-Page Resume)

```json
{
  "file_id": "multi_page_resume",
  "processing_time_sec": 31.93,
  "created_at": "2025-04-24T19:14:41Z",
  "pages": [
    {
      "image_id": "multi_page_resume_page1",
      "image_width_px": 595,
      "image_height_px": 841,
      "data": [
        {
          "text": "John Doe",
          "label_name": "Name"
        },
        {
          "text": "john.doe@example.com",
          "label_name": "Email"
        },
        {
          "text": "+1 (555) 123-4567",
          "label_name": "Phone"
        },
        {
          "text": "San Francisco, CA",
          "label_name": "Location"
        }
      ],
      "page_num": 1
    },
    {
      "image_id": "multi_page_resume_page2",
      "image_width_px": 595,
      "image_height_px": 841,
      "data": [
        {
          "text": "Software Engineer",
          "label_name": "JobTitle"
        },
        {
          "text": "Tech Solutions Inc.",
          "label_name": "Work_1_Company"
        },
        {
          "text": "2019-Present",
          "label_name": "Work_1_Duration"
        }
      ],
      "page_num": 2
    }
  ],
  "image_urls": [
    "http://127.0.0.1:8000/api/static/annotations/multi_page_resume/multi_page_resume_page1.png",
    "http://127.0.0.1:8000/api/static/annotations/multi_page_resume/multi_page_resume_page2.png"
  ],
  "message": "Resume processed successfully",
  "summary_generated": true
}
```

### Results Endpoint

Retrieves the results of a processed resume.

#### Endpoint Details

- **URL**: `{{base_url}}/resumes/results/{file_id}`
- **Method**: GET

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | string | Yes | ID of the processed resume file (path parameter) |

#### Example Request

1. Create a new request in your collection
2. Set the request type to GET
3. Enter the URL: `{{base_url}}/resumes/results/john_doe_resume`
4. Click "Send"

#### Example Response

```json
{
  "status": "success",
  "message": "Results retrieved successfully",
  "data": {
    "file_id": "john_doe_resume",
    "extraction_data": {
      "file_id": "john_doe_resume",
      "processing_time_sec": 8.45,
      "created_at": "2025-04-24T15:30:22Z",
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
            {
              "text": "john.doe@example.com",
              "label_name": "Email"
            }
          ],
          "page_num": 1
        }
      ],
      "image_urls": [
        "http://127.0.0.1:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
      ]
    },
    "annotation_files": [
      "/path/to/annotations/john_doe_resume/john_doe_resume_page1.png"
    ]
  }
}
```

### Cleanup Endpoint

Clean up storage directories to free up disk space.

#### Endpoint Details

- **URL**: `{{base_url}}/resumes/cleanup`
- **Method**: POST

#### Parameters

None

#### Example Request

1. Create a new request in your collection
2. Set the request type to POST
3. Enter the URL: `{{base_url}}/resumes/cleanup`
4. Click "Send"

#### Example Response

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
  "execution_time": 0.01
}
```

## Workflow Examples

### Complete Processing Workflow - Combined Method (Recommended)

Here's a step-by-step guide for the simplest resume processing workflow:

#### 1. Upload and Process in One Step

1. Send a POST request to `http://127.0.0.1:8000/api/resumes/upload-and-process` with a PDF or PNG file
2. Wait for processing to complete (this may take 5-30 seconds depending on the resume complexity)
3. Review the response for extracted fields and annotation URLs

#### 2. (Optional) View the Results

1. Send a GET request to `http://127.0.0.1:8000/api/resumes/results/{file_id}` using the file_id from the previous response
2. Review the detailed extraction results
3. (Optional) Open the annotation URLs in a browser to see the visual field highlighting

#### 3. (Optional) Clean Up

1. When you're done with processing or need to free up space, send a POST request to `http://127.0.0.1:8000/api/resumes/cleanup`
2. This will remove all processed files and clear storage

### Complete Processing Workflow - Step-by-Step Method

If you prefer more control over the process:

#### 1. Upload a Resume

1. Send a POST request to `http://127.0.0.1:8000/api/resumes/upload` with a PDF or PNG file
2. Note the `file_id` from the response (e.g., "john_doe_resume")

#### 2. Process the Resume

1. Send a POST request to `http://127.0.0.1:8000/api/resumes/process?file_id=john_doe_resume`
2. Wait for processing to complete (this may take 5-30 seconds depending on the resume complexity)
3. Review the response for extracted fields and annotation URLs

#### 3. View the Results

1. Send a GET request to `http://127.0.0.1:8000/api/resumes/results/john_doe_resume`
2. Review the detailed extraction results
3. (Optional) Open the annotation URLs in a browser to see the visual field highlighting

#### 4. (Optional) Clean Up

1. When you're done with processing or need to free up space, send a POST request to `http://127.0.0.1:8000/api/resumes/cleanup`
2. This will remove all processed files and clear storage

## Processing Multiple Resumes

To process multiple resumes, you can create a Postman Collection Runner:

1. In your collection, click the "..." button and select "Run collection"
2. Add multiple requests for the `upload-and-process` endpoint
3. Set up variables for each resume file
4. Run the collection

Alternatively, you can use the Python script provided in the documentation to process multiple files in a folder.

## Troubleshooting

### Common Issues and Solutions

#### Connection Refused

**Issue**: Unable to connect to the API server (connection refused)

**Solution**: 
- Verify the API server is running
- Check that the port (8000) is correct in your environment variables
- Ensure there are no firewalls blocking the connection

#### File Upload Issues

**Issue**: Error when uploading files

**Solution**:
- Ensure the file format is supported (PDF or PNG)
- Check that the file size is reasonable (under 10MB recommended)
- Verify you're using the correct content type (multipart/form-data)

#### Processing Timeouts

**Issue**: Request times out during processing

**Solution**:
- Increase Postman's request timeout in settings
- For large or complex resumes, use the separate upload and process endpoints to avoid timeouts
- Check server logs for processing errors

#### Invalid File ID

**Issue**: "File not found" error when processing or retrieving results

**Solution**:
- Verify the file ID matches exactly what was returned from the upload endpoint
- Check that the file hasn't been removed by a cleanup operation
- Ensure there are no typos in the file ID

#### GPU Memory Issues

**Issue**: Processing fails with GPU memory errors

**Solution**:
- Check if the server has properly configured GPU support
- Try disabling GPU processing by setting USE_GPU=False in the server environment
- Reduce batch size in the server configuration