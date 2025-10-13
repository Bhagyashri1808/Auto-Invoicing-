"""Processing job model for queue management."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from .enums import ProcessingStatus, ProcessingMode


class ProcessingJob(BaseModel):
    """Model for managing document processing workflow and queue operations."""
    
    __tablename__ = "processing_jobs"
    
    # Foreign key to invoice document
    invoice_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoice_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    
    # Queue management
    queue_position = Column(Integer, nullable=False)
    processing_mode = Column(Enum(ProcessingMode), nullable=False)
    
    # Status tracking
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    
    # Execution tracking
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Relationships
    invoice_document = relationship("InvoiceDocument", back_populates="processing_job")
    
    @property
    def is_completed(self) -> bool:
        """Check if processing is completed."""
        return self.completed_at is not None
    
    @property
    def is_failed(self) -> bool:
        """Check if processing has failed."""
        return self.retry_count >= self.max_retries and not self.is_completed
    
    def __repr__(self):
        return f"<ProcessingJob(position={self.queue_position}, mode='{self.processing_mode.value}', retries={self.retry_count})>"