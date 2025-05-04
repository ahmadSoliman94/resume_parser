import pytest

from app.services.processing import (
    clean_date,
    update_image_urls,
    validate_cv_data,
    validate_email,
    validate_linkedin_url,
    validate_phone,
    validate_url,
)


class TestValidateEmail:
    """Test the validate_email function."""

    @pytest.mark.parametrize(
        "email,expected",
        [
            ("john.doe@example.com", True),
            ("john_doe@example.co.uk", True),
            ("john+doe@example.com", True),
            ("john.doe@subdomain.example.com", True),
            ("john-doe@example.com", True),
            ("john@example", False),
            ("john@.com", False),
            ("john@example..com", False),
            ("john@example.c", False),
            ("john@example@com", False),
            ("john doe@example.com", False),
            ("@example.com", False),
            ("john@", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_email(self, email, expected):
        """Test email validation with various inputs."""
        result = validate_email(email)
        assert result == expected


class TestValidatePhone:
    """Test the validate_phone function."""

    @pytest.mark.parametrize(
        "phone,expected",
        [
            ("+1 (123) 456-7890", True),
            ("+1-123-456-7890", True),
            ("+11234567890", True),
            ("123-456-7890", True),
            ("(123) 456-7890", True),
            ("123.456.7890", True),
            ("1234567890", True),
            ("+1-123-45", False),  # Too short
            ("+1-123-456-7890-1234", False),  # Too long
            ("abc-def-ghij", False),  # Non-digit characters
            ("", False),
            (None, False),
        ],
    )
    def test_validate_phone(self, phone, expected):
        """Test phone validation with various inputs."""
        result = validate_phone(phone)
        assert result == expected


class TestValidateURL:
    """Test the validate_url function."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://example.com", True),
            ("http://example.com", True),
            ("www.example.com", True),
            ("example.com", True),
            ("example.com/path", True),
            ("sub.example.com", True),
            ("example.com/path/to/resource", True),
            ("example", False),
            ("example.", False),
            ("http://", False),
            ("http://.com", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_url(self, url, expected):
        """Test URL validation with various inputs."""
        result = validate_url(url)
        assert result == expected


class TestValidateLinkedInURL:
    """Test the validate_linkedin_url function."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://linkedin.com/in/johndoe", True),
            ("http://linkedin.com/in/johndoe", True),
            ("www.linkedin.com/in/johndoe", True),
            ("linkedin.com/in/johndoe", True),
            ("https://www.linkedin.com/in/john-doe", True),
            ("https://facebook.com/johndoe", False),  # Not LinkedIn
            ("linkedin", False),
            ("www.linkedn.com/in/johndoe", False),  # Typo in domain
            ("", False),
            (None, False),
        ],
    )
    def test_validate_linkedin_url(self, url, expected):
        """Test LinkedIn URL validation with various inputs."""
        result = validate_linkedin_url(url)
        assert result == expected


class TestCleanDate:
    """Test the clean_date function."""

    @pytest.mark.parametrize(
        "date_str,expected",
        [
            ("2020-01-01", "2020-01-01"),
            ("01/01/2020", "01/01/2020"),
            ("January 2020", "January 2020"),
            ("2020", "2020"),
            ("2018-2022", "2018-2022"),
            ("Present", "Present"),
            ("Not Found", "Not Found"),
            ("", "Not Found"),
            (None, "Not Found"),
        ],
    )
    def test_clean_date(self, date_str, expected):
        """Test date cleaning with various inputs."""
        result = clean_date(date_str)
        assert result == expected


class TestValidateCVData:
    """Test the validate_cv_data function."""

    def test_validate_cv_data_personal_info(self):
        """Test validation of personal information."""
        # Create test data with invalid email and phone
        cv_data = {
            "pages": {
                "page1": {
                    "PersonalInfo": {
                        "Name": "John Doe",
                        "Email": "not_an_email",
                        "Phone": "not_a_phone",
                        "Location": "New York, NY",
                    }
                }
            }
        }

        # Validate data
        result = validate_cv_data(cv_data)

        # Check if invalid fields were set to "Not Found"
        assert result["pages"]["page1"]["PersonalInfo"]["Name"] == "John Doe"
        assert result["pages"]["page1"]["PersonalInfo"]["Email"] == "Not Found"
        assert result["pages"]["page1"]["PersonalInfo"]["Phone"] == "Not Found"
        assert result["pages"]["page1"]["PersonalInfo"]["Location"] == "New York, NY"

    def test_validate_cv_data_education(self):
        """Test validation of education information."""
        # Create test data with education entries
        cv_data = {
            "pages": {
                "page1": {
                    "Education": [
                        {
                            "Degree": "Bachelor of Science",
                            "Institution": "Test University",
                            "GradDate": "01/01/2020",
                        },
                        {
                            "Degree": "Master of Science",
                            "Institution": "Another University",
                            "GradDate": None,
                        },
                    ]
                }
            }
        }

        # Validate data
        result = validate_cv_data(cv_data)

        # Check if dates were cleaned
        assert result["pages"]["page1"]["Education"][0]["GradDate"] == "01/01/2020"
        assert result["pages"]["page1"]["Education"][1]["GradDate"] == "Not Found"

    def test_validate_cv_data_work_experience(self):
        """Test validation of work experience information."""
        # Create test data with work experience entries
        cv_data = {
            "pages": {
                "page1": {
                    "WorkExperience": [
                        {
                            "JobTitle": "Software Engineer",
                            "Company": "Tech Company",
                            "Duration": "2018-2020",
                            "Responsibilities": "Developing applications",
                        },
                        {
                            "JobTitle": "Senior Engineer",
                            "Company": "Another Company",
                            "Duration": None,
                            "Responsibilities": "Leading projects",
                        },
                    ]
                }
            }
        }

        # Validate data
        result = validate_cv_data(cv_data)

        # Check if dates were cleaned
        assert result["pages"]["page1"]["WorkExperience"][0]["Duration"] == "2018-2020"
        assert result["pages"]["page1"]["WorkExperience"][1]["Duration"] == "Not Found"

    def test_validate_cv_data_skills(self):
        """Test validation of skills information."""
        # Create test data with skills as strings instead of lists
        cv_data = {
            "pages": {
                "page1": {
                    "Skills": {
                        "TechnicalSkills": "Python, JavaScript",
                        "Languages": "English, Spanish",
                    }
                }
            }
        }

        # Validate data
        result = validate_cv_data(cv_data)

        # Check if strings were converted to lists
        assert isinstance(result["pages"]["page1"]["Skills"]["TechnicalSkills"], list)
        assert isinstance(result["pages"]["page1"]["Skills"]["Languages"], list)
        assert (
            "Python, JavaScript"
            in result["pages"]["page1"]["Skills"]["TechnicalSkills"]
        )
        assert "English, Spanish" in result["pages"]["page1"]["Skills"]["Languages"]

    def test_validate_cv_data_empty_skills(self):
        """Test validation of empty skills."""
        # Create test data with empty or "Not Found" skills
        cv_data = {
            "pages": {
                "page1": {"Skills": {"TechnicalSkills": "Not Found", "Languages": None}}
            }
        }

        # Validate data
        result = validate_cv_data(cv_data)

        # Check if empty skills were converted to empty lists
        assert isinstance(result["pages"]["page1"]["Skills"]["TechnicalSkills"], list)
        assert isinstance(result["pages"]["page1"]["Skills"]["Languages"], list)
        assert len(result["pages"]["page1"]["Skills"]["TechnicalSkills"]) == 0
        assert len(result["pages"]["page1"]["Skills"]["Languages"]) == 0


class TestUpdateImageUrls:
    """Test the update_image_urls function."""

    def test_update_image_urls_relative(self):
        """Test updating relative image URLs."""
        # Create test data with relative image URLs
        result = {
            "image_urls": [
                "api/static/annotations/test_resume_page1.png",
                "/api/static/annotations/test_resume_page2.png",
            ]
        }

        # Update image URLs
        updated = update_image_urls(result, "http://localhost:8000")

        # Check if URLs were updated correctly
        assert (
            updated["image_urls"][0]
            == "http://localhost:8000/api/static/annotations/test_resume_page1.png"
        )
        assert (
            updated["image_urls"][1]
            == "http://localhost:8000/api/static/annotations/test_resume_page2.png"
        )

    def test_update_image_urls_absolute(self):
        """Test updating already absolute image URLs."""
        # Create test data with absolute image URLs
        result = {
            "image_urls": [
                "http://example.com/api/static/annotations/test_resume_page1.png",
                "https://example.com/api/static/annotations/test_resume_page2.png",
            ]
        }

        # Update image URLs
        updated = update_image_urls(result, "http://localhost:8000")

        # Check if URLs were left unchanged
        assert (
            updated["image_urls"][0]
            == "http://example.com/api/static/annotations/test_resume_page1.png"
        )
        assert (
            updated["image_urls"][1]
            == "https://example.com/api/static/annotations/test_resume_page2.png"
        )

    def test_update_image_urls_mixed(self):
        """Test updating a mix of relative and absolute image URLs."""
        # Create test data with mixed image URLs
        result = {
            "image_urls": [
                "api/static/annotations/test_resume_page1.png",
                "http://example.com/api/static/annotations/test_resume_page2.png",
            ]
        }

        # Update image URLs
        updated = update_image_urls(result, "http://localhost:8000")

        # Check if URLs were updated correctly
        assert (
            updated["image_urls"][0]
            == "http://localhost:8000/api/static/annotations/test_resume_page1.png"
        )
        assert (
            updated["image_urls"][1]
            == "http://example.com/api/static/annotations/test_resume_page2.png"
        )

    def test_update_image_urls_empty(self):
        """Test updating empty image URLs list."""
        # Create test data with empty image URLs list
        result = {"image_urls": []}

        # Update image URLs
        updated = update_image_urls(result, "http://localhost:8000")

        # Check if result is unchanged
        assert updated["image_urls"] == []

    def test_update_image_urls_no_urls(self):
        """Test updating result with no image_urls key."""
        # Create test data without image_urls key
        result = {}

        # Update image URLs
        updated = update_image_urls(result, "http://localhost:8000")

        # Check if result is unchanged
        assert "image_urls" not in updated
