import gc
import os
import shutil
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
import torch
import uvicorn
from api.routers import resumes
from dependencies import get_model_and_processor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import ORJSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# First, preload the model before creating the FastAPI app
model, processor = get_model_and_processor()

# Clear GPU memory on startup
torch.cuda.empty_cache()
torch.backends.cudnn.benchmark = True
gc.collect()

# Create FastAPI app
app = FastAPI(
    title="📄 Resume Parser AI",
    description="""
    🚀 Advanced Resume/CV Data Extraction System
    This API provides powerful tools for CV data extraction and analysis:

    ✨ Features:
    - 📤 Easy PDF and DOCX resume upload with batch processing
    - 🔍 Advanced OCR processing optimized for resumes and CVs
    - 🤖 Powered by Qwen2.5-VL vision-language model
    - 📊 Visual field annotations on extracted documents
    - 💪 GPU-accelerated processing with quantization support
    - 📝 Structured JSON output with personal, education, and work experience data
    - 🏢 Automatic skill categorization and matching
    - 🧹 Storage cleanup functionality for maintenance

    🔧 Supported File Formats:
    - PDF (single or multiple pages)
    - PNG
    """,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    default_response_class=ORJSONResponse,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(resumes.router, prefix="/api")

# Mount static files for annotations
app.mount(
    "/api/static/annotations",
    StaticFiles(directory=config.ANNOTATIONS_DIR),
    name="annotations",
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="📄 Resume Parser AI Documentation",
        swagger_favicon_url="",
    )


def clean_model_cache():
    """Clean up model cache directory after loading."""
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)


# Clean up cache
clean_model_cache()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
