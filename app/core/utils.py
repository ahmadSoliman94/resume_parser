import re


def clean_text(text: str) -> str:
    """
    Clean text by removing excess whitespace and normalizing.

    Args:
        text: The text to clean

    Returns:
        Cleaned text
    """
    if not text or text == "Not Found":
        return "Not Found"

    # Replace multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    # Trim whitespace
    return text.strip()


def extract_skills_from_text(text: str, skill_keywords: list[str]) -> list[str]:
    """
    Extract skills from text based on a list of skill keywords.

    Args:
        text: The text to analyze
        skill_keywords: List of skill keywords to look for

    Returns:
        List of found skills
    """
    found_skills = []

    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()

    for skill in skill_keywords:
        skill_lower = skill.lower()
        # Match whole words only
        pattern = r"\b" + re.escape(skill_lower) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


def categorize_skills(
    skills: list[str], categories: dict[str, list[str]]
) -> dict[str, list[str]]:
    """
    Categorize skills into different categories.

    Args:
        skills: List of skills to categorize
        categories: Dictionary mapping category names to lists of skills in
                    that category

    Returns:
        Dictionary mapping category names to found skills in that category
    """
    result: dict[str, list[str]] = {category: [] for category in categories}

    for skill in skills:
        skill_lower = skill.lower()

        for category, category_skills in categories.items():
            if skill_lower in [s.lower() for s in category_skills]:
                result[category].append(skill)
                break

    return {k: v for k, v in result.items() if v}  # Remove empty categories
