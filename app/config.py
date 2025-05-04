import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Storage paths
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
PREDICTIONS_DIR = os.path.join(STORAGE_DIR, "predictions")
EXTRACTION_DIR = os.path.join(PREDICTIONS_DIR, "extraction_results")
LOGS_DIR = os.path.join(PREDICTIONS_DIR, "logs")
ANNOTATIONS_DIR = os.path.join(PREDICTIONS_DIR, "annotations")

# Create necessary directories
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(EXTRACTION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

SYSTEM_PROMPT = """
Act as an advanced Resume/CV analysis assistant. Analyze the provided
resume/CV and extract the following key information:

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

After extraction, format results as a valid JSON:

{
    "PersonalInfo": {
        "Name": "string",
        "Email": "string",
        "Phone": "string",
        "Location": "string"
    },
    "Education": [
        {
            "Degree": "string",
            "Institution": "string",
            "GradDate": "string"
        }
    ],
    "WorkExperience": [
        {
            "JobTitle": "string",
            "Company": "string",
            "Duration": "string",
            "Responsibilities": "string"
        }
    ],
    "Skills": {
        "TechnicalSkills": ["string"],
        "Languages": ["string"]
    }
}

Extraction guidelines:
* Extract values exactly as they appear
* For missing information, use "Not Found"
* Create separate entries for each education, work experience
* Format technical skills and languages as lists when possible
* If dates are ranges (e.g., "2018-2020"), preserve the format
"""

# System prompt for summary generation
SUMMARY_PROMPT = """
Based on the extracted resume data, generate a professional summary of the
candidate (3-5 sentences) that includes:
1. Years of experience and current professional role/focus
2. Key areas of expertise based on work history and skills
3. Educational background relevant to their career
4. Notable career achievements or specializations

Format your response as JSON:
{
    "Summary": "Professional summary text here"
}
"""

# Field colors for annotation
FIELD_COLORS = {
    "Name": (0, 0, 255),  # Blue
    "Email": (255, 165, 0),  # Orange
    "Phone": (0, 255, 0),  # Green
    "Location": (255, 0, 0),  # Red
    "JobTitle": (0, 128, 128),  # Teal
}

DEFAULT_COLOR = (75, 0, 130)  # Indigo
