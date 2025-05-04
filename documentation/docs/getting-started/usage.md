# Usage Guide

This guide will walk you through the basic steps of using the Resume Parser AI API, from uploading a resume to retrieving the processed results.

## Basic Workflow

There are two ways to use the API:

1. **Combined Approach (Recommended)**: Upload and process in a single step
2. **Step-by-Step Approach**: Upload, then process, then retrieve results

Let's explore each approach in detail.

## Combined Upload and Process

The simplest way to use the API is with the combined upload-and-process endpoint:

=== "cURL"

    ```bash
    curl -X POST -F "file=@resume.pdf" -F "annotate=true" -F "generate_summary=true" http://localhost:8000/api/resumes/upload-and-process
    ```

=== "Python"

    ```python
    import requests
    
    url = "http://localhost:8000/api/resumes/upload-and-process"
    files = {"file": open("resume.pdf", "rb")}
    data = {
        "annotate": "true",
        "generate_summary": "true"
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Processing time: {result['processing_time_sec']} seconds")
    ```

The response includes the extracted data and processing information:

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
        {
          "text": "john.doe@example.com",
          "label_name": "Email"
        },
        {
          "text": "Software Engineer",
          "label_name": "JobTitle"
        }
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

## Step-by-Step Approach

If you prefer more control over the process, you can use the step-by-step approach.

### Uploading a Resume

To upload a single resume (PDF or PNG):

=== "cURL"

    ```bash
    curl -X POST -F "file=@resume.pdf" http://localhost:8000/api/resumes/upload
    ```

=== "Python"

    ```python
    import requests
    
    url = "http://localhost:8000/api/resumes/upload"
    files = {"file": open("resume.pdf", "rb")}
    
    response = requests.post(url, files=files)
    result = response.json()
    
    file_id = result["file_id"]
    print(f"Uploaded file with ID: {file_id}")
    ```

The response will include a `file_id` that you'll need for the next steps:

```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "file_id": "john_doe_resume"
}
```

### Processing a Resume

To process a single uploaded file:

=== "cURL"

    ```bash
    curl -X POST "http://localhost:8000/api/resumes/process?file_id=john_doe_resume&annotate=true&generate_summary=true"
    ```

=== "Python"

    ```python
    import requests
    
    url = "http://localhost:8000/api/resumes/process"
    params = {
        "file_id": "john_doe_resume",
        "annotate": "true",
        "generate_summary": "true"
    }
    
    response = requests.post(url, params=params)
    result = response.json()
    
    print(f"Processing time: {result['processing_time_sec']} seconds")
    ```

The response includes the extracted data and processing information:

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
        {
          "text": "john.doe@example.com",
          "label_name": "Email"
        },
        {
          "text": "Software Engineer",
          "label_name": "JobTitle"
        }
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

## Retrieving Results

To retrieve the processing results for a specific file:

=== "cURL"

    ```bash
    curl -X GET "http://localhost:8000/api/resumes/results/john_doe_resume"
    ```

=== "Python"

    ```python
    import requests
    
    url = "http://localhost:8000/api/resumes/results/john_doe_resume"
    
    response = requests.get(url)
    result = response.json()
    
    print(f"Status: {result['status']}")
    print(f"Pages: {len(result['data']['extraction_data']['pages'])}")
    ```

The response includes detailed extraction data:

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
        {
          "image_id": "john_doe_resume_page1",
          "image_width_px": 595,
          "image_height_px": 842,
          "data": [
            // Extracted fields...
          ],
          "page_num": 1
        }
      ],
      "image_urls": [
        "http://localhost:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
      ]
    },
    "annotation_files": [
      "/path/to/annotations/john_doe_resume/john_doe_resume_page1.png"
    ]
  }
}
```

## Advanced Usage

### Controlling Annotation and Summary Generation

You can control whether to create visual annotations and generate a professional summary:

=== "cURL"

    ```bash
    # For combined endpoint
    curl -X POST -F "file=@resume.pdf" -F "annotate=false" -F "generate_summary=false" http://localhost:8000/api/resumes/upload-and-process
    
    # For separate process endpoint
    curl -X POST "http://localhost:8000/api/resumes/process?file_id=john_doe_resume&annotate=false&generate_summary=false"
    ```

=== "Python"

    ```python
    # For combined endpoint
    import requests
    
    url = "http://localhost:8000/api/resumes/upload-and-process"
    files = {"file": open("resume.pdf", "rb")}
    data = {
        "annotate": "false",
        "generate_summary": "false"
    }
    
    response = requests.post(url, files=files, data=data)
    
    # For separate process endpoint
    url = "http://localhost:8000/api/resumes/process"
    params = {
        "file_id": "john_doe_resume",
        "annotate": "false",
        "generate_summary": "false"
    }
    
    response = requests.post(url, params=params)
    ```

### Cleaning Up Storage

To free up disk space and remove all processed files:

=== "cURL"

    ```bash
    curl -X POST "http://localhost:8000/api/resumes/cleanup"
    ```

=== "Python"

    ```python
    import requests
    
    url = "http://localhost:8000/api/resumes/cleanup"
    
    response = requests.post(url)
    result = response.json()
    
    print(f"Message: {result['message']}")
    print(f"Cleaned directories: {result['data']['directories_cleaned']}")
    ```

## Common Patterns

### Complete Processing Workflow (Combined Approach)

Here's a complete example using the combined endpoint:

```python
import requests

# API base URL
base_url = "http://localhost:8000/api"

# Upload and process the resume in one step
url = f"{base_url}/resumes/upload-and-process"
files = {"file": open("resume.pdf", "rb")}
data = {
    "annotate": "true",
    "generate_summary": "true"
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Processing time: {result['processing_time_sec']} seconds")

# Access extracted data
for page in result["pages"]:
    print(f"Page {page['page_num']}:")
    for field in page["data"]:
        print(f"  {field['label_name']}: {field['text']}")

# Display annotation image URL
for image_url in result["image_urls"]:
    print(f"Annotation URL: {image_url}")
```

### Complete Processing Workflow (Step-by-Step)

Here's a complete example of the step-by-step approach:

```python
import requests
import time

# API base URL
base_url = "http://localhost:8000/api"

# 1. Upload the resume
upload_url = f"{base_url}/resumes/upload"
files = {"file": open("resume.pdf", "rb")}
upload_response = requests.post(upload_url, files=files)
file_id = upload_response.json()["file_id"]
print(f"Uploaded file with ID: {file_id}")

# 2. Process the resume
process_url = f"{base_url}/resumes/process"
process_params = {
    "file_id": file_id,
    "annotate": "true",
    "generate_summary": "true"
}
process_response = requests.post(process_url, params=process_params)
process_result = process_response.json()
print(f"Processing time: {process_result['processing_time_sec']} seconds")

# 3. Retrieve the results
results_url = f"{base_url}/resumes/results/{file_id}"
results_response = requests.get(results_url)
results = results_response.json()

# 4. Access extracted data
extraction_data = results["data"]["extraction_data"]
for page in extraction_data["pages"]:
    print(f"Page {page['page_num']}:")
    for field in page["data"]:
        print(f"  {field['label_name']}: {field['text']}")

# 5. Display annotation image URL
for image_url in extraction_data["image_urls"]:
    print(f"Annotation URL: {image_url}")
```

## Error Handling

Always check for errors in API responses:

```python
import requests

def safe_api_call(method, url, **kwargs):
    """Make an API call with error handling."""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
        try:
            error_detail = response.json().get("detail", "No detail provided")
            print(f"Error detail: {error_detail}")
        except:
            print(f"Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Connection error: Could not connect to the API")
    except requests.exceptions.Timeout:
        print("Timeout error: Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except ValueError:
        print("Error: Could not parse response as JSON")
    return None

# Example usage with combined endpoint
result = safe_api_call(
    "POST", 
    "http://localhost:8000/api/resumes/upload-and-process", 
    files={"file": open("resume.pdf", "rb")},
    data={"annotate": "true", "generate_summary": "true"}
)

if result:
    print("Processing successful")
else:
    print("Processing failed")
```