from fastapi import HTTPException, status


class ResumeProcessingError(HTTPException):
    """Exception for Resume processing errors."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resumeice processing error: {detail}",
        )


class FileNotFoundError(HTTPException):
    """Exception for file not found errors."""

    def __init__(self, file_path: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}",
        )


class UnsupportedFileTypeError(HTTPException):
    """Exception for unsupported file types."""

    def __init__(self, file_type: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"""Unsupported file type: {file_type}.
            Only PDF and PNG files are supported.""",
        )


class ModelLoadingError(HTTPException):
    """Exception for model loading errors."""

    def __init__(self, detail: str = "Failed to load OCR model"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
