"""Common enums used across models."""

import enum


class ProcessingStatus(enum.Enum):
    """Processing status enumeration."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEWING = "REVIEWING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class FileType(enum.Enum):
    """Supported file types."""
    PDF = "PDF"
    JPG = "JPG"
    PNG = "PNG"
    TIFF = "TIFF"


class ProcessingMode(enum.Enum):
    """Processing mode enumeration."""
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"


class ReviewDecision(enum.Enum):
    """Review decision enumeration."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REPROCESSING = "REQUIRES_REPROCESSING"


class ConfigDataType(enum.Enum):
    """Configuration data type enumeration."""
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"