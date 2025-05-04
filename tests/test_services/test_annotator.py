import json
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pytest

from app.services.annotator import ResumeAnnotator, annotate_resume


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
                "Degree": "Bachelor of Science",
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
            "TechnicalSkills": ["Python", "JavaScript"],
            "Languages": ["English"],
        },
    }


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
                }
            },
            "page2": {
                "WorkExperience": [
                    {
                        "JobTitle": "Software Engineer",
                        "Company": "Tech Company",
                        "Duration": "2021-Present",
                        "Responsibilities": "Developing applications",
                    }
                ]
            },
        }
    }


class TestResumeAnnotator:
    """Test the ResumeAnnotator class."""

    def test_init_pdf(self, mock_easyocr, mock_fitz, mock_cv2, sample_json_data):
        """Test initializing with a PDF file."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".pdf")

            annotator = ResumeAnnotator("test.pdf", sample_json_data)

            assert annotator.is_pdf
            assert mock_fitz.open.called
            assert annotator.reader is not None

    def test_init_png(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test initializing with a PNG file."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            assert not annotator.is_pdf
            assert mock_cv2.imread.called
            assert annotator.reader is not None

    def test_load_images_pdf(self, mock_easyocr, mock_fitz, mock_cv2, sample_json_data):
        """Test loading images from a PDF file."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".pdf")

            # Configure mock document to have 2 pages
            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = [MagicMock(), MagicMock()]
            mock_fitz.open.return_value = mock_doc

            annotator = ResumeAnnotator("test.pdf", sample_json_data)

            assert len(annotator.images) == 2

    def test_find_text_locations(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test finding text locations in an image."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Get a test image
            test_image = np.zeros((600, 800, 3), dtype=np.uint8)

            # Call find_text_locations
            locations = annotator.find_text_locations(test_image)

            # Check results
            assert "john doe" in locations
            assert "john.doe@example.com" in locations
            assert len(locations) > 5  # Should include words and full phrases

    def test_find_tfidf_match(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test finding text matches using TF-IDF similarity."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Create test candidates
            candidates = {
                "john doe": (0.1, 0.1, 0.2, 0.2),
                "jane smith": (0.3, 0.3, 0.4, 0.4),
            }

            # Test exact match
            match, coords, score = annotator.find_tfidf_match("john doe", candidates)
            assert match == "john doe"
            assert score > 0.8

            # Test similar match
            match, coords, score = annotator.find_tfidf_match("John", candidates)
            assert "john" in match
            assert score > 0

    def test_find_sequence_match(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test finding text matches using sequence matching."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Create test candidates
            candidates = {
                "john.doe@example.com": (0.1, 0.1, 0.2, 0.2),
                "+1 (234) 567-890": (0.3, 0.3, 0.4, 0.4),
            }

            # Test email match
            match, coords, score = annotator.find_sequence_match(
                "john.doe@example.com", candidates, "Email"
            )
            assert match == "john.doe@example.com"
            assert score > 0.8

            # Test phone match with different formatting
            match, coords, score = annotator.find_sequence_match(
                "+1-234-567-890", candidates, "Phone"
            )
            assert "+1" in match
            assert score > 0.7

    def test_match_fields(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test matching fields to text locations."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Create test text locations
            text_locations = {
                "john doe": (0.1, 0.1, 0.2, 0.2),
                "john.doe@example.com": (0.3, 0.3, 0.4, 0.4),
                "+1234567890": (0.5, 0.5, 0.6, 0.6),
                "new york, ny": (0.7, 0.7, 0.8, 0.8),
                "software engineer": (0.8, 0.8, 0.9, 0.9),
            }

            # Create flattened JSON data
            flat_json = {
                "Name": "John Doe",
                "Email": "john.doe@example.com",
                "Phone": "+1234567890",
                "Location": "New York, NY",
                "JobTitle": "Software Engineer",
            }

            # Call _match_fields
            coords = annotator._match_fields(text_locations, flat_json)

            # Check results
            assert "Name" in coords
            assert "Email" in coords
            assert "Phone" in coords
            assert "Location" in coords
            assert "JobTitle" in coords

    def test_process_document(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test processing a document to find field coordinates."""
        with patch("app.services.annotator.os.path.splitext") as mock_splitext:
            mock_splitext.return_value = ("test", ".png")

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Mock find_text_locations and _match_fields
            annotator.find_text_locations = MagicMock(
                return_value={
                    "john doe": (0.1, 0.1, 0.2, 0.2),
                    "john.doe@example.com": (0.3, 0.3, 0.4, 0.4),
                }
            )
            annotator._match_fields = MagicMock(
                return_value={
                    "Name": (0.1, 0.1, 0.2, 0.2),
                    "Email": (0.3, 0.3, 0.4, 0.4),
                }
            )

            # Call process_document
            results = annotator.process_document()

            # Check results
            assert len(results) == 1  # One page
            assert results[0]["page"] == 0
            assert "coordinates" in results[0]
            assert "dimensions" in results[0]
            assert len(results[0]["coordinates"]) == 2  # Two fields matched

    def test_annotate_document(self, mock_easyocr, mock_cv2, sample_json_data):
        """Test annotating a document with field bounding boxes."""
        with (
            patch("app.services.annotator.os.path.splitext") as mock_splitext,
            patch("app.services.annotator.os.makedirs") as mock_makedirs,
            patch("app.services.annotator.os.path.basename") as mock_basename,
        ):
            mock_splitext.return_value = ("test", ".png")
            mock_basename.return_value = "test.png"

            annotator = ResumeAnnotator("test.png", sample_json_data)

            # Mock process_document
            annotator.process_document = MagicMock(
                return_value=[
                    {
                        "page": 0,
                        "coordinates": {
                            "Name": (0.1, 0.1, 0.2, 0.2),
                            "Email": (0.3, 0.3, 0.4, 0.4),
                        },
                        "dimensions": (800, 600),
                    }
                ]
            )

            # Call annotate_document
            annotated_images = annotator.annotate_document("/tmp/output")

            # Check results
            assert len(annotated_images) == 1
            assert mock_makedirs.called
            assert mock_cv2.imwrite.called


class TestAnnotateResume:
    """Test the annotate_resume function."""

    @patch("app.services.annotator.os.makedirs")
    @patch("app.services.annotator.os.path.exists")
    @patch("app.services.annotator.os.path.basename")
    @patch("app.services.annotator.os.path.splitext")
    @patch("app.services.annotator.open", new_callable=mock_open, read_data="{}")
    def test_annotate_resume_png(
        self,
        mock_file,
        mock_splitext,
        mock_basename,
        mock_exists,
        mock_makedirs,
        mock_easyocr,
        mock_cv2,
    ):
        """Test annotating a PNG resume."""
        mock_splitext.return_value = ("test", ".png")
        mock_basename.return_value = "test.png"
        mock_exists.return_value = True

        # Mock ResumeAnnotator
        with patch("app.services.annotator.ResumeAnnotator") as MockAnnotator:
            mock_annotator = MagicMock()
            MockAnnotator.return_value = mock_annotator

            # Call annotate_resume
            annotate_resume("test.png", "test.json", "/tmp/output")

            # Check if ResumeAnnotator was created and methods called
            assert MockAnnotator.called
            assert mock_annotator.annotate_document.called

    @patch("app.services.annotator.os.makedirs")
    @patch("app.services.annotator.os.path.exists")
    @patch("app.services.annotator.os.path.basename")
    @patch("app.services.annotator.os.path.splitext")
    @patch(
        "app.services.annotator.open",
        new_callable=mock_open,
        read_data=json.dumps({"pages": {"page1": {}}}),
    )
    def test_annotate_resume_multipage_pdf(
        self,
        mock_file,
        mock_splitext,
        mock_basename,
        mock_exists,
        mock_makedirs,
        mock_easyocr,
        mock_fitz,
        mock_cv2,
    ):
        """Test annotating a multi-page PDF resume."""
        mock_splitext.return_value = ("test", ".pdf")
        mock_basename.return_value = "test.pdf"
        mock_exists.return_value = True

        # Mock fitz.open to return a multi-page document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_fitz.open.return_value = mock_doc

        # Mock ResumeAnnotator
        with patch("app.services.annotator.ResumeAnnotator") as MockAnnotator:
            mock_annotator = MagicMock()
            MockAnnotator.return_value = mock_annotator

            # Call annotate_resume
            annotate_resume("test.pdf", "test.json", "/tmp/output")

            # Check if fitz.open was called
            assert mock_fitz.open.called

            # For multi-page PDFs, we should annotate each page
            assert mock_annotator.annotate_page.call_count > 0
