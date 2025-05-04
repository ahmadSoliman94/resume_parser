# OCR Service

The OCR Service is the core component of the Resume Parser AI system. It's responsible for extracting structured data from resume documents using advanced vision-language models (VLMs) and natural language processing techniques.

## Overview

The OCR Service offers several key capabilities:

1. **Document Parsing**: Extracts text and structure from PDF and image files
2. **Multi-Page Support**: Processes resumes with multiple pages
3. **Structured Data Extraction**: Identifies and extracts key resume fields
4. **Professional Summary Generation**: Creates concise candidate summaries 
5. **Integration with Annotation**: Enables visual marking of detected fields

## Architecture

The OCR service consists of several interconnected components:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Document     │      │  Vision-Language │      │   Structured    │
│     Parser      │─────▶│      Model      │─────▶│   Data Output   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Multi-page     │      │    Summary      │      │   Annotation    │
│  Handling       │      │   Generation    │      │    Service      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Core Components

### Document Parser

The `doc_parser` function in `ocr_service.py` is responsible for extracting text from resume documents. It handles both PDF and PNG files.

Key features:
- PDF page extraction with PyMuPDF (fitz)
- Image preprocessing and enhancement
- Integration with the Qwen2.5-VL vision-language model
- JSON extraction and validation

### Vision-Language Model Integration

The system uses Qwen2.5-VL-7B-Instruct, a powerful vision-language model that can understand both text and visual elements in documents:

```python
# Loading the model
model, processor = get_model_and_processor()

# Processing with VLM
text_prompt = processor.apply_chat_template(
    messages, tokenize=False, add_generation_prompt=True
)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(
    text=[text_prompt],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
)
inputs = inputs.to("cuda")
generated_ids = model.generate(**inputs, max_new_tokens=1024)
```

### Multi-Page Handling

The system supports multi-page PDF documents by:
1. Detecting multiple pages in PDF files
2. Converting each page to an image for processing
3. Preserving key information across pages
4. Creating a consolidated JSON structure

```python
# For multi-page PDFs, keep each page's data separate
if len(doc) > 1:
    all_pages_data: Dict[str, Dict[str, Any]] = {"pages": {}}
    
    # Process each page
    for page_num in range(len(doc)):
        # Process page and extract data
        page_data = process_page(page)
        
        # Store in comprehensive structure
        all_pages_data["pages"][f"page{page_num + 1}"] = page_data
```

### Professional Summary Generation

The system can automatically generate professional summaries for candidates using the extracted data:

```python
# Generate summary using the extracted data
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": config.SUMMARY_PROMPT + "\n\nResume Data:\n" + resume_text,
            }
        ],
    }
]
```

The summary is based on the candidate's:
- Work experience and career history
- Education background
- Technical skills and expertise
- Professional achievements

## Process Flow

1. **Input Validation**: The system verifies that the input file exists and is a supported format (PDF or PNG)
2. **File Processing**:
   - PDFs are converted to images page by page
   - Images are processed directly
3. **OCR Extraction**:
   - The VLM processes each page image
   - System prompt guides extraction of specific fields
   - Results are parsed into structured JSON
4. **Data Validation**:
   - Extracted data is validated against expected schema
   - Contact information is verified (email, phone)
5. **Summary Generation**: (Optional) A professional summary is generated based on the extracted data
6. **Result Storage**:
   - Extracted data is saved as JSON
   - Processing logs are recorded

## System Prompt

The OCR service uses a specialized system prompt to guide the VLM in extracting specific fields:

```
Act as an advanced Resume/CV analysis assistant. Analyze the provided resume/CV and extract the following key information:

## PERSONAL INFORMATION:
* Full Name (Name): The candidate's full name
* Email (Email): Email address
* Phone (Phone): Phone number
* Location (Location): City, state/province, country

## EDUCATION:
* For each educational entry, extract:
  * Degree (Degree): Type of degree/certificate
  * Institution (Institution): Name of university or institution
  * Graduation Date (GradDate): Date of graduation or expected graduation

## WORK EXPERIENCE:
* For each work experience entry, extract:
  * Job Title (JobTitle): Position held
  * Company (Company): Organization or company name
  * Duration (Duration): Start and end dates
  * Responsibilities (Responsibilities): Main duties and achievements

## SKILLS:
* Technical Skills (TechnicalSkills): Programming languages, tools, frameworks
* Languages (Languages): Human languages and proficiency levels
```

## Performance Optimization

The OCR service includes several optimizations:

1. **GPU Acceleration**: Uses CUDA for processing when available
2. **Model Quantization**: 4-bit quantization for the VLM model
3. **Flash Attention**: Advanced attention mechanism for faster processing
4. **Memory Management**: Explicit GPU memory cleanup

## Error Handling

The service implements comprehensive error handling:

1. **File Processing Errors**: Handles issues with file access or corrupt files
2. **Model Execution Errors**: Manages problems during model inference
3. **Graceful Degradation**: Falls back to basic OCR if advanced features fail
4. **Detailed Logging**: Records comprehensive error information

## Integration with External Tools

The OCR service integrates with:

1. **AutoGen**: For orchestration of processing agents
2. **EasyOCR**: For supplementary OCR processing
3. **PyMuPDF**: For PDF handling
4. **OpenCV**: For image preprocessing

## Usage Example

Here's a basic example of using the OCR service programmatically:

```python
from services.ocr_service import process_resume

# Process a resume file
result = process_resume(
    file_path="path/to/resume.pdf",
    use_annotator=True,
    generate_summary=True
)

# Access the extracted data
print(f"Processing time: {result['processing_time_sec']} seconds")
print(f"Candidate name: {result['pages'][0]['data'][0]['text']}")
print(f"Generated summary available: {result['summary_generated']}")
```

## Next Steps

- **[Annotator](annotator.md)**: Learn about the visual annotation component
- **[Processing](processing.md)**: Explore the data validation and processing pipeline
- **[API Endpoints](../api/endpoints.md)**: See how to use the OCR service via API