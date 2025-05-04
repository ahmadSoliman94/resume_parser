# Resume Parser AI

Welcome to the Resume Parser AI documentation. This system provides powerful tools for parsing, analyzing, and extracting structured data from resumes and CVs.

## 🔍 System Overview

Resume Parser AI is a comprehensive solution that extracts key information from resume documents using advanced vision-language models. The system can:

- Process PDF and PNG resume files
- Extract personal information, education, work experience, and skills
- Generate professional summaries of candidates
- Create visual annotations showing detected fields
- Provide structured data output in JSON format

## 🚀 Key Features

- **📤 Easy Upload**: Simple file upload via API or user interface
- **🧠 Advanced ML Processing**: Powered by Qwen2.5-VL vision-language model
- **👁️ Visual Field Detection**: Identifies and annotates key resume fields
- **📚 Multi-Page Support**: Processes multi-page resumes with page-specific data
- **📝 Summary Generation**: Creates professional candidate summaries
- **📊 Structured Output**: Provides standardized JSON data for downstream applications
- **💪 GPU Acceleration**: Optimized performance with GPU support

## 📄 Technical Architecture

The system is built with a modular architecture:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  FastAPI        │      │  OCR Service    │      │   Annotator     │
│  Web Server     │─────▶│  (VLM-based)    │─────▶│   Service       │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                         │                        │
        │                         │                        │
        ▼                         ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│    Storage      │      │   Processing    │      │   Summary       │
│    Management   │◀────▶│   Pipeline      │◀────▶│   Generation    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## 🏗️ Core Components

The Resume Parser AI consists of several key components:

- **OCR Service**: Extracts text and structure using vision-language models
- **Annotator**: Creates visual annotations of detected fields
- **Processing**: Validates and cleans extracted data
- **API Layer**: Provides REST API endpoints for client applications

## 📥 Getting Started

To get started with Resume Parser AI:

1. [Installation](getting-started/installation.md): Set up the system on your infrastructure
2. [Configuration](getting-started/configuration.md): Configure the system to your needs
3. [Usage](getting-started/usage.md): Learn how to use the API endpoints

## 🛠️ API Reference

Explore the API documentation:

- [API Overview](api/overview.md): High-level overview of the API
- [Endpoints](api/endpoints.md): Detailed endpoint documentation
- [Models](api/models.md): Data models and schemas

## 📊 Example Output

Here's an example of the structured data output:

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
    },
    {
      "JobTitle": "Software Developer",
      "Company": "Innovation Labs",
      "Duration": "2018-2019",
      "Responsibilities": "Developed web applications using React and Node.js"
    }
  ],
  "Skills": {
    "TechnicalSkills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
    "Languages": ["English (Native)", "Spanish (Intermediate)"]
  },
  "Summary": "Experienced software engineer with 5+ years of expertise in full-stack development and cloud technologies. Specializes in scalable web applications with a strong background in computer science from Stanford University. Proven leadership skills managing development teams and delivering high-quality software products."
}
```


## 📚 Next Steps

- Explore the [core components](components/ocr-service.md) for detailed implementation information
- Learn about [API usage](api/overview.md) to integrate with your applications
- Check out the [configuration options](getting-started/configuration.md) to customize the system