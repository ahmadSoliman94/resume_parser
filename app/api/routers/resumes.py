import json
import os
import shutil
import sys
import time
from typing import Annotated

import config
from core.settings import get_settings
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from services.ocr_service import process_resume
from services.processing import update_image_urls

# Add parent directory to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Create separate routers for better organization
upload_router = APIRouter(
    prefix="/resumes",
    tags=["📤 Upload & Storage Management"],
    dependencies=[Depends(get_settings)],
)

processing_router = APIRouter(
    prefix="/resumes",
    tags=["🔍 OCR Processing"],
    dependencies=[Depends(get_settings)],
)

results_router = APIRouter(
    prefix="/resumes",
    tags=["📊 Results & Reporting"],
    dependencies=[Depends(get_settings)],
)

maintenance_router = APIRouter(
    prefix="/resumes",
    tags=["🧹 System Maintenance"],
    dependencies=[Depends(get_settings)],
)


@upload_router.post("/upload")
async def upload(
    file: Annotated[UploadFile, File(...)],
):
    """
    📤 Upload resume file for OCR processing

    Upload a PDF or Image (png) resume file for processing.

    Returns:
    - file_id for processing
    """
    # Ensure uploads directory exists
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)

    filename = file.filename or "unnamed_file"  # Handle None case
    file_extension = os.path.splitext(filename)[1].lower()
    base_filename = os.path.splitext(filename)[0]

    # Handle PDF or PNG file
    if file_extension in [".pdf", ".PDF", ".png"]:
        filename = file.filename or "unnamed_file"  # Handle None case
        file_path = os.path.join(config.UPLOADS_DIR, filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": base_filename,
        }
    else:
        return {
            "status": "error",
            "message": (
                f"Unsupported file type: {file_extension}. "
                "Only PDF and PNG files are supported."
            ),
        }


@upload_router.post("/upload-and-process")
async def upload_and_process(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    annotate: bool = True,
    generate_summary: bool = True,
):
    """
    📤🔍 Upload and process resume file in one step

    Upload a PDF or DOCX resume file and automatically process it.

    Parameters:
    - **file**: PDF, PNG or DOCX resume file to upload and process
    - **annotate**: Create visual annotations of detected fields (default: True)
    - **generate_summary**: Create a professional summary of the candidate
      (default: False)

    Returns structured data including personal info, education, experience,
    skills, etc.
    """
    # Ensure uploads directory exists
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)

    start_time = time.time()
    filename = file.filename or "unnamed_file"  # Handle None case
    file_extension = os.path.splitext(filename)[1].lower()
    base_filename = os.path.splitext(filename)[0]

    # Check if file is supported
    if file_extension not in [".pdf", ".PDF", ".png", ".docx", ".DOCX"]:
        return {
            "status": "error",
            "message": (
                f"Unsupported file type: {file_extension}. "
                "Only PDF, PNG, and DOCX files are supported."
            ),
        }

    # Save the uploaded file
    file_path = os.path.join(config.UPLOADS_DIR, filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Process the file
    try:
        # Process the resume with optional summary generation
        result = process_resume(
            file_path=file_path,
            use_annotator=annotate,
            generate_summary=generate_summary,
        )

        # Update image URLs with proper base URL
        base_url = str(request.base_url)
        result = update_image_urls(result, base_url)

        # Save updated result
        json_file_path = os.path.join(config.EXTRACTION_DIR, f"{base_filename}.json")
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        return result

    except Exception as e:
        return {
            "file_id": base_filename,
            "processing_time_sec": round(time.time() - start_time, 2),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pages": [],
            "image_urls": [],
            "message": f"Error processing file: {str(e)}",
        }


@processing_router.post("/process")
async def process(
    request: Request,
    file_id: str,
    annotate: bool = True,
    generate_summary: bool = True,
):
    """
    🔍 Process uploaded resume for data extraction

    Extract structured data from uploaded resumes and CVs.

    Parameters:
    - **file_id**: ID of resume file to process
    - **annotate**: Create visual annotations of detected fields (default: True)
    - **generate_summary**: Create a professional summary of the candidate
      (default: False)

    Returns structured data including personal information, education, work
    experience, skills, etc.
    """
    start_time = time.time()
    base_url = str(request.base_url)

    # First check if there's a file with that ID plus known extensions
    file_path = None
    for ext in [".pdf", ".PDF", ".png", ".docx", ".DOCX"]:
        potential_path = os.path.join(config.UPLOADS_DIR, f"{file_id}{ext}")
        if os.path.exists(potential_path):
            file_path = potential_path
            break

    # Verify file exists
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"File not found for ID: {file_id}",
        )

    try:
        # Process the resume with optional summary generation
        result = process_resume(
            file_path=file_path,
            use_annotator=annotate,
            generate_summary=generate_summary,
        )

        # Update image URLs
        result = update_image_urls(result, base_url)

        # Update the JSON file with the updated URLs
        json_file_path = os.path.join(config.EXTRACTION_DIR, f"{file_id}.json")
        if os.path.exists(json_file_path):
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

        return result

    except Exception as e:
        return {
            "file_id": file_id,
            "processing_time_sec": round(time.time() - start_time, 2),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pages": [],
            "image_urls": [],
            "message": f"Error processing file: {str(e)}",
        }


@results_router.get("/results/{file_id}")
async def get_results(file_id: str):
    """
    📊 Retrieve processing results for a resume

    Get the structured data and field annotations for a processed resume.

    Parameters:
    - **file_id**: ID of the processed resume file

    Returns:
    - Extracted JSON data with resume information
    - Paths to annotation images showing detected fields
    - Field values including personal information, education, experience, skills, etc.
    """
    # Check for JSON results
    json_path = os.path.join(config.EXTRACTION_DIR, f"{file_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(
            status_code=404,
            detail=f"Results not found for: {file_id}",
        )

    # Load JSON data
    with open(json_path, encoding="utf-8") as f:
        json_data = json.load(f)

    subfolder_path = os.path.join(config.ANNOTATIONS_DIR, file_id)
    annotations: list[str] = []

    if os.path.exists(subfolder_path):
        for file in sorted(os.listdir(subfolder_path)):
            if file.lower().endswith(".png"):
                annotations.append(os.path.join(subfolder_path, file))

    # Check for single-page annotation
    single_annotation = os.path.join(config.ANNOTATIONS_DIR, f"{file_id}_annotated.png")
    if os.path.exists(single_annotation):
        annotations.append(single_annotation)

    return {
        "status": "success",
        "message": "Results retrieved successfully",
        "data": {
            "file_id": file_id,
            "extraction_data": json_data,
            "annotation_files": annotations,
        },
    }


@maintenance_router.post("/cleanup")
async def cleanup_storage():
    """
    🧹 Clean up storage directories

    Removes all files from storage directories and recreates the directory structure.
    Use this endpoint to free up disk space or reset the system.

    Cleans:
    - Uploaded files
    - Extraction results
    - Annotations
    - Logs

    Returns information about the cleanup operation.
    """
    start_time = time.time()
    result = {
        "directories_cleaned": [],
        "directories_created": [],
        "errors": [],
    }

    # List of directories to clean
    directories = [
        {"path": config.UPLOADS_DIR, "name": "uploads"},
        {"path": config.EXTRACTION_DIR, "name": "extraction_results"},
        {"path": config.ANNOTATIONS_DIR, "name": "annotations"},
        {"path": config.LOGS_DIR, "name": "logs"},
    ]

    # Clean and recreate each directory
    for dir_info in directories:
        dir_path = dir_info["path"]
        dir_name = dir_info["name"]

        try:
            # Remove directory if it exists
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                result["directories_cleaned"].append(dir_name)

            # Create directory
            os.makedirs(dir_path, exist_ok=True)
            result["directories_created"].append(dir_name)

        except Exception as e:
            result["errors"].append({"directory": dir_name, "error": str(e)})

    return {
        "status": ("success" if not result["errors"] else "partial_success"),
        "message": (
            "Storage directories cleaned and recreated successfully"
            if not result["errors"]
            else "Some errors occurred during cleanup"
        ),
        "data": result,
        "execution_time": round(time.time() - start_time, 2),
    }


# Create a combined router for easier inclusion in the main app
router = APIRouter()
router.include_router(upload_router)
router.include_router(processing_router)
router.include_router(results_router)
router.include_router(maintenance_router)
