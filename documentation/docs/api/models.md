# API Models

This page documents the data models used in the Resume Parser AI API. These models define the structure of data exchanged between different components of the system and the API responses returned to clients.

## Core Models

These core models are defined in `core.py` and are used throughout the application to represent file types, processing status, and results.

### FileType

An enumeration of supported file types for resume processing.

```python
class FileType(str, Enum):
    """Supported file types."""

    PDF = "pdf"
    PNG = "png"
```

These file types are used to validate incoming files and determine the appropriate processing method.

### ProcessingStatus

An enumeration of possible statuses for resume processing operations.

```python
class ProcessingStatus(str, Enum):
    """Status of resume processing."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
```

This status is used in responses to indicate the outcome of processing operations.

### ProcessingMetrics

A data class that captures performance metrics during resume processing.

```python
@dataclass
class ProcessingMetrics:
    """Metrics for resume processing."""

    start_time: float
    end_time: Optional[float] = None
    total_execution_time: Optional[float] = None
    ocr_time: Optional[float] = None
    annotation_time: Optional[float] = None
```

**Fields:**
- `start_time`: Timestamp when processing began
- `end_time`: Timestamp when processing completed
- `total_execution_time`: Total processing time in seconds
- `ocr_time`: Time spent on OCR processing
- `annotation_time`: Time spent on field annotation

### ProcessingResult

A data class that contains the comprehensive results of a resume processing operation.

```python
@dataclass
class ProcessingResult:
    """Result of resume processing."""

    file_path: str
    status: ProcessingStatus
    extraction_file_path: Optional[str] = None
    annotated_file_paths: Optional[List[str]] = None
    metrics: Optional[ProcessingMetrics] = None
    error: Optional[str] = None
```

**Fields:**
- `file_path`: Path to the processed resume file
- `status`: Processing status (SUCCESS, FAILURE, or PENDING)
- `extraction_file_path`: Path to the JSON file containing extracted data
- `annotated_file_paths`: List of paths to annotated resume images
- `metrics`: Performance metrics for the processing operation
- `error`: Error message if processing failed

## Resume Data Models

These models represent the structured data extracted from resume documents.

### PersonalInfo

Represents personal information extracted from a resume.

```python
class PersonalInfo(BaseModel):
    """Personal information from a resume."""

    Name: str = Field(..., description="The candidate's full name")
    Email: str = Field(..., description="Email address")
    Phone: str = Field(..., description="Phone number")
    Location: str = Field(..., description="City, state/province, country")
```

### Education

Represents an educational entry in a resume.

```python
class Education(BaseModel):
    """Educational entry in a resume."""

    Degree: str = Field(..., description="Type of degree/certificate")
    Institution: str = Field(..., description="Name of university or institution")
    GradDate: str = Field(..., description="Date of graduation or expected graduation")
```

### WorkExperience

Represents a work experience entry in a resume.

```python
class WorkExperience(BaseModel):
    """Work experience entry in a resume."""

    JobTitle: str = Field(..., description="Position held")
    Company: str = Field(..., description="Organization or company name")
    Duration: str = Field(..., description="Start and end dates")
    Responsibilities: str = Field(..., description="Main duties and achievements")
```

### Skills

Represents skills extracted from a resume.

```python
class Skills(BaseModel):
    """Skills section of a resume."""

    TechnicalSkills: List[str] = Field(default_factory=list, description="Programming languages, tools, frameworks")
    Languages: List[str] = Field(default_factory=list, description="Human languages and proficiency levels")
```

### ResumeData

Represents the complete set of data extracted from a resume.

```python
class ResumeData(BaseModel):
    """Complete resume data."""

    PersonalInfo: PersonalInfo
    Education: List[Education] = Field(default_factory=list)
    WorkExperience: List[WorkExperience] = Field(default_factory=list)
    Skills: Skills = Field(default_factory=Skills)
    Summary: Optional[str] = None
```

## API Response Models

These models represent the structure of API responses.

### PageData

Represents data extracted from a single page of a multi-page resume.

```python
class PageData(BaseModel):
    """Data extracted from a single page."""

    image_id: str = Field(..., description="Unique identifier for the page image")
    image_width_px: int = Field(..., description="Width of the page image in pixels")
    image_height_px: int = Field(..., description="Height of the page image in pixels")
    data: List[Dict[str, str]] = Field(..., description="Extracted field data")
    page_num: int = Field(..., description="Page number")
```

### ProcessingResponse

Standard response structure for processing operations.

```python
class ProcessingResponse(BaseModel):
    """Response model for processing requests."""

    file_id: str = Field(..., description="Unique identifier for the processed file")
    processing_time_sec: float = Field(..., description="Processing time in seconds")
    created_at: str = Field(..., description="Timestamp when processing was completed")
    pages: List[PageData] = Field(..., description="Extracted data for each page")
    image_urls: List[str] = Field(..., description="URLs to annotated images")
    message: str = Field(..., description="Processing status message")
    summary_generated: bool = Field(..., description="Whether a summary was generated")
```

### ResultsResponse

Response structure for retrieving processing results.

```python
class ResultsResponse(BaseModel):
    """Response model for results retrieval."""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Result data")
```

### CleanupResponse

Response structure for cleanup operations.

```python
class CleanupResponse(BaseModel):
    """Response model for cleanup operations."""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Dict[str, List[str]] = Field(..., description="Cleanup details")
    execution_time: float = Field(..., description="Execution time in seconds")
```

## Data Flow

The data flow through the system follows this general pattern:

1. Client uploads a resume file (PDF or PNG)
2. System processes the file using OCR to extract text
3. Extracted text is structured into `ResumeData` objects
4. For multi-page documents, data is organized by page
5. Processing results are recorded in `ProcessingResponse` objects
6. API responses are formatted using the appropriate response models

## Example JSON Structures

### Example Resume Data JSON

```json
{
  "PersonalInfo": {
    "Name": "John Doe",
    "Email": "john.doe@example.com",
    "Phone": "+1 (555) 123-4567",
    "Location": "San Francisco, CA"
  },
  "Education": [
    {
      "Degree": "Bachelor of Science in Computer Science",
      "Institution": "Stanford University",
      "GradDate": "2018"
    }
  ],
  "WorkExperience": [
    {
      "JobTitle": "Senior Software Engineer",
      "Company": "Tech Solutions Inc.",
      "Duration": "2019-Present",
      "Responsibilities": "Led development of cloud-based applications, managed team of 5 developers"
    }
  ],
  "Skills": {
    "TechnicalSkills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
    "Languages": ["English (Native)", "Spanish (Intermediate)"]
  },
  "Summary": "Experienced software engineer with 5+ years of expertise in full-stack development and cloud technologies."
}
```

### Example Processing Response JSON

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
          "text": "+1 (555) 123-4567",
          "label_name": "Phone"
        },
        {
          "text": "San Francisco, CA",
          "label_name": "Location"
        },
        {
          "text": "Senior Software Engineer",
          "label_name": "JobTitle"
        }
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

### Example Results Response JSON

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
        "http://localhost:8000/api/static/annotations/john_doe_resume/john_doe_resume_page1.png"
      ]
    },
    "annotation_files": [
      "/path/to/annotations/john_doe_resume/john_doe_resume_page1.png"
    ]
  }
}
```

### Example Cleanup Response JSON

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