import json
from unittest.mock import MagicMock, mock_open, patch

import pytest
import torch

from app.services.ocr_service import (
    doc_parser,
    generate_summary_from_json,
    process_resume,
)


@pytest.fixture
def mock_model_and_processor():
    """Mock the model and processor for testing."""
    with patch("app.dependencies.get_model_and_processor") as mock_get:
        mock_model = MagicMock()
        mock_processor = MagicMock()

        # Setup mock model
        mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

        # Setup mock processor
        mock_processor.apply_chat_template.return_value = "test prompt"
        mock_processor.batch_decode.return_value = [
            """
            {
                "PersonalInfo": {
                    "Name": "John Doe",
                    "Email": "john@example.com",
                    "Phone": "+1234567890",
                    "Location": "New York, NY"
                },
                "Education": [
                    {
                        "Degree": "Bachelor of Science",
                        "Institution": "Test University",
                        "GradDate": "2020"
                    }
                ],
                "WorkExperience": [
                    {
                        "JobTitle": "Software Engineer",
                        "Company": "Tech Company",
                        "Duration": "2021-Present",
                        "Responsibilities": "Developing applications"
                    }
                ],
                "Skills": {
                    "TechnicalSkills": ["Python", "JavaScript"],
                    "Languages": ["English"]
                }
            }
            """
        ]

        mock_get.return_value = (mock_model, mock_processor)
        yield (mock_model, mock_processor)


@pytest.fixture
def mock_fitz():
    """Mock the fitz (PyMuPDF) module."""
    with patch("app.services.ocr_service.fitz") as mock:
        # Set up mock document
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

        yield mock


@pytest.fixture
def mock_cv2():
    """Mock the cv2 module."""
    with patch("app.services.ocr_service.cv2") as mock:
        mock.imdecode.return_value = MagicMock()
        mock.imread.return_value = MagicMock()
        yield mock


class TestDocParser:
    """Test the doc_parser function."""

    def test_file_not_found(self, mock_model_and_processor):
        """Test handling of nonexistent files."""
        with pytest.raises(FileNotFoundError):
            doc_parser("nonexistent_file.pdf")

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    def test_single_page_pdf(
        self, mock_abspath, mock_isfile, mock_fitz, mock_model_and_processor, mock_cv2
    ):
        """Test processing a single-page PDF."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/test.pdf"

        # Mock fitz.open to return a single-page document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        result = doc_parser("test.pdf")

        # Check the result is valid JSON with the expected structure
        parsed_result = json.loads(result)
        assert "pages" in parsed_result
        assert "page1" in parsed_result["pages"]
        assert "PersonalInfo" in parsed_result["pages"]["page1"]

        # Verify model and processor were called correctly
        model, processor = mock_model_and_processor
        assert processor.apply_chat_template.called
        assert model.generate.called
        assert processor.batch_decode.called

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    def test_multi_page_pdf(
        self, mock_abspath, mock_isfile, mock_fitz, mock_model_and_processor, mock_cv2
    ):
        """Test processing a multi-page PDF."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/test.pdf"

        # Mock fitz.open to return a multi-page document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_fitz.open.return_value = mock_doc

        result = doc_parser("test.pdf")

        # Check the result is valid JSON with the expected structure
        parsed_result = json.loads(result)
        assert "pages" in parsed_result
        assert len(parsed_result["pages"]) > 0

        # Verify model and processor were called multiple times (once per page)
        model, processor = mock_model_and_processor
        assert processor.apply_chat_template.call_count >= 3
        assert model.generate.call_count >= 3
        assert processor.batch_decode.call_count >= 3

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    def test_png_file(
        self, mock_abspath, mock_isfile, mock_model_and_processor, mock_cv2
    ):
        """Test processing a PNG file."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/test.png"

        result = doc_parser("test.png")

        # Check the result is valid JSON with the expected structure
        parsed_result = json.loads(result)
        assert "pages" in parsed_result
        assert "page1" in parsed_result["pages"]

        # Verify model and processor were called correctly
        model, processor = mock_model_and_processor
        assert processor.apply_chat_template.called
        assert model.generate.called
        assert processor.batch_decode.called


class TestProcessResume:
    """Test the process_resume function."""

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    @patch("app.services.ocr_service.time.time")
    @patch("app.services.ocr_service.doc_parser")
    @patch("app.services.ocr_service.annotate_resume")
    def test_process_resume_full(
        self, mock_annotate, mock_doc_parser, mock_time, mock_abspath, mock_isfile
    ):
        """Test processing a resume with annotation and summary generation."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/test.pdf"
        mock_time.side_effect = [1000, 1005]  # Start and end times

        # Mock doc_parser to return valid JSON
        mock_doc_parser.return_value = json.dumps(
            {
                "pages": {
                    "page1": {
                        "PersonalInfo": {
                            "Name": "John Doe",
                            "Email": "john@example.com",
                        }
                    }
                }
            }
        )

        # Mock open function for writing JSON
        with patch("builtins.open", mock_open()):
            result = process_resume(
                "test.pdf", use_annotator=True, generate_summary=True
            )

        # Check result structure
        assert result["file_id"] == "test"
        assert result["processing_time_sec"] == 5.0
        assert "pages" in result
        assert result["message"] == "Resume processed successfully"
        assert result["summary_generated"]

        # Verify annotator was called
        assert mock_annotate.called

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    @patch("app.services.ocr_service.time.time")
    @patch("app.services.ocr_service.doc_parser")
    @patch("app.services.ocr_service.annotate_resume")
    def test_process_resume_no_annotation(
        self, mock_annotate, mock_doc_parser, mock_time, mock_abspath, mock_isfile
    ):
        """Test processing a resume without annotation."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/test.pdf"
        mock_time.side_effect = [1000, 1005]  # Start and end times

        # Mock doc_parser to return valid JSON
        mock_doc_parser.return_value = json.dumps(
            {
                "pages": {
                    "page1": {
                        "PersonalInfo": {
                            "Name": "John Doe",
                            "Email": "john@example.com",
                        }
                    }
                }
            }
        )

        # Mock open function for writing JSON
        with patch("builtins.open", mock_open()):
            result = process_resume(
                "test.pdf", use_annotator=False, generate_summary=True
            )

        # Check result structure
        assert result["file_id"] == "test"
        assert "pages" in result
        assert result["message"] == "Resume processed successfully"

        # Verify annotator was not called
        assert not mock_annotate.called

    @patch("app.services.ocr_service.os.path.isfile")
    def test_process_resume_file_not_found(self, mock_isfile):
        """Test processing a nonexistent resume file."""
        mock_isfile.return_value = False

        with pytest.raises(FileNotFoundError):
            process_resume("nonexistent.pdf")


class TestSummaryGeneration:
    """Test the generate_summary_from_json function."""

    @patch("app.services.ocr_service.os.path.isfile")
    @patch("app.services.ocr_service.os.path.abspath")
    def test_generate_summary(
        self, mock_abspath, mock_isfile, mock_model_and_processor
    ):
        """Test generating a summary from JSON data."""
        mock_isfile.return_value = True
        mock_abspath.return_value = "/path/to/resume.json"

        # Mock JSON file content
        json_content = {
            "pages": {
                "page1": {
                    "PersonalInfo": {"Name": "John Doe", "Email": "john@example.com"},
                    "WorkExperience": [
                        {
                            "JobTitle": "Software Engineer",
                            "Company": "Tech Company",
                            "Duration": "2021-Present",
                        }
                    ],
                }
            }
        }

        # Override processor's batch_decode to return a summary
        mock_model_and_processor[1].batch_decode.return_value = [
            '{"Summary": "John Doe is a Software Engineer with experience at Tech Company."}'
        ]

        # Mock open function for reading and writing JSON
        with patch("builtins.open", mock_open(read_data=json.dumps(json_content))):
            result = generate_summary_from_json("resume.json")

        # Parse the result
        summary_data = json.loads(result)

        # Check the summary was generated
        assert "Summary" in summary_data
        assert "John Doe" in summary_data["Summary"]

    @patch("app.services.ocr_service.os.path.isfile")
    def test_generate_summary_file_not_found(self, mock_isfile):
        """Test generating a summary from a nonexistent JSON file."""
        mock_isfile.return_value = False

        with pytest.raises(FileNotFoundError):
            generate_summary_from_json("nonexistent.json")
