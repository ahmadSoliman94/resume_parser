from dataclasses import dataclass
from enum import Enum


class FileType(str, Enum):
    """Supported file types."""

    PDF = "pdf"
    PNG = "png"


class ProcessingStatus(str, Enum):
    """Status of invoice processing."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


@dataclass
class ProcessingMetrics:
    """Metrics for invoice processing."""

    start_time: float
    end_time: float | None = None
    total_execution_time: float | None = None
    ocr_time: float | None = None
    annotation_time: float | None = None

    def calculate_total_time(self):
        """Calculate total execution time."""
        if self.end_time and self.start_time:
            self.total_execution_time = self.end_time - self.start_time
        return self.total_execution_time


@dataclass
class ProcessingResult:
    """Result of invoice processing."""

    file_path: str
    status: ProcessingStatus
    extraction_file_path: str | None = None
    annotated_file_paths: list[str] | None = None
    metrics: ProcessingMetrics | None = None
    error: str | None = None
