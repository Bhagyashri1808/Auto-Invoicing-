"""Pydantic models for LLM processing jobs."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LLMProcessingJobDB(Base):
    """SQLAlchemy model for LLM processing jobs."""
    __tablename__ = "llm_processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    invoice_document_id = Column(String(36), nullable=False)
    preprocessing_config_id = Column(String(36), ForeignKey('preprocessing_configurations.id'), nullable=True)
    llm_model_name = Column(String(255), nullable=False)
    preprocessed_image_path = Column(Text, nullable=True)
    llm_request_payload = Column(JSON, nullable=True)
    llm_response_raw = Column(JSON, nullable=True)
    llm_response_validated = Column(JSON, nullable=True)
    processing_started_at = Column(DateTime, nullable=False)
    llm_started_at = Column(DateTime, nullable=True)
    llm_completed_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    timeout_occurred = Column(Boolean, nullable=False, default=False)
    fallback_triggered = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    memory_peak_mb = Column(Integer, nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)

    # Relationships
    preprocessing_config = relationship("PreprocessingConfigurationDB", back_populates="llm_jobs")

    __table_args__ = (
        CheckConstraint('retry_count <= max_retries', name='valid_retry_count'),
    )


class LLMProcessingJobBase(BaseModel):
    """Base schema for LLM processing job."""
    invoice_document_id: str
    preprocessing_config_id: Optional[str] = None
    llm_model_name: str
    preprocessed_image_path: Optional[str] = None
    max_retries: int = 3


class LLMProcessingJobCreate(LLMProcessingJobBase):
    """Schema for creating LLM processing job."""
    processing_started_at: datetime = Field(default_factory=datetime.utcnow)


class LLMProcessingJobUpdate(BaseModel):
    """Schema for updating LLM processing job."""
    llm_request_payload: Optional[Dict[str, Any]] = None
    llm_response_raw: Optional[Dict[str, Any]] = None
    llm_response_validated: Optional[Dict[str, Any]] = None
    llm_started_at: Optional[datetime] = None
    llm_completed_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    timeout_occurred: Optional[bool] = None
    fallback_triggered: Optional[bool] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    memory_peak_mb: Optional[int] = None
    processing_duration_ms: Optional[int] = None


class LLMProcessingJob(LLMProcessingJobBase):
    """Schema for LLM processing job response."""
    id: str
    processing_started_at: datetime
    llm_started_at: Optional[datetime] = None
    llm_completed_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    timeout_occurred: bool
    fallback_triggered: bool
    error_message: Optional[str] = None
    retry_count: int
    memory_peak_mb: Optional[int] = None
    processing_duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


class LLMProcessingJobDetail(LLMProcessingJob):
    """Schema for detailed LLM processing job response."""
    llm_request_payload: Optional[Dict[str, Any]] = None
    llm_response_raw: Optional[Dict[str, Any]] = None
    llm_response_validated: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True