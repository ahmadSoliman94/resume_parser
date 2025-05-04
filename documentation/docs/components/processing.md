# Processing

The Processing component is responsible for validating, cleaning, and post-processing the data extracted from resumes. It ensures that the extracted information meets quality standards and is ready for use in downstream applications.

## Overview

The Processing system provides several key capabilities:

1. **Data Validation**: Verifies that extracted fields conform to expected formats
2. **Field Cleaning**: Normalizes dates, removes excess whitespace, and standardizes formats
3. **Format Conversion**: Ensures lists and structured data are in the proper format
4. **URL Management**: Updates image URLs with proper base URLs for API responses
5. **Quality Assurance**: Filters out low-confidence or invalid extractions

## Architecture

The Processing component serves as a critical link between raw extraction and usable data:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   OCR Service   │      │    Processing   │      │   API Response  │
│  (Raw Data)     │─────▶│     Pipeline    │─────▶│  (Clean Data)   │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │                          │
                                │                          │
                                ▼                          ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │    Validation   │      │    Storage &    │
                         │     Services    │      │   Persistence   │
                         └─────────────────┘      └─────────────────┘
```

## Key Components

### Data Validation Functions

The `processing.py` module contains several validation functions:

#### Email Validation

```python
def validate_email(email: str) -> bool:
    """
    Validate if a string is a properly formatted email address.
    
    Args:
        email: The email string to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    # Basic regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))
```

#### Phone Number Validation

```python
def validate_phone(phone: str) -> bool:
    """
    Validate if a string contains a valid phone number.
    
    Args:
        phone: The phone string to validate
        
    Returns:
        True if the phone is valid, False otherwise
    """
    # Remove common separators
    clean_phone = re.sub(r'[\s\-\.\(\)]', '', phone)
    # Check if we have a reasonable number of digits
    return 7 <= len(clean_phone) <= 15 and bool(re.match(r'^[+]?\d+$', clean_phone))
```

#### URL Validation

```python
def validate_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    # Basic regex for URL validation
    url_pattern = r'^(https?:\/\/)?(www\.)?([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)(\/[a-zA-Z0-9_-]+)*\/?$'
    return bool(re.match(url_pattern, url))
```

### Date Cleaning

```python
def clean_date(date_str: str) -> str:
    """
    Clean and standardize date strings from various formats.
    
    Args:
        date_str: Date string to clean
        
    Returns:
        Cleaned date string
    """
    # Handle empty values
    if not date_str or date_str == "Not Found":
        return "Not Found"
        
    # Try to clean and standardize the date format
    # This is a simplified version - you can expand it as needed
    return date_str
```

### Resume Data Validation

The core validation function processes the entire resume data structure:

```python
def validate_cv_data(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean extracted CV data.
    
    Args:
        json_data: The CV data dictionary
        
    Returns:
        Validated CV data dictionary
    """
    pages = json_data.get("pages", {})
    
    for page_key, page_data in pages.items():
        # Validate personal info
        if "PersonalInfo" in page_data:
            personal_info = page_data["PersonalInfo"]
            
            # Validate email
            if "Email" in personal_info and personal_info["Email"] != "Not Found":
                if not validate_email(personal_info["Email"]):
                    personal_info["Email"] = "Not Found"
            
            # Validate phone
            if "Phone" in personal_info and personal_info["Phone"] != "Not Found":
                if not validate_phone(personal_info["Phone"]):
                    personal_info["Phone"] = "Not Found"
        
        # Clean education dates
        if "Education" in page_data and isinstance(page_data["Education"], list):
            for edu in page_data["Education"]:
                if "GradDate" in edu:
                    edu["GradDate"] = clean_date(edu["GradDate"])
        
        # Clean work experience dates
        if "WorkExperience" in page_data and isinstance(page_data["WorkExperience"], list):
            for work in page_data["WorkExperience"]:
                if "Duration" in work:
                    work["Duration"] = clean_date(work["Duration"])
        
        # Validate skill entries
        if "Skills" in page_data:
            skills = page_data["Skills"]
            
            # Ensure TechnicalSkills is a list
            if "TechnicalSkills" in skills and not isinstance(skills["TechnicalSkills"], list):
                if skills["TechnicalSkills"] and skills["TechnicalSkills"] != "Not Found":
                    # Convert to list if it's a string
                    skills["TechnicalSkills"] = [skills["TechnicalSkills"]]
                else:
                    skills["TechnicalSkills"] = []
            
            # Ensure Languages is a list
            if "Languages" in skills and not isinstance(skills["Languages"], list):
                if skills["Languages"] and skills["Languages"] != "Not Found":
                    # Convert to list if it's a string
                    skills["Languages"] = [skills["Languages"]]
                else:
                    skills["Languages"] = []

    return json_data
```

### URL Management

The processing module also handles URL updates for API responses:

```python
def update_image_urls(result, base_url):
    """
    Update image URLs with the proper base URL.

    Args:
        result: The result dictionary with image_urls
        base_url: The base URL to prepend

    Returns:
        Updated result dictionary
    """
    # Make sure base URL ends with a slash if it doesn't already
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"

    # Update the image URLs
    updated_urls = []
    for url in result.get("image_urls", []):
        # Check if it's already a full URL
        if url.startswith(("http://", "https://")):
            updated_urls.append(url)
        else:
            # Remove leading slash if present to avoid double slash
            clean_url = url.lstrip("/")
            updated_url = f"{base_url}{clean_url}"
            updated_urls.append(updated_url)

    result["image_urls"] = updated_urls
    return result
```

### Text Cleaning (from utils.py)

The system also includes utility functions for text cleaning:

```python
def clean_text(text: str) -> str:
    """
    Clean text by removing excess whitespace and normalizing.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    if not text or text == "Not Found":
        return "Not Found"
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Trim whitespace
    return text.strip()
```

## Processing Workflow

The complete processing workflow consists of these steps:

1. **Initial Extraction**: The OCR service extracts raw data from the resume
2. **Validation**: Fields are validated against expected formats
3. **Cleaning**: Data is cleaned and normalized
4. **Format Standardization**: Data structures are standardized
5. **URL Management**: Image URLs are properly formatted
6. **Storage**: Processed data is saved in the extraction directory

## Integration with OCR Service

The processing module integrates with the OCR service via the validation process:

```python
# In ocr_service.py
def process_resume(file_path: str, use_annotator: bool = True, generate_summary: bool = True) -> Dict[str, Any]:
    """
    Process a resume with OCR, optional annotation, and optional summary generation.
    """
    # Extract data from the resume
    # ...
    
    # Validate the extracted data
    validated_data = validate_cv_data(all_pages_data)
    
    # Save validated result
    with open(extraction_file, "w", encoding="utf-8") as f:
        json.dump(
            validated_data,
            f,
            indent=4,
            ensure_ascii=False,
        )
```

## Integration with API Endpoints

The processing module is used in API endpoints to ensure proper response formatting:

```python
# In resumes.py
@upload_router.post("/upload-and-process")
async def upload_and_process(
    request: Request,
    file: UploadFile = File(...),
    annotate: bool = True,
    generate_summary: bool = True,
    settings: Settings = Depends(get_settings),
):
    """
    📤🔍 Upload and process resume file in one step
    """
    # Process the file
    try:
        # Process the resume with optional summary generation
        result = process_resume(
            file_path=file_path, 
            use_annotator=annotate,
            generate_summary=generate_summary
        )
        
        # Update image URLs with proper base URL
        base_url = str(request.base_url)
        result = update_image_urls(result, base_url)
        
        # Save updated result
        json_file_path = os.path.join(config.EXTRACTION_DIR, f"{base_filename}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        return result
```

## Skill Extraction and Categorization (utils.py)

Advanced processing includes skill extraction and categorization:

```python
def extract_skills_from_text(text: str, skill_keywords: List[str]) -> List[str]:
    """
    Extract skills from text based on a list of skill keywords.
    
    Args:
        text: The text to analyze
        skill_keywords: List of skill keywords to look for
        
    Returns:
        List of found skills
    """
    found_skills = []
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    for skill in skill_keywords:
        skill_lower = skill.lower()
        # Match whole words only
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    return found_skills

def categorize_skills(skills: List[str], categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Categorize skills into different categories.
    
    Args:
        skills: List of skills to categorize
        categories: Dictionary mapping category names to lists of skills in that category
        
    Returns:
        Dictionary mapping category names to found skills in that category
    """
    result = {category: [] for category in categories}
    
    for skill in skills:
        skill_lower = skill.lower()
        
        for category, category_skills in categories.items():
            if skill_lower in [s.lower() for s in category_skills]:
                result[category].append(skill)
                break
    
    return {k: v for k, v in result.items() if v}  # Remove empty categories
```

## Performance and Quality Considerations

The processing system is designed with several quality safeguards:

1. **Fail-Safe Default Values**: If a field cannot be validated, it defaults to "Not Found"
2. **Type Safety**: Checks for proper data types and converts as needed
3. **Data Structure Validation**: Ensures proper nesting of JSON objects
4. **List Handling**: Proper handling of both string and list values for skills
5. **Whitespace Normalization**: Consistent handling of whitespace and separators

## Next Steps

- **[OCR Service](ocr-service.md)**: Learn about the text extraction component
- **[Annotator](annotator.md)**: Explore the visual annotation component
- **[API Endpoints](../api/endpoints.md)**: See how to use the processing capabilities via API