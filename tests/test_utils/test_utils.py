import pytest

from app.core.utils import categorize_skills, clean_text, extract_skills_from_text


class TestCleanText:
    """Test the clean_text function."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Test", "Test"),
            ("  Test  ", "Test"),
            ("Test   with    multiple    spaces", "Test with multiple spaces"),
            ("Test\nwith\nnewlines", "Test with newlines"),
            ("Test\t with\ttabs", "Test with tabs"),
            (None, "Not Found"),
            ("", "Not Found"),
            ("Not Found", "Not Found"),
        ],
    )
    def test_clean_text(self, text, expected):
        """Test cleaning text with various inputs."""
        result = clean_text(text)
        assert result == expected


class TestExtractSkillsFromText:
    """Test the extract_skills_from_text function."""

    def test_extract_skills_exact_match(self):
        """Test extracting skills with exact matches."""
        text = "Proficient in Python, JavaScript, and SQL. Experience with React and Node.js."
        skill_keywords = ["Python", "JavaScript", "SQL", "Java", "C++"]

        result = extract_skills_from_text(text, skill_keywords)

        assert len(result) == 3
        assert "Python" in result
        assert "JavaScript" in result
        assert "SQL" in result
        assert "Java" not in result
        assert "C++" not in result

    def test_extract_skills_case_insensitive(self):
        """Test extracting skills with case-insensitive matching."""
        text = "Proficient in python, javascript, and sql."
        skill_keywords = ["Python", "JavaScript", "SQL"]

        result = extract_skills_from_text(text, skill_keywords)

        assert len(result) == 3
        assert "Python" in result
        assert "JavaScript" in result
        assert "SQL" in result

    def test_extract_skills_word_boundaries(self):
        """Test extracting skills respecting word boundaries."""
        text = "Experience with JavaScript and TypeScript."
        skill_keywords = ["Java", "JavaScript", "Script"]

        result = extract_skills_from_text(text, skill_keywords)

        assert len(result) == 1
        assert "JavaScript" in result
        assert "Java" not in result  # Should not match "Java" inside "JavaScript"
        assert "Script" not in result  # Should not match "Script" inside "JavaScript"

    def test_extract_skills_empty(self):
        """Test extracting skills with empty inputs."""
        text = "Proficient in Python, JavaScript, and SQL."

        # Empty skill keywords
        result = extract_skills_from_text(text, [])
        assert len(result) == 0

        # Empty text
        result = extract_skills_from_text("", ["Python", "JavaScript"])
        assert len(result) == 0


class TestCategorizeSkills:
    """Test the categorize_skills function."""

    def test_categorize_skills(self):
        """Test categorizing skills into different categories."""
        skills = ["Python", "JavaScript", "English", "French", "Project Management"]
        categories = {
            "Programming": ["Python", "JavaScript", "Java", "C++"],
            "Languages": ["English", "French", "Spanish", "German"],
            "Management": ["Project Management", "Team Leadership", "Agile"],
        }

        result = categorize_skills(skills, categories)

        assert len(result) == 3
        assert "Programming" in result
        assert "Languages" in result
        assert "Management" in result
        assert len(result["Programming"]) == 2
        assert len(result["Languages"]) == 2
        assert len(result["Management"]) == 1
        assert "Python" in result["Programming"]
        assert "JavaScript" in result["Programming"]
        assert "English" in result["Languages"]
        assert "French" in result["Languages"]
        assert "Project Management" in result["Management"]

    def test_categorize_skills_case_insensitive(self):
        """Test categorizing skills with case-insensitive matching."""
        skills = ["python", "javascript", "english"]
        categories = {
            "Programming": ["Python", "JavaScript"],
            "Languages": ["English", "French"],
        }

        result = categorize_skills(skills, categories)

        assert len(result) == 2
        assert "Programming" in result
        assert "Languages" in result
        assert len(result["Programming"]) == 2
        assert len(result["Languages"]) == 1

    def test_categorize_skills_empty_categories(self):
        """Test categorizing skills with empty categories."""
        skills = ["Python", "JavaScript", "English"]

        # Empty categories
        result = categorize_skills(skills, {})
        assert len(result) == 0

        # Category with no matching skills
        result = categorize_skills(skills, {"Other": ["C++", "Java"]})
        assert len(result) == 0

    def test_categorize_skills_empty_skills(self):
        """Test categorizing an empty skills list."""
        categories = {
            "Programming": ["Python", "JavaScript"],
            "Languages": ["English", "French"],
        }

        result = categorize_skills([], categories)

        assert len(result) == 0
