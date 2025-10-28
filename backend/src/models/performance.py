"""Pydantic models for processing performance metrics."""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Boolean, Column, Date, Float, Integer, String, CheckConstraint
from sqlalchemy.sql import func

from .base import Base


class ExtractionMethod(str, Enum):
    """Enum for extraction method types."""
    OCR_ONLY = "OCR_ONLY"
    LLM_PRIMARY = "LLM_PRIMARY"
    LLM_FALLBACK = "LLM_FALLBACK"


class ProcessingPerformanceMetricDB(Base):
    """SQLAlchemy model for processing performance metrics."""
    __tablename__ = "processing_performance_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    invoice_document_id = Column(String(36), nullable=False)
    processing_date = Column(Date, nullable=False)
    extraction_method = Column(String(50), nullable=False)
    preprocessing_duration_ms = Column(Integer, nullable=True)
    ocr_duration_ms = Column(Integer, nullable=True)
    llm_duration_ms = Column(Integer, nullable=True)
    total_duration_ms = Column(Integer, nullable=False)
    memory_peak_mb = Column(Float, nullable=False)
    file_size_mb = Column(Float, nullable=False)
    image_dimensions = Column(String(50), nullable=True)
    preprocessing_applied = Column(Boolean, nullable=False)
    timeout_occurred = Column(Boolean, nullable=False)
    error_occurred = Column(Boolean, nullable=False)
    accuracy_score = Column(Float, nullable=True)
    user_corrections_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint('accuracy_score IS NULL OR (accuracy_score BETWEEN 0.0 AND 1.0)', name='valid_accuracy_score'),
        CheckConstraint("extraction_method IN ('OCR_ONLY', 'LLM_PRIMARY', 'LLM_FALLBACK')", name='valid_extraction_method'),
    )


class ProcessingPerformanceMetricBase(BaseModel):
    """Base schema for processing performance metric."""
    invoice_document_id: str
    processing_date: date
    extraction_method: ExtractionMethod
    preprocessing_duration_ms: Optional[int] = None
    ocr_duration_ms: Optional[int] = None
    llm_duration_ms: Optional[int] = None
    total_duration_ms: int
    memory_peak_mb: float = Field(gt=0)
    file_size_mb: float = Field(gt=0)
    image_dimensions: Optional[str] = None
    preprocessing_applied: bool
    timeout_occurred: bool
    error_occurred: bool
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_corrections_count: int = Field(default=0, ge=0)

    @validator('total_duration_ms')
    def validate_total_duration(cls, v, values):
        """Ensure total duration is >= sum of individual durations."""
        individual_durations = [
            values.get('preprocessing_duration_ms', 0) or 0,
            values.get('ocr_duration_ms', 0) or 0,
            values.get('llm_duration_ms', 0) or 0
        ]
        sum_individual = sum(individual_durations)
        if v < sum_individual:
            raise ValueError(f'total_duration_ms ({v}) must be >= sum of individual durations ({sum_individual})')
        return v


class ProcessingPerformanceMetricCreate(ProcessingPerformanceMetricBase):
    """Schema for creating processing performance metric."""
    pass


class ProcessingPerformanceMetric(ProcessingPerformanceMetricBase):
    """Schema for processing performance metric response."""
    id: str

    class Config:
        from_attributes = True


class ProcessingMetricsSummary(BaseModel):
    """Schema for aggregated processing metrics."""
    total_processed: int
    success_rate: float = Field(ge=0.0, le=1.0)
    average_processing_time_ms: int
    average_accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    method_breakdown: dict = Field(default_factory=dict)
    daily_metrics: list = Field(default_factory=list)


class DailyMetric(BaseModel):
    """Schema for daily processing metrics."""
    date: date
    processed_count: int
    average_duration_ms: int
    success_rate: float = Field(ge=0.0, le=1.0)