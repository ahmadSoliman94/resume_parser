# Configuration

This page details how to configure the Resume Parser AI to suit your needs.


## Directory Structure

The application uses several directories for storing uploaded files, processing results, and logs:

```
storage/
├── uploads/           # Uploaded resume files
└── predictions/
    ├── extraction_results/  # JSON results from processing
    ├── annotations/         # Annotated resume images
    └── logs/                # Processing logs
```

These directories are created automatically but can be customized by modifying the `config.py` file.

## Customizing the OCR Model

The application uses the Qwen2.5-VL-7B-Instruct model by default. To use a different model:

1. Edit `dependencies.py` to change the model path:

```python
# Change this line
model_name = "/app/hf_models/Qwen2.5-VL-7B-Instruct"

# To use a different model
model_name = "/app/hf_models/your-preferred-model"
```

2. Make sure to download the model files to the specified path.

## System Prompts

The application uses system prompts to guide the model in extracting information from resumes. You can customize these prompts in `config.py`:

### Main Extraction Prompt

This prompt instructs the model on how to extract key resume information:

```python
SYSTEM_PROMPT = """
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

After extraction, format results as a valid JSON:
...
```

### Summary Generation Prompt

This prompt guides the generation of a professional summary:

```python
SUMMARY_PROMPT = """
Based on the extracted resume data, generate a professional summary of the candidate (3-5 sentences) that includes:
1. Years of experience and current professional role/focus
2. Key areas of expertise based on work history and skills
3. Educational background relevant to their career
4. Notable career achievements or specializations

Format your response as JSON:
{
    "Summary": "Professional summary text here"
}
"""
```

## Field Annotation Colors

You can customize the colors used for field annotations by modifying the `FIELD_COLORS` dictionary in `config.py`:

```python
FIELD_COLORS = {
    "Name": (0, 0, 255),          # Blue
    "Email": (255, 165, 0),       # Orange
    "Phone": (0, 255, 0),         # Green
    "Location": (255, 0, 0),      # Red
    "JobTitle": (0, 128, 128),    # Teal
}
```

Colors are specified as RGB tuples.

## Performance Tuning



1. **Model Quantization**: The model uses 4-bit quantization by default. You can adjust this in `dependencies.py`:

```python
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,  # Set to False for higher precision but more memory usage
    bnb_4bit_compute_dtype=torch.float16
)
```

## Next Steps

After configuring your application, proceed to the [Usage](usage.md) guide to learn how to use the API.