"""Invoice document model for uploaded files."""

from sqlalchemy import Column, String, Integer, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
from .enums import ProcessingStatus, FileType


class InvoiceDocument(BaseModel):
    """Model for uploaded invoice documents."""
    
    __tablename__ = "invoice_documents"
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, nullable=False)
    processing_status = Column(
        Enum(ProcessingStatus), 
        default=ProcessingStatus.PENDING, 
        nullable=False
    )
    uploaded_at = Column(DateTime, nullable=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    error_message = Column(String(1000), nullable=True)
    
    # Relationships
    extracted_data = relationship("ExtractedData", back_populates="invoice_document", uselist=False, cascade="all, delete-orphan")
    processing_job = relationship("ProcessingJob", back_populates="invoice_document", uselist=False, cascade="all, delete-orphan")
    review_session = relationship("ReviewSession", back_populates="invoice_document", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InvoiceDocument(filename='{self.filename}', status='{self.processing_status.value}')>"