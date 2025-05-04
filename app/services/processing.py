import os
import re
import sys
from typing import Any

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def validate_email(email: str) -> bool:
    """
    Validate if a string is a properly formatted email address.

    Args:
        email: The email string to validate

    Returns:
        True if the email is valid, False otherwise
    """
    # Basic regex for email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate if a string contains a valid phone number.

    Args:
        phone: The phone string to validate

    Returns:
        True if the phone is valid, False otherwise
    """
    # Remove common separators
    clean_phone = re.sub(r"[\s\-\.\(\)]", "", phone)
    # Check if we have a reasonable number of digits
    return 7 <= len(clean_phone) <= 15 and bool(re.match(r"^[+]?\d+$", clean_phone))


def validate_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted URL.

    Args:
        url: The URL string to validate

    Returns:
        True if the URL is valid, False otherwise
    """
    # Basic regex for URL validation (shortened)
    url_pattern = (
        r"^(https?:\/\/)?(www\.)?([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)"
        r"(\/[a-zA-Z0-9_-]+)*\/?$"
    )
    return bool(re.match(url_pattern, url))


def validate_linkedin_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted LinkedIn URL.

    Args:
        url: The LinkedIn URL string to validate

    Returns:
        True if the LinkedIn URL is valid, False otherwise
    """
    # Check if it's a valid URL with linkedin.com domain
    return validate_url(url) and ("linkedin.com" in url)


def clean_date(date_str: str) -> str:
    """
    Clean and standardize date strings from various formats.

    Args:
        date_str: Date string to clean

    Returns:
        Cleaned date string
    """
    # Handle empty values
    if not date_str or date_str == "Not Found":
        return "Not Found"

    # Try to clean and standardize the date format
    # This is a simplified version - you can expand it as needed
    return date_str


def validate_cv_data(json_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and clean extracted CV data.

    Args:
        json_data: The CV data dictionary

    Returns:
        Validated CV data dictionary
    """
    pages = json_data.get("pages", {})

    for _page_key, page_data in pages.items():
        # Validate personal info
        if "PersonalInfo" in page_data:
            personal_info = page_data["PersonalInfo"]

            # Validate email (Combined if statement)
            if (
                "Email" in personal_info
                and personal_info["Email"] != "Not Found"
                and not validate_email(personal_info["Email"])
            ):
                personal_info["Email"] = "Not Found"

            # Validate phone (Combined if statement)
            if (
                "Phone" in personal_info
                and personal_info["Phone"] != "Not Found"
                and not validate_phone(personal_info["Phone"])
            ):
                personal_info["Phone"] = "Not Found"

        # Clean education dates
        if "Education" in page_data and isinstance(page_data["Education"], list):
            for edu in page_data["Education"]:
                if "GradDate" in edu:
                    edu["GradDate"] = clean_date(edu["GradDate"])

        # Clean work experience dates
        if "WorkExperience" in page_data and isinstance(
            page_data["WorkExperience"], list
        ):
            for work in page_data["WorkExperience"]:
                if "Duration" in work:
                    work["Duration"] = clean_date(work["Duration"])

        # Validate skill entries
        if "Skills" in page_data:
            skills = page_data["Skills"]

            # Ensure TechnicalSkills is a list
            if "TechnicalSkills" in skills and not isinstance(
                skills["TechnicalSkills"], list
            ):
                if (
                    skills["TechnicalSkills"]
                    and skills["TechnicalSkills"] != "Not Found"
                ):
                    # Convert to list if it's a string
                    skills["TechnicalSkills"] = [skills["TechnicalSkills"]]
                else:
                    skills["TechnicalSkills"] = []

            # Ensure Languages is a list
            if "Languages" in skills and not isinstance(skills["Languages"], list):
                if skills["Languages"] and skills["Languages"] != "Not Found":
                    # Convert to list if it's a string
                    skills["Languages"] = [skills["Languages"]]
                else:
                    skills["Languages"] = []

    return json_data


def update_image_urls(result, base_url):
    """
    Update image URLs with the proper base URL.

    Args:
        result: The result dictionary with image_urls
        base_url: The base URL to prepend

    Returns:
        Updated result dictionary
    """
    # Make sure base URL ends with a slash if it doesn't already
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"

    # Update the image URLs
    updated_urls = []
    for url in result.get("image_urls", []):
        # Check if it's already a full URL
        if url.startswith(("http://", "https://")):
            updated_urls.append(url)
        else:
            # Remove leading slash if present to avoid double slash
            clean_url = url.lstrip("/")
            updated_url = f"{base_url}{clean_url}"
            updated_urls.append(updated_url)

    result["image_urls"] = updated_urls
    return result
