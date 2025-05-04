import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

# Set test environment variables
os.environ["DEBUG"] = "True"
os.environ["USE_GPU"] = "False"  # Disable GPU for tests


@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_pdf(test_dir):
    """Create a sample PDF file for testing."""
    pdf_path = test_dir / "sample_resume.pdf"
    # Create an empty file
    pdf_path.write_bytes(b"%PDF-1.5\n%Test PDF file")
    return pdf_path


@pytest.fixture
def sample_png(test_dir):
    """Create a sample PNG file for testing."""
    png_path = test_dir / "sample_resume.png"
    # Create an empty PNG file with minimal header
    png_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0eIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdb\xfd\x0f\xf8\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return png_path


@pytest.fixture
def sample_json_data():
    """Create sample JSON data for testing."""
    return {
        "PersonalInfo": {
            "Name": "John Doe",
            "Email": "john.doe@example.com",
            "Phone": "+1234567890",
            "Location": "New York, NY",
        },
        "Education": [
            {
                "Degree": "Bachelor of Science in Computer Science",
                "Institution": "Test University",
                "GradDate": "2020",
            }
        ],
        "WorkExperience": [
            {
                "JobTitle": "Software Engineer",
                "Company": "Tech Company",
                "Duration": "2021-Present",
                "Responsibilities": "Developing applications",
            }
        ],
        "Skills": {
            "TechnicalSkills": ["Python", "JavaScript", "React"],
            "Languages": ["English", "Spanish"],
        },
    }


@pytest.fixture
def sample_json_file(test_dir, sample_json_data):
    """Create a sample JSON file for testing."""
    json_path = test_dir / "sample_resume.json"
    with open(json_path, "w") as f:
        json.dump(sample_json_data, f)
    return json_path


@pytest.fixture
def multipage_json_data():
    """Create sample multi-page JSON data for testing."""
    return {
        "pages": {
            "page1": {
                "PersonalInfo": {
                    "Name": "John Doe",
                    "Email": "john.doe@example.com",
                    "Phone": "+1234567890",
                    "Location": "New York, NY",
                },
                "Education": [
                    {
                        "Degree": "Bachelor of Science in Computer Science",
                        "Institution": "Test University",
                        "GradDate": "2020",
                    }
                ],
            },
            "page2": {
                "WorkExperience": [
                    {
                        "JobTitle": "Software Engineer",
                        "Company": "Tech Company",
                        "Duration": "2021-Present",
                        "Responsibilities": "Developing applications",
                    }
                ],
                "Skills": {
                    "TechnicalSkills": ["Python", "JavaScript", "React"],
                    "Languages": ["English", "Spanish"],
                },
            },
        }
    }


@pytest.fixture
def multipage_json_file(test_dir, multipage_json_data):
    """Create a sample multi-page JSON file for testing."""
    json_path = test_dir / "multipage_resume.json"
    with open(json_path, "w") as f:
        json.dump(multipage_json_data, f)
    return json_path


@pytest.fixture(scope="session", autouse=True)
def patch_model_loading():
    """Patch model loading for all tests."""
    with patch("app.dependencies.get_model_and_processor") as mock_get:
        # Create mock model
        mock_model = MagicMock()
        mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

        # Create mock processor
        mock_processor = MagicMock()
        mock_processor.apply_chat_template.return_value = "test prompt"
        mock_processor.batch_decode.return_value = [
            """
            {
                "PersonalInfo": {
                    "Name": "John Doe",
                    "Email": "john.doe@example.com"
                }
            }
            """
        ]

        mock_get.return_value = (mock_model, mock_processor)
        yield


@pytest.fixture
def mock_easyocr():
    """Mock the easyOCR Reader."""
    with patch("app.services.annotator.easyocr") as mock:
        mock_reader = MagicMock()
        # Mock the readtext method to return some text boxes
        mock_reader.readtext.return_value = [
            ([[0, 0], [100, 0], [100, 30], [0, 30]], "John Doe", 0.99),
            ([[0, 40], [150, 40], [150, 70], [0, 70]], "john.doe@example.com", 0.95),
            ([[0, 80], [120, 80], [120, 110], [0, 110]], "+1234567890", 0.98),
            ([[0, 120], [200, 120], [200, 150], [0, 150]], "New York, NY", 0.97),
            ([[0, 160], [180, 160], [180, 190], [0, 190]], "Software Engineer", 0.96),
        ]
        mock.Reader.return_value = mock_reader
        yield mock


@pytest.fixture
def mock_fitz():
    """Mock the PyMuPDF (fitz) module."""
    with patch("app.services.annotator.fitz") as mock:
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()

        # Set up chain of mock calls
        mock.open.return_value = mock_doc
        mock_doc.load_page.return_value = mock_page
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pixmap.tobytes.return_value = b"test image data"

        # Set up Matrix class
        mock.Matrix.return_value = MagicMock()

        # Set up rect property for page dimensions
        mock_page.rect.width = 595
        mock_page.rect.height = 842

        yield mock


@pytest.fixture
def mock_cv2():
    """Mock the OpenCV (cv2) module."""
    with patch("app.services.annotator.cv2") as mock:
        # Mock image reading and writing
        mock.imread.return_value = np.zeros((600, 800, 3), dtype=np.uint8)
        mock.imdecode.return_value = np.zeros((600, 800, 3), dtype=np.uint8)
        mock.rectangle = MagicMock()
        mock.putText = MagicMock()
        mock.imwrite = MagicMock()

        yield mock


@pytest.fixture
def mock_storage_dirs():
    """Mock storage directories."""
    storage_base = Path("mock_storage")
    uploads_dir = storage_base / "uploads"
    extraction_dir = storage_base / "predictions" / "extraction_results"
    annotations_dir = storage_base / "predictions" / "annotations"
    logs_dir = storage_base / "predictions" / "logs"

    # Create patch for config
    with patch("app.config") as mock_config:
        mock_config.STORAGE_DIR = str(storage_base)
        mock_config.UPLOADS_DIR = str(uploads_dir)
        mock_config.EXTRACTION_DIR = str(extraction_dir)
        mock_config.ANNOTATIONS_DIR = str(annotations_dir)
        mock_config.LOGS_DIR = str(logs_dir)
        yield {
            "storage_base": storage_base,
            "uploads_dir": uploads_dir,
            "extraction_dir": extraction_dir,
            "annotations_dir": annotations_dir,
            "logs_dir": logs_dir,
        }


@pytest.fixture
def mock_process_resume():
    """Mock the process_resume function."""
    with patch("app.api.routers.resumes.process_resume") as mock:
        mock.return_value = {
            "file_id": "test_resume",
            "processing_time_sec": 1.23,
            "created_at": "2025-04-01T12:00:00Z",
            "pages": [
                {
                    "image_id": "test_resume_page1",
                    "image_width_px": 595,
                    "image_height_px": 842,
                    "data": [
                        {"text": "John Doe", "label_name": "Name"},
                        {"text": "john@example.com", "label_name": "Email"},
                    ],
                    "page_num": 1,
                }
            ],
            "image_urls": ["/api/static/annotations/test_resume_page1.png"],
            "message": "Resume processed successfully",
            "summary_generated": True,
        }
        yield mock
