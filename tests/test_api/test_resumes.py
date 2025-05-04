import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

# Add this patch before creating the test client
with patch("app.dependencies.get_model_and_processor") as mock_get_model:
    # Setup mock model and processor
    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_get_model.return_value = (mock_model, mock_processor)

    # Now initialize the test client
    client = TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = get_settings()
    settings.ENABLE_ANNOTATION = True
    return settings


@pytest.fixture
def test_file():
    """Create a test file for upload."""
    test_file_path = os.path.join(os.path.dirname(__file__), "test_resume.pdf")
    with open(test_file_path, "wb") as f:
        f.write(b"test file content")
    yield test_file_path
    os.remove(test_file_path)


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


class TestUploadEndpoint:
    """Test the upload endpoint."""

    def test_upload_pdf(self, test_file):
        """Test uploading a PDF file."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload",
                files={"file": ("test_resume.pdf", f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "file_id" in data

    def test_upload_png(self, test_file):
        """Test uploading a PNG file."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload",
                files={"file": ("test_resume.png", f, "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "file_id" in data

    def test_upload_unsupported_file(self, test_file):
        """Test uploading an unsupported file type."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload",
                files={"file": ("test_resume.txt", f, "text/plain")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Unsupported file type" in data["message"]


class TestUploadAndProcessEndpoint:
    """Test the upload and process endpoint."""

    def test_upload_and_process(self, test_file, mock_process_resume):
        """Test uploading and processing a file."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload-and-process",
                files={"file": ("test_resume.pdf", f, "application/pdf")},
                data={"annotate": "true", "generate_summary": "true"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test_resume"
        assert len(data["pages"]) == 1
        assert data["message"] == "Resume processed successfully"
        assert data["summary_generated"]

        # Verify process_resume was called with correct parameters
        mock_process_resume.assert_called_once()
        args, kwargs = mock_process_resume.call_args
        assert kwargs["use_annotator"]
        assert kwargs["generate_summary"]

    def test_upload_and_process_no_annotation(self, test_file, mock_process_resume):
        """Test uploading and processing without annotation."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload-and-process",
                files={"file": ("test_resume.pdf", f, "application/pdf")},
                data={"annotate": "false", "generate_summary": "true"},
            )

        assert response.status_code == 200

        # Verify process_resume was called with correct parameters
        mock_process_resume.assert_called_once()
        args, kwargs = mock_process_resume.call_args
        assert not kwargs["use_annotator"]
        assert kwargs["generate_summary"]

    def test_upload_and_process_error(self, test_file, mock_process_resume):
        """Test error handling during processing."""
        mock_process_resume.side_effect = Exception("Processing error")

        with open(test_file, "rb") as f:
            response = client.post(
                "/api/resumes/upload-and-process",
                files={"file": ("test_resume.pdf", f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "Error processing file" in data["message"]
        assert data["pages"] == []


class TestProcessEndpoint:
    """Test the process endpoint."""

    @patch("app.api.routers.resumes.os.path.exists")
    def test_process_valid_file(self, mock_exists, mock_process_resume):
        """Test processing a valid file."""
        mock_exists.return_value = True

        response = client.post(
            "/api/resumes/process",
            params={
                "file_id": "test_resume",
                "annotate": "true",
                "generate_summary": "true",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["file_id"] == "test_resume"
        assert len(data["pages"]) == 1
        assert data["message"] == "Resume processed successfully"

        # Verify process_resume was called with correct parameters
        mock_process_resume.assert_called_once()
        args, kwargs = mock_process_resume.call_args
        assert kwargs["use_annotator"]
        assert kwargs["generate_summary"]

    @patch("app.api.routers.resumes.os.path.exists")
    def test_process_nonexistent_file(self, mock_exists, mock_process_resume):
        """Test processing a nonexistent file."""
        mock_exists.return_value = False

        response = client.post(
            "/api/resumes/process", params={"file_id": "nonexistent_file"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "File not found" in data["detail"]


class TestResultsEndpoint:
    """Test the results endpoint."""

    @patch("app.api.routers.resumes.os.path.exists")
    @patch("app.api.routers.resumes.open")
    def test_get_valid_results(self, mock_open, mock_exists):
        """Test retrieving valid results."""
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps(
            {
                "file_id": "test_resume",
                "pages": [{"data": [{"text": "John Doe", "label_name": "Name"}]}],
                "image_urls": ["/api/static/annotations/test_resume_page1.png"],
            }
        )

        response = client.get("/api/resumes/results/test_resume")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["file_id"] == "test_resume"

    @patch("app.api.routers.resumes.os.path.exists")
    def test_get_nonexistent_results(self, mock_exists):
        """Test retrieving nonexistent results."""
        mock_exists.return_value = False

        response = client.get("/api/resumes/results/nonexistent_file")

        assert response.status_code == 404
        data = response.json()
        assert "Results not found" in data["detail"]


class TestCleanupEndpoint:
    """Test the cleanup endpoint."""

    @patch("app.api.routers.resumes.shutil.rmtree")
    @patch("app.api.routers.resumes.os.makedirs")
    @patch("app.api.routers.resumes.os.path.exists")
    def test_cleanup(self, mock_exists, mock_makedirs, mock_rmtree):
        """Test cleaning up storage directories."""
        mock_exists.return_value = True

        response = client.post("/api/resumes/cleanup")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Storage directories cleaned" in data["message"]
        assert len(data["data"]["directories_cleaned"]) == 4
        assert len(data["data"]["directories_created"]) == 4

        # Verify that rmtree and makedirs were called for each directory
        assert mock_rmtree.call_count == 4
        assert mock_makedirs.call_count == 4

    @patch("app.api.routers.resumes.shutil.rmtree")
    @patch("app.api.routers.resumes.os.makedirs")
    @patch("app.api.routers.resumes.os.path.exists")
    def test_cleanup_error(self, mock_exists, mock_makedirs, mock_rmtree):
        """Test error handling during cleanup."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = Exception("Cleanup error")

        response = client.post("/api/resumes/cleanup")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial_success" or data["status"] == "failure"
        assert len(data["data"]["errors"]) > 0
